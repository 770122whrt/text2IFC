"""Move the user-selected audit directory to external, preserving evidence bytes.

This one-off migration never opens, extracts, repairs, or moves an IFC/ZIP.
It refuses an existing destination and verifies moved evidence by direct bytes,
not by recomputing a dataset hash inventory. Run without --apply to preview.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = Path("dataset/processed/review/incoming-ifc-audit-20260910")
NEW = Path("dataset/external/_checks/incoming-ifc-audit-20260910")


def migrate(root: Path, *, apply: bool = False) -> dict:
    root = root.resolve()
    source, target = root / OLD, root / NEW
    for path in (source, target):
        path.resolve().relative_to(root)
        if path.is_symlink():
            raise RuntimeError(f"SYMLINK_NOT_ALLOWED:{path}")
    if not source.is_dir():
        raise RuntimeError("SOURCE_DIRECTORY_MISSING")
    if target.exists():
        raise RuntimeError("DESTINATION_ALREADY_EXISTS")
    files = sorted(p for p in source.rglob("*") if p.is_file())
    if not files or len(files) > 500:
        raise RuntimeError("UNEXPECTED_REPORT_FILE_COUNT")
    if any(p.is_symlink() or p.suffix.lower() not in {".md", ".json", ".txt"} for p in files):
        raise RuntimeError("UNEXPECTED_REPORT_CONTENT")
    total = sum(p.stat().st_size for p in files)
    if total > 32 * 1024 * 1024:
        raise RuntimeError("REPORT_RESOURCE_LIMIT")
    before = {p.relative_to(source).as_posix(): p.read_bytes() for p in files}
    result = {"old_path": OLD.as_posix(), "new_path": NEW.as_posix(),
              "file_count": len(before), "size_bytes": total,
              "applied": apply, "model_files_touched": False}
    if not apply:
        return result
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)
    after = {p.relative_to(target).as_posix(): p.read_bytes()
             for p in target.rglob("*") if p.is_file()}
    if after != before:
        if not source.exists():
            target.rename(source)
        raise RuntimeError("MIGRATION_BYTE_COMPARISON_FAILED_ROLLED_BACK")
    result.update(verified_at=datetime.now(timezone.utc).isoformat(),
                  byte_equality_verified=True, old_directory_absent=not source.exists(),
                  evidence_policy="Historical JSON, failures, and original reports retained unchanged; README navigation may be updated separately.")
    result["moved_files"] = [{"path": k, "size_bytes_at_move": len(v)} for k, v in before.items()]
    with (target / "migration.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {k: v for k, v in result.items() if k != "moved_files"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(ROOT, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
