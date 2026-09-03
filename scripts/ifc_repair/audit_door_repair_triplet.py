"""Audit original/damaged/repaired IFC triplets without leaking Gold to repair."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell
import ifcopenshell.util.element


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.door_geometry import (  # noqa: E402
    measure_door_opening_alignment,
)
from text2ifc_ifc_repair.geometry import (  # noqa: E402
    product_geometry_bounds_in_host_mm,
)
from text2ifc_ifc_repair.occurrence_fidelity import (  # noqa: E402
    GENERIC_SCHEMA_VERSION,
    compare_occurrence_snapshots,
    snapshot_ifc_occurrence,
)
from text2ifc_ifc_repair.operations import (  # noqa: E402
    create_default_registry,
)
from text2ifc_ifc_repair.release_decision import (  # noqa: E402
    build_release_decision,
)


DOOR_OPERATION_TYPES = {
    "add_door_with_opening_to_wall",
    "fill_existing_opening_with_door",
}
WINDOW_OPERATION_TYPES = {"add_window_with_opening_to_wall"}


def audit_case(case_root: Path | str, *, write: bool = True) -> dict[str, Any]:
    root = Path(case_root).resolve()
    paths = _case_paths(root)
    source_hashes_before = {
        name: _sha256(path)
        for name, path in paths.items()
        if name in {"original", "damaged", "repaired"}
    }
    models, reopen_checks = _open_models(paths)
    changeset = _read_json(paths["changeset"])
    application = _read_json(paths["application"])
    production = _read_json(paths["evaluation"])
    manifest = _read_json(paths["manifest"])
    private_mapping_path = root / "private-benchmark-mapping.json"
    private_manifest = manifest
    if private_mapping_path.exists():
        private_mapping = _read_json(private_mapping_path)
        private_manifest = {
            **manifest,
            "damage": private_mapping.get("damage", {}),
        }
    request = paths["request"].read_text(encoding="utf-8").rstrip(
        "\r\n"
    )
    l0_checks = [
        *reopen_checks,
        _check(
            "L0_BASE_MODEL_FINGERPRINT",
            changeset.get("base_model_fingerprint")
            == source_hashes_before["damaged"],
            {
                "expected": source_hashes_before["damaged"],
                "actual": changeset.get("base_model_fingerprint"),
            },
        ),
        _check(
            "L0_SOURCE_REQUEST_HASH",
            changeset.get("source_request_hash")
            == _hash_text(request),
            {
                "expected": _hash_text(request),
                "actual": changeset.get("source_request_hash"),
            },
        ),
        _check_operation_identity(changeset, application),
        _check_relationship_integrity(models["repaired"]),
    ]
    boundary = (
        _read_json(paths["production_boundary"])
        if "production_boundary" in paths
        else None
    )
    l0_checks.append(
        _check_production_input_boundary(
            boundary=boundary,
            damaged_sha256=source_hashes_before["damaged"],
            request=request,
            changeset=changeset,
        )
    )
    source_hashes_after = {
        name: _sha256(path)
        for name, path in paths.items()
        if name in {"original", "damaged", "repaired"}
    }
    l0_checks.append(
        _check(
            "L0_SOURCE_FILES_UNCHANGED",
            source_hashes_before == source_hashes_after,
            {
                "before": source_hashes_before,
                "after": source_hashes_after,
            },
        )
    )
    l0_pass = all(item["status"] == "passed" for item in l0_checks)

    operation_results = {
        str(item["operation_id"]): item
        for item in application.get("operations", ())
    }
    registry = create_default_registry()
    production_checks = []
    blocking_findings = []
    for operation in changeset.get("operations", ()):
        operation_id = str(operation["operation_id"])
        applied = operation_results.get(operation_id, {})
        result = registry.dispatch(
            "postcondition_checker",
            operation,
            model=models["repaired"],
            application=applied.get("changes", {}),
        )
        production_checks.append(
            {
                "operation_id": operation_id,
                "operation_type": operation["operation_type"],
                **result,
            }
        )
        if not result.get("valid"):
            blocking_findings.extend(
                {
                    "code": str(issue.get("code", "L1_FAILURE")),
                    "operation_id": operation_id,
                    "message": str(issue.get("message", "L1 failure")),
                }
                for issue in result.get("issues", ())
            )

    effective_evaluation = copy.deepcopy(production)
    independent_by_id = {
        item["operation_id"]: item for item in production_checks
    }
    for operation in effective_evaluation.get("operations", ()):
        independent = independent_by_id.get(
            str(operation.get("operation_id"))
        )
        if independent is None or independent.get("valid") is not True:
            for level in operation.get("levels", ()):
                if level.get("level") == "L1":
                    level["status"] = "failed"
            operation["status"] = "failed"
    if blocking_findings:
        effective_evaluation["status"] = "failed"
        effective_evaluation["successful_artifact_publishable"] = False

    original_door_ids = _removed_door_ids(private_manifest)
    original_window_ids = _removed_window_ids(private_manifest)
    door_operations = [
        item
        for item in changeset.get("operations", ())
        if item.get("operation_type") in DOOR_OPERATION_TYPES
    ]
    repaired_door_ids = [
        _role_id(operation_results[str(item["operation_id"])], "door")
        for item in door_operations
    ]
    leakage = _ground_truth_leakage_check(
        request=request,
        changeset=changeset,
        private_deleted_ids=[
            *original_door_ids,
            *original_window_ids,
        ],
    )
    if not leakage["passed"]:
        blocking_findings.append(
            {
                "code": "PRIVATE_GROUND_TRUTH_LEAKAGE",
                "message": "Deleted Door identity leaked into production inputs.",
            }
        )
    private_objects = []
    fidelity_warnings = []
    for operation, original_id, repaired_id in zip(
        door_operations,
        original_door_ids,
        repaired_door_ids,
        strict=True,
    ):
        record = _private_door_comparison(
            operation=operation,
            original_model=models["original"],
            repaired_model=models["repaired"],
            original_id=original_id,
            repaired_id=repaired_id,
        )
        private_objects.append(record)
        if not record["private_exact_fidelity_pass"]:
            fidelity_warnings.append(
                {
                    "code": "PRIVATE_GROUND_TRUTH_FIDELITY_GAP",
                    "operation_id": operation["operation_id"],
                    "message": (
                        "Non-required original occurrence authoring facts "
                        "remain different; production Manifest still passes."
                    ),
                }
            )

    window_operations = [
        item
        for item in changeset.get("operations", ())
        if item.get("operation_type") in WINDOW_OPERATION_TYPES
    ]
    repaired_window_ids = [
        _role_id(operation_results[str(item["operation_id"])], "window")
        for item in window_operations
    ]
    for operation, original_id, repaired_id in zip(
        window_operations,
        original_window_ids,
        repaired_window_ids,
        strict=True,
    ):
        record = _private_window_comparison(
            operation=operation,
            original_model=models["original"],
            repaired_model=models["repaired"],
            original_id=original_id,
            repaired_id=repaired_id,
        )
        private_objects.append(record)
        if not record["private_exact_fidelity_pass"]:
            fidelity_warnings.append(
                {
                    "code": "PRIVATE_GROUND_TRUTH_FIDELITY_GAP",
                    "operation_id": operation["operation_id"],
                    "message": (
                        "Non-required original occurrence authoring facts "
                        "remain different; production Manifest still passes."
                    ),
                }
            )

    mutation = _mutation_comparison(
        original=models["original"],
        damaged=models["damaged"],
        removed_door_ids=original_door_ids,
    )
    production_diff = _production_comparison(
        damaged=models["damaged"],
        repaired=models["repaired"],
        application=application,
    )
    if production_diff["undeclared_added_roots"]:
        blocking_findings.append(
            {
                "code": "UNDECLARED_ADDED_ROOTS",
                "message": (
                    "Production repair created IFC Roots that were not "
                    "declared by any Applicator operation result."
                ),
                "global_ids": production_diff[
                    "undeclared_added_roots"
                ],
            }
        )
    l2_public_pass = _all_levels_pass(production, "L2")
    if not l2_public_pass:
        blocking_findings.append(
            {
                "code": "PRODUCTION_L2_FAILED",
                "message": "At least one operation failed public L2.",
            }
        )
    decision = build_release_decision(
        l0_pass=l0_pass,
        production_evaluation=effective_evaluation,
        blocking_findings=blocking_findings,
        warnings=fidelity_warnings,
        diagnostics=[
            {
                "code": "PRIVATE_EXACTNESS_INFORMATIONAL",
                "message": (
                    "Private Ground Truth gaps never participate in target "
                    "resolution or ChangeSet construction."
                ),
            }
        ],
    )
    evidence = {
        "schema_version": "text2ifc/door-repair-three-way-audit/0.1",
        "case_id": manifest.get("case_id", root.name),
        "source_hashes": source_hashes_after,
        "run_fingerprints": {
            "original_ifc_sha256": source_hashes_after["original"],
            "damaged_ifc_sha256": source_hashes_after["damaged"],
            "repaired_ifc_sha256": source_hashes_after["repaired"],
            "request_sha256": _hash_text(request),
            "changeset_sha256": _sha256(paths["changeset"]),
            "application_sha256": _sha256(paths["application"]),
            "production_evaluation_sha256": _sha256(paths["evaluation"]),
        },
        "artifact_paths": {
            role: path.as_posix() for role, path in paths.items()
        },
        "production_ground_truth_isolation": leakage,
        "l0": {"pass": l0_pass, "checks": l0_checks},
        "production_damaged_to_repaired": {
            "l1_pass": _all_checks_valid(production_checks),
            "l2_pass": l2_public_pass,
            "operation_checks": production_checks,
            "model_diff": production_diff,
        },
        "private_original_to_damaged": mutation,
        "private_original_to_repaired": {
            "objects": private_objects,
            "private_exact_fidelity_pass": all(
                item["private_exact_fidelity_pass"]
                for item in private_objects
            ),
        },
        "release_decision": decision,
    }
    if write:
        _write_json(root / "three-way-audit.json", evidence)
        _write_json(root / "release-decision.json", decision)
        (root / "AUDIT-REPORT.md").write_text(
            _render_report(evidence), encoding="utf-8"
        )
        if paths["manifest"].parent == root:
            refreshed_manifest = _read_json(paths["manifest"])
            if private_mapping_path.exists():
                refreshed_manifest["private_benchmark"] = {
                    "visibility": "post_repair_comparator_only",
                    "mapping_path": "private-benchmark-mapping.json",
                }
                refreshed_manifest["damage"] = private_mapping.get(
                    "damage", {}
                )
            artifacts = refreshed_manifest.setdefault("artifacts", {})
            for name in (
                "three-way-audit.json",
                "release-decision.json",
                "AUDIT-REPORT.md",
            ):
                artifact = root / name
                artifacts[name] = {
                    "path": name,
                    "sha256": _sha256(artifact),
                    "bytes": artifact.stat().st_size,
                }
            _write_json(paths["manifest"], refreshed_manifest)
    return evidence


def _private_door_comparison(
    *,
    operation: Mapping[str, Any],
    original_model: Any,
    repaired_model: Any,
    original_id: str,
    repaired_id: str,
) -> dict[str, Any]:
    original = original_model.by_guid(original_id)
    repaired = repaired_model.by_guid(repaired_id)
    original_opening = original.FillsVoids[0].RelatingOpeningElement
    repaired_opening = repaired.FillsVoids[0].RelatingOpeningElement
    original_snapshot = snapshot_ifc_occurrence(
        original_model,
        original_id,
        scope="door_occurrence",
        role="door",
    )
    repaired_snapshot = snapshot_ifc_occurrence(
        repaired_model,
        repaired_id,
        scope="door_occurrence",
        role="door",
    )
    required = {
        "door_occurrence:attribute:OverallWidth",
        "door_occurrence:attribute:OverallHeight",
        *(
            _assignment_occurrence_key(item)
            for item in operation.get("semantic_assignments", ())
            if _assignment_occurrence_key(item) is not None
        ),
    }
    occurrence = compare_occurrence_snapshots(
        expected=original_snapshot,
        actual=repaired_snapshot,
        authorization_ledger=required,
        required_fact_keys=required,
        complete_replication=False,
        geometry_relationship_success=(
            measure_door_opening_alignment(
                repaired, repaired_opening
            )["valid"]
        ),
        schema_version=GENERIC_SCHEMA_VERSION,
    )
    original_bounds = product_geometry_bounds_in_host_mm(
        original, original_opening
    )
    repaired_bounds = product_geometry_bounds_in_host_mm(
        repaired, repaired_opening
    )
    bounds_delta = {
        axis: [
            round(
                repaired_bounds[axis][index]
                - original_bounds[axis][index],
                6,
            )
            for index in (0, 1)
        ]
        for axis in ("x", "y", "z")
    }
    type_match = _type_id(original) == _type_id(repaired)
    host_match = _host_id(original) == _host_id(repaired)
    storey_match = _storey_id(original) == _storey_id(repaired)
    original_provenance = _semantic_provenance_summary(
        original, original_snapshot
    )
    repaired_provenance = _semantic_provenance_summary(
        repaired, repaired_snapshot
    )
    effective_material_match = (
        original_provenance["material"]["effective"]
        == repaired_provenance["material"]["effective"]
    )
    material_provenance_match = (
        original_provenance["material"]["sources"]
        == repaired_provenance["material"]["sources"]
    )
    geometry_match = all(
        abs(value) <= 1.0
        for values in bounds_delta.values()
        for value in values
    )
    exact_gap_count = sum(
        item["expected"] is not None
        and item["classification"] not in {"matched", "ownership_only"}
        for item in occurrence["details"]
    )
    return {
        "operation_id": operation["operation_id"],
        "object_class": "IfcDoor",
        "mapping": {
            "original_guid": original_id,
            "repaired_guid": repaired_id,
            "match_method": "mutation_manifest+application_role",
            "confidence": 1.0,
            "evidence": {
                "retained_opening_global_id": str(
                    repaired_opening.GlobalId
                )
            },
        },
        "geometry": {
            "original_alignment": measure_door_opening_alignment(
                original, original_opening
            ),
            "repaired_alignment": measure_door_opening_alignment(
                repaired, repaired_opening
            ),
            "opening_local_bounds_delta_mm": bounds_delta,
            "equivalent_within_1mm": geometry_match,
        },
        "semantics": {
            "type_match": type_match,
            "host_match": host_match,
            "storey_match": storey_match,
            "production_required_occurrence_facts": sorted(required),
            "occurrence_comparison": occurrence,
            "private_exact_gap_count": exact_gap_count,
            "original_provenance": original_provenance,
            "repaired_provenance": repaired_provenance,
            "effective_material_match": effective_material_match,
            "material_provenance_match": material_provenance_match,
        },
        "private_exact_fidelity_pass": bool(
            geometry_match
            and type_match
            and host_match
            and storey_match
            and exact_gap_count == 0
        ),
    }


def _private_window_comparison(
    *,
    operation: Mapping[str, Any],
    original_model: Any,
    repaired_model: Any,
    original_id: str,
    repaired_id: str,
) -> dict[str, Any]:
    original = original_model.by_guid(original_id)
    repaired = repaired_model.by_guid(repaired_id)
    original_opening = original.FillsVoids[0].RelatingOpeningElement
    repaired_opening = repaired.FillsVoids[0].RelatingOpeningElement
    original_wall = original_opening.VoidsElements[0].RelatingBuildingElement
    repaired_wall = repaired_opening.VoidsElements[0].RelatingBuildingElement
    original_snapshot = snapshot_ifc_occurrence(
        original_model,
        original_id,
        scope="window_occurrence",
        role="window",
    )
    repaired_snapshot = snapshot_ifc_occurrence(
        repaired_model,
        repaired_id,
        scope="window_occurrence",
        role="window",
    )
    required = {
        "window_occurrence:attribute:OverallWidth",
        "window_occurrence:attribute:OverallHeight",
        *(
            _assignment_occurrence_key_for_scope(
                item, scope="window_occurrence"
            )
            for item in operation.get("semantic_assignments", ())
            if _assignment_occurrence_key_for_scope(
                item, scope="window_occurrence"
            )
            is not None
        ),
    }
    original_bounds = product_geometry_bounds_in_host_mm(
        original, original_wall
    )
    repaired_bounds = product_geometry_bounds_in_host_mm(
        repaired, repaired_wall
    )
    bounds_delta = {
        axis: [
            round(
                repaired_bounds[axis][index]
                - original_bounds[axis][index],
                6,
            )
            for index in (0, 1)
        ]
        for axis in ("x", "y", "z")
    }
    type_match = _type_id(original) == _type_id(repaired)
    host_match = str(original_wall.GlobalId) == str(repaired_wall.GlobalId)
    storey_match = _storey_id(original) == _storey_id(repaired)
    original_provenance = _semantic_provenance_summary(
        original, original_snapshot
    )
    repaired_provenance = _semantic_provenance_summary(
        repaired, repaired_snapshot
    )
    effective_material_match = (
        original_provenance["material"]["effective"]
        == repaired_provenance["material"]["effective"]
    )
    material_provenance_match = (
        original_provenance["material"]["sources"]
        == repaired_provenance["material"]["sources"]
    )
    geometry_match = all(
        abs(value) <= 1.0
        for values in bounds_delta.values()
        for value in values
    )
    occurrence = compare_occurrence_snapshots(
        expected=original_snapshot,
        actual=repaired_snapshot,
        authorization_ledger=required,
        required_fact_keys=required,
        complete_replication=False,
        geometry_relationship_success=geometry_match,
        schema_version=GENERIC_SCHEMA_VERSION,
    )
    exact_gap_count = sum(
        item["expected"] is not None
        and item["classification"] not in {"matched", "ownership_only"}
        for item in occurrence["details"]
    )
    return {
        "operation_id": operation["operation_id"],
        "object_class": "IfcWindow",
        "mapping": {
            "original_guid": original_id,
            "repaired_guid": repaired_id,
            "match_method": "mutation_manifest+application_role",
            "confidence": 1.0,
            "evidence": {
                "original_opening_global_id": str(
                    original_opening.GlobalId
                ),
                "repaired_opening_global_id": str(
                    repaired_opening.GlobalId
                ),
                "host_wall_global_id": str(repaired_wall.GlobalId),
            },
        },
        "geometry": {
            "opening_local_bounds_delta_mm": bounds_delta,
            "equivalent_within_1mm": geometry_match,
        },
        "semantics": {
            "type_match": type_match,
            "host_match": host_match,
            "storey_match": storey_match,
            "production_required_occurrence_facts": sorted(required),
            "occurrence_comparison": occurrence,
            "private_exact_gap_count": exact_gap_count,
            "original_provenance": original_provenance,
            "repaired_provenance": repaired_provenance,
            "effective_material_match": effective_material_match,
            "material_provenance_match": material_provenance_match,
        },
        "private_exact_fidelity_pass": bool(
            geometry_match
            and type_match
            and host_match
            and storey_match
            and exact_gap_count == 0
        ),
    }


def _semantic_provenance_summary(
    element: Any,
    snapshot: Any,
) -> dict[str, Any]:
    occurrence_psets = [
        key
        for key, fact in snapshot.facts.items()
        if ":pset:" in key and fact.ownership == "occurrence_direct"
    ]
    inherited_psets = [
        key
        for key, fact in snapshot.facts.items()
        if ":pset:" in key and fact.ownership == "type_inherited"
    ]
    quantities = [
        key for key in snapshot.facts if ":quantity:" in key
    ]
    direct_materials = [
        relation.RelatingMaterial
        for relation in element.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    element_type = ifcopenshell.util.element.get_type(element)
    type_materials = (
        []
        if element_type is None
        else [
            relation.RelatingMaterial
            for relation in element_type.HasAssociations
            if relation.is_a("IfcRelAssociatesMaterial")
        ]
    )
    effective = ifcopenshell.util.element.get_material(
        element, should_inherit=True
    )
    sources = []
    if direct_materials:
        sources.append("occurrence")
    if type_materials:
        sources.append("type")
    return {
        "occurrence_pset_fact_count": len(occurrence_psets),
        "occurrence_pset_fact_keys": occurrence_psets,
        "type_inherited_pset_fact_count": len(inherited_psets),
        "type_inherited_pset_fact_keys": inherited_psets,
        "quantity_fact_count": len(quantities),
        "quantity_fact_keys": quantities,
        "material": {
            "effective": _material_identity(effective),
            "sources": sources,
            "occurrence_assignments": [
                _material_identity(item) for item in direct_materials
            ],
            "type_assignments": [
                _material_identity(item) for item in type_materials
            ],
        },
    }


def _material_identity(material: Any) -> Any:
    if material is None:
        return None
    names = sorted(_material_names(material))
    return {
        "ifc_class": material.is_a(),
        "names": names,
    }


def _material_names(material: Any) -> set[str]:
    names = set()
    name = getattr(material, "Name", None)
    if name is not None:
        names.add(str(name))
    for attribute in (
        "Materials",
        "MaterialLayers",
        "MaterialProfiles",
        "MaterialConstituents",
    ):
        for child in getattr(material, attribute, ()) or ():
            nested = getattr(child, "Material", child)
            names.update(_material_names(nested))
    layer_set = getattr(material, "ForLayerSet", None)
    if layer_set is not None:
        names.update(_material_names(layer_set))
    return names


def _mutation_comparison(
    *,
    original: Any,
    damaged: Any,
    removed_door_ids: list[str],
) -> dict[str, Any]:
    original_ids = _root_ids(original)
    damaged_ids = _root_ids(damaged)
    return {
        "private_only": True,
        "removed_root_count": len(original_ids - damaged_ids),
        "added_root_count": len(damaged_ids - original_ids),
        "removed_door_ids": removed_door_ids,
        "all_expected_doors_removed": all(
            original.by_guid(item) is not None
            and _by_guid_or_none(damaged, item) is None
            for item in removed_door_ids
        ),
        "door_count_delta": (
            len(damaged.by_type("IfcDoor"))
            - len(original.by_type("IfcDoor"))
        ),
        "window_count_delta": (
            len(damaged.by_type("IfcWindow"))
            - len(original.by_type("IfcWindow"))
        ),
        "opening_count_delta": (
            len(damaged.by_type("IfcOpeningElement"))
            - len(original.by_type("IfcOpeningElement"))
        ),
        "entity_count_delta": len(list(damaged)) - len(list(original)),
    }


def _production_comparison(
    *,
    damaged: Any,
    repaired: Any,
    application: Mapping[str, Any],
) -> dict[str, Any]:
    damaged_ids = _root_ids(damaged)
    repaired_ids = _root_ids(repaired)
    declared_created = {
        str(item["global_id"])
        for operation in application.get("operations", ())
        for item in operation.get("changes", {}).get("created", ())
        if item.get("global_id")
    }
    added = repaired_ids - damaged_ids
    return {
        "added_root_count": len(added),
        "removed_root_count": len(damaged_ids - repaired_ids),
        "declared_created_root_count": len(declared_created),
        "undeclared_added_roots": sorted(added - declared_created),
        "door_count_delta": (
            len(repaired.by_type("IfcDoor"))
            - len(damaged.by_type("IfcDoor"))
        ),
        "window_count_delta": (
            len(repaired.by_type("IfcWindow"))
            - len(damaged.by_type("IfcWindow"))
        ),
        "opening_count_delta": (
            len(repaired.by_type("IfcOpeningElement"))
            - len(damaged.by_type("IfcOpeningElement"))
        ),
        "entity_count_delta": len(list(repaired)) - len(list(damaged)),
    }


def _case_paths(root: Path) -> dict[str, Path]:
    curated = (root / "01-original.ifc").is_file()
    paths = {
        "original": root / ("01-original.ifc" if curated else "original.ifc"),
        "damaged": root / ("02-damaged.ifc" if curated else "damaged.ifc"),
        "repaired": root / ("03-repaired.ifc" if curated else "repaired.ifc"),
        "request": root
        / ("input/request.txt" if curated else "request.txt"),
        "changeset": root
        / (
            "changeset/bound-changeset.json"
            if curated
            else "changeset.json"
        ),
        "application": root
        / (
            "validation/application.json"
            if curated
            else "application.json"
        ),
        "evaluation": root
        / (
            "validation/production-evaluation.json"
            if curated
            else "evaluation.json"
        ),
        "manifest": root
        / (
            "validation/source-run-manifest.json"
            if curated
            else "manifest.json"
        ),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"DOOR_AUDIT_INPUT_MISSING:{missing[0]}")
    boundary = root / (
        "validation/production-boundary.json"
        if curated
        else "production-boundary.json"
    )
    if boundary.is_file():
        paths["production_boundary"] = boundary
    return paths


def _open_models(
    paths: Mapping[str, Path],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    models = {}
    checks = []
    for role in ("original", "damaged", "repaired"):
        try:
            model = ifcopenshell.open(str(paths[role]))
            passed = model.schema == "IFC2X3"
            evidence = {
                "path": paths[role].as_posix(),
                "schema": model.schema,
            }
            models[role] = model
        except Exception as error:
            passed = False
            evidence = {"error": f"{type(error).__name__}:{error}"}
        checks.append(_check(f"L0_REOPEN_{role.upper()}", passed, evidence))
    if len(models) != 3:
        raise ValueError("DOOR_AUDIT_IFC_REOPEN_FAILED")
    return models, checks


def _check_operation_identity(
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
) -> dict[str, Any]:
    expected = [
        str(item["operation_id"])
        for item in changeset.get("operations", ())
    ]
    actual = [
        str(item["operation_id"])
        for item in application.get("operations", ())
    ]
    return _check(
        "L0_OPERATION_IDENTITY",
        bool(application.get("valid"))
        and bool(application.get("published"))
        and expected == actual,
        {"expected": expected, "actual": actual},
    )


def _check_production_input_boundary(
    *,
    boundary: Mapping[str, Any] | None,
    damaged_sha256: str,
    request: str,
    changeset: Mapping[str, Any],
) -> dict[str, Any]:
    expected_changeset_hash = _hash_text(
        json.dumps(
            changeset,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    passed = (
        boundary is not None
        and boundary.get("schema_version")
        in {
            "text2ifc/production-input-boundary/0.1",
            "text2ifc/production-input-boundary/0.2",
        }
        and boundary.get("ifc_inputs") == ["damaged_ifc_path"]
        and boundary.get("original_ifc_supplied") is False
        and boundary.get("mutation_manifest_supplied") is False
        and boundary.get("deleted_object_ids_supplied") is False
        and (
            boundary.get("schema_version")
            != "text2ifc/production-input-boundary/0.2"
            or (
                boundary.get(
                    "private_comparator_available_during_repair"
                )
                is False
                and boundary.get("request_inputs")
                == ["public_request_bundle"]
            )
        )
        and boundary.get("damaged_ifc_sha256") == damaged_sha256
        and boundary.get("request_sha256") == _hash_text(request)
        and boundary.get("changeset_canonical_sha256")
        == expected_changeset_hash
    )
    return _check(
        "L0_PRODUCTION_INPUT_BOUNDARY",
        passed,
        {
            "boundary": boundary,
            "expected_damaged_ifc_sha256": damaged_sha256,
            "expected_request_sha256": _hash_text(request),
            "expected_changeset_canonical_sha256": expected_changeset_hash,
        },
    )


def _check_relationship_integrity(model: Any) -> dict[str, Any]:
    duplicate_openings = [
        str(opening.GlobalId)
        for opening in model.by_type("IfcOpeningElement")
        if len(opening.HasFillings) > 1
    ]
    broken_fills = [
        relation.id()
        for relation in model.by_type("IfcRelFillsElement")
        if relation.RelatingOpeningElement is None
        or relation.RelatedBuildingElement is None
    ]
    broken_voids = [
        relation.id()
        for relation in model.by_type("IfcRelVoidsElement")
        if relation.RelatingBuildingElement is None
        or relation.RelatedOpeningElement is None
    ]
    return _check(
        "L0_RELATIONSHIP_INTEGRITY",
        not duplicate_openings and not broken_fills and not broken_voids,
        {
            "duplicate_fill_openings": duplicate_openings,
            "broken_fill_relationship_steps": broken_fills,
            "broken_void_relationship_steps": broken_voids,
        },
    )


def _ground_truth_leakage_check(
    *,
    request: str,
    changeset: Mapping[str, Any],
    private_deleted_ids: list[str],
) -> dict[str, Any]:
    public_payload = request + json.dumps(
        changeset, ensure_ascii=False, sort_keys=True
    )
    leaked = [
        global_id
        for global_id in private_deleted_ids
        if global_id in public_payload
    ]
    return {
        "passed": not leaked,
        "checked_private_deleted_object_count": len(private_deleted_ids),
        "leaked_deleted_object_ids": leaked,
        "production_inputs": [
            "02-damaged.ifc",
            "request.txt",
            "bound ChangeSet",
            "authorized surviving IFC evidence",
        ],
        "private_comparator_started_after_repair": True,
    }


def _removed_door_ids(manifest: Mapping[str, Any]) -> list[str]:
    damage = manifest.get("damage", {})
    removed = list(damage.get("removed_doors", ()))
    if not removed and damage.get("door"):
        removed = [damage["door"]]
    values = [str(item["global_id"]) for item in removed]
    if not values:
        raise ValueError("PRIVATE_DOOR_MAPPING_MISSING")
    return values


def _removed_window_ids(manifest: Mapping[str, Any]) -> list[str]:
    removed = list(manifest.get("damage", {}).get("removed_windows", ()))
    return [str(item["global_id"]) for item in removed]


def _assignment_occurrence_key(
    assignment: Mapping[str, Any],
) -> str | None:
    return _assignment_occurrence_key_for_scope(
        assignment, scope="door_occurrence"
    )


def _assignment_occurrence_key_for_scope(
    assignment: Mapping[str, Any],
    *,
    scope: str,
) -> str | None:
    key = str(assignment.get("fact_key", ""))
    if key.startswith(("pset:", "quantity:", "attribute:")):
        return f"{scope}:{key}"
    return None


def _role_id(operation_result: Mapping[str, Any], role: str) -> str:
    matches = [
        str(item["global_id"])
        for item in operation_result.get("changes", {}).get("created", ())
        if item.get("role") == role
    ]
    if len(matches) != 1:
        raise ValueError(f"APPLICATION_ROLE_MAPPING_INVALID:{role}")
    return matches[0]


def _type_id(element: Any) -> str | None:
    value = ifcopenshell.util.element.get_type(element)
    return None if value is None else str(value.GlobalId)


def _host_id(element: Any) -> str | None:
    hosts = {
        str(void.RelatingBuildingElement.GlobalId)
        for fill in element.FillsVoids
        for void in fill.RelatingOpeningElement.VoidsElements
    }
    return next(iter(hosts)) if len(hosts) == 1 else None


def _storey_id(element: Any) -> str | None:
    value = ifcopenshell.util.element.get_container(
        element, ifc_class="IfcBuildingStorey"
    )
    return None if value is None else str(value.GlobalId)


def _root_ids(model: Any) -> set[str]:
    return {
        str(entity.GlobalId)
        for entity in model.by_type("IfcRoot")
        if getattr(entity, "GlobalId", None)
    }


def _by_guid_or_none(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _all_checks_valid(checks: list[Mapping[str, Any]]) -> bool:
    return bool(checks) and all(item.get("valid") is True for item in checks)


def _all_levels_pass(
    evaluation: Mapping[str, Any],
    level_name: str,
) -> bool:
    operations = evaluation.get("operations")
    if not isinstance(operations, list) or not operations:
        return False
    for operation in operations:
        matches = [
            item
            for item in operation.get("levels", ())
            if item.get("level") == level_name
        ]
        if len(matches) != 1 or matches[0].get("status") != "passed":
            return False
    return True


def _check(
    code: str,
    passed: bool,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "code": code,
        "status": "passed" if passed else "failed",
        "evidence": dict(evidence),
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _render_report(evidence: Mapping[str, Any]) -> str:
    release = evidence["release_decision"]
    production = evidence["production_damaged_to_repaired"]
    mutation = evidence["private_original_to_damaged"]
    private = evidence["private_original_to_repaired"]
    mapping_rows = []
    geometry_rows = []
    relation_rows = []
    semantic_rows = []
    for item in private["objects"]:
        geometry = item["geometry"]
        semantics = item["semantics"]
        mapping = item["mapping"]
        mapping_rows.append(
            f"| {item['object_class']} | {item['operation_id']} | "
            f"`{mapping['original_guid']}` | `{mapping['repaired_guid']}` | "
            f"{mapping['match_method']} | {mapping['confidence']:.1f} |"
        )
        alignment = geometry.get("repaired_alignment")
        geometry_rows.append(
            f"| {item['object_class']} | {item['operation_id']} | "
            + (
                f"{alignment['projected_overlap_ratio']:.3f} | "
                f"{alignment['nominal_center_deviation_mm']:.3f} | "
                f"{alignment['axis_deviation_degrees']:.3f} | "
                if alignment is not None
                else "不适用 | 不适用 | 不适用 | "
            )
            + (
                "通过"
                if geometry["equivalent_within_1mm"]
                else "失败"
            )
            + " |"
        )
        relation_rows.append(
            f"| {item['object_class']} | {item['operation_id']} | "
            f"{'通过' if semantics['host_match'] else '失败'} | "
            f"{'通过' if semantics['storey_match'] else '失败'} | "
            f"{'通过' if semantics['type_match'] else '失败'} |"
        )
        original_provenance = semantics["original_provenance"]
        repaired_provenance = semantics["repaired_provenance"]
        semantic_rows.append(
            f"| {item['object_class']} | {item['operation_id']} | "
            f"{original_provenance['occurrence_pset_fact_count']}→"
            f"{repaired_provenance['occurrence_pset_fact_count']} | "
            f"{original_provenance['quantity_fact_count']}→"
            f"{repaired_provenance['quantity_fact_count']} | "
            f"{'通过' if semantics['effective_material_match'] else '失败'} | "
            f"{'通过' if semantics['material_provenance_match'] else '变化'} | "
            f"{semantics['private_exact_gap_count']} |"
        )
    blockers = release["blocking_findings"]
    warnings = release["warnings"]
    l0_rows = [
        f"| {item['code']} | {item['status']} |"
        for item in evidence["l0"]["checks"]
    ]
    blocker_lines = (
        ["- 无。"]
        if not blockers
        else [
            f"- `{item.get('code')}`"
            + (
                f" / `{item.get('operation_id')}`"
                if item.get("operation_id")
                else ""
            )
            + f"：{item.get('message', '')}"
            for item in blockers
        ]
    )
    warning_lines = (
        ["- 无。"]
        if not warnings
        else [
            f"- `{item.get('code')}`"
            + (
                f" / `{item.get('operation_id')}`"
                if item.get("operation_id")
                else ""
            )
            + f"：{item.get('message', '')}"
            for item in warnings
        ]
    )
    fingerprints = evidence["run_fingerprints"]
    fingerprint_lines = [
        f"- `{key}`：`{value}`" for key, value in fingerprints.items()
    ]
    artifact_lines = [
        f"- `{role}`：`{path}`"
        for role, path in evidence["artifact_paths"].items()
    ]
    return (
        f"# {evidence['case_id']} Door 三方审计报告\n\n"
        "## 1. 最终发布结论\n\n"
        f"- L0：`{release['l0_pass']}`\n"
        f"- L1：`{release['l1_pass']}`\n"
        f"- L2（生产 Semantic Manifest）：`{release['l2_pass']}`\n"
        f"- 可发布：`{release['publishable']}`\n"
        f"- 阻塞项：`{len(blockers)}`\n"
        f"- 私有 Ground Truth 忠实度警告：`{len(warnings)}`\n\n"
        "生产修复只使用 damaged IFC、用户请求、Bound ChangeSet 与仍存活的"
        " IFC 事实。original IFC 和被删除对象 GUID 仅在修复完成后进入本"
        "私有 comparator。\n\n"
        "## 2. Mutation audit：original → damaged（私有）\n\n"
        f"- Door 数量变化：`{mutation['door_count_delta']}`\n"
        f"- Window 数量变化：`{mutation['window_count_delta']}`\n"
        f"- Opening 数量变化：`{mutation['opening_count_delta']}`\n"
        f"- Root 删除/新增：`{mutation['removed_root_count']}` / "
        f"`{mutation['added_root_count']}`\n"
        f"- Manifest 中的 Door 均被删除："
        f"`{mutation['all_expected_doors_removed']}`\n\n"
        "这部分只证明 benchmark 损伤范围，不参与 Target、Type、ChangeSet "
        "或 Applicator 决策。\n\n"
        "## 3. Production repair audit：damaged → repaired\n\n"
        f"- operation 数：`{len(production['operation_checks'])}`\n"
        f"- L1 全部通过：`{production['l1_pass']}`\n"
        f"- L2 全部通过：`{production['l2_pass']}`\n"
        f"- Door/Window/Opening 数量变化："
        f"`{production['model_diff']['door_count_delta']}` / "
        f"`{production['model_diff']['window_count_delta']}` / "
        f"`{production['model_diff']['opening_count_delta']}`\n"
        f"- 未声明新增 Root："
        f"`{len(production['model_diff']['undeclared_added_roots'])}`\n"
        f"- Ground Truth 泄漏检查："
        f"`{evidence['production_ground_truth_isolation']['passed']}`\n\n"
        "### L0 检查\n\n"
        "| 检查 | 状态 |\n|---|---|\n"
        + "\n".join(l0_rows)
        + "\n\n"
        "## 4. Private fidelity：original → repaired\n\n"
        f"- 完整 authoring exactness："
        f"`{private['private_exact_fidelity_pass']}`\n"
        f"- 成功映射对象数：`{len(private['objects'])}`\n"
        f"- 非阻塞 fidelity warning：`{len(warnings)}`\n\n"
        "私有 comparator 只解释修复质量；它无权改变 production release "
        "facts，也不会把缺失原值回灌到修复链路。\n\n"
        "## 5. 逐对象语义映射\n\n"
        "| 类别 | Operation | Original GUID | Repaired GUID | 方法 | 置信度 |\n"
        "|---|---|---|---|---|---:|\n"
        + "\n".join(mapping_rows)
        + "\n\n"
        "## 6. 几何与 placement 证据\n\n"
        "| 类别 | Operation | Opening 覆盖率 | 名义中心偏差 mm | 轴偏差 ° | "
        "原始世界几何≤1mm |\n"
        "|---|---|---:|---:|---:|---|\n"
        + "\n".join(geometry_rows)
        + "\n\n"
        "Door 的覆盖率、名义中心和轴向来自 repaired IFC 的 Opening 局部坐标"
        "测量；“原始世界几何≤1mm”只来自修复后的私有 comparator。\n\n"
        "## 7. Host / Opening / Fill / Storey / Type\n\n"
        "| 类别 | Operation | Host | Storey | Type |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(relation_rows)
        + "\n\n"
        "Door production operation 还逐项验证恰好一条 fill、Opening 恰好 void "
        "一个 Wall、唯一 Storey containment 与唯一 Type 关系；完整机器证据见 "
        "`three-way-audit.json`。\n\n"
        "## 8. Pset / Qto / Material provenance\n\n"
        "| 类别 | Operation | occurrence Pset facts | Qto facts | "
        "effective material | provenance | 私有差异数 |\n"
        "|---|---|---:|---:|---|---|---:|\n"
        + "\n".join(semantic_rows)
        + "\n\n"
        "原模型中未被用户请求或 Semantic Manifest 授权的 occurrence Pset/"
        "Qto 差异保留为私有 fidelity warning；它们不会被伪装成 exact "
        "restoration，也不会把 private Ground Truth 泄漏回生产修复。\n\n"
        "## 9. 非目标保全\n\n"
        f"- damaged→repaired 新增 Root："
        f"`{production['model_diff']['added_root_count']}`\n"
        f"- 声明新增 Root："
        f"`{production['model_diff']['declared_created_root_count']}`\n"
        f"- damaged→repaired 删除 Root："
        f"`{production['model_diff']['removed_root_count']}`\n"
        f"- 未声明新增 Root："
        f"`{len(production['model_diff']['undeclared_added_roots'])}`\n"
        "- 共享 Type 不可变性与其他 Root/关系保全由 production full-model "
        "comparator 和 operation scope gate 负责。\n\n"
        "## 10. 阻塞项与警告\n\n"
        "### 阻塞项\n\n"
        + "\n".join(blocker_lines)
        + "\n\n### 警告\n\n"
        + "\n".join(warning_lines)
        + "\n\n"
        "## 11. 指纹与产物路径\n\n"
        "### 运行指纹\n\n"
        + "\n".join(fingerprint_lines)
        + "\n\n### 输入产物\n\n"
        + "\n".join(artifact_lines)
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    result = audit_case(args.case_root, write=not args.no_write)
    print(
        json.dumps(
            result["release_decision"],
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["release_decision"]["publishable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
