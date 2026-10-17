"""Record a user-requested stop without resuming or rewriting case evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def checkpoint(root: Path) -> dict:
    records = []
    for path in sorted((root / "sources").glob("*/cases/case-*/case.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        records.append({"path": path.relative_to(root).as_posix(), "status": record["status"]})
    results = list((root / "sources").glob("*/result.json"))
    data = {
        "status": "stopped_by_user",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "User deferred the 40 x 25 batch and requested first-batch validation and prompt cross-checks.",
        "execution": "Ctrl+C; parent exited with code 1; subsequent Get-Process found no Python processes.",
        "completed_case_records": len(records),
        "passed_case_records": sum(row["status"] == "passed" for row in records),
        "failed_case_records": sum(row["status"] != "passed" for row in records),
        "completed_source_records": len(results),
        "unfinished_build_folders": len(list((root / "sources").glob("*/cases/.building-*"))),
        "provider_calls": 0,
        "cases": records,
        "preservation": "Case files, failures, partial building folders and source records remain unchanged. This is not a completed dataset.",
    }
    path = root / "STOPPED-BY-USER.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    info = checkpoint(parser.parse_args().root)
    print(json.dumps({key: value for key, value in info.items() if key != "cases"}, ensure_ascii=False))
