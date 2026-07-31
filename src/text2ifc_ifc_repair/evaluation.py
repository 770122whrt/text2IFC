"""Pure aggregation and canonical serialization for evaluation 0.2."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)
from dataclasses import dataclass
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import ifcopenshell
from jsonschema import Draft202012Validator

from .compare import ComparisonIntegrityError, normalized_model_diff
from .ifc_validation import (
    DIAGNOSTIC_NORMALIZATION_VERSION,
    VALIDATION_POLICY_VERSION,
    compare_validation_models,
    normalized_validation_result,
)
from .validation_cache import ValidationCache, ValidationCacheKey

from .evaluation_models import (
    CheckResult,
    EVALUATION_SCHEMA_VERSION,
    EvaluationContractError,
    EvaluationStatus,
    EvidenceFact,
    LEGACY_EVALUATION_SCHEMA_VERSION,
    LegacyEvaluationProjection,
    LevelResult,
    OperationEvaluation,
    RepairEvaluation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-evaluation-0.2.schema.json"
)
_STATUS_PRECEDENCE = {
    EvaluationStatus.PASSED: 0,
    EvaluationStatus.NOT_REQUIRED: 0,
    EvaluationStatus.NOT_EVALUABLE: 1,
    EvaluationStatus.PARTIAL: 2,
    EvaluationStatus.FAILED: 3,
}

_COMMON_L1_POLICY_ID = "l1.common"
_L1_EVIDENCE_VALUE_MAX_BYTES = 4096
COMMON_L1_CHECK_IDS = (
    "l1.output.readable",
    "l1.output.schema",
    "l1.output.validation",
    "l1.source.immutable",
    "l1.scope.created-roots",
    "l1.scope.modified-roots",
    "l1.scope.removed-roots",
    "l1.scope.relations",
)
_SCOPE_L1_CHECK_IDS = COMMON_L1_CHECK_IDS[4:]


@dataclass(frozen=True)
class EvaluationExecutionPolicy:
    mode: str = "accelerated"
    deadline_seconds: float = 180.0
    max_workers: int = 2
    rss_limit_bytes: int = 4 * 1024**3
    cache_mode: str = "read_write"

    def __post_init__(self) -> None:
        if self.mode not in {"sequential", "accelerated"}:
            raise ValueError("EVALUATION_EXECUTION_MODE_INVALID")
        if self.deadline_seconds <= 0:
            raise ValueError("EVALUATION_DEADLINE_INVALID")
        if not 1 <= self.max_workers <= 2:
            raise ValueError("EVALUATION_WORKER_COUNT_INVALID")
        if self.rss_limit_bytes <= 0:
            raise ValueError("EVALUATION_RSS_LIMIT_INVALID")


def execute_validation_and_diff(
    *,
    damaged_ifc_path: Path | str,
    repaired_ifc_path: Path | str,
    cache_dir: Path | str,
    policy: EvaluationExecutionPolicy,
    validation_worker: Any | None = None,
    diff_worker: Any | None = None,
    rss_reader: Any | None = None,
    baseline_model: Any | None = None,
    candidate_model: Any | None = None,
) -> dict[str, Any]:
    """Schedule unchanged validation and full diff with a fail-closed deadline."""

    started = time.monotonic()
    if (baseline_model is None) != (candidate_model is None):
        raise ValueError("EVALUATION_REUSED_MODEL_PAIR_REQUIRED")
    if baseline_model is not None and candidate_model is not None:
        if validation_worker is not None or diff_worker is not None:
            raise ValueError("EVALUATION_REUSED_MODEL_CUSTOM_WORKER_UNSUPPORTED")
        return _execute_reused_models(
            damaged_path=Path(damaged_ifc_path),
            repaired_path=Path(repaired_ifc_path),
            cache_dir=Path(cache_dir),
            policy=policy,
            started=started,
            rss_reader=rss_reader or _process_tree_rss,
            baseline_model=baseline_model,
            candidate_model=candidate_model,
        )
    if (
        policy.mode == "accelerated"
        and validation_worker is None
        and diff_worker is None
    ):
        return _execute_default_accelerated(
            damaged_path=Path(damaged_ifc_path),
            repaired_path=Path(repaired_ifc_path),
            cache_dir=Path(cache_dir),
            policy=policy,
            started=started,
            rss_reader=rss_reader or _process_tree_rss,
        )
    validate = validation_worker or _cached_validation_worker
    compare = diff_worker or _path_diff_worker
    rss = rss_reader or _process_tree_rss
    tasks = {
        "validation": lambda: validate(
            Path(damaged_ifc_path),
            Path(repaired_ifc_path),
            Path(cache_dir),
            policy.cache_mode,
        ),
        "diff": lambda: compare(
            Path(damaged_ifc_path), Path(repaired_ifc_path)
        ),
    }
    results: dict[str, Any] = {}
    stage_seconds: dict[str, float] = {}

    def timed(name: str):
        stage_started = time.monotonic()
        value = tasks[name]()
        return value, time.monotonic() - stage_started

    try:
        if policy.mode == "sequential":
            for name in ("validation", "diff"):
                remaining = policy.deadline_seconds - (
                    time.monotonic() - started
                )
                if remaining <= 0:
                    raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED")
                value, elapsed = timed(name)
                results[name] = value
                stage_seconds[name] = elapsed
        else:
            executor = ThreadPoolExecutor(
                max_workers=min(policy.max_workers, 2),
                thread_name_prefix="ifc-evaluation",
            )
            try:
                futures = {
                    name: executor.submit(timed, name) for name in tasks
                }
                for name in ("validation", "diff"):
                    remaining = policy.deadline_seconds - (
                        time.monotonic() - started
                    )
                    if remaining <= 0:
                        raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED")
                    try:
                        value, elapsed = futures[name].result(timeout=remaining)
                    except FuturesTimeoutError as error:
                        raise TimeoutError(
                            "EVALUATION_DEADLINE_EXCEEDED"
                        ) from error
                    results[name] = value
                    stage_seconds[name] = elapsed
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
    except Exception as error:
        return {
            "status": "failed",
            "reason_code": (
                str(error)
                if isinstance(error, TimeoutError)
                else "EVALUATION_WORKER_FAILED"
            ),
            "error": f"{type(error).__name__}:{error}"[:1000],
            "results": {},
            "metrics": {
                "mode": policy.mode,
                "worker_count": (
                    1 if policy.mode == "sequential" else policy.max_workers
                ),
                "wall_seconds": time.monotonic() - started,
                "stage_seconds": stage_seconds,
                "peak_rss_bytes": rss(),
            },
        }
    if set(results) != {"validation", "diff"} or any(
        value is None for value in results.values()
    ):
        return {
            "status": "failed",
            "reason_code": "EVALUATION_WORKER_RESULT_MISSING",
            "results": results,
            "metrics": {},
        }
    peak_rss = int(rss())
    if peak_rss > policy.rss_limit_bytes:
        return {
            "status": "failed",
            "reason_code": "EVALUATION_RSS_LIMIT_EXCEEDED",
            "results": {},
            "metrics": {
                "peak_rss_bytes": peak_rss,
                "rss_limit_bytes": policy.rss_limit_bytes,
            },
        }
    return {
        "status": "passed",
        "reason_code": None,
        "results": results,
        "metrics": {
            "mode": policy.mode,
            "worker_count": (
                1 if policy.mode == "sequential" else policy.max_workers
            ),
            "wall_seconds": time.monotonic() - started,
            "stage_seconds": stage_seconds,
            "peak_rss_bytes": peak_rss,
            "rss_limit_bytes": policy.rss_limit_bytes,
        },
    }


def _execute_reused_models(
    *,
    damaged_path: Path,
    repaired_path: Path,
    cache_dir: Path,
    policy: EvaluationExecutionPolicy,
    started: float,
    rss_reader: Any,
    baseline_model: Any,
    candidate_model: Any,
) -> dict[str, Any]:
    """Run complete evidence rules while overlapping validation and full diff."""

    cache = ValidationCache(cache_dir, mode=policy.cache_mode)
    normalized: dict[str, dict[str, Any]] = {}
    cache_evidence: dict[str, Any] = {}
    stage_seconds: dict[str, float] = {}
    worker_peak_rss: dict[str, int] = {}
    pending: dict[str, subprocess.Popen[str]] = {}
    try:
        validation_started = time.monotonic()
        for role, path, model in (
            ("baseline", damaged_path, baseline_model),
            ("candidate", repaired_path, candidate_model),
        ):
            if time.monotonic() - started > policy.deadline_seconds:
                raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED")
            path_hash = _path_sha256(path)
            if path_hash is None:
                raise OSError(f"EVALUATION_IFC_HASH_FAILED:{path}")
            key = ValidationCacheKey(
                ifc_sha256=path_hash,
                ifc_schema=str(model.schema).upper(),
                ifcopenshell_version=str(ifcopenshell.version),
                validation_policy_version=VALIDATION_POLICY_VERSION,
                diagnostic_normalization_version=(
                    DIAGNOSTIC_NORMALIZATION_VERSION
                ),
            )
            cached = None
            if policy.cache_mode not in {"off", "refresh"}:
                cached, _ = cache.read(key)
            if cached is not None:
                result, evidence = cache.get_or_compute(
                    key,
                    lambda cached=cached: cached,
                )
                normalized[role] = result
                cache_evidence[role] = evidence
                continue
            pending[role] = _start_validation_subprocess(
                path=path,
                cache_dir=cache_dir,
                cache_mode=policy.cache_mode,
                key=key,
            )
        if time.monotonic() - started > policy.deadline_seconds:
            raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED")
        diff_started = time.monotonic()
        diff = normalized_model_diff(baseline_model, candidate_model)
        stage_seconds["diff"] = time.monotonic() - diff_started
        for role in ("baseline", "candidate"):
            process = pending.get(role)
            if process is None:
                continue
            remaining = policy.deadline_seconds - (
                time.monotonic() - started
            )
            if remaining <= 0:
                raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED")
            try:
                stdout, stderr = process.communicate(
                    timeout=remaining
                )
            except subprocess.TimeoutExpired as error:
                process.kill()
                process.communicate()
                raise TimeoutError(
                    "EVALUATION_DEADLINE_EXCEEDED"
                ) from error
            if process.returncode != 0:
                raise RuntimeError(
                    "VALIDATION_SUBPROCESS_FAILED:"
                    + stderr.strip()[:800]
                )
            payload = json.loads(stdout)
            result = payload.get("result")
            if result is None:
                result, cache_reason = cache.read(
                    ValidationCacheKey(
                        **payload["key"]
                    )
                )
                if result is None:
                    raise RuntimeError(
                        "VALIDATION_SUBPROCESS_CACHE_RESULT_MISSING:"
                        + cache_reason
                    )
            evidence = payload["evidence"]
            worker_peak = int(payload["peak_rss_bytes"])
            normalized[role] = result
            cache_evidence[role] = evidence
            worker_peak_rss[role] = worker_peak
        stage_seconds["validation"] = (
            time.monotonic() - validation_started
        )
        validation = compare_validation_models(
            baseline_model,
            candidate_model,
            baseline_result=normalized["baseline"],
            candidate_result=normalized["candidate"],
        )
    except Exception as error:
        for process in pending.values():
            if process.poll() is None:
                process.kill()
                process.communicate()
        failed = _execution_failure(
            error,
            policy=policy,
            started=started,
            rss_reader=rss_reader,
        )
        failed["metrics"]["mode"] = "reused_models"
        failed["metrics"]["worker_count"] = 1 + len(pending)
        failed["metrics"]["stage_seconds"] = stage_seconds
        return failed
    wall = time.monotonic() - started
    if wall > policy.deadline_seconds:
        failed = _execution_failure(
            TimeoutError("EVALUATION_DEADLINE_EXCEEDED"),
            policy=policy,
            started=started,
            rss_reader=rss_reader,
        )
        failed["metrics"]["mode"] = "reused_models"
        failed["metrics"]["worker_count"] = 1 + len(pending)
        failed["metrics"]["stage_seconds"] = stage_seconds
        return failed
    peak_rss = max(
        int(rss_reader()),
        _current_process_peak_rss() + sum(worker_peak_rss.values()),
    )
    if peak_rss > policy.rss_limit_bytes:
        return {
            "status": "failed",
            "reason_code": "EVALUATION_RSS_LIMIT_EXCEEDED",
            "results": {},
            "metrics": {
                "mode": "reused_models",
                "worker_count": 1 + len(pending),
                "wall_seconds": wall,
                "stage_seconds": stage_seconds,
                "peak_rss_bytes": peak_rss,
                "rss_limit_bytes": policy.rss_limit_bytes,
            },
        }
    return {
        "status": "passed",
        "reason_code": None,
        "results": {
            "validation": {
                "comparison": validation,
                "cache": cache_evidence,
            },
            "diff": diff,
        },
        "metrics": {
            "mode": "reused_models",
            "worker_count": 1 + len(pending),
            "wall_seconds": wall,
            "stage_seconds": stage_seconds,
            "peak_rss_bytes": peak_rss,
            "rss_limit_bytes": policy.rss_limit_bytes,
        },
    }


def _execute_default_accelerated(
    *,
    damaged_path: Path,
    repaired_path: Path,
    cache_dir: Path,
    policy: EvaluationExecutionPolicy,
    started: float,
    rss_reader: Any,
) -> dict[str, Any]:
    """Validate both files concurrently, then run the dependent full diff."""

    executor = ProcessPoolExecutor(max_workers=2)
    futures = {
        role: executor.submit(
            _cached_single_validation,
            path,
            cache_dir,
            policy.cache_mode,
        )
        for role, path in (
            ("baseline", damaged_path),
            ("candidate", repaired_path),
        )
    }
    normalized: dict[str, dict[str, Any]] = {}
    cache_evidence: dict[str, Any] = {}
    worker_peak_rss: dict[str, int] = {}
    stage_seconds: dict[str, float] = {}
    try:
        validation_started = time.monotonic()
        for role in ("baseline", "candidate"):
            remaining = policy.deadline_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED")
            try:
                result, evidence, worker_peak = futures[role].result(
                    timeout=remaining
                )
            except FuturesTimeoutError as error:
                raise TimeoutError("EVALUATION_DEADLINE_EXCEEDED") from error
            normalized[role] = result
            cache_evidence[role] = evidence
            worker_peak_rss[role] = worker_peak
        stage_seconds["validation"] = time.monotonic() - validation_started
    except Exception as error:
        executor.shutdown(wait=False, cancel_futures=True)
        return _execution_failure(
            error, policy=policy, started=started, rss_reader=rss_reader
        )
    executor.shutdown(wait=False, cancel_futures=True)
    remaining = policy.deadline_seconds - (time.monotonic() - started)
    if remaining <= 0:
        return _execution_failure(
            TimeoutError("EVALUATION_DEADLINE_EXCEEDED"),
            policy=policy,
            started=started,
            rss_reader=rss_reader,
        )
    try:
        baseline = ifcopenshell.open(str(damaged_path))
        candidate = ifcopenshell.open(str(repaired_path))
        validation = compare_validation_models(
            baseline,
            candidate,
            baseline_result=normalized["baseline"],
            candidate_result=normalized["candidate"],
        )
        diff_started = time.monotonic()
        diff = normalized_model_diff(baseline, candidate)
        stage_seconds["diff"] = time.monotonic() - diff_started
    except Exception as error:
        return _execution_failure(
            error, policy=policy, started=started, rss_reader=rss_reader
        )
    wall = time.monotonic() - started
    if wall > policy.deadline_seconds:
        return _execution_failure(
            TimeoutError("EVALUATION_DEADLINE_EXCEEDED"),
            policy=policy,
            started=started,
            rss_reader=rss_reader,
        )
    peak_rss = max(
        int(rss_reader()),
        _current_process_peak_rss() + sum(worker_peak_rss.values()),
    )
    if peak_rss > policy.rss_limit_bytes:
        return {
            "status": "failed",
            "reason_code": "EVALUATION_RSS_LIMIT_EXCEEDED",
            "results": {},
            "metrics": {
                "wall_seconds": wall,
                "peak_rss_bytes": peak_rss,
                "rss_limit_bytes": policy.rss_limit_bytes,
            },
        }
    return {
        "status": "passed",
        "reason_code": None,
        "results": {
            "validation": {
                "comparison": validation,
                "cache": cache_evidence,
            },
            "diff": diff,
        },
        "metrics": {
            "mode": "accelerated",
            "worker_count": 2,
            "wall_seconds": wall,
            "stage_seconds": stage_seconds,
            "peak_rss_bytes": peak_rss,
            "rss_limit_bytes": policy.rss_limit_bytes,
            "worker_peak_rss_bytes": worker_peak_rss,
        },
    }


def _execution_failure(
    error: Exception,
    *,
    policy: EvaluationExecutionPolicy,
    started: float,
    rss_reader: Any,
) -> dict[str, Any]:
    return {
        "status": "failed",
        "reason_code": (
            str(error)
            if isinstance(error, TimeoutError)
            else "EVALUATION_WORKER_FAILED"
        ),
        "error": f"{type(error).__name__}:{error}"[:1000],
        "results": {},
        "metrics": {
            "mode": policy.mode,
            "worker_count": policy.max_workers,
            "wall_seconds": time.monotonic() - started,
            "peak_rss_bytes": int(rss_reader()),
        },
    }


def _cached_validation_worker(
    damaged_path: Path,
    repaired_path: Path,
    cache_dir: Path,
    cache_mode: str,
) -> dict[str, Any]:
    cache = ValidationCache(cache_dir, mode=cache_mode)
    evidence: dict[str, Any] = {}
    normalized: dict[str, dict[str, Any]] = {}
    for role, path in (
        ("baseline", damaged_path),
        ("candidate", repaired_path),
    ):
        key = cache.build_key(
            path,
            validation_policy_version=VALIDATION_POLICY_VERSION,
            diagnostic_normalization_version=DIAGNOSTIC_NORMALIZATION_VERSION,
        )
        result, cache_evidence = cache.get_or_compute(
            key,
            lambda path=path: normalized_validation_result(
                ifcopenshell.open(str(path))
            ),
        )
        normalized[role] = result
        evidence[role] = cache_evidence
    baseline = ifcopenshell.open(str(damaged_path))
    candidate = ifcopenshell.open(str(repaired_path))
    return {
        "comparison": compare_validation_models(
            baseline,
            candidate,
            baseline_result=normalized["baseline"],
            candidate_result=normalized["candidate"],
        ),
        "cache": evidence,
    }


def _cached_single_validation(
    path: Path,
    cache_dir: Path,
    cache_mode: str,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    cache = ValidationCache(cache_dir, mode=cache_mode)
    key = cache.build_key(
        path,
        validation_policy_version=VALIDATION_POLICY_VERSION,
        diagnostic_normalization_version=DIAGNOSTIC_NORMALIZATION_VERSION,
    )
    result, evidence = cache.get_or_compute(
        key,
        lambda: normalized_validation_result(ifcopenshell.open(str(path))),
    )
    return result, evidence, _current_process_peak_rss()


def _cached_single_validation_for_key(
    path: Path,
    cache_dir: Path,
    cache_mode: str,
    key: ValidationCacheKey,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    cache = ValidationCache(cache_dir, mode=cache_mode)
    result, evidence = cache.get_or_compute(
        key,
        lambda: normalized_validation_result(ifcopenshell.open(str(path))),
    )
    return result, evidence, _current_process_peak_rss()


def _start_validation_subprocess(
    *,
    path: Path,
    cache_dir: Path,
    cache_mode: str,
    key: ValidationCacheKey,
) -> subprocess.Popen[str]:
    """Start an isolated validator without multiprocessing spawn/pickle state."""

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "text2ifc_ifc_repair.validation_worker",
            "--ifc",
            str(path),
            "--cache-dir",
            str(cache_dir),
            "--cache-mode",
            cache_mode,
            "--key-json",
            json.dumps(
                key.to_dict(),
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )


def _path_diff_worker(
    damaged_path: Path,
    repaired_path: Path,
) -> dict[str, Any]:
    return normalized_model_diff(
        ifcopenshell.open(str(damaged_path)),
        ifcopenshell.open(str(repaired_path)),
    )


def _process_tree_rss() -> int:
    try:
        import psutil

        process = psutil.Process()
        return int(
            process.memory_info().rss
            + sum(
                child.memory_info().rss
                for child in process.children(recursive=True)
                if child.is_running()
            )
        )
    except Exception:
        return _current_process_peak_rss()


def _current_process_peak_rss() -> int:
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            get_current_process = ctypes.windll.kernel32.GetCurrentProcess
            get_current_process.restype = wintypes.HANDLE
            process = get_current_process()
            get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
            get_memory.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(ProcessMemoryCounters),
                wintypes.DWORD,
            ]
            get_memory.restype = wintypes.BOOL
            if get_memory(
                process, ctypes.byref(counters), counters.cb
            ):
                return int(counters.PeakWorkingSetSize)
        else:
            import resource

            value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return int(value * 1024)
    except Exception:
        pass
    return 0


def evaluate_independent_l1(
    *,
    damaged_ifc_path: Path | str,
    repaired_ifc_path: Path | str,
    changeset: Mapping[str, Any],
    application_result: Mapping[str, Any],
    registry: Any,
    execution_policy: EvaluationExecutionPolicy | None = None,
    validation_cache_dir: Path | str | None = None,
    reopened_models: (
        tuple[
            tuple[Any | None, str | None],
            tuple[Any | None, str | None],
        ]
        | None
    ) = None,
) -> LevelResult:
    """Evaluate actual reopened IFC effects against policy and declared intent."""

    damaged_path = Path(damaged_ifc_path)
    repaired_path = Path(repaired_ifc_path)
    source_hash_before = _path_sha256(damaged_path)
    if reopened_models is None:
        reopened_models = _open_ifc_pair(
            damaged_path,
            repaired_path,
            accelerated=(
                execution_policy is not None
                and execution_policy.mode == "accelerated"
            ),
        )
    (before_model, before_error), (after_model, after_error) = reopened_models
    readable = before_model is not None and after_model is not None
    readability_status = (
        EvaluationStatus.PASSED if readable else EvaluationStatus.NOT_EVALUABLE
    )
    checks = [
        _l1_check(
            check_id="l1.output.readable",
            policy_id=_COMMON_L1_POLICY_ID,
            status=readability_status,
            reason="Both source and repaired IFC artifacts must reopen independently.",
            expected={"before_readable": True, "after_readable": True},
            actual={
                "before_readable": before_model is not None,
                "after_readable": after_model is not None,
                "before_error": before_error,
                "after_error": after_error,
            },
            source_kind="ifc_reopen",
            source_ref="repaired-ifc",
        )
    ]
    checks.append(_source_immutability_check(damaged_path, changeset, source_hash_before))
    if not readable:
        checks.append(
            _l1_check(
                check_id="l1.output.schema",
                policy_id=_COMMON_L1_POLICY_ID,
                status=EvaluationStatus.NOT_EVALUABLE,
                reason="Schema cannot be measured until both IFC artifacts reopen.",
                expected="matching IFC schema",
                actual="unavailable",
                source_kind="ifc_reopen",
                source_ref="repaired-ifc",
            )
        )
        return _l1_level(checks, readable=False)

    assert before_model is not None and after_model is not None
    schema_matches = before_model.schema == after_model.schema
    checks.append(
        _l1_check(
            check_id="l1.output.schema",
            policy_id=_COMMON_L1_POLICY_ID,
            status=(
                EvaluationStatus.PASSED
                if schema_matches
                else EvaluationStatus.FAILED
            ),
            reason="The repaired IFC schema must match the source IFC schema.",
            expected=before_model.schema,
            actual=after_model.schema,
            source_kind="ifc_schema",
            source_ref="repaired-ifc",
        )
    )
    if not schema_matches:
        return _l1_level(checks, readable=True)

    validation = None
    actual_changes = None
    execution_metrics = None
    if execution_policy is not None:
        accelerated = execute_validation_and_diff(
            damaged_ifc_path=damaged_path,
            repaired_ifc_path=repaired_path,
            cache_dir=(
                Path(validation_cache_dir)
                if validation_cache_dir is not None
                else repaired_path.parent / ".validation-cache"
            ),
            policy=execution_policy,
            baseline_model=(
                before_model if validation_cache_dir is not None else None
            ),
            candidate_model=(
                after_model if validation_cache_dir is not None else None
            ),
        )
        execution_metrics = accelerated.get("metrics")
        if accelerated["status"] == "passed":
            validation = accelerated["results"]["validation"]["comparison"]
            validation = {
                **validation,
                "cache": accelerated["results"]["validation"]["cache"],
            }
            actual_changes = accelerated["results"]["diff"]
        else:
            checks.append(
                _l1_check(
                    check_id="l1.output.validation",
                    policy_id=_COMMON_L1_POLICY_ID,
                    status=EvaluationStatus.NOT_EVALUABLE,
                    reason="Accelerated validation/diff must complete within resource bounds.",
                    expected={"status": "passed"},
                    actual=accelerated,
                    source_kind="evaluation_execution",
                    source_ref="damaged-to-repaired",
                )
            )
            checks.extend(
                _comparison_not_evaluable_checks(
                    ComparisonIntegrityError(
                        f"{accelerated['reason_code']}: accelerated evaluation failed"
                    )
                )
            )
            return _l1_level(checks, readable=True)
    try:
        if validation is None:
            validation = compare_validation_models(before_model, after_model)
    except Exception as error:
        checks.append(
            _l1_check(
                check_id="l1.output.validation",
                policy_id=_COMMON_L1_POLICY_ID,
                status=EvaluationStatus.NOT_EVALUABLE,
                reason=(
                    "IfcOpenShell validation must complete before the repaired "
                    "IFC can be published."
                ),
                expected={"new_diagnostic_count": 0},
                actual={
                    "error_type": type(error).__name__,
                    "error": str(error)[:512],
                },
                source_kind="ifcopenshell_validation",
                source_ref="damaged-to-repaired",
            )
        )
    else:
        checks.append(
            _l1_check(
                check_id="l1.output.validation",
                policy_id=_COMMON_L1_POLICY_ID,
                status=(
                    EvaluationStatus.PASSED
                    if validation["status"] == "passed"
                    else EvaluationStatus.FAILED
                ),
                reason=(
                    "The repaired IFC must not introduce IfcOpenShell "
                    "validation diagnostics beyond the damaged baseline."
                ),
                expected={"new_diagnostic_count": 0},
                actual={
                    **_bounded_validation_evidence(validation),
                    **(
                        {"execution": execution_metrics}
                        if execution_metrics is not None
                        else {}
                    ),
                    **(
                        {"cache": validation["cache"]}
                        if "cache" in validation
                        else {}
                    ),
                },
                source_kind="ifcopenshell_validation",
                source_ref="damaged-to-repaired",
            )
        )

    try:
        if actual_changes is None:
            actual_changes = normalized_model_diff(before_model, after_model)
    except ComparisonIntegrityError as error:
        checks.extend(_comparison_not_evaluable_checks(error))
        return _l1_level(checks, readable=True)
    operation_contexts = _operation_l1_contexts(
        before_model=before_model,
        after_model=after_model,
        changeset=changeset,
        application_result=application_result,
        registry=registry,
    )
    checks.extend(
        _scope_checks(
            actual_changes=actual_changes,
            changeset=changeset,
            operation_contexts=operation_contexts,
            before_model=before_model,
            after_model=after_model,
        )
    )
    measurement_id_counts = Counter(
        str(check_id)
        for context in operation_contexts
        for check_id in context["report"].get("l1_checks", {})
    )
    duplicate_measurement_ids = frozenset(
        check_id
        for check_id, count in measurement_id_counts.items()
        if count > 1
    )
    for context in operation_contexts:
        checks.extend(
            _operation_measurement_checks(
                context,
                qualified_check_ids=duplicate_measurement_ids,
            )
        )
    return _l1_level(checks, readable=True)


def _comparison_not_evaluable_checks(
    error: ComparisonIntegrityError,
) -> list[CheckResult]:
    error_text = str(error)
    error_code = error_text.split(":", 1)[0] or type(error).__name__
    return [
        _l1_check(
            check_id=check_id,
            policy_id=_COMMON_L1_POLICY_ID,
            status=EvaluationStatus.NOT_EVALUABLE,
            reason=(
                "The blocking global preservation comparator did not produce "
                "complete trustworthy evidence."
            ),
            expected="complete fail-closed global preservation evidence",
            actual={"error_code": error_code, "error": error_text},
            source_kind="ifc_actual_diff",
            source_ref="reopened-ifc",
        )
        for check_id in _SCOPE_L1_CHECK_IDS
    ]


def _open_ifc(path: Path) -> tuple[Any | None, str | None]:
    try:
        return ifcopenshell.open(str(path)), None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def _open_ifc_pair(
    damaged_path: Path,
    repaired_path: Path,
    *,
    accelerated: bool,
) -> tuple[tuple[Any | None, str | None], tuple[Any | None, str | None]]:
    if not accelerated:
        return _open_ifc(damaged_path), _open_ifc(repaired_path)
    with ThreadPoolExecutor(
        max_workers=2,
        thread_name_prefix="ifc-reopen",
    ) as executor:
        baseline = executor.submit(_open_ifc, damaged_path)
        candidate = executor.submit(_open_ifc, repaired_path)
        return baseline.result(), candidate.result()


def _path_sha256(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _bounded_validation_evidence(
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": validation.get("schema_version"),
        "status": validation.get("status"),
        "baseline_status": validation.get("baseline_status"),
        "baseline_diagnostic_count": validation.get(
            "baseline_diagnostic_count"
        ),
        "candidate_diagnostic_count": validation.get(
            "candidate_diagnostic_count"
        ),
        "new_diagnostic_count": validation.get("new_diagnostic_count"),
        "resolved_diagnostic_count": validation.get(
            "resolved_diagnostic_count"
        ),
        "new_diagnostics": [
            {
                "signature": item.get("signature"),
                "attribute": item.get("attribute"),
                "instance_class": item.get("instance_class"),
                "instance_identity": item.get("instance_identity"),
            }
            for item in tuple(validation.get("new_diagnostics", ()))[:8]
        ],
        "new_diagnostics_truncated": validation.get(
            "new_diagnostics_truncated"
        ),
    }


def _source_immutability_check(
    damaged_path: Path,
    changeset: Mapping[str, Any],
    source_hash_before: str | None,
) -> CheckResult:
    source_hash_after = _path_sha256(damaged_path)
    expected = str(changeset.get("base_model_fingerprint", ""))
    passed = bool(expected) and source_hash_before == expected == source_hash_after
    return _l1_check(
        check_id="l1.source.immutable",
        policy_id=_COMMON_L1_POLICY_ID,
        status=EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED,
        reason="The source IFC must remain bound to the declared base fingerprint.",
        expected=expected,
        actual={"before": source_hash_before, "after": source_hash_after},
        source_kind="source_fingerprint",
        source_ref=str(damaged_path),
    )


def _operation_l1_contexts(
    *,
    before_model: Any,
    after_model: Any,
    changeset: Mapping[str, Any],
    application_result: Mapping[str, Any],
    registry: Any,
) -> list[dict[str, Any]]:
    applications = {
        str(item.get("operation_id")): item
        for item in application_result.get("operations", ())
    }
    contexts = []
    for operation in changeset.get("operations", ()):
        application = applications.get(str(operation.get("operation_id")), {})
        changes = application.get("changes", {})
        role_ids, id_roles, role_entries = _application_role_bindings(changes)
        report = registry.dispatch(
            "comparison_adapter",
            operation,
            before_model=before_model,
            after_model=after_model,
            application=changes,
            batch_operations=tuple(changeset.get("operations", ())),
            batch_applications=applications,
            role_mapping=role_ids,
        )
        binding_errors = _application_role_binding_errors(
            role_entries=role_entries,
            id_roles=id_roles,
            authorization=report.get("authorization", {}),
        )
        target_ids = {
            str(value)
            for key, value in operation.get("target", {}).items()
            if key.endswith("global_id") and value
        }
        contexts.append(
            {
                "operation": operation,
                "report": report,
                "authorization": report.get("authorization", {}),
                "role_ids": role_ids,
                "id_roles": id_roles,
                "binding_errors": binding_errors,
                "target_ids": target_ids,
            }
        )
    return contexts


def _application_role_bindings(
    changes: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, list[str]], dict[tuple[str, str], list[str]]]:
    role_entries: dict[tuple[str, str], list[str]] = {}
    id_roles: dict[str, list[str]] = {}
    for change_kind in ("created", "modified", "removed"):
        for item in changes.get(change_kind, ()):
            role = str(item.get("role", ""))
            global_id = str(item.get("global_id", ""))
            if role and global_id:
                role_entries.setdefault((change_kind, role), []).append(global_id)
                id_roles.setdefault(global_id, []).append(role)
    identifiers_by_role: dict[str, list[str]] = {}
    for (_, role), identifiers in role_entries.items():
        identifiers_by_role.setdefault(role, []).extend(identifiers)
    role_ids = {
        role: identifiers[0]
        for role, identifiers in identifiers_by_role.items()
        if len(identifiers) == 1
    }
    return role_ids, id_roles, role_entries


def _application_role_binding_errors(
    *,
    role_entries: Mapping[tuple[str, str], list[str]],
    id_roles: Mapping[str, list[str]],
    authorization: Mapping[str, Any],
) -> tuple[str, ...]:
    errors = [
        f"role {change_kind}.{role} has {len(identifiers)} bindings"
        for (change_kind, role), identifiers in role_entries.items()
        if len(identifiers) != 1
    ]
    identifiers_by_role: dict[str, list[str]] = {}
    for (_, role), identifiers in role_entries.items():
        identifiers_by_role.setdefault(role, []).extend(identifiers)
    errors.extend(
        f"role {role} has {len(identifiers)} operation bindings"
        for role, identifiers in identifiers_by_role.items()
        if len(identifiers) != 1
    )
    errors.extend(
        f"GlobalId {global_id} has multiple roles"
        for global_id, roles in id_roles.items()
        if len(set(roles)) != 1
    )
    for change_kind, roles in authorization.get("required_roles", {}).items():
        for role in roles:
            identifiers = role_entries.get((str(change_kind), str(role)), ())
            if len(identifiers) != 1:
                errors.append(
                    f"required role {change_kind}.{role} has {len(identifiers)} bindings"
                )
    return tuple(sorted(set(errors)))


def _scope_checks(
    *,
    actual_changes: Mapping[str, list[dict[str, Any]]],
    changeset: Mapping[str, Any],
    operation_contexts: list[dict[str, Any]],
    before_model: Any,
    after_model: Any,
) -> list[CheckResult]:
    decisions: dict[tuple[str, str], tuple[bool, str]] = {}
    for change_kind in ("created", "modified", "removed"):
        for fact in actual_changes[change_kind]:
            decisions[(change_kind, fact["global_id"])] = _authorize_actual_change(
                fact=fact,
                changeset=changeset,
                operation_contexts=operation_contexts,
                before_model=before_model,
                after_model=after_model,
            )

    root_groups = {
        _SCOPE_L1_CHECK_IDS[0]: [
            item for item in actual_changes["created"] if not item["is_relationship"]
        ],
        _SCOPE_L1_CHECK_IDS[1]: [
            item for item in actual_changes["modified"] if not item["is_relationship"]
        ],
        _SCOPE_L1_CHECK_IDS[2]: [
            item for item in actual_changes["removed"] if not item["is_relationship"]
        ],
        _SCOPE_L1_CHECK_IDS[3]: [
            item
            for kind in ("created", "modified", "removed")
            for item in actual_changes[kind]
            if item["is_relationship"]
        ],
    }
    checks = []
    for check_id, facts in root_groups.items():
        evidence = _actual_change_evidence(check_id, facts, decisions)
        unauthorized = [
            fact
            for fact in facts
            if not decisions[(fact["change_kind"], fact["global_id"])][0]
        ]
        checks.append(
            _required_check(
                check_id=check_id,
                policy_id=_COMMON_L1_POLICY_ID,
                status=(
                    EvaluationStatus.FAILED
                    if unauthorized
                    else EvaluationStatus.PASSED
                ),
                reason="Every actual IFC effect must be authorized by policy and declared scope.",
                evidence=evidence,
            )
        )
    return checks


def _authorize_actual_change(
    *,
    fact: Mapping[str, Any],
    changeset: Mapping[str, Any],
    operation_contexts: list[dict[str, Any]],
    before_model: Any,
    after_model: Any,
) -> tuple[bool, str]:
    global_id = str(fact["global_id"])
    if global_id in {str(item) for item in changeset.get("scope", {}).get("forbidden_ids", ())}:
        return False, "actual effect touches a forbidden GlobalId"
    candidates = [
        context for context in operation_contexts if global_id in context["id_roles"]
    ]
    if len(candidates) != 1:
        if fact["is_relationship"] and candidates:
            return _authorize_shared_relation(
                fact=fact,
                contexts=candidates,
                changeset=changeset,
                before_model=before_model,
                after_model=after_model,
            )
        if fact["change_kind"] == "modified" and candidates:
            return _authorize_shared_modified_root(
                fact=fact,
                contexts=candidates,
                changeset=changeset,
            )
        return False, "actual effect has no unique Applicator role binding"
    context = candidates[0]
    if context["binding_errors"]:
        return False, "; ".join(context["binding_errors"])
    declared_targets = {
        str(item) for item in changeset.get("scope", {}).get("target_ids", ())
    }
    if not context["target_ids"] or not context["target_ids"].issubset(declared_targets):
        return False, "operation target is outside the ChangeSet declared scope"
    roles = sorted(set(context["id_roles"][global_id]))
    if len(roles) != 1:
        return False, "Applicator assigned multiple roles to one actual effect"
    role = roles[0]
    allowed = context["authorization"].get(str(fact["change_kind"]), {})
    if allowed.get(role) != fact["ifc_class"]:
        return False, "Registry policy does not authorize this role/class/effect"
    if fact["is_relationship"]:
        return _authorize_relation(
            fact=fact,
            role=role,
            context=context,
            before_model=before_model,
            after_model=after_model,
        )
    return True, "authorized by Registry policy and ChangeSet operation scope"


def _authorize_shared_modified_root(
    *,
    fact: Mapping[str, Any],
    contexts: list[dict[str, Any]],
    changeset: Mapping[str, Any],
) -> tuple[bool, str]:
    declared_targets = {
        str(item) for item in changeset.get("scope", {}).get("target_ids", ())
    }
    roles = set()
    for context in contexts:
        if context["binding_errors"]:
            return False, "; ".join(context["binding_errors"])
        if not context["target_ids"] or not context["target_ids"].issubset(
            declared_targets
        ):
            return False, "operation target is outside the ChangeSet declared scope"
        context_roles = sorted(set(context["id_roles"][str(fact["global_id"])]))
        if len(context_roles) != 1:
            return False, "Applicator assigned multiple roles to one actual effect"
        role = context_roles[0]
        roles.add(role)
        allowed = context["authorization"].get("modified", {})
        if allowed.get(role) != fact["ifc_class"]:
            return False, "Registry policy does not authorize this role/class/effect"
    if len(roles) != 1:
        return False, "shared modified root has inconsistent operation roles"
    return True, "authorized shared modified root across declared operations"


def _authorize_shared_relation(
    *,
    fact: Mapping[str, Any],
    contexts: list[dict[str, Any]],
    changeset: Mapping[str, Any],
    before_model: Any,
    after_model: Any,
) -> tuple[bool, str]:
    """Authorize one IFC relationship changed by multiple declared operations."""

    declared_targets = {
        str(item) for item in changeset.get("scope", {}).get("target_ids", ())
    }
    specifications = []
    roles = set()
    for context in contexts:
        if context["binding_errors"]:
            return False, "; ".join(context["binding_errors"])
        if not context["target_ids"] or not context["target_ids"].issubset(
            declared_targets
        ):
            return False, "operation target is outside the ChangeSet declared scope"
        context_roles = sorted(set(context["id_roles"][str(fact["global_id"])]))
        if len(context_roles) != 1:
            return False, "Applicator assigned multiple roles to one actual effect"
        role = context_roles[0]
        roles.add(role)
        allowed = context["authorization"].get(str(fact["change_kind"]), {})
        if allowed.get(role) != fact["ifc_class"]:
            return False, "Registry policy does not authorize this role/class/effect"
        specification = context["authorization"].get("relations", {}).get(role)
        if not specification or specification.get("ifc_class") != fact["ifc_class"]:
            return False, "Registry policy does not authorize the relationship role"
        specifications.append((context, specification))
    if len(roles) != 1:
        return False, "shared relationship is assigned inconsistent operation roles"

    model = before_model if fact["change_kind"] == "removed" else after_model
    try:
        relation = model.by_guid(str(fact["global_id"]))
    except RuntimeError:
        return False, "actual relationship cannot be reopened by GlobalId"

    expected_added: set[str] = set()
    for context, specification in specifications:
        for attribute, endpoint_role in specification.get("endpoints", {}).items():
            endpoint = getattr(relation, attribute, None)
            actual_id = str(getattr(endpoint, "GlobalId", ""))
            expected_id = (
                next(iter(context["target_ids"]), "")
                if endpoint_role == "target"
                else context["role_ids"].get(endpoint_role, "")
            )
            if not expected_id or actual_id != expected_id:
                return False, f"relationship endpoint {attribute} is outside declared roles"
        for role_name in specification.get("added_endpoint_roles", ()):
            expected_id = context["role_ids"].get(role_name, "")
            if expected_id:
                expected_added.add(expected_id)

    after_ids = _direct_root_ids(relation)
    if fact["change_kind"] == "modified":
        before_relation = before_model.by_guid(str(fact["global_id"]))
        actual_added = after_ids - _direct_root_ids(before_relation)
        if actual_added != expected_added:
            return False, "shared relationship endpoint delta exceeds declared operations"
    elif fact["change_kind"] == "created" and not expected_added.issubset(after_ids):
        return False, "created relationship omits declared generated roles"
    return True, "authorized shared relationship delta across declared operations"


def _authorize_relation(
    *,
    fact: Mapping[str, Any],
    role: str,
    context: Mapping[str, Any],
    before_model: Any,
    after_model: Any,
) -> tuple[bool, str]:
    specification = context["authorization"].get("relations", {}).get(role)
    if not specification or specification.get("ifc_class") != fact["ifc_class"]:
        return False, "Registry policy does not authorize the relationship role"
    model = before_model if fact["change_kind"] == "removed" else after_model
    try:
        relation = model.by_guid(str(fact["global_id"]))
    except RuntimeError:
        return False, "actual relationship cannot be reopened by GlobalId"
    for attribute, endpoint_role in specification.get("endpoints", {}).items():
        endpoint = getattr(relation, attribute, None)
        actual_id = str(getattr(endpoint, "GlobalId", ""))
        expected_id = (
            next(iter(context["target_ids"]), "")
            if endpoint_role == "target"
            else context["role_ids"].get(endpoint_role, "")
        )
        if not expected_id or actual_id != expected_id:
            return False, f"relationship endpoint {attribute} is outside declared roles"
    added_roles = tuple(specification.get("added_endpoint_roles", ()))
    if added_roles:
        expected_added = {context["role_ids"].get(role_name, "") for role_name in added_roles}
        expected_added.discard("")
        after_ids = _direct_root_ids(relation)
        if fact["change_kind"] == "modified":
            before_relation = before_model.by_guid(str(fact["global_id"]))
            actual_added = after_ids - _direct_root_ids(before_relation)
            if actual_added != expected_added:
                return False, "relationship endpoint delta exceeds declared generated roles"
        elif not expected_added.issubset(after_ids):
            return False, "created relationship omits a declared generated role"
    return True, "authorized relationship role and endpoints"


def _direct_root_ids(entity: Any) -> set[str]:
    identifiers: set[str] = set()
    for index in range(len(entity)):
        value = entity[index]
        children = value if isinstance(value, (tuple, list)) else (value,)
        for child in children:
            global_id = getattr(child, "GlobalId", None)
            if global_id:
                identifiers.add(str(global_id))
    return identifiers


def _actual_change_evidence(
    check_id: str,
    facts: list[dict[str, Any]],
    decisions: Mapping[tuple[str, str], tuple[bool, str]],
) -> tuple[EvidenceFact, ...]:
    if not facts:
        return (
            _evidence(
                fact_id=f"{check_id}.evidence",
                source_kind="ifc_actual_diff",
                source_ref="reopened-ifc",
                expected="no unexplained effects",
                actual={"changes": []},
            ),
        )
    return tuple(
        _evidence(
            fact_id=f"{check_id}.{index:04d}",
            source_kind="ifc_actual_diff",
            source_ref=f"ifc-guid:{fact['global_id']}",
            expected="policy-and-scope-authorized effect",
            actual={
                **_compact_actual_change(fact),
                "authorized": decisions[(fact["change_kind"], fact["global_id"])][0],
                "authorization_reason": decisions[(fact["change_kind"], fact["global_id"])][1],
            },
        )
        for index, fact in enumerate(facts)
    )


def _compact_actual_change(fact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "change_kind": fact["change_kind"],
        "global_id": fact["global_id"],
        "ifc_class": fact["ifc_class"],
        "is_relationship": fact["is_relationship"],
        "before": _compact_snapshot(fact.get("before")),
        "after": _compact_snapshot(fact.get("after")),
    }


def _compact_snapshot(snapshot: Any) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    canonical = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    attributes = snapshot.get("attributes", {})
    attribute_bytes = json.dumps(
        attributes,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "ifc_class": snapshot.get("ifc_class"),
        "name": snapshot.get("name"),
        "placement": snapshot.get("placement"),
        "containers": snapshot.get("containers"),
        "types": snapshot.get("types"),
        "geometry": snapshot.get("geometry"),
        "attribute_sha256": "sha256:" + hashlib.sha256(attribute_bytes).hexdigest(),
        "snapshot_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def _operation_measurement_checks(
    context: Mapping[str, Any],
    *,
    qualified_check_ids: frozenset[str] = frozenset(),
) -> list[CheckResult]:
    authorization = context["authorization"]
    policy_id = str(authorization.get("policy_id", "l1.operation"))
    operation_id = str(context["operation"].get("operation_id", "operation"))
    checks = []
    for check_id, measurement in sorted(context["report"].get("l1_checks", {}).items()):
        effective_check_id = str(check_id)
        if effective_check_id in qualified_check_ids:
            effective_check_id = f"{effective_check_id}.{operation_id}"
        checks.append(
            _l1_check(
                check_id=effective_check_id,
                policy_id=policy_id,
                status=EvaluationStatus(str(measurement["status"])),
                reason=str(measurement["reason"]),
                expected=measurement.get("expected"),
                actual=measurement.get("actual"),
                source_kind="operation_measurement",
                source_ref=f"operation:{operation_id}",
            )
        )
    return checks


def _l1_check(
    *,
    check_id: str,
    policy_id: str,
    status: EvaluationStatus,
    reason: str,
    expected: Any,
    actual: Any,
    source_kind: str,
    source_ref: str,
) -> CheckResult:
    return _required_check(
        check_id=check_id,
        policy_id=policy_id,
        status=status,
        reason=reason,
        evidence=(
            _evidence(
                fact_id=f"{check_id}.evidence",
                source_kind=source_kind,
                source_ref=source_ref,
                expected=expected,
                actual=actual,
            ),
        ),
    )


def _required_check(
    *,
    check_id: str,
    policy_id: str,
    status: EvaluationStatus,
    reason: str,
    evidence: tuple[EvidenceFact, ...],
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        policy_id=policy_id,
        applicability="required",
        mandatory=True,
        status=status,
        reason=reason,
        evidence=evidence,
    )


def _evidence(
    *,
    fact_id: str,
    source_kind: str,
    source_ref: str,
    expected: Any,
    actual: Any,
) -> EvidenceFact:
    evidence_size = len(
        json.dumps(
            {"expected": expected, "actual": actual},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )
    if evidence_size > _L1_EVIDENCE_VALUE_MAX_BYTES:
        raise EvaluationContractError(
            "invalid_schema",
            f"L1 evidence {fact_id} exceeds {_L1_EVIDENCE_VALUE_MAX_BYTES} bytes",
        )
    return EvidenceFact(
        fact_id=fact_id,
        source_kind=source_kind,
        source_ref=source_ref,
        expected_state="available",
        actual_state="available",
        expected_value=expected,
        actual_value=actual,
        provenance=(source_kind, source_ref),
    )


def _l1_level(checks: Iterable[CheckResult], *, readable: bool) -> LevelResult:
    ordered = tuple(sorted(checks, key=lambda item: item.check_id))
    if len({check.check_id for check in ordered}) != len(ordered):
        raise EvaluationContractError("invalid_schema", "duplicate L1 check identifier")
    return aggregate_level(
        level="L1",
        checks=ordered,
        reason="Independent reopened IFC L1 authorization and measurement.",
        evidence=(
            _evidence(
                fact_id="l1.summary",
                source_kind="ifc_actual_diff",
                source_ref="reopened-ifc",
                expected="readable policy-authorized physical repair",
                actual={"readable": readable, "check_count": len(ordered)},
            ),
        ),
    )


def aggregate_status(
    results: Iterable[CheckResult | LevelResult | OperationEvaluation],
) -> EvaluationStatus:
    """Return the total, order-independent status of mandatory children."""

    statuses: list[EvaluationStatus] = []
    for result in results:
        if isinstance(result, CheckResult) and not result.mandatory:
            continue
        if isinstance(result, OperationEvaluation) and not result.mandatory:
            continue
        if result.status is EvaluationStatus.NOT_REQUIRED:
            continue
        statuses.append(result.status)
    if not statuses:
        return EvaluationStatus.PASSED
    return max(statuses, key=_STATUS_PRECEDENCE.__getitem__)


def aggregate_level(
    *,
    level: str,
    checks: Iterable[CheckResult],
    reason: str,
    evidence: Iterable[EvidenceFact],
) -> LevelResult:
    frozen_checks = tuple(checks)
    return LevelResult(
        level=level,
        status=aggregate_status(frozen_checks),
        reason=reason,
        evidence=tuple(evidence),
        checks=frozen_checks,
    )


def make_l3_not_required(
    *,
    checks: Iterable[CheckResult],
    reason: str,
    evidence: Iterable[EvidenceFact],
) -> LevelResult:
    """Construct the disclosed but non-gating v1.1 L3 boundary."""

    return LevelResult(
        level="L3",
        status=EvaluationStatus.NOT_REQUIRED,
        reason=reason,
        evidence=tuple(evidence),
        checks=tuple(checks),
    )


def aggregate_operation(
    *,
    operation_id: str,
    operation_type: str,
    mandatory: bool,
    policy_id: str,
    policy_version: str,
    levels: Iterable[LevelResult],
    reason: str,
    evidence: Iterable[EvidenceFact],
) -> OperationEvaluation:
    frozen_levels = tuple(levels)
    gating_levels = tuple(
        level for level in frozen_levels if level.level in {"L1", "L2"}
    )
    return OperationEvaluation(
        operation_id=operation_id,
        operation_type=operation_type,
        mandatory=mandatory,
        policy_id=policy_id,
        policy_version=policy_version,
        status=aggregate_status(gating_levels),
        reason=reason,
        evidence=tuple(evidence),
        levels=frozen_levels,
    )


def aggregate_repair(
    *,
    policy_version: str,
    application: CheckResult,
    preservation: CheckResult,
    operations: Iterable[OperationEvaluation],
    reason: str,
    evidence: Iterable[EvidenceFact],
    diagnostic_artifact_retained: bool,
) -> RepairEvaluation:
    for gate_name, gate in (("application", application), ("preservation", preservation)):
        if not gate.mandatory or gate.applicability != "required":
            raise EvaluationContractError(
                "invalid_status_transition",
                f"{gate_name} must be a mandatory required check",
            )
    frozen_operations = tuple(operations)
    status = aggregate_status((application, preservation, *frozen_operations))
    complete = status is EvaluationStatus.PASSED
    return RepairEvaluation(
        schema_version=EVALUATION_SCHEMA_VERSION,
        policy_version=policy_version,
        status=status,
        reason=reason,
        evidence=tuple(evidence),
        application=application,
        preservation=preservation,
        operations=frozen_operations,
        complete_repair_success=complete,
        successful_artifact_publishable=complete,
        diagnostic_artifact_retained=diagnostic_artifact_retained,
    )


def evaluation_to_dict(value: RepairEvaluation) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "policy_version": value.policy_version,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
        "application": _check_to_dict(value.application),
        "preservation": _check_to_dict(value.preservation),
        "operations": [_operation_to_dict(item) for item in value.operations],
        "complete_repair_success": value.complete_repair_success,
        "successful_artifact_publishable": value.successful_artifact_publishable,
        "diagnostic_artifact_retained": value.diagnostic_artifact_retained,
    }


def evaluation_to_json(value: RepairEvaluation) -> str:
    return json.dumps(
        evaluation_to_dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def evaluation_from_dict(value: Mapping[str, Any]) -> RepairEvaluation:
    payload = dict(value)
    validate_evaluation_report(payload, semantic=False)
    application = _check_from_dict(payload["application"])
    preservation = _check_from_dict(payload["preservation"])
    operations = tuple(_operation_from_dict(item) for item in payload["operations"])
    result = aggregate_repair(
        policy_version=str(payload["policy_version"]),
        application=application,
        preservation=preservation,
        operations=operations,
        reason=str(payload["reason"]),
        evidence=tuple(_evidence_from_dict(item) for item in payload["evidence"]),
        diagnostic_artifact_retained=bool(payload["diagnostic_artifact_retained"]),
    )
    if evaluation_to_dict(result) != payload:
        raise EvaluationContractError(
            "invalid_status_transition",
            "serialized aggregate fields do not match their mandatory children",
        )
    return result


def validate_evaluation_report(
    value: Mapping[str, Any], *, semantic: bool = True
) -> None:
    payload = dict(value)
    _validate_mandatory_invariants(payload)
    if _contains_empty_evidence(payload):
        raise EvaluationContractError(
            "missing_evidence", "report contains an empty evidence collection"
        )
    errors = sorted(
        _validator().iter_errors(payload),
        key=lambda error: [str(item) for item in error.absolute_path],
    )
    if errors:
        raise EvaluationContractError("invalid_schema", errors[0].message)
    if semantic:
        evaluation_from_dict(payload)


def read_evaluation_report(
    path: Path | str,
) -> RepairEvaluation | LegacyEvaluationProjection:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version == EVALUATION_SCHEMA_VERSION:
        return evaluation_from_dict(payload)
    if schema_version == LEGACY_EVALUATION_SCHEMA_VERSION:
        return LegacyEvaluationProjection(
            schema_version=LEGACY_EVALUATION_SCHEMA_VERSION,
            original_report=payload,
            l1_assurance=EvaluationStatus.NOT_EVALUABLE,
            l2_assurance=EvaluationStatus.NOT_EVALUABLE,
            complete_repair_success=False,
            successful_artifact_publishable=False,
            assurance_error_code="legacy_assurance_unavailable",
        )
    raise EvaluationContractError(
        "invalid_schema", f"unsupported evaluation schema: {schema_version!r}"
    )


def _validator() -> Draft202012Validator:
    schema = json.loads(EVALUATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _contains_empty_evidence(value: Any) -> bool:
    if isinstance(value, Mapping):
        if "evidence" in value and value["evidence"] == []:
            return True
        return any(_contains_empty_evidence(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_empty_evidence(child) for child in value)
    return False


def _validate_mandatory_invariants(payload: Mapping[str, Any]) -> None:
    gates = (payload.get("application"), payload.get("preservation"))
    for gate in gates:
        if isinstance(gate, Mapping) and (
            gate.get("applicability") != "required" or gate.get("mandatory") is not True
        ):
            raise EvaluationContractError(
                "invalid_status_transition",
                "application and preservation must be mandatory required checks",
            )
    checks = [gate for gate in gates if isinstance(gate, Mapping)]
    for operation in payload.get("operations", ()):
        if not isinstance(operation, Mapping):
            continue
        for level in operation.get("levels", ()):
            if isinstance(level, Mapping):
                checks.extend(
                    check
                    for check in level.get("checks", ())
                    if isinstance(check, Mapping)
                )
    for check in checks:
        applicability = check.get("applicability")
        mandatory = check.get("mandatory")
        status = check.get("status")
        valid = (
            (applicability == "required" and mandatory is True)
            or (applicability == "informational" and mandatory is False)
            or (
                applicability == "conditional"
                and mandatory is (status != EvaluationStatus.NOT_REQUIRED.value)
            )
        )
        if not valid:
            raise EvaluationContractError(
                "invalid_status_transition",
                "check mandatory state does not match applicability and status",
            )


def _evidence_to_dict(value: EvidenceFact) -> dict[str, Any]:
    return {
        "fact_id": value.fact_id,
        "source_kind": value.source_kind,
        "source_ref": value.source_ref,
        "expected_state": value.expected_state,
        "actual_state": value.actual_state,
        "expected_value": _json_safe_copy(value.expected_value),
        "actual_value": _json_safe_copy(value.actual_value),
        "provenance": list(value.provenance),
    }


def _check_to_dict(value: CheckResult) -> dict[str, Any]:
    return {
        "check_id": value.check_id,
        "policy_id": value.policy_id,
        "applicability": value.applicability,
        "mandatory": value.mandatory,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
    }


def _level_to_dict(value: LevelResult) -> dict[str, Any]:
    return {
        "level": value.level,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
        "checks": [_check_to_dict(item) for item in value.checks],
    }


def _operation_to_dict(value: OperationEvaluation) -> dict[str, Any]:
    return {
        "operation_id": value.operation_id,
        "operation_type": value.operation_type,
        "mandatory": value.mandatory,
        "policy_id": value.policy_id,
        "policy_version": value.policy_version,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
        "levels": [_level_to_dict(item) for item in value.levels],
    }


def _evidence_from_dict(value: Mapping[str, Any]) -> EvidenceFact:
    return EvidenceFact(
        fact_id=str(value["fact_id"]),
        source_kind=str(value["source_kind"]),
        source_ref=str(value["source_ref"]),
        expected_state=str(value["expected_state"]),
        actual_state=str(value["actual_state"]),
        expected_value=value["expected_value"],
        actual_value=value["actual_value"],
        provenance=tuple(str(item) for item in value["provenance"]),
    )


def _check_from_dict(value: Mapping[str, Any]) -> CheckResult:
    return CheckResult(
        check_id=str(value["check_id"]),
        policy_id=str(value["policy_id"]),
        applicability=str(value["applicability"]),
        mandatory=bool(value["mandatory"]),
        status=EvaluationStatus(str(value["status"])),
        reason=str(value["reason"]),
        evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
    )


def _level_from_dict(value: Mapping[str, Any]) -> LevelResult:
    checks = tuple(_check_from_dict(item) for item in value["checks"])
    if value["level"] == "L3":
        result = make_l3_not_required(
            checks=checks,
            reason=str(value["reason"]),
            evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
        )
    else:
        result = aggregate_level(
            level=str(value["level"]),
            checks=checks,
            reason=str(value["reason"]),
            evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
        )
    _require_aggregate_match(result.status, value["status"], scope="level")
    return result


def _operation_from_dict(value: Mapping[str, Any]) -> OperationEvaluation:
    result = aggregate_operation(
        operation_id=str(value["operation_id"]),
        operation_type=str(value["operation_type"]),
        mandatory=bool(value["mandatory"]),
        policy_id=str(value["policy_id"]),
        policy_version=str(value["policy_version"]),
        levels=tuple(_level_from_dict(item) for item in value["levels"]),
        reason=str(value["reason"]),
        evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
    )
    _require_aggregate_match(result.status, value["status"], scope="operation")
    return result


def _require_aggregate_match(
    actual: EvaluationStatus, serialized: Any, *, scope: str
) -> None:
    if actual.value != serialized:
        raise EvaluationContractError(
            "invalid_status_transition",
            f"{scope} status does not match its mandatory children",
        )


def _json_safe_copy(value: Any) -> Any:
    """Detach arbitrary evidence values while retaining canonical JSON types."""

    if isinstance(value, Mapping):
        return {str(key): _json_safe_copy(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_safe_copy(child) for child in value]
    return value


__all__ = [
    "COMMON_L1_CHECK_IDS",
    "aggregate_level",
    "aggregate_operation",
    "aggregate_repair",
    "aggregate_status",
    "evaluation_from_dict",
    "evaluate_independent_l1",
    "evaluation_to_dict",
    "evaluation_to_json",
    "make_l3_not_required",
    "read_evaluation_report",
    "validate_evaluation_report",
]
