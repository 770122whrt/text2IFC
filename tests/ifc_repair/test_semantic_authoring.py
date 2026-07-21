from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
import math

from jsonschema import Draft202012Validator
import pytest


def _api():
    try:
        import text2ifc_ifc_repair.semantic_authoring as api
    except ModuleNotFoundError:
        pytest.fail("semantic authoring manifest contract is not implemented")
    return api


def valid_manifest() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.1",
        "manifest_id": "semantic-manifest-window-001",
        "operation_id": "operation-window-001",
        "operation_type": "add_window_with_opening_to_wall",
        "base_model_fingerprint": "sha256:" + "a" * 64,
        "policy": {
            "policy_id": "window.add-with-opening.l2",
            "policy_version": "0.2",
        },
        "assignments": [
            {
                "operation_id": "operation-window-001",
                "fact_key": "pset:Pset_WindowCommon.IsExternal",
                "source_fact_key": "pset:Pset_WindowCommon.IsExternal",
                "value": True,
                "value_type": "IfcBoolean",
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "surviving_type",
                "source_ref": "type-index:window-style-001",
                "provenance": ["index:sha256:fixture", "IfcWindowStyle#42"],
                "authoring_action": "set_occurrence_pset",
            },
            {
                "operation_id": "operation-window-001",
                "fact_key": "attribute:OverallWidth",
                "source_fact_key": "request:/opening/width_mm",
                "value": 915.0,
                "value_type": "IfcPositiveLengthMeasure",
                "unit": "mm",
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_request",
                "source_ref": "request:/opening/width_mm",
                "provenance": ["request:sha256:fixture"],
                "authoring_action": "set_attribute",
            },
        ],
    }


def _error_code(payload: dict) -> str:
    api = _api()
    with pytest.raises(api.SemanticManifestError) as caught:
        api.parse_semantic_manifest(payload)
    return caught.value.code


def test_manifest_schema_is_exact_meta_valid_and_model_is_immutable() -> None:
    api = _api()
    schema = api.load_semantic_manifest_schema()
    Draft202012Validator.check_schema(schema)

    manifest = api.parse_semantic_manifest(valid_manifest())

    assert manifest.schema_version == api.SEMANTIC_MANIFEST_SCHEMA_VERSION
    assert manifest.policy_id == "window.add-with-opening.l2"
    assert manifest.policy_version == "0.2"
    assert [item.fact_key for item in manifest.assignments] == [
        "attribute:OverallWidth",
        "pset:Pset_WindowCommon.IsExternal",
    ]
    with pytest.raises(FrozenInstanceError):
        manifest.operation_id = "other"  # type: ignore[misc]


def test_manifest_rejects_wrong_schema_version_with_stable_code() -> None:
    payload = valid_manifest()
    payload["schema_version"] = "text2ifc/ifc-repair-semantic-manifest/9.9"

    assert _error_code(payload) == "SEMANTIC_MANIFEST_SCHEMA_VERSION_MISMATCH"


def test_manifest_rejects_missing_provenance_with_stable_code() -> None:
    payload = valid_manifest()
    payload["assignments"][0]["provenance"] = []

    assert _error_code(payload) == "MISSING_SEMANTIC_PROVENANCE"


@pytest.mark.parametrize("source_kind", ["private_original", "provider_output"])
def test_manifest_rejects_private_or_provider_sources(source_kind: str) -> None:
    payload = valid_manifest()
    payload["assignments"][0]["source_kind"] = source_kind

    assert _error_code(payload) == "UNAUTHORIZED_SEMANTIC_SOURCE"


def test_manifest_rejects_cross_operation_assignment() -> None:
    payload = valid_manifest()
    payload["assignments"][0]["operation_id"] = "operation-window-foreign"

    assert _error_code(payload) == "CROSS_OPERATION_SEMANTIC_ASSIGNMENT"


def test_manifest_rejects_conflicting_duplicate_fact_key() -> None:
    payload = valid_manifest()
    duplicate = deepcopy(payload["assignments"][0])
    duplicate["value"] = False
    payload["assignments"].append(duplicate)

    assert _error_code(payload) == "CONFLICTING_SEMANTIC_ASSIGNMENT"


def test_manifest_rejects_unsupported_fact_kind() -> None:
    payload = valid_manifest()
    payload["assignments"][0]["fact_key"] = "geometry:Representation"

    assert _error_code(payload) == "UNSUPPORTED_SEMANTIC_FACT_KIND"


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_manifest_rejects_non_finite_values(value: float) -> None:
    payload = valid_manifest()
    payload["assignments"][1]["value"] = value

    assert _error_code(payload) == "NON_FINITE_SEMANTIC_VALUE"


@pytest.mark.parametrize(
    "source_key",
    ["quantity:BaseQuantities.Width", "quantity:Qto_WindowBaseQuantities.Width"],
)
def test_window_quantity_aliases_share_one_role_and_keep_source_key(
    source_key: str,
) -> None:
    from text2ifc_ifc_repair.operations.window import canonicalize_window_fact_key

    normalized = canonicalize_window_fact_key(source_key)

    assert normalized.fact_key == "quantity:window-base.Width"
    assert normalized.source_fact_key == source_key


def test_window_quantity_alias_rejects_unrelated_qto() -> None:
    from text2ifc_ifc_repair.operations.window import canonicalize_window_fact_key

    with pytest.raises(ValueError, match="UNSUPPORTED_WINDOW_QUANTITY_ALIAS"):
        canonicalize_window_fact_key("quantity:Qto_DoorBaseQuantities.Width")


def test_explicit_request_extension_is_exact_not_a_global_wildcard() -> None:
    from text2ifc_ifc_repair.evaluation_policy import extend_policy_with_explicit_facts
    from text2ifc_ifc_repair.operations.window import window_operation_definition

    policy = extend_policy_with_explicit_facts(
        window_operation_definition().evaluation_policy,
        ("label:Name", "pset:CustomRequested.FireRating"),
    )
    extensions = {spec.fact_pattern: spec for spec in policy.semantic_facts}

    assert extensions["label:Name"].allowed_sources[0].value == "explicit_request"
    assert extensions["pset:CustomRequested.FireRating"].allowed_sources[0].value == "explicit_request"
    assert "pset:*" not in extensions
    assert "instance:*" not in extensions


def test_assignment_identity_and_sorting_are_operation_neutral() -> None:
    api = _api()
    manifest = api.parse_semantic_manifest(valid_manifest())

    identities = [api.semantic_assignment_identity(item) for item in manifest.assignments]

    assert identities == sorted(identities)
    assert identities[0] == (
        "operation-window-001",
        "attribute:OverallWidth",
        "occurrence_direct",
        "set_attribute",
    )


def test_future_operation_registers_its_own_fact_key_normalizer() -> None:
    from text2ifc_ifc_repair.evaluation_policy import (
        ComparisonRule,
        EvidenceSourceKind,
        FactKeyNormalization,
        OperationEvaluationPolicy,
        SemanticApplicability,
        SemanticFactSpec,
        normalize_policy_fact_key,
    )
    from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry

    def normalize_fixture(fact_key: str) -> FactKeyNormalization:
        canonical = fact_key.replace("quantity:FixtureBaseQuantities.", "quantity:fixture-base.")
        return FactKeyNormalization(canonical, fact_key)

    policy = OperationEvaluationPolicy(
        policy_id="fixture.add-component.l2",
        version="0.1",
        operation_type="fixture_add_component",
        semantic_facts=(
            SemanticFactSpec(
                check_id="fixture.height",
                version="0.1",
                fact_pattern="quantity:fixture-base.Height",
                applicability=SemanticApplicability.REQUIRED,
                allowed_sources=(EvidenceSourceKind.EXPLICIT_REQUEST,),
                comparison=ComparisonRule.TYPED_EQUIVALENCE,
            ),
        ),
        fact_key_normalizer=normalize_fixture,
    )
    registry = OperationRegistry()
    registry.register(
        OperationDefinition(
            operation_type="fixture_add_component",
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
    )

    registered = registry.require_evaluation_policy("fixture_add_component")
    normalized = normalize_policy_fact_key(
        registered, "quantity:FixtureBaseQuantities.Height"
    )

    assert normalized.fact_key == "quantity:fixture-base.Height"
    assert normalized.source_fact_key == "quantity:FixtureBaseQuantities.Height"
