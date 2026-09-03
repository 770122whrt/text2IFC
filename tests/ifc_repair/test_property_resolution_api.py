from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import ifcopenshell
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.repair_intent import RepairIntent, fingerprint_text, hash_request
from text2ifc_ifc_repair.run_models import RunStage, RunStoreError
from text2ifc_knowledge.property_runtime import create_property_runtime
from text2ifc_knowledge.property_search import (
    InMemoryVectorIndex,
    build_standard_property_records,
    default_standard_corpus_fingerprint,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BEAM_ID = "0000000000000000000001"


def test_repair_api_from_environment_shares_provider_and_property_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import text2ifc_agent.openai_compat as openai_compat
    import text2ifc_ifc_repair.api as api_module

    environment = {
        "DEEPSEEK_API_KEY": "not-used",
        "TEXT2IFC_PROPERTY_BGE_MODEL_PATH": "models/bge-m3",
        "TEXT2IFC_PROPERTY_QDRANT_PATH": "vectors/qdrant",
    }
    provider_config = object()
    provider = object()
    property_runtime = object()
    captured: dict[str, Any] = {}

    class CapturingRepairAPI(RepairAPI):
        def __init__(self, output_root: Path | str, **kwargs: Any) -> None:
            captured["output_root"] = output_root
            captured.update(kwargs)

    monkeypatch.setattr(
        openai_compat,
        "load_openai_compatible_runtime_config",
        lambda values: (
            provider_config
            if values == environment
            else pytest.fail("Provider received the wrong environment")
        ),
    )
    monkeypatch.setattr(
        openai_compat,
        "OpenAICompatibleLiveProvider",
        lambda *, config: (
            provider
            if config is provider_config
            else pytest.fail("Provider received the wrong config")
        ),
    )
    monkeypatch.setattr(
        api_module,
        "create_property_runtime_from_environment",
        lambda values: (
            property_runtime
            if values == environment
            else pytest.fail("Property runtime received the wrong environment")
        ),
    )

    result = CapturingRepairAPI.from_environment(tmp_path, environment)

    assert result is not None
    assert captured["output_root"] == tmp_path
    assert captured["provider"] is provider
    assert captured["property_knowledge_runtime"] is property_runtime


class _Embedding:
    model_id = "fixture-semantic"
    model_version = "fixture-semantic/0.1"
    model_fingerprint = "offline-test-only"

    def embed(self, texts):
        vectors = []
        for text in texts:
            normalized = text.casefold().replace("_", "")
            if "unmatched property" in normalized:
                vectors.append([0.0, 0.0])
            elif "load" in normalized:
                vectors.append([1.0, 0.0])
            elif "external" in normalized:
                vectors.append([0.9, 0.1])
            else:
                vectors.append([0.0, 1.0])
        return vectors


class _VectorIndex(InMemoryVectorIndex):
    def __init__(self, events: list[str]) -> None:
        super().__init__(_Embedding())
        self.events = events

    def search_allowed(self, text: str, *, allowed_record_ids, limit: int):
        self.events.append("vector")
        return super().search_allowed(
            text,
            allowed_record_ids=allowed_record_ids,
            limit=limit,
        )

    def release_transient_resources(self) -> None:
        self.events.append("property_runtime_released")


class _DecisionProvider:
    def __init__(self, events: list[str], decisions: list[dict[str, Any]]) -> None:
        self.events = events
        self.decisions = list(decisions)
        self.calls: list[dict[str, Any]] = []

    def generate_candidate(self, **kwargs: Any) -> ProviderOutput:
        self.events.append("property_resolution")
        self.calls.append(kwargs)
        if not self.decisions:
            raise AssertionError("unexpected Property Resolution call")
        return ProviderOutput(
            text=json.dumps(self.decisions.pop(0), ensure_ascii=False),
            metadata={"provider": "fixture", "model": "property-resolution"},
        )


def _policy() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/property-resolution-policy/0.2",
        "policy_id": "ifc2x3.single-value.vector-reranker",
        "version": "0.2",
        "max_candidates": 5,
        "max_attempts": 2,
        "vector_required": True,
        "minimum_retrieval_score": 0.5,
        "alias_authority": False,
        "vector_top1_authority": False,
        "vector_margin_authority": False,
        "standard_selection": "stage_1_5_required",
        "project_or_custom": "explicit_confirmation_required",
        "explicit_canonical": "exact_path_bypass",
        "supported_template": "TypePropertySingleValue",
        "supported_scope": "occurrence_direct",
    }


def _runtime(events: list[str]):
    registry = load_ifc2x3_registry(PROJECT_ROOT)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=default_standard_corpus_fingerprint(),
    )
    return create_property_runtime(
        registry=registry,
        standard_records=records,
        project_records=(),
        vector_index=_VectorIndex(events),
        policy_document=_policy(),
        corpus_version="ifc2x3-property-records/0.2",
        embedding_model_version="fixture-semantic/0.1",
        document_renderer_version="property-record-text/0.1",
        collection_version="ifc2x3-property-vector/0.2",
        runtime_mode="offline_test",
    )


def _source(path: Path) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 12.1")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="Property Resolution API fixture",
        ApplicationIdentifier="text2ifc",
    )
    person = model.create_entity("IfcPerson", FamilyName="Tester")
    user = model.create_entity(
        "IfcPersonAndOrganization",
        ThePerson=person,
        TheOrganization=organization,
    )
    history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    model.create_entity(
        "IfcBeam",
        GlobalId=BEAM_ID,
        OwnerHistory=history,
        Name="Target beam",
    )
    model.write(str(path))


def _source_record() -> dict[str, str]:
    return {
        "source_kind": "user_request",
        "reference": "request:/text/property-1",
        "excerpt": "Set the selected beam load bearing to true.",
    }


def _intent(
    request_id: str,
    request: str,
    registry,
    *,
    kind: str,
    natural_phrase: str = "load bearing",
) -> RepairIntent:
    properties: list[dict[str, Any]]
    if kind == "natural":
        properties = [
            {
                "intent_kind": "natural_language_property",
                "property_phrase": natural_phrase,
                "raw_value": True,
                "raw_unit": None,
                "scope": "occurrence_direct",
                "source": _source_record(),
            }
        ]
    elif kind == "natural_multi":
        properties = [
            {
                "intent_kind": "natural_language_property",
                "property_phrase": "load bearing",
                "raw_value": True,
                "raw_unit": None,
                "scope": "occurrence_direct",
                "source": _source_record(),
            },
            {
                "intent_kind": "natural_language_property",
                "property_phrase": "external",
                "raw_value": True,
                "raw_unit": None,
                "scope": "occurrence_direct",
                "source": _source_record(),
            },
        ]
    elif kind == "exact":
        properties = [
            {
                "intent_kind": "exact_property",
                "set_name": "Pset_BeamCommon",
                "property_name": "LoadBearing",
                "raw_value": True,
                "raw_unit": None,
                "requested_value_type": "IfcBoolean",
                "scope": "occurrence_direct",
                "source": _source_record(),
            }
        ]
    else:
        properties = []
    return RepairIntent.from_dict(
        {
            "schema_version": "text2ifc/ifc-repair-intent/0.8",
            "request_id": request_id,
            "source_request_hash": hash_request(request),
            "model_fingerprint": fingerprint_text("offline-property-api"),
            "prompt_fingerprint": "sha256:" + "1" * 64,
            "operations": [
                {
                    "operation_id": "operation-1",
                    "operation_type": "set_occurrence_properties",
                    "routing_intent": {
                        "component_family": "beam",
                        "action": "set_properties",
                        "operation_profile": "occurrence.set-properties",
                        "source": _source_record(),
                    },
                    "target_query": {
                        "schema_version": "text2ifc/ifc-target-query/0.1",
                        "allowed_ifc_classes": ["IfcBeam"],
                        "global_id": BEAM_ID,
                    },
                    "parameters": {},
                    "attribute_intents": [],
                    "property_intents": properties,
                    "semantic_bundle_refs": [],
                    "quantity_intents": [],
                    "occurrence_reuse_intent": None,
                    "prototype_intent": None,
                    "provenance": [_source_record()],
                }
            ],
            "unsupported_requests": [],
            "semantic_bundles": [],
            "provenance": [_source_record()],
        },
        registry=registry,
    )


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _api(
    tmp_path: Path,
    *,
    kind: str,
    decisions: list[dict[str, Any]],
    derive_natural_phrase: bool = False,
    classification: str = "repair_intent",
    reason_code: str | None = None,
) -> tuple[RepairAPI, list[str], _DecisionProvider]:
    events: list[str] = []
    provider = _DecisionProvider(events, decisions)
    runtime = _runtime(events)

    def intent_stage(**kwargs):
        events.append("stage1")
        return {
            "valid": True,
            "classification": classification,
            "reason_code": reason_code,
            "intent": _intent(
                kwargs["request_id"],
                kwargs["repair_request"],
                kwargs["registry"],
                kind=kind,
                natural_phrase=(
                    "load bearing"
                    if derive_natural_phrase
                    and "load bearing" in kwargs["repair_request"].casefold()
                    else "unmatched property"
                    if derive_natural_phrase
                    else "load bearing"
                ),
            ),
            "missing_parameters": [],
        }

    def changeset_stage(**kwargs):
        events.append("stage2")
        return {
            "valid": True,
            "changeset": {
                "base_model_fingerprint": kwargs["base_model_fingerprint"],
                "operations": [
                    {
                        "operation_id": operation.operation_id,
                        "operation_type": operation.operation_type,
                    }
                    for operation in kwargs["resolved_operations"]
                ],
            },
        }

    def apply_stage(**kwargs):
        target = Path(kwargs["output_path"])
        shutil.copyfile(kwargs["damaged_ifc_path"], target)
        return {
            "valid": True,
            "published": True,
            "audit": {
                "valid": True,
                "operation_audits": [
                    {"operation_id": "operation-1", "valid": True}
                ],
            },
            "operations": [{"operation_id": "operation-1"}],
            "output": {
                "path": str(target),
                "sha256": _sha256(target).removeprefix("sha256:"),
            },
        }

    evidence = SimpleNamespace(
        expected_facts_by_operation={"operation-1": ()},
        applicability_by_operation={"operation-1": {}},
        conflicts=(),
    )
    api = RepairAPI(
        tmp_path / "output",
        provider=provider,
        intent_stage=intent_stage,
        changeset_stage=changeset_stage,
        property_knowledge_runtime=runtime,
        orchestrator_options={
            "apply_stage": apply_stage,
            "evaluation_stage": lambda _inputs: {
                "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
                "policy_version": "phase12.1.test",
                "status": "passed",
                "reason": "offline fixture",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "diagnostic_artifact_retained": False,
                "application": {
                    "check_id": "application.valid",
                    "status": "passed",
                    "reason": "fixture",
                },
                "preservation": {
                    "check_id": "preservation.valid",
                    "status": "passed",
                    "reason": "fixture",
                },
                "operations": [],
            },
            "evidence_builder": lambda **_: evidence,
        },
    )
    return api, events, provider


def _confirmed(candidate_id: str = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"):
    return {
        "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
        "decision": "confirmed",
        "selected_candidate_id": candidate_id,
        "conflicting_candidate_ids": [],
        "clarification_question": None,
    }


def test_public_natural_property_path_orders_all_three_provider_stages(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _source(source)
    before = source.read_bytes()
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[_confirmed()],
    )

    result = api.start(source, "Set the selected beam load bearing to true.")

    assert result.status == "succeeded"
    assert events[:5] == [
        "stage1",
        "vector",
        "property_resolution",
        "property_runtime_released",
        "stage2",
    ]
    assert len(provider.calls) == 1
    assert provider.calls[0]["state"]["provider_call_ordinal"] == (
        "property_resolution"
    )
    assert source.read_bytes() == before
    state = api.store.load(result.run_id)
    checkpoints = [
        item.stage_payload["property_resolution"]["checkpoint"]
        for item in state.transitions
        if "property_resolution" in item.stage_payload
    ]
    assert checkpoints == ["candidates", "decision", "admissibility"]


@pytest.mark.parametrize("kind", ["exact", "none"])
def test_explicit_canonical_and_no_property_bypass_stage_1_5(
    tmp_path: Path,
    kind: str,
) -> None:
    source = tmp_path / f"source-{kind}.ifc"
    _source(source)
    api, events, provider = _api(tmp_path / kind, kind=kind, decisions=[])

    result = api.start(source, f"Run {kind} property request.")

    assert result.status == "succeeded"
    assert events[:2] == ["stage1", "stage2"]
    assert "vector" not in events
    assert "property_resolution" not in events
    assert provider.calls == []


def test_property_clarification_resumes_stored_candidate_without_second_llm_call(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-clarify.ifc"
    _source(source)
    first_id = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    second_id = "candidate:2:ifc2x3:Pset_BeamCommon.IsExternal"
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[
            {
                "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                "decision": "clarification_required",
                "selected_candidate_id": None,
                "conflicting_candidate_ids": [first_id, second_id],
                "clarification_question": "Which Beam property did you mean?",
            }
        ],
    )

    pending = api.start(source, "Set the selected beam load bearing to true.")

    assert pending.status == "clarification_required"
    assert pending.clarification is not None
    assert pending.clarification.reason_code == "property_resolution"
    assert pending.clarification.answer_modes == (
        "select_candidate",
        "add_detail",
        "cancel",
    )
    assert [item.token for item in pending.clarification.candidates] == [
        first_id,
        second_id,
    ]
    assert events[:4] == [
        "stage1",
        "vector",
        "property_resolution",
        "property_runtime_released",
    ]
    assert "stage2" not in events

    with pytest.raises(RunStoreError):
        api.continue_with_answer(
            pending.run_id,
            {"kind": "select_candidate", "candidate_token": "candidate:other"},
            clarification_id=pending.clarification.clarification_id,
            expected_state_version=pending.state_version,
        )

    result = api.continue_with_answer(
        pending.run_id,
        {"kind": "select_candidate", "candidate_token": first_id},
        clarification_id=pending.clarification.clarification_id,
        expected_state_version=pending.state_version,
    )

    assert result.status == "succeeded"
    assert len(provider.calls) == 1
    assert events.count("vector") == 1
    assert events.count("property_resolution") == 1
    assert events.count("stage2") == 1


def test_property_clarification_with_candidates_accepts_add_detail(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-candidate-add-detail.ifc"
    _source(source)
    first_id = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    second_id = "candidate:2:ifc2x3:Pset_BeamCommon.IsExternal"
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[
            {
                "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                "decision": "clarification_required",
                "selected_candidate_id": None,
                "conflicting_candidate_ids": [first_id, second_id],
                "clarification_question": "Which property did you mean?",
            },
            _confirmed(first_id),
        ],
    )
    pending = api.start(source, "Set the selected property to true.")
    assert pending.clarification is not None

    result = api.continue_with_answer(
        pending.run_id,
        {"kind": "add_detail", "detail": "Use the load-bearing property."},
        clarification_id=pending.clarification.clarification_id,
        expected_state_version=pending.state_version,
    )

    assert result.status == "succeeded"
    assert len(provider.calls) == 2
    assert events.count("stage1") == 2
    assert events.count("property_resolution") == 2
    assert events.count("stage2") == 1


def test_unsupported_intent_is_state_bound_before_terminal_publication(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-unsupported-route.ifc"
    _source(source)
    source_before = source.read_bytes()
    api, events, _provider = _api(
        tmp_path,
        kind="none",
        decisions=[],
        classification="unsupported",
        reason_code="STRUCTURAL_ANALYSIS_UNSUPPORTED",
    )

    result = api.start(
        source,
        "Add a Beam and a structural analysis node atomically.",
    )

    assert result.status == "unsupported"
    assert result.reason_code == "STRUCTURAL_ANALYSIS_UNSUPPORTED"
    assert events == ["stage1"]
    assert source.read_bytes() == source_before
    state = api.store.load(result.run_id)
    intent_ready = [
        transition
        for transition in state.transitions
        if transition.to_stage is RunStage.INTENT_READY
    ]
    assert len(intent_ready) == 1
    assert set(intent_ready[0].stage_payload) >= {
        "intent",
        "api_context",
        "route",
    }
    assert intent_ready[0].stage_payload["route"] == {
        "classification": "unsupported",
        "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
    }
    assert set(result.artifacts) == {"manifest", "evaluation", "evidence"}


def test_property_resolution_unsupported_is_terminal_before_stage_2(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-unsupported.ifc"
    _source(source)
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[
            {
                "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                "decision": "unsupported",
                "selected_candidate_id": None,
                "conflicting_candidate_ids": [],
                "clarification_question": None,
            }
        ],
    )

    result = api.start(source, "Set an unsupported Beam property.")

    assert result.status == "unsupported"
    assert len(provider.calls) == 1
    assert "stage2" not in events
    assert result.successful_artifact_publishable is False


def test_property_add_detail_starts_a_new_claim_lineage_in_the_same_run(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-add-detail.ifc"
    _source(source)
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[_confirmed()],
        derive_natural_phrase=True,
    )
    pending = api.start(source, "Set the selected beam property.")
    assert pending.clarification is not None
    assert pending.clarification.answer_modes == ("add_detail", "cancel")

    result = api.continue_with_answer(
        pending.run_id,
        {"kind": "add_detail", "detail": "The property is load bearing."},
        clarification_id=pending.clarification.clarification_id,
        expected_state_version=pending.state_version,
    )

    assert result.status == "succeeded"
    assert len(provider.calls) == 1
    assert events.count("stage1") == 2
    assert events.count("vector") == 2
    assert events.count("property_resolution") == 1
    state = api.store.load(result.run_id)
    claim_ids = {
        item.stage_payload["property_resolution"]["claim_id"]
        for item in state.transitions
        if "property_resolution" in item.stage_payload
    }
    assert claim_ids == {
        "claim-001",
        f"claim-001-resume-{pending.state_version + 1:03d}",
    }


def test_property_selection_is_bound_to_one_claim_within_an_operation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-multi-claim.ifc"
    _source(source)
    load_id = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    external_id = "candidate:1:ifc2x3:Pset_BeamCommon.IsExternal"
    external_peer = "candidate:2:ifc2x3:Pset_BeamCommon.LoadBearing"
    api, events, provider = _api(
        tmp_path,
        kind="natural_multi",
        decisions=[
            _confirmed(load_id),
            {
                "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                "decision": "clarification_required",
                "selected_candidate_id": None,
                "conflicting_candidate_ids": [external_id, external_peer],
                "clarification_question": "Which second Beam property?",
            },
        ],
    )

    pending = api.start(source, "Set two properties on the selected beam.")
    assert pending.clarification is not None
    assert pending.clarification.operation_id == "operation-1"
    assert pending.clarification.claim_id == "claim-002"

    result = api.continue_with_answer(
        pending.run_id,
        {"kind": "select_candidate", "candidate_token": external_id},
        clarification_id=pending.clarification.clarification_id,
        expected_state_version=pending.state_version,
    )

    assert result.status == "succeeded"
    assert len(provider.calls) == 2
    assert events.count("vector") == 2
    assert events.count("property_resolution") == 2
    assert events.count("stage2") == 1
