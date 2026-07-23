from __future__ import annotations

import inspect
from types import MappingProxyType

import pytest

from text2ifc_ifc_repair.evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SemanticApplicability,
    SemanticFactSpec,
)
from text2ifc_ifc_repair.index_models import ElementRecord, PropertyFact, TypeRecord
from text2ifc_ifc_repair.production_evidence import (
    ProductionEvidenceError,
    _property_claim_matches_authority,
    build_production_evidence,
)
from text2ifc_ifc_repair.property_intent import (
    ExactPropertyIntent,
    NaturalLanguagePropertyIntent,
)
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry
from text2ifc_ifc_repair.repair_intent import (
    AttributeIntent,
    OperationIntent,
    PublicProvenance,
    RepairIntent,
)
from text2ifc_ifc_repair.resolution_flow import ResolutionBatch, ResolvedOperation
from text2ifc_ifc_repair.semantic_facts import SemanticFact
from text2ifc_ifc_repair.target_query import TargetQuery


OPERATION_TYPE = "fixture_add_component"
FACT_KEY = "pset:Pset_Fixture.Marker"


def test_natural_language_property_claim_binds_by_immutable_source() -> None:
    source = PublicProvenance(
        source_kind="user_request",
        reference="request:/text",
        excerpt="标记为外窗",
    )
    authority = {
        "set_name": "Pset_WindowCommon",
        "property_name": "IsExternal",
        "value": True,
        "ownership": "occurrence_direct",
        "source": source.to_dict(),
    }
    natural = NaturalLanguagePropertyIntent(
        property_phrase="外窗",
        raw_value=True,
        raw_unit=None,
        scope=None,
        source=source,
    )
    exact = ExactPropertyIntent(
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value=True,
        requested_value_type=None,
        requested_unit=None,
        scope=None,
        source=source,
    )

    assert _property_claim_matches_authority(natural, authority)
    assert _property_claim_matches_authority(exact, authority)
    assert not _property_claim_matches_authority(
        NaturalLanguagePropertyIntent(
            property_phrase="外窗",
            raw_value=True,
            raw_unit=None,
            scope=None,
            source=PublicProvenance(
                source_kind="user_request",
                reference="request:/other",
                excerpt="标记为外窗",
            ),
        ),
        authority,
    )


def _spec(
    fact_pattern: str,
    *,
    check_id: str,
    applicability: SemanticApplicability = SemanticApplicability.CONDITIONAL,
) -> SemanticFactSpec:
    return SemanticFactSpec(
        check_id=check_id,
        version="0.1",
        fact_pattern=fact_pattern,
        applicability=applicability,
        allowed_sources=(
            EvidenceSourceKind.EXPLICIT_REQUEST,
            EvidenceSourceKind.SURVIVING_TARGET,
            EvidenceSourceKind.SURVIVING_HOST,
            EvidenceSourceKind.SURVIVING_TYPE,
            EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
            EvidenceSourceKind.APPROVED_PROTOTYPE,
            EvidenceSourceKind.DETERMINISTIC_POLICY,
        ),
        comparison=ComparisonRule.TYPED_EQUIVALENCE,
    )


def _registry() -> OperationRegistry:
    registry = OperationRegistry()
    registry.register(
        OperationDefinition(
            operation_type=OPERATION_TYPE,
            target_ifc_classes=("IfcBuildingElement",),
            parameter_schema={"type": "object"},
            context_adapter=lambda **kwargs: kwargs,
            precondition_checker=lambda **kwargs: kwargs,
            applicator=lambda **kwargs: kwargs,
            postcondition_checker=lambda **kwargs: kwargs,
            comparison_adapter=lambda **kwargs: kwargs,
            capability_constraints={"future_families": ("Door", "Opening", "Beam", "Column")},
            evaluation_policy=OperationEvaluationPolicy(
                policy_id="fixture.production.l2",
                version="0.1",
                operation_type=OPERATION_TYPE,
                semantic_facts=(
                    _spec(FACT_KEY, check_id="fixture.marker"),
                    _spec("material:*", check_id="fixture.material"),
                    _spec("classification:*", check_id="fixture.classification"),
                    _spec("quantity:*", check_id="fixture.quantity"),
                    _spec(
                        "relationship:host",
                        check_id="fixture.host",
                        applicability=SemanticApplicability.REQUIRED,
                    ),
                    _spec(
                        "pset:Pset_Fixture.IsExternal",
                        check_id="fixture.external",
                        applicability=SemanticApplicability.REQUIRED,
                    ),
                ),
                cohort_fact_patterns=("pset:Pset_Fixture.IsExternal",),
            ),
        )
    )
    return registry


def _provenance(reference: str = "request:/operations/0") -> PublicProvenance:
    return PublicProvenance(
        source_kind="user_request",
        reference=reference,
        excerpt="set fixture marker",
    )


def _intent(*, operation_id: str = "operation-1", request_value: object = "request") -> RepairIntent:
    query = TargetQuery(
        allowed_ifc_classes=("IfcBuildingElement",),
        global_id="target-1",
        host_global_id="host-1",
    )
    operation = OperationIntent(
        operation_id=operation_id,
        operation_type=OPERATION_TYPE,
        target_query=query,
        parameters=MappingProxyType({}),
        attribute_intents=(
            AttributeIntent(
                intent_kind="pset",
                name="Pset_Fixture.Marker",
                value=request_value,
                source=_provenance(),
            ),
        ),
        prototype_intent=None,
        provenance=(_provenance(),),
        _target_query_document=MappingProxyType(
            {
                "schema_version": query.schema_version,
                "allowed_ifc_classes": list(query.allowed_ifc_classes),
                "global_id": query.global_id,
                "host_global_id": query.host_global_id,
            }
        ),
    )
    return RepairIntent(
        request_id="request-1",
        source_request_hash="sha256:" + "1" * 64,
        model_fingerprint="sha256:" + "2" * 64,
        prompt_fingerprint="sha256:" + "3" * 64,
        operations=(operation,),
        provenance=(_provenance("request:/"),),
    )


def _property(
    value: object,
    *,
    set_kind: str = "pset",
    set_name: str = "Pset_Fixture",
    property_name: str = "Marker",
) -> PropertyFact:
    return PropertyFact(
        set_kind=set_kind,
        set_name=set_name,
        property_name=property_name,
        value=value,
        value_type="IfcBoolean" if isinstance(value, bool) else "IfcLabel",
        unit=None,
        inherited=False,
        provenance="ifcopenshell.util.element.get_psets",
    )


def _record(
    global_id: str,
    value: object,
    *,
    type_global_id: str | None = None,
    properties: tuple[PropertyFact, ...] | None = None,
) -> ElementRecord:
    return ElementRecord(
        record_id=f"ifc:{global_id}",
        ifc_global_id=global_id,
        identity_reliable=True,
        ifc_class="IfcBuildingElement",
        name=global_id,
        long_name=None,
        tag=None,
        object_type=None,
        type_name=None,
        type_global_id=type_global_id,
        storey_name="Level 1",
        storey_global_id="storey-1",
        geometry_capability="bbox",
        facets={"host_wall_global_ids": ["host-1"]},
        properties=properties if properties is not None else (_property(value),),
    )


def _type_record(
    global_id: str,
    value: object,
    *,
    properties: tuple[PropertyFact, ...] | None = None,
    ifc_class: str = "IfcBuildingElementType",
) -> TypeRecord:
    return TypeRecord(
        record_id=f"type:{global_id}",
        ifc_global_id=global_id,
        identity_reliable=True,
        ifc_class=ifc_class,
        name=global_id,
        applicable_occurrence=None,
        predefined_type=None,
        element_type=None,
        provenance={"source": "current_ifc", "step_id": 42},
        properties=properties if properties is not None else (_property(value),),
    )


def _resolution(*, operation_id: str = "operation-1") -> ResolutionBatch:
    return ResolutionBatch(
        status="resolved",
        source_ifc_sha256="sha256:" + "4" * 64,
        model_fingerprint="sha256:" + "2" * 64,
        operations=(
            ResolvedOperation(
                operation_id=operation_id,
                operation_type=OPERATION_TYPE,
                target_global_id="target-1",
                scope_ids=("target-1",),
                evidence_pointers=(f"resolution:/{operation_id}/target",),
                parameters={},
                context={"candidate_targets": [], "model_constraints": {}},
                authorized_semantics=(
                    {
                        "kind": "formal_type_binding",
                        "global_id": "type-1",
                        "provenance": "current_ifc",
                    },
                    {
                        "kind": "user_authorized_prototype",
                        "global_id": "prototype-1",
                        "authorization": "stored_user_answer",
                    },
                ),
            ),
        ),
    )


def _changeset(*, operation_id: str = "operation-1") -> dict[str, object]:
    return {
        "base_model_fingerprint": "sha256:" + "4" * 64,
        "operations": [
            {
                "operation_id": operation_id,
                "operation_type": OPERATION_TYPE,
                "target": {"global_id": "target-1"},
                "parameters": {},
            }
        ],
    }


def _policy_fact(value: object = "policy") -> SemanticFact:
    return SemanticFact(
        fact_key=FACT_KEY,
        value=value,
        value_type="IfcLabel",
        unit=None,
        inherited=False,
        pset_path="Pset_Fixture.Marker",
        entity_source="policy:fixture.production.l2",
        source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
        source_ref="policy:fixture.production.l2/fixture.marker",
        provenance=("registered-policy:fixture.production.l2@0.1",),
    )


def _build(**overrides: object):
    values = {
        "intent": _intent(),
        "resolution": _resolution(),
        "changeset": _changeset(),
        "registry": _registry(),
        "records_by_global_id": {
            "target-1": _record("target-1", "target", type_global_id="type-1"),
            "host-1": _record("host-1", "host"),
        },
        "type_records_by_global_id": {
            "type-1": _type_record("type-1", "type"),
            "prototype-1": _type_record("prototype-1", "prototype"),
        },
        "deterministic_policy_facts_by_operation": {"operation-1": (_policy_fact(),)},
        "verified_absent_categories_by_operation": {
            "operation-1": ("material", "classification", "quantity")
        },
    }
    values.update(overrides)
    return build_production_evidence(**values)


def test_explicit_request_wins_all_lower_authority_and_records_conflicts() -> None:
    evidence = _build()

    marker = next(
        fact
        for fact in evidence.expected_facts_by_operation["operation-1"]
        if fact.fact_key == FACT_KEY
    )
    assert marker.value == "request"
    assert marker.source_kind is EvidenceSourceKind.EXPLICIT_REQUEST
    assert marker.source_ref == "request:/operations/0"
    assert marker.provenance[-1] == "operation:operation-1"
    assert {conflict.rejected_source.value for conflict in evidence.conflicts} == {
        "surviving_target",
        "surviving_host",
        "surviving_type",
        "approved_prototype",
        "deterministic_policy",
    }
    assert all(conflict.reason == "lower_authority_conflict" for conflict in evidence.conflicts)


def test_formal_type_and_user_approved_prototype_have_distinct_auditable_sources() -> None:
    evidence = _build(intent=_intent(request_value="request-other"))
    facts = evidence.candidate_facts_by_operation["operation-1"]

    formal = next(fact for fact in facts if fact.source_kind is EvidenceSourceKind.SURVIVING_TYPE)
    prototype = next(
        fact for fact in facts if fact.source_kind is EvidenceSourceKind.APPROVED_PROTOTYPE
    )
    assert formal.source_ref == "formal-type:type-1"
    assert "formal_type_binding:current_ifc" in formal.provenance
    assert prototype.source_ref == "user-approved-prototype:prototype-1"
    assert "user_authorization:stored_user_answer" in prototype.provenance


def test_explicit_request_prototype_is_authorized_with_distinct_provenance() -> None:
    base = _resolution().operations[0]
    explicit = ResolvedOperation(
        operation_id=base.operation_id,
        operation_type=base.operation_type,
        target_global_id=base.target_global_id,
        scope_ids=base.scope_ids,
        evidence_pointers=base.evidence_pointers,
        parameters=base.parameters,
        context=base.context,
        authorized_semantics=(
            base.authorized_semantics[0],
            {
                "kind": "user_authorized_prototype",
                "global_id": "prototype-1",
                "authorization": "explicit_request_reference",
                "prototype_lookup": "type_global_id",
                "request_provenance": {
                    "source_kind": "user_request",
                    "reference": "request:/prototype",
                    "excerpt": "use prototype-1",
                },
            },
        ),
    )
    resolution = ResolutionBatch(
        status="resolved",
        source_ifc_sha256="sha256:" + "4" * 64,
        model_fingerprint="sha256:" + "2" * 64,
        operations=(explicit,),
    )

    type_marker = PropertyFact(
        set_kind="pset",
        set_name="Pset_Fixture",
        property_name="Marker",
        value="prototype",
        value_type="IfcLabel",
        unit=None,
        inherited=False,
        provenance="ifcopenshell.util.element.get_psets:direct",
    )
    direct_level_1 = _property("Level 1", set_name="Constraints", property_name="Level")
    direct_level_2 = _property("Level 2", set_name="Constraints", property_name="Level")
    evidence = _build(
        resolution=resolution,
        records_by_global_id={
            "target-1": _record("target-1", "target", type_global_id="type-1"),
            "host-1": _record("host-1", "host"),
            "prototype-occurrence-1": _record(
                "prototype-occurrence-1",
                "prototype-instance-value",
                type_global_id="prototype-1",
                properties=(direct_level_1,),
            ),
            "prototype-occurrence-2": _record(
                "prototype-occurrence-2",
                "prototype-instance-value",
                type_global_id="prototype-1",
                properties=(direct_level_2,),
            ),
        },
        type_records_by_global_id={
            "type-1": _type_record("type-1", "type"),
            "prototype-1": _type_record(
                "prototype-1", "prototype", properties=(type_marker,)
            ),
        },
    )
    prototype = next(
        fact
        for fact in evidence.candidate_facts_by_operation["operation-1"]
        if fact.source_kind is EvidenceSourceKind.APPROVED_PROTOTYPE
    )
    assert "user_authorization:explicit_request_reference" in prototype.provenance
    assert "type_record:prototype-1" in prototype.provenance
    assert prototype.inherited is False
    assert not any(
        fact.fact_key == "pset:Constraints.Level"
        for fact in evidence.candidate_facts_by_operation["operation-1"]
        if fact.source_kind is EvidenceSourceKind.APPROVED_PROTOTYPE
    )


def test_contradictory_direct_type_facts_fail_closed() -> None:
    conflict_type = _type_record(
        "prototype-1",
        "prototype",
        properties=(_property("A"), _property("B")),
    )
    with pytest.raises(ProductionEvidenceError) as caught:
        _build(
            type_records_by_global_id={
                "type-1": _type_record("type-1", "type"),
                "prototype-1": conflict_type,
            }
        )
    assert caught.value.code == "PROTOTYPE_TYPE_FACT_CONFLICT"


@pytest.mark.parametrize(
    "category,fact",
    [
        ("material", _property("Aluminium", set_name="Material", property_name="Primary")),
        ("classification", _property("EF_25", set_name="Classification", property_name="Uniclass")),
        ("quantity", _property("2.4", set_kind="quantity", set_name="Qto_Fixture", property_name="Area")),
    ],
)
def test_conditional_category_verified_absence_is_not_required_but_presence_is_evaluable(
    category: str, fact: PropertyFact
) -> None:
    absent = _build()
    status = absent.applicability_by_operation["operation-1"][f"fixture.{category}"]
    assert status.outcome == "not_required"
    assert status.verified_absence is True

    key_prefix = {
        "material": "material:",
        "classification": "classification:",
        "quantity": "quantity:",
    }[category]
    policy_fact = SemanticFact(
        **{
            **_policy_fact().__dict__,
            "fact_key": key_prefix + "fixture",
            "value": fact.value,
        }
    )
    present = _build(
        deterministic_policy_facts_by_operation={"operation-1": (policy_fact,)},
        verified_absent_categories_by_operation={"operation-1": ()},
    )
    assert present.applicability_by_operation["operation-1"][f"fixture.{category}"].outcome == "evaluable"


def test_missing_mandatory_authority_is_not_evaluable_including_is_external() -> None:
    evidence = _build()
    applicability = evidence.applicability_by_operation["operation-1"]

    assert applicability["fixture.host"].outcome == "evaluable"
    assert applicability["fixture.external"].outcome == "not_evaluable"
    assert applicability["fixture.external"].mandatory is True


def test_cross_operation_facts_and_unregistered_policy_facts_are_rejected() -> None:
    with pytest.raises(ProductionEvidenceError, match="CROSS_OPERATION_EVIDENCE"):
        _build(
            deterministic_policy_facts_by_operation={"operation-foreign": (_policy_fact(),)}
        )

    unregistered = SemanticFact(
        **{**_policy_fact().__dict__, "fact_key": "llm:common-knowledge"}
    )
    with pytest.raises(ProductionEvidenceError, match="UNREGISTERED_POLICY_FACT"):
        _build(
            deterministic_policy_facts_by_operation={"operation-1": (unregistered,)}
        )


@pytest.mark.parametrize(
    "kind",
    [
        "nearest_candidate",
        "name_match",
        "same_storey",
        "vector_similarity",
        "llm_claim",
        "model_common_knowledge",
        "private_original",
        "mutation_mapping",
    ],
)
def test_unapproved_similar_llm_and_private_authorization_kinds_are_rejected(kind: str) -> None:
    operation = _resolution().operations[0]
    poisoned = ResolvedOperation(
        **{
            **operation.__dict__,
            "authorized_semantics": (
                {"kind": kind, "global_id": "prototype-1", "provenance": kind},
            ),
        }
    )
    with pytest.raises(ProductionEvidenceError, match="UNAUTHORIZED_SEMANTIC_AUTHORITY"):
        _build(resolution=ResolutionBatch(**{**_resolution().__dict__, "operations": (poisoned,)}))


def test_public_builder_signature_and_outputs_cannot_accept_gold_objects() -> None:
    forbidden = {
        "original_ifc_path",
        "private_original_ifc_path",
        "mutation_mapping",
        "private_mutation_mapping",
        "gold",
    }
    assert forbidden.isdisjoint(inspect.signature(build_production_evidence).parameters)

    private_fact = SemanticFact(
        **{
            **_policy_fact().__dict__,
            "source_kind": EvidenceSourceKind.PRIVATE_ORIGINAL,
            "source_ref": "gold:CANARY-GOLD",
        }
    )
    with pytest.raises(ProductionEvidenceError, match="PRODUCTION_PRIVATE_ORIGINAL_FORBIDDEN"):
        _build(
            deterministic_policy_facts_by_operation={"operation-1": (private_fact,)}
        )


def test_authorized_type_cohort_is_distinct_from_type_record_authority() -> None:
    external = _property(
        True, set_name="Pset_Fixture", property_name="IsExternal"
    )
    evidence = _build(
        records_by_global_id={
            "target-1": _record("target-1", "target", type_global_id="type-1"),
            "host-1": _record("host-1", "host"),
            "cohort-1": _record(
                "cohort-1", "ignored", type_global_id="type-1", properties=(external,)
            ),
            "unrelated-same-size": _record(
                "unrelated-same-size",
                "ignored",
                type_global_id="other-type",
                properties=(external,),
            ),
        }
    )
    cohort = [
        fact
        for fact in evidence.candidate_facts_by_operation["operation-1"]
        if fact.fact_key == "pset:Pset_Fixture.IsExternal"
    ]

    assert len(cohort) == 1
    assert cohort[0].source_kind.value == "authorized_type_cohort"
    assert "cohort-type:type-1" in cohort[0].provenance
    assert cohort[0].source_ref == "type-cohort:type-1"
    assert not any("unrelated-same-size" in item for item in cohort[0].provenance)


def test_conflicting_authorized_type_cohort_fails_closed() -> None:
    true_fact = _property(True, set_name="Pset_Fixture", property_name="IsExternal")
    false_fact = _property(False, set_name="Pset_Fixture", property_name="IsExternal")

    with pytest.raises(ProductionEvidenceError) as caught:
        _build(
            records_by_global_id={
                "target-1": _record("target-1", "target", type_global_id="type-1"),
                "host-1": _record("host-1", "host"),
                "cohort-1": _record(
                    "cohort-1", "ignored", type_global_id="type-1", properties=(true_fact,)
                ),
                "cohort-2": _record(
                    "cohort-2", "ignored", type_global_id="type-1", properties=(false_fact,)
                ),
            }
        )

    assert caught.value.code == "AUTHORIZED_TYPE_COHORT_CONFLICT"


def test_one_authority_result_builds_manifest_and_identical_l2_facts() -> None:
    from text2ifc_ifc_repair.semantic_authoring import build_semantic_manifest

    evidence = _build()
    manifest = build_semantic_manifest(
        production_evidence=evidence,
        operation_id="operation-1",
        base_model_fingerprint="sha256:" + "2" * 64,
        registry=_registry(),
    )
    expected = evidence.expected_facts_by_operation["operation-1"]
    by_key = {fact.fact_key: fact for fact in expected}

    assert manifest.operation_id == "operation-1"
    assert manifest.policy_id == "fixture.production.l2"
    assert {
        (
            item.fact_key,
            item.value,
            item.value_type,
            item.unit,
            item.source_kind,
            item.source_ref,
        )
        for item in manifest.assignments
    } == {
        (
            fact.fact_key,
            fact.value,
            fact.value_type,
            fact.unit,
            fact.source_kind,
            fact.source_ref,
        )
        for fact in expected
    }
    forbidden = {
        "original_ifc_path",
        "mutation_mapping",
        "similarity_score",
        "embedding",
        "provider_facts",
    }
    assert forbidden.isdisjoint(inspect.signature(build_semantic_manifest).parameters)


def test_operation_identity_and_registry_policy_drive_future_family_expansion() -> None:
    evidence = _build(
        type_records_by_global_id={
            "type-1": _type_record("type-1", "type"),
            "prototype-1": _type_record(
                "prototype-1", "prototype", ifc_class="IfcDoorStyle"
            ),
        }
    )

    assert tuple(evidence.expected_facts_by_operation) == ("operation-1",)
    assert evidence.operation_types == {"operation-1": OPERATION_TYPE}
    assert "Door" in _registry().require(OPERATION_TYPE).capability_constraints["future_families"]
    assert not hasattr(evidence, "window")
    prototype = next(
        fact
        for fact in evidence.candidate_facts_by_operation["operation-1"]
        if fact.source_kind is EvidenceSourceKind.APPROVED_PROTOTYPE
    )
    assert prototype.entity_source.startswith("IfcDoorStyle:")
