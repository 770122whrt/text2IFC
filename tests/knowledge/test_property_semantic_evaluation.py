from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from text2ifc_agent.providers import ProviderOutput, ProviderOutputError
from text2ifc_knowledge.property_runtime import create_property_runtime
from text2ifc_knowledge.property_search import (
    InMemoryVectorIndex,
    build_standard_property_records,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


class _UniformEmbedding:
    """Non-semantic vector fixture: it deliberately encodes no expected answer."""

    model_id = "fixture-uniform"
    model_version = "fixture-uniform/0.1"
    model_fingerprint = "offline-nonsemantic"

    def embed(self, texts):
        return [[1.0] for _ in texts]


class _OfflineProviderDouble:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_candidate(self, **arguments):
        self.calls.append(arguments)
        serialized = json.dumps(arguments, ensure_ascii=False, sort_keys=True).casefold()
        for forbidden in (
            '"expected"',
            '"expected_route"',
            '"authorize"',
            "benchmark_gold",
            "private_gold",
            "mutation_recipe",
        ):
            assert forbidden not in serialized
        return ProviderOutput(
            text=json.dumps(
                {
                    "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                    "decision": "unsupported",
                    "selected_candidate_id": None,
                    "conflicting_candidate_ids": [],
                    "clarification_question": None,
                },
                sort_keys=True,
            ),
            metadata={
                "provider": "offline-provider-double",
                "model": "nonsemantic-fixture",
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                },
            },
        )


class _InfrastructureFailureProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_candidate(self, **_arguments):
        self.calls += 1
        raise ProviderOutputError(
            "offline infrastructure failure",
            details={"failure_class": "provider_connection_error"},
        )


def _runtime(project_root: Path):
    registry = load_ifc2x3_registry(project_root)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint="fixture-public-corpus/0.1",
    )
    policy = json.loads(
        (
            project_root
            / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
        ).read_text(encoding="utf-8")
    )
    return create_property_runtime(
        registry=registry,
        standard_records=records,
        project_records=(),
        vector_index=InMemoryVectorIndex(_UniformEmbedding()),
        policy_document=policy,
        corpus_version="ifc2x3-property-records/0.2",
        embedding_model_version="fixture-uniform/0.1",
        document_renderer_version="property-record-text/0.1",
        collection_version="ifc2x3-property-vector/0.2",
        runtime_mode="offline_test",
    )


def test_no_network_readiness_probe_uses_the_production_configured_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    environment = {
        "TEXT2IFC_PROPERTY_BGE_MODEL_PATH": "models/bge-m3",
        "TEXT2IFC_PROPERTY_QDRANT_PATH": "vectors/qdrant",
    }
    closed = False
    runtime = SimpleNamespace(
        health=SimpleNamespace(
            to_dict=lambda: {
                "status": "ready",
                "reason_code": None,
                "acceptance_eligible": True,
            }
        ),
        vector_index=SimpleNamespace(),
    )

    def close() -> None:
        nonlocal closed
        closed = True

    runtime.vector_index.close = close
    config = SimpleNamespace(
        qdrant_url=None,
        to_redacted_dict=lambda: {
            "embedding_model_path": str(tmp_path / "models/bge-m3"),
            "qdrant_path": str(tmp_path / "vectors/qdrant"),
            "qdrant_url": None,
            "local_files_only": True,
        },
    )
    monkeypatch.setattr(
        semantic,
        "load_property_runtime_config",
        lambda values, *, project_root: (
            config
            if values is environment and project_root == tmp_path
            else pytest.fail("readiness resolved a different configuration")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        semantic,
        "create_property_runtime_from_environment",
        lambda values, *, project_root: (
            runtime
            if values is environment and project_root == tmp_path
            else pytest.fail("readiness constructed a different runtime")
        ),
    )

    result = semantic.probe_property_runtime_readiness(
        environment=environment,
        project_root=tmp_path,
        require_no_network=True,
    )

    assert result["status"] == "ready"
    assert result["configuration"]["local_files_only"] is True
    assert closed is True


def test_no_network_readiness_probe_rejects_remote_qdrant_before_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    config = SimpleNamespace(
        qdrant_url="https://qdrant.invalid",
        to_redacted_dict=lambda: {
            "qdrant_url": "https://qdrant.invalid",
            "local_files_only": True,
        },
    )
    monkeypatch.setattr(
        semantic,
        "load_property_runtime_config",
        lambda _values, *, project_root: config,
        raising=False,
    )
    monkeypatch.setattr(
        semantic,
        "create_property_runtime_from_environment",
        lambda *_args, **_kwargs: pytest.fail(
            "no-network probe must reject remote Qdrant before construction"
        ),
    )

    result = semantic.probe_property_runtime_readiness(
        environment={},
        project_root=tmp_path,
        require_no_network=True,
    )

    assert result["status"] == "not_ready"
    assert result["reason_code"] == "NO_NETWORK_PROBE_REQUIRES_LOCAL_QDRANT"


def test_offline_runner_executes_all_frozen_cases_without_semantic_claim(
    project_root: Path,
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    provider = _OfflineProviderDouble()
    ledger_path = tmp_path / "semantic-predictions.json"
    result = semantic.produce_semantic_prediction_ledger(
        project_root=project_root,
        output_root=tmp_path / "run",
        ledger_path=ledger_path,
        provider=provider,
        property_runtime=_runtime(project_root),
    )

    assert result["schema_version"] == (
        "text2ifc/phase12.1-property-semantic-prediction-ledger/0.2"
    )
    assert result["status"] == "completed"
    assert result["case_count"] == 60
    assert result["semantic_accuracy_claim_eligible"] is False
    assert result["provider_evidence_mode"] == "injected_offline"
    assert result["ifc_publication_attempted"] is False
    assert provider.calls
    assert result["semantic_contract"] == {
        "benchmark_id": "phase12.1-stage1.5-semantic-acceptance",
        "evaluation_label": "STAGE15_SEMANTIC_EVALUATION",
        "taxonomy_version": "text2ifc/property-semantic-taxonomy/0.3",
        "template_id": "ifc-property-resolution.v0.2",
    }
    assert all(
        call["state"]["stage"] == "ifc_property_resolution"
        for call in provider.calls
    )
    assert ledger_path.is_file()
    assert not list((tmp_path / "run").rglob("*.ifc"))

    invoked = [
        case for case in result["cases"] if case["route"] == "property_resolution"
    ]
    assert invoked
    for case in invoked:
        assert case["provider_attempt_count"] >= 1
        assert case["attempts"]
        for attempt in case["attempts"]:
            assert Path(attempt["rendered_prompt_path"]).is_file()
            assert Path(attempt["raw_response_path"]).is_file()
            assert Path(attempt["parsed_response_path"]).is_file()
            assert attempt["latency_ms"] >= 0.0
            assert attempt["usage"]["total_tokens"] == 18
    assert all(Path(case["prediction_path"]).is_file() for case in result["cases"])


def test_gold_opens_only_after_ledger_and_case_predictions_are_durable(
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    ledger_path = tmp_path / "semantic-predictions.json"
    report_path = tmp_path / "semantic-report.json"
    semantic.produce_semantic_prediction_ledger(
        project_root=project_root,
        output_root=tmp_path / "run",
        ledger_path=ledger_path,
        provider=_OfflineProviderDouble(),
        property_runtime=_runtime(project_root),
    )
    real_loader = semantic._load_gold_cases
    observed = {"opened": False}

    def guarded_gold_loader(root: Path):
        assert ledger_path.is_file()
        persisted = json.loads(ledger_path.read_text(encoding="utf-8"))
        assert persisted["prediction_frozen_before_gold"] is True
        for case in persisted["cases"]:
            prediction_path = Path(case["prediction_path"])
            assert prediction_path.is_file()
            assert json.loads(prediction_path.read_text(encoding="utf-8")) == case[
                "prediction"
            ]
        observed["opened"] = True
        return real_loader(root)

    monkeypatch.setattr(semantic, "_load_gold_cases", guarded_gold_loader)
    report = semantic.score_semantic_prediction_ledger(
        project_root=project_root,
        ledger_path=ledger_path,
        output_path=report_path,
    )

    assert observed["opened"] is True
    assert report["status"] == "offline_contract_only"
    assert report["stage_1_5_semantic_evaluation_status"] == "not_evaluated_offline"
    assert report["semantic_accuracy_claim_eligible"] is False
    assert report["metrics"]["strict_outcome_accuracy"] is None
    assert report["metrics"]["clarification_accuracy"] is None
    assert report["metrics"]["unsupported_accuracy"] is None
    assert report_path.is_file()


def test_completed_prediction_ledger_enters_scorer_without_regeneration(
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    output_root = tmp_path / "run"
    ledger_path = output_root / "prediction-ledger.json"
    ledger = semantic.produce_semantic_prediction_ledger(
        project_root=project_root,
        output_root=output_root,
        ledger_path=ledger_path,
        provider=_OfflineProviderDouble(),
        property_runtime=_runtime(project_root),
    )
    prediction_bytes = {
        Path(case["prediction_path"]): Path(case["prediction_path"]).read_bytes()
        for case in ledger["cases"]
    }

    def reuse_completed_ledger(**arguments):
        assert Path(arguments["output_root"]) == output_root.resolve()
        assert Path(arguments["ledger_path"]) == ledger_path.resolve()
        return ledger

    monkeypatch.setattr(
        semantic,
        "produce_semantic_prediction_ledger",
        reuse_completed_ledger,
    )

    result = semantic.run_semantic_evaluation(
        output_root=output_root,
        provider=object(),
        environment={},
        project_root=project_root,
    )

    report_path = output_root / "semantic-evaluation-report.json"
    assert result["status"] == "offline_contract_only"
    assert result["semantic_report"] == str(report_path)
    assert report_path.is_file()
    assert all(path.read_bytes() == content for path, content in prediction_bytes.items())


def test_taxonomy_corrected_rescore_reuses_frozen_predictions_without_provider(
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    source_root = tmp_path / "source-run"
    ledger_path = source_root / "prediction-ledger.json"
    provider = _OfflineProviderDouble()
    ledger = semantic.produce_semantic_prediction_ledger(
        project_root=project_root,
        output_root=source_root,
        ledger_path=ledger_path,
        provider=provider,
        property_runtime=_runtime(project_root),
    )
    ledger["semantic_contract"]["taxonomy_version"] = (
        "text2ifc/property-semantic-taxonomy/0.2"
    )
    ledger_path.write_text(
        json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    source_report_path = source_root / "semantic-evaluation-report.json"
    source_report_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "text2ifc/phase12.1-property-semantic-evaluation/0.2"
                ),
                "status": "failed",
                "case_count": 60,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    ledger_bytes = ledger_path.read_bytes()
    report_bytes = source_report_path.read_bytes()
    prediction_bytes = {
        Path(case["prediction_path"]): Path(case["prediction_path"]).read_bytes()
        for case in ledger["cases"]
    }
    provider_call_count = len(provider.calls)
    monkeypatch.setattr(
        semantic,
        "TAXONOMY_RESCORE_SOURCE_RUN_ID",
        source_root.name,
        raising=False,
    )
    monkeypatch.setattr(
        semantic,
        "TAXONOMY_RESCORE_SOURCE_LEDGER_SHA256",
        hashlib.sha256(ledger_bytes).hexdigest(),
        raising=False,
    )
    monkeypatch.setattr(
        semantic,
        "TAXONOMY_RESCORE_SOURCE_REPORT_SHA256",
        hashlib.sha256(report_bytes).hexdigest(),
        raising=False,
    )

    output_path = tmp_path / "taxonomy-rescore" / "semantic-evaluation-report.json"
    result = semantic.rescore_semantic_prediction_ledger(
        project_root=project_root,
        ledger_path=ledger_path,
        source_report_path=source_report_path,
        output_path=output_path,
        source_prediction_run=source_root.name,
    )

    assert output_path.is_file()
    assert result["schema_version"] == (
        "text2ifc/phase12.1-property-semantic-evaluation/0.3"
    )
    assert result["evaluation_mode"] == "taxonomy_corrected_rescore"
    assert result["semantic_contract"]["taxonomy_version"] == (
        "text2ifc/property-semantic-taxonomy/0.2"
    )
    assert result["scoring_taxonomy"]["version"] == (
        "text2ifc/property-semantic-taxonomy/0.3"
    )
    assert result["rescore_evidence"] == {
        "source_prediction_run": source_root.name,
        "source_prediction_ledger": str(ledger_path.resolve()),
        "source_prediction_ledger_sha256": hashlib.sha256(
            ledger_bytes
        ).hexdigest(),
        "source_historical_report": str(source_report_path.resolve()),
        "source_historical_report_sha256": hashlib.sha256(
            report_bytes
        ).hexdigest(),
        "provider_calls_during_rescore": 0,
        "predictions_regenerated": 0,
        "predictions_modified": 0,
        "prediction_artifact_count": 60,
        "gold_accessed_during_original_prediction": False,
        "gold_opened_only_by_post_prediction_scorer": True,
        "historical_result_preserved": True,
    }
    assert len(provider.calls) == provider_call_count
    assert ledger_path.read_bytes() == ledger_bytes
    assert source_report_path.read_bytes() == report_bytes
    assert all(path.read_bytes() == content for path, content in prediction_bytes.items())


def test_infrastructure_failure_aborts_ledger_without_opening_gold(
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    monkeypatch.setattr(
        semantic,
        "_load_gold_cases",
        lambda _root: pytest.fail("aborted evaluation must not open Gold"),
    )
    provider = _InfrastructureFailureProvider()
    ledger_path = tmp_path / "semantic-predictions.json"

    result = semantic.produce_semantic_prediction_ledger(
        project_root=project_root,
        output_root=tmp_path / "run",
        ledger_path=ledger_path,
        provider=provider,
        property_runtime=_runtime(project_root),
        require_genuine_provider=True,
    )

    assert result["status"] == "aborted"
    assert result["reason_code"] == "PROPERTY_PROVIDER_REQUEST_FAILED"
    assert result["case_count"] < 60
    assert result["expected_case_count"] == 60
    assert result["gold_accessed_during_prediction"] is False
    assert result["semantic_accuracy_claim_eligible"] is False
    assert provider.calls == 2
    assert ledger_path.is_file()
    persisted = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert persisted == result
    assert persisted["cases"][-1]["route"] == "infrastructure_runtime_failure"


def test_aborted_run_never_invokes_semantic_scorer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    observed: dict[str, Any] = {}

    def abort_prediction(**arguments):
        observed.update(arguments)
        return {
            "status": "aborted",
            "reason_code": "QDRANT_UNAVAILABLE",
            "provider_attempt_count": 0,
            "semantic_accuracy_claim_eligible": False,
        }

    monkeypatch.setattr(
        semantic,
        "produce_semantic_prediction_ledger",
        abort_prediction,
    )
    monkeypatch.setattr(
        semantic,
        "score_semantic_prediction_ledger",
        lambda **_kwargs: pytest.fail("aborted run must not open Gold/scorer"),
    )

    result = semantic.run_semantic_evaluation(
        output_root=tmp_path / "run",
        provider=object(),
        environment={},
        project_root=tmp_path,
        evaluation_label=semantic.POST_FIX_EVALUATION_LABEL,
    )

    assert result["status"] == "aborted"
    assert result["reason_code"] == "QDRANT_UNAVAILABLE"
    assert result["semantic_report"] is None
    assert observed["evaluation_label"] == (
        "POST_FIX_STAGE15_ACCEPTANCE_EVALUATION"
    )


def test_family_slice_reports_route_and_invoked_uncertainty_separately() -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    rows = [
        {"passed": True, "provider_invoked": False},
        {"passed": True, "provider_invoked": True},
        {"passed": False, "provider_invoked": True},
    ]

    result = semantic._family_slice(rows, acceptance_eligible=True)

    assert result["case_count"] == 3
    assert result["provider_invoked_count"] == 2
    assert result["strict_outcome_accuracy"] == pytest.approx(2 / 3)
    assert result["invoked_strict_outcome_accuracy"] == pytest.approx(1 / 2)
    assert set(result["strict_outcome_accuracy_95ci"]) == {"lower", "upper"}
    assert set(result["invoked_strict_outcome_accuracy_95ci"]) == {
        "lower",
        "upper",
    }


def test_genuine_malformed_model_output_remains_semantic_score_eligible(
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    row = {
        "case_id": "semantic-error",
        "route": "property_resolution",
        "provider_attempt_count": 2,
        "retry_count": 1,
        "provider_acceptance_eligible": False,
        "attempts": [
            {"evidence_class": "live"},
            {"evidence_class": "live"},
        ],
    }

    ledger = semantic._prediction_ledger(
        rows=[row],
        runtime_health={"status": "ready", "acceptance_eligible": True},
        destination=tmp_path / "ledger.json",
        status="completed",
        reason_code=None,
        expected_case_count=1,
        abort_case_id=None,
        require_genuine_provider=True,
    )

    assert ledger["provider_evidence_mode"] == "genuine_live"
    assert ledger["semantic_accuracy_claim_eligible"] is True


@pytest.mark.parametrize(
    ("prediction", "gold", "expected"),
    (
        (
            {
                "route": "property_resolution",
                "candidate_paths": ["Pset_BeamCommon.LoadBearing"],
                "stage_valid": True,
                "classification": "confirmed",
                "selected_path": "Pset_BeamCommon.LoadBearing",
                "admissibility_status": "passed",
            },
            {"authorize": True, "expected": "Pset_BeamCommon.LoadBearing"},
            "correct_offered_candidate_selection",
        ),
        (
            {
                "route": "property_resolution",
                "stage_valid": True,
                "classification": "clarification_required",
                "candidate_paths": [],
            },
            {"authorize": False, "expected": None},
            "clarification",
        ),
        (
            {
                "route": "property_resolution",
                "stage_valid": True,
                "classification": "unsupported",
                "candidate_paths": [],
            },
            {"authorize": False, "expected": None},
            "unsupported",
        ),
        (
            {"route": "not_invoked_no_candidates", "candidate_paths": []},
            {"authorize": True, "expected": "Pset_BeamCommon.LoadBearing"},
            "retrieval_failure",
        ),
    ),
)
def test_semantic_evaluator_classifies_primary_outcome_families(
    prediction: dict[str, Any],
    gold: dict[str, Any],
    expected: str,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    assert semantic.classify_semantic_outcome(prediction, gold) == expected


@pytest.mark.parametrize(
    ("prediction", "gold", "expected"),
    (
        (
            {
                "route": "property_resolution",
                "candidate_paths": ["Pset_BeamCommon.LoadBearing"],
                "stage_valid": True,
                "classification": "confirmed",
                "selected_path": "Pset_BeamCommon.IsExternal",
                "admissibility_status": "passed",
            },
            {"authorize": True, "expected": "Pset_BeamCommon.LoadBearing"},
            "semantic_selection_failure",
        ),
        (
            {
                "route": "property_resolution",
                "candidate_paths": [],
                "stage_valid": False,
                "issue_codes": ["PROPERTY_CANDIDATE_NOT_OFFERED"],
            },
            {"authorize": False, "expected": None},
            "unoffered_selection",
        ),
        (
            {
                "route": "property_resolution",
                "candidate_paths": [],
                "stage_valid": False,
                "error_code": "PROPERTY_RESOLUTION_RETRY_EXHAUSTED",
                "issue_codes": ["JSON_DECODE_ERROR"],
            },
            {"authorize": False, "expected": None},
            "malformed_retry_exhaustion",
        ),
        (
            {
                "route": "property_resolution",
                "candidate_paths": ["Pset_BeamCommon.LoadBearing"],
                "stage_valid": True,
                "classification": "confirmed",
                "selected_path": "Pset_BeamCommon.LoadBearing",
                "admissibility_status": "rejected",
            },
            {"authorize": False, "expected": None},
            "admissibility_rejection",
        ),
        (
            {
                "route": "infrastructure_runtime_failure",
                "candidate_paths": [],
            },
            {"authorize": False, "expected": None},
            "infrastructure_runtime_failure",
        ),
    ),
)
def test_semantic_evaluator_classifies_failure_outcome_families(
    prediction: dict[str, Any],
    gold: dict[str, Any],
    expected: str,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    assert semantic.classify_semantic_outcome(prediction, gold) == expected


def test_v02_taxonomy_audits_all_cases_and_changes_only_clarification_class() -> None:
    project_root = Path(__file__).resolve().parents[2]
    taxonomy = json.loads(
        (
            project_root
            / "tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json"
        ).read_text(encoding="utf-8")
    )
    baseline = json.loads(
        (
            project_root
            / "tests/fixtures/knowledge/phase10_2_property_retrieval.json"
        ).read_text(encoding="utf-8")
    )
    additions = json.loads(
        (
            project_root
            / "tests/fixtures/knowledge/phase12_1_property_resolution.json"
        ).read_text(encoding="utf-8")
    )

    rows = {row["case_id"]: row for row in taxonomy["cases"]}
    source_ids = {
        row["id"] for row in [*baseline["cases"], *additions["cases"]]
    }
    assert taxonomy["schema_version"] == (
        "text2ifc/property-semantic-taxonomy/0.2"
    )
    assert taxonomy["case_count"] == 60
    assert set(rows) == source_ids

    assert rows["a08"]["semantic_category"] == "explicit_property_intent"
    assert rows["a08"]["expected_route"] == "confirmed_standard"
    assert rows["n06"]["semantic_category"] == "vague_repair_goal"
    assert rows["n06"]["expected_route"] == "clarification_required"
    assert rows["p12m04"]["semantic_category"] == (
        "underspecified_supported_property"
    )
    assert rows["p12m04"]["expected_route"] == "clarification_required"
    assert rows["n04"]["semantic_category"] == "unsupported_subjective_goal"
    assert rows["n04"]["expected_route"] == "unsupported"

    changed = {
        row["case_id"]: row["previous_expected_route"]
        for row in rows.values()
        if row["taxonomy_change"] == "clarified"
    }
    assert changed == {
        "n06": "unsupported",
        "p12m04": "clarification_or_unsupported",
    }


def test_v03_taxonomy_freezes_general_clarification_and_unsupported_boundary() -> None:
    project_root = Path(__file__).resolve().parents[2]
    taxonomy = json.loads(
        (
            project_root
            / "tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_3.json"
        ).read_text(encoding="utf-8")
    )
    baseline = json.loads(
        (
            project_root
            / "tests/fixtures/knowledge/phase10_2_property_retrieval.json"
        ).read_text(encoding="utf-8")
    )
    additions = json.loads(
        (
            project_root
            / "tests/fixtures/knowledge/phase12_1_property_resolution.json"
        ).read_text(encoding="utf-8")
    )

    rows = {row["case_id"]: row for row in taxonomy["cases"]}
    source_ids = {
        row["id"] for row in [*baseline["cases"], *additions["cases"]]
    }
    assert taxonomy["schema_version"] == (
        "text2ifc/property-semantic-taxonomy/0.3"
    )
    assert taxonomy["case_count"] == 60
    assert set(rows) == source_ids
    assert taxonomy["decision_rule"] == {
        "confirmed": (
            "The request directly and sufficiently identifies exactly one "
            "offered canonical property."
        ),
        "clarification_required": (
            "The request is plausibly within the supported repair capability "
            "but lacks enough information to determine one executable intent."
        ),
        "unsupported_property": (
            "The property intent is specific, but no such property exists in "
            "the authoritative supported property universe."
        ),
        "unsupported_operation": (
            "The requested repair operation is outside the supported repair "
            "capability."
        ),
    }

    assert rows["n05"]["semantic_category"] == (
        "underspecified_supported_property_edit"
    )
    assert rows["n05"]["expected_route"] == "clarification_required"
    assert rows["n05"]["previous_expected_route"] == "unsupported"
    assert rows["n04"]["semantic_category"] == "unsupported_operation"
    assert rows["n04"]["expected_route"] == "unsupported_operation"
    assert rows["n06"]["expected_route"] == "clarification_required"
    assert rows["p12m04"]["expected_route"] == "clarification_required"


@pytest.mark.parametrize(
    ("semantic_case", "expected_route", "outcome", "passed"),
    (
        (
            "underspecified_supported_property_edit",
            "clarification_required",
            "clarification",
            True,
        ),
        (
            "multiple_plausible_properties",
            "clarification_required",
            "clarification",
            True,
        ),
        (
            "explicit_nonexistent_property",
            "unsupported_property",
            "unsupported",
            True,
        ),
        (
            "unsupported_repair_operation",
            "unsupported_operation",
            "unsupported",
            True,
        ),
        (
            "resolved_property_invalid_value",
            "inadmissible",
            "admissibility_rejection",
            True,
        ),
    ),
)
def test_v03_terminal_routes_keep_semantics_and_validation_separate(
    semantic_case: str,
    expected_route: str,
    outcome: str,
    passed: bool,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    gold = {
        "authorize": False,
        "expected": None,
        "expected_route": expected_route,
        "semantic_category": semantic_case,
    }
    assert semantic._outcome_matches_gold(outcome, {}, gold) is passed


@pytest.mark.parametrize(
    ("expected_route", "outcome", "passed"),
    (
        ("clarification_required", "clarification", True),
        ("clarification_required", "unsupported", False),
        ("clarification_required", "semantic_selection_failure", False),
        ("unsupported", "unsupported", True),
        ("unsupported", "clarification", False),
    ),
)
def test_v02_clarification_and_unsupported_routes_are_scored_separately(
    expected_route: str,
    outcome: str,
    passed: bool,
) -> None:
    from scripts.ifc_repair import run_phase12_1_semantic_evaluation as semantic

    gold = {
        "authorize": False,
        "expected": None,
        "expected_route": expected_route,
    }
    assert semantic._outcome_matches_gold(outcome, {}, gold) is passed
