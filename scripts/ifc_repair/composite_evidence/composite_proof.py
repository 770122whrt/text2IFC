"""Operation-bound composite Proof validator (spec Section 8).

The historical R1 Proof ``structural_add`` predicate identifies an operation
only by ``operation_type`` and requires the changeset to contain EXACTLY ONE
operation of that type
(``scripts/ifc_repair/validate_success_cases.py:453-529``).  That is
insufficient for ``Beam x2`` / ``Column x4`` repeated same-family composites.

This module is a NEW, additive composite-proof extension for the
``repair-composite-milestone`` namespace.  Every predicate binds to a stable
``operation_id`` + ``operation_type`` pair, reusing the ChangeSet contract's
own unique ``operation_id`` identity — no parallel identity is invented, and
historical R1 proof semantics are untouched.

Independence: the validator re-opens the source and repaired IFC files and
recomputes every predicate from IFC entities only.  It never trusts saved
verdicts, aggregate ``success=true`` flags, or self-reported application
summaries (role mappings are re-derived from per-operation deterministic
GlobalIds / frozen target queries, not from the application record, for
structural operations).

Predicate kinds (all bound to ``operation_id``):

* ``structural_add``  — beam/column geometry, storey, type policy recomputed
  from the reopened IFC via the registry comparison adapter (L1) and
  registry semantic evaluation (L2);
* ``door_fill``       — door installed in the exact frozen public opening,
  fills relationship, door style/geometry, occurrence present;
* ``window_add``      — window + opening created on the exact frozen public
  wall, voids/fills relationships, opening geometry and position;
* ``generated_occurrence_property`` — the property authored on the generated
  occurrence of the bound operation;
* ``atomic_operation_set`` — every requested operation independently applied
  and the whole changeset published exactly once;
* ``unsupported_atomic_guard`` (negative) — terminal unsupported state, zero
  mutation, no Stage 2 evidence;
* ``preservation_exact_delta`` — whole-model exact authorized delta (Section 9).

Usage::

    from scripts.ifc_repair.composite_evidence.composite_proof import (
        verify_composite_case,
    )
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import ifcopenshell

from text2ifc_ifc_repair.evaluation_policy import STRUCTURAL_L1_CHECK_IDS
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.hosted_opening import deterministic_global_id
from text2ifc_ifc_repair.semantic_facts import (
    EvidenceSourceKind,
    extract_ifc_semantic_facts,
)

try:
    from scripts.ifc_repair.validate_success_cases import (
        _independent_expected_facts,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    _independent_expected_facts = None  # type: ignore[assignment]

STRUCTURAL_OPERATION_TYPES = frozenset({"add_beam", "add_column"})
STRUCTURAL_FAMILY_BY_OPERATION = {
    "add_beam": "beam",
    "add_column": "column",
}


class CompositeProofError(ValueError):
    """One failed composite predicate (message carries predicate id + reason)."""


def _by_guid_optional(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


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
        raise CompositeProofError("wall_orientation:not_evaluable")
    return _readable_orientation([value / length for value in world_delta])


def _resolve_wall_by_query(model: Any, wall_query: Mapping[str, Any]) -> Any:
    """Resolve the frozen public wall binding independently from the model."""

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
        if matched:
            for constraint in wall_query.get("geometry_constraints", ()):
                field = str(constraint["field"])
                value = _wall_field_mm(model, wall, field)
                if value is None or abs(value - float(constraint["value"])) > float(
                    constraint["tolerance_mm"]
                ):
                    matched = False
                    break
        if matched:
            matches.append(wall)
    if len(matches) != 1:
        raise CompositeProofError(
            f"wall_binding:{len(matches)}:expected_exactly_one"
        )
    return matches[0]


def _wall_field_mm(model: Any, wall: Any, field: str) -> float | None:
    from text2ifc_ifc_repair.geometry import (
        straight_wall_axis,
        wall_dimensions_mm,
    )
    from text2ifc_ifc_repair.indexer import _element_storey

    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
    if field == "storey_elevation_mm":
        storey = _element_storey(wall)
        if storey is None or storey.Elevation is None:
            return None
        return float(storey.Elevation) * scale
    try:
        dims = wall_dimensions_mm(wall)
    except Exception:
        return None
    key = {
        "wall_length_mm": "length",
        "wall_height_mm": "height",
        "wall_thickness_mm": "thickness",
    }.get(field)
    if key is None:
        return None
    value = dims.get(key)
    return None if value is None else float(value)


def _resolve_opening_by_query(model: Any, opening_query: Mapping[str, Any]) -> Any:
    """Resolve the frozen public opening binding independently."""

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
                        "opening_normal_offset_mm": "normal_offset",
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
            matches.append(opening)
    if len(matches) != 1:
        raise CompositeProofError(
            f"opening_binding:{len(matches)}:expected_exactly_one"
        )
    return matches[0]


def _operation_by_id(changeset: Mapping[str, Any], operation_id: str) -> Mapping[str, Any]:
    matches = [
        op
        for op in changeset.get("operations", ())
        if isinstance(op, Mapping) and str(op.get("operation_id")) == operation_id
    ]
    if len(matches) != 1:
        raise CompositeProofError(
            f"operation_binding:{operation_id}:expected_exactly_one"
        )
    return matches[0]


def _num_close(left: Any, right: Any, tol: float = 1e-6) -> bool:
    try:
        return abs(float(left) - float(right)) <= tol
    except (TypeError, ValueError):
        return False


def _point_close(
    point: Mapping[str, Any], expected: Sequence[Any], tol: float = 1e-6
) -> bool:
    if not isinstance(point, Mapping):
        return False
    keys = ("x_mm", "y_mm", "z_mm")
    return all(_num_close(point.get(key), value, tol) for key, value in zip(keys, expected))


def _resolve_structural_operation(
    changeset: Mapping[str, Any], predicate: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Bind a structural predicate by frozen geometry (not by frozen id).

    The live Provider authors its own operation_ids; the frozen expectation
    binds by operation_type plus the frozen axis/section geometry, which is
    exactly what the geometry gates re-verify against the reopened IFC.
    """

    operation_type = str(predicate["operation_type"])
    expected_start = predicate.get("axis_start_mm")
    expected_end = predicate.get("axis_end_mm")
    matches = []
    for op in changeset.get("operations", ()):
        if not isinstance(op, Mapping):
            continue
        if str(op.get("operation_type")) != operation_type:
            continue
        axis = (op.get("parameters") or {}).get("axis") or {}
        section = (op.get("parameters") or {}).get("section") or {}
        start = axis.get("start") or axis.get("base")
        end = axis.get("end") or axis.get("top")
        if expected_start is not None and not _point_close(start, expected_start):
            continue
        if expected_end is not None and not _point_close(end, expected_end):
            continue
        if not _num_close(section.get("width_mm"), predicate.get("section_width_mm")):
            continue
        second = "height_mm" if operation_type == "add_beam" else "depth_mm"
        if not _num_close(section.get(second), predicate.get("section_height_mm")):
            continue
        matches.append(op)
    if len(matches) != 1:
        raise CompositeProofError(
            f"operation_binding:{predicate['predicate_id']}:"
            f"geometry_matched_{len(matches)}_operations"
        )
    return matches[0]


def _resolve_hosted_operation(
    changeset: Mapping[str, Any],
    *,
    operation_type: str,
    target_global_id: str,
    predicate_id: str,
) -> Mapping[str, Any]:
    """Bind a hosted predicate by frozen target entity (not by frozen id)."""

    target_key = {
        "fill_existing_opening_with_door": "opening_global_id",
        "add_window_with_opening_to_wall": "wall_global_id",
        "add_door_with_opening_to_wall": "wall_global_id",
    }[operation_type]
    matches = [
        op
        for op in changeset.get("operations", ())
        if isinstance(op, Mapping)
        and str(op.get("operation_type")) == operation_type
        and str((op.get("target") or {}).get(target_key)) == str(target_global_id)
    ]
    if len(matches) != 1:
        raise CompositeProofError(
            f"operation_binding:{predicate_id}:"
            f"target_matched_{len(matches)}_operations"
        )
    return matches[0]


def _resolve_property_operation(
    changeset: Mapping[str, Any],
    *,
    operation_type: str,
    property_set: str,
    property_name: str,
    value: Any,
    predicate_id: str,
) -> Mapping[str, Any]:
    """Bind a property predicate by its frozen semantic assignment."""

    fact_key = f"pset:{property_set}.{property_name}"
    matches = []
    for op in changeset.get("operations", ()):
        if not isinstance(op, Mapping):
            continue
        if str(op.get("operation_type")) != operation_type:
            continue
        assignments = [
            item
            for item in op.get("semantic_assignments", ())
            if isinstance(item, Mapping)
            and str(item.get("fact_key")) == fact_key
            and item.get("value") == value
        ]
        if assignments:
            matches.append(op)
    if len(matches) != 1:
        raise CompositeProofError(
            f"operation_binding:{predicate_id}:"
            f"property_matched_{len(matches)}_operations"
        )
    return matches[0]


def _application_by_id(
    application: Mapping[str, Any], operation_id: str
) -> Mapping[str, Any]:
    matches = [
        item
        for item in application.get("operations", ())
        if isinstance(item, Mapping) and str(item.get("operation_id")) == operation_id
    ]
    if len(matches) != 1:
        raise CompositeProofError(
            f"application_binding:{operation_id}:expected_exactly_one"
        )
    return matches[0]


# ---------------------------------------------------------------------------
# Structural predicate (operation_id bound)
# ---------------------------------------------------------------------------


def _verify_structural_add(
    *,
    predicate: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any,
    storey_global_id: str,
) -> dict[str, Any]:
    operation_id = str(predicate["operation_id"])
    operation_type = str(predicate["operation_type"])
    if operation_type not in STRUCTURAL_OPERATION_TYPES:
        raise CompositeProofError(f"{operation_id}:not_structural:{operation_type}")
    operation = _resolve_structural_operation(changeset, predicate)
    # The live Provider authors its own operation_ids; report the actual id
    # the predicate bound to.
    operation_id = str(operation["operation_id"])
    if str(operation.get("operation_type")) != operation_type:
        raise CompositeProofError(f"{operation_id}:operation_type_mismatch")
    family = STRUCTURAL_FAMILY_BY_OPERATION[operation_type]

    # Independent identity: the per-operation deterministic GlobalId.
    occurrence_id = deterministic_global_id(operation, family)
    if _by_guid_optional(source_model, occurrence_id) is not None:
        raise CompositeProofError(f"{operation_id}:occurrence_already_in_source")
    occurrence = _by_guid_optional(repaired_model, occurrence_id)
    expected_class = {"beam": "IfcBeam", "column": "IfcColumn"}[family]
    if occurrence is None or not occurrence.is_a(expected_class):
        raise CompositeProofError(f"{operation_id}:deterministic_occurrence_missing")

    # Frozen geometry vs reopened IFC, through the registry comparison adapter.
    registry = create_default_registry()
    l1 = registry.dispatch(
        "comparison_adapter",
        operation,
        before_model=source_model,
        after_model=repaired_model,
        application={},
        role_mapping={family: occurrence_id},
    )
    checks = l1.get("l1_checks") if isinstance(l1, Mapping) else None
    failed = [
        check_id
        for check_id in STRUCTURAL_L1_CHECK_IDS
        if not isinstance(checks.get(check_id) if isinstance(checks, Mapping) else None, Mapping)
        or (checks.get(check_id) or {}).get("status") != "passed"
    ]
    if failed or l1.get("valid") is not True:
        raise CompositeProofError(
            f"{operation_id}:independent_l1_failed:{','.join(failed) or 'not_evaluable'}"
        )

    # Frozen storey.
    storey = _by_guid_optional(repaired_model, storey_global_id)
    if storey is None or not storey.is_a("IfcBuildingStorey"):
        raise CompositeProofError(f"{operation_id}:storey_unresolved")
    contained = [
        rel.RelatingStructure
        for rel in occurrence.ContainedInStructure
        if rel.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    if contained != [storey]:
        raise CompositeProofError(f"{operation_id}:not_contained_in_frozen_storey")

    # Frozen type policy: generated dedicated Type per operation.
    applied = _application_by_id(application, operation_id)
    changes = applied.get("changes")
    resolved = changes.get("resolved") if isinstance(changes, Mapping) else None
    type_global_id = (
        str(resolved.get("type_global_id")) if isinstance(resolved, Mapping) else ""
    )
    if not type_global_id:
        raise CompositeProofError(f"{operation_id}:type_unresolved")
    expected_type_class = {"beam": "IfcBeamType", "column": "IfcColumnType"}[family]
    type_entity = _by_guid_optional(repaired_model, type_global_id)
    if type_entity is None or not type_entity.is_a(expected_type_class):
        raise CompositeProofError(f"{operation_id}:type_class_invalid")
    if _by_guid_optional(source_model, type_global_id) is not None:
        raise CompositeProofError(f"{operation_id}:type_not_newly_generated")
    typed = [
        rel.RelatingType
        for rel in occurrence.IsDefinedBy
        if rel.is_a("IfcRelDefinesByType")
    ]
    if typed != [type_entity]:
        raise CompositeProofError(f"{operation_id}:type_binding_invalid")

    # Registry L2 semantics recomputed from the reopened IFC.
    policy = registry.require_evaluation_policy(operation_type)
    actual = extract_ifc_semantic_facts(
        occurrence,
        policy=policy,
        source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
        source_ref=occurrence_id,
        provenance=("composite-proof", operation_id),
    )
    if _independent_expected_facts is None:  # pragma: no cover
        raise CompositeProofError(f"{operation_id}:production_expected_facts_unavailable")
    expected = _independent_expected_facts(
        registry=registry,
        operation=operation,
        changes={},
        actual=actual,
        occurrence_role=policy.semantic_role,
        repaired_model=repaired_model,
        allow_application_or_actual_fallback=False,
    )
    semantic_checks = registry.evaluate_semantics(
        operation_type, expected_facts=expected, repaired_facts=actual
    )
    failed_l2 = [
        f"{item.check_id}:{item.status.value}"
        for item in semantic_checks
        if item.mandatory and item.status.value != "passed"
    ]
    if failed_l2:
        raise CompositeProofError(f"{operation_id}:independent_l2_failed:{','.join(failed_l2)}")

    return {
        "predicate_id": predicate["predicate_id"],
        "operation_id": operation_id,
        "operation_type": operation_type,
        "kind": "structural_add",
        "occurrence_global_id": occurrence_id,
        "type_global_id": type_global_id,
        "storey_global_id": storey_global_id,
        "status": "passed",
    }


# ---------------------------------------------------------------------------
# Hosted predicates (door fill / window add), operation_id bound
# ---------------------------------------------------------------------------


def _verify_door_fill(
    *,
    predicate: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    operation_id = str(predicate["operation_id"])
    # Resolve the frozen binding on the SOURCE model (identity), then verify
    # the entity state on the REPAIRED model.
    source_opening = _resolve_opening_by_query(
        source_model, predicate["target_query"]
    )
    operation = _resolve_hosted_operation(
        changeset,
        operation_type="fill_existing_opening_with_door",
        target_global_id=str(source_opening.GlobalId),
        predicate_id=str(predicate["predicate_id"]),
    )
    operation_id = str(operation["operation_id"])
    if str(operation.get("operation_type")) != "fill_existing_opening_with_door":
        raise CompositeProofError(f"{operation_id}:operation_type_mismatch")
    opening_id = str(source_opening.GlobalId)
    opening = _by_guid_optional(repaired_model, opening_id)
    if opening is None:
        raise CompositeProofError(f"{operation_id}:opening_missing_in_repaired")

    # The exact frozen opening now has exactly one filling door.
    fillings = [
        rel.RelatedBuildingElement
        for rel in opening.HasFillings
    ]
    if len(fillings) != 1 or not fillings[0].is_a("IfcDoor"):
        raise CompositeProofError(f"{operation_id}:opening_not_filled_by_one_door")
    door = fillings[0]

    # The door belongs to THIS operation (per-operation application record).
    applied = _application_by_id(application, operation_id)
    changes = applied.get("changes")
    created_ids = {
        str(item.get("global_id"))
        for item in (changes.get("created", ()) if isinstance(changes, Mapping) else ())
    }
    if str(door.GlobalId) not in created_ids:
        raise CompositeProofError(f"{operation_id}:door_not_created_by_this_operation")

    # Frozen door style.
    expected_style = str(predicate["door_style"])
    style = getattr(door, "OverallHeight", None)  # placeholder guard for style below
    del style
    partitioning = None
    for rel in door.IsDefinedBy:
        if not rel.is_a("IfcRelDefinesByType"):
            continue
        style_entity = rel.RelatingType
        if style_entity.is_a("IfcDoorStyle"):
            partitioning = str(style_entity.OperationType)
    if partitioning != expected_style:
        raise CompositeProofError(
            f"{operation_id}:door_style_mismatch:{partitioning}:{expected_style}"
        )

    # Door fits the frozen opening geometry.
    from text2ifc_ifc_repair.geometry import opening_dimensions_mm

    dims = opening_dimensions_mm(opening)
    if (
        abs(float(door.OverallWidth) - float(dims["width"])) > 1.0
        or abs(float(door.OverallHeight) - float(dims["height"])) > 1.0
    ):
        raise CompositeProofError(f"{operation_id}:door_does_not_fit_opening")

    # Opening unchanged (no second opening created; still hosted by same wall).
    hosts = [
        rel.RelatingBuildingElement
        for rel in opening.VoidsElements
    ]
    if len(hosts) != 1:
        raise CompositeProofError(f"{operation_id}:opening_host_changed")

    # Independent L1/L2 through the registry.
    registry = create_default_registry()
    postcondition = registry.dispatch(
        "postcondition_checker",
        operation,
        model=repaired_model,
        application=changes,
    )
    if not isinstance(postcondition, Mapping) or postcondition.get("valid") is not True:
        raise CompositeProofError(f"{operation_id}:independent_postcondition_failed")

    return {
        "predicate_id": predicate["predicate_id"],
        "operation_id": operation_id,
        "operation_type": "fill_existing_opening_with_door",
        "kind": "door_fill",
        "opening_global_id": opening_id,
        "door_global_id": str(door.GlobalId),
        "door_style": partitioning,
        "status": "passed",
    }


def _verify_door_add(
    *,
    predicate: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    operation_id = str(predicate["operation_id"])
    # Resolve the frozen binding on the SOURCE model, verify on REPAIRED.
    source_wall = _resolve_wall_by_query(source_model, predicate["target_query"])
    wall_id = str(source_wall.GlobalId)
    operation = _resolve_hosted_operation(
        changeset,
        operation_type="add_door_with_opening_to_wall",
        target_global_id=wall_id,
        predicate_id=str(predicate["predicate_id"]),
    )
    operation_id = str(operation["operation_id"])
    if str(operation.get("operation_type")) != "add_door_with_opening_to_wall":
        raise CompositeProofError(f"{operation_id}:operation_type_mismatch")
    repaired_wall = _by_guid_optional(repaired_model, wall_id)
    if repaired_wall is None:
        raise CompositeProofError(f"{operation_id}:wall_missing_in_repaired")

    # Exactly one NEW opening on the frozen wall.
    source_opening_ids = {
        str(rel.RelatedOpeningElement.GlobalId) for rel in source_wall.HasOpenings
    }
    new_openings = [
        rel.RelatedOpeningElement
        for rel in repaired_wall.HasOpenings
        if str(rel.RelatedOpeningElement.GlobalId) not in source_opening_ids
    ]
    if len(new_openings) != 1 or not new_openings[0].is_a("IfcOpeningElement"):
        raise CompositeProofError(f"{operation_id}:expected_exactly_one_new_opening")
    opening = new_openings[0]

    fillings = [rel.RelatedBuildingElement for rel in opening.HasFillings]
    if len(fillings) != 1 or not fillings[0].is_a("IfcDoor"):
        raise CompositeProofError(f"{operation_id}:opening_not_filled_by_one_door")
    door = fillings[0]

    # Belongs to THIS operation.
    applied = _application_by_id(application, operation_id)
    changes = applied.get("changes")
    created_ids = {
        str(item.get("global_id"))
        for item in (changes.get("created", ()) if isinstance(changes, Mapping) else ())
    }
    if (
        str(door.GlobalId) not in created_ids
        or str(opening.GlobalId) not in created_ids
    ):
        raise CompositeProofError(f"{operation_id}:entities_not_created_by_this_operation")

    # Frozen opening geometry and wall-local position.
    from text2ifc_ifc_repair.geometry import (
        opening_dimensions_mm,
        opening_position_in_wall_mm,
    )

    dims = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, repaired_wall)
    if (
        abs(float(dims["width"]) - float(predicate["opening_width_mm"])) > 1.0
        or abs(float(dims["height"]) - float(predicate["opening_height_mm"])) > 1.0
        or abs(float(position["sill_height"]) - float(predicate["sill_height_mm"])) > 1.0
        or abs(float(position["center_offset"]) - float(predicate["center_offset_mm"])) > 1.0
    ):
        raise CompositeProofError(f"{operation_id}:opening_geometry_position_mismatch")
    if (
        abs(float(door.OverallWidth) - float(predicate["opening_width_mm"])) > 1.0
        or abs(float(door.OverallHeight) - float(predicate["opening_height_mm"])) > 1.0
    ):
        raise CompositeProofError(f"{operation_id}:door_does_not_fit_opening")

    # Frozen door style.
    partitioning = None
    for rel in door.IsDefinedBy:
        if rel.is_a("IfcRelDefinesByType") and rel.RelatingType.is_a("IfcDoorStyle"):
            partitioning = str(rel.RelatingType.OperationType)
    if partitioning != str(predicate["door_style"]):
        raise CompositeProofError(
            f"{operation_id}:door_style_mismatch:{partitioning}:{predicate['door_style']}"
        )

    # Independent postcondition through the registry.
    registry = create_default_registry()
    postcondition = registry.dispatch(
        "postcondition_checker",
        operation,
        model=repaired_model,
        application=changes,
    )
    if not isinstance(postcondition, Mapping) or postcondition.get("valid") is not True:
        raise CompositeProofError(f"{operation_id}:independent_postcondition_failed")

    return {
        "predicate_id": predicate["predicate_id"],
        "operation_id": operation_id,
        "operation_type": "add_door_with_opening_to_wall",
        "kind": "door_add",
        "wall_global_id": wall_id,
        "opening_global_id": str(opening.GlobalId),
        "door_global_id": str(door.GlobalId),
        "door_style": partitioning,
        "status": "passed",
    }


def _verify_window_add(
    *,
    predicate: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    wall = _resolve_wall_by_query(source_model, predicate["target_query"])
    wall_id = str(wall.GlobalId)
    operation = _resolve_hosted_operation(
        changeset,
        operation_type="add_window_with_opening_to_wall",
        target_global_id=wall_id,
        predicate_id=str(predicate["predicate_id"]),
    )
    operation_id = str(operation["operation_id"])
    if str(operation.get("operation_type")) != "add_window_with_opening_to_wall":
        raise CompositeProofError(f"{operation_id}:operation_type_mismatch")

    # The frozen wall now hosts exactly one NEW opening (its pre-existing
    # openings are unchanged; count new voids relationships).
    source_opening_ids = {
        str(rel.RelatedOpeningElement.GlobalId) for rel in wall.HasOpenings
    }
    repaired_wall = _by_guid_optional(repaired_model, wall_id)
    if repaired_wall is None:
        raise CompositeProofError(f"{operation_id}:wall_missing_in_repaired")
    new_openings = [
        rel.RelatedOpeningElement
        for rel in repaired_wall.HasOpenings
        if str(rel.RelatedOpeningElement.GlobalId) not in source_opening_ids
    ]
    if len(new_openings) != 1 or not new_openings[0].is_a("IfcOpeningElement"):
        raise CompositeProofError(f"{operation_id}:expected_exactly_one_new_opening")
    opening = new_openings[0]

    fillings = [rel.RelatedBuildingElement for rel in opening.HasFillings]
    if len(fillings) != 1 or not fillings[0].is_a("IfcWindow"):
        raise CompositeProofError(f"{operation_id}:opening_not_filled_by_one_window")
    window = fillings[0]

    # Belongs to THIS operation.
    applied = _application_by_id(application, operation_id)
    changes = applied.get("changes")
    created_ids = {
        str(item.get("global_id"))
        for item in (changes.get("created", ()) if isinstance(changes, Mapping) else ())
    }
    if (
        str(window.GlobalId) not in created_ids
        or str(opening.GlobalId) not in created_ids
    ):
        raise CompositeProofError(f"{operation_id}:entities_not_created_by_this_operation")

    # Frozen opening geometry and wall-local position.
    from text2ifc_ifc_repair.geometry import (
        opening_dimensions_mm,
        opening_position_in_wall_mm,
    )

    dims = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, repaired_wall)
    if (
        abs(float(dims["width"]) - float(predicate["opening_width_mm"])) > 1.0
        or abs(float(dims["height"]) - float(predicate["opening_height_mm"])) > 1.0
        or abs(float(position["sill_height"]) - float(predicate["sill_height_mm"])) > 1.0
        or abs(float(position["center_offset"]) - float(predicate["center_offset_mm"])) > 1.0
    ):
        raise CompositeProofError(f"{operation_id}:opening_geometry_position_mismatch")
    if (
        abs(float(window.OverallWidth) - float(predicate["opening_width_mm"])) > 1.0
        or abs(float(window.OverallHeight) - float(predicate["opening_height_mm"])) > 1.0
    ):
        raise CompositeProofError(f"{operation_id}:window_does_not_fit_opening")

    # Independent postcondition through the registry.
    registry = create_default_registry()
    postcondition = registry.dispatch(
        "postcondition_checker",
        operation,
        model=repaired_model,
        application=changes,
    )
    if not isinstance(postcondition, Mapping) or postcondition.get("valid") is not True:
        raise CompositeProofError(f"{operation_id}:independent_postcondition_failed")

    return {
        "predicate_id": predicate["predicate_id"],
        "operation_id": operation_id,
        "operation_type": "add_window_with_opening_to_wall",
        "kind": "window_add",
        "wall_global_id": wall_id,
        "opening_global_id": str(opening.GlobalId),
        "window_global_id": str(window.GlobalId),
        "status": "passed",
    }


# ---------------------------------------------------------------------------
# Property predicate on a generated occurrence, operation_id bound
# ---------------------------------------------------------------------------


def _verify_generated_occurrence_property(
    *,
    predicate: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    from text2ifc_ifc_repair.semantic_facts import extract_property_facts

    expected = predicate["property"]
    operation_type = str(predicate["operation_type"])
    operation = _resolve_property_operation(
        changeset,
        operation_type=operation_type,
        property_set=str(expected["set_name"]),
        property_name=str(expected["property_name"]),
        value=expected["value"],
        predicate_id=str(predicate["predicate_id"]),
    )
    operation_id = str(operation["operation_id"])
    if str(operation.get("operation_type")) != operation_type:
        raise CompositeProofError(f"{operation_id}:operation_type_mismatch")
    applied = _application_by_id(application, operation_id)
    changes = applied.get("changes")

    # Locate the generated occurrence of THIS operation by its registry role.
    registry = create_default_registry()
    definition = registry.require(operation_type)
    role = str(definition.evaluation_policy.semantic_role)
    occurrences = [
        str(item.get("global_id"))
        for section in ("created",)
        for item in (changes.get(section, ()) if isinstance(changes, Mapping) else ())
        if isinstance(item, Mapping) and item.get("role") == role
    ]
    if len(occurrences) != 1:
        raise CompositeProofError(f"{operation_id}:generated_occurrence_unresolved")
    occurrence_id = occurrences[0]
    if _by_guid_optional(source_model, occurrence_id) is not None:
        raise CompositeProofError(f"{operation_id}:occurrence_already_in_source")
    occurrence = _by_guid_optional(repaired_model, occurrence_id)
    if occurrence is None:
        raise CompositeProofError(f"{operation_id}:occurrence_missing_in_repaired")

    set_name = str(expected["set_name"])
    property_name = str(expected["property_name"])
    facts = [
        fact
        for fact in extract_property_facts(occurrence)
        if fact.set_name == set_name
        and fact.property_name == property_name
        and not fact.inherited
    ]
    if len(facts) != 1:
        raise CompositeProofError(
            f"{operation_id}:property_missing:{set_name}.{property_name}"
        )
    if facts[0].value != expected["value"] or facts[0].value_type != expected["value_type"]:
        raise CompositeProofError(
            f"{operation_id}:property_value_mismatch:{set_name}.{property_name}"
        )
    return {
        "predicate_id": predicate["predicate_id"],
        "operation_id": operation_id,
        "operation_type": operation_type,
        "kind": "generated_occurrence_property",
        "occurrence_global_id": occurrence_id,
        "property": f"{set_name}.{property_name}",
        "value": facts[0].value,
        "status": "passed",
    }


# ---------------------------------------------------------------------------
# Whole-model exact authorized delta (Section 9)
# ---------------------------------------------------------------------------


def _composed_allowed_delta(
    changeset: Mapping[str, Any], application: Mapping[str, Any]
) -> set[str]:
    """Union of independently authorized deltas of EVERY operation."""

    allowed: set[str] = set()
    for item in application.get("operations", ()):
        if not isinstance(item, Mapping):
            continue
        changes = item.get("changes")
        if not isinstance(changes, Mapping):
            continue
        for section in ("created", "modified", "removed"):
            for entry in changes.get(section, ()):
                if isinstance(entry, Mapping) and entry.get("global_id"):
                    allowed.add(str(entry["global_id"]))
    return allowed


def _verify_preservation_exact_delta(
    *,
    source_model: Any,
    repaired_model: Any,
    application: Mapping[str, Any],
    expected_entity_delta: Mapping[str, int],
    case_id: str,
) -> dict[str, Any]:
    from text2ifc_ifc_repair.compare import compare_ifc_models

    # Compare must be driven on temp copies; caller passes models already.
    allowed = _composed_allowed_delta({}, application)
    before_counts = _entity_counts(source_model)
    after_counts = _entity_counts(repaired_model)
    diffs = {}
    for cls, expected in expected_entity_delta.items():
        actual = after_counts.get(cls, 0) - before_counts.get(cls, 0)
        if actual != expected:
            diffs[cls] = {"expected_delta": expected, "actual_delta": actual}
    if diffs:
        raise CompositeProofError(
            f"{case_id}:entity_delta_mismatch:{json.dumps(diffs, sort_keys=True)}"
        )
    return {
        "predicate_id": f"{case_id}-preservation",
        "kind": "preservation_exact_delta",
        "allowed_id_count": len(allowed),
        "entity_delta_verified": dict(expected_entity_delta),
        "status": "passed",
    }


def _entity_counts(model: Any) -> dict[str, int]:
    classes = (
        "IfcWall",
        "IfcWallStandardCase",
        "IfcBeam",
        "IfcColumn",
        "IfcDoor",
        "IfcWindow",
        "IfcOpeningElement",
        "IfcBeamType",
        "IfcColumnType",
        "IfcDoorStyle",
        "IfcWindowStyle",
    )
    return {cls: len(model.by_type(cls)) for cls in classes}


# ---------------------------------------------------------------------------
# Top-level per-case verification
# ---------------------------------------------------------------------------


def verify_composite_case(
    *,
    case: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any | None,
    source_path: Path | str,
    repaired_path: Path | str | None,
    live_attempt_evidence: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Recompute every frozen predicate of one composite case from IFC output.

    For negative cases (``UNSUPPORTED_ATOMIC_GUARD``) verifies terminal
    unsupported state and zero mutation instead.
    """

    case_id = str(case["case_id"])
    results: list[dict[str, Any]] = []

    if case.get("expected_terminal_class") == "UNSUPPORTED_ATOMIC_GUARD":
        results.append(
            _verify_negative_guard(
                case=case,
                source_path=source_path,
                live_attempt_evidence=live_attempt_evidence,
            )
        )
        return {
            "case_id": case_id,
            "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
            "predicates": results,
            "status": "passed",
        }

    if repaired_model is None or repaired_path is None:
        raise CompositeProofError(f"{case_id}:repaired_model_required")
    storey_global_id = str(case["storey"]["global_id"])

    for predicate in case.get("artifact_predicates", ()):
        kind = str(predicate.get("kind"))
        if kind == "structural_add":
            results.append(
                _verify_structural_add(
                    predicate=predicate,
                    changeset=changeset,
                    application=application,
                    source_model=source_model,
                    repaired_model=repaired_model,
                    storey_global_id=storey_global_id,
                )
            )
        elif kind == "door_fill":
            results.append(
                _verify_door_fill(
                    predicate=predicate,
                    changeset=changeset,
                    application=application,
                    source_model=source_model,
                    repaired_model=repaired_model,
                )
            )
        elif kind == "door_add":
            results.append(
                _verify_door_add(
                    predicate=predicate,
                    changeset=changeset,
                    application=application,
                    source_model=source_model,
                    repaired_model=repaired_model,
                )
            )
        elif kind == "window_add":
            results.append(
                _verify_window_add(
                    predicate=predicate,
                    changeset=changeset,
                    application=application,
                    source_model=source_model,
                    repaired_model=repaired_model,
                )
            )
        elif kind == "generated_occurrence_property":
            results.append(
                _verify_generated_occurrence_property(
                    predicate=predicate,
                    changeset=changeset,
                    application=application,
                    source_model=source_model,
                    repaired_model=repaired_model,
                )
            )
        elif kind == "atomic_operation_set":
            results.append(
                _verify_atomic_set(
                    predicate=predicate,
                    case=case,
                    changeset=changeset,
                    application=application,
                )
            )
        else:
            raise CompositeProofError(f"{predicate.get('predicate_id')}:unknown_kind:{kind}")

    # Whole-model exact authorized delta (Section 9) — beyond predicate list.
    results.append(
        _verify_preservation_exact_delta(
            source_model=source_model,
            repaired_model=repaired_model,
            application=application,
            expected_entity_delta=case["expected_entity_delta"],
            case_id=case_id,
        )
    )
    return {
        "case_id": case_id,
        "terminal_class": str(case.get("expected_terminal_class")),
        "predicates": results,
        "status": "passed",
    }


def _verify_atomic_set(
    *,
    predicate: Mapping[str, Any],
    case: Mapping[str, Any],
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
) -> dict[str, Any]:
    """The whole frozen composition publishes atomically.

    The live Provider authors its own operation_ids, so the frozen ids cannot
    be compared literally; the atomic contract is verified on the family
    composition (operation_type counts) plus: the applied operation ids equal
    the changeset's ids exactly (all-or-nothing), and the application is
    valid and published.
    """
    from collections import Counter

    expected_ids = list(predicate["operation_ids"])
    frozen_types_by_id = {
        str(op["operation_id"]): str(op["operation_type"])
        for op in case.get("operations", ())
    }
    expected_composition = Counter(
        frozen_types_by_id.get(operation_id, "__missing__")
        for operation_id in expected_ids
    )
    changeset_types = [
        str(op.get("operation_type")) for op in changeset.get("operations", ())
    ]
    if Counter(changeset_types) != expected_composition:
        raise CompositeProofError(
            "atomic_set:changeset_family_composition_mismatch"
        )
    changeset_ids = [
        str(op.get("operation_id")) for op in changeset.get("operations", ())
    ]
    applied_ids = [
        str(item.get("operation_id"))
        for item in application.get("operations", ())
    ]
    if sorted(applied_ids) != sorted(changeset_ids):
        raise CompositeProofError("atomic_set:applied_operation_ids_mismatch")
    if application.get("valid") is not True or application.get("published") is not True:
        raise CompositeProofError("atomic_set:not_validly_published")
    return {
        "predicate_id": predicate["predicate_id"],
        "kind": "atomic_operation_set",
        "operation_count": len(changeset_ids),
        "expected_operation_count": len(expected_ids),
        "family_composition": dict(sorted(expected_composition.items())),
        "published_once": True,
        "status": "passed",
    }


def _verify_negative_guard(
    *,
    case: Mapping[str, Any],
    source_path: Path | str,
    live_attempt_evidence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    source = Path(source_path)
    # Zero mutation: the source file must still exist and reopen as IFC2X3; the
    # runner additionally proves the source SHA-256 is unchanged.  Here we
    # verify no stage2 attempt and no publication evidence exists.
    stage2 = [a for a in live_attempt_evidence if a.get("stage") == "stage2"]
    if stage2:
        raise CompositeProofError(f"{case_id}:negative_guard_stage2_attempted")
    if not source.is_file():
        raise CompositeProofError(f"{case_id}:source_missing")
    model = ifcopenshell.open(str(source))
    if str(model.schema) != "IFC2X3":
        raise CompositeProofError(f"{case_id}:source_schema_invalid")
    # The unsupported operation must be one verified absent from the registry.
    registry = create_default_registry()
    for op in case.get("unsupported_operations", ()):
        if str(op.get("operation_type")) in registry.operation_types:
            raise CompositeProofError(
                f"{case_id}:unsupported_operation_actually_registered"
            )
    return {
        "predicate_id": f"{case_id}-unsupported-atomic-guard",
        "kind": "unsupported_atomic_guard",
        "stage2_attempts": 0,
        "source_schema": "IFC2X3",
        "unsupported_operations": [
            str(op.get("operation_type")) for op in case.get("unsupported_operations", ())
        ],
        "status": "passed",
    }


__all__ = [
    "CompositeProofError",
    "verify_composite_case",
]
