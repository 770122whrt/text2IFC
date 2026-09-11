"""Build a unified IFC candidate pool from discovery scans.

The pool is discovery authority only. Admission is a separate filtering step.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "dataset/manifests/candidates/ifc-candidate-pool.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize(row: dict, discovery: str) -> dict:
    result = dict(row)
    result.setdefault("discovery", discovery)
    result.setdefault("candidate_status", result.get("status", "discovered"))
    if not result.get("source_id") and discovery.startswith("archiset-"):
        result["source_id"] = "archiset-performance-floorplans"
    result.setdefault("source_id", "unknown")
    result.setdefault("upstream_path", result.get("path"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT.relative_to(ROOT)))
    args = parser.parse_args()

    sources = [
        (ROOT / ".tmp/dataset-acquisition/archiset-ifc2x3-1to3-scan.jsonl", "archiset-1to3"),
        (ROOT / ".tmp/dataset-acquisition/archiset-ifc1-3to10.jsonl", "archiset-ifc1-3to10"),
        (ROOT / ".tmp/dataset-acquisition/archiset-ifc2-3to10.jsonl", "archiset-ifc2-3to10"),
        (ROOT / ".tmp/dataset-acquisition/archiset-ifc3-3to10.jsonl", "archiset-ifc3-3to10"),
        (ROOT / ".tmp/dataset-acquisition/thatopen-lt10-scan.jsonl", "thatopen-lt10"),
        (ROOT / ".tmp/dataset-acquisition/bimdata-rd-file-candidates.jsonl", "bimdata-rd"),
        (ROOT / ".tmp/dataset-acquisition/buildingsmart-community-candidates.jsonl", "buildingsmart-community"),
        (ROOT / ".tmp/dataset-acquisition/ifc-bench-v2-candidates.jsonl", "ifc-bench-v2"),
        (ROOT / ".tmp/dataset-acquisition/manual-new-candidates.jsonl", "manual-discovery"),
    ]

    rows: list[dict] = []
    seen_keys: set[tuple] = set()
    for path, discovery in sources:
        for row in read_jsonl(path):
            normalized = normalize(row, discovery)
            key = (
                normalized.get("source_id"),
                normalized.get("sha256"),
                normalized.get("upstream_path"),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rows.append(normalized)

    rows.sort(
        key=lambda row: (
            str(row.get("source_id", "")),
            int(row.get("size_bytes") or 0),
            str(row.get("upstream_path") or ""),
        )
    )
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    by_source: dict[str, int] = {}
    for row in rows:
        source = str(row.get("source_id"))
        by_source[source] = by_source.get(source, 0) + 1
    print(json.dumps({"records": len(rows), "by_source": by_source}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
