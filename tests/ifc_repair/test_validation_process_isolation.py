"""Warm property models must not be inherited by IFC validation workers."""
from pathlib import Path
import sys

import pytest

import text2ifc_ifc_repair.evaluation as evaluation


LIMIT = 4 * 1024**3


def test_pool_worker_uses_current_executable_peak(monkeypatch) -> None:
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.as_posix() == '/proc/self/status':
            return 'Name:\tpython\nVmHWM:\t128000 kB\nVmRSS:\t64000 kB\n'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(Path, 'read_text', read)
    assert evaluation._current_process_peak_rss() == 128000 * 1024


@pytest.mark.parametrize(
    "parent_rss, fresh_worker_rss, expected_status",
    [
        (100_000_000, 150_000_000, "passed"),
        (2_668_261_376, 150_000_000, "passed"),
        (LIMIT - 200, 100, "passed"),
        (LIMIT - 199, 100, "failed"),
        (100_000_000, LIMIT // 2, "failed"),
    ],
    ids=["cold-parent", "warm-property-parent", "exact-limit", "parent-over", "workers-over"],
)
def test_validation_workers_do_not_inherit_property_memory(
    tmp_path: Path, monkeypatch, parent_rss, fresh_worker_rss, expected_status
) -> None:
    contexts = []
    shutdowns = []

    class Result:
        def __init__(self, start_method):
            self.start_method = start_method

        def result(self, timeout):
            assert 0 < timeout <= 180
            # Linux fork copies the warmed runtime's address space. A fresh
            # interpreter has only the validator's measured resident memory.
            peak = fresh_worker_rss if self.start_method == "spawn" else 1_142_751_232
            return ({"valid": True}, {"status": "miss"}, peak)

    class Pool:
        def __init__(self, max_workers, mp_context=None):
            assert max_workers == 2
            self.start_method = mp_context.get_start_method() if mp_context else "fork"
            contexts.append(self.start_method)

        def submit(self, *_args):
            return Result(self.start_method)

        def shutdown(self, **kwargs):
            shutdowns.append(kwargs)

    monkeypatch.setattr(evaluation, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(evaluation.ifcopenshell, "open", lambda *_: object())
    monkeypatch.setattr(evaluation, "compare_validation_models", lambda *_args, **_kw: {"valid": True})
    monkeypatch.setattr(evaluation, "normalized_model_diff", lambda *_: {"same": True})

    result = evaluation._execute_default_accelerated(
        damaged_path=tmp_path / "D.ifc", repaired_path=tmp_path / "R.ifc",
        cache_dir=tmp_path / "cache", policy=evaluation.EvaluationExecutionPolicy(),
        started=evaluation.time.monotonic(), rss_reader=lambda: parent_rss,
    )

    assert contexts == ["spawn"]
    assert shutdowns == [{"wait": True, "cancel_futures": True}]
    assert result["status"] == expected_status
    assert result["metrics"]["rss_limit_bytes"] == LIMIT
    assert result["metrics"]["worker_peak_rss_bytes"] == {
        "baseline": fresh_worker_rss, "candidate": fresh_worker_rss,
    }
    if expected_status == "failed":
        assert result["reason_code"] == "EVALUATION_RSS_LIMIT_EXCEEDED"
        assert result["results"] == {}
    else:
        assert result["results"]["diff"] == {"same": True}


def test_spawned_validation_timeout_still_fails_closed(tmp_path: Path, monkeypatch) -> None:
    shutdowns = []

    class Timeout:
        def result(self, timeout):
            raise evaluation.FuturesTimeoutError()

    class Pool:
        def __init__(self, *, max_workers, mp_context=None):
            assert max_workers == 2
            assert mp_context is not None and mp_context.get_start_method() == "spawn"

        def submit(self, *_args):
            return Timeout()

        def shutdown(self, **kwargs):
            shutdowns.append(kwargs)

    monkeypatch.setattr(evaluation, "ProcessPoolExecutor", Pool)
    result = evaluation._execute_default_accelerated(
        damaged_path=tmp_path / "D.ifc", repaired_path=tmp_path / "R.ifc",
        cache_dir=tmp_path / "cache", policy=evaluation.EvaluationExecutionPolicy(),
        started=evaluation.time.monotonic(), rss_reader=lambda: 0,
    )
    assert result["reason_code"] == "EVALUATION_DEADLINE_EXCEEDED"
    assert result["results"] == {}
    assert shutdowns == [{"wait": False, "cancel_futures": True}]
