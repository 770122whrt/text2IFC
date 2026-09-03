from __future__ import annotations

from pathlib import Path

from scripts.ifc_repair import run_phase12_live_uat as live
from scripts.ifc_repair import run_repair_milestone_r1 as runner
from text2ifc_ifc_repair.benchmark_evaluation import (
    ProductionEvaluationInputs,
)
from text2ifc_ifc_repair.evaluation import EvaluationExecutionPolicy


def test_r1_budget_keeps_180_seconds_as_nonblocking_slo() -> None:
    policy = runner._r1_evaluation_execution_policy()

    assert policy.deadline_seconds == 600.0
    assert policy.rss_limit_bytes == 4 * 1024**3
    assert runner.R1_PERFORMANCE_SLO_SECONDS == 180.0
    assert runner.R1_PERFORMANCE_SLO_BLOCKING is False


def test_live_executor_policy_wrapper_records_recoverable_configuration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}
    evidence = {}
    inputs = ProductionEvaluationInputs(
        damaged_ifc_path=tmp_path / "damaged.ifc",
        repaired_ifc_path=tmp_path / "repaired.ifc",
        changeset={},
        application_result={},
        registry=object(),
    )
    expected = object()

    def fake_evaluate(configured):
        captured["policy"] = configured.execution_policy
        return expected

    monkeypatch.setattr(live, "evaluate_production", fake_evaluate)
    stage = live._evaluation_stage_with_policy(
        EvaluationExecutionPolicy(
            deadline_seconds=600.0,
            rss_limit_bytes=4 * 1024**3,
        ),
        performance_slo_seconds=180.0,
        evidence=evidence,
    )

    assert stage(inputs) is expected
    assert captured["policy"].deadline_seconds == 600.0
    assert evidence["correctness_deadline_seconds"] == 600.0
    assert evidence["performance_slo_seconds"] == 180.0
    assert evidence["performance_slo_blocking"] is False
    assert isinstance(evidence["performance_slo_met"], bool)
    assert evidence["wall_seconds"] >= 0.0


def test_r1_stops_on_any_failed_case_contract() -> None:
    assert runner._case_stop_reason(
        contract_pass=False,
        execution_error=None,
    ) == "R1_CASE_CONTRACT_STOP"
    assert runner._case_stop_reason(
        contract_pass=False,
        execution_error="boom",
    ) == "R1_EXECUTION_DEFECT_STOP"
    assert runner._case_stop_reason(
        contract_pass=True,
        execution_error=None,
    ) is None