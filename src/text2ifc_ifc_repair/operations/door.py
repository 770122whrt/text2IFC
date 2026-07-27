"""Deterministic IFC2X3 Door authoring for new or surviving Openings."""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping

import ifcopenshell.api.geometry

from text2ifc_ifc_repair.door_resolution import resolve_door_parameters
from text2ifc_ifc_repair.evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SemanticApplicability,
    SemanticFactSpec,
)
from text2ifc_ifc_repair.geometry import (
    opening_dimensions_mm,
    opening_position_in_wall_mm,
)
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistryError
from text2ifc_ifc_repair.semantic_facts import SemanticFact
from text2ifc_ifc_repair.type_templates import ensure_bound_type

from .hosted_opening import (
    add_to_containment,
    assert_ids_available,
    body_context,
    check_hosted_opening_preconditions,
    create_hosted_opening,
    deterministic_global_id,
    hosted_opening_conflict_checker,
    local_placement,
    require_guid,
    sorted_roots,
    wall_containment,
)


ADD_OPERATION_TYPE = "add_door_with_opening_to_wall"
FILL_OPERATION_TYPE = "fill_existing_opening_with_door"
_ADD_TARGET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["wall_global_id"],
    "properties": {"wall_global_id": {"type": "string", "minLength": 1}},
}
_FILL_TARGET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["opening_global_id"],
    "properties": {
        "opening_global_id": {"type": "string", "minLength": 1}
    },
}
_CANONICAL_PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "required": ["position", "opening", "door"],
    "properties": {
        "position": {
            "type": "object",
            "additionalProperties": True,
            "required": ["reference", "center_offset_mm"],
            "properties": {
                "reference": {"const": "wall_local_start"},
                "center_offset_mm": {"type": "number", "minimum": 0},
            },
        },
        "opening": {
            "type": "object",
            "additionalProperties": True,
            "required": ["width_mm", "height_mm", "sill_height_mm"],
            "properties": {
                "width_mm": {"type": "number", "exclusiveMinimum": 0},
                "height_mm": {"type": "number", "exclusiveMinimum": 0},
                "sill_height_mm": {"type": "number", "minimum": 0},
            },
        },
        "door": {
            "type": "object",
            "additionalProperties": True,
            "required": [
                "overall_width_mm",
                "overall_height_mm",
                "operation_type",
            ],
            "properties": {
                "overall_width_mm": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                },
                "overall_height_mm": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                },
                "operation_type": {
                    "enum": [
                        "SINGLE_SWING_LEFT",
                        "SINGLE_SWING_RIGHT",
                        "NOTDEFINED",
                    ]
                },
            },
        },
        "host_wall_global_id": {"type": "string", "minLength": 1},
    },
}
_SOURCES = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.SURVIVING_HOST,
    EvidenceSourceKind.SURVIVING_TYPE,
    EvidenceSourceKind.APPROVED_PROTOTYPE,
    EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
    EvidenceSourceKind.PRIVATE_ORIGINAL,
)


def _policy(operation_type: str, suffix: str) -> OperationEvaluationPolicy:
    def fact(
        check_id: str,
        pattern: str,
        applicability: SemanticApplicability,
    ) -> SemanticFactSpec:
        return SemanticFactSpec(
            check_id,
            "0.1",
            pattern,
            applicability,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        )

    return OperationEvaluationPolicy(
        policy_id=f"door.{suffix}.l2",
        version="0.1",
        operation_type=operation_type,
        semantic_role="door",
        semantic_facts=(
            fact("door.type", "relationship:type", SemanticApplicability.REQUIRED),
            fact("door.host", "relationship:host", SemanticApplicability.REQUIRED),
            fact("door.storey", "relationship:storey", SemanticApplicability.REQUIRED),
            fact("door.width", "attribute:OverallWidth", SemanticApplicability.REQUIRED),
            fact("door.height", "attribute:OverallHeight", SemanticApplicability.REQUIRED),
            fact("door.pset", "pset:*", SemanticApplicability.CONDITIONAL),
            fact("door.quantity", "quantity:*", SemanticApplicability.CONDITIONAL),
            fact("door.material", "material:*", SemanticApplicability.CONDITIONAL),
            fact(
                "door.classification",
                "classification:*",
                SemanticApplicability.CONDITIONAL,
            ),
        ),
        target_authority_mode="host_for_created_entity",
    )


ADD_DOOR_EVALUATION_POLICY = _policy(ADD_OPERATION_TYPE, "add-with-opening")
FILL_DOOR_EVALUATION_POLICY = _policy(
    FILL_OPERATION_TYPE, "fill-existing-opening"
)


def add_door_operation_definition() -> OperationDefinition:
    return _definition(
        operation_type=ADD_OPERATION_TYPE,
        target_classes=("IfcWall",),
        target_schema=_ADD_TARGET_SCHEMA,
        evaluation_policy=ADD_DOOR_EVALUATION_POLICY,
        prompt_profile_id="door.add-with-opening",
        applicator=_add_door_applicator,
        precondition_checker=_add_preconditions,
    )


def fill_door_operation_definition() -> OperationDefinition:
    return _definition(
        operation_type=FILL_OPERATION_TYPE,
        target_classes=("IfcOpeningElement",),
        target_schema=_FILL_TARGET_SCHEMA,
        evaluation_policy=FILL_DOOR_EVALUATION_POLICY,
        prompt_profile_id="door.fill-existing-opening",
        applicator=_fill_door_applicator,
        precondition_checker=_fill_preconditions,
    )


def _definition(
    *,
    operation_type: str,
    target_classes: tuple[str, ...],
    target_schema: Mapping[str, Any],
    evaluation_policy: OperationEvaluationPolicy,
    prompt_profile_id: str,
    applicator: Any,
    precondition_checker: Any,
) -> OperationDefinition:
    return OperationDefinition(
        operation_type=operation_type,
        target_ifc_classes=target_classes,
        parameter_schema=_CANONICAL_PARAMETER_SCHEMA,
        target_schema=target_schema,
        context_adapter=_context_adapter,
        precondition_checker=precondition_checker,
        applicator=applicator,
        postcondition_checker=_postconditions,
        comparison_adapter=_comparison_adapter,
        capability_constraints={
            "ifc_schemas": ["IFC2X3"],
            "wall_geometry": ["straight_wall"],
            "door_operations": [
                "SINGLE_SWING_LEFT",
                "SINGLE_SWING_RIGHT",
                "NOTDEFINED",
            ],
            "shared_type_mutation": False,
        },
        prototype_ifc_classes=("IfcDoorStyle",),
        prototype_dimension_paths={
            "width_mm": ("opening", "width_mm"),
            "height_mm": ("opening", "height_mm"),
        },
        precondition_names=(
            "target_exists",
            "opening_available",
            "opening_within_wall",
        ),
        postcondition_names=(
            "door_fills_opening",
            "door_contained_in_storey",
            "door_type_bound",
        ),
        evaluation_policy=evaluation_policy,
        semantic_policy_fact_builder=_semantic_policy_facts,
        editable_occurrence_ifc_class="IfcDoor",
        inherited_type_evidence_role="IfcDoorStyle",
        generated_type_template=_generated_door_type_template,
        generated_type_factory=_create_generated_door_style,
        prompt_profile_id=prompt_profile_id,
        semantic_scope_roles={
            "door": "door_occurrence",
            "opening": "opening_occurrence",
        },
        conflict_domain="hosted_opening",
        intent_policy_checker=_intent_policy_checker,
        parameter_resolver=resolve_door_parameters,
        operation_conflict_checker=hosted_opening_conflict_checker,
    )


def _context_adapter(
    *,
    operation: Mapping[str, Any],
    target: Any,
    storey: str,
) -> dict[str, Any]:
    del operation
    return {
        "record_id": f"ifc:{target.GlobalId}",
        "ifc_global_id": str(target.GlobalId),
        "ifc_class": target.is_a(),
        "name": None if target.Name is None else str(target.Name),
        "storey_name": storey,
    }


def _intent_policy_checker(**kwargs: Any) -> dict[str, Any]:
    del kwargs
    return {"status": "resolved"}


def _add_preconditions(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    return check_hosted_opening_preconditions(operation=operation, model=model)


def _fill_preconditions(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    try:
        opening = require_guid(
            model,
            str(operation["target"]["opening_global_id"]),
            "IfcOpeningElement",
        )
    except OperationRegistryError as error:
        return _issue(error.code, "/target/opening_global_id", error.detail)
    if len(opening.HasFillings) != 0:
        return _issue(
            "OPENING_ALREADY_FILLED",
            "/target/opening_global_id",
            str(opening.GlobalId),
        )
    if len(opening.VoidsElements) != 1:
        return _issue(
            "OPENING_TARGET_INVALID",
            "/target/opening_global_id",
            str(opening.GlobalId),
        )
    wall = opening.VoidsElements[0].RelatingBuildingElement
    if str(wall.GlobalId) != str(
        operation["parameters"].get("host_wall_global_id")
    ):
        return _issue(
            "OPENING_HOST_MISMATCH",
            "/parameters/host_wall_global_id",
            str(wall.GlobalId),
        )
    return {
        "checks": [
            {
                "code": "EMPTY_OPENING_AVAILABLE",
                "status": "passed",
                "evidence": {
                    "opening_global_id": str(opening.GlobalId),
                    "host_wall_global_id": str(wall.GlobalId),
                },
            }
        ],
        "issues": [],
        "evidence": {"opening_global_id": str(opening.GlobalId)},
    }


def _add_door_applicator(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    wall = require_guid(
        model, str(operation["target"]["wall_global_id"]), "IfcWall"
    )
    hosted = create_hosted_opening(
        model=model, operation=operation, wall=wall
    )
    return _create_door(
        model=model,
        operation=operation,
        wall=wall,
        opening=hosted["opening"],
        opening_depth_mm=float(hosted["opening_depth_mm"]),
        created_opening=hosted,
    )


def _fill_door_applicator(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    opening = require_guid(
        model,
        str(operation["target"]["opening_global_id"]),
        "IfcOpeningElement",
    )
    if len(opening.HasFillings) or len(opening.VoidsElements) != 1:
        raise OperationRegistryError(
            "OPENING_TARGET_INVALID", str(opening.GlobalId)
        )
    wall = opening.VoidsElements[0].RelatingBuildingElement
    dimensions = opening_dimensions_mm(opening)
    return _create_door(
        model=model,
        operation=operation,
        wall=wall,
        opening=opening,
        opening_depth_mm=float(dimensions["depth"]),
        created_opening=None,
    )


def _create_door(
    *,
    model: Any,
    operation: Mapping[str, Any],
    wall: Any,
    opening: Any,
    opening_depth_mm: float,
    created_opening: Mapping[str, Any] | None,
) -> dict[str, Any]:
    door_id = deterministic_global_id(operation, "door")
    fill_id = deterministic_global_id(operation, "fills_relationship")
    assert_ids_available(model, (door_id, fill_id))
    door_parameters = operation["parameters"]["door"]
    width = float(door_parameters["overall_width_mm"])
    height = float(door_parameters["overall_height_mm"])
    assignment = next(
        (
            item
            for item in operation.get("semantic_assignments", ())
            if item.get("fact_key") == "relationship:type"
        ),
        None,
    )
    door_style = None
    generated = False
    if assignment is not None:
        door_style, generated = ensure_bound_type(
            model,
            assignment,
            owner_history=wall.OwnerHistory,
            operation_id=str(operation["operation_id"]),
            expected_ifc_class="IfcDoorStyle",
            generated_type_factory=_create_generated_door_style,
            factory_context={
                "width_mm": width,
                "height_mm": height,
                "depth_mm": opening_depth_mm,
            },
        )
    door = model.create_entity(
        "IfcDoor",
        GlobalId=door_id,
        OwnerHistory=wall.OwnerHistory,
        Name=f"Text2IFC door {operation['operation_id']}",
        ObjectType=(
            str(door_style.Name) if door_style is not None else "Text2IFC door"
        ),
        Tag=str(operation["operation_id"]),
        OverallHeight=height,
        OverallWidth=width,
    )
    if door_style is not None and door_style.RepresentationMaps:
        representations = [
            ifcopenshell.api.geometry.map_representation(
                model,
                representation=item.MappedRepresentation,
            )
            for item in door_style.RepresentationMaps
        ]
    else:
        representations = [
            ifcopenshell.api.geometry.add_wall_representation(
                model,
                context=body_context(model),
                length=width / 1000.0,
                height=height / 1000.0,
                thickness=min(opening_depth_mm, 50.0) / 1000.0,
                offset=-min(opening_depth_mm, 50.0) / 2000.0,
            )
        ]
    door.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=representations
    )
    door.ObjectPlacement = local_placement(
        model,
        relative_to=opening.ObjectPlacement,
        location=(0.0, 0.0, 0.0),
    )
    fill = model.create_entity(
        "IfcRelFillsElement",
        GlobalId=fill_id,
        OwnerHistory=wall.OwnerHistory,
        RelatingOpeningElement=opening,
        RelatedBuildingElement=door,
    )
    modified = []
    created_type_relation = None
    if door_style is not None:
        relation = next(iter(door_style.ObjectTypeOf), None)
        if relation is None:
            relation = model.create_entity(
                "IfcRelDefinesByType",
                GlobalId=deterministic_global_id(
                    operation, "type_relationship"
                ),
                OwnerHistory=wall.OwnerHistory,
                RelatedObjects=[door],
                RelatingType=door_style,
            )
            created_type_relation = relation
        else:
            relation.RelatedObjects = sorted_roots(
                [*relation.RelatedObjects, door]
            )
        if created_type_relation is None:
            modified.append(
                {
                    "role": "door_type_relationship",
                    "global_id": str(relation.GlobalId),
                }
            )
    containment = wall_containment(wall)
    add_to_containment(containment, door)
    modified.append(
        {
            "role": "spatial_containment",
            "global_id": str(containment.GlobalId),
        }
    )
    created = [
        *(
            [
                {
                    "role": "opening",
                    "ifc_class": created_opening["opening"].is_a(),
                    "global_id": str(created_opening["opening"].GlobalId),
                },
                {
                    "role": "voids_relationship",
                    "ifc_class": created_opening[
                        "voids_relationship"
                    ].is_a(),
                    "global_id": str(
                        created_opening["voids_relationship"].GlobalId
                    ),
                },
            ]
            if created_opening is not None
            else []
        ),
        *(
            [
                {
                    "role": "generated_door_type",
                    "ifc_class": door_style.is_a(),
                    "global_id": str(door_style.GlobalId),
                }
            ]
            if generated
            else []
        ),
        *(
            [
                {
                    "role": "door_type_relationship",
                    "ifc_class": created_type_relation.is_a(),
                    "global_id": str(created_type_relation.GlobalId),
                }
            ]
            if created_type_relation is not None
            else []
        ),
        {"role": "door", "ifc_class": door.is_a(), "global_id": door_id},
        {
            "role": "fills_relationship",
            "ifc_class": fill.is_a(),
            "global_id": fill_id,
        },
    ]
    return {
        "created": created,
        "modified": [
            {"role": "host_wall", "global_id": str(wall.GlobalId)},
            *modified,
        ],
        "removed": [],
        "resolved": {
            "opening_global_id": str(opening.GlobalId),
            "door_type_global_id": (
                None if door_style is None else str(door_style.GlobalId)
            ),
            "opening_depth_mm": opening_depth_mm,
        },
    }


def _create_generated_door_style(
    *,
    model: Any,
    global_id: str,
    owner_history: Any,
    operation_id: str,
    derivation: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    formal = derivation["formal_attributes"]
    template = derivation["template"]
    style = model.create_entity(
        "IfcDoorStyle",
        GlobalId=global_id,
        OwnerHistory=owner_history,
        Name=str(
            template.get("name")
            or f"Text2IFC generated door type {operation_id}"
        ),
        Description="text2ifc-door-single-swing-template/0.1",
        ConstructionType=str(
            formal.get("construction_type", "NOTDEFINED")
        ),
        OperationType=str(formal["operation_type"]),
        ParameterTakesPrecedence=bool(
            formal.get("parameter_takes_precedence", False)
        ),
        Sizeable=bool(formal.get("sizeable", False)),
    )
    width = float(context["width_mm"])
    height = float(context["height_mm"])
    depth = min(float(context["depth_mm"]), 50.0)
    representation = ifcopenshell.api.geometry.add_wall_representation(
        model,
        context=body_context(model),
        length=width / 1000.0,
        height=height / 1000.0,
        thickness=depth / 1000.0,
        offset=-depth / 2000.0,
    )
    origin = model.create_entity(
        "IfcAxis2Placement3D",
        Location=model.create_entity(
            "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
        ),
        Axis=model.create_entity(
            "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
        ),
        RefDirection=model.create_entity(
            "IfcDirection", DirectionRatios=(1.0, 0.0, 0.0)
        ),
    )
    style.RepresentationMaps = [
        model.create_entity(
            "IfcRepresentationMap",
            MappingOrigin=origin,
            MappedRepresentation=representation,
        )
    ]
    return style


def _generated_door_type_template(
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
    resolved_operation: Any,
) -> dict[str, Any]:
    del request_hash, model_fingerprint
    operation_type = str(
        resolved_operation.parameters["door"]["operation_type"]
    )
    if operation_type not in {
        "SINGLE_SWING_LEFT",
        "SINGLE_SWING_RIGHT",
        "NOTDEFINED",
    }:
        raise ValueError("GENERATED_DOOR_OPERATION_UNSUPPORTED")
    return {
        "template_id": "text2ifc-door-single-swing-template",
        "template_version": "0.1",
        "ifc_class": "IfcDoorStyle",
        "name": f"Text2IFC generated door type {operation_id}",
        "construction_type": "NOTDEFINED",
        "operation_type": operation_type,
        "parameter_takes_precedence": False,
        "sizeable": False,
    }


def _semantic_policy_facts(
    *,
    operation: Mapping[str, Any],
) -> tuple[SemanticFact, ...]:
    operation_id = str(operation["operation_id"])
    door = operation["parameters"]["door"]
    values = (
        (
            "attribute:OverallWidth",
            float(door["overall_width_mm"]),
            "IfcPositiveLengthMeasure",
        ),
        (
            "attribute:OverallHeight",
            float(door["overall_height_mm"]),
            "IfcPositiveLengthMeasure",
        ),
    )
    return tuple(
        SemanticFact(
            fact_key=fact_key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source=f"resolved-operation:{operation_id}",
            source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
            source_ref=f"resolved:/operations/{operation_id}/parameters/door",
            provenance=(
                f"operation:{operation_id}",
                "registered-door-parameter-policy:0.1",
            ),
            occurrence_scope="door_occurrence",
            canonical_source_kind="deterministic_derived",
        )
        for fact_key, value, value_type in values
    )


def _postconditions(
    *,
    operation: Mapping[str, Any],
    model: Any,
    application: Mapping[str, Any],
) -> dict[str, Any]:
    created = {item["role"]: item for item in application.get("created", ())}
    try:
        door = require_guid(
            model, str(created["door"]["global_id"]), "IfcDoor"
        )
        opening_id = str(application["resolved"]["opening_global_id"])
        opening = require_guid(model, opening_id, "IfcOpeningElement")
        wall = opening.VoidsElements[0].RelatingBuildingElement
    except (KeyError, IndexError, OperationRegistryError) as error:
        return {
            "valid": False,
            "checks": [],
            "issues": [
                {
                    "code": "CREATED_DOOR_CHAIN_NOT_FOUND",
                    "path": "/application",
                    "message": str(error),
                }
            ],
            "evidence": {},
        }
    expected = operation["parameters"]["door"]
    predicates = {
        "DOOR_FILLS_OPENING": (
            len(door.FillsVoids) == 1
            and door.FillsVoids[0].RelatingOpeningElement == opening
        ),
        "OPENING_VOIDS_WALL": (
            len(opening.VoidsElements) == 1
            and opening.VoidsElements[0].RelatingBuildingElement == wall
        ),
        "DOOR_DIMENSIONS_MATCH": (
            math.isclose(
                float(door.OverallWidth),
                float(expected["overall_width_mm"]),
                abs_tol=1e-4,
            )
            and math.isclose(
                float(door.OverallHeight),
                float(expected["overall_height_mm"]),
                abs_tol=1e-4,
            )
        ),
        "DOOR_STOREY_CONTAINMENT": bool(door.ContainedInStructure),
        "DOOR_TYPE_BOUND": any(
            relation.is_a("IfcRelDefinesByType")
            for relation in door.IsDefinedBy
        ),
    }
    issues = [
        {
            "code": code,
            "path": "/postconditions",
            "message": code.replace("_", " ").title(),
        }
        for code, passed in predicates.items()
        if not passed
    ]
    return {
        "valid": not issues,
        "checks": [
            {
                "code": code,
                "status": "passed" if passed else "failed",
                "evidence": {},
            }
            for code, passed in predicates.items()
        ],
        "issues": issues,
        "evidence": {
            "door_global_id": str(door.GlobalId),
            "opening_global_id": str(opening.GlobalId),
            "host_wall_global_id": str(wall.GlobalId),
        },
    }


def _comparison_adapter(
    *,
    operation: Mapping[str, Any],
    after_model: Any,
    application: Mapping[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    del kwargs
    result = _postconditions(
        operation=operation,
        model=after_model,
        application=application,
    )
    return {
        **result,
        "authorization": _l1_authorization(
            creates_opening=operation["operation_type"] == ADD_OPERATION_TYPE
        ),
        "l1_checks": {
            "l1.door.topology": {
                "status": "passed" if result["valid"] else "failed",
                "reason": "Door must fill one hosted Opening and be contained and typed.",
                "expected": True,
                "actual": result["valid"],
            }
        },
    }


def _l1_authorization(*, creates_opening: bool) -> dict[str, Any]:
    created = {
        "door": "IfcDoor",
        "fills_relationship": "IfcRelFillsElement",
        "generated_door_type": "IfcDoorStyle",
        "door_type_relationship": "IfcRelDefinesByType",
    }
    if creates_opening:
        created.update(
            {
                "opening": "IfcOpeningElement",
                "voids_relationship": "IfcRelVoidsElement",
            }
        )
    return {
        "policy_id": "door.hosted-opening.l1",
        "policy_version": "0.1",
        "created": created,
        "modified": {
            "door_type_relationship": "IfcRelDefinesByType",
            "spatial_containment": "IfcRelContainedInSpatialStructure",
        },
        "removed": {},
        "required_roles": {
            "created": (
                ("opening", "voids_relationship")
                if creates_opening
                else ()
            )
            + ("door", "fills_relationship"),
            "modified": ("spatial_containment",),
        },
        "relations": {
            "fills_relationship": {
                "ifc_class": "IfcRelFillsElement",
                "endpoints": {
                    "RelatingOpeningElement": "opening",
                    "RelatedBuildingElement": "door",
                },
            },
            "voids_relationship": {
                "ifc_class": "IfcRelVoidsElement",
                "endpoints": {
                    "RelatingBuildingElement": "target",
                    "RelatedOpeningElement": "opening",
                },
            },
            "door_type_relationship": {
                "ifc_class": "IfcRelDefinesByType",
                "added_endpoint_roles": ("door",),
            },
            "spatial_containment": {
                "ifc_class": "IfcRelContainedInSpatialStructure",
                "added_endpoint_roles": ("door",),
            },
        },
    }


def _issue(code: str, path: str, detail: str) -> dict[str, Any]:
    return {
        "checks": [
            {"code": code, "status": "failed", "evidence": {"detail": detail}}
        ],
        "issues": [{"code": code, "path": path, "message": detail}],
        "evidence": {},
    }


__all__ = [
    "ADD_DOOR_EVALUATION_POLICY",
    "ADD_OPERATION_TYPE",
    "FILL_DOOR_EVALUATION_POLICY",
    "FILL_OPERATION_TYPE",
    "add_door_operation_definition",
    "fill_door_operation_definition",
]
