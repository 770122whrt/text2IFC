"""Pure deterministic policy for IFC2X3 Door intent canonicalization."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from .index_models import ElementRecord, TypeRecord


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

    del repository, context
    decision = canonicalize_door_intent(
        operation_type=str(operation.get("operation_type", "")),
        parameters=operation.get("parameters", {}),
        target_record=target_record,
        type_record=type_record,
    )
    return decision.to_dict()


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
    "resolve_door_parameters",
]
