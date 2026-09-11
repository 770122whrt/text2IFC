"""Acquire semantically meaningful IFC2X3 models under 10 MiB from UdK-VPT/BIM2Modelica."""

from __future__ import annotations

import hashlib
import io
import json
import re
import ssl
import urllib.request
import zipfile
from pathlib import Path

import certifi
import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "dataset/external/bim2modelica"
LEDGER = ROOT / "dataset/manifests/acquisitions/bim2modelica-small-ifc2x3.jsonl"
ARCHIVE_URL = "https://codeload.github.com/UdK-VPT/BIM2Modelica/zip/refs/heads/master"
MAX_BYTES = 10 * 1024 * 1024
USER_AGENT = "text2ifc-dataset/1.0"
KEY_CLASSES = (
    "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement",
    "IfcBeam", "IfcColumn", "IfcStair", "IfcRoof", "IfcSpace",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_hashes() -> dict[str, str]:
    result = {}
    manifest = ROOT / "dataset/manifests/ifc-files.jsonl"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result[row["sha256"]] = row["local_path"]
    return result


def count(model, cls: str) -> int:
    try:
        return len(model.by_type(cls))
    except RuntimeError:
        return 0


def meaningful(path: Path) -> tuple[bool, dict]:
    try:
        model = ifcopenshell.open(str(path))
        if str(model.schema).upper() != "IFC2X3":
            return False, {"reason": "not_ifc2x3"}
        key = {cls: count(model, cls) for cls in KEY_CLASSES}
        metrics = {
            "project_count": count(model, "IfcProject"),
            "building_count": count(model, "IfcBuilding"),
            "storey_count": count(model, "IfcBuildingStorey"),
            "containment_rel_count": count(model, "IfcRelContainedInSpatialStructure"),
            "element_count": count(model, "IfcElement"),
            "key_class_diversity": sum(v > 0 for v in key.values()),
            "key_class_counts": key,
        }
        ok = (
            metrics["project_count"] >= 1
            and metrics["building_count"] >= 1
            and metrics["storey_count"] >= 1
            and metrics["containment_rel_count"] >= 1
            and metrics["element_count"] >= 10
            and metrics["key_class_diversity"] >= 2
        )
        return ok, metrics
    except Exception as exc:
        return False, {"reason": f"{type(exc).__name__}:{exc}"}


def main() -> int:
    req = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=180, context=ctx) as response:
        archive_bytes = response.read()
    known = local_hashes()
    records = []
    TARGET.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        infos = [
            info for info in zf.infolist()
            if not info.is_dir()
            and "/IFC/IFC2X3/" in info.filename.replace("\\", "/")
            and info.filename.lower().endswith(".ifc")
            and info.file_size < MAX_BYTES
        ]
        for info in sorted(infos, key=lambda x: x.filename.casefold()):
            data = zf.read(info)
            digest = sha256_bytes(data)
            duplicate = known.get(digest)
            if duplicate:
                records.append({
                    "upstream_path": info.filename,
                    "size_bytes": len(data),
                    "sha256": digest,
                    "status": "exact_duplicate_local",
                    "canonical_path": duplicate,
                })
                continue
            temp = TARGET / ".candidate.ifc"
            temp.write_bytes(data)
            ok, metrics = meaningful(temp)
            temp.unlink(missing_ok=True)
            if not ok:
                records.append({
                    "upstream_path": info.filename,
                    "size_bytes": len(data),
                    "sha256": digest,
                    "status": "excluded_not_meaningful",
                    "metrics": metrics,
                })
                continue
            name = Path(info.filename).name
            target = TARGET / name
            if target.exists() and sha256_bytes(target.read_bytes()) != digest:
                raise RuntimeError(f"TARGET_CONFLICT:{target}")
            target.write_bytes(data)
            known[digest] = target.relative_to(ROOT).as_posix()
            records.append({
                "upstream_path": info.filename,
                "size_bytes": len(data),
                "sha256": digest,
                "status": "stored_canonical",
                "canonical_path": target.relative_to(ROOT).as_posix(),
                "metrics": metrics,
            })
    clean = [r for r in records if r["status"] != "excluded_not_meaningful"]
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in clean), encoding="utf-8")
    print(json.dumps({
        "archive_bytes": len(archive_bytes),
        "under10_ifc2x3_paths": len(records),
        "stored_meaningful": sum(r["status"] == "stored_canonical" for r in records),
        "exact_duplicate_local": sum(r["status"] == "exact_duplicate_local" for r in records),
        "excluded_not_meaningful": sum(r["status"] == "excluded_not_meaningful" for r in records),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
