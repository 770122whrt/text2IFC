"""Expand BIMData R&D table-group discovery rows into file-level candidates."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / ".tmp/dataset-acquisition/bimdata-rd-candidates.jsonl"
OUTPUT = ROOT / ".tmp/dataset-acquisition/bimdata-rd-file-candidates.jsonl"


def main() -> int:
    groups = [
        json.loads(line)
        for line in SOURCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows: list[dict] = []
    for group_index, group in enumerate(groups):
        names = list(group.get("ifc_names") or [])
        numbers = list(group.get("numbers") or [])
        urls = list(group.get("source_urls") or [])
        for index, name in enumerate(names):
            size_mb = None
            if index < len(numbers):
                try:
                    size_mb = float(numbers[index])
                except (TypeError, ValueError):
                    pass
            rows.append(
                {
                    "source_id": "bimdata-rd-index",
                    "upstream_path": name,
                    "reported_size_mb": size_mb,
                    "size_bytes": int(size_mb * 1024 * 1024) if size_mb is not None else None,
                    "source_urls": urls,
                    "candidate_status": "index_only",
                    "discovery_group": group_index,
                }
            )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"groups": len(groups), "files": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
