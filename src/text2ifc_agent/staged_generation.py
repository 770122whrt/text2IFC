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
        base_issues = [
            {
                "issue_id": issue_id,
                "actual_ref": f"entity:{package['owned_component_ids'][0]}#/" if package.get("owned_component_ids") else "package:/",
                "expected_fact_ref": f"expected-facts:/generation_package_manifest/packages/{sequence}",
                "evidence": f"Generate only components owned by {package_id}.",
            }
        ]
        retry_feedback: list[dict[str, Any]] = []
        stage: dict[str, Any] = {}
        gate: dict[str, Any] = {"valid": False, "issues": []}
        changeset: dict[str, Any] | None = None
        active_dir = package_dir
        attempt_count = 0
        for attempt_count in range(1, 4):
            active_dir = (
                package_dir
                if attempt_count == 1
                else package_dir / f"attempt-{attempt_count:02d}"
            )
            active_dir.mkdir(parents=True, exist_ok=True)
            stage = run_changeset_stage(
                provider=provider,
                output_dir=active_dir,
                case_id=case_id,
                call_index=sequence * 10 + attempt_count,
                user_request=user_request,
                conversation=conversation,
                design_brief=design_brief,
                expected_facts=expected_facts,
                candidate=workspace,
                base_revision=revision,
                scope=scope,
                issues=[*base_issues, *retry_feedback],
                trace_level=trace_level,
            )
            if stage.get("classification") == "draft" and stage.get("valid") is True:
                record = {
                    "package_id": package_id,
                    "artifact_dir": active_dir.relative_to(output).as_posix(),
                    "pre_apply_status": "partial_not_formal",
                    "response_id": stage.get("response_id"),
                    "classification": "draft",
                    "attempt_count": attempt_count,
                    "status": "draft_required",
                }
                package_records.append(record)
                _write_json(output / "package-records.json", {"packages": package_records})
                return _blocked("draft_required", stage.get("diagnostics", []), package_records)
            if stage.get("classification") != "changeset" or stage.get("valid") is not True:
                retry_feedback = _retry_issues(
                    issue_id, stage.get("diagnostics", []), "stage_contract"
                )
                if attempt_count < 3:
                    continue
                break
            changeset = _read_json(active_dir / "changeset.json")
            gate = validate_package_changeset(
                manifest=manifest,
                package_id=package_id,
                workspace=workspace,
                changeset=changeset,
            )
            _write_json(active_dir / "package-gate.json", gate)
            if gate["valid"]:
                break
            retry_feedback = _retry_issues(issue_id, gate["issues"], "package_gate")

        record = {
            "package_id": package_id,
            "artifact_dir": active_dir.relative_to(output).as_posix(),
            "pre_apply_status": "partial_not_formal",
            "response_id": stage.get("response_id"),
            "classification": stage.get("classification"),
            "attempt_count": attempt_count,
        }
        if changeset is None or not gate["valid"]:
            diagnostics = gate["issues"] or stage.get("diagnostics", [])
            package_records.append({**record, "status": "blocked"})
            _write_json(output / "package-records.json", {"packages": package_records})
            return _blocked("package_blocked", diagnostics, package_records)

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
            artifact=f"{active_dir.relative_to(output).as_posix()}/workspace-after.json",
        )
        _write_json(active_dir / "workspace-after.json", workspace)
        _write_json(active_dir / "revision.json", revision)
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


def _retry_issues(
    issue_id: str,
    diagnostics: Any,
    source: str,
) -> list[dict[str, Any]]:
    return [
        {
            "issue_id": issue_id,
            "actual_ref": str(diagnostic.get("path") or "package:/"),
            "expected_fact_ref": None,
            "evidence": (
                f"{source}:{diagnostic.get('code', 'UNKNOWN')}:"
                f"{diagnostic.get('message', 'Package output failed validation.')}"
            ),
        }
        for diagnostic in diagnostics
        if isinstance(diagnostic, Mapping)
    ]


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
