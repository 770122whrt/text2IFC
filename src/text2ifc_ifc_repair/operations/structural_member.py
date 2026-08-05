"""Shared deterministic primitives for straight rectangular structural members."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence
import uuid

import ifcopenshell.guid

from text2ifc_ifc_repair.evaluation_policy import (
    STRUCTURAL_L1_CHECK_IDS,
    compare_structural_l1_measurement,
    structural_l1_authorization,
)
from text2ifc_ifc_repair.run_models import hash_json
from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations.hosted_opening import (
    millimetres_to_project_units,
    sorted_roots,
)
from text2ifc_ifc_repair.type_templates import ensure_bound_type


STRUCTURAL_TYPE_TEMPLATE_VERSION = "0.1"
_STRUCTURAL_TYPE_CONTRACTS = {
    "beam": {
        "ifc_class": "IfcBeamType",
        "template_id": "text2ifc-rectangular-beam-type",
        "section_keys": ("shape", "width_mm", "height_mm"),
    },
    "column": {
        "ifc_class": "IfcColumnType",
        "template_id": "text2ifc-rectangular-column-type",
        "section_keys": ("shape", "width_mm", "depth_mm"),
    },
}


def resolve_structural_member_frame(
    *,
    occurrence_class: str,
    axis_start_mm: Any,
    axis_end_mm: Any,
    section: Any,
) -> dict[str, Any]:
    """Validate and resolve one frozen straight rectangular member frame."""

    if occurrence_class not in {"IfcBeam", "IfcColumn"}:
        raise ValueError("STRUCTURAL_OCCURRENCE_CLASS_UNSUPPORTED")
    start = _point3(axis_start_mm)
    end = _point3(axis_end_mm)
    delta = tuple(end[index] - start[index] for index in range(3))
    extent = math.sqrt(sum(value * value for value in delta))
    if extent <= 0.0:
        raise ValueError("STRUCTURAL_AXIS_ZERO_LENGTH")
    axis_direction = tuple(value / extent for value in delta)
    canonical_section = _geometry_section(occurrence_class, section)

    if occurrence_class == "IfcBeam":
        if abs(delta[2]) > 1e-6:
            raise ValueError("STRUCTURAL_BEAM_NOT_HORIZONTAL")
        horizontal_extent = math.hypot(delta[0], delta[1])
        profile_x = (-delta[1] / horizontal_extent, delta[0] / horizontal_extent, 0.0)
        profile_y = (0.0, 0.0, 1.0)
        orientation = None
    else:
        if math.hypot(delta[0], delta[1]) > 1e-6:
            raise ValueError("STRUCTURAL_COLUMN_NOT_VERTICAL")
        if delta[2] <= 0.0:
            raise ValueError("STRUCTURAL_COLUMN_AXIS_DIRECTION_INVALID")
        orientation_value = canonical_section.get("orientation")
        if orientation_value is None:
            profile_x = None
            profile_y = None
            orientation = None
        else:
            x = float(orientation_value["x"])
            y = float(orientation_value["y"])
            magnitude = math.hypot(x, y)
            orientation = (x / magnitude, y / magnitude, 0.0)
            profile_x = orientation
            profile_y = (-orientation[1], orientation[0], 0.0)
    return {
        "axis_start_mm": start,
        "axis_end_mm": end,
        "axis_direction": axis_direction,
        "axis_extent_mm": extent,
        "profile_x_direction": profile_x,
        "profile_y_direction": profile_y,
        "orientation": orientation,
        "section": canonical_section,
    }


def structural_l1_comparison_report(
    *,
    family: str,
    operation: Mapping[str, Any],
    after_model: Any,
    application: Mapping[str, Any],
    role_mapping: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Measure one registered structural operation from reopened IFC only."""

    authorization = structural_l1_authorization(family)
    try:
        occurrence_class = {
            "beam": "IfcBeam",
            "column": "IfcColumn",
        }[family]
        type_class = {
            "beam": "IfcBeamType",
            "column": "IfcColumnType",
        }[family]
        start_key, end_key = {
            "beam": ("start", "end"),
            "column": ("base", "top"),
        }[family]
        roles = (
            {str(key): str(value) for key, value in role_mapping.items()}
            if role_mapping is not None
            else {
                str(item["role"]): str(item["global_id"])
                for change_kind in ("created", "modified", "removed")
                for item in application.get(change_kind, ())
                if item.get("role") and item.get("global_id")
            }
        )
        occurrence_id = roles[family]
        member = after_model.by_guid(occurrence_id)
        if member is None or not member.is_a(occurrence_class):
            raise ValueError("STRUCTURAL_L1_PRODUCT_UNRESOLVED")
        storey_id = str(operation["target"]["storey_global_id"])
        storey = after_model.by_guid(storey_id)
        if storey is None or not storey.is_a("IfcBuildingStorey"):
            raise ValueError("STRUCTURAL_L1_STOREY_UNRESOLVED")

        axis = operation["parameters"]["axis"]
        expected = resolve_structural_member_frame(
            occurrence_class=occurrence_class,
            axis_start_mm=_operation_point(axis[start_key]),
            axis_end_mm=_operation_point(axis[end_key]),
            section=operation["parameters"]["section"],
        )
        measured = measure_straight_rectangular_member(
            member, relative_to=storey
        )
        geometry = compare_structural_l1_measurement(
            family=family,
            expected=expected,
            measured=measured,
        )
        type_assignments = [
            item
            for item in operation.get("semantic_assignments", ())
            if item.get("fact_key") == "relationship:type"
        ]
        expected_type_id = (
            str(type_assignments[0]["value"])
            if len(type_assignments) == 1
            else ""
        )
        contained = [
            relation.RelatingStructure
            for relation in member.ContainedInStructure
            if relation.RelatingStructure.is_a("IfcBuildingStorey")
        ]
        typed = [
            relation.RelatingType
            for relation in member.IsDefinedBy
            if relation.is_a("IfcRelDefinesByType")
        ]
        product_ok = (
            str(member.GlobalId) == occurrence_id
            and member.is_a() == occurrence_class
            and measured.get("representation_type") == "SweptSolid"
            and not getattr(member, "HasStructuralMember", ())
        )
        relationships_ok = (
            contained == [storey]
            and len(typed) == 1
            and typed[0].is_a(type_class)
            and str(typed[0].GlobalId) == expected_type_id
        )

        def exact_check(
            passed: bool,
            reason: str,
            expected_value: Any,
            actual_value: Any,
        ) -> dict[str, Any]:
            return {
                "status": "passed" if passed else "failed",
                "reason": reason,
                "expected": expected_value,
                "actual": actual_value,
            }

        l1_checks = {
            **geometry["l1_checks"],
            "l1.structural.product": exact_check(
                product_ok,
                "The reopened product must be one physical member of the registered IFC class.",
                {
                    "global_id": occurrence_id,
                    "ifc_class": occurrence_class,
                    "representation_type": "SweptSolid",
                    "analysis_relationship_count": 0,
                },
                {
                    "global_id": str(member.GlobalId),
                    "ifc_class": member.is_a(),
                    "representation_type": measured.get("representation_type"),
                    "analysis_relationship_count": len(
                        getattr(member, "HasStructuralMember", ())
                    ),
                },
            ),
            "l1.structural.relationships": exact_check(
                relationships_ok,
                "The member must have exactly one declared Storey and one declared Type binding.",
                {
                    "storey_global_ids": [storey_id],
                    "type_global_ids": [expected_type_id],
                    "type_ifc_class": type_class,
                },
                {
                    "storey_global_ids": [
                        str(item.GlobalId) for item in contained
                    ],
                    "type_global_ids": [str(item.GlobalId) for item in typed],
                    "type_ifc_classes": [item.is_a() for item in typed],
                },
            ),
        }
        issues = [
            {
                "code": check_id.upper().replace(".", "_"),
                "path": "/evaluation/L1",
                "message": str(check["reason"]),
            }
            for check_id, check in l1_checks.items()
            if check["status"] != "passed"
        ]
        return {
            "valid": not issues,
            "checks": {
                check_id: check["status"] == "passed"
                for check_id, check in l1_checks.items()
            },
            "metrics": geometry["metrics"],
            "measurement": measured,
            "issues": issues,
            "authorization": authorization,
            "l1_checks": l1_checks,
        }
    except Exception as error:
        detail = f"{type(error).__name__}: {error}"
        return {
            "valid": False,
            "checks": {},
            "metrics": {},
            "issues": [
                {
                    "code": "STRUCTURAL_L1_NOT_EVALUABLE",
                    "path": "/evaluation/L1",
                    "message": detail,
                }
            ],
            "authorization": authorization,
            "l1_checks": {
                check_id: {
                    "status": "not_evaluable",
                    "reason": "Mandatory structural geometry or relationships could not be measured from reopened IFC.",
                    "expected": "measurable reopened structural evidence",
                    "actual": detail,
                }
                for check_id in STRUCTURAL_L1_CHECK_IDS
            },
        }


def _operation_point(value: Any) -> tuple[float, float, float]:
    if not isinstance(value, Mapping):
        raise ValueError("STRUCTURAL_AXIS_INVALID")
    return tuple(float(value[key]) for key in ("x_mm", "y_mm", "z_mm"))


def create_straight_rectangular_member(
    *,
    model: Any,
    occurrence_class: str,
    occurrence_global_id: str,
    operation_id: str,
    axis_start_mm: Any,
    axis_end_mm: Any,
    section: Any,
    storey: Any,
    owner_history: Any,
    representation_context: Any,
) -> dict[str, Any]:
    """Create one IFC2X3 straight rectangular member in Storey-local space."""

    frame = resolve_structural_member_frame(
        occurrence_class=occurrence_class,
        axis_start_mm=axis_start_mm,
        axis_end_mm=axis_end_mm,
        section=section,
    )
    if not storey.is_a("IfcBuildingStorey"):
        raise ValueError("STRUCTURAL_STOREY_REQUIRED")
    if not owner_history.is_a("IfcOwnerHistory"):
        raise ValueError("STRUCTURAL_OWNER_HISTORY_REQUIRED")
    if not representation_context.is_a("IfcRepresentationContext"):
        raise ValueError("STRUCTURAL_REPRESENTATION_CONTEXT_REQUIRED")
    try:
        existing = model.by_guid(str(occurrence_global_id))
    except RuntimeError:
        existing = None
    if existing is not None:
        raise ValueError("STRUCTURAL_GLOBAL_ID_COLLISION")

    section_value = frame["section"]
    second_key = "height_mm" if occurrence_class == "IfcBeam" else "depth_mm"
    profile = model.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        ProfileName=None,
        Position=model.create_entity(
            "IfcAxis2Placement2D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
            RefDirection=None,
        ),
        XDim=millimetres_to_project_units(model, section_value["width_mm"]),
        YDim=millimetres_to_project_units(model, section_value[second_key]),
    )
    if occurrence_class == "IfcBeam":
        solid_axis = (1.0, 0.0, 0.0)
        solid_ref_direction = (0.0, 1.0, 0.0)
    else:
        solid_axis = (0.0, 0.0, 1.0)
        solid_ref_direction = (1.0, 0.0, 0.0)
    solid = model.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=_axis2placement3d(
            model,
            location=(0.0, 0.0, 0.0),
            axis=solid_axis,
            ref_direction=solid_ref_direction,
        ),
        ExtrudedDirection=model.create_entity(
            "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
        ),
        Depth=millimetres_to_project_units(model, frame["axis_extent_mm"]),
    )
    representation = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=representation_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid],
    )
    product_shape = model.create_entity(
        "IfcProductDefinitionShape", Representations=[representation]
    )
    orientation = frame["axis_direction"] if occurrence_class == "IfcBeam" else frame["orientation"]
    object_placement = _member_local_placement(
        model,
        storey=storey,
        start_mm=frame["axis_start_mm"],
        ref_direction=orientation,
    )
    family = occurrence_class.removeprefix("Ifc").lower()
    occurrence = model.create_entity(
        occurrence_class,
        GlobalId=str(occurrence_global_id),
        OwnerHistory=owner_history,
        Name=f"Text2IFC {family} {operation_id}",
        ObjectType=family.title(),
        ObjectPlacement=object_placement,
        Representation=product_shape,
        Tag=str(operation_id),
    )
    measurement = measure_straight_rectangular_member(
        occurrence,
        relative_to=storey,
    )
    return {
        "occurrence": occurrence,
        "representation": representation,
        "measurement": measurement,
    }


def bind_structural_type(
    *,
    model: Any,
    occurrence: Any,
    assignment: Mapping[str, Any],
    owner_history: Any,
    operation_id: str,
    expected_ifc_class: str,
    generated_type_factory: Any,
    factory_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind one exact/generated structural Type without copying semantics.

    Material and Pset assignments remain in the common semantic-authoring
    stage.  This function creates or extends only `IfcRelDefinesByType`.
    """

    expected_occurrence_class = expected_ifc_class.removesuffix("Type")
    if expected_ifc_class not in {"IfcBeamType", "IfcColumnType"}:
        raise ValueError("STRUCTURAL_TYPE_CLASS_UNSUPPORTED")
    if not occurrence.is_a(expected_occurrence_class):
        raise ValueError("STRUCTURAL_TYPE_OCCURRENCE_CLASS_MISMATCH")
    bound_type, generated = ensure_bound_type(
        model,
        assignment,
        owner_history=owner_history,
        operation_id=operation_id,
        expected_ifc_class=expected_ifc_class,
        generated_type_factory=generated_type_factory,
        factory_context=factory_context,
    )
    relations = [
        relation
        for relation in bound_type.ObjectTypeOf
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(relations) > 1:
        raise ValueError("STRUCTURAL_TYPE_RELATIONSHIP_AMBIGUOUS")
    created: list[dict[str, str]] = []
    modified: list[dict[str, str]] = []
    if relations:
        relationship = relations[0]
        relationship.RelatedObjects = sorted_roots(
            [*relationship.RelatedObjects, occurrence]
        )
        modified.append(
            {
                "role": "structural_type_relationship",
                "ifc_class": relationship.is_a(),
                "global_id": str(relationship.GlobalId),
            }
        )
    else:
        relationship = model.create_entity(
            "IfcRelDefinesByType",
            GlobalId=_structural_relationship_global_id(
                operation_id=operation_id,
                occurrence_global_id=str(occurrence.GlobalId),
                type_global_id=str(bound_type.GlobalId),
            ),
            OwnerHistory=owner_history,
            RelatedObjects=[occurrence],
            RelatingType=bound_type,
        )
        created.append(
            {
                "role": "structural_type_relationship",
                "ifc_class": relationship.is_a(),
                "global_id": str(relationship.GlobalId),
            }
        )
    if generated:
        created.insert(
            0,
            {
                "role": "structural_type",
                "ifc_class": bound_type.is_a(),
                "global_id": str(bound_type.GlobalId),
            },
        )
    return {
        "type": bound_type,
        "relationship": relationship,
        "generated": generated,
        "created": created,
        "modified": modified,
        "semantic_target_role": expected_occurrence_class.removeprefix("Ifc").lower(),
    }


def _structural_relationship_global_id(
    *,
    operation_id: str,
    occurrence_global_id: str,
    type_global_id: str,
) -> str:
    value = uuid.uuid5(
        uuid.NAMESPACE_URL,
        "https://text2ifc.local/ifc-repair/structural-type/"
        f"{operation_id}/{occurrence_global_id}/{type_global_id}",
    )
    return ifcopenshell.guid.compress(value.hex)


def _point3(value: Any) -> tuple[float, float, float]:
    if (
        isinstance(value, (str, bytes, Mapping))
        or not isinstance(value, Sequence)
        or len(value) != 3
    ):
        raise ValueError("STRUCTURAL_AXIS_INVALID")
    result: list[float] = []
    for raw in value:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("STRUCTURAL_AXIS_INVALID")
        number = float(raw)
        if not math.isfinite(number):
            raise ValueError("STRUCTURAL_AXIS_INVALID")
        result.append(number)
    return result[0], result[1], result[2]


def _geometry_section(occurrence_class: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("shape") != "rectangle":
        raise ValueError("STRUCTURAL_SECTION_UNSUPPORTED")
    keys = {str(key) for key in value}
    if "length_mm" in keys or (
        occurrence_class == "IfcColumn" and "height_mm" in keys
    ):
        raise ValueError("STRUCTURAL_SCALAR_EXTENT_UNSUPPORTED")
    if occurrence_class == "IfcBeam" and any(
        key in keys for key in ("orientation", "rotation", "rotation_degrees")
    ):
        raise ValueError("STRUCTURAL_SECTION_ROTATION_UNSUPPORTED")
    dimension_keys = (
        ("width_mm", "height_mm")
        if occurrence_class == "IfcBeam"
        else ("width_mm", "depth_mm")
    )
    allowed = {"shape", *dimension_keys}
    if occurrence_class == "IfcColumn":
        allowed.add("orientation")
    if keys != allowed and not (
        occurrence_class == "IfcColumn" and keys == allowed - {"orientation"}
    ):
        raise ValueError("STRUCTURAL_SECTION_INVALID")
    canonical: dict[str, Any] = {"shape": "rectangle"}
    for key in dimension_keys:
        raw = value.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("STRUCTURAL_SECTION_INVALID")
        number = float(raw)
        if not math.isfinite(number) or number <= 0.0:
            raise ValueError("STRUCTURAL_SECTION_INVALID")
        canonical[key] = number

    if occurrence_class == "IfcColumn":
        orientation = value.get("orientation")
        non_square = not math.isclose(
            canonical["width_mm"],
            canonical["depth_mm"],
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        if orientation is None:
            if non_square:
                raise ValueError("STRUCTURAL_COLUMN_ORIENTATION_REQUIRED")
        else:
            if not isinstance(orientation, Mapping) or set(orientation) != {"x", "y"}:
                raise ValueError("STRUCTURAL_COLUMN_ORIENTATION_INVALID")
            components: dict[str, float] = {}
            for key in ("x", "y"):
                raw = orientation.get(key)
                if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                    raise ValueError("STRUCTURAL_COLUMN_ORIENTATION_INVALID")
                number = float(raw)
                if not math.isfinite(number):
                    raise ValueError("STRUCTURAL_COLUMN_ORIENTATION_INVALID")
                components[key] = number
            if math.hypot(components["x"], components["y"]) <= 0.0:
                raise ValueError("STRUCTURAL_COLUMN_ORIENTATION_INVALID")
            canonical["orientation"] = components
    return canonical


def _axis2placement3d(
    model: Any,
    *,
    location: tuple[float, float, float],
    axis: tuple[float, float, float],
    ref_direction: tuple[float, float, float] | None,
) -> Any:
    return model.create_entity(
        "IfcAxis2Placement3D",
        Location=model.create_entity("IfcCartesianPoint", Coordinates=location),
        Axis=model.create_entity("IfcDirection", DirectionRatios=axis),
        RefDirection=(
            model.create_entity("IfcDirection", DirectionRatios=ref_direction)
            if ref_direction is not None
            else None
        ),
    )


def _member_local_placement(
    model: Any,
    *,
    storey: Any,
    start_mm: tuple[float, float, float],
    ref_direction: tuple[float, float, float] | None,
) -> Any:
    location = tuple(
        millimetres_to_project_units(model, value) for value in start_mm
    )
    relative = _axis2placement3d(
        model,
        location=location,
        axis=(0.0, 0.0, 1.0),
        ref_direction=ref_direction,
    )
    return model.create_entity(
        "IfcLocalPlacement",
        PlacementRelTo=storey.ObjectPlacement,
        RelativePlacement=relative,
    )


def generated_beam_type_template(
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    del request_hash, model_fingerprint
    return _generated_structural_type_template(
        family="beam",
        operation_id=operation_id,
        resolved_operation=resolved_operation,
    )


def generated_column_type_template(
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    del request_hash, model_fingerprint
    return _generated_structural_type_template(
        family="column",
        operation_id=operation_id,
        resolved_operation=resolved_operation,
    )


def create_generated_beam_type(
    *,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    return _create_generated_structural_type(
        family="beam",
        model=model,
        global_id=global_id,
        owner_history=owner_history,
        operation_id=operation_id,
        derivation=derivation,
        context=context,
    )


def create_generated_column_type(
    *,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    return _create_generated_structural_type(
        family="column",
        model=model,
        global_id=global_id,
        owner_history=owner_history,
        operation_id=operation_id,
        derivation=derivation,
        context=context,
    )


def _generated_structural_type_template(
    *,
    family: str,
    operation_id: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    contract = _contract(family)
    section = _canonical_section(
        family,
        _type_section_input(
            family,
            getattr(resolved_operation, "parameters", {}).get("section"),
        ),
    )
    return {
        "template_id": contract["template_id"],
        "template_version": STRUCTURAL_TYPE_TEMPLATE_VERSION,
        "ifc_class": contract["ifc_class"],
        **_structural_template_payload(
            family=family,
            operation_id=operation_id,
            section=section,
        ),
    }


def _create_generated_structural_type(
    *,
    family: str,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    contract = _contract(family)
    if str(derivation.get("template_id")) != contract["template_id"]:
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_ID_MISMATCH")
    if (
        str(derivation.get("template_version"))
        != STRUCTURAL_TYPE_TEMPLATE_VERSION
    ):
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_VERSION_MISMATCH")
    if dict(derivation.get("formal_attributes", {})):
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_MISMATCH")

    section = _canonical_section(
        family,
        _type_section_input(family, context.get("section")),
    )
    template = derivation.get("template")
    if not isinstance(template, Mapping):
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_MISMATCH")
    if template.get("section") != section:
        raise ValueError("GENERATED_STRUCTURAL_SECTION_MISMATCH")
    expected = _structural_template_payload(
        family=family,
        operation_id=operation_id,
        section=section,
    )
    if dict(template) != expected:
        raise ValueError("GENERATED_STRUCTURAL_TEMPLATE_MISMATCH")

    name = str(expected["name"])
    return model.create_entity(
        contract["ifc_class"],
        GlobalId=global_id,
        OwnerHistory=owner_history,
        Name=name,
        Description=(
            f"{contract['template_id']}/{STRUCTURAL_TYPE_TEMPLATE_VERSION}"
        ),
        ElementType=name,
        PredefinedType="NOTDEFINED",
    )


def _structural_template_payload(
    *,
    family: str,
    operation_id: str,
    section: Mapping[str, Any],
) -> dict[str, Any]:
    contract = _contract(family)
    canonical_section = dict(section)
    return {
        "name": f"Text2IFC generated {family} type {operation_id}",
        "predefined_type": "NOTDEFINED",
        "section": canonical_section,
        "section_digest": hash_json(
            {
                "ifc_class": contract["ifc_class"],
                "section": canonical_section,
            }
        ),
    }


def _canonical_section(family: str, value: Any) -> dict[str, Any]:
    contract = _contract(family)
    if not isinstance(value, Mapping):
        raise ValueError("GENERATED_STRUCTURAL_SECTION_REQUIRED")
    keys = tuple(str(key) for key in value)
    expected_keys = tuple(contract["section_keys"])
    if set(keys) != set(expected_keys) or value.get("shape") != "rectangle":
        raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
    result: dict[str, Any] = {"shape": "rectangle"}
    for key in expected_keys[1:]:
        raw = value.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
        number = float(raw)
        if not math.isfinite(number) or number <= 0.0:
            raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
        result[key] = number
    return result


def _type_section_input(family: str, value: Any) -> Mapping[str, Any]:
    """Project canonical occurrence geometry onto the frozen Type section."""

    contract = _contract(family)
    if not isinstance(value, Mapping):
        raise ValueError("GENERATED_STRUCTURAL_SECTION_REQUIRED")
    expected_keys = set(contract["section_keys"])
    actual_keys = {str(key) for key in value}
    if actual_keys == expected_keys:
        return value
    if family != "column" or actual_keys != expected_keys | {"orientation"}:
        raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")

    orientation = value.get("orientation")
    if not isinstance(orientation, Mapping) or set(orientation) != {"x", "y"}:
        raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
    components: list[float] = []
    for key in ("x", "y"):
        raw = orientation.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
        number = float(raw)
        if not math.isfinite(number):
            raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
        components.append(number)
    if math.hypot(*components) <= 0.0:
        raise ValueError("GENERATED_STRUCTURAL_SECTION_INVALID")
    return {key: value[key] for key in contract["section_keys"]}


def _contract(family: str) -> Mapping[str, Any]:
    try:
        return _STRUCTURAL_TYPE_CONTRACTS[family]
    except KeyError as error:
        raise ValueError("GENERATED_STRUCTURAL_FAMILY_UNSUPPORTED") from error


__all__ = [
    "STRUCTURAL_TYPE_TEMPLATE_VERSION",
    "bind_structural_type",
    "create_straight_rectangular_member",
    "create_generated_beam_type",
    "create_generated_column_type",
    "generated_beam_type_template",
    "generated_column_type_template",
    "resolve_structural_member_frame",
    "structural_l1_comparison_report",
]
