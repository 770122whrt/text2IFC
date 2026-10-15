"""Frozen offline family for existing custom occurrence-property types.

The real E-pilot failure remains untouched. These public synthetic siblings cover
type preservation, explicit type requests, ambiguous facts, source ownership,
new-property defaults, incompatible values, and shared-Pset copy-on-write.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import ifcopenshell
import pytest

from scripts.ifc_repair.repair_comparison.ours_adapter import _draft
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.index_models import ElementRecord, IndexMetadata, PropertyFact
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import EXTRACTOR_VERSION
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.production_evidence import (
    ProductionEvidenceError,
    _authorized_property_fact,
)
from text2ifc_ifc_repair.property_intent import (
    ExactPropertyIntent,
    PropertyConfirmationPreview,
    PropertyResolutionStatus,
    authorize_custom_property,
    resolve_exact_property_intent,
)
from text2ifc_ifc_repair.repair_intent import (
    PublicProvenance,
    RepairIntent,
    fingerprint_text,
    hash_request,
)
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
from text2ifc_knowledge.registry import load_ifc2x3_registry
from text2ifc_ifc_repair.run_models import hash_json


TARGET_ID = "0000000000000000000001"
SIBLING_ID = "0000000000000000000002"


def _intent(value="replacement", requested_type=None):
    return ExactPropertyIntent(
        set_name="Asset Notes",
        property_name="Description",
        value=value,
        requested_value_type=requested_type,
        requested_unit=None,
        scope="occurrence_direct",
        source=PublicProvenance("user_request", "request:/text", "Keep the original property type."),
        intent_kind="exact_property",
    )


def _fact(value_type="IfcText", *, inherited=False, set_kind="pset", unit=None):
    return PropertyFact(
        set_kind, "Asset Notes", "Description", "old", value_type,
        unit, inherited, "public-source:direct" if not inherited else "public-source:type",
    )


def _resolve(intent, facts=()):
    return resolve_exact_property_intent(
        intent, target_ifc_class="IfcDoor", existing_facts=facts,
        registry=load_ifc2x3_registry(),
    )


@pytest.mark.parametrize("original_type", ["IfcText", "IfcLabel", "IfcIdentifier"])
def test_existing_custom_string_retains_original_type(original_type):
    result = _resolve(_intent(), (_fact(original_type),))

    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert result.value_type == original_type
    assert result.requires_confirmation
    assert "existing-fact:public-source:direct" in result.evidence


@pytest.mark.parametrize("requested_type", ["IfcText", "IfcLabel", "IfcIdentifier"])
def test_explicit_legal_type_request_remains_an_unconfirmed_custom_preview(requested_type):
    result = _resolve(_intent(requested_type=requested_type), (_fact(),))

    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert result.value_type == requested_type
    assert result.requires_confirmation


def test_conflicting_existing_direct_types_require_clarification():
    result = _resolve(_intent(), (_fact("IfcText"), _fact("IfcLabel")))

    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "CUSTOM_VALUE_TYPE_CONFLICT"
    assert result.value_type is None


@pytest.mark.parametrize("value,expected_type", [("new", "IfcLabel"), (True, "IfcBoolean"), (7, "IfcInteger")])
def test_new_custom_property_keeps_safe_primitive_default(value, expected_type):
    result = _resolve(_intent(value))

    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert result.value_type == expected_type


@pytest.mark.parametrize("fact", [_fact(inherited=True), _fact(set_kind="quantity")])
def test_non_occurrence_pset_facts_cannot_determine_custom_type(fact):
    result = _resolve(_intent(), (fact,))

    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert result.value_type == "IfcLabel"
    assert not any(item.startswith("existing-fact:") for item in result.evidence)


def test_direct_type_wins_over_inherited_fact_with_the_same_path():
    result = _resolve(_intent(), (_fact("IfcIdentifier"), _fact("IfcLabel", inherited=True)))

    assert result.value_type == "IfcIdentifier"
    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED


def test_incompatible_new_value_cannot_silently_replace_existing_numeric_type():
    result = _resolve(_intent("text"), (_fact("IfcInteger"),))

    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "PROPERTY_VALUE_TYPE_INCOMPATIBLE"
    assert result.value_type == "IfcInteger"


@pytest.mark.parametrize("value", [[], {}, math.inf])
def test_invalid_values_fail_before_custom_preview(value):
    result = _resolve(_intent(value), (_fact(),))

    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "PROPERTY_VALUE_INVALID"


def test_unknown_explicit_type_remains_rejected():
    result = _resolve(_intent(requested_type="IfcImaginaryType"), (_fact(),))

    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "CUSTOM_VALUE_TYPE_UNKNOWN"


def test_new_occurrence_does_not_reuse_host_property_type(tmp_path):
    registry = OperationRegistry()
    registry.register(OperationDefinition(
        operation_type="fixture_create_window", target_ifc_classes=("IfcWall",),
        parameter_schema={"type": "object", "additionalProperties": False},
        context_adapter=lambda **kwargs: kwargs, precondition_checker=lambda **kwargs: (),
        applicator=lambda **kwargs: kwargs, postcondition_checker=lambda **kwargs: (),
        comparison_adapter=lambda **kwargs: kwargs, capability_constraints={},
        editable_occurrence_ifc_class="IfcWindow",
    ))
    source_hash = "sha256:" + "a" * 64
    source = _intent().source.to_dict()
    request = RepairIntent.from_dict({
        "schema_version": "text2ifc/ifc-repair-intent/0.2", "request_id": "host-boundary",
        "source_request_hash": source_hash, "model_fingerprint": "sha256:" + "b" * 64,
        "prompt_fingerprint": "sha256:" + "c" * 64,
        "operations": [{
            "operation_id": "set-property", "operation_type": "fixture_create_window",
            "target_query": {
                "schema_version": "text2ifc/ifc-target-query/0.1",
                "allowed_ifc_classes": ["IfcWall"], "global_id": TARGET_ID,
            },
            "parameters": {}, "attribute_intents": [], "property_intents": [{
                "intent_kind": "pset_property", "set_name": "Asset Notes",
                "property_name": "Description", "value": "replacement",
                "requested_unit": None, "requested_value_type": None,
                "scope": "occurrence_direct", "source": source,
            }],
            "prototype_intent": None, "provenance": [source],
        }], "provenance": [source],
    }, registry=registry)
    metadata = IndexMetadata(source_hash, "IFC2X3", EXTRACTOR_VERSION, 1, "2026-10-10T00:00:00Z")
    database = tmp_path / "targets.sqlite"
    with SQLiteIndexRepository.create(database, metadata) as writer:
        writer.put_record(ElementRecord(
            record_id=f"ifc:{TARGET_ID}", ifc_global_id=TARGET_ID, identity_reliable=True,
            ifc_class="IfcWall", name="Host", long_name=None, tag=None, object_type=None,
            type_name=None, type_global_id=None, storey_name=None, storey_global_id=None,
            geometry_capability="straight_wall", geometry_summary={"orientation": "east"},
            facets={"editable_target": True}, provenance={"source": "public fixture"},
            properties=(_fact("IfcText"),),
        ))
        writer.publish()
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_repair_intent(
            request, repository, expected_source_sha256=source_hash, operation_registry=registry,
        )

    assert result.reason_code == "property_confirmation"
    assert result.property_preview["value_type"] == "IfcLabel"


def _confirmed_authority():
    preview = PropertyConfirmationPreview.create(
        _resolve(_intent(requested_type="IfcText")),
        operation_id="set-property", target_global_id=TARGET_ID,
        request_hash="sha256:" + "a" * 64, model_fingerprint="sha256:" + "b" * 64,
        source=_intent().source,
    )
    return authorize_custom_property(
        preview, answer_kind="confirm_property", preview_hash=preview.preview_hash,
        confirmation_ref="run:offline-property-family/clarify-004",
    ).to_dict()


def _rehash(authority, *, preview=False):
    if preview:
        fields = {
            key: authority[key] for key in (
                "operation_id", "target_global_id", "request_hash", "model_fingerprint",
                "set_name", "property_name", "value", "value_type", "unit", "source",
            )
        }
        fields["scope"] = authority["ownership"]
        authority["confirmation_hash"] = hash_json(fields)
    authority["property_hash"] = hash_json({key: value for key, value in authority.items() if key != "property_hash"})
    return authority


def _production_fact(authority):
    return _authorized_property_fact(
        authority, operation_id="set-property",
        operation_intent=SimpleNamespace(
            property_intents=(_intent(),), target_query=SimpleNamespace(allowed_ifc_classes=("IfcDoor",)),
        ),
        resolved_operation=SimpleNamespace(target_global_id=TARGET_ID),
        request_hash="sha256:" + "a" * 64, model_fingerprint="sha256:" + "b" * 64,
    )


@pytest.mark.parametrize("field,value,code", [
    ("confirmation_ref", None, "AUTHORIZED_PROPERTY_CONFIRMATION_REQUIRED"),
    ("confirmation_hash", None, "AUTHORIZED_PROPERTY_CONFIRMATION_REQUIRED"),
    ("confirmation_hash", "sha256:" + "c" * 64, "AUTHORIZED_PROPERTY_CONFIRMATION_HASH_MISMATCH"),
    ("classification", "custom_unconfirmed", "AUTHORIZED_PROPERTY_CLASSIFICATION_INVALID"),
])
def test_custom_authority_cannot_forge_confirmation_by_rehashing(field, value, code):
    authority = _confirmed_authority()
    authority[field] = value

    with pytest.raises(ProductionEvidenceError, match=code):
        _production_fact(_rehash(authority))


def test_custom_property_cannot_impersonate_standard_authority():
    authority = _confirmed_authority()
    authority.update(classification="standard", confirmation_ref=None, confirmation_hash=None)

    with pytest.raises(ProductionEvidenceError, match="AUTHORIZED_PROPERTY_CLASSIFICATION_MISMATCH"):
        _production_fact(_rehash(authority))


@pytest.mark.parametrize("field,value,code", [
    ("target_global_id", SIBLING_ID, "AUTHORIZED_PROPERTY_BINDING_MISMATCH"),
    ("request_hash", "sha256:" + "d" * 64, "AUTHORIZED_PROPERTY_BINDING_MISMATCH"),
    ("model_fingerprint", "sha256:" + "e" * 64, "AUTHORIZED_PROPERTY_BINDING_MISMATCH"),
    ("source", PublicProvenance("user_request", "request:/other", "different claim").to_dict(), "AUTHORIZED_PROPERTY_CLAIM_MISMATCH"),
])
def test_rehashed_confirmed_authority_still_binds_source_request_model_and_target(field, value, code):
    authority = _confirmed_authority()
    authority[field] = value

    with pytest.raises(ProductionEvidenceError, match=code):
        _production_fact(_rehash(authority, preview=True))


def _custom_operation(authority):
    fact = _production_fact(authority)
    return {
        "operation_id": "set-property", "operation_type": "set_occurrence_properties",
        "target": {"element_global_id": TARGET_ID}, "parameters": {},
        "semantic_assignments": [{
            "operation_id": "set-property", "fact_key": fact.fact_key,
            "source_fact_key": "pset:Asset Notes.Description", "value": fact.value,
            "value_type": fact.value_type, "unit": fact.unit,
            "ownership": "occurrence_direct", "applicability": "required",
            "source_kind": "explicit_request", "source_ref": fact.source_ref,
            "provenance": list(fact.provenance), "authoring_action": "set_occurrence_pset",
        }],
    }


def test_confirmed_custom_assignment_reaches_occurrence_preconditions(tmp_path):
    source = tmp_path / "source.ifc"
    _source(source, "IfcDoor", "Asset Notes", "Description", "IfcText", False)
    result = create_default_registry().dispatch(
        "precondition_checker", _custom_operation(_confirmed_authority()),
        model=ifcopenshell.open(str(source)),
    )

    assert result["issues"] == []


@pytest.mark.parametrize("field,value", [
    ("source_ref", "request:/other"), ("value", "forged"), ("value_type", "IfcLabel"),
    ("source_fact_key", "pset:Other.Value"), ("operation_id", "another-operation"),
    ("provenance", ["classification:custom_confirmed", "confirmation:made-up"]),
])
def test_custom_assignment_cannot_override_confirmed_authority(tmp_path, field, value):
    source = tmp_path / "source.ifc"
    _source(source, "IfcDoor", "Asset Notes", "Description", "IfcText", False)
    operation = _custom_operation(_confirmed_authority())
    operation["semantic_assignments"][0][field] = deepcopy(value)
    result = create_default_registry().dispatch(
        "precondition_checker", operation, model=ifcopenshell.open(str(source)),
    )

    assert result["issues"]


def _source(path: Path, ifc_class: str, set_name: str, property_name: str, value_type: str, shared: bool, *, value="old"):
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Public synthetic property family")
    application = model.create_entity(
        "IfcApplication", ApplicationDeveloper=organization, Version="1",
        ApplicationFullName="Offline property test", ApplicationIdentifier="text2ifc",
    )
    user = model.create_entity(
        "IfcPersonAndOrganization", ThePerson=model.create_entity("IfcPerson", FamilyName="Test"),
        TheOrganization=organization,
    )
    history = model.create_entity(
        "IfcOwnerHistory", OwningUser=user, OwningApplication=application,
        ChangeAction="ADDED", CreationDate=0,
    )
    targets = [model.create_entity(ifc_class, GlobalId=TARGET_ID, OwnerHistory=history, Name="Target")]
    if shared:
        targets.append(model.create_entity(ifc_class, GlobalId=SIBLING_ID, OwnerHistory=history, Name="Sibling"))
    pset = model.create_entity(
        "IfcPropertySet", GlobalId=ifcopenshell.guid.new(), OwnerHistory=history, Name=set_name,
        HasProperties=[model.create_entity(
            "IfcPropertySingleValue", Name=property_name,
            NominalValue=model.create_entity(value_type, value),
        )],
    )
    model.create_entity(
        "IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
        RelatedObjects=targets, RelatingPropertyDefinition=pset,
    )
    model.write(str(path))


class _DraftProvider:
    """Keyless Stage 2 fixture; production binding, apply and evaluation remain real."""

    def __init__(self):
        self.calls = []

    def generate_candidate(self, **kwargs):
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(_draft(kwargs["prompt"], kwargs["schema"])),
            metadata={"provider": "fixture", "model": "offline-property-draft", "evidence_class": "deterministic_replay"},
        )


def _api(root: Path, ifc_class: str, set_name: str, property_name: str, provider, *, value="replacement", unit=None, requested_type=None):
    def intent_stage(**kwargs):
        source = {
            "source_kind": "user_request", "reference": "request:/text",
            "excerpt": kwargs["repair_request"],
        }
        intent = RepairIntent.from_dict({
            "schema_version": "text2ifc/ifc-repair-intent/0.8",
            "request_id": kwargs["request_id"],
            "source_request_hash": hash_request(kwargs["repair_request"]),
            "model_fingerprint": fingerprint_text("offline-type-preservation"),
            "prompt_fingerprint": "sha256:" + "1" * 64,
            "operations": [{
                "operation_id": "set-property", "operation_type": "set_occurrence_properties",
                "routing_intent": {
                    "component_family": "occurrence", "action": "set_properties",
                    "operation_profile": "occurrence.set-properties", "source": source,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": [ifc_class], "global_id": TARGET_ID,
                },
                "parameters": {}, "attribute_intents": [],
                "property_intents": [{
                    "intent_kind": "exact_property", "set_name": set_name,
                    "property_name": property_name, "raw_value": value,
                    "raw_unit": unit, "requested_value_type": requested_type,
                    "scope": "occurrence_direct", "source": source,
                }],
                "semantic_bundle_refs": [], "quantity_intents": [],
                "occurrence_reuse_intent": None, "prototype_intent": None,
                "provenance": [source],
            }],
            "unsupported_requests": [], "semantic_bundles": [], "provenance": [source],
        }, registry=kwargs["registry"])
        return {"valid": True, "classification": "repair_intent", "intent": intent, "missing_parameters": []}

    return RepairAPI(root, provider=provider, intent_stage=intent_stage)


def _nominal(model, target_id, set_name, property_name):
    target = model.by_guid(target_id)
    pset = next(
        rel.RelatingPropertyDefinition for rel in target.IsDefinedBy
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.Name == set_name
    )
    prop = next(prop for prop in pset.HasProperties if prop.Name == property_name)
    return prop.NominalValue.is_a(), prop.NominalValue.wrappedValue


@pytest.mark.parametrize("ifc_class,set_name,property_name,value_type,shared", [
    ("IfcDoor", "Asset Notes", "Description", "IfcText", True),
    ("IfcBeam", "Maintenance", "Inspection Code", "IfcIdentifier", False),
    ("IfcWindow", "Operations", "Display Value", "IfcLabel", False),
])
def test_public_api_preserves_existing_type_after_hash_bound_confirmation(
    tmp_path, ifc_class, set_name, property_name, value_type, shared,
):
    source = tmp_path / "source.ifc"
    _source(source, ifc_class, set_name, property_name, value_type, shared)
    before = source.read_bytes()
    provider = _DraftProvider()
    api = _api(tmp_path / "output", ifc_class, set_name, property_name, provider)
    result = api.start(source, f"Set {set_name}.{property_name} to replacement; keep the original property type.")

    assert result.status == "clarification_required", result.to_dict()
    assert result.reason_code == "property_confirmation"
    question = result.clarification
    assert question is not None
    preview = question.property_preview
    assert preview["value_type"] == value_type
    assert preview["value"] == "replacement"
    assert not result.successful_artifact_publishable
    assert provider.calls == []
    assert source.read_bytes() == before
    assert _nominal(ifcopenshell.open(str(source)), TARGET_ID, set_name, property_name) == (value_type, "old")

    with pytest.raises(ValueError, match="CLARIFICATION_ANSWER_INVALID"):
        api.continue_with_answer(
            result.run_id, {"kind": "confirm_property", "preview_hash": "sha256:" + "0" * 64},
            clarification_id=question.clarification_id, expected_state_version=result.state_version,
        )
    assert api.read_result(result.run_id).state_version == result.state_version
    assert provider.calls == []

    confirmed = api.continue_with_answer(
        result.run_id, {"kind": "confirm_property", "preview_hash": preview["preview_hash"]},
        clarification_id=question.clarification_id, expected_state_version=result.state_version,
    )
    assert confirmed.status == "succeeded", confirmed.to_dict()
    assert confirmed.successful_artifact_publishable
    assert len(provider.calls) == 1
    repaired_path = api.store.runs_root / result.run_id / confirmed.artifacts["successful_ifc"]
    repaired = ifcopenshell.open(str(repaired_path))
    assert _nominal(repaired, TARGET_ID, set_name, property_name) == (value_type, "replacement")
    if shared:
        assert _nominal(repaired, SIBLING_ID, set_name, property_name) == (value_type, "old")
    assert source.read_bytes() == before
