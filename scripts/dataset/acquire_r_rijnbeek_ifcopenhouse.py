"""Acquire the strict IFC2X3 IfcOpenHouse representative from R-Rijnbeek/IFC_WebViewer."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
URL = "https://raw.githubusercontent.com/R-Rijnbeek/IFC_WebViewer/master/app/static/ifc/IfcOpenHouse.ifc"
TARGET = ROOT / "dataset/external/r-rijnbeek-ifc-webviewer/IfcOpenHouse.ifc"
LEDGER = ROOT / "dataset/manifests/acquisitions/r-rijnbeek-ifcopenhouse.jsonl"
MIB = 1024 * 1024
KEY_CLASSES = (
    "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement",
    "IfcBeam", "IfcColumn", "IfcStair", "IfcRoof", "IfcSpace",
    "IfcFlowTerminal", "IfcFlowSegment", "IfcFlowFitting",
)


def _count(model, cls: str) -> int:
    try:
        return len(model.by_type(cls))
    except RuntimeError:
        return 0


def main() -> int:
    response = requests.get(URL, headers={"User-Agent": "text2ifc-dataset/1.0"}, timeout=60)
    response.raise_for_status()
    data = response.content
    digest = hashlib.sha256(data).hexdigest()

    for line in (ROOT / "dataset/manifests/ifc-files.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row["sha256"] == digest:
                raise RuntimeError(f"exact local duplicate: {row['local_path']}")

    with tempfile.TemporaryDirectory(prefix="ifcopenhouse-") as temp_dir:
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
            "key_class_diversity": sum(value > 0 for value in key_counts.values()),
        }
        if str(model.schema).upper() != "IFC2X3":
            raise RuntimeError(f"schema gate failed: {model.schema}")
        if not (
            len(data) < 10 * MIB
            and metrics["project_count"] >= 1
            and metrics["building_count"] >= 1
            and metrics["storey_count"] >= 1
            and metrics["containment_rel_count"] >= 1
            and metrics["element_count"] >= 10
            and metrics["key_class_diversity"] >= 3
        ):
            raise RuntimeError(f"semantic gate failed: {metrics}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(data)
    record = {
        "source_id": "r-rijnbeek-ifc-webviewer",
        "canonical_source": "R-Rijnbeek/IFC_WebViewer",
        "source_ref": "master",
        "upstream_path": "app/static/ifc/IfcOpenHouse.ifc",
        "canonical_path": TARGET.relative_to(ROOT).as_posix(),
        "sha256": digest,
        "size_bytes": len(data),
        "size_mib": round(len(data) / MIB, 6),
        "schema": "IFC2X3",
        "license": "repository-MIT-model-rights-review-required",
        "meaningfulness": "meaningful_model",
        "metrics": metrics,
        "selection_reason": "complete_tiny_ifcopenhouse_family_representative",
        "size_class": "lt1_mib_generation_reference",
        "recommended_usage": ["generation_reference", "repair_source"],
        "training_use": "review_required",
        "redistribution": "review_required",
        "status": "stored_pending_technical_certification",
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"stored": 1, "size_mib": record["size_mib"], "sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
