"""Isolated full-IFC validation worker used by the bounded evaluator."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
from typing import Any

import ifcopenshell

from .ifc_validation import normalized_validation_result
from .validation_cache import ValidationCache, ValidationCacheKey


def run(
    *,
    ifc_path: Path,
    cache_dir: Path,
    cache_mode: str,
    key_data: dict[str, Any],
) -> dict[str, Any]:
    key = ValidationCacheKey(**key_data)
    cache = ValidationCache(cache_dir, mode=cache_mode)
    result, evidence = cache.get_or_compute(
        key,
        lambda: normalized_validation_result(
            ifcopenshell.open(str(ifc_path))
        ),
    )
    payload = {
        "evidence": evidence,
        "key": key.to_dict(),
        "peak_rss_bytes": _peak_rss_bytes(),
    }
    if cache_mode == "off":
        payload["result"] = result
    return payload


def _peak_rss_bytes() -> int:
    try:
        if os.name == "nt":
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
            process = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(
                process, ctypes.byref(counters), counters.cb
            ):
                return int(counters.PeakWorkingSetSize)
        else:
            import resource

            return int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            )
    except Exception:
        pass
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ifc", required=True, type=Path)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--cache-mode", required=True)
    parser.add_argument("--key-json", required=True)
    args = parser.parse_args(argv)
    result = run(
        ifc_path=args.ifc,
        cache_dir=args.cache_dir,
        cache_mode=args.cache_mode,
        key_data=json.loads(args.key_json),
    )
    print(
        json.dumps(
            result,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
