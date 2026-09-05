"""Admit the approved small meaningful IFC2X3 batch from GNI BIM Dataset."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW_EVIDENCE = ROOT / ".tmp/dataset-acquisition/ifc2x3-small-review-batch.jsonl"
TARGET_ROOT = ROOT / "dataset/external/gni-bim-dataset"
LEDGER = ROOT / "dataset/manifests/acquisitions/gni-bim-dataset-small-ifc2x3.jsonl"
MIB = 1024 * 1024


def _load_review_module():
    path = ROOT / "scripts/dataset/build_small_ifc2x3_review_batch.py"
    spec = importlib.util.spec_from_file_location("small_review_batch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load review-batch helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _size_class(size: int) -> str:
    if size < MIB:
        return "lt1_mib_generation_reference"
    if size < 3 * MIB:
        return "1to3_mib_repair_small"
    return "3to10_mib_repair_compact"


def _usage(size: int) -> list[str]:
    if size < MIB:
        return ["generation_reference", "repair_small"]
    if size < 3 * MIB:
        return ["repair_small", "generation_complex_reference"]
    return ["repair_compact"]


def main() -> int:
    helper = _load_review_module()
    review_rows = [
        json.loads(line)
        for line in REVIEW_EVIDENCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selected = [
        row
        for row in review_rows
        if row.get("source_id") == "gni-bim-dataset"
        and row.get("schema") == "IFC2X3"
        and row.get("meaningfulness") == "meaningful_model"
        and not row.get("local_exact_duplicate")
        and row.get("sha256")
    ]
    by_package: dict[str, list[dict]] = {}
    for row in selected:
        by_package.setdefault(str(row["package"]), []).append(row)

    packages = {item["key"]: item for item in helper._zenodo_gni_files()}
    ledger_rows: list[dict] = []
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)

    for package_name, rows in sorted(by_package.items()):
        package = packages[package_name]
        remote = helper.HTTPRangeFile(package["url"])
        with zipfile.ZipFile(remote) as archive:
            infos = {info.filename: info for info in archive.infolist()}
            for index, row in enumerate(sorted(rows, key=lambda item: item["path"]), start=1):
                path = str(row["path"])
                info = infos[path]
                data = None
                last_error = None
                for delay in (0, 4, 12, 30):
                    if delay:
                        time.sleep(delay)
                    try:
                        data = archive.read(info)
                        break
                    except Exception as exc:  # transient Zenodo range throttling
                        last_error = exc
                if data is None:
                    raise RuntimeError(f"failed to download {path}: {last_error}")
                digest = _sha256(data)
                expected = str(row["sha256"])
                if digest != expected:
                    raise RuntimeError(f"sha mismatch for {path}: {digest} != {expected}")

                package_dir = TARGET_ROOT / package_name.removesuffix(".zip")
                package_dir.mkdir(parents=True, exist_ok=True)
                target = package_dir / Path(path).name
                if target.exists() and _sha256(target.read_bytes()) != digest:
                    raise RuntimeError(f"target collision: {target}")
                target.write_bytes(data)

                ledger_rows.append(
                    {
                        "source_id": "gni-bim-dataset",
                        "canonical_source": "ZijianWang-ZW/GNI-BIM-Dataset / Zenodo 19722012",
                        "zenodo_record": "19722012",
                        "package": package_name,
                        "upstream_path": path,
                        "canonical_path": target.relative_to(ROOT).as_posix(),
                        "sha256": digest,
                        "size_bytes": len(data),
                        "size_mib": round(len(data) / MIB, 6),
                        "schema": "IFC2X3",
                        "license": "CC-BY-4.0",
                        "attribution": "required",
                        "meaningfulness": "meaningful_model",
                        "metrics": row.get("metrics", {}),
                        "size_class": _size_class(len(data)),
                        "recommended_usage": _usage(len(data)),
                        "status": "stored_pending_technical_certification",
                    }
                )
                print(f"STORE {index}/{len(rows)} {target.relative_to(ROOT).as_posix()} {len(data)} {digest[:12]}", flush=True)
                time.sleep(1)

    ledger_rows.sort(key=lambda row: (row["size_bytes"], row["canonical_path"]))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in ledger_rows),
        encoding="utf-8",
    )
    print(json.dumps({"stored": len(ledger_rows), "lt1": sum(r["size_bytes"] < MIB for r in ledger_rows), "lt3": sum(r["size_bytes"] < 3 * MIB for r in ledger_rows), "lt10": len(ledger_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
