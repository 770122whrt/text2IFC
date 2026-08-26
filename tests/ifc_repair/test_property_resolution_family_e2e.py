from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import ifcopenshell
import pytest

import text2ifc_knowledge
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.repair_intent import (
    RepairIntent,
    fingerprint_text,
    hash_request,
)
from text2ifc_knowledge.property_runtime import create_property_runtime
from text2ifc_knowledge.property_search import (
    InMemoryVectorIndex,
    PropertyKnowledgeResolver,
    build_standard_property_records,
    default_standard_corpus_fingerprint,
    load_reviewed_aliases,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ID = "0000000000000000000001"


def test_active_property_authority_does_not_export_legacy_alias_entrypoints() -> None:
    assert not hasattr(text2ifc_knowledge, "create_default_property_resolver")
    assert not hasattr(text2ifc_knowledge, "load_reviewed_aliases")
    assert not hasattr(text2ifc_knowledge, "PropertyAlias")
    assert not hasattr(text2ifc_knowledge, "PropertyKnowledgeResolver")


def test_repair_api_rejects_alias_bearing_property_resolver(tmp_path: Path) -> None:
    registry = load_ifc2x3_registry(PROJECT_ROOT)
    resolver = PropertyKnowledgeResolver(
        registry=registry,
        records=build_standard_property_records(
            registry,
            corpus_fingerprint=default_standard_corpus_fingerprint(),
        ),
        aliases=load_reviewed_aliases(),
    )

    with pytest.raises(ValueError, match="ACTIVE_REVIEWED_ALIASES_FORBIDDEN"):
        RepairAPI(
            tmp_path / "output",
            provider=object(),
            property_knowledge_resolver=resolver,
        )


def test_active_phase12_entrypoints_do_not_reference_legacy_alias_factory() -> None:
    active_paths = (
        PROJECT_ROOT / "scripts/ifc_repair/run_phase12_live_uat.py",
        PROJECT_ROOT / "scripts/ifc_repair/run_phase12_public_structural_repair.py",
        PROJECT_ROOT / "scripts/ifc_repair/validate_success_cases.py",
    )

    for path in active_paths:
        source = path.read_text(encoding="utf-8")
        assert "create_default_property_resolver" not in source, path
        assert "load_reviewed_aliases" not in source, path


class _FamilyEmbedding:
    model_id = "fixture-family-semantic"
    model_version = "fixture-family-semantic/0.1"
    model_fingerprint = "offline-test-only"

    def embed(self, texts):
        vectors = []
        for text in texts:
            normalized = text.casefold().replace("_", "")
            vectors.append(
                [
                    float(
                        "isexternal" in normalized
                        or "external" in normalized
                        or "外窗" in normalized
                        or "外墙" in normalized
                    ),
                    float(
                        "selfclosing" in normalized
                        or "自动闭合" in normalized
                    ),
                    float(
                        "loadbearing" in normalized
                        or "load bearing" in normalized
                        or "承重" in normalized
                    ),
                ]
            )
        return vectors


class _Provider:
    def __init__(self, selected_candidate_id: str) -> None:
        self.selected_candidate_id = selected_candidate_id
        self.calls: list[dict[str, Any]] = []

    def generate_candidate(self, **kwargs: Any) -> ProviderOutput:
        self.calls.append(kwargs)
        assert kwargs["state"]["provider_call_ordinal"] == "property_resolution"
        assert self.selected_candidate_id in kwargs["prompt"]
        return ProviderOutput(
            text=json.dumps(
                {
                    "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                    "decision": "confirmed",
                    "selected_candidate_id": self.selected_candidate_id,
                    "conflicting_candidate_ids": [],
                    "clarification_question": None,
                },
                ensure_ascii=False,
            ),
            metadata={"provider": "fixture", "model": "family-reranker"},
        )


def _runtime():
    registry = load_ifc2x3_registry(PROJECT_ROOT)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=default_standard_corpus_fingerprint(),
    )
    policy = json.loads(
        (
            PROJECT_ROOT
            / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
        ).read_text(encoding="utf-8")
    )
    return create_property_runtime(
        registry=registry,
        standard_records=records,
        project_records=(),
        vector_index=InMemoryVectorIndex(_FamilyEmbedding()),
        policy_document=policy,
        corpus_version="ifc2x3-property-records/0.2",
        embedding_model_version="fixture-family-semantic/0.1",
        document_renderer_version="property-record-text/0.1",
        collection_version="ifc2x3-property-vector/0.2",
        runtime_mode="offline_test",
    )


def _source(path: Path, ifc_class: str) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 12.1")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="Property family fixture",
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
        ifc_class,
        GlobalId=GLOBAL_ID,
        OwnerHistory=history,
        Name=f"Target {ifc_class}",
    )
    model.write(str(path))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("family", "ifc_class", "phrase", "canonical_path"),
    (
        ("window", "IfcWindow", "外窗", "Pset_WindowCommon.IsExternal"),
        ("door", "IfcDoor", "门需要自动闭合", "Pset_DoorCommon.SelfClosing"),
        ("wall", "IfcWall", "建筑外墙属性", "Pset_WallCommon.IsExternal"),
        ("beam", "IfcBeam", "load bearing", "Pset_BeamCommon.LoadBearing"),
        ("column", "IfcColumn", "load bearing", "Pset_ColumnCommon.LoadBearing"),
    ),
)
def test_existing_occurrence_property_family_runs_public_api_stage_1_5_chain(
    tmp_path: Path,
    family: str,
    ifc_class: str,
    phrase: str,
    canonical_path: str,
) -> None:
    source = tmp_path / f"{family}.ifc"
    _source(source, ifc_class)
    source_before = source.read_bytes()
    request = f"Set {phrase} to true on the selected {family}."
    provider = _Provider(f"candidate:1:ifc2x3:{canonical_path}")
    registry = load_ifc2x3_registry(PROJECT_ROOT)
    source_record = {
        "source_kind": "user_request",
        "reference": "request:/text/property-1",
        "excerpt": request,
    }
    captured: dict[str, Any] = {}

    def intent_stage(**kwargs: Any) -> dict[str, Any]:
        intent = RepairIntent.from_dict(
            {
                "schema_version": "text2ifc/ifc-repair-intent/0.8",
                "request_id": kwargs["request_id"],
                "source_request_hash": hash_request(kwargs["repair_request"]),
                "model_fingerprint": fingerprint_text("family-e2e"),
                "prompt_fingerprint": "sha256:" + "1" * 64,
                "operations": [
                    {
                        "operation_id": f"{family}-property-1",
                        "operation_type": "set_occurrence_properties",
                        "routing_intent": {
                            "component_family": family,
                            "action": "set_properties",
                            "operation_profile": "occurrence.set-properties",
                            "source": source_record,
                        },
                        "target_query": {
                            "schema_version": "text2ifc/ifc-target-query/0.1",
                            "allowed_ifc_classes": [ifc_class],
                            "global_id": GLOBAL_ID,
                        },
                        "parameters": {},
                        "attribute_intents": [],
                        "property_intents": [
                            {
                                "intent_kind": "natural_language_property",
                                "property_phrase": phrase,
                                "raw_value": True,
                                "raw_unit": None,
                                "scope": "occurrence_direct",
                                "source": source_record,
                            }
                        ],
                        "semantic_bundle_refs": [],
                        "quantity_intents": [],
                        "occurrence_reuse_intent": None,
                        "prototype_intent": None,
                        "provenance": [source_record],
                    }
                ],
                "unsupported_requests": [],
                "semantic_bundles": [],
                "provenance": [source_record],
            },
            registry=kwargs["registry"],
        )
        return {
            "valid": True,
            "classification": "repair_intent",
            "intent": intent,
            "missing_parameters": [],
        }

    def changeset_stage(**kwargs: Any) -> dict[str, Any]:
        captured["operations"] = kwargs["resolved_operations"]
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

    def apply_stage(**kwargs: Any) -> dict[str, Any]:
        target = Path(kwargs["output_path"])
        shutil.copyfile(kwargs["damaged_ifc_path"], target)
        return {
            "valid": True,
            "published": True,
            "audit": {
                "valid": True,
                "operation_audits": [
                    {"operation_id": f"{family}-property-1", "valid": True}
                ],
            },
            "operations": [{"operation_id": f"{family}-property-1"}],
            "output": {"path": str(target), "sha256": _sha256(target)},
        }

    evidence = SimpleNamespace(
        expected_facts_by_operation={f"{family}-property-1": ()},
        applicability_by_operation={f"{family}-property-1": {}},
        conflicts=(),
    )
    api = RepairAPI(
        tmp_path / "output",
        provider=provider,
        intent_stage=intent_stage,
        changeset_stage=changeset_stage,
        property_knowledge_runtime=_runtime(),
        orchestrator_options={
            "apply_stage": apply_stage,
            "evaluation_stage": lambda _inputs: {
                "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
                "policy_version": "phase12.1.family-e2e",
                "status": "passed",
                "reason": "offline family fixture",
                "complete_repair_success": True,
                "successful_artifact_publishable": True,
                "diagnostic_artifact_retained": False,
                "application": {"check_id": "application.valid", "status": "passed", "reason": "fixture"},
                "preservation": {"check_id": "preservation.valid", "status": "passed", "reason": "fixture"},
                "operations": [],
            },
            "evidence_builder": lambda **_: evidence,
        },
    )

    result = api.start(source, request)

    assert result.status == "succeeded"
    assert len(provider.calls) == 1
    assert source.read_bytes() == source_before
    operations = captured["operations"]
    assert len(operations) == 1
    assert operations[0].operation_type == "set_occurrence_properties"
    assert operations[0].operation_type != "add_wall"
    fact = operations[0].authorized_semantics[0]
    assert f"{fact['set_name']}.{fact['property_name']}" == canonical_path
    assert fact["value"] is True
    assert fact["value_type"] == "IfcBoolean"
