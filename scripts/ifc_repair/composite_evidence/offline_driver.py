"""Offline (zero-Provider) composite driver for the Composite Repair Milestone.

Builds a BOUND changeset for each frozen composite case directly from the
frozen public bindings (deterministic target resolution + generated Type
authority, exactly the deterministic policy path Stage 2 uses), applies it
through the production ``apply_changeset``, and returns the artifacts the
composite proof and artifact-delta generators need.

This module is used for:

* the composite Proof extension's focused zero-provider tests (Section 8);
* the offline full-chain preflight (Section 10.1);
* preservation semantics verification (Section 9).

It is NOT a substitute for genuine Provider execution; offline outputs are
never reported as live evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.resolution_flow import (
    ResolvedOperation,
    generated_type_authority,
)

ROOT = Path(__file__).resolve().parents[3]
FREEZE_PATH = (
    ROOT
    / "docs"
    / "validation"
    / "repair-composite-milestone"
    / "composite-acceptance-freeze.json"
)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def load_freeze() -> dict[str, Any]:
    with FREEZE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _wall_orientation(model: Any, wall: Any) -> str:
    """World orientation of a wall, computed like ``WallIndexAdapter``."""

    import math

    import ifcopenshell.util.placement as placement

    from text2ifc_ifc_repair.geometry import straight_wall_axis
    from text2ifc_ifc_repair.index_adapters import _readable_orientation

    start, end = straight_wall_axis(wall)
    try:
        matrix = placement.get_local_placement(wall.ObjectPlacement)
        world_start = matrix @ [*start, 1.0]
        world_end = matrix @ [*end, 1.0]
        world_delta = [world_end[i] - world_start[i] for i in range(3)]
    except Exception:
        world_delta = [end[i] - start[i] for i in range(3)]
    length = math.sqrt(sum(value * value for value in world_delta))
    if length <= 0.0:
        raise ValueError("COMPOSITE_WALL_DIRECTION_INVALID")
    direction = [value / length for value in world_delta]
    return _readable_orientation(direction)


def _resolve_wall_global_id(model: Any, wall_query: Mapping[str, Any]) -> str:
    """Deterministically resolve the frozen public wall binding."""

    from text2ifc_ifc_repair.geometry import (
        straight_wall_axis,
        wall_dimensions_mm,
    )
    from text2ifc_ifc_repair.indexer import _element_storey
    from text2ifc_ifc_repair.index_adapters import _readable_orientation

    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
    matches = []
    for wall in model.by_type("IfcWall"):
        matched = True
        if wall_query.get("direction"):
            try:
                orientation = _wall_orientation(model, wall)
            except ValueError as error:
                if str(error) == "UNSUPPORTED_WALL_GEOMETRY":
                    matched = False
                    orientation = None
                else:
                    raise
            if orientation != str(wall_query["direction"]):
                matched = False
        for constraint in wall_query.get("geometry_constraints", ()):
            field = str(constraint["field"])
            if field == "storey_elevation_mm":
                storey = _element_storey(wall)
                if storey is None or storey.Elevation is None:
                    matched = False
                    break
                value = float(storey.Elevation) * scale
            else:
                try:
                    dims = wall_dimensions_mm(wall)
                except Exception:
                    matched = False
                    break
                key = {
                    "wall_length_mm": "length",
                    "wall_height_mm": "height",
                    "wall_thickness_mm": "thickness",
                }[field]
                value = float(dims[key])
            if abs(value - float(constraint["value"])) > float(
                constraint["tolerance_mm"]
            ):
                matched = False
                break
        if matched:
            matches.append(str(wall.GlobalId))
    if len(matches) != 1:
        raise ValueError(
            f"COMPOSITE_WALL_BINDING_AMBIGUOUS:{len(matches)}"
        )
    return matches[0]


def _resolve_opening_global_id(model: Any, opening_query: Mapping[str, Any]) -> str:
    """Deterministically resolve the frozen public opening binding."""

    from text2ifc_ifc_repair.geometry import (
        opening_dimensions_mm,
        opening_position_in_wall_mm,
    )

    matches = []
    for opening in model.by_type("IfcOpeningElement"):
        host_ids = [
            str(rel.RelatingBuildingElement.GlobalId)
            for rel in opening.VoidsElements
        ]
        fillings = [
            str(rel.RelatedBuildingElement.GlobalId)
            for rel in opening.HasFillings
        ]
        if len(host_ids) != 1 or fillings:
            continue
        host = opening.VoidsElements[0].RelatingBuildingElement
        matched = True
        for constraint in opening_query.get("geometry_constraints", ()):
            field = str(constraint["field"])
            try:
                if field in {
                    "opening_width_mm": "width",
                    "opening_height_mm": "height",
                    "opening_depth_mm": "depth",
                }:
                    dims = opening_dimensions_mm(opening)
                    key = {
                        "opening_width_mm": "width",
                        "opening_height_mm": "height",
                        "opening_depth_mm": "depth",
                    }[field]
                    value = float(dims[key])
                else:
                    position = opening_position_in_wall_mm(opening, host)
                    key = {
                        "opening_center_offset_mm": "center_offset",
                        "opening_sill_height_mm": "sill_height",
                    }[field]
                    value = float(position[key])
            except Exception:
                matched = False
                break
            if abs(value - float(constraint["value"])) > float(
                constraint["tolerance_mm"]
            ):
                matched = False
                break
        if matched:
            matches.append(str(opening.GlobalId))
    if len(matches) != 1:
        raise ValueError(
            f"COMPOSITE_OPENING_BINDING_AMBIGUOUS:{len(matches)}"
        )
    return matches[0]


def _structural_type_assignment(
    *,
    family: str,
    operation: Mapping[str, Any],
    request_hash: str,
    model_hash: str,
) -> dict[str, Any]:
    from text2ifc_ifc_repair.operations.beam import beam_operation_definition
    from text2ifc_ifc_repair.operations.column import column_operation_definition

    definition = (
        beam_operation_definition()
        if family == "beam"
        else column_operation_definition()
    )
    storey_id = str(operation["target"]["storey_global_id"])
    resolved = ResolvedOperation(
        operation_id=str(operation["operation_id"]),
        operation_type=f"add_{family}",
        target_global_id=storey_id,
        scope_ids=(storey_id,),
        evidence_pointers=(f"request:/operations/{operation['operation_id']}",),
        parameters=dict(operation["parameters"]),
        context={},
    )
    return _type_assignment_from_authority(
        definition=definition,
        operation=operation,
        request_hash=request_hash,
        model_hash=model_hash,
        resolved_operation=resolved,
        scope=f"{family}_occurrence",
    )


def _hosted_type_assignment(
    *,
    operation: Mapping[str, Any],
    request_hash: str,
    model_hash: str,
) -> dict[str, Any]:
    """Generated Type authority for a door/window operation (hosted families)."""

    from text2ifc_ifc_repair.operations.door import (
        add_door_operation_definition,
        fill_door_operation_definition,
    )
    from text2ifc_ifc_repair.operations.window import window_operation_definition

    operation_type = str(operation["operation_type"])
    definition = {
        "fill_existing_opening_with_door": fill_door_operation_definition,
        "add_door_with_opening_to_wall": add_door_operation_definition,
        "add_window_with_opening_to_wall": window_operation_definition,
    }[operation_type]()
    target_key = (
        "opening_global_id"
        if operation_type == "fill_existing_opening_with_door"
        else "wall_global_id"
    )
    resolved = ResolvedOperation(
        operation_id=str(operation["operation_id"]),
        operation_type=operation_type,
        target_global_id=str(operation["target"][target_key]),
        scope_ids=(str(operation["target"][target_key]),),
        evidence_pointers=(f"request:/operations/{operation['operation_id']}",),
        parameters=dict(operation["parameters"]),
        context={},
    )
    semantic_role = str(definition.evaluation_policy.semantic_role)
    return _type_assignment_from_authority(
        definition=definition,
        operation=operation,
        request_hash=request_hash,
        model_hash=model_hash,
        resolved_operation=resolved,
        scope=f"{semantic_role}_occurrence",
    )


def _type_assignment_from_authority(
    *,
    definition: Any,
    operation: Mapping[str, Any],
    request_hash: str,
    model_hash: str,
    resolved_operation: ResolvedOperation,
    scope: str,
) -> dict[str, Any]:
    operation_id = str(operation["operation_id"])
    authority = generated_type_authority(
        definition,
        operation_id=operation_id,
        request_hash=request_hash,
        model_fingerprint=model_hash,
        resolved_operation=resolved_operation,
    )
    return {
        "operation_id": operation_id,
        "scope": scope,
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": authority["global_id"],
        "value_type": authority["ifc_class"],
        "unit": None,
        "ownership": "type_inherited",
        "applicability": "required",
        "source_kind": "deterministic_derived",
        "source_ref": f"generated-type:{authority['global_id']}",
        "provenance": ["generated-type-template:0.1"],
        "derivation": {
            key: authority[key]
            for key in (
                "template_id",
                "template_version",
                "ifc_class",
                "formal_attributes",
                "template_digest",
                "template",
            )
        },
        "authoring_action": "inherit_from_type",
    }


def _canonical_fill_door_parameters(
    model: Any, opening_id: str, requested: Mapping[str, Any]
) -> dict[str, Any]:
    """Canonical fill-door parameters measured from the existing opening.

    This mirrors the deterministic resolution the production parameter
    resolver performs for ``fill_existing_opening_with_door`` (fit the
    existing opening exactly; derive position from the opening).
    """

    from text2ifc_ifc_repair.geometry import (
        opening_dimensions_mm,
        opening_position_in_wall_mm,
    )

    opening = model.by_guid(opening_id)
    wall = opening.VoidsElements[0].RelatingBuildingElement
    dims = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, wall)
    style = str(requested["door"]["operation_type"])
    return {
        "host_wall_global_id": str(wall.GlobalId),
        "position": {
            "reference": "wall_local_start",
            "center_offset_mm": round(float(position["center_offset"]), 6),
            "derivation": {
                "formula": "existing_opening_center",
                "source_anchor": f"opening:{opening_id}",
            },
        },
        "opening": {
            "width_mm": round(float(dims["width"]), 6),
            "height_mm": round(float(dims["height"]), 6),
            "sill_height_mm": round(float(position["sill_height"]), 6),
            "dimension_meaning": "overall_opening",
            "derivation": {
                "formula": "fit_existing_opening",
                "source": f"opening:{opening_id}",
            },
        },
        "door": {
            "overall_width_mm": round(float(dims["width"]), 6),
            "overall_height_mm": round(float(dims["height"]), 6),
            "operation_type": style,
            "operation_derivation": {"source": "explicit_formal_enum"},
        },
    }


def build_bound_changeset(
    *,
    case: Mapping[str, Any],
    source_path: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build a bound changeset from the frozen case bindings (deterministic)."""

    model = ifcopenshell.open(str(source_path))
    model_hash = _sha256_path(source_path)
    request = str(case["request"])
    request_hash = _sha256_text(request)
    storey_id = str(case["storey"]["global_id"])

    target_ids: list[str] = [storey_id]
    resolved_bindings: dict[str, str] = {}
    operations: list[dict[str, Any]] = []

    for op in case["operations"]:
        operation_id = str(op["operation_id"])
        operation_type = str(op["operation_type"])
        parameters = dict(op["parameters"])
        if operation_type == "add_beam":
            target = {"storey_global_id": storey_id}
            assignments = [
                _structural_type_assignment(
                    family="beam",
                    operation={"operation_id": operation_id, "target": target, "parameters": parameters},
                    request_hash=request_hash,
                    model_hash=model_hash,
                )
            ]
        elif operation_type == "add_column":
            target = {"storey_global_id": storey_id}
            assignments = [
                _structural_type_assignment(
                    family="column",
                    operation={"operation_id": operation_id, "target": target, "parameters": parameters},
                    request_hash=request_hash,
                    model_hash=model_hash,
                )
            ]
        elif operation_type == "fill_existing_opening_with_door":
            opening_id = _resolve_opening_global_id(
                model, op["expected_target"]["opening_query"]
            )
            resolved_bindings[operation_id] = opening_id
            target = {"opening_global_id": opening_id}
            target_ids.append(opening_id)
            parameters = _canonical_fill_door_parameters(
                model, opening_id, parameters
            )
            assignments = [
                _hosted_type_assignment(
                    operation={
                        "operation_id": operation_id,
                        "operation_type": operation_type,
                        "target": target,
                        "parameters": parameters,
                    },
                    request_hash=request_hash,
                    model_hash=model_hash,
                )
            ]
        elif operation_type == "add_door_with_opening_to_wall":
            wall_id = _resolve_wall_global_id(
                model, op["expected_target"]["wall_query"]
            )
            resolved_bindings[operation_id] = wall_id
            target = {"wall_global_id": wall_id}
            target_ids.append(wall_id)
            assignments = [
                _hosted_type_assignment(
                    operation={
                        "operation_id": operation_id,
                        "operation_type": operation_type,
                        "target": target,
                        "parameters": parameters,
                    },
                    request_hash=request_hash,
                    model_hash=model_hash,
                )
            ]
        elif operation_type == "add_window_with_opening_to_wall":
            wall_id = _resolve_wall_global_id(
                model, op["expected_target"]["wall_query"]
            )
            resolved_bindings[operation_id] = wall_id
            target = {"wall_global_id": wall_id}
            target_ids.append(wall_id)
            assignments = [
                _hosted_type_assignment(
                    operation={
                        "operation_id": operation_id,
                        "operation_type": operation_type,
                        "target": target,
                        "parameters": parameters,
                    },
                    request_hash=request_hash,
                    model_hash=model_hash,
                )
            ]
        else:
            raise ValueError(f"COMPOSITE_OPERATION_UNSUPPORTED:{operation_type}")
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": operation_type,
                "target": target,
                "parameters": parameters,
                "evidence_refs": [f"request:/operations/{operation_id}"],
                "semantic_manifest": {
                    "manifest_id": f"manifest-{operation_id}",
                    "policy_id": _policy_id(operation_type),
                    "policy_version": "0.1",
                },
                "semantic_assignments": assignments,
            }
        )

    # Property intents resolved deterministically from the frozen public
    # request text (the live path resolves the same claim through Stage 1.5;
    # the value, set, property and type are frozen in the case).
    for intent in case.get("property_intents", ()):
        scope_operation_id = str(intent["scope_operation_id"])
        scope = next(
            op for op in operations if op["operation_id"] == scope_operation_id
        )
        semantic_role = _semantic_role(str(intent["scope_operation_type"]))
        fact_key = f"pset:{intent['set_name']}.{intent['property_name']}"
        scope["semantic_assignments"].append(
            {
                "operation_id": scope_operation_id,
                "scope": f"{semantic_role}_occurrence",
                "fact_key": fact_key,
                "source_fact_key": fact_key,
                "value": intent["value"],
                "value_type": intent["value_type"],
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_value",
                "source_ref": f"request:/properties/{intent['property_name']}",
                "provenance": [f"property-hash:{request_hash}"],
                "authoring_action": "set_occurrence_pset",
            }
        )

    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-composite-{case['case_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {"target_ids": sorted(set(target_ids)), "forbidden_ids": []},
        "evidence_refs": [
            "request:/operations",
            *(ref for op in operations for ref in op["evidence_refs"]),
        ],
        "preconditions": ["composite_targets_available"],
        "postconditions": ["composite_operations_atomic"],
        "operations": operations,
    }
    return changeset, resolved_bindings


def _policy_id(operation_type: str) -> str:
    return {
        "add_beam": "beam.add.l2",
        "add_column": "column.add.l2",
        "fill_existing_opening_with_door": "door.fill-existing-opening.l2",
        "add_door_with_opening_to_wall": "door.add-with-opening.l2",
        "add_window_with_opening_to_wall": "window.add-with-opening.l2",
    }[operation_type]


def _semantic_role(operation_type: str) -> str:
    return {
        "add_beam": "beam",
        "add_column": "column",
        "fill_existing_opening_with_door": "door",
        "add_door_with_opening_to_wall": "door",
        "add_window_with_opening_to_wall": "window",
    }[operation_type]


def run_offline_case(
    *,
    case: Mapping[str, Any],
    source_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Apply one frozen composite case deterministically (zero Provider)."""

    changeset, resolved_bindings = build_bound_changeset(
        case=case, source_path=source_path
    )
    result = apply_changeset(
        damaged_ifc_path=source_path,
        repair_request=str(case["request"]),
        changeset=changeset,
        output_path=output_path,
        registry=create_default_registry(),
    )
    return {
        "case_id": str(case["case_id"]),
        "changeset": changeset,
        "resolved_bindings": resolved_bindings,
        "application": result,
        "output_path": output_path,
    }


__all__ = [
    "build_bound_changeset",
    "load_freeze",
    "run_offline_case",
]
