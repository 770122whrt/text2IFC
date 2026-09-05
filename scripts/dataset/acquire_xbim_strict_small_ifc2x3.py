"""Acquire strict small IFC2X3 examples from xBIM Essentials."""

from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.parse
from pathlib import Path

import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
REPO = "xBimTeam/XbimEssentials"
REF = "master"
MIB = 1024 * 1024
LEDGER = ROOT / "dataset/manifests/acquisitions/xbim-essentials-small-ifc2x3.jsonl"
KEY_CLASSES = (
    "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement",
    "IfcBeam", "IfcColumn", "IfcStair", "IfcRoof", "IfcSpace",
    "IfcFlowTerminal", "IfcFlowSegment", "IfcFlowFitting",
)
SELECTED = (
    ("Tests/TestSourceFiles/House.ifc", "House.ifc", "independent_complete_house_model"),
    ("Xbim.Essentials.NetCore.Tests/TestFiles/CPM.ifc", "CPM.ifc", "independent_complete_small_cpm_model"),
)


def _count(model, cls: str) -> int:
    try:
        return len(model.by_type(cls))
    except RuntimeError:
        return 0


def main() -> int:
    local_hashes = {}
    for line in (ROOT / "dataset/manifests/ifc-files.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            local_hashes[row["sha256"]] = row["local_path"]

    records = []
    for upstream_path, target_name, reason in SELECTED:
        url = f"https://raw.githubusercontent.com/{REPO}/{REF}/" + urllib.parse.quote(upstream_path, safe="/")
        response = requests.get(url, headers={"User-Agent": "text2ifc-dataset/1.0"}, timeout=120)
        response.raise_for_status()
        data = response.content
        digest = hashlib.sha256(data).hexdigest()
        if digest in local_hashes:
            raise RuntimeError(f"exact local duplicate: {upstream_path} -> {local_hashes[digest]}")
        with tempfile.TemporaryDirectory(prefix="xbim-strict-small-") as temp_dir:
            path = Path(temp_dir) / "candidate.ifc"
            path.write_bytes(data)
            model = ifcopenshell.open(str(path))
            key_counts = {cls: _count(model, cls) for cls in KEY_CLASSES}
            metrics = {
                "entity_count": sum(1 for _ in model),
                "project_count": _count(model, "IfcProject"),
                "building_count": _count(model, "IfcBuilding"),
                "storey_count": _count(model, "IfcBuildingStorey"),
                "element_count": _count(model, "IfcElement"),
                "containment_rel_count": _count(model, "IfcRelContainedInSpatialStructure"),
                "key_class_counts": key_counts,
                "key_class_diversity": sum(v > 0 for v in key_counts.values()),
            }
            if str(model.schema).upper() != "IFC2X3":
                raise RuntimeError(f"schema gate failed: {model.schema}")
            if len(data) >= 10 * MIB:
                raise RuntimeError(f"size gate failed: {len(data)}")
            if not (
                metrics["project_count"] >= 1
                and metrics["building_count"] >= 1
                and metrics["storey_count"] >= 1
                and metrics["containment_rel_count"] >= 1
                and metrics["element_count"] >= 10
                and metrics["key_class_diversity"] >= 3
            ):
                raise RuntimeError(f"semantic gate failed: {metrics}")

        target = ROOT / "dataset/external/xbim-essentials-examples" / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"target collision: {target}")
        target.write_bytes(data)
        size_class = "lt1_mib_generation_reference" if len(data) < MIB else "1to3_mib_repair_small"
        usage = ["generation_reference", "repair_source"] if len(data) < MIB else ["generation_complex_reference", "repair_source"]
        records.append({
            "source_id": "xbim-essentials-examples",
            "canonical_source": REPO,
            "source_ref": REF,
            "upstream_path": upstream_path,
            "canonical_path": target.relative_to(ROOT).as_posix(),
            "sha256": digest,
            "size_bytes": len(data),
            "size_mib": round(len(data) / MIB, 6),
            "schema": "IFC2X3",
            "license": "repository-CDDL-model-rights-review-required",
            "meaningfulness": "meaningful_model",
            "metrics": metrics,
            "selection_reason": reason,
            "size_class": size_class,
            "recommended_usage": usage,
            "training_use": "review_required",
            "redistribution": "review_required",
            "status": "stored_pending_technical_certification",
        })
        print(f"STORE {target.relative_to(ROOT).as_posix()} {len(data)} {digest[:12]}", flush=True)

    records.sort(key=lambda row: row["size_bytes"])
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in records), encoding="utf-8")
    print(json.dumps({"stored": len(records), "lt1": sum(r["size_bytes"] < MIB for r in records), "lt3": len(records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
