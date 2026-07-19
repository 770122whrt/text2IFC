from __future__ import annotations

from dataclasses import FrozenInstanceError

import ifcopenshell
import pytest

from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    PolicyContractError,
    SemanticApplicability,
    SemanticFactSpec,
)
from text2ifc_ifc_repair.index_models import ElementRecord, PropertyFact
from text2ifc_ifc_repair.operations.window import window_operation_definition
from text2ifc_ifc_repair.registry import (
    OperationDefinition,
    OperationRegistry,
    OperationRegistryError,
)
from text2ifc_ifc_repair.semantic_facts import (
    SemanticFact,
    SemanticFactError,
    evaluate_operation_semantics,
    extract_ifc_semantic_facts,
    semantic_fact_from_property_fact,
    semantic_facts_from_element_record,
)


def _spec(
    fact_pattern: str = "instance:Marker",
    *,
    check_id: str = "fixture.marker",
    applicability: SemanticApplicability = SemanticApplicability.CONDITIONAL,
    allowed_sources: tuple[EvidenceSourceKind, ...] | None = None,
) -> SemanticFactSpec:
    return SemanticFactSpec(
        check_id=check_id,
        version="0.1",
        fact_pattern=fact_pattern,
        applicability=applicability,
        allowed_sources=allowed_sources
        or (
            EvidenceSourceKind.EXPLICIT_REQUEST,
            EvidenceSourceKind.PRIVATE_ORIGINAL,
            EvidenceSourceKind.SURVIVING_TARGET,
            EvidenceSourceKind.SURVIVING_HOST,
            EvidenceSourceKind.SURVIVING_TYPE,
            EvidenceSourceKind.APPROVED_PROTOTYPE,
        ),
        comparison=ComparisonRule.TYPED_EQUIVALENCE,
    )


def _policy(
    operation_type: str = "fixture_add_component",
    *,
    policy_id: str | None = None,
    facts: tuple[SemanticFactSpec, ...] | None = None,
) -> OperationEvaluationPolicy:
    return OperationEvaluationPolicy(
        policy_id=policy_id or f"{operation_type}.l2",
        version="0.1",
        operation_type=operation_type,
        semantic_facts=facts or (_spec(),),
    )


def _definition(
    operation_type: str,
    *,
    policy: OperationEvaluationPolicy | None,
) -> OperationDefinition:
    return OperationDefinition(
        operation_type=operation_type,
        target_ifc_classes=("IfcBuildingElement",),
        parameter_schema={"type": "object"},
        context_adapter=lambda **kwargs: kwargs,
        precondition_checker=lambda **kwargs: kwargs,
        applicator=lambda **kwargs: kwargs,
        postcondition_checker=lambda **kwargs: kwargs,
        comparison_adapter=lambda **kwargs: kwargs,
        capability_constraints={"fixture": True},
        evaluation_policy=policy,
    )


def _fact(
    fact_key: str = "instance:Marker",
    value: object = "A",
    *,
    source_kind: EvidenceSourceKind = EvidenceSourceKind.EXPLICIT_REQUEST,
    compatible: bool = True,
) -> SemanticFact:
    return SemanticFact(
        fact_key=fact_key,
        value=value,
        value_type="IfcLabel" if isinstance(value, str) else "IfcReal",
        unit=None if isinstance(value, str) else "mm",
        inherited=source_kind is EvidenceSourceKind.SURVIVING_TYPE,
        pset_path=(
            fact_key.removeprefix("pset:") if fact_key.startswith("pset:") else None
        ),
        entity_source="IfcWindow:window-01",
        source_kind=source_kind,
        source_ref=f"fixture/{source_kind.value}",
        provenance=("sha256:fixture", "IfcWindow#42"),
        compatible=compatible,
    )


def _actual(fact_key: str = "instance:Marker", value: object = "A") -> SemanticFact:
    return _fact(
        fact_key,
        value,
        source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
    )


def test_policy_records_are_immutable_and_versioned() -> None:
    policy = _policy()

    assert policy.policy_id == "fixture_add_component.l2"
    assert policy.version == "0.1"
    assert policy.semantic_facts[0].version == "0.1"
    with pytest.raises(FrozenInstanceError):
        policy.version = "0.2"  # type: ignore[misc]


def test_policy_rejects_duplicate_check_ids() -> None:
    with pytest.raises(PolicyContractError) as caught:
        _policy(facts=(_spec(), _spec(fact_pattern="instance:Other")))

    assert caught.value.code == "DUPLICATE_EVALUATION_CHECK_ID"


def test_policy_rejects_invalid_check_version() -> None:
    with pytest.raises(PolicyContractError) as caught:
        SemanticFactSpec(**{**_spec().__dict__, "version": "latest"})

    assert caught.value.code == "INVALID_EVALUATION_CHECK_VERSION"


def test_policy_rejects_invalid_policy_version_with_stable_code() -> None:
    with pytest.raises(PolicyContractError) as caught:
        OperationEvaluationPolicy(
            policy_id="fixture.l2",
            version="latest",
            operation_type="fixture",
            semantic_facts=(_spec(),),
        )

    assert caught.value.code == "INVALID_EVALUATION_POLICY_VERSION"


def test_registry_reports_missing_policy_only_when_evaluation_is_required() -> None:
    registry = OperationRegistry()
    registry.register(_definition("legacy_fixture", policy=None))

    with pytest.raises(OperationRegistryError) as caught:
        registry.require_evaluation_policy("legacy_fixture")

    assert caught.value.code == "MISSING_EVALUATION_POLICY"


def test_registry_rejects_duplicate_policy_ids_across_operations() -> None:
    registry = OperationRegistry()
    registry.register(_definition("fixture_a", policy=_policy("fixture_a", policy_id="shared.l2")))

    with pytest.raises(OperationRegistryError) as caught:
        registry.register(
            _definition("fixture_b", policy=_policy("fixture_b", policy_id="shared.l2"))
        )

    assert caught.value.code == "DUPLICATE_EVALUATION_POLICY_ID"


def test_window_and_future_operation_dispatch_through_one_registry_seam() -> None:
    registry = OperationRegistry()
    registry.register(window_operation_definition())
    fixture_policy = _policy()
    registry.register(_definition("fixture_add_component", policy=fixture_policy))

    fixture_result = registry.evaluate_semantics(
        "fixture_add_component",
        expected_facts=(_fact(),),
        repaired_facts=(_actual(),),
    )
    window_policy = registry.require_evaluation_policy(
        "add_window_with_opening_to_wall"
    )

    assert fixture_result[0].status is EvaluationStatus.PASSED
    assert window_policy.operation_type == "add_window_with_opening_to_wall"
    assert registry.operation_types == (
        "add_window_with_opening_to_wall",
        "fixture_add_component",
    )


def test_window_policy_declares_required_and_conditional_semantic_contract() -> None:
    policy = window_operation_definition().evaluation_policy
    assert policy is not None
    specs = {spec.fact_pattern: spec for spec in policy.semantic_facts}

    for required_pattern in (
        "relationship:type",
        "relationship:host",
        "relationship:storey",
        "pset:Pset_WindowCommon.IsExternal",
        "attribute:OverallWidth",
        "attribute:OverallHeight",
        "quantity:Qto_WindowBaseQuantities.*",
    ):
        assert specs[required_pattern].applicability is SemanticApplicability.REQUIRED
    for conditional_pattern in (
        "material:*",
        "classification:*",
        "pset:*",
        "quantity:*",
        "label:Name",
        "label:Tag",
        "instance:*",
    ):
        assert (
            specs[conditional_pattern].applicability
            is SemanticApplicability.CONDITIONAL
        )


def test_explicit_request_wins_fixed_source_precedence() -> None:
    facts = (
        _fact(value="policy", source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY),
        _fact(value="prototype", source_kind=EvidenceSourceKind.APPROVED_PROTOTYPE),
        _fact(value="type", source_kind=EvidenceSourceKind.SURVIVING_TYPE),
        _fact(value="target", source_kind=EvidenceSourceKind.SURVIVING_TARGET),
        _fact(value="original", source_kind=EvidenceSourceKind.PRIVATE_ORIGINAL),
        _fact(value="request", source_kind=EvidenceSourceKind.EXPLICIT_REQUEST),
    )

    result = evaluate_operation_semantics(
        _policy(), expected_facts=facts, repaired_facts=(_actual(value="request"),)
    )[0]

    assert result.status is EvaluationStatus.PASSED
    assert result.evidence[0].source_kind == "explicit_request"
    assert result.evidence[0].expected_value["value"] == "request"


@pytest.mark.parametrize("source", ["nearby_element", "name_match", "llm_guess", "model_knowledge"])
def test_prohibited_inference_sources_cannot_enter_evidence(source: str) -> None:
    with pytest.raises(SemanticFactError) as caught:
        SemanticFact(**{**_fact().__dict__, "source_kind": source})  # type: ignore[arg-type]

    assert caught.value.code == "UNAUTHORIZED_EVIDENCE_SOURCE"


def test_incompatible_prototype_cannot_activate_conditional_fact() -> None:
    result = evaluate_operation_semantics(
        _policy(),
        expected_facts=(
            _fact(
                value="prototype-value",
                source_kind=EvidenceSourceKind.APPROVED_PROTOTYPE,
                compatible=False,
            ),
        ),
        repaired_facts=(),
    )[0]

    assert result.status is EvaluationStatus.NOT_REQUIRED
    assert result.mandatory is False
    assert result.evidence[0].expected_state == "unavailable"
    assert "approved_prototype:incompatible" in result.evidence[0].provenance


CONDITIONAL_FACTS = (
    ("material:primary", "Aluminium", "IfcLabel"),
    ("classification:Uniclass", "Ss_25_30_95", "IfcIdentifier"),
    ("pset:Pset_WindowCommon.FireRating", "EI30", "IfcLabel"),
    ("quantity:Qto_WindowBaseQuantities.Area", 2.4, "IfcAreaMeasure"),
    ("label:Name", "W-01", "IfcLabel"),
    ("label:Tag", "WIN-01", "IfcIdentifier"),
    ("instance:AcousticRating", 42.0, "IfcSoundPowerMeasure"),
)


@pytest.mark.parametrize(("fact_key", "value", "value_type"), CONDITIONAL_FACTS)
def test_authorized_semantic_fact_equivalent_repair_passes(
    fact_key: str, value: object, value_type: str
) -> None:
    spec = _spec(fact_key, check_id="fixture.conditional")
    expected = SemanticFact(
        **{
            **_fact(fact_key, value).__dict__,
            "value_type": value_type,
            "unit": "m2" if "Area" in fact_key else None,
        }
    )
    repaired = SemanticFact(
        **{
            **_actual(fact_key, value).__dict__,
            "value_type": value_type,
            "unit": "m2" if "Area" in fact_key else None,
        }
    )

    result = evaluate_operation_semantics(
        _policy(facts=(spec,)), expected_facts=(expected,), repaired_facts=(repaired,)
    )[0]

    assert result.status is EvaluationStatus.PASSED
    assert result.mandatory is True
    evidence = result.evidence[0]
    assert evidence.expected_value == {
        "value": value,
        "value_type": value_type,
        "unit": "m2" if "Area" in fact_key else None,
        "inherited": False,
        "pset_path": fact_key.removeprefix("pset:") if fact_key.startswith("pset:") else None,
        "entity_source": "IfcWindow:window-01",
    }
    assert evidence.provenance[:2] == ("sha256:fixture", "IfcWindow#42")


@pytest.mark.parametrize(("fact_key", "value", "value_type"), CONDITIONAL_FACTS)
@pytest.mark.parametrize("actual", [None, "mismatch"])
def test_authorized_semantic_fact_missing_or_mismatched_repair_fails(
    fact_key: str, value: object, value_type: str, actual: object | None
) -> None:
    expected = SemanticFact(
        **{**_fact(fact_key, value).__dict__, "value_type": value_type}
    )
    repaired = (
        ()
        if actual is None
        else (
            SemanticFact(
                **{**_actual(fact_key, actual).__dict__, "value_type": value_type}
            ),
        )
    )

    result = evaluate_operation_semantics(
        _policy(facts=(_spec(fact_key),)),
        expected_facts=(expected,),
        repaired_facts=repaired,
    )[0]

    assert result.status is EvaluationStatus.FAILED
    assert result.mandatory is True
    assert result.evidence[0].actual_state == (
        "unavailable" if actual is None else "available"
    )


@pytest.mark.parametrize(("fact_key", "value", "value_type"), CONDITIONAL_FACTS)
def test_conditional_semantic_fact_without_authority_is_not_required(
    fact_key: str, value: object, value_type: str
) -> None:
    del value, value_type
    result = evaluate_operation_semantics(
        _policy(facts=(_spec(fact_key),)), expected_facts=(), repaired_facts=()
    )[0]

    assert result.status is EvaluationStatus.NOT_REQUIRED
    assert result.mandatory is False
    assert result.evidence[0].expected_state == "unavailable"
    assert result.evidence[0].actual_state == "not_applicable"
    assert result.evidence[0].source_kind == "source_search"


def test_required_fact_without_reliable_expected_value_is_not_evaluable() -> None:
    result = evaluate_operation_semantics(
        _policy(
            facts=(
                _spec(
                    "relationship:type",
                    check_id="fixture.type",
                    applicability=SemanticApplicability.REQUIRED,
                ),
            )
        ),
        expected_facts=(),
        repaired_facts=(_actual("relationship:type", "type-01"),),
    )[0]

    assert result.status is EvaluationStatus.NOT_EVALUABLE
    assert result.mandatory is True
    assert result.evidence[0].expected_state == "unavailable"
    assert "reliable expected evidence" in result.reason


def test_phase7_property_fact_conversion_preserves_typed_value_and_provenance() -> None:
    property_fact = PropertyFact(
        set_kind="pset",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value=True,
        value_type="IfcBoolean",
        unit=None,
        inherited=True,
        provenance="ifcopenshell.util.element.get_psets",
    )

    semantic = semantic_fact_from_property_fact(
        property_fact,
        source_kind=EvidenceSourceKind.SURVIVING_TYPE,
        source_ref="index/window-type-01",
        entity_source="IfcWindowType:type-01",
        provenance=("sha256:index",),
    )

    assert semantic.fact_key == "pset:Pset_WindowCommon.IsExternal"
    assert semantic.value is True
    assert semantic.value_type == "IfcBoolean"
    assert semantic.unit is None
    assert semantic.inherited is True
    assert semantic.pset_path == "Pset_WindowCommon.IsExternal"
    assert semantic.entity_source == "IfcWindowType:type-01"
    assert semantic.provenance == (
        "sha256:index",
        "ifcopenshell.util.element.get_psets",
    )


def test_phase7_record_and_future_family_share_the_generic_fact_conversion() -> None:
    record = ElementRecord(
        record_id="ifc:future-01",
        ifc_global_id="future-01",
        identity_reliable=True,
        ifc_class="IfcDoor",
        name="D-01",
        long_name=None,
        tag="DOOR-01",
        object_type=None,
        type_name="Door Type A",
        type_global_id="door-type-01",
        storey_name="Level 1",
        storey_global_id="storey-01",
        geometry_capability="bbox",
        properties=(
            PropertyFact(
                set_kind="quantity",
                set_name="Qto_DoorBaseQuantities",
                property_name="Height",
                value=2100.0,
                value_type="IfcLengthMeasure",
                unit="mm",
                inherited=False,
                provenance="ifcopenshell.util.element.get_psets",
            ),
        ),
    )

    facts = semantic_facts_from_element_record(
        record,
        source_kind=EvidenceSourceKind.SURVIVING_TARGET,
        source_ref="index/future-01",
    )

    assert {fact.fact_key for fact in facts} == {
        "label:Name",
        "label:Tag",
        "quantity:Qto_DoorBaseQuantities.Height",
        "relationship:storey",
        "relationship:type",
    }
    quantity = next(fact for fact in facts if fact.fact_key.startswith("quantity:"))
    assert quantity.value == 2100.0
    assert quantity.value_type == "IfcLengthMeasure"
    assert quantity.unit == "mm"
    assert quantity.provenance == (
        "index:ifc:future-01",
        "ifcopenshell.util.element.get_psets",
    )


def test_repaired_ifc_extraction_uses_inheritance_aware_official_utilities() -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    window = model.create_entity(
        "IfcWindow",
        GlobalId="0000000000000000000001",
        Name="W-01",
        OverallHeight=1200.0,
        OverallWidth=1000.0,
    )
    material = model.create_entity("IfcMaterial", Name="Aluminium")
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId="0000000000000000000002",
        RelatedObjects=[window],
        RelatingMaterial=material,
    )
    classification = model.create_entity(
        "IfcClassification", Source="NBS", Edition="2025", Name="Uniclass"
    )
    reference = model.create_entity(
        "IfcClassificationReference",
        ItemReference="Ss_25_30_95",
        Name="Windows",
        ReferencedSource=classification,
    )
    model.create_entity(
        "IfcRelAssociatesClassification",
        GlobalId="0000000000000000000003",
        RelatedObjects=[window],
        RelatingClassification=reference,
    )
    property_value = model.create_entity("IfcBoolean", True)
    prop = model.create_entity(
        "IfcPropertySingleValue", Name="IsExternal", NominalValue=property_value
    )
    pset = model.create_entity(
        "IfcPropertySet",
        GlobalId="0000000000000000000004",
        Name="Pset_WindowCommon",
        HasProperties=[prop],
    )
    model.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId="0000000000000000000005",
        RelatedObjects=[window],
        RelatingPropertyDefinition=pset,
    )

    facts = extract_ifc_semantic_facts(
        window,
        policy=window_operation_definition().evaluation_policy,
        source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
        source_ref="repaired.ifc",
        provenance=("sha256:repaired",),
    )

    by_key = {fact.fact_key: fact for fact in facts}
    assert by_key["pset:Pset_WindowCommon.IsExternal"].value is True
    assert by_key["pset:Pset_WindowCommon.IsExternal"].inherited is False
    assert by_key["material:Aluminium"].value == "Aluminium"
    assert by_key["classification:Uniclass:Ss_25_30_95"].value == {
        "system": "Uniclass",
        "identification": "Ss_25_30_95",
        "name": "Windows",
    }
