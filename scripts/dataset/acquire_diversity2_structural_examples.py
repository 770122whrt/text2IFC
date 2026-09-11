"""Acquire strict IFC2X3 structural examples admitted after diversity floor changed to 2."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import urllib.parse
import zipfile
from pathlib import Path

import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
MIB = 1024 * 1024
LEDGER = ROOT / "dataset/manifests/acquisitions/diversity2-structural-examples.jsonl"
KEY_CLASSES = (
    "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement",
    "IfcBeam", "IfcColumn", "IfcStair", "IfcRoof", "IfcSpace",
    "IfcFlowTerminal", "IfcFlowSegment", "IfcFlowFitting",
)

SELECTED = (
    {
        "source_id": "kaggle-ifc-examples",
        "canonical_source": "claytonmiller/example-ifc-file (Kaggle)",
        "kind": "kaggle",
        "upstream_path": "Open IFC Model Repository 2021-09-23/20200205Model_PNO.ifc",
        "target": "dataset/external/kaggle-ifc-examples/open-ifc-model-repository/20200205Model_PNO.ifc",
        "license": "dataset-CC-BY-4.0-upstream-model-rights-review-required",
        "selection_reason": "complete_structural_model_admitted_at_diversity_2",
    },
    {
        "source_id": "geometrygym-ifc-examples",
        "canonical_source": "GeometryGym/GeometryGymIFCExamples",
        "kind": "github",
        "repo": "GeometryGym/GeometryGymIFCExamples",
        "ref": "master",
        "upstream_path": "consoleSummarizeElements/IFC Model.ifc",
        "target": "dataset/external/geometrygym-ifc-examples/IFC_Model.ifc",
        "license": "repository-MIT-model-rights-review-required",
        "selection_reason": "complete_structural_model_admitted_at_diversity_2",
    },
)


def _count(model, cls: str) -> int:
    try:
        return len(model.by_type(cls))
    except RuntimeError:
        return 0


def _download(item: dict) -> bytes:
    if item["kind"] == "github":
        url = (
            f"https://raw.githubusercontent.com/{item['repo']}/{item['ref']}/"
            + urllib.parse.quote(item["upstream_path"], safe="/")
        )
        response = requests.get(url, headers={"User-Agent": "text2ifc-dataset/1.0"}, timeout=120)
        response.raise_for_status()
        return response.content
    url = (
        "https://www.kaggle.com/api/v1/datasets/download/claytonmiller/example-ifc-file/"
        + urllib.parse.quote(item["upstream_path"], safe="")
    )
    response = requests.get(url, headers={"User-Agent": "text2ifc-dataset/1.0"}, timeout=120)
    response.raise_for_status()
    data = response.content
    if data.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = [i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith(".ifc")]
            if len(members) != 1:
                raise RuntimeError(f"ambiguous Kaggle payload: {len(members)} IFC members")
            return archive.read(members[0])
    return data


def main() -> int:
    local_hashes = {}
    for line in (ROOT / "dataset/manifests/ifc-files.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            local_hashes[row["sha256"]] = row["local_path"]

    records = []
    for item in SELECTED:
        data = _download(item)
        digest = hashlib.sha256(data).hexdigest()
        if digest in local_hashes:
            raise RuntimeError(f"exact local duplicate: {item['upstream_path']} -> {local_hashes[digest]}")
        with tempfile.TemporaryDirectory(prefix="diversity2-structural-") as temp_dir:
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
            if not (
                len(data) < 10 * MIB
                and metrics["project_count"] >= 1
                and metrics["building_count"] >= 1
                and metrics["storey_count"] >= 1
                and metrics["containment_rel_count"] >= 1
                and metrics["element_count"] >= 10
                and metrics["key_class_diversity"] >= 2
            ):
                raise RuntimeError(f"semantic gate failed: {metrics}")

        target = ROOT / item["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append({
            "source_id": item["source_id"],
            "canonical_source": item["canonical_source"],
            "upstream_path": item["upstream_path"],
            "canonical_path": target.relative_to(ROOT).as_posix(),
            "sha256": digest,
            "size_bytes": len(data),
            "size_mib": round(len(data) / MIB, 6),
            "schema": "IFC2X3",
            "license": item["license"],
            "meaningfulness": "discipline_model",
            "metrics": metrics,
            "selection_reason": item["selection_reason"],
            "size_class": "lt1_mib_generation_reference" if len(data) < MIB else "1to3_mib_repair_small",
            "recommended_usage": ["structural_reference", "repair_source"],
            "training_use": "review_required",
            "redistribution": "review_required",
            "status": "stored_pending_technical_certification",
        })
        print(f"STORE {target.relative_to(ROOT).as_posix()} {len(data)} {digest[:12]}", flush=True)

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in records),
        encoding="utf-8",
    )
    print(json.dumps({"stored": len(records), "lt1": sum(r["size_bytes"] < MIB for r in records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
