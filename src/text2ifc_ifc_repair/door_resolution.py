"""Pure deterministic policy for IFC2X3 Door intent canonicalization."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from .index_models import ElementRecord, TypeRecord
from .indexer import normalize_alias


ADD_DOOR_OPERATION = "add_door_with_opening_to_wall"
FILL_DOOR_OPERATION = "fill_existing_opening_with_door"
SUPPORTED_GENERATED_OPERATIONS = frozenset(
    {"SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "NOTDEFINED"}
)
UNSUPPORTED_COMPLEX_OPERATIONS = frozenset(
    {
        "DOUBLE_DOOR_SINGLE_SWING",
        "DOUBLE_DOOR_DOUBLE_SWING",
        "DOUBLE_SWING_LEFT",
        "DOUBLE_SWING_RIGHT",
        "FOLDING_TO_LEFT",
        "FOLDING_TO_RIGHT",
        "REVOLVING",
        "ROLLINGUP",
        "SLIDING_TO_LEFT",
        "SLIDING_TO_RIGHT",
        "SWING_FIXED_LEFT",
        "SWING_FIXED_RIGHT",
    }
)
DIMENSION_MEANINGS = frozenset(
    {
        "overall_opening",
        "clear_passage",
        "door_leaf",
        "rough_opening",
        "unknown",
    }
)


@dataclass(frozen=True)
class DoorResolutionDecision:
    status: str
    parameters: Mapping[str, Any] | None = None
    reason_code: str | None = None
    missing_slots: tuple[str, ...] = ()
    candidates: tuple[Mapping[str, Any], ...] = ()
    authorized_semantics: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason_code": self.reason_code,
            "parameters": (
                None if self.parameters is None else copy.deepcopy(dict(self.parameters))
            ),
            "missing_slots": list(self.missing_slots),
            "candidates": [copy.deepcopy(dict(item)) for item in self.candidates],
            "authorized_semantics": [
                copy.deepcopy(dict(item)) for item in self.authorized_semantics
            ],
        }


def resolve_door_parameters(
    *,
    operation: Mapping[str, Any],
    target_record: ElementRecord,
    type_record: TypeRecord | None = None,
    repository: Any = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Registry hook returning complete canonical parameters or one pause."""

    del context
    parameters = copy.deepcopy(dict(operation.get("parameters", {})))
    door_parameters = parameters.get("door")
    requested_operation_type = (
        door_parameters.get("operation_type")
        if isinstance(door_parameters, Mapping)
        else None
    )
    type_record, type_decision = _resolve_exact_type(
        operation.get("prototype_intent"),
        repository,
        requested_operation_type=requested_operation_type,
    )
    if type_decision is not None:
        return type_decision.to_dict()
    viewpoint_decision = _enrich_space_viewpoint(
        parameters=parameters,
        target_record=target_record,
        repository=repository,
    )
    if viewpoint_decision is not None:
        return viewpoint_decision.to_dict()
    decision = canonicalize_door_intent(
        operation_type=str(operation.get("operation_type", "")),
        parameters=parameters,
        target_record=target_record,
        type_record=type_record,
    )
    return decision.to_dict()


def resolve_space_viewpoint(
    *,
    wall_record: ElementRecord,
    from_space: ElementRecord,
    to_space: ElementRecord,
    tolerance_mm: float = 1.0,
) -> dict[str, Any]:
    """Resolve the observer side from bounded indexed geometry evidence."""

    basis = wall_record.geometry_summary.get("coordinate_basis", {})
    start = basis.get("world_axis_start_mm", basis.get("axis_start_mm"))
    direction = basis.get(
        "world_axis_direction", basis.get("axis_direction")
    )
    from_center = from_space.geometry_summary.get("centroid_mm")
    to_center = to_space.geometry_summary.get("centroid_mm")
    if not all(
        isinstance(item, (list, tuple)) and len(item) >= 2
        for item in (start, direction, from_center, to_center)
    ):
        return {
            "status": "clarification_required",
            "reason_code": "SPACE_SIDE_UNRESOLVED",
        }
    normal = (-float(direction[1]), float(direction[0]))

    def signed(center: Any) -> float:
        return (
            (float(center[0]) - float(start[0])) * normal[0]
            + (float(center[1]) - float(start[1])) * normal[1]
        )

    from_sign = signed(from_center)
    to_sign = signed(to_center)
    if (
        abs(from_sign) <= tolerance_mm
        or abs(to_sign) <= tolerance_mm
        or from_sign * to_sign >= 0
    ):
        return {
            "status": "clarification_required",
            "reason_code": "SPACE_SIDE_UNRESOLVED",
            "evidence": {
                "from_signed_distance_mm": from_sign,
                "to_signed_distance_mm": to_sign,
                "tolerance_mm": tolerance_mm,
            },
        }
    formal_boundary = (
        wall_record.ifc_global_id
        in from_space.facets.get("boundary_wall_global_ids", ())
        and wall_record.ifc_global_id
        in to_space.facets.get("boundary_wall_global_ids", ())
    )
    return {
        "status": "resolved",
        "observation_side": (
            "wall_positive" if from_sign > 0 else "wall_negative"
        ),
        "destination": to_space.name or to_space.ifc_global_id,
        "evidence": {
            "method": (
                "formal_boundary_plus_geometry_side"
                if formal_boundary
                else "geometry_side"
            ),
            "wall_global_id": wall_record.ifc_global_id,
            "from_space_global_id": from_space.ifc_global_id,
            "to_space_global_id": to_space.ifc_global_id,
            "from_signed_distance_mm": from_sign,
            "to_signed_distance_mm": to_sign,
            "tolerance_mm": tolerance_mm,
        },
    }


def canonicalize_door_intent(
    *,
    operation_type: str,
    parameters: Mapping[str, Any],
    target_record: ElementRecord,
    type_record: TypeRecord | None = None,
) -> DoorResolutionDecision:
    if operation_type not in {ADD_DOOR_OPERATION, FILL_DOOR_OPERATION}:
        return _unsupported("DOOR_OPERATION_UNSUPPORTED")
    if any(
        key in parameters
        for key in ("replace_existing_door", "delete_door", "resize_door", "move_door")
    ):
        return _unsupported("EXISTING_DOOR_MUTATION_UNSUPPORTED")
    if operation_type == FILL_DOOR_OPERATION:
        topology = _opening_topology_issue(target_record)
        if topology is not None:
            return topology

    dimensions = _resolve_dimensions(
        operation_type=operation_type,
        parameters=parameters,
        target_record=target_record,
    )
    position = _resolve_position(
        operation_type=operation_type,
        parameters=parameters,
        target_record=target_record,
        overall_width_mm=dimensions.get("width_mm"),
    )
    operation = _resolve_formal_operation(
        parameters=parameters,
        type_record=type_record,
    )
    blocking = [item for item in (dimensions, position, operation) if item["status"] != "resolved"]
    unsupported = [item for item in blocking if item["status"] == "unsupported"]
    if unsupported:
        return _unsupported(str(unsupported[0]["reason_code"]))
    if blocking:
        missing = tuple(
            sorted(
                {
                    str(slot)
                    for item in blocking
                    for slot in item.get("missing_slots", ())
                }
            )
        )
        reason_codes = {
            str(item["reason_code"])
            for item in blocking
            if item.get("reason_code")
        }
        return DoorResolutionDecision(
            status="clarification_required",
            reason_code=(
                next(iter(reason_codes))
                if len(reason_codes) == 1
                else "DOOR_BLOCKING_FACTS_REQUIRED"
            ),
            missing_slots=missing,
            candidates=tuple(
                {
                    "slot": slot,
                    "reason_code": item.get("reason_code"),
                }
                for item in blocking
                for slot in item.get("missing_slots", ())
            ),
        )

    canonical = {
        "position": position["value"],
        "opening": {
            "width_mm": dimensions["width_mm"],
            "height_mm": dimensions["height_mm"],
            "sill_height_mm": dimensions["sill_height_mm"],
            "dimension_meaning": "overall_opening",
            "derivation": dimensions["derivation"],
        },
        "door": {
            "overall_width_mm": dimensions["width_mm"],
            "overall_height_mm": dimensions["height_mm"],
            "operation_type": operation["operation_type"],
            "operation_derivation": operation["derivation"],
        },
        "derivation": {
            "position": position["derivation"],
            "digest": _digest(
                {
                    "dimensions": dimensions["derivation"],
                    "position": position["derivation"],
                    "operation": operation["derivation"],
                }
            ),
        },
    }
    if operation_type == FILL_DOOR_OPERATION:
        host_ids = target_record.facets.get("host_wall_global_ids", ())
        if len(host_ids) != 1:
            return _unsupported("OPENING_TARGET_INVALID")
        canonical["host_wall_global_id"] = str(host_ids[0])
    authorized = (
        {
            "kind": "door_canonicalization",
            "operation_type": operation["operation_type"],
            "derivation_digest": canonical["derivation"]["digest"],
            "source": "deterministic_policy",
        },
    )
    return DoorResolutionDecision(
        status="resolved",
        parameters=canonical,
        authorized_semantics=authorized,
    )


def _resolve_dimensions(
    *,
    operation_type: str,
    parameters: Mapping[str, Any],
    target_record: ElementRecord,
) -> dict[str, Any]:
    if (
        operation_type == FILL_DOOR_OPERATION
        and parameters.get("fit_existing_opening") is True
    ):
        dimensions = target_record.geometry_summary.get("dimensions_mm", {})
        width = _positive_number(dimensions.get("width"))
        height = _positive_number(dimensions.get("height"))
        position = target_record.geometry_summary.get("wall_local_position_mm", {})
        sill = _nonnegative_number(position.get("sill_height_mm"))
        if width is None or height is None or sill is None:
            return _clarify(
                "OPENING_GEOMETRY_UNAVAILABLE",
                ("/target_opening/geometry",),
            )
        return {
            "status": "resolved",
            "width_mm": width,
            "height_mm": height,
            "sill_height_mm": sill,
            "derivation": {
                "source": f"opening:{target_record.ifc_global_id}",
                "formula": "fit_existing_opening",
            },
        }

    opening = parameters.get("opening")
    if not isinstance(opening, Mapping):
        opening = parameters.get("dimensions")
    if not isinstance(opening, Mapping):
        return _clarify(
            "DOOR_DIMENSIONS_REQUIRED",
            (
                "/parameters/opening/width_mm",
                "/parameters/opening/height_mm",
                "/parameters/opening/dimension_meaning",
            ),
        )
    meaning = str(
        opening.get("dimension_meaning", opening.get("meaning", "unknown"))
    )
    if meaning not in DIMENSION_MEANINGS:
        return _unsupported_mapping("DOOR_DIMENSION_MEANING_UNSUPPORTED")
    if meaning == "unknown":
        return _clarify(
            "DOOR_DIMENSION_MEANING_REQUIRED",
            ("/parameters/opening/dimension_meaning",),
        )
    if meaning != "overall_opening":
        return _clarify(
            "DOOR_OVERALL_DIMENSIONS_REQUIRED",
            (
                "/parameters/opening/width_mm",
                "/parameters/opening/height_mm",
            ),
        )
    width = _positive_number(opening.get("width_mm"))
    height = _positive_number(opening.get("height_mm"))
    missing = []
    if width is None:
        missing.append("/parameters/opening/width_mm")
    if height is None:
        missing.append("/parameters/opening/height_mm")
    if missing:
        return _clarify("DOOR_DIMENSIONS_REQUIRED", tuple(missing))
    sill = _nonnegative_number(opening.get("sill_height_mm", 0.0))
    if sill is None:
        return _unsupported_mapping("DOOR_SILL_HEIGHT_INVALID")
    return {
        "status": "resolved",
        "width_mm": width,
        "height_mm": height,
        "sill_height_mm": sill,
        "derivation": {
            "source": "explicit_request",
            "meaning": meaning,
            "formula": "identity",
        },
    }


def _resolve_exact_type(
    prototype_intent: Any,
    repository: Any,
    *,
    requested_operation_type: Any = None,
) -> tuple[TypeRecord | None, DoorResolutionDecision | None]:
    if not isinstance(prototype_intent, Mapping):
        return None, None
    if repository is None:
        return None, DoorResolutionDecision(
            status="clarification_required",
            reason_code="DOOR_TYPE_EVIDENCE_REQUIRED",
            missing_slots=("/prototype_intent",),
        )
    kind = str(prototype_intent.get("reference_kind", ""))
    reference = str(prototype_intent.get("reference", ""))
    candidates: list[TypeRecord]
    if kind == "global_id":
        record = repository.get_type_by_global_id(reference)
        candidates = [] if record is None else [record]
    elif kind == "type_name":
        candidates = [
            item
            for item in repository.find_type_aliases(normalize_alias(reference))
            if item.ifc_class == "IfcDoorStyle"
            and item.identity_reliable
            and item.name is not None
            and normalize_alias(item.name) == normalize_alias(reference)
        ]
    else:
        return None, DoorResolutionDecision(
            status="clarification_required",
            reason_code="DOOR_TYPE_SELECTION_REQUIRED",
            missing_slots=("/prototype_intent",),
        )
    candidates = [
        item
        for item in candidates
        if item.ifc_class == "IfcDoorStyle" and item.identity_reliable
    ]
    if requested_operation_type:
        candidates = [
            item
            for item in candidates
            if str(item.formal_attributes.get("OperationType"))
            == str(requested_operation_type)
        ]
    if len(candidates) == 1:
        return candidates[0], None
    if not candidates:
        return None, DoorResolutionDecision(
            status="clarification_required",
            reason_code="DOOR_TYPE_NOT_FOUND",
            missing_slots=("/prototype_intent",),
        )
    return None, DoorResolutionDecision(
        status="clarification_required",
        reason_code="DOOR_TYPE_SELECTION_REQUIRED",
        candidates=tuple(
            {
                "ifc_global_id": item.ifc_global_id,
                "ifc_class": item.ifc_class,
                "name": item.name,
                "formal_operation_type": item.formal_attributes.get(
                    "OperationType"
                ),
            }
            for item in sorted(
                candidates,
                key=lambda item: (str(item.name), str(item.ifc_global_id)),
            )[:5]
        ),
    )


def _enrich_space_viewpoint(
    *,
    parameters: dict[str, Any],
    target_record: ElementRecord,
    repository: Any,
) -> DoorResolutionDecision | None:
    door = parameters.get("door")
    if not isinstance(door, Mapping):
        return None
    viewpoint = door.get("viewpoint")
    if not isinstance(viewpoint, Mapping) or viewpoint.get("observation_side"):
        return None
    from_name = viewpoint.get("from_space")
    to_name = viewpoint.get("to_space")
    if not from_name and not to_name:
        return None
    if not from_name or not to_name or repository is None:
        return DoorResolutionDecision(
            status="clarification_required",
            reason_code="DOOR_VIEWPOINT_REQUIRED",
            missing_slots=(
                "/parameters/door/viewpoint/from_space",
                "/parameters/door/viewpoint/to_space",
            ),
        )

    def exact_space(name: Any) -> list[ElementRecord]:
        return [
            item
            for item in repository.find_aliases(normalize_alias(str(name)))
            if item.ifc_class == "IfcSpace"
            and item.identity_reliable
            and item.name is not None
            and normalize_alias(item.name) == normalize_alias(str(name))
        ]

    from_spaces = exact_space(from_name)
    to_spaces = exact_space(to_name)
    if len(from_spaces) != 1 or len(to_spaces) != 1:
        return DoorResolutionDecision(
            status="clarification_required",
            reason_code="SPACE_SIDE_UNRESOLVED",
            candidates=tuple(
                {
                    "role": role,
                    "ifc_global_id": item.ifc_global_id,
                    "name": item.name,
                    "storey_name": item.storey_name,
                }
                for role, values in (
                    ("from_space", from_spaces),
                    ("to_space", to_spaces),
                )
                for item in values[:5]
            ),
        )
    wall = target_record
    if target_record.ifc_class == "IfcOpeningElement":
        host_ids = target_record.facets.get("host_wall_global_ids", ())
        wall = (
            repository.get_by_global_id(str(host_ids[0]))
            if len(host_ids) == 1
            else None
        )
    if wall is None:
        return DoorResolutionDecision(
            status="clarification_required",
            reason_code="SPACE_SIDE_UNRESOLVED",
        )
    decision = resolve_space_viewpoint(
        wall_record=wall,
        from_space=from_spaces[0],
        to_space=to_spaces[0],
    )
    if decision["status"] != "resolved":
        return DoorResolutionDecision(
            status="clarification_required",
            reason_code=str(decision["reason_code"]),
        )
    updated_door = copy.deepcopy(dict(door))
    updated_door["viewpoint"] = {
        **copy.deepcopy(dict(viewpoint)),
        "observation_side": decision["observation_side"],
        "destination": decision["destination"],
        "derivation": decision["evidence"],
    }
    parameters["door"] = updated_door
    return None


def _resolve_position(
    *,
    operation_type: str,
    parameters: Mapping[str, Any],
    target_record: ElementRecord,
    overall_width_mm: Any,
) -> dict[str, Any]:
    if operation_type == FILL_DOOR_OPERATION:
        position = target_record.geometry_summary.get("wall_local_position_mm", {})
        center = _nonnegative_number(position.get("center_offset_mm"))
        if center is None:
            return _clarify(
                "OPENING_POSITION_UNAVAILABLE",
                ("/target_opening/wall_local_position",),
            )
        return {
            "status": "resolved",
            "value": {
                "reference": "wall_local_start",
                "center_offset_mm": center,
            },
            "derivation": {
                "source_anchor": f"opening:{target_record.ifc_global_id}",
                "formula": "existing_opening_center",
            },
        }

    position = parameters.get("position")
    if not isinstance(position, Mapping):
        return _clarify("DOOR_POSITION_REQUIRED", ("/parameters/position",))
    if any(
        key in position
        for key in ("project_x", "project_y", "project_z", "coordinates")
    ) or position.get("reference") == "project_coordinates":
        return _unsupported_mapping("PROJECT_COORDINATES_UNSUPPORTED")
    reference = str(position.get("reference", ""))
    if reference == "wall_local_start":
        center = _nonnegative_number(position.get("center_offset_mm"))
        if center is None:
            return _clarify(
                "DOOR_POSITION_REQUIRED",
                ("/parameters/position/center_offset_mm",),
            )
        return {
            "status": "resolved",
            "value": {
                "reference": "wall_local_start",
                "center_offset_mm": center,
            },
            "derivation": {
                "source_anchor": "wall_local_start",
                "formula": "identity",
            },
        }
    length = _wall_length(target_record)
    if length is None:
        return _clarify(
            "WALL_LENGTH_UNAVAILABLE",
            ("/target_wall/geometry/length",),
        )
    if reference == "wall_midpoint":
        center = length / 2.0
        return {
            "status": "resolved",
            "value": {
                "reference": "wall_local_start",
                "center_offset_mm": center,
            },
            "derivation": {
                "source_anchor": "wall_midpoint",
                "formula": "wall_length_mm / 2",
            },
        }
    if reference != "wall_end":
        return _clarify(
            "DOOR_POSITION_MEANING_REQUIRED",
            ("/parameters/position/reference",),
        )
    anchor = str(position.get("anchor", ""))
    measure_to = str(position.get("measure_to", ""))
    offset = _nonnegative_number(position.get("offset_mm"))
    if anchor not in {"start", "end"} or measure_to not in {
        "center",
        "nearest_edge",
    } or offset is None:
        return _clarify(
            "DOOR_POSITION_MEANING_REQUIRED",
            (
                "/parameters/position/anchor",
                "/parameters/position/measure_to",
                "/parameters/position/offset_mm",
            ),
        )
    distance_to_center = offset
    formula = "offset_mm"
    if measure_to == "nearest_edge":
        width = _positive_number(overall_width_mm)
        if width is None:
            return _clarify(
                "DOOR_OVERALL_DIMENSIONS_REQUIRED",
                ("/parameters/opening/width_mm",),
            )
        distance_to_center += width / 2.0
        formula = "offset_mm + overall_width_mm / 2"
    center = distance_to_center if anchor == "start" else length - distance_to_center
    if center < 0 or center > length:
        return _unsupported_mapping("DOOR_POSITION_OUTSIDE_WALL")
    return {
        "status": "resolved",
        "value": {
            "reference": "wall_local_start",
            "center_offset_mm": center,
        },
        "derivation": {
            "source_anchor": f"wall_local_{anchor}",
            "measure_to": measure_to,
            "formula": formula if anchor == "start" else f"wall_length_mm - ({formula})",
        },
    }


def _resolve_formal_operation(
    *,
    parameters: Mapping[str, Any],
    type_record: TypeRecord | None,
) -> dict[str, Any]:
    door = parameters.get("door")
    if not isinstance(door, Mapping):
        door = {}
    requested = door.get("operation_type")
    formal_type_operation = (
        None
        if type_record is None
        else type_record.formal_attributes.get("OperationType")
    )
    if formal_type_operation and formal_type_operation != "NOTDEFINED":
        if requested and str(requested) != str(formal_type_operation):
            return _clarify(
                "DOOR_TYPE_OPERATION_CONFLICT",
                ("/prototype_intent", "/parameters/door/operation_type"),
            )
        return {
            "status": "resolved",
            "operation_type": str(formal_type_operation),
            "derivation": {
                "source": f"door_style:{type_record.ifc_global_id}",
                "formal_attribute": "OperationType",
            },
        }
    if requested in UNSUPPORTED_COMPLEX_OPERATIONS:
        return _unsupported_mapping("DOOR_OPERATION_TYPE_UNSUPPORTED")
    if requested == "NOTDEFINED":
        if door.get("notdefined_accepted") is not True:
            return _clarify(
                "DOOR_NOTDEFINED_CONFIRMATION_REQUIRED",
                ("/parameters/door/notdefined_accepted",),
            )
        return {
            "status": "resolved",
            "operation_type": "NOTDEFINED",
            "derivation": {"source": "explicit_notdefined_acceptance"},
        }
    viewpoint = door.get("viewpoint")
    hinge_side = door.get("hinge_side")
    if requested in {"SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT"} and (
        door.get("formal_enum_explicit") is True
    ):
        return {
            "status": "resolved",
            "operation_type": str(requested),
            "derivation": {"source": "explicit_formal_enum"},
        }
    if hinge_side in {"left", "right"}:
        if not isinstance(viewpoint, Mapping):
            return _clarify(
                "DOOR_VIEWPOINT_REQUIRED",
                ("/parameters/door/viewpoint",),
            )
        observation_side = viewpoint.get("observation_side")
        destination = viewpoint.get("destination")
        if observation_side not in {"wall_positive", "wall_negative"} or not destination:
            return _clarify(
                "DOOR_VIEWPOINT_REQUIRED",
                (
                    "/parameters/door/viewpoint/observation_side",
                    "/parameters/door/viewpoint/destination",
                ),
            )
        left = hinge_side == "left"
        if observation_side == "wall_negative":
            left = not left
        return {
            "status": "resolved",
            "operation_type": (
                "SINGLE_SWING_LEFT" if left else "SINGLE_SWING_RIGHT"
            ),
            "derivation": {
                "source": "explicit_viewpoint",
                "observation_side": observation_side,
                "destination": destination,
                "hinge_side": hinge_side,
            },
        }
    return _clarify(
        "DOOR_OPERATION_REQUIRED",
        (
            "/parameters/door/operation_type",
            "/parameters/door/hinge_side",
            "/parameters/door/viewpoint",
        ),
    )


def _opening_topology_issue(record: ElementRecord) -> DoorResolutionDecision | None:
    if record.ifc_class != "IfcOpeningElement":
        return _unsupported("OPENING_TARGET_CLASS_REQUIRED")
    if record.facets.get("fill_state") == "filled":
        return _unsupported("OPENING_ALREADY_FILLED")
    if (
        not record.identity_reliable
        or record.facets.get("editable_target") is not True
        or record.geometry_capability != "measured_hosted_opening"
    ):
        return _unsupported("OPENING_TARGET_INVALID")
    return None


def _wall_length(record: ElementRecord) -> float | None:
    dimensions = record.geometry_summary.get("dimensions_mm", {})
    return _positive_number(dimensions.get("length"))


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def _nonnegative_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else None


def _clarify(reason_code: str, missing_slots: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "clarification_required",
        "reason_code": reason_code,
        "missing_slots": missing_slots,
    }


def _unsupported(reason_code: str) -> DoorResolutionDecision:
    return DoorResolutionDecision(status="unsupported", reason_code=reason_code)


def _unsupported_mapping(reason_code: str) -> dict[str, Any]:
    return {"status": "unsupported", "reason_code": reason_code}


def _digest(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "ADD_DOOR_OPERATION",
    "DIMENSION_MEANINGS",
    "DoorResolutionDecision",
    "FILL_DOOR_OPERATION",
    "SUPPORTED_GENERATED_OPERATIONS",
    "canonicalize_door_intent",
    "resolve_space_viewpoint",
    "resolve_door_parameters",
]
