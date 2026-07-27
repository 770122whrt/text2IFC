"""Run clean-process Comparator 0.2 performance acceptance."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import ifcopenshell

from text2ifc_ifc_repair.compare import profile_normalized_model_diff
from text2ifc_text.splits import atomic_write_text


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _peak_rss_bytes() -> int:
    if os.name == "nt":
        from ctypes import wintypes

        size_t = ctypes.c_size_t

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", size_t),
                ("WorkingSetSize", size_t),
                ("QuotaPeakPagedPoolUsage", size_t),
                ("QuotaPagedPoolUsage", size_t),
                ("QuotaPeakNonPagedPoolUsage", size_t),
                ("QuotaNonPagedPoolUsage", size_t),
                ("PagefileUsage", size_t),
                ("PeakPagefileUsage", size_t),
                ("PrivateUsage", size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_current_process.argtypes = []
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        get_process_memory_info.restype = wintypes.BOOL
        process = get_current_process()
        succeeded = get_process_memory_info(
            process,
            ctypes.byref(counters),
            counters.cb,
        )
        if not succeeded:
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)

    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _worker(before: Path, after: Path, timeout_seconds: float) -> dict[str, Any]:
    started = time.perf_counter()
    before_model = ifcopenshell.open(str(before))
    after_model = ifcopenshell.open(str(after))
    open_seconds = time.perf_counter() - started
    profiled = profile_normalized_model_diff(
        before_model,
        after_model,
        timeout_seconds=timeout_seconds,
    )
    finished = time.perf_counter()
    return {
        "status": "passed",
        "open_seconds": round(open_seconds, 6),
        "wall_seconds": round(finished - started, 6),
        "peak_rss_bytes": _peak_rss_bytes(),
        "change_counts": {
            key: len(value) for key, value in profiled["changes"].items()
        },
        "metrics": profiled["metrics"],
    }


def _run_clean_workers(
    *,
    before: Path,
    after: Path,
    repetitions: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    results = []
    for run_number in range(1, repetitions + 1):
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--before",
            str(before),
            "--after",
            str(after),
            "--timeout-seconds",
            str(timeout_seconds),
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            results.append(
                {
                    "run": run_number,
                    "status": "failed",
                    "returncode": completed.returncode,
                    "stderr": completed.stderr[-4000:],
                }
            )
            continue
        result = json.loads(completed.stdout)
        result["run"] = run_number
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--memory-budget-gib", type=float, default=4.0)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()

    before = args.before.resolve()
    after = args.after.resolve()
    if args.worker:
        print(
            json.dumps(
                _worker(before, after, args.timeout_seconds),
                ensure_ascii=False,
            )
        )
        return 0

    if args.output is None:
        parser.error("--output is required unless --worker is used")
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    runs = _run_clean_workers(
        before=before,
        after=after,
        repetitions=args.repetitions,
        timeout_seconds=args.timeout_seconds,
    )
    successful = [run for run in runs if run["status"] == "passed"]
    consistent_counts = {
        json.dumps(run["change_counts"], sort_keys=True) for run in successful
    }
    median_comparison_seconds = (
        statistics.median(
            run["metrics"]["total_seconds"] for run in successful
        )
        if successful
        else None
    )
    median_wall_seconds = (
        statistics.median(run["wall_seconds"] for run in successful)
        if successful
        else None
    )
    peak_rss_bytes = max(
        (run["peak_rss_bytes"] for run in successful),
        default=None,
    )
    memory_budget_bytes = int(args.memory_budget_gib * 1024**3)
    accepted = (
        len(successful) == args.repetitions
        and len(consistent_counts) == 1
        and median_comparison_seconds is not None
        and median_comparison_seconds <= args.timeout_seconds
        and peak_rss_bytes is not None
        and peak_rss_bytes <= memory_budget_bytes
    )
    report = {
        "schema_version": "text2ifc/comparator-0.2-benchmark/0.1",
        "status": "passed" if accepted else "failed",
        "before": {
            "path": str(before),
            "sha256": _sha256(before),
        },
        "after": {
            "path": str(after),
            "sha256": _sha256(after),
        },
        "budgets": {
            "comparison_seconds": args.timeout_seconds,
            "peak_rss_bytes": memory_budget_bytes,
        },
        "summary": {
            "successful_runs": len(successful),
            "requested_runs": args.repetitions,
            "consistent_change_counts": len(consistent_counts) == 1,
            "median_comparison_seconds": median_comparison_seconds,
            "median_wall_seconds": median_wall_seconds,
            "peak_rss_bytes": peak_rss_bytes,
        },
        "runs": runs,
    }
    atomic_write_text(
        args.output.resolve(),
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
