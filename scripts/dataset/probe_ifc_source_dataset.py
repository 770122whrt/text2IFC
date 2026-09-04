"""Incrementally validate canonical IFC source files and cache evidence by SHA-256."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.source_manifests import (
    VALIDATION_CACHE_PATH,
    build_file_records,
    load_validation_cache,
    render_jsonl,
    validation_record,
)
from text2ifc_text.splits import atomic_write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--schema", action="append", default=["IFC2X3"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--retry-failures", action="store_true")
    args = parser.parse_args()

    records = build_file_records(ROOT, probe=False)
    cache = load_validation_cache(ROOT)
    source_filter = set(args.source_id)
    schema_filter = {value.upper() for value in args.schema}

    candidates = [
        record
        for record in records
        if (not source_filter or record["source_id"] in source_filter)
        and str(record["header_schema"]).upper() in schema_filter
    ]
    if args.limit is not None:
        candidates = candidates[: args.limit]

    cache_path = ROOT / VALIDATION_CACHE_PATH
    completed = 0
    skipped = 0
    for index, record in enumerate(candidates, start=1):
        digest = record["sha256"]
        existing = cache.get(digest)
        if existing is not None and not (
            args.retry_failures and not existing.get("roundtrip_reopen_ok", False)
        ):
            skipped += 1
            continue

        path = ROOT / record["local_path"]
        print(
            f"PROBE {index}/{len(candidates)} {record['source_id']} "
            f"{record['header_schema']} {record['local_path']}",
            flush=True,
        )
        evidence = validation_record(path=path, root=ROOT, digest=digest)
        cache[digest] = evidence
        atomic_write_text(
            cache_path,
            render_jsonl(cache[key] for key in sorted(cache)),
        )
        completed += 1
        print(
            "RESULT "
            f"parse={evidence['parseable']} traversal={evidence['traversal_ok']} "
            f"write={evidence['roundtrip_write_ok']} reopen={evidence['roundtrip_reopen_ok']} "
            f"entities={evidence['entity_count']} error={evidence['probe_error']}",
            flush=True,
        )

    print(
        f"SUMMARY candidates={len(candidates)} completed={completed} "
        f"skipped_cached={skipped} cache_records={len(cache)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
