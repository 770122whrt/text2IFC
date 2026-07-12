"""Provider-backed staged composition for dynamic multi-storey candidates."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from text2ifc_contract.validation_v2 import validate_v2_document

from .candidate_index import build_candidate_index
from .changeset_stage import run_changeset_stage
from .package_gates import validate_package_changeset
from .revisions import hash_json_value


def build_skeleton_workspace(expected_facts: Mapping[str, Any]) -> dict[str, Any]:
    """Build only deterministic spatial hierarchy from explicit storey facts."""

    storeys = [
        dict(storey)
        for storey in expected_facts.get("storeys", [])
        if isinstance(storey, Mapping)
    ]
    entities = [
        _entity("project-main", "IfcProject", "Project"),
        _entity("site-main", "IfcSite", "Site", relative_to="project-main"),
        _entity("building-main", "IfcBuilding", "Building", relative_to="site-main"),
    ]
    for index, storey in enumerate(storeys, start=1):
        storey_id = str(storey["id"])
        elevation = storey["elevation_mm"]
        entity = _entity(
            storey_id,
            "IfcBuildingStorey",
            str(storey.get("name") or f"Storey {index}"),
            relative_to="building-main",
            origin=[0, 0, elevation],
        )
        entity["attributes"]["Elevation"] = elevation
        entities.append(entity)
    relationships = [
        _aggregate("aggregate-project-site", "project-main", ["site-main"]),
        _aggregate("aggregate-site-building", "site-main", ["building-main"]),
        _aggregate(
            "aggregate-building-storeys",
            "building-main",
            [str(storey["id"]) for storey in storeys],
        ),
    ]
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": entities,
        "relationships": relationships,
        "provenance": {"source": "text2ifc/staged-skeleton"},
    }


def run_staged_generation(
    *,
    provider: Any,
    output_dir: Path | str,
    case_id: str,
    user_request: str,
    conversation: list[dict[str, Any]],
    design_brief: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
    skeleton: Mapping[str, Any],
    manifest: Mapping[str, Any],
    trace_level: str | None = "debug",
) -> dict[str, Any]:
    """Compose all non-skeleton packages and promote only one final Formal candidate."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if manifest.get("status") != "ready":
        return _blocked("draft_required", manifest.get("issues", []), [])
    workspace = copy.deepcopy(dict(skeleton))
    revision = _revision(
        candidate=workspace,
        expected_facts=expected_facts,
        sequence=0,
        parent_revision_id=None,
        source_route="staged_composition",
        artifact="workspace-skeleton.json",
    )
    _write_json(output / "workspace-skeleton.json", workspace)
    _write_json(output / "generation-package-manifest.json", manifest)
    _write_json(output / "workspace-status.json", _workspace_status(False, 0, len(manifest.get("packages", [])) - 1))
    package_records: list[dict[str, Any]] = []
    packages = [
        dict(package)
        for package in manifest.get("packages", [])
        if isinstance(package, Mapping) and package.get("kind") != "skeleton"
    ]

    for sequence, package in enumerate(packages, start=1):
        package_id = str(package["package_id"])
        artifact_dir = f"package-{sequence:02d}-{package_id}"
        package_dir = output / artifact_dir
        package_dir.mkdir(parents=True, exist_ok=True)
        issue_id = f"issue-{package_id}"
        scope = _package_scope(
            package=package,
            workspace=workspace,
            revision=revision,
            sequence=sequence,
            issue_id=issue_id,
        )
        issues = [
            {
                "issue_id": issue_id,
                "actual_ref": f"entity:{package['owned_component_ids'][0]}#/" if package.get("owned_component_ids") else "package:/",
                "expected_fact_ref": f"expected-facts:/generation_package_manifest/packages/{sequence}",
                "evidence": f"Generate only components owned by {package_id}.",
            }
        ]
        stage = run_changeset_stage(
            provider=provider,
            output_dir=package_dir,
            case_id=case_id,
            call_index=sequence,
            user_request=user_request,
            conversation=conversation,
            design_brief=design_brief,
            expected_facts=expected_facts,
            candidate=workspace,
            base_revision=revision,
            scope=scope,
            issues=issues,
            trace_level=trace_level,
        )
        record = {
            "package_id": package_id,
            "artifact_dir": artifact_dir,
            "pre_apply_status": "partial_not_formal",
            "response_id": stage.get("response_id"),
            "classification": stage.get("classification"),
        }
        if stage.get("classification") == "draft" and stage.get("valid") is True:
            package_records.append({**record, "status": "draft_required"})
            _write_json(output / "package-records.json", {"packages": package_records})
            return _blocked("draft_required", stage.get("diagnostics", []), package_records)
        if stage.get("classification") != "changeset" or stage.get("valid") is not True:
            package_records.append({**record, "status": "blocked"})
            _write_json(output / "package-records.json", {"packages": package_records})
            return _blocked("package_blocked", stage.get("diagnostics", []), package_records)

        changeset = _read_json(package_dir / "changeset.json")
        gate = validate_package_changeset(
            manifest=manifest,
            package_id=package_id,
            workspace=workspace,
            changeset=changeset,
        )
        _write_json(package_dir / "package-gate.json", gate)
        if not gate["valid"]:
            package_records.append({**record, "status": "blocked", "gate_issue_count": len(gate["issues"])})
            _write_json(output / "package-records.json", {"packages": package_records})
            return _blocked("package_blocked", gate["issues"], package_records)

        before_hashes = build_candidate_index(workspace)["component_hashes"]
        workspace = _apply_add_operations(workspace, changeset["operations"])
        after_hashes = build_candidate_index(workspace)["component_hashes"]
        changed_existing = sorted(
            component_id
            for component_id, before_hash in before_hashes.items()
            if after_hashes.get(component_id) != before_hash
        )
        if changed_existing:
            issue = {
                "code": "PACKAGE_FROZEN_COMPONENT_DRIFT",
                "path": "/operations",
                "component_ids": changed_existing,
            }
            package_records.append({**record, "status": "blocked", "gate_issue_count": 1})
            return _blocked("package_blocked", [issue], package_records)
        revision = _revision(
            candidate=workspace,
            expected_facts=expected_facts,
            sequence=sequence,
            parent_revision_id=str(revision["revision_id"]),
            source_route="staged_composition",
            artifact=f"{artifact_dir}/workspace-after.json",
        )
        _write_json(package_dir / "workspace-after.json", workspace)
        _write_json(package_dir / "revision.json", revision)
        package_records.append(
            {
                **record,
                "status": "accepted",
                "gate_issue_count": 0,
                "revision_id": revision["revision_id"],
                "candidate_hash": revision["candidate_hash"],
                "frozen_component_count": len(before_hashes),
            }
        )
        _write_json(output / "workspace-status.json", _workspace_status(False, sequence, len(packages)))

    formal_issues = validate_v2_document(workspace)
    diagnostics = [
        {"code": issue.code, "path": issue.path, "message": issue.message}
        for issue in formal_issues
    ]
    if diagnostics:
        _write_json(output / "final-validation.json", {"valid": False, "issues": diagnostics})
        return _blocked("final_validation_blocked", diagnostics, package_records)
    _write_json(output / "candidate.json", workspace)
    _write_json(output / "candidate-revision.json", revision)
    _write_json(output / "package-records.json", {"packages": package_records})
    _write_json(output / "final-validation.json", {"valid": True, "issues": []})
    _write_json(output / "workspace-status.json", _workspace_status(True, len(packages), len(packages)))
    return {
        "valid": True,
        "status": "formal",
        "candidate": workspace,
        "revision": revision,
        "package_records": package_records,
        "issues": [],
    }


def _package_scope(
    *,
    package: Mapping[str, Any],
    workspace: Mapping[str, Any],
    revision: Mapping[str, Any],
    sequence: int,
    issue_id: str,
) -> dict[str, Any]:
    owned = [str(value) for value in package.get("owned_component_ids", [])]
    return {
        "schema_version": "text2ifc/change-scope/1.0",
        "scope_id": f"scope-package-{sequence}",
        "base_revision_id": revision["revision_id"],
        "source_issue_ids": [issue_id],
        "entity_ids": owned,
        "relationship_ids": [],
        "allowed_paths": {component_id: ["/"] for component_id in owned},
        "dependencies": [],
        "forbidden_ids": sorted(build_candidate_index(workspace)["component_hashes"]),
    }


def _apply_add_operations(
    workspace: Mapping[str, Any], operations: list[Mapping[str, Any]]
) -> dict[str, Any]:
    result = copy.deepcopy(dict(workspace))
    for operation in operations:
        value = copy.deepcopy(dict(operation["value"]))
        collection = "relationships" if operation["op"] == "add_relationship" else "entities"
        result[collection].append(value)
    result["entities"] = sorted(result["entities"], key=lambda item: item["id"])
    result["relationships"] = sorted(result["relationships"], key=lambda item: item["id"])
    return result


def _revision(
    *,
    candidate: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
    sequence: int,
    parent_revision_id: str | None,
    source_route: str,
    artifact: str,
) -> dict[str, Any]:
    index = build_candidate_index(candidate)
    return {
        "schema_version": "text2ifc/bim-json-revision/1.0",
        "revision_id": f"revision-{sequence:02d}",
        "sequence": sequence,
        "parent_revision_id": parent_revision_id,
        "candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected_facts),
        "component_hashes": index["component_hashes"],
        "source_route": source_route,
        "artifacts": {"candidate": artifact},
    }


def _workspace_status(formal: bool, applied: int, total: int) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/staged-workspace-status/1.0",
        "status": "formal" if formal else "partial_not_formal",
        "formal": formal,
        "applied_package_count": applied,
        "total_package_count": total,
        "compile_eligible": formal,
    }


def _blocked(
    status: str,
    issues: Any,
    package_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "valid": False,
        "status": status,
        "candidate": None,
        "revision": None,
        "package_records": package_records,
        "issues": [dict(issue) for issue in issues if isinstance(issue, Mapping)],
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _entity(
    entity_id: str,
    ifc_class: str,
    name: str,
    *,
    relative_to: str | None = None,
    origin: list[int | float] | None = None,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {"Name": name}
    if relative_to is not None:
        attributes["ObjectPlacement"] = {
            "relative_to": relative_to,
            "origin": origin or [0, 0, 0],
            "axis": [0, 0, 1],
            "ref_direction": [1, 0, 0],
        }
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "text2ifc/staged-skeleton"},
    }


def _aggregate(
    relationship_id: str, relating: str, related: list[str]
) -> dict[str, Any]:
    return {
        "id": relationship_id,
        "ifc_class": "IfcRelAggregates",
        "attributes": {
            "RelatingObject": relating,
            "RelatedObjects": related,
        },
        "provenance": {"source": "text2ifc/staged-skeleton"},
    }
