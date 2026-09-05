"""Admit a strict curated subset from the Kaggle IFC examples dataset."""

from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.parse
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / ".tmp/dataset-acquisition/kaggle-ifc-examples-small-ifc2x3.jsonl"
TARGET_ROOT = ROOT / "dataset/external/kaggle-ifc-examples"
LEDGER = ROOT / "dataset/manifests/acquisitions/kaggle-ifc-examples-small-ifc2x3.jsonl"
BASE = "https://www.kaggle.com/api/v1/datasets/download/claytonmiller/example-ifc-file/"
MIB = 1024 * 1024

SELECTED_PATHS = {
    "Grethes-hus-bok-2.ifc": "distinct_complete_residential_model",
    "Open IFC Model Repository 2021-09-23/20160613office_model_CV2b_fordesign.ifc": "distinct_complete_office_model_latest_representative",
    "Open IFC Model Repository 2021-09-23/20160125Trapelo - Existing-RST_2010_Trapelo.ifc": "distinct_complete_structural_model",
    "Open IFC Model Repository 2021-09-23/20191002V57-3-BA2-01-001.ifc": "distinct_complete_mep_model",
    "Open IFC Model Repository 2021-09-23/20200106QT42__190412.ifc": "distinct_complete_architectural_model",
    "Open IFC Model Repository 2021-09-23/20160125Autodesk_Hospital_Parking Garage_2015.ifc": "distinct_complete_parking_garage_model",
    "Open IFC Model Repository 2021-09-23/20200117TOWER_TOTAL_00_10006320176.ifc": "distinct_complete_structural_tower_model",
    "Open IFC Model Repository 2021-09-23/20210125Prova.ifc": "distinct_complete_mixed_arch_mep_model",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download(path: str) -> bytes:
    url = BASE + urllib.parse.quote(path, safe="")
    last_error = None
    for delay in (0, 2, 6, 15):
        if delay:
            time.sleep(delay)
        try:
            response = requests.get(url, headers={"User-Agent": "text2ifc-dataset/1.0"}, timeout=120)
            response.raise_for_status()
            data = response.content
            if data.startswith(b"PK\x03\x04"):
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    members = [i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith(".ifc")]
                    if len(members) != 1:
                        raise RuntimeError(f"ambiguous zip payload for {path}: {len(members)} IFC members")
                    return archive.read(members[0])
            return data
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"download failed for {path}: {last_error}")


def _size_class(size: int) -> str:
    if size < MIB:
        return "lt1_mib_generation_reference"
    if size < 3 * MIB:
        return "1to3_mib_repair_small"
    return "3to10_mib_repair_compact"


def _recommended_usage(size: int, metrics: dict) -> list[str]:
    usage = ["repair_source"]
    if size < MIB and metrics.get("key_class_diversity", 0) >= 4:
        usage.insert(0, "generation_reference")
    elif size < 3 * MIB:
        usage.insert(0, "generation_complex_reference")
    if any(metrics.get("key_class_counts", {}).get(name, 0) for name in ("IfcFlowTerminal", "IfcFlowSegment", "IfcFlowFitting")):
        usage.append("mep_diversity")
    return usage


def main() -> int:
    rows = [json.loads(line) for line in SCAN.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = []
    for row in rows:
        upstream_path = str(row.get("path", ""))
        if upstream_path not in SELECTED_PATHS:
            continue
        if row.get("status") != "meaningful_model" or row.get("schema") != "IFC2X3":
            raise RuntimeError(f"selected candidate no longer passes strict scan: {row.get('path')}")
        if row.get("local_exact_duplicate"):
            raise RuntimeError(f"selected candidate became local exact duplicate: {row.get('path')}")
        selected.append(row)
    if len(selected) != len(SELECTED_PATHS):
        found = {str(r["path"]) for r in selected}
        raise RuntimeError(f"missing selected candidates: {sorted(set(SELECTED_PATHS) - found)}")

    ledger = []
    for index, row in enumerate(sorted(selected, key=lambda r: r["size_bytes"]), start=1):
        upstream_path = str(row["path"])
        data = _download(upstream_path)
        digest = _sha256(data)
        if digest != row["sha256"]:
            raise RuntimeError(f"SHA mismatch for {upstream_path}: {digest} != {row['sha256']}")
        family = str(row.get("upstream_family") or "unknown")
        target_dir = TARGET_ROOT / family
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / Path(upstream_path).name
        if target.exists() and _sha256(target.read_bytes()) != digest:
            raise RuntimeError(f"target collision: {target}")
        target.write_bytes(data)
        metrics = row.get("metrics") or {}
        record = {
            "source_id": "kaggle-ifc-examples",
            "canonical_source": "claytonmiller/example-ifc-file (Kaggle)",
            "dataset_license": "CC-BY-4.0",
            "upstream_family": family,
            "upstream_path": upstream_path,
            "canonical_path": target.relative_to(ROOT).as_posix(),
            "sha256": digest,
            "size_bytes": len(data),
            "size_mib": round(len(data) / MIB, 6),
            "schema": "IFC2X3",
            "meaningfulness": "meaningful_model",
            "metrics": metrics,
            "selection_reason": SELECTED_PATHS[upstream_path],
            "size_class": _size_class(len(data)),
            "recommended_usage": _recommended_usage(len(data), metrics),
            "training_use": "review_required",
            "redistribution": "review_required",
            "status": "stored_pending_technical_certification",
        }
        ledger.append(record)
        print(f"STORE {index}/{len(selected)} {record['canonical_path']} {len(data)} {digest[:12]}", flush=True)

    ledger.sort(key=lambda r: (r["size_bytes"], r["canonical_path"]))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in ledger),
        encoding="utf-8",
    )
    print(json.dumps({
        "stored": len(ledger),
        "lt1": sum(r["size_bytes"] < MIB for r in ledger),
        "lt3": sum(r["size_bytes"] < 3 * MIB for r in ledger),
        "lt10": len(ledger),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
