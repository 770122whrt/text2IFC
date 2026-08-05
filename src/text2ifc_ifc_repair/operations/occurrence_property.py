"""Occurrence-only scalar IFC property authoring for existing elements."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from text2ifc_ifc_repair.evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SemanticApplicability,
    SemanticFactSpec,
)
from text2ifc_ifc_repair.registry import OperationDefinition
from text2ifc_ifc_repair.semantic_facts import extract_property_facts
from text2ifc_knowledge.registry import load_ifc2x3_registry


OPERATION_TYPE = "set_occurrence_properties"
TARGET_IFC_CLASSES = (
    "IfcBeam",
    "IfcColumn",
    "IfcDoor",
    "IfcWall",
    "IfcWallStandardCase",
    "IfcWindow",
)
TARGET_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["element_global_id"],
    "properties": {
        "element_global_id": {"type": "string", "minLength": 1},
    },
}
PARAMETER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "maxProperties": 0,
}

PROPERTY_EVALUATION_POLICY = OperationEvaluationPolicy(
    policy_id="occurrence.property.l2",
    version="0.1",
    operation_type=OPERATION_TYPE,
    semantic_role="target",
    semantic_facts=(
        SemanticFactSpec(
            check_id="occurrence.requested-property",
            version="0.1",
            fact_pattern="pset:*",
            applicability=SemanticApplicability.CONDITIONAL,
            allowed_sources=(EvidenceSourceKind.EXPLICIT_REQUEST,),
            comparison=ComparisonRule.TYPED_EQUIVALENCE,
            absolute_tolerance=1e-6,
        ),
    ),
    target_authority_mode="edited_entity",
)


def occurrence_property_operation_definition() -> OperationDefinition:
    return OperationDefinition(
        operation_type=OPERATION_TYPE,
        target_ifc_classes=TARGET_IFC_CLASSES,
        parameter_schema=PARAMETER_SCHEMA,
        target_schema=TARGET_SCHEMA,
        context_adapter=_context_adapter,
        precondition_checker=_precondition_checker,
        applicator=_applicator,
        postcondition_checker=_postcondition_checker,
        comparison_adapter=_comparison_adapter,
        capability_constraints={
            "ifc_schemas": ["IFC2X3"],
            "property_templates": ["IfcPropertySingleValue"],
            "mutation_scope": "occurrence_only",
            "semantic_authoring_scope": "explicit_request_only",
            "geometry_mutation": False,
            "shared_type_mutation": False,
        },
        precondition_names=(
            "target_exists",
            "target_class_supported",
            "property_assignments_bound",
        ),
        postcondition_names=(
            "target_preserved",
            "requested_properties_match",
            "shared_type_unchanged",
        ),
        evaluation_policy=PROPERTY_EVALUATION_POLICY,
        editable_occurrence_ifc_classes=TARGET_IFC_CLASSES,
        prompt_profile_id="occurrence.set-properties",
        semantic_scope_roles={"target": "occurrence_direct"},
        conflict_domain="occurrence_property",
    )


def _context_adapter(
    *,
    operation: Mapping[str, Any],
    target: Any,
    storey: str,
) -> dict[str, Any]:
    del operation
    return {
        "record_id": f"occurrence:{target.GlobalId}",
        "ifc_global_id": str(target.GlobalId),
        "ifc_class": target.is_a(),
        "name": None if target.Name is None else str(target.Name),
        "storey_name": storey,
    }


def _target(model: Any, operation: Mapping[str, Any]) -> Any | None:
    global_id = str(operation.get("target", {}).get("element_global_id", ""))
    if not global_id:
        return None
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _precondition_checker(
    *,
    operation: Mapping[str, Any],
    model: Any,
) -> dict[str, Any]:
    target = _target(model, operation)
    if target is None:
        return _check_failure(
            "PROPERTY_TARGET_NOT_FOUND",
            "/target/element_global_id",
        )
    if target.is_a() not in TARGET_IFC_CLASSES:
        return _check_failure(
            "PROPERTY_TARGET_CLASS_UNSUPPORTED",
            "/target/element_global_id",
            actual=target.is_a(),
        )
    assignments = tuple(operation.get("semantic_assignments", ()))
    if not assignments:
        return _check_failure(
            "PROPERTY_ASSIGNMENTS_REQUIRED",
            "/semantic_assignments",
        )
    if any(
        item.get("ownership") != "occurrence_direct"
        or item.get("authoring_action") != "set_occurrence_pset"
        or not str(item.get("fact_key", "")).startswith("pset:")
        for item in assignments
    ):
        return _check_failure(
            "PROPERTY_ASSIGNMENT_UNSUPPORTED",
            "/semantic_assignments",
        )
    for index, assignment in enumerate(assignments):
        issue = _assignment_authority_issue(
            target_ifc_class=target.is_a(),
            assignment=assignment,
        )
        if issue is not None:
            code, actual = issue
            return _check_failure(
                code,
                f"/semantic_assignments/{index}",
                actual=actual,
            )
    return {
        "checks": [
            {
                "code": "PROPERTY_OCCURRENCE_READY",
                "status": "passed",
                "evidence": {
                    "global_id": str(target.GlobalId),
                    "ifc_class": target.is_a(),
                    "assignment_count": len(assignments),
                },
            }
        ],
        "issues": [],
        "evidence": {"target_global_id": str(target.GlobalId)},
    }


def _check_failure(
    code: str,
    path: str,
    *,
    actual: str | None = None,
) -> dict[str, Any]:
    return {
        "checks": [
            {
                "code": code,
                "status": "failed",
                "evidence": {"actual": actual},
            }
        ],
        "issues": [{"code": code, "path": path, "message": code}],
        "evidence": {},
    }


def _assignment_authority_issue(
    *,
    target_ifc_class: str,
    assignment: Mapping[str, Any],
) -> tuple[str, str] | None:
    fact_key = str(assignment.get("fact_key") or "")
    source_fact_key = str(assignment.get("source_fact_key") or "")
    if fact_key != source_fact_key or not fact_key.startswith("pset:"):
        return "PROPERTY_ASSIGNMENT_NONCANONICAL", source_fact_key
    path = fact_key.removeprefix("pset:")
    if path.count(".") != 1:
        return "PROPERTY_ASSIGNMENT_NONCANONICAL", path
    set_name, property_name = path.split(".", 1)

    registry = load_ifc2x3_registry()
    property_set = registry.property_set(set_name)
    if property_set is None or property_name not in property_set["properties"]:
        return "PROPERTY_ASSIGNMENT_NONCANONICAL", path
    applicable_classes = tuple(
        str(value) for value in property_set.get("applicable_classes", ())
    )
    declaration = registry.entity(target_ifc_class)
    supertypes = (
        ()
        if declaration is None
        else tuple(str(value) for value in declaration.get("supertypes", ()))
    )
    if target_ifc_class not in applicable_classes and not any(
        value in applicable_classes for value in supertypes
    ):
        return "PROPERTY_PSET_NOT_APPLICABLE", set_name

    expected_type = str(property_set["properties"][property_name]["data_type"])
    actual_type = str(assignment.get("value_type") or "")
    if actual_type != expected_type:
        return "PROPERTY_VALUE_TYPE_MISMATCH", actual_type

    class_scope = {
        "IfcBeam": "beam_occurrence",
        "IfcColumn": "column_occurrence",
        "IfcDoor": "door_occurrence",
        "IfcWindow": "window_occurrence",
    }.get(target_ifc_class)
    allowed_scopes = {"target_occurrence"}
    if class_scope is not None:
        allowed_scopes.add(class_scope)
    scope = str(assignment.get("scope") or "target_occurrence")
    if scope not in allowed_scopes:
        return "PROPERTY_ASSIGNMENT_SCOPE_UNSUPPORTED", scope
    return None


def _applicator(*, operation: Mapping[str, Any], model: Any) -> dict[str, Any]:
    target = _target(model, operation)
    if target is None or target.is_a() not in TARGET_IFC_CLASSES:
        raise ValueError("PROPERTY_TARGET_INVALID")
    return {
        "created": [],
        "modified": [
            {
                "role": "target",
                "ifc_class": target.is_a(),
                "global_id": str(target.GlobalId),
            }
        ],
        "removed": [],
        "resolved": {
            "target_global_id": str(target.GlobalId),
            "target_ifc_class": target.is_a(),
        },
    }


def _postcondition_checker(
    *,
    operation: Mapping[str, Any],
    model: Any,
    application: Mapping[str, Any],
) -> dict[str, Any]:
    del application
    target = _target(model, operation)
    if target is None:
        return {
            "valid": False,
            "checks": [],
            "issues": [
                {
                    "code": "PROPERTY_TARGET_NOT_FOUND_AFTER_APPLY",
                    "path": "/target/element_global_id",
                    "message": "Target occurrence is absent after property authoring.",
                }
            ],
            "evidence": {},
        }
    facts = {
        (fact.set_name, fact.property_name): fact
        for fact in extract_property_facts(target)
    }
    issues: list[dict[str, str]] = []
    checks: list[dict[str, Any]] = []
    for assignment in operation.get("semantic_assignments", ()):
        path = str(assignment["source_fact_key"]).split(":", 1)[1]
        set_name, property_name = path.rsplit(".", 1)
        fact = facts.get((set_name, property_name))
        passed = (
            fact is not None
            and fact.value == assignment["value"]
            and fact.value_type == assignment["value_type"]
            and not fact.inherited
        )
        checks.append(
            {
                "code": f"PROPERTY_MATCH:{set_name}.{property_name}",
                "status": "passed" if passed else "failed",
                "evidence": {
                    "expected": assignment["value"],
                    "actual": None if fact is None else fact.value,
                    "ownership": (
                        None
                        if fact is None
                        else ("type_inherited" if fact.inherited else "occurrence_direct")
                    ),
                },
            }
        )
        if not passed:
            issues.append(
                {
                    "code": "REQUESTED_PROPERTY_POSTCONDITION_FAILED",
                    "path": f"/properties/{set_name}/{property_name}",
                    "message": f"{set_name}.{property_name}",
                }
            )
    return {
        "valid": not issues,
        "checks": checks,
        "issues": issues,
        "evidence": {"target_global_id": str(target.GlobalId)},
    }


def _comparison_adapter(
    *,
    operation: Mapping[str, Any],
    before_model: Any,
    after_model: Any,
    application: Mapping[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    del application, kwargs
    global_id = str(operation["target"]["element_global_id"])
    before = before_model.by_guid(global_id)
    after = after_model.by_guid(global_id)
    target_class = after.is_a()
    identity_ok = before.is_a() == after.is_a() and str(after.GlobalId) == global_id
    placement_ok = _entity_signature(before.ObjectPlacement) == _entity_signature(
        after.ObjectPlacement
    )
    representation_ok = _entity_signature(before.Representation) == _entity_signature(
        after.Representation
    )
    relationships_ok = _relationship_signature(before) == _relationship_signature(after)
    authorization = {
        "policy_id": "occurrence.property.l1",
        "policy_version": "0.1",
        "created": {
            "semantic_pset": "IfcPropertySet",
            "semantic_pset_relationship": "IfcRelDefinesByProperties",
            "semantic_pset_copy_on_write": "IfcPropertySet",
            "semantic_pset_relationship_copy_on_write": "IfcRelDefinesByProperties",
            **{
                f"semantic_pset_{index}": "IfcPropertySet"
                for index in range(2, 65)
            },
            **{
                f"semantic_pset_relationship_{index}": "IfcRelDefinesByProperties"
                for index in range(2, 65)
            },
        },
        "modified": {
            "target": target_class,
            "semantic_pset_updated": "IfcPropertySet",
            "semantic_shared_pset_relationship": "IfcRelDefinesByProperties",
        },
        "removed": {},
        "required_roles": {"modified": ("target",)},
        "relations": {
            "semantic_pset_relationship": {
                "ifc_class": "IfcRelDefinesByProperties"
            },
            "semantic_pset_relationship_copy_on_write": {
                "ifc_class": "IfcRelDefinesByProperties"
            },
            "semantic_shared_pset_relationship": {
                "ifc_class": "IfcRelDefinesByProperties"
            },
            **{
                f"semantic_pset_relationship_{index}": {
                    "ifc_class": "IfcRelDefinesByProperties"
                }
                for index in range(2, 65)
            },
        },
    }
    return {
        "authorization": authorization,
        "l1_checks": {
            "occurrence.identity-preserved": _measurement(
                identity_ok, global_id, str(after.GlobalId)
            ),
            "occurrence.placement-preserved": _measurement(
                placement_ok, "unchanged", "unchanged" if placement_ok else "changed"
            ),
            "occurrence.representation-preserved": _measurement(
                representation_ok,
                "unchanged",
                "unchanged" if representation_ok else "changed",
            ),
            "occurrence.relationships-preserved": _measurement(
                relationships_ok,
                "type/containment/host unchanged",
                "unchanged" if relationships_ok else "changed",
            ),
        },
    }


def _measurement(passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {
        "status": "passed" if passed else "failed",
        "reason": "Occurrence property authoring preserves non-property state.",
        "expected": expected,
        "actual": actual,
    }


def _entity_signature(entity: Any | None) -> str | None:
    if entity is None:
        return None
    return hashlib.sha256(str(entity).encode("utf-8")).hexdigest()


def _relationship_signature(element: Any) -> str:
    values = {
        "types": sorted(
            str(rel.RelatingType.GlobalId)
            for rel in getattr(element, "IsDefinedBy", ())
            if rel.is_a("IfcRelDefinesByType")
        ),
        "containers": sorted(
            str(rel.RelatingStructure.GlobalId)
            for rel in getattr(element, "ContainedInStructure", ())
        ),
        "openings": sorted(
            str(rel.RelatedOpeningElement.GlobalId)
            for rel in getattr(element, "HasOpenings", ())
        ),
        "fills": sorted(
            str(rel.RelatingOpeningElement.GlobalId)
            for rel in getattr(element, "FillsVoids", ())
        ),
    }
    return hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


__all__ = [
    "OPERATION_TYPE",
    "PROPERTY_EVALUATION_POLICY",
    "TARGET_IFC_CLASSES",
    "occurrence_property_operation_definition",
]
