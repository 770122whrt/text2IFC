"""Registered deterministic IFC2X3 straight rectangular Column operation."""

from __future__ import annotations

import math
from typing import Any, Mapping

from text2ifc_ifc_repair.evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SemanticApplicability,
    SemanticFactSpec,
)
from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistryError
from text2ifc_ifc_repair.semantic_facts import SemanticFact
from text2ifc_ifc_repair.structural_resolution import (
    resolve_structural_parameters,
    structural_intent_capability,
    structural_operation_conflict_checker,
)

from .hosted_opening import (
    add_to_containment,
    body_context,
    deterministic_global_id,
    require_guid,
)
from .structural_member import (
    bind_structural_type,
    create_generated_column_type,
    create_straight_rectangular_member,
    generated_column_type_template,
    resolve_structural_member_frame,
    structural_l1_comparison_report,
)


OPERATION_TYPE = "add_column"
_POINT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["x_mm", "y_mm", "z_mm"],
    "properties": {
        key: {"type": "number"} for key in ("x_mm", "y_mm", "z_mm")
    },
}
_ORIENTATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["x", "y"],
    "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
}
_SECTION_PROPERTIES = {
    "shape": {"const": "rectangle"},
    "width_mm": {"type": "number", "exclusiveMinimum": 0},
    "depth_mm": {"type": "number", "exclusiveMinimum": 0},
    "orientation": _ORIENTATION_SCHEMA,
}
_PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["axis", "section"],
    "properties": {
        "axis": {
            "type": "object",
            "additionalProperties": False,
            "required": ["base", "top"],
            "properties": {"base": _POINT_SCHEMA, "top": _POINT_SCHEMA},
        },
        "section": {
            "type": "object",
            "additionalProperties": False,
            "required": ["shape", "width_mm", "depth_mm"],
            "properties": _SECTION_PROPERTIES,
        },
    },
}
_REFERENCE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "allowed_ifc_classes"],
    "properties": {
        "schema_version": {"const": "text2ifc/ifc-target-query/0.1"},
        "allowed_ifc_classes": {"const": ["IfcColumn"]},
        "global_id": {"type": "string", "minLength": 1},
        "names": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "storey_global_id": {"type": "string", "minLength": 1},
        "storey_name": {"type": "string", "minLength": 1},
        "grid": {"type": "string", "minLength": 1},
        "max_candidates": {"type": "integer", "minimum": 1, "maximum": 10},
        "winner_margin": {"type": "integer", "minimum": 1},
    },
}
_INTENT_PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["axis", "section"],
    "properties": {
        "axis": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "base": _POINT_SCHEMA,
                "top": _POINT_SCHEMA,
                "reference": _REFERENCE_SCHEMA,
                "grid": {"type": "string"},
                "curve": {"type": "object"},
            },
        },
        "section": {
            "type": "object",
            "additionalProperties": False,
            "required": ["shape", "width_mm", "depth_mm"],
            "properties": {
                **_SECTION_PROPERTIES,
                "shape": {
                    "enum": [
                        "rectangle",
                        "round_section",
                        "i_section",
                        "h_section",
                        "arbitrary_section",
                        "variable_section",
                    ]
                },
            },
        },
        "height_mm": {"type": "number", "exclusiveMinimum": 0},
        "split_at_storeys": {"type": "boolean"},
    },
}
_INTENT_TARGET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "allowed_ifc_classes"],
    "properties": {
        "schema_version": {"const": "text2ifc/ifc-target-query/0.1"},
        "allowed_ifc_classes": {"const": ["IfcBuildingStorey"]},
        "global_id": {"type": "string", "minLength": 1},
        "names": {
            "type": "array",
            "minItems": 1,
            "maxItems": 16,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1, "maxLength": 256},
        },
    },
    "anyOf": [{"required": ["global_id"]}, {"required": ["names"]}],
}
_TARGET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["storey_global_id"],
    "properties": {"storey_global_id": {"type": "string", "minLength": 1}},
}
_SOURCES = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.SURVIVING_TYPE,
    EvidenceSourceKind.APPROVED_PROTOTYPE,
    EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
    EvidenceSourceKind.PRIVATE_ORIGINAL,
)


COLUMN_EVALUATION_POLICY = OperationEvaluationPolicy(
    policy_id="column.add.l2",
    version="0.1",
    operation_type=OPERATION_TYPE,
    semantic_role="column",
    semantic_facts=(
        SemanticFactSpec(
            "column.type",
            "0.1",
            "relationship:type",
            SemanticApplicability.REQUIRED,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
        SemanticFactSpec(
            "column.storey",
            "0.1",
            "relationship:storey",
            SemanticApplicability.REQUIRED,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
        SemanticFactSpec(
            "column.pset",
            "0.1",
            "pset:*",
            SemanticApplicability.CONDITIONAL,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
        SemanticFactSpec(
            "column.material",
            "0.1",
            "material:*",
            SemanticApplicability.CONDITIONAL,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
    ),
    target_authority_mode="host_for_created_entity",
)


def column_operation_definition() -> OperationDefinition:
    return OperationDefinition(
        operation_type=OPERATION_TYPE,
        target_ifc_classes=("IfcBuildingStorey",),
        parameter_schema=_PARAMETER_SCHEMA,
        target_schema=_TARGET_SCHEMA,
        intent_target_schema=_INTENT_TARGET_SCHEMA,
        intent_parameter_schema=_INTENT_PARAMETER_SCHEMA,
        intent_capability_checker=_intent_capability_checker,
        context_adapter=_context_adapter,
        precondition_checker=_preconditions,
        applicator=_applicator,
        postcondition_checker=_postconditions,
        comparison_adapter=_comparison_adapter,
        capability_constraints={
            "ifc_schemas": ["IFC2X3"],
            "axis": "straight_vertical_storey_local",
            "section": "rectangle_explicit_non_square_orientation",
            "automatic_storey_split": False,
            "grid_placement": False,
            "structural_analysis": False,
            "handler_owned_semantic_facts": [
                "relationship:host",
                "relationship:storey",
            ],
        },
        prototype_ifc_classes=("IfcColumnType",),
        prototype_dimension_paths={
            "width_mm": ("section", "width_mm"),
            "depth_mm": ("section", "depth_mm"),
        },
        precondition_names=(
            "target_exists",
            "structural_axis_available",
            "structural_type_authorized",
        ),
        postcondition_names=(
            "column_geometry_matches",
            "column_contained_in_base_storey",
            "column_type_bound",
        ),
        evaluation_policy=COLUMN_EVALUATION_POLICY,
        semantic_policy_fact_builder=_semantic_policy_facts,
        editable_occurrence_ifc_class="IfcColumn",
        inherited_type_evidence_role="IfcColumnType",
        generated_type_template=generated_column_type_template,
        generated_type_factory=create_generated_column_type,
        prompt_profile_id="column.add.v0.3",
        stage2_prompt_profile_id="column.add.stage2.v0.1",
        semantic_scope_roles={"column": "column_occurrence"},
        conflict_domain="structural_member",
        intent_policy_checker=_intent_policy_checker,
        parameter_resolver=resolve_column_parameters,
        operation_conflict_checker=structural_operation_conflict_checker,
    )


def resolve_column_parameters(**kwargs: Any) -> dict[str, Any]:
    return resolve_structural_parameters(family="column", **kwargs)


def _intent_policy_checker(**kwargs: Any) -> dict[str, str]:
    del kwargs
    return {"status": "resolved"}


def _intent_capability_checker(
    *, operation: Mapping[str, Any]
) -> dict[str, str]:
    return structural_intent_capability(operation=operation, family="column")


def _context_adapter(
    *, operation: Mapping[str, Any], target: Any, storey: str
) -> dict[str, Any]:
    del operation
    return {
        "record_id": f"ifc:{target.GlobalId}",
        "ifc_global_id": str(target.GlobalId),
        "ifc_class": target.is_a(),
        "name": None if target.Name is None else str(target.Name),
        "storey_name": storey,
        "coordinate_reference": "storey_local_mm",
        "containment_policy": "axis_base_storey_only",
    }


def _preconditions(
    *, operation: Mapping[str, Any], model: Any
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    storey_id = str(operation.get("target", {}).get("storey_global_id", ""))
    try:
        storey = require_guid(model, storey_id, "IfcBuildingStorey")
    except OperationRegistryError as error:
        return _issue(error.code, "/target/storey_global_id", error.detail)
    try:
        frame = _frame(operation)
    except ValueError as error:
        return _issue(str(error), "/parameters/axis", str(error))
    assignments = [
        item
        for item in operation.get("semantic_assignments", ())
        if item.get("fact_key") == "relationship:type"
    ]
    if len(assignments) != 1:
        issues.append(
            {
                "code": "STRUCTURAL_TYPE_AUTHORITY_REQUIRED",
                "path": "/semantic_assignments",
                "message": "Exactly one Column Type authority is required.",
            }
        )
    containment = list(storey.ContainsElements)
    if len(containment) > 1:
        issues.append(
            {
                "code": "STRUCTURAL_STOREY_CONTAINMENT_AMBIGUOUS",
                "path": "/target/storey_global_id",
                "message": storey_id,
            }
        )
    for relation in containment:
        for existing_column in relation.RelatedElements:
            if not existing_column.is_a("IfcColumn"):
                continue
            try:
                measured = measure_straight_rectangular_member(
                    existing_column, relative_to=storey
                )
            except (ValueError, RuntimeError):
                continue
            existing_operation = {
                "operation_type": OPERATION_TYPE,
                "target": dict(operation["target"]),
                "parameters": {
                    "axis": {
                        "base": _point_document(measured["axis_start_mm"]),
                        "top": _point_document(measured["axis_end_mm"]),
                    }
                },
            }
            if structural_operation_conflict_checker(
                existing_operation, operation
            ):
                issues.append(
                    {
                        "code": "STRUCTURAL_EXISTING_SAME_AXIS_OVERLAP",
                        "path": "/parameters/axis/base",
                        "message": str(existing_column.GlobalId),
                    }
                )
                break
        if any(
            issue["code"] == "STRUCTURAL_EXISTING_SAME_AXIS_OVERLAP"
            for issue in issues
        ):
            break
    occurrence_id = deterministic_global_id(operation, "column")
    try:
        existing = model.by_guid(occurrence_id)
    except RuntimeError:
        existing = None
    if existing is not None:
        issues.append(
            {
                "code": "DETERMINISTIC_GLOBAL_ID_COLLISION",
                "path": "/operation_id",
                "message": occurrence_id,
            }
        )
    return {
        "checks": [
            {
                "code": "STRUCTURAL_STOREY_AVAILABLE",
                "status": "passed",
                "evidence": {"storey_global_id": storey_id},
            },
            {
                "code": "STRUCTURAL_AXIS_AVAILABLE",
                "status": "passed",
                "evidence": {"axis_extent_mm": frame["axis_extent_mm"]},
            },
            {
                "code": "STRUCTURAL_TYPE_AUTHORIZED",
                "status": "passed" if len(assignments) == 1 else "failed",
                "evidence": {"assignment_count": len(assignments)},
            },
        ],
        "issues": issues,
        "evidence": {
            "storey_global_id": storey_id,
            "axis_extent_mm": frame["axis_extent_mm"],
        },
    }


def _applicator(
    *, operation: Mapping[str, Any], model: Any
) -> dict[str, Any]:
    storey = require_guid(
        model,
        str(operation["target"]["storey_global_id"]),
        "IfcBuildingStorey",
    )
    frame = _frame(operation)
    occurrence_id = deterministic_global_id(operation, "column")
    created_member = create_straight_rectangular_member(
        model=model,
        occurrence_class="IfcColumn",
        occurrence_global_id=occurrence_id,
        operation_id=str(operation["operation_id"]),
        axis_start_mm=frame["axis_start_mm"],
        axis_end_mm=frame["axis_end_mm"],
        section=frame["section"],
        storey=storey,
        owner_history=storey.OwnerHistory,
        representation_context=body_context(model),
    )
    column = created_member["occurrence"]
    assignment = next(
        item
        for item in operation.get("semantic_assignments", ())
        if item.get("fact_key") == "relationship:type"
    )
    binding = bind_structural_type(
        model=model,
        occurrence=column,
        assignment=assignment,
        owner_history=storey.OwnerHistory,
        operation_id=str(operation["operation_id"]),
        expected_ifc_class="IfcColumnType",
        generated_type_factory=create_generated_column_type,
        factory_context={"section": frame["section"]},
    )
    containment = list(storey.ContainsElements)
    created: list[dict[str, str]] = [
        {
            "role": "column",
            "ifc_class": "IfcColumn",
            "global_id": occurrence_id,
        },
        *binding["created"],
    ]
    modified: list[dict[str, str]] = [*binding["modified"]]
    if containment:
        add_to_containment(containment[0], column)
        modified.append(
            {
                "role": "spatial_containment",
                "ifc_class": containment[0].is_a(),
                "global_id": str(containment[0].GlobalId),
            }
        )
    else:
        relation = model.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=deterministic_global_id(operation, "spatial_containment"),
            OwnerHistory=storey.OwnerHistory,
            RelatedElements=[column],
            RelatingStructure=storey,
        )
        created.append(
            {
                "role": "spatial_containment",
                "ifc_class": relation.is_a(),
                "global_id": str(relation.GlobalId),
            }
        )
    return {
        "created": created,
        "modified": modified,
        "removed": [],
        "resolved": {
            "storey_global_id": str(storey.GlobalId),
            "geometry": created_member["measurement"],
            "type_global_id": str(binding["type"].GlobalId),
            "containment_policy": "axis_base_storey_only",
        },
    }


def _postconditions(
    *,
    operation: Mapping[str, Any],
    model: Any,
    application: Mapping[str, Any],
) -> dict[str, Any]:
    created = {item["role"]: item for item in application.get("created", ())}
    try:
        column = require_guid(
            model, str(created["column"]["global_id"]), "IfcColumn"
        )
        storey = require_guid(
            model,
            str(operation["target"]["storey_global_id"]),
            "IfcBuildingStorey",
        )
        measured = measure_straight_rectangular_member(
            column, relative_to=storey
        )
    except (KeyError, OperationRegistryError, ValueError) as error:
        return {
            "valid": False,
            "checks": [],
            "issues": [
                {
                    "code": "CREATED_COLUMN_NOT_FOUND",
                    "path": "/application",
                    "message": str(error),
                }
            ],
            "evidence": {},
        }
    frame = _frame(operation)
    geometry_matches = (
        _point_close(measured["axis_start_mm"], frame["axis_start_mm"])
        and _point_close(measured["axis_end_mm"], frame["axis_end_mm"])
        and measured["section"]
        == {
            key: value
            for key, value in frame["section"].items()
            if key != "orientation"
        }
        and (
            measured["orientation"] is None
            if frame["orientation"] is None
            else _point_close(measured["orientation"], frame["orientation"])
        )
    )
    contained = [
        relation.RelatingStructure
        for relation in column.ContainedInStructure
        if relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    typed = [
        relation.RelatingType
        for relation in column.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    predicates = {
        "COLUMN_GEOMETRY_MATCHES": geometry_matches,
        "COLUMN_CONTAINED_IN_BASE_STOREY": contained == [storey],
        "COLUMN_TYPE_BOUND": len(typed) == 1
        and typed[0].is_a("IfcColumnType"),
        "COLUMN_ANALYSIS_RELATIONSHIPS_ABSENT": not getattr(
            column, "HasStructuralMember", ()
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
                "evidence": measured if code == "COLUMN_GEOMETRY_MATCHES" else {},
            }
            for code, passed in predicates.items()
        ],
        "issues": issues,
        "evidence": {"measurement": measured},
    }


def _comparison_adapter(
    *,
    operation: Mapping[str, Any],
    after_model: Any,
    application: Mapping[str, Any],
    role_mapping: Mapping[str, str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    del kwargs
    return structural_l1_comparison_report(
        family="column",
        operation=operation,
        after_model=after_model,
        application=application,
        role_mapping=role_mapping,
    )


def _semantic_policy_facts(
    *, operation: Mapping[str, Any]
) -> tuple[SemanticFact, ...]:
    operation_id = str(operation["operation_id"])
    storey_id = str(operation["target"]["storey_global_id"])
    return (
        SemanticFact(
            fact_key="relationship:storey",
            value=storey_id,
            value_type="IfcBuildingStorey",
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source=f"generated-operation:{operation_id}",
            source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
            source_ref=f"resolved:/operations/{operation_id}/target",
            provenance=(
                f"operation:{operation_id}",
                "registered-column-base-storey-policy:0.1",
            ),
            occurrence_scope="column_occurrence",
            canonical_source_kind="deterministic_derived",
        ),
    )


def _frame(operation: Mapping[str, Any]) -> dict[str, Any]:
    parameters = operation["parameters"]
    axis = parameters["axis"]
    return resolve_structural_member_frame(
        occurrence_class="IfcColumn",
        axis_start_mm=_point(axis["base"]),
        axis_end_mm=_point(axis["top"]),
        section=parameters["section"],
    )


def _point(value: Mapping[str, Any]) -> tuple[float, float, float]:
    return tuple(float(value[key]) for key in ("x_mm", "y_mm", "z_mm"))


def _point_document(value: Any) -> dict[str, float]:
    return {
        key: float(item)
        for key, item in zip(("x_mm", "y_mm", "z_mm"), value, strict=True)
    }


def _point_close(first: Any, second: Any) -> bool:
    return all(
        math.isclose(float(left), float(right), abs_tol=1e-4)
        for left, right in zip(first, second, strict=True)
    )


def _issue(code: str, path: str, message: str) -> dict[str, Any]:
    return {
        "checks": [
            {"code": code, "status": "failed", "evidence": {"detail": message}}
        ],
        "issues": [{"code": code, "path": path, "message": message}],
        "evidence": {},
    }


__all__ = [
    "COLUMN_EVALUATION_POLICY",
    "column_operation_definition",
    "resolve_column_parameters",
]
