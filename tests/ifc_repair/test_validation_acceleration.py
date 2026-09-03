from __future__ import annotations

import hashlib
import time
from pathlib import Path

import ifcopenshell
import pytest

import text2ifc_ifc_repair.benchmark_evaluation as benchmark_evaluation_module
import text2ifc_ifc_repair.evaluation as evaluation_module
from text2ifc_ifc_repair.benchmark_evaluation import (
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.evaluation import (
    EvaluationExecutionPolicy,
    _open_ifc_pair,
    execute_validation_and_diff,
)
from text2ifc_ifc_repair.operations import create_default_registry


PARITY_TEST_DEADLINE_SECONDS = 60.0


def _write(path: Path, *, extra_error: bool = False) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcCartesianPoint")
    if extra_error:
        model.create_entity("IfcDirection")
    model.write(str(path))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(
    tmp_path: Path,
    *,
    mode: str,
    validation_worker=None,
    diff_worker=None,
    rss_reader=None,
    deadline: float = PARITY_TEST_DEADLINE_SECONDS,
    rss_limit: int = 4 * 1024**3,
):
    baseline = tmp_path / "baseline.ifc"
    candidate = tmp_path / "candidate.ifc"
    if not baseline.exists():
        _write(baseline)
        _write(candidate, extra_error=True)
    return execute_validation_and_diff(
        damaged_ifc_path=baseline,
        repaired_ifc_path=candidate,
        cache_dir=tmp_path / "cache",
        policy=EvaluationExecutionPolicy(
            mode=mode,
            deadline_seconds=deadline,
            max_workers=2,
            rss_limit_bytes=rss_limit,
        ),
        validation_worker=validation_worker,
        diff_worker=diff_worker,
        rss_reader=rss_reader,
    )


def test_sequential_and_accelerated_evidence_is_identical(tmp_path: Path) -> None:
    sequential = _run(tmp_path, mode="sequential")
    accelerated = _run(tmp_path, mode="accelerated")

    assert sequential["status"] == accelerated["status"] == "passed"
    assert (
        sequential["results"]["validation"]["comparison"]
        == accelerated["results"]["validation"]["comparison"]
    )
    assert sequential["results"]["diff"] == accelerated["results"]["diff"]
    assert sequential["metrics"]["worker_count"] == 1
    assert accelerated["metrics"]["worker_count"] == 2
    assert (
        accelerated["results"]["validation"]["cache"]["baseline"]["status"]
        == "hit"
    )


def test_cache_cold_then_warm_preserves_diagnostic_signatures(
    tmp_path: Path,
) -> None:
    cold = _run(tmp_path, mode="accelerated")
    warm = _run(tmp_path, mode="accelerated")

    cold_cache = cold["results"]["validation"]["cache"]
    warm_cache = warm["results"]["validation"]["cache"]
    assert {item["status"] for item in cold_cache.values()} == {"miss"}
    assert {item["status"] for item in warm_cache.values()} == {"hit"}
    assert (
        cold["results"]["validation"]["comparison"]
        == warm["results"]["validation"]["comparison"]
    )


def test_reopened_model_reuse_preserves_full_validation_and_diff(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.ifc"
    candidate = tmp_path / "candidate.ifc"
    _write(baseline)
    _write(candidate, extra_error=True)
    policy = EvaluationExecutionPolicy(
        mode="accelerated",
        deadline_seconds=PARITY_TEST_DEADLINE_SECONDS,
    )
    expected = execute_validation_and_diff(
        damaged_ifc_path=baseline,
        repaired_ifc_path=candidate,
        cache_dir=tmp_path / "expected-cache",
        policy=policy,
    )
    reused = execute_validation_and_diff(
        damaged_ifc_path=baseline,
        repaired_ifc_path=candidate,
        cache_dir=tmp_path / "reused-cache",
        policy=policy,
        baseline_model=ifcopenshell.open(str(baseline)),
        candidate_model=ifcopenshell.open(str(candidate)),
    )

    assert expected["status"] == reused["status"] == "passed"
    assert expected["results"]["validation"]["comparison"] == (
        reused["results"]["validation"]["comparison"]
    )
    assert expected["results"]["diff"] == reused["results"]["diff"]
    assert reused["metrics"]["mode"] == "reused_models"
    assert reused["metrics"]["worker_count"] == 3


def test_accelerated_reopen_loads_the_independent_pair_concurrently(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.ifc"
    candidate = tmp_path / "candidate.ifc"
    _write(baseline)
    _write(candidate, extra_error=True)

    before, after = _open_ifc_pair(
        baseline,
        candidate,
        accelerated=True,
    )

    assert before[0] is not None and before[1] is None
    assert after[0] is not None and after[1] is None


def test_worker_exception_fails_closed(tmp_path: Path) -> None:
    def broken_validation(*_args):
        raise RuntimeError("validation boom")

    result = _run(
        tmp_path,
        mode="accelerated",
        validation_worker=broken_validation,
        diff_worker=lambda *_: {"same": True},
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "EVALUATION_WORKER_FAILED"
    assert result["results"] == {}


def test_deadline_timeout_fails_closed(tmp_path: Path) -> None:
    def slow(*_args):
        time.sleep(0.05)
        return {"late": True}

    result = _run(
        tmp_path,
        mode="accelerated",
        validation_worker=slow,
        diff_worker=slow,
        deadline=0.01,
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "EVALUATION_DEADLINE_EXCEEDED"


def test_missing_worker_result_fails_closed(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        mode="sequential",
        validation_worker=lambda *_: None,
        diff_worker=lambda *_: {"diff": "complete"},
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "EVALUATION_WORKER_RESULT_MISSING"


def test_rss_limit_failure_suppresses_results(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        mode="sequential",
        validation_worker=lambda *_: {"validation": "complete"},
        diff_worker=lambda *_: {"diff": "complete"},
        rss_reader=lambda: 1025,
        rss_limit=1024,
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "EVALUATION_RSS_LIMIT_EXCEEDED"
    assert result["results"] == {}


def test_accelerated_rss_ignores_unrelated_parent_lifetime_peak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical_parent_peak = 4_150_000_000
    monkeypatch.setattr(
        evaluation_module,
        "_current_process_peak_rss",
        lambda: historical_parent_peak,
    )

    result = _run(tmp_path, mode="accelerated")

    assert result["status"] == "passed"
    metrics = result["metrics"]
    assert metrics["parent_current_rss_bytes"] < historical_parent_peak
    assert metrics["diff_phase_peak_rss_bytes"] == metrics[
        "parent_current_rss_bytes"
    ]
    assert metrics["peak_rss_bytes"] == max(
        metrics["validation_phase_peak_rss_bytes"],
        metrics["diff_phase_peak_rss_bytes"],
    )


def test_accelerated_rss_peak_respects_nonoverlapping_phases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker_peak = 1_000_000_000
    validation_parent_rss = 1_500_000_000
    diff_parent_rss = 3_000_000_000
    models_opened = False

    class ImmediateFuture:
        def result(self, timeout=None):
            return ({"valid": True}, {"status": "miss"}, worker_peak)

    class ImmediateExecutor:
        def __init__(self, max_workers):
            assert max_workers == 2

        def submit(self, *_args, **_kwargs):
            return ImmediateFuture()

        def shutdown(self, *, wait, cancel_futures):
            return None

    def open_model(_path):
        nonlocal models_opened
        models_opened = True
        return object()

    monkeypatch.setattr(
        evaluation_module, "ProcessPoolExecutor", ImmediateExecutor
    )
    monkeypatch.setattr(evaluation_module.ifcopenshell, "open", open_model)
    monkeypatch.setattr(
        evaluation_module,
        "compare_validation_models",
        lambda *_args, **_kwargs: {"same": True},
    )
    monkeypatch.setattr(
        evaluation_module,
        "normalized_model_diff",
        lambda *_args, **_kwargs: {"same": True},
    )

    result = _run(
        tmp_path,
        mode="accelerated",
        rss_reader=lambda: (
            diff_parent_rss if models_opened else validation_parent_rss
        ),
        rss_limit=4_000_000_000,
    )

    assert result["status"] == "passed"
    metrics = result["metrics"]
    assert metrics["validation_phase_peak_rss_bytes"] == 3_500_000_000
    assert metrics["diff_phase_peak_rss_bytes"] == 3_000_000_000
    assert metrics["peak_rss_bytes"] == 3_500_000_000

def test_accelerated_current_rss_limit_violation_still_fails_closed(
    tmp_path: Path,
) -> None:
    limit = 1024

    result = _run(
        tmp_path,
        mode="accelerated",
        rss_reader=lambda: limit + 1,
        rss_limit=limit,
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "EVALUATION_RSS_LIMIT_EXCEEDED"
    assert result["results"] == {}
    assert result["metrics"]["parent_current_rss_bytes"] == limit + 1


def test_evaluate_production_uses_green_accelerated_scheduler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    damaged = tmp_path / "production-damaged.ifc"
    repaired = tmp_path / "production-repaired.ifc"
    _write(damaged)
    repaired.write_bytes(damaged.read_bytes())
    scheduler_results: list[dict[str, object]] = []
    real_execute = evaluation_module.execute_validation_and_diff

    def record_execute(**kwargs):
        result = real_execute(**kwargs)
        scheduler_results.append(result)
        return result

    monkeypatch.setattr(
        evaluation_module,
        "execute_validation_and_diff",
        record_execute,
    )
    monkeypatch.setattr(
        benchmark_evaluation_module,
        "aggregate_repair",
        lambda **kwargs: type(
            "ProductionSchedulerProbe",
            (),
            {
                "complete_repair_success": (
                    kwargs["preservation"].status.value == "passed"
                )
            },
        )(),
    )

    evaluate_production(
        ProductionEvaluationInputs(
            damaged_ifc_path=damaged,
            repaired_ifc_path=repaired,
            changeset={
                "schema_version": "text2ifc/ifc-repair-changeset/0.3",
                "base_model_fingerprint": _sha256(damaged),
                "operations": [],
            },
            application_result={
                "valid": True,
                "published": True,
                "operations": [],
            },
            registry=create_default_registry(),
        )
    )

    assert len(scheduler_results) == 1
    assert scheduler_results[0]["status"] == "passed"
    assert scheduler_results[0]["metrics"]["mode"] == "accelerated"


def test_policy_rejects_more_than_two_workers() -> None:
    try:
        EvaluationExecutionPolicy(max_workers=3)
    except ValueError as error:
        assert str(error) == "EVALUATION_WORKER_COUNT_INVALID"
    else:
        raise AssertionError("three workers must be rejected")
