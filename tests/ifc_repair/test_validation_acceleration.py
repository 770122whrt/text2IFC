from __future__ import annotations

import time
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.evaluation import (
    EvaluationExecutionPolicy,
    execute_validation_and_diff,
)


def _write(path: Path, *, extra_error: bool = False) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcCartesianPoint")
    if extra_error:
        model.create_entity("IfcDirection")
    model.write(str(path))


def _run(
    tmp_path: Path,
    *,
    mode: str,
    validation_worker=None,
    diff_worker=None,
    rss_reader=None,
    deadline: float = 10.0,
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


def test_policy_rejects_more_than_two_workers() -> None:
    try:
        EvaluationExecutionPolicy(max_workers=3)
    except ValueError as error:
        assert str(error) == "EVALUATION_WORKER_COUNT_INVALID"
    else:
        raise AssertionError("three workers must be rejected")
