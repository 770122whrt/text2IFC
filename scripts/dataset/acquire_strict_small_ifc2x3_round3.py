"""Acquire a strict third round of small meaningful IFC2X3 examples.

Sources:
- opensourceBIM/TestFiles (GPL-3.0-or-later TestData license)
- opensourceBIM/IFC-files (CC BY-ND 4.0 repository policy)
- AsuniSoft/ifc2x3-SDK (repository LGPL-2.1; model rights review required)
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.parse
from pathlib import Path

import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "dataset/manifests/acquisitions/strict-small-ifc2x3-round3.jsonl"
MIB = 1024 * 1024
MAX_BYTES = 10 * MIB
USER_AGENT = "text2ifc-dataset/1.0"

KEY_CLASSES = (
    "IfcWall",
    "IfcSlab",
    "IfcDoor",
    "IfcWindow",
    "IfcOpeningElement",
    "IfcBeam",
    "IfcColumn",
    "IfcStair",
    "IfcRoof",
    "IfcSpace",
    "IfcFlowTerminal",
    "IfcFlowSegment",
    "IfcFlowFitting",
)

SELECTED = (
    {
        "source_id": "opensourcebim-testfiles",
        "repo": "opensourceBIM/TestFiles",
        "ref": "master",
        "upstream_path": "TestData/data/example.ifc",
        "target": "dataset/external/opensourcebim-testfiles/example.ifc",
        "license": "GPL-3.0-or-later",
        "selection_reason": "independent_complete_small_building_model",
    },
    {
        "source_id": "opensourcebim-testfiles",
        "repo": "opensourceBIM/TestFiles",
        "ref": "master",
        "upstream_path": "TestData/data/AC90R1-niedriha-V2-2x3.ifc",
        "target": "dataset/external/opensourcebim-testfiles/AC90R1-niedriha-V2-2x3.ifc",
        "license": "GPL-3.0-or-later",
        "selection_reason": "single_representative_of_niedriha_model_family",
    },
    {
        "source_id": "opensourcebim-testfiles",
        "repo": "opensourceBIM/TestFiles",
        "ref": "master",
        "upstream_path": "TestData/data/Jesse.1.ifc",
        "target": "dataset/external/opensourcebim-testfiles/Jesse.1.ifc",
        "license": "GPL-3.0-or-later",
        "selection_reason": "independent_complete_multistorey_model",
    },
    {
        "source_id": "opensourcebim-testfiles",
        "repo": "opensourceBIM/TestFiles",
        "ref": "master",
        "upstream_path": "TestData/data/AC90R1-Jasmin-Sun-105-2x3.ifc",
        "target": "dataset/external/opensourcebim-testfiles/AC90R1-Jasmin-Sun-105-2x3.ifc",
        "license": "GPL-3.0-or-later",
        "selection_reason": "independent_complete_residential_model",
    },
    {
        "source_id": "opensourcebim-testfiles",
        "repo": "opensourceBIM/TestFiles",
        "ref": "master",
        "upstream_path": "TestData/data/AC9R1-Haus-G-H-Ver2-2x3.ifc",
        "target": "dataset/external/opensourcebim-testfiles/AC9R1-Haus-G-H-Ver2-2x3.ifc",
        "license": "GPL-3.0-or-later",
        "selection_reason": "single_representative_of_haus_g_h_model_family",
    },
    {
        "source_id": "opensourcebim-ifc-files",
        "repo": "opensourceBIM/IFC-files",
        "ref": "master",
        "upstream_path": "HHS Office/construction.ifc",
        "target": "dataset/external/opensourcebim-ifc-files/HHS_Office_construction.ifc",
        "license": "CC-BY-ND-4.0",
        "selection_reason": "single_representative_of_hhs_office_construction_family",
    },
    {
        "source_id": "asunisoft-ifc2x3-sdk",
        "repo": "AsuniSoft/ifc2x3-SDK",
        "ref": "master",
        "upstream_path": "data/Ifc/builtModel.ifc",
        "target": "dataset/external/asunisoft-ifc2x3-sdk/builtModel.ifc",
        "license": "repository-LGPL-2.1-model-rights-review-required",
        "selection_reason": "non_ticket_complete_sdk_example",
    },
)


def _download(repo: str, ref: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/" + urllib.parse.quote(path, safe="/")
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
    response.raise_for_status()
    return response.content


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local_hashes() -> dict[str, str]:
    path = ROOT / "dataset/manifests/ifc-files.jsonl"
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result[str(row["sha256"])] = str(row["local_path"])
    return result


def _count(model, ifc_class: str) -> int:
    try:
        return len(model.by_type(ifc_class))
    except RuntimeError:
        return 0


def _analyze(data: bytes) -> dict:
    with tempfile.TemporaryDirectory(prefix="strict-small-ifc2x3-round3-") as temp_dir:
        path = Path(temp_dir) / "candidate.ifc"
        path.write_bytes(data)
        model = ifcopenshell.open(str(path))
        schema = str(model.schema).upper()
        key_counts = {name: _count(model, name) for name in KEY_CLASSES}
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
        if schema != "IFC2X3":
            raise RuntimeError(f"schema gate failed: {schema}")
        if len(data) >= MAX_BYTES:
            raise RuntimeError(f"size gate failed: {len(data)}")
        if not (
            metrics["project_count"] >= 1
            and metrics["building_count"] >= 1
            and metrics["storey_count"] >= 1
            and metrics["containment_rel_count"] >= 1
            and metrics["element_count"] >= 10
            and metrics["key_class_diversity"] >= 2
        ):
            raise RuntimeError(f"semantic gate failed: {metrics}")
        return {"schema": schema, "metrics": metrics}


def _size_class(size: int) -> str:
    if size < MIB:
        return "lt1_mib_generation_reference"
    if size < 3 * MIB:
        return "1to3_mib_repair_small"
    return "3to10_mib_repair_compact"


def _recommended_usage(size: int, metrics: dict) -> list[str]:
    usage = ["repair_source"]
    if size < MIB and metrics["key_class_diversity"] >= 4:
        usage.insert(0, "generation_reference")
    elif size < 3 * MIB:
        usage.insert(0, "generation_complex_reference")
    return usage


def main() -> int:
    local_hashes = _local_hashes()
    records = []
    for index, item in enumerate(SELECTED, start=1):
        data = _download(item["repo"], item["ref"], item["upstream_path"])
        digest = _sha256(data)
        if digest in local_hashes:
            raise RuntimeError(
                f"selected candidate is now an exact local duplicate: {item['upstream_path']} -> {local_hashes[digest]}"
            )
        analyzed = _analyze(data)
        target = ROOT / item["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and _sha256(target.read_bytes()) != digest:
            raise RuntimeError(f"target collision: {target}")
        target.write_bytes(data)
        metrics = analyzed["metrics"]
        record = {
            "source_id": item["source_id"],
            "canonical_source": item["repo"],
            "source_ref": item["ref"],
            "upstream_path": item["upstream_path"],
            "canonical_path": target.relative_to(ROOT).as_posix(),
            "sha256": digest,
            "size_bytes": len(data),
            "size_mib": round(len(data) / MIB, 6),
            "schema": analyzed["schema"],
            "license": item["license"],
            "meaningfulness": "meaningful_model",
            "metrics": metrics,
            "selection_reason": item["selection_reason"],
            "size_class": _size_class(len(data)),
            "recommended_usage": _recommended_usage(len(data), metrics),
            "training_use": "review_required",
            "status": "stored_pending_technical_certification",
        }
        if item["source_id"] == "opensourcebim-ifc-files":
            record["redistribution"] = "allowed_with_attribution_no_derivatives"
        elif item["source_id"] == "opensourcebim-testfiles":
            record["redistribution"] = "allowed_with_license_conditions"
        else:
            record["redistribution"] = "review_required"
        records.append(record)
        print(
            f"STORE {index}/{len(SELECTED)} {record['canonical_path']} "
            f"{record['size_mib']:.3f}MiB {digest[:12]}",
            flush=True,
        )

    records.sort(key=lambda row: (row["source_id"], row["size_bytes"], row["canonical_path"]))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for row in records
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "stored": len(records),
                "lt1": sum(row["size_bytes"] < MIB for row in records),
                "lt3": sum(row["size_bytes"] < 3 * MIB for row in records),
                "lt10": len(records),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
