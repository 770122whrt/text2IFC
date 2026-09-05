"""Straight-wall Window plus Opening repair operation."""

from __future__ import annotations

import copy
import json
import math
import uuid
from typing import Any, Mapping

import ifcopenshell.api.geometry
import ifcopenshell.guid
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.shape

from text2ifc_ifc_repair.context import build_window_wall_candidate
from text2ifc_ifc_repair.geometry import (
    UNSUPPORTED_WALL_GEOMETRY,
    opening_dimensions_mm,
    opening_position_in_wall_mm,
    product_geometry_bounds_in_host_mm,
    straight_wall_axis,
    wall_dimensions_mm,
)
from text2ifc_ifc_repair.evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    FactKeyNormalization,
    OperationEvaluationPolicy,
    SemanticApplicability,
    SemanticFactSpec,
)
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistryError
from text2ifc_ifc_repair.type_templates import ensure_bound_type
from text2ifc_ifc_repair.operations.hosted_opening import (
    body_context as hosted_body_context,
    deterministic_global_id as hosted_deterministic_global_id,
    hosted_opening_conflict_checker,
    local_placement as hosted_local_placement,
    millimetres_to_project_units,
    opening_placement as hosted_opening_placement,
    project_units_to_millimetres,
    wall_containment as hosted_wall_containment,
)


OPERATION_TYPE = "add_window_with_opening_to_wall"

TARGET_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["wall_global_id"],
    "properties": {
        "wall_global_id": {"type": "string", "minLength": 1},
    },
}

PARAMETER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["position", "opening", "window"],
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
            "additionalProperties": False,
            "required": ["width_mm", "height_mm", "sill_height_mm"],
            "properties": {
                "width_mm": {"type": "number", "exclusiveMinimum": 0},
                "height_mm": {"type": "number", "exclusiveMinimum": 0},
                "sill_height_mm": {"type": "number", "minimum": 0},
            },
        },
        "window": {
            "type": "object",
            "additionalProperties": False,
            "required": ["fit_opening"],
            "properties": {"fit_opening": {"const": True}},
        },
    },
}

_AUTHORIZED_SEMANTIC_SOURCES = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.PRIVATE_ORIGINAL,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.SURVIVING_HOST,
    EvidenceSourceKind.SURVIVING_TYPE,
    EvidenceSourceKind.APPROVED_PROTOTYPE,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
)


def _semantic_spec_0_1(
    check_id: str,
    fact_pattern: str,
    applicability: SemanticApplicability,
) -> SemanticFactSpec:
    return SemanticFactSpec(
        check_id=check_id,
        version="0.1",
        fact_pattern=fact_pattern,
        applicability=applicability,
        allowed_sources=_AUTHORIZED_SEMANTIC_SOURCES,
        comparison=ComparisonRule.TYPED_EQUIVALENCE,
        absolute_tolerance=1e-6,
    )


WINDOW_EVALUATION_POLICY_0_1 = OperationEvaluationPolicy(
    policy_id="window.add-with-opening.l2",
    version="0.1",
    operation_type=OPERATION_TYPE,
    semantic_role="window",
    semantic_facts=(
        _semantic_spec_0_1("window.type", "relationship:type", SemanticApplicability.REQUIRED),
        _semantic_spec_0_1("window.host", "relationship:host", SemanticApplicability.REQUIRED),
        _semantic_spec_0_1("window.storey", "relationship:storey", SemanticApplicability.REQUIRED),
        _semantic_spec_0_1(
            "window.is-external",
            "pset:Pset_WindowCommon.IsExternal",
            SemanticApplicability.REQUIRED,
        ),
        _semantic_spec_0_1("window.width", "attribute:OverallWidth", SemanticApplicability.REQUIRED),
        _semantic_spec_0_1("window.height", "attribute:OverallHeight", SemanticApplicability.REQUIRED),
        _semantic_spec_0_1(
            "window.base-quantities",
            "quantity:Qto_WindowBaseQuantities.*",
            SemanticApplicability.REQUIRED,
        ),
        _semantic_spec_0_1("window.material", "material:*", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_1(
            "window.classification",
            "classification:*",
            SemanticApplicability.CONDITIONAL,
        ),
        _semantic_spec_0_1("window.pset", "pset:*", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_1("window.quantity", "quantity:*", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_1("window.name", "label:Name", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_1("window.tag", "label:Tag", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_1("window.instance", "instance:*", SemanticApplicability.CONDITIONAL),
    ),
)

_WINDOW_PRODUCTION_SOURCES = _AUTHORIZED_SEMANTIC_SOURCES + (
    EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
)


def _semantic_spec_0_2(
    check_id: str,
    fact_pattern: str,
    applicability: SemanticApplicability,
) -> SemanticFactSpec:
    return SemanticFactSpec(
        check_id=check_id,
        version="0.2",
        fact_pattern=fact_pattern,
        applicability=applicability,
        allowed_sources=_WINDOW_PRODUCTION_SOURCES,
        comparison=ComparisonRule.TYPED_EQUIVALENCE,
        absolute_tolerance=1e-6,
    )


_WINDOW_QUANTITY_ALIASES = {
    f"quantity:{set_name}.{quantity}": f"quantity:window-base.{quantity}"
    for set_name in ("BaseQuantities", "Qto_WindowBaseQuantities")
    for quantity in ("Width", "Height", "Area", "SillHeight")
}


def canonicalize_window_fact_key(fact_key: str) -> FactKeyNormalization:
    canonical = _WINDOW_QUANTITY_ALIASES.get(fact_key)
    if canonical is not None:
        return FactKeyNormalization(canonical, fact_key)
    if fact_key.startswith("quantity:") and (
        "BaseQuantities." in fact_key or fact_key.startswith("quantity:Qto_")
    ):
        raise ValueError(f"UNSUPPORTED_WINDOW_QUANTITY_ALIAS: {fact_key}")
    return FactKeyNormalization(fact_key, fact_key)


WINDOW_EVALUATION_POLICY = OperationEvaluationPolicy(
    policy_id="window.add-with-opening.l2",
    version="0.2",
    operation_type=OPERATION_TYPE,
    semantic_role="window",
    semantic_facts=(
        _semantic_spec_0_2("window.type", "relationship:type", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2("window.host", "relationship:host", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2("window.storey", "relationship:storey", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2("window.width", "attribute:OverallWidth", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2("window.height", "attribute:OverallHeight", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2(
            "window.is-external",
            "pset:Pset_WindowCommon.IsExternal",
            SemanticApplicability.REQUIRED,
        ),
        _semantic_spec_0_2("window.quantity.width", "quantity:window-base.Width", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2("window.quantity.height", "quantity:window-base.Height", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2("window.quantity.area", "quantity:window-base.Area", SemanticApplicability.REQUIRED),
        _semantic_spec_0_2(
            "window.quantity.sill-height",
            "quantity:window-base.SillHeight",
            SemanticApplicability.CONDITIONAL,
        ),
        _semantic_spec_0_2("window.material", "material:*", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_2("window.classification", "classification:*", SemanticApplicability.CONDITIONAL),
        _semantic_spec_0_2(
            "window.reference",
            "pset:Pset_WindowCommon.Reference",
            SemanticApplicability.CONDITIONAL,
        ),
        _semantic_spec_0_2(
            "window.thermal-transmittance",
            "pset:Pset_WindowCommon.ThermalTransmittance",
            SemanticApplicability.CONDITIONAL,
        ),
    ),
    fact_key_normalizer=canonicalize_window_fact_key,
    cohort_fact_patterns=(
        "pset:Pset_WindowCommon.IsExternal",
        "pset:Pset_WindowCommon.Reference",
        "pset:Pset_WindowCommon.ThermalTransmittance",
        "quantity:window-base.*",
        "material:*",
        "classification:*",
    ),
    target_authority_mode="host_for_created_entity",
)

WINDOW_L1_POLICY_ID = "window.add-with-opening.l1"
WINDOW_L1_POLICY_VERSION = "0.2"
WINDOW_L1_AUTHORIZATION = {
    "policy_id": WINDOW_L1_POLICY_ID,
    "policy_version": WINDOW_L1_POLICY_VERSION,
    "created": {
        "opening": "IfcOpeningElement",
        "window": "IfcWindow",
        "voids_relationship": "IfcRelVoidsElement",
        "fills_relationship": "IfcRelFillsElement",
        "window_type_relationship": "IfcRelDefinesByType",
        "generated_window_type": "IfcWindowStyle",
        "semantic_pset": "IfcPropertySet",
        "semantic_pset_relationship": "IfcRelDefinesByProperties",
        "semantic_quantities": "IfcElementQuantity",
        "semantic_quantity_relationship": "IfcRelDefinesByProperties",
        "semantic_opening_quantities": "IfcElementQuantity",
        "semantic_opening_quantity_relationship": "IfcRelDefinesByProperties",
        "semantic_material_relationship": "IfcRelAssociatesMaterial",
        "semantic_classification_relationship": "IfcRelAssociatesClassification",
        **{
            f"semantic_material_relationship_{index}": "IfcRelAssociatesMaterial"
            for index in range(2, 65)
        },
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
        "window_type_relationship": "IfcRelDefinesByType",
        "spatial_containment": "IfcRelContainedInSpatialStructure",
    },
    "removed": {},
    "required_roles": {
        "created": (
            "opening",
            "window",
            "voids_relationship",
            "fills_relationship",
        ),
        "modified": ("spatial_containment",),
    },
    "relations": {
        "voids_relationship": {
            "ifc_class": "IfcRelVoidsElement",
            "endpoints": {
                "RelatingBuildingElement": "target",
                "RelatedOpeningElement": "opening",
            },
        },
        "fills_relationship": {
            "ifc_class": "IfcRelFillsElement",
            "endpoints": {
                "RelatingOpeningElement": "opening",
                "RelatedBuildingElement": "window",
            },
        },
        "window_type_relationship": {
            "ifc_class": "IfcRelDefinesByType",
            "added_endpoint_roles": ("window",),
        },
        "spatial_containment": {
            "ifc_class": "IfcRelContainedInSpatialStructure",
            "added_endpoint_roles": ("window",),
        },
        "semantic_pset_relationship": {
            "ifc_class": "IfcRelDefinesByProperties",
            "added_endpoint_roles": ("window",),
        },
        "semantic_quantity_relationship": {
            "ifc_class": "IfcRelDefinesByProperties",
            "added_endpoint_roles": ("window",),
        },
        "semantic_opening_quantity_relationship": {
            "ifc_class": "IfcRelDefinesByProperties",
            "added_endpoint_roles": ("opening",),
        },
        "semantic_material_relationship": {
            "ifc_class": "IfcRelAssociatesMaterial",
            "added_endpoint_roles": ("window",),
        },
        **{
            f"semantic_material_relationship_{index}": {
                "ifc_class": "IfcRelAssociatesMaterial",
                "added_endpoint_roles": ("window",),
            }
            for index in range(2, 65)
        },
        "semantic_classification_relationship": {
            "ifc_class": "IfcRelAssociatesClassification",
            "added_endpoint_roles": ("window",),
        },
        **{
            f"semantic_pset_relationship_{index}": {
                "ifc_class": "IfcRelDefinesByProperties",
                "added_endpoint_roles": ("window",),
            }
            for index in range(2, 65)
        },
    },
}


def window_operation_definition() -> OperationDefinition:
    return OperationDefinition(
        operation_type=OPERATION_TYPE,
        target_ifc_classes=("IfcWall",),
        parameter_schema=PARAMETER_SCHEMA,
        context_adapter=_context_adapter,
        precondition_checker=_precondition_checker,
        applicator=_applicator,
        postcondition_checker=_postcondition_checker,
        comparison_adapter=_comparison_adapter,
        capability_constraints={
            "ifc_schemas": ["IFC2X3"],
            "wall_geometry": ["straight_wall"],
            "length_unit": "millimetre",
        },
        prototype_ifc_classes=("IfcWindowStyle", "IfcWindowType"),
        prototype_dimension_paths={
            "width_mm": ("opening", "width_mm"),
            "height_mm": ("opening", "height_mm"),
        },
        target_schema=TARGET_SCHEMA,
        precondition_names=(
            "base_model_fingerprint_matches",
            "source_request_hash_matches",
            "target_exists",
            "opening_within_wall",
            "opening_interval_available",
        ),
        postcondition_names=(
            "opening_voids_wall",
            "window_fills_opening",
            "requested_geometry_matches",
        ),
        evaluation_policy=WINDOW_EVALUATION_POLICY,
        semantic_policy_fact_builder=_semantic_policy_facts,
        editable_occurrence_ifc_class="IfcWindow",
        inherited_type_evidence_role="IfcWindowStyle",
        generated_type_template=_generated_window_type_template,
        generated_occurrence_facts=_generated_window_occurrence_facts,
        operation_conflict_checker=_operation_conflict_checker,
        prompt_profile_id="window.add-with-opening.v0.2",
        semantic_scope_roles={
            "window": "window_occurrence",
            "opening": "opening_occurrence",
        },
        conflict_domain="hosted_opening",
    )


def _operation_conflict_checker(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> list[dict[str, str]]:
    return hosted_opening_conflict_checker(previous, current)


def _generated_window_type_template(
    *,
    operation_id: str,
    request_hash: str,
    model_fingerprint: str,
) -> dict[str, Any]:
    del request_hash, model_fingerprint
    return {
        "template_version": "0.1",
        "ifc_class": "IfcWindowStyle",
        "name": f"Text2IFC generated window type {operation_id}",
        "construction_type": "NOTDEFINED",
        "operation_type": "NOTDEFINED",
        "parameter_takes_precedence": False,
        "sizeable": False,
    }


def _generated_window_occurrence_facts(*, target_record: Any) -> tuple[dict[str, Any], ...]:
    wall_external = next(
        (
            fact
            for fact in target_record.properties
            if fact.set_kind == "pset"
            and fact.set_name == "Pset_WallCommon"
            and fact.property_name == "IsExternal"
            and isinstance(fact.value, bool)
        ),
        None,
    )
    if wall_external is None:
        return ()
    return (
        {
            "kind": "deterministic_occurrence_property",
            "set_name": "Pset_WindowCommon",
            "property_name": "IsExternal",
            "value": wall_external.value,
            "value_type": "IfcBoolean",
            "unit": None,
            "source_ref": f"current-host:{target_record.ifc_global_id}",
            "provenance": (
                f"host-wall-property:{wall_external.provenance}",
                "window-adapter:generated-template-0.1",
            ),
        },
    )


def _semantic_policy_facts(*, operation: Mapping[str, Any]) -> tuple[Any, ...]:
    from text2ifc_ifc_repair.semantic_facts import SemanticFact

    operation_id = str(operation["operation_id"])
    opening = operation["parameters"]["opening"]
    width = float(opening["width_mm"])
    height = float(opening["height_mm"])
    values = [
        ("attribute:OverallWidth", width, "IfcPositiveLengthMeasure", None),
        ("attribute:OverallHeight", height, "IfcPositiveLengthMeasure", None),
    ]
    managed_quantity_aliases = {
        "quantity:window-base.Width": "quantity:window-base.Width",
        "quantity:window-base.Height": "quantity:window-base.Height",
        "quantity:window-base.Area": "quantity:window-base.Area",
        "quantity:BaseQuantities.Width": "quantity:window-base.Width",
        "quantity:BaseQuantities.Height": "quantity:window-base.Height",
        "quantity:BaseQuantities.Area": "quantity:window-base.Area",
        "quantity:Qto_WindowBaseQuantities.Width": "quantity:window-base.Width",
        "quantity:Qto_WindowBaseQuantities.Height": "quantity:window-base.Height",
        "quantity:Qto_WindowBaseQuantities.Area": "quantity:window-base.Area",
    }
    authorized_quantity_keys = {
        managed_quantity_aliases[str(item.get("fact_key"))]
        for item in operation.get("authorized_semantics", ())
        if isinstance(item, Mapping)
        and item.get("kind") == "authorized_occurrence_assignment"
        and str(item.get("fact_key")) in managed_quantity_aliases
    }
    for value in (
        ("quantity:window-base.Width", width, "IfcQuantityLength", None),
        ("quantity:window-base.Height", height, "IfcQuantityLength", None),
        ("quantity:window-base.Area", width * height, "IfcQuantityArea", None),
    ):
        if value[0] not in authorized_quantity_keys:
            values.append(value)
    return tuple(
        SemanticFact(
            fact_key=fact_key,
            value=value,
            value_type=value_type,
            unit=unit,
            inherited=False,
            pset_path=None,
            entity_source=f"resolved-operation:{operation_id}",
            source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
            source_ref=f"resolved:/operations/{operation_id}/parameters/opening",
            provenance=(f"operation:{operation_id}", "registered-window-parameter-policy:0.2"),
            # The parameter facts are registry policy, so their canonical kind
            # is deterministic_derived regardless of authorized occurrence
            # assignments.  Gating it kept the manifest at v0.1 vocabulary,
            # which cannot coexist with v0.3 structural manifests under one
            # bound envelope (mixed-family changesets failed binding).
            canonical_source_kind="deterministic_derived",
        )
        for fact_key, value, value_type, unit in values
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
    wall_global_id = str(operation["target"]["wall_global_id"])
    try:
        wall = model.by_guid(wall_global_id)
    except RuntimeError:
        wall = None
    if wall is None:
        return _result_with_issue(
            "TARGET_NOT_FOUND", "/target/wall_global_id", wall_global_id
        )
    try:
        straight_wall_axis(wall)
    except ValueError as error:
        if str(error) != UNSUPPORTED_WALL_GEOMETRY:
            raise
        return _result_with_issue(
            UNSUPPORTED_WALL_GEOMETRY,
            "/target/wall_global_id",
            wall_global_id,
        )

    dimensions = _clean_numbers(wall_dimensions_mm(wall))
    parameters = operation["parameters"]
    center = float(parameters["position"]["center_offset_mm"])
    opening = parameters["opening"]
    width = float(opening["width_mm"])
    height = float(opening["height_mm"])
    sill = float(opening["sill_height_mm"])
    requested_interval = [center - width / 2.0, center + width / 2.0]
    evidence = {
        "wall_global_id": wall_global_id,
        "wall_dimensions_mm": dimensions,
        "requested_interval_mm": requested_interval,
        "requested_vertical_interval_mm": [sill, sill + height],
        "existing_opening_intervals_mm": [],
        "existing_opening_regions_mm": [],
    }
    checks: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []

    _record_check(
        checks,
        issues,
        code="OPENING_WITHIN_WALL_HORIZONTAL",
        passed=requested_interval[0] >= 0 and requested_interval[1] <= dimensions["length"],
        failure_code="OPENING_OUTSIDE_WALL_HORIZONTAL",
        path="/parameters/position/center_offset_mm",
        evidence={"requested_interval_mm": requested_interval, "wall_length_mm": dimensions["length"]},
    )
    _record_check(
        checks,
        issues,
        code="OPENING_WITHIN_WALL_VERTICAL",
        passed=sill >= 0 and sill + height <= dimensions["height"],
        failure_code="OPENING_OUTSIDE_WALL_VERTICAL",
        path="/parameters/opening",
        evidence={"requested_interval_mm": [sill, sill + height], "wall_height_mm": dimensions["height"]},
    )
    _record_check(
        checks,
        issues,
        code="WALL_VOID_DEPTH_RESOLVED",
        passed=dimensions["thickness"] > 0,
        failure_code="WALL_VOID_DEPTH_UNRESOLVED",
        path="/target/wall_global_id",
        evidence={"wall_thickness_mm": dimensions["thickness"]},
    )

    overlap = None
    for relationship in wall.HasOpenings:
        existing = relationship.RelatedOpeningElement
        existing_dimensions = opening_dimensions_mm(existing)
        existing_position = opening_position_in_wall_mm(existing, wall)
        existing_center = existing_position["center_offset"]
        existing_width = existing_dimensions["width"]
        interval = [
            existing_center - existing_width / 2.0,
            existing_center + existing_width / 2.0,
        ]
        vertical_interval = [
            float(existing_position["sill_height"]),
            float(existing_position["sill_height"]) + float(existing_dimensions["height"]),
        ]
        evidence["existing_opening_intervals_mm"].append(interval)
        region = {
            "horizontal_interval_mm": interval,
            "vertical_interval_mm": vertical_interval,
        }
        evidence["existing_opening_regions_mm"].append(region)
        horizontal_overlap = max(requested_interval[0], interval[0]) < min(
            requested_interval[1], interval[1]
        )
        vertical_overlap = max(sill, vertical_interval[0]) < min(
            sill + height, vertical_interval[1]
        )
        if horizontal_overlap and vertical_overlap:
            overlap = region
    evidence["existing_opening_intervals_mm"].sort(key=lambda item: item[0])
    evidence["existing_opening_regions_mm"].sort(
        key=lambda item: (
            item["horizontal_interval_mm"][0],
            item["vertical_interval_mm"][0],
        )
    )
    _record_check(
        checks,
        issues,
        code="OPENING_INTERVAL_AVAILABLE",
        passed=overlap is None,
        failure_code="OPENING_OVERLAP",
        path="/parameters/position/center_offset_mm",
        evidence={"overlapping_region_mm": overlap},
    )
    return {"checks": checks, "issues": issues, "evidence": evidence}


def _record_check(
    checks: list[dict[str, Any]],
    issues: list[dict[str, str]],
    *,
    code: str,
    passed: bool,
    failure_code: str,
    path: str,
    evidence: Mapping[str, Any],
) -> None:
    checks.append(
        {
            "code": code,
            "status": "passed" if passed else "failed",
            "evidence": dict(evidence),
        }
    )
    if not passed:
        issues.append(
            {
                "code": failure_code,
                "path": path,
                "message": failure_code.replace("_", " ").title(),
            }
        )


def _result_with_issue(code: str, path: str, detail: str) -> dict[str, Any]:
    return {
        "checks": [{"code": code, "status": "failed", "evidence": {"detail": detail}}],
        "issues": [{"code": code, "path": path, "message": detail}],
        "evidence": {},
    }


def _clean_numbers(values: Mapping[str, float]) -> dict[str, float]:
    return {key: round(float(value), 6) for key, value in values.items()}


def _applicator(*, operation: Mapping[str, Any], model: Any) -> dict[str, Any]:
    """Create a deterministic Window-Opening-Wall chain incrementally."""

    wall = _require_guid(model, str(operation["target"]["wall_global_id"]), "IfcWall")
    parameters = operation["parameters"]
    opening_parameters = parameters["opening"]
    width = float(opening_parameters["width_mm"])
    height = float(opening_parameters["height_mm"])
    sill = float(opening_parameters["sill_height_mm"])
    center = float(parameters["position"]["center_offset_mm"])
    wall_dimensions = wall_dimensions_mm(wall)
    thickness = float(wall_dimensions["thickness"])
    body_context = _body_context(model)

    ids = {
        role: _deterministic_global_id(operation, role)
        for role in (
            "opening",
            "window",
            "voids_relationship",
            "fills_relationship",
        )
    }
    for global_id in ids.values():
        try:
            existing = model.by_guid(global_id)
        except RuntimeError:
            existing = None
        if existing is not None:
            raise OperationRegistryError("DETERMINISTIC_GLOBAL_ID_COLLISION", global_id)

    owner_history = wall.OwnerHistory
    opening = model.create_entity(
        "IfcOpeningElement",
        GlobalId=ids["opening"],
        OwnerHistory=owner_history,
        Name=f"Text2IFC opening {operation['operation_id']}",
        ObjectType="Opening",
        Tag=str(operation["operation_id"]),
    )
    opening_representation = ifcopenshell.api.geometry.add_wall_representation(
        model,
        context=body_context,
        length=width / 1000.0,
        height=height / 1000.0,
        thickness=thickness / 1000.0,
        offset=-thickness / 2000.0,
    )
    opening.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[opening_representation]
    )
    opening.ObjectPlacement = _opening_placement(
        model,
        wall=wall,
        center_mm=center,
        width_mm=width,
        sill_mm=sill,
    )

    bound_type_assignment = next(
        (
            item
            for item in operation.get("semantic_assignments", ())
            if item.get("fact_key") == "relationship:type"
        ),
        None,
    )
    generated_type_created = False
    if bound_type_assignment is not None:
        window_type, generated_type_created = ensure_bound_type(
            model,
            bound_type_assignment,
            owner_history=owner_history,
            operation_id=str(operation["operation_id"]),
        )
    else:
        window_type = None
    window = model.create_entity(
        "IfcWindow",
        GlobalId=ids["window"],
        OwnerHistory=owner_history,
        Name=f"Text2IFC window {operation['operation_id']}",
        ObjectType=str(window_type.Name) if window_type is not None else "Text2IFC fixed window",
        Tag=str(operation["operation_id"]),
        OverallHeight=millimetres_to_project_units(model, height),
        OverallWidth=millimetres_to_project_units(model, width),
    )
    if window_type is not None and window_type.RepresentationMaps:
        mapped_representations = [
            ifcopenshell.api.geometry.map_representation(
                model, representation=representation_map.MappedRepresentation
            )
            for representation_map in window_type.RepresentationMaps
        ]
        window.Representation = model.create_entity(
            "IfcProductDefinitionShape", Representations=mapped_representations
        )
    else:
        window_representation = ifcopenshell.api.geometry.add_wall_representation(
            model,
            context=body_context,
            length=width / 1000.0,
            height=height / 1000.0,
            thickness=thickness / 1000.0,
            offset=-thickness / 2000.0,
        )
        window.Representation = model.create_entity(
            "IfcProductDefinitionShape", Representations=[window_representation]
        )
    uses_mapped_representation = bool(
        window_type is not None and window_type.RepresentationMaps
    )
    window.ObjectPlacement = _local_placement(
        model,
        relative_to=opening.ObjectPlacement,
        location=(
            0.0,
            (
                -millimetres_to_project_units(model, thickness / 2.0)
                if uses_mapped_representation
                else 0.0
            ),
            0.0,
        ),
    )

    voids = model.create_entity(
        "IfcRelVoidsElement",
        GlobalId=ids["voids_relationship"],
        OwnerHistory=owner_history,
        RelatingBuildingElement=wall,
        RelatedOpeningElement=opening,
    )
    fills = model.create_entity(
        "IfcRelFillsElement",
        GlobalId=ids["fills_relationship"],
        OwnerHistory=owner_history,
        RelatingOpeningElement=opening,
        RelatedBuildingElement=window,
    )

    created_type_relationship = None
    modified = [{"role": "host_wall", "global_id": str(wall.GlobalId)}]
    if window_type is not None:
        type_relation = next(iter(window_type.ObjectTypeOf), None)
        if type_relation is None:
            type_relation = model.create_entity(
                "IfcRelDefinesByType",
                GlobalId=_deterministic_global_id(operation, "type_relationship"),
                OwnerHistory=owner_history,
                RelatedObjects=[window],
                RelatingType=window_type,
            )
            created_type_relationship = type_relation
        else:
            type_relation.RelatedObjects = _sorted_roots(
                [*type_relation.RelatedObjects, window]
            )
            modified.append(
                {
                    "role": "window_type_relationship",
                    "global_id": str(type_relation.GlobalId),
                }
            )

    containment = _wall_containment(wall)
    containment.RelatedElements = _sorted_roots([*containment.RelatedElements, window])
    modified.append(
        {"role": "spatial_containment", "global_id": str(containment.GlobalId)}
    )

    return {
        "created": [
            *(
                [
                    {
                        "role": "generated_window_type",
                        "ifc_class": window_type.is_a(),
                        "global_id": str(window_type.GlobalId),
                    }
                ]
                if generated_type_created
                else []
            ),
            *(
                [
                    {
                        "role": "window_type_relationship",
                        "ifc_class": created_type_relationship.is_a(),
                        "global_id": str(
                            created_type_relationship.GlobalId
                        ),
                    }
                ]
                if created_type_relationship is not None
                else []
            ),
            {"role": "opening", "ifc_class": opening.is_a(), "global_id": ids["opening"]},
            {"role": "window", "ifc_class": window.is_a(), "global_id": ids["window"]},
            {"role": "voids_relationship", "ifc_class": voids.is_a(), "global_id": ids["voids_relationship"]},
            {"role": "fills_relationship", "ifc_class": fills.is_a(), "global_id": ids["fills_relationship"]},
        ],
        "modified": modified,
        "removed": [],
        "resolved": {
            "center_offset_mm": center,
            "opening_depth_mm": thickness,
            "window_type_global_id": (
                str(window_type.GlobalId) if window_type is not None else None
            ),
        },
    }


def _postcondition_checker(
    *,
    operation: Mapping[str, Any],
    model: Any,
    application: Mapping[str, Any],
) -> dict[str, Any]:
    created = {item["role"]: item for item in application.get("created", [])}
    issues: list[dict[str, str]] = []
    checks: list[dict[str, Any]] = []

    try:
        wall = _require_guid(model, str(operation["target"]["wall_global_id"]), "IfcWall")
        opening = _require_guid(model, created["opening"]["global_id"], "IfcOpeningElement")
        window = _require_guid(model, created["window"]["global_id"], "IfcWindow")
    except (KeyError, OperationRegistryError) as error:
        return {
            "valid": False,
            "checks": [],
            "issues": [
                {
                    "code": "CREATED_CHAIN_NOT_FOUND",
                    "path": "/application/created",
                    "message": str(error),
                }
            ],
            "evidence": {},
        }

    parameters = operation["parameters"]
    requested_opening = parameters["opening"]
    dimensions = _clean_numbers(opening_dimensions_mm(opening))
    position = opening_position_in_wall_mm(opening, wall)
    voids_ok = (
        len(opening.VoidsElements) == 1
        and opening.VoidsElements[0].RelatingBuildingElement == wall
    )
    fills_ok = (
        len(window.FillsVoids) == 1
        and window.FillsVoids[0].RelatingOpeningElement == opening
    )
    expected = {
        "width": float(requested_opening["width_mm"]),
        "height": float(requested_opening["height_mm"]),
        "center": float(parameters["position"]["center_offset_mm"]),
        "sill": float(requested_opening["sill_height_mm"]),
    }
    facts = {
        "width": dimensions["width"],
        "height": dimensions["height"],
        "center": float(position["center_offset"]),
        "sill": float(position["sill_height"]),
    }
    predicates = (
        ("OPENING_VOIDS_TARGET_WALL", voids_ok, "/relationships/voids"),
        ("WINDOW_FILLS_OPENING", fills_ok, "/relationships/fills"),
        (
            "OPENING_GEOMETRY_MATCHES_PARAMETERS",
            all(math.isclose(facts[key], expected[key], abs_tol=1e-4) for key in expected),
            "/parameters/opening",
        ),
        (
            "WINDOW_DIMENSIONS_MATCH_OPENING",
            math.isclose(
                project_units_to_millimetres(model, window.OverallWidth),
                expected["width"],
                abs_tol=1e-4,
            )
            and math.isclose(
                project_units_to_millimetres(model, window.OverallHeight),
                expected["height"],
                abs_tol=1e-4,
            ),
            "/parameters/window",
        ),
    )
    for code, passed, path in predicates:
        checks.append(
            {"code": code, "status": "passed" if passed else "failed", "evidence": facts}
        )
        if not passed:
            issues.append({"code": code, "path": path, "message": code.replace("_", " ").title()})
    return {
        "valid": not issues,
        "checks": checks,
        "issues": issues,
        "evidence": {
            "opening_global_id": str(opening.GlobalId),
            "window_global_id": str(window.GlobalId),
            "measured": facts,
            "expected": expected,
        },
    }


def _comparison_adapter(
    *,
    operation: Mapping[str, Any],
    before_model: Any,
    after_model: Any,
    application: Mapping[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """Return structured non-evaluable evidence when IFC geometry cannot measure."""

    try:
        return _measure_comparison_adapter(
            operation=operation,
            before_model=before_model,
            after_model=after_model,
            application=application,
            **kwargs,
        )
    except Exception as error:
        return _unmeasurable_l1_result(error)


def _measure_comparison_adapter(
    *,
    operation: Mapping[str, Any],
    before_model: Any,
    after_model: Any,
    application: Mapping[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """Measure repair geometry independently from the authoring path."""

    role_mapping = kwargs.pop("role_mapping", None)
    batch_operations = tuple(kwargs.pop("batch_operations", (operation,)))
    batch_applications = kwargs.pop("batch_applications", {})
    del kwargs
    linear_tolerance = 0.1
    angle_tolerance = 0.1
    volume_tolerance = 1e-5
    created = (
        {str(role): {"global_id": str(global_id)} for role, global_id in role_mapping.items()}
        if role_mapping is not None
        else {item["role"]: item for item in application.get("created", [])}
    )
    try:
        wall_id = str(operation["target"]["wall_global_id"])
        wall_before = _require_guid(before_model, wall_id, "IfcWall")
        wall_after = _require_guid(after_model, wall_id, "IfcWall")
        opening = _require_guid(
            after_model, created["opening"]["global_id"], "IfcOpeningElement"
        )
        window = _require_guid(
            after_model, created["window"]["global_id"], "IfcWindow"
        )
    except (KeyError, OperationRegistryError) as error:
        return _unmeasurable_l1_result(error)

    parameters = operation["parameters"]
    expected_opening = parameters["opening"]
    expected_center = float(parameters["position"]["center_offset_mm"])
    expected_width = float(expected_opening["width_mm"])
    expected_height = float(expected_opening["height_mm"])
    expected_sill = float(expected_opening["sill_height_mm"])
    expected_depth = float(application["resolved"]["opening_depth_mm"])
    dimensions = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, wall_after)
    opening_bounds = position["geometry_bounds_mm"]
    window_bounds = product_geometry_bounds_in_host_mm(window, wall_after)

    center_error = abs(float(position["center_offset"]) - expected_center)
    sill_error = abs(float(position["sill_height"]) - expected_sill)
    width_error = abs(float(dimensions["width"]) - expected_width)
    height_error = abs(float(dimensions["height"]) - expected_height)
    depth_error = abs(float(dimensions["depth"]) - expected_depth)
    orientation_error = _opening_orientation_error_degrees(opening, wall_after)
    before_volume = _element_volume_m3(wall_before)
    after_volume = _element_volume_m3(wall_after)
    restored_void_volume = before_volume - after_volume
    expected_void_volume = 0.0
    for sibling in batch_operations:
        if sibling.get("operation_type") != OPERATION_TYPE:
            continue
        if sibling.get("target", {}).get("wall_global_id") != wall_id:
            continue
        sibling_opening = sibling["parameters"]["opening"]
        sibling_application = batch_applications.get(
            str(sibling.get("operation_id")),
            {},
        )
        sibling_depth = float(
            sibling_application.get("changes", {})
            .get("resolved", {})
            .get("opening_depth_mm", expected_depth)
        )
        expected_void_volume += (
            float(sibling_opening["width_mm"])
            * float(sibling_opening["height_mm"])
            * sibling_depth
            / 1_000_000_000.0
        )

    voids_correct = (
        len(opening.VoidsElements) == 1
        and opening.VoidsElements[0].RelatingBuildingElement == wall_after
    )
    fills_correct = (
        len(window.FillsVoids) == 1
        and window.FillsVoids[0].RelatingOpeningElement == opening
    )
    window_geometry_contained = all(
        float(window_bounds[axis][0])
        >= float(opening_bounds[axis][0]) - linear_tolerance
        and float(window_bounds[axis][1])
        <= float(opening_bounds[axis][1]) + linear_tolerance
        for axis in ("x", "z")
    )
    # A frame may legitimately project beyond both faces of its wall Opening.
    # Require its depth midpoint to remain inside the Opening interval instead
    # of requiring the whole frame depth to be contained by the wall void.
    window_depth_midpoint = sum(
        float(value) for value in window_bounds["y"]
    ) / 2.0
    window_depth_aligned = (
        float(opening_bounds["y"][0]) - linear_tolerance
        <= window_depth_midpoint
        <= float(opening_bounds["y"][1]) + linear_tolerance
    )
    window_geometry_matches_opening_edges = all(
        abs(float(window_bounds[axis][bound]) - float(opening_bounds[axis][bound]))
        <= linear_tolerance
        for axis in ("x", "z")
        for bound in (0, 1)
    )
    window_geometry_centered = all(
        abs(
            sum(float(value) for value in window_bounds[axis])
            - sum(float(value) for value in opening_bounds[axis])
        )
        <= 2.0 * linear_tolerance
        for axis in ("x", "z")
    )
    window_nominal_dimensions_match = (
        math.isclose(
            project_units_to_millimetres(after_model, window.OverallWidth),
            expected_width,
            abs_tol=linear_tolerance,
        )
        and math.isclose(
            project_units_to_millimetres(after_model, window.OverallHeight),
            expected_height,
            abs_tol=linear_tolerance,
        )
    )
    uses_mapped_representation = any(
        str(getattr(representation, "RepresentationType", ""))
        == "MappedRepresentation"
        for representation in getattr(window.Representation, "Representations", ())
    )
    wall_storeys = {
        str(relation.RelatingStructure.GlobalId)
        for relation in wall_after.ContainedInStructure
    }
    window_storeys = {
        str(relation.RelatingStructure.GlobalId)
        for relation in window.ContainedInStructure
    }
    duplicate_count = 0
    for relation in wall_after.HasOpenings:
        candidate = relation.RelatedOpeningElement
        candidate_dimensions = opening_dimensions_mm(candidate)
        candidate_position = opening_position_in_wall_mm(candidate, wall_after)
        if (
            abs(float(candidate_position["center_offset"]) - expected_center)
            <= linear_tolerance
            and abs(float(candidate_position["sill_height"]) - expected_sill)
            <= linear_tolerance
            and abs(float(candidate_dimensions["width"]) - expected_width)
            <= linear_tolerance
            and abs(float(candidate_dimensions["height"]) - expected_height)
            <= linear_tolerance
        ):
            duplicate_count += 1

    checks = {
        "correct_host_wall": voids_correct,
        "opening_voids_wall": voids_correct,
        "window_fills_opening": fills_correct,
        "window_geometry_fits_opening": (
            window_geometry_contained
            and window_depth_aligned
            and (
                window_geometry_matches_opening_edges
                or (
                    uses_mapped_representation
                    and window_geometry_centered
                    and window_nominal_dimensions_match
                )
            )
        ),
        "storey_consistent": bool(wall_storeys) and wall_storeys == window_storeys,
        "linear_geometry_within_tolerance": max(
            center_error, sill_error, width_error, height_error, depth_error
        )
        <= linear_tolerance,
        "orientation_within_tolerance": orientation_error <= angle_tolerance,
        "geometric_void_restored": abs(restored_void_volume - expected_void_volume)
        <= volume_tolerance,
        "duplicate_chain_absent": duplicate_count == 1,
    }
    metrics = {
        "center_error_mm": round(center_error, 6),
        "sill_error_mm": round(sill_error, 6),
        "width_error_mm": round(width_error, 6),
        "height_error_mm": round(height_error, 6),
        "depth_error_mm": round(depth_error, 6),
        "orientation_error_degrees": round(orientation_error, 6),
        "restored_void_volume_m3": round(restored_void_volume, 6),
        "expected_void_volume_m3": round(expected_void_volume, 6),
        "matching_chain_count": duplicate_count,
    }
    issues = [
        {
            "code": code.upper(),
            "path": "/evaluation",
            "message": code.replace("_", " ").title(),
        }
        for code, passed in checks.items()
        if not passed
    ]
    l1_checks = _window_l1_checks(
        checks=checks,
        metrics=metrics,
        linear_tolerance=linear_tolerance,
        angle_tolerance=angle_tolerance,
        volume_tolerance=volume_tolerance,
    )
    return {
        "valid": not issues,
        "checks": checks,
        "metrics": metrics,
        "issues": issues,
        "authorization": copy.deepcopy(WINDOW_L1_AUTHORIZATION),
        "l1_checks": l1_checks,
    }


WINDOW_L1_CHECK_IDS = (
    "l1.window.containment",
    "l1.window.dimensions",
    "l1.window.duplicate-chain",
    "l1.window.filling-topology",
    "l1.window.geometry-fit",
    "l1.window.host-topology",
    "l1.window.placement",
    "l1.window.tolerances",
    "l1.window.volume-preservation",
)


def _unmeasurable_l1_result(error: Exception) -> dict[str, Any]:
    detail = f"{type(error).__name__}: {error}"
    return {
        "valid": False,
        "checks": {"created_chain_resolved": False},
        "metrics": {},
        "authorization": copy.deepcopy(WINDOW_L1_AUTHORIZATION),
        "l1_checks": {
            check_id: {
                "status": "not_evaluable",
                "reason": "Mandatory Window geometry or topology could not be measured.",
                "expected": "measurable reopened IFC evidence",
                "actual": detail,
            }
            for check_id in WINDOW_L1_CHECK_IDS
        },
        "issues": [
            {
                "code": "WINDOW_L1_NOT_EVALUABLE",
                "path": "/evaluation/L1",
                "message": detail,
            }
        ],
    }


def _window_l1_checks(
    *,
    checks: Mapping[str, bool],
    metrics: Mapping[str, float | int],
    linear_tolerance: float,
    angle_tolerance: float,
    volume_tolerance: float,
) -> dict[str, dict[str, Any]]:
    dimension_errors = {
        key: metrics[key]
        for key in ("width_error_mm", "height_error_mm", "depth_error_mm")
    }
    placement_errors = {
        key: metrics[key]
        for key in (
            "center_error_mm",
            "sill_error_mm",
            "orientation_error_degrees",
        )
    }
    dimension_ok = max(float(value) for value in dimension_errors.values()) <= linear_tolerance
    placement_ok = (
        max(
            float(placement_errors["center_error_mm"]),
            float(placement_errors["sill_error_mm"]),
        )
        <= linear_tolerance
        and float(placement_errors["orientation_error_degrees"]) <= angle_tolerance
    )
    volume_error = abs(
        float(metrics["restored_void_volume_m3"])
        - float(metrics["expected_void_volume_m3"])
    )
    volume_ok = volume_error <= volume_tolerance

    def measured(
        passed: bool,
        reason: str,
        expected: Any,
        actual: Any,
    ) -> dict[str, Any]:
        return {
            "status": "passed" if passed else "failed",
            "reason": reason,
            "expected": expected,
            "actual": actual,
        }

    return {
        "l1.window.containment": measured(
            checks["storey_consistent"],
            "Window and Host must have identical spatial containment.",
            "same non-empty storey set",
            checks["storey_consistent"],
        ),
        "l1.window.dimensions": measured(
            dimension_ok,
            "Opening dimensions must match the declared dimensions.",
            {"linear_tolerance_mm": linear_tolerance},
            dimension_errors,
        ),
        "l1.window.duplicate-chain": measured(
            checks["duplicate_chain_absent"],
            "Exactly one matching Opening chain must exist.",
            {"matching_chain_count": 1},
            {"matching_chain_count": metrics["matching_chain_count"]},
        ),
        "l1.window.filling-topology": measured(
            checks["window_fills_opening"],
            "The generated Window must fill exactly the generated Opening.",
            True,
            checks["window_fills_opening"],
        ),
        "l1.window.geometry-fit": measured(
            checks["window_geometry_fits_opening"],
            "Window geometry bounds must fit the Opening geometry bounds.",
            True,
            checks["window_geometry_fits_opening"],
        ),
        "l1.window.host-topology": measured(
            checks["correct_host_wall"] and checks["opening_voids_wall"],
            "The generated Opening must void exactly the declared Host Wall.",
            True,
            checks["correct_host_wall"] and checks["opening_voids_wall"],
        ),
        "l1.window.placement": measured(
            placement_ok,
            "Opening placement and orientation must match the declared placement.",
            {
                "linear_tolerance_mm": linear_tolerance,
                "orientation_tolerance_degrees": angle_tolerance,
            },
            placement_errors,
        ),
        "l1.window.tolerances": measured(
            dimension_ok and placement_ok and volume_ok,
            "All linear, orientation, and volume measurements must be within policy tolerances.",
            {
                "linear_mm": linear_tolerance,
                "orientation_degrees": angle_tolerance,
                "volume_m3": volume_tolerance,
            },
            {**dimension_errors, **placement_errors, "volume_error_m3": round(volume_error, 6)},
        ),
        "l1.window.volume-preservation": measured(
            volume_ok,
            "Host volume change must equal the requested Opening void volume.",
            {"absolute_tolerance_m3": volume_tolerance},
            {"volume_error_m3": round(volume_error, 6)},
        ),
    }


def _opening_orientation_error_degrees(opening: Any, wall: Any) -> float:
    wall_matrix = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)
    opening_matrix = ifcopenshell.util.placement.get_local_placement(
        opening.ObjectPlacement
    )
    relative = _inverse_rigid_transform(wall_matrix) @ opening_matrix
    opening_x = [float(relative[index, 0]) for index in range(3)]
    opening_length = math.sqrt(sum(value * value for value in opening_x))
    start, end = straight_wall_axis(wall)
    wall_x = [end[index] - start[index] for index in range(3)]
    wall_length = math.sqrt(sum(value * value for value in wall_x))
    dot = sum(
        opening_x[index] * wall_x[index] for index in range(3)
    ) / (opening_length * wall_length)
    # Either axis direction is geometrically aligned; authoring anchors may
    # legitimately use the left or right edge.
    return math.degrees(math.acos(max(-1.0, min(1.0, abs(dot)))))


def _inverse_rigid_transform(matrix: Any) -> Any:
    inverse = matrix.copy()
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -(rotation.T @ matrix[:3, 3])
    inverse[3, :] = (0.0, 0.0, 0.0, 1.0)
    return inverse


def _element_volume_m3(element: Any) -> float:
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), element)
    return float(ifcopenshell.util.shape.get_volume(shape.geometry))


def _opening_placement(
    model: Any,
    *,
    wall: Any,
    center_mm: float,
    width_mm: float,
    sill_mm: float,
) -> Any:
    return hosted_opening_placement(
        model,
        wall=wall,
        center_mm=center_mm,
        width_mm=width_mm,
        sill_mm=sill_mm,
    )


def _local_placement(
    model: Any,
    *,
    relative_to: Any,
    location: tuple[float, float, float],
    ref_direction: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> Any:
    return hosted_local_placement(
        model,
        relative_to=relative_to,
        location=location,
        ref_direction=ref_direction,
    )


def _body_context(model: Any) -> Any:
    return hosted_body_context(model)


def _wall_containment(wall: Any) -> Any:
    return hosted_wall_containment(wall)


def _sorted_roots(entities: list[Any]) -> list[Any]:
    unique = {entity.id(): entity for entity in entities}
    return sorted(
        unique.values(),
        key=lambda entity: (str(getattr(entity, "GlobalId", "")), entity.id()),
    )


def _deterministic_global_id(operation: Mapping[str, Any], role: str) -> str:
    return hosted_deterministic_global_id(operation, role)


def _require_guid(model: Any, global_id: str, ifc_class: str) -> Any:
    try:
        entity = model.by_guid(global_id)
    except RuntimeError as error:
        raise OperationRegistryError("IFC_ENTITY_NOT_FOUND", global_id) from error
    if not entity.is_a(ifc_class):
        raise OperationRegistryError(
            "IFC_ENTITY_CLASS_MISMATCH", f"{global_id}:{entity.is_a()}"
        )
    return entity
