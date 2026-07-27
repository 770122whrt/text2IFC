"""Deterministic IFC2X3 Opening-only authoring on a straight Wall."""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from text2ifc_ifc_repair.context import build_window_wall_candidate
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

from .hosted_opening import (
    check_hosted_opening_preconditions,
    create_hosted_opening,
    hosted_opening_conflict_checker,
    require_guid,
)


OPERATION_TYPE = "add_opening_to_wall"
TARGET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["wall_global_id"],
    "properties": {"wall_global_id": {"type": "string", "minLength": 1}},
}
PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["position", "opening"],
    "properties": {
        "position": {
            "type": "object",
            "additionalProperties": False,
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
    },
}
_SOURCES = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
    EvidenceSourceKind.PRIVATE_ORIGINAL,
)
OPENING_EVALUATION_POLICY = OperationEvaluationPolicy(
    policy_id="opening.add-to-wall.l2",
    version="0.1",
    operation_type=OPERATION_TYPE,
    semantic_role="opening",
    semantic_facts=(
        SemanticFactSpec(
            "opening.host",
            "0.1",
            "relationship:host",
            SemanticApplicability.REQUIRED,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
        SemanticFactSpec(
            "opening.quantity",
            "0.1",
            "quantity:*",
            SemanticApplicability.CONDITIONAL,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
        SemanticFactSpec(
            "opening.pset",
            "0.1",
            "pset:*",
            SemanticApplicability.CONDITIONAL,
            _SOURCES,
            ComparisonRule.TYPED_EQUIVALENCE,
            1e-6,
        ),
    ),
    target_authority_mode="host_for_created_entity",
)
OPENING_L1_AUTHORIZATION = {
    "policy_id": "opening.add-to-wall.l1",
    "policy_version": "0.1",
    "created": {
        "opening": "IfcOpeningElement",
        "voids_relationship": "IfcRelVoidsElement",
    },
    "modified": {},
    "removed": {},
    "required_roles": {
        "created": ("opening", "voids_relationship"),
        "modified": (),
    },
    "relations": {
        "voids_relationship": {
            "ifc_class": "IfcRelVoidsElement",
            "endpoints": {
                "RelatingBuildingElement": "target",
                "RelatedOpeningElement": "opening",
            },
        }
    },
}


def opening_operation_definition() -> OperationDefinition:
    return OperationDefinition(
        operation_type=OPERATION_TYPE,
        target_ifc_classes=("IfcWall",),
        parameter_schema=PARAMETER_SCHEMA,
        target_schema=TARGET_SCHEMA,
        context_adapter=_context_adapter,
        precondition_checker=_precondition_checker,
        applicator=_applicator,
        postcondition_checker=_postcondition_checker,
        comparison_adapter=_comparison_adapter,
        capability_constraints={
            "ifc_schemas": ["IFC2X3"],
            "wall_geometry": ["straight_wall"],
            "filling_element": False,
        },
        precondition_names=(
            "target_exists",
            "opening_within_wall",
            "opening_interval_available",
        ),
        postcondition_names=(
            "opening_voids_wall",
            "requested_geometry_matches",
            "opening_unfilled",
        ),
        evaluation_policy=OPENING_EVALUATION_POLICY,
        editable_occurrence_ifc_class="IfcOpeningElement",
        prompt_profile_id="opening.add-to-wall",
        semantic_scope_roles={"opening": "opening_occurrence"},
        conflict_domain="hosted_opening",
        operation_conflict_checker=hosted_opening_conflict_checker,
    )


def _context_adapter(
    *,
    operation: Mapping[str, Any],
    target: Any,
    storey: str,
) -> dict[str, Any]:
    del operation
    return build_window_wall_candidate(target, storey=storey)


def _precondition_checker(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    return check_hosted_opening_preconditions(operation=operation, model=model)


def _applicator(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    wall = require_guid(
        model, str(operation["target"]["wall_global_id"]), "IfcWall"
    )
    created = create_hosted_opening(
        model=model, operation=operation, wall=wall
    )
    opening = created["opening"]
    void = created["voids_relationship"]
    return {
        "created": [
            {
                "role": "opening",
                "ifc_class": opening.is_a(),
                "global_id": str(opening.GlobalId),
            },
            {
                "role": "voids_relationship",
                "ifc_class": void.is_a(),
                "global_id": str(void.GlobalId),
            },
        ],
        "modified": [
            {"role": "host_wall", "global_id": str(wall.GlobalId)}
        ],
        "removed": [],
        "resolved": {
            "center_offset_mm": created["footprint"].center_offset_mm,
            "opening_depth_mm": created["opening_depth_mm"],
        },
    }


def _postcondition_checker(
    *,
    operation: Mapping[str, Any],
    model: Any,
    application: Mapping[str, Any],
) -> dict[str, Any]:
    created = {item["role"]: item for item in application.get("created", ())}
    try:
        wall = require_guid(
            model, str(operation["target"]["wall_global_id"]), "IfcWall"
        )
        opening = require_guid(
            model,
            str(created["opening"]["global_id"]),
            "IfcOpeningElement",
        )
    except (KeyError, OperationRegistryError) as error:
        return {
            "valid": False,
            "checks": [],
            "issues": [
                {
                    "code": "CREATED_OPENING_NOT_FOUND",
                    "path": "/application/created",
                    "message": str(error),
                }
            ],
            "evidence": {},
        }
    dimensions = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, wall)
    requested = operation["parameters"]["opening"]
    expected = {
        "width": float(requested["width_mm"]),
        "height": float(requested["height_mm"]),
        "center": float(
            operation["parameters"]["position"]["center_offset_mm"]
        ),
        "sill": float(requested["sill_height_mm"]),
    }
    actual = {
        "width": float(dimensions["width"]),
        "height": float(dimensions["height"]),
        "center": float(position["center_offset"]),
        "sill": float(position["sill_height"]),
    }
    predicates = {
        "OPENING_VOIDS_TARGET_WALL": (
            len(opening.VoidsElements) == 1
            and opening.VoidsElements[0].RelatingBuildingElement == wall
        ),
        "OPENING_HAS_NO_FILLING": len(opening.HasFillings) == 0,
        "OPENING_GEOMETRY_MATCHES_PARAMETERS": all(
            math.isclose(actual[key], expected[key], abs_tol=1e-4)
            for key in expected
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
                "evidence": actual,
            }
            for code, passed in predicates.items()
        ],
        "issues": issues,
        "evidence": {
            "opening_global_id": str(opening.GlobalId),
            "actual": actual,
            "expected": expected,
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
    result = _postcondition_checker(
        operation=operation,
        model=after_model,
        application=application,
    )
    return {
        **result,
        "authorization": copy.deepcopy(OPENING_L1_AUTHORIZATION),
        "l1_checks": {
            "l1.opening.topology": {
                "status": "passed" if result["valid"] else "failed",
                "reason": "Opening must void the target Wall without a filling.",
                "expected": True,
                "actual": result["valid"],
            }
        },
    }


__all__ = [
    "OPENING_EVALUATION_POLICY",
    "OPENING_L1_AUTHORIZATION",
    "OPERATION_TYPE",
    "opening_operation_definition",
]
