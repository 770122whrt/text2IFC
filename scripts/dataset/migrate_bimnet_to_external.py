"""Atomically migrate legacy BIMNet IFC files into dataset/external/bimnet."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_ROOTS = (ROOT / "dataset/ifc/train", ROOT / "dataset/ifc/test")
TARGET_ROOT = ROOT / "dataset/external/bimnet"
REPORT_PATH = ROOT / "dataset/manifests/bimnet-migration-map.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def legacy_files() -> list[Path]:
    return sorted(
        [path for root in LEGACY_ROOTS if root.is_dir() for path in root.glob("*.ifc")],
        key=lambda path: path.name.casefold(),
    )


def build_map() -> list[dict[str, str]]:
    records = []
    seen_names: set[str] = set()
    for source in legacy_files():
        if source.name.casefold() in seen_names:
            raise SystemExit(f"BIMNET_FILENAME_COLLISION:{source.name}")
        seen_names.add(source.name.casefold())
        records.append(
            {
                "old_path": source.relative_to(ROOT).as_posix(),
                "new_path": (TARGET_ROOT / source.name).relative_to(ROOT).as_posix(),
                "sha256": sha256(source),
            }
        )
    return records


def apply(records: list[dict[str, str]]) -> None:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    for record in records:
        source = ROOT / record["old_path"]
        target = ROOT / record["new_path"]
        if target.exists():
            if sha256(target) != record["sha256"]:
                raise SystemExit(f"BIMNET_TARGET_CONFLICT:{record['new_path']}")
            source.unlink()
            continue
        shutil.move(str(source), str(target))
        if sha256(target) != record["sha256"]:
            raise SystemExit(f"BIMNET_POST_MOVE_HASH_MISMATCH:{record['new_path']}")

    for root in LEGACY_ROOTS:
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()
    dataset_ifc = ROOT / "dataset/ifc"
    if dataset_ifc.is_dir() and not any(dataset_ifc.iterdir()):
        dataset_ifc.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    records = build_map()
    if not records:
        existing = sorted(TARGET_ROOT.glob("*.ifc")) if TARGET_ROOT.is_dir() else []
        if len(existing) != 25:
            raise SystemExit(f"BIMNET_ALREADY_MIGRATED_COUNT_MISMATCH:{len(existing)}")
        print(json.dumps({"status": "already_migrated", "file_count": len(existing)}, indent=2))
        return 0

    if len(records) != 25:
        raise SystemExit(f"BIMNET_LEGACY_COUNT_MISMATCH:{len(records)}")

    payload = {"schema_version": "text2ifc/bimnet-migration-map/1.0", "file_count": len(records), "records": records}
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not args.apply:
        return 0

    apply(records)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
