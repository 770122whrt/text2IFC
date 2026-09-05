"""Acquire selected DURAARK upstream packages discovered through the BIMData R&D index."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import tempfile
import urllib.request

import certifi
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "duraark-public"
TARGET_ROOT = ROOT / "dataset/external/duraark"
LEDGER_PATH = ROOT / "dataset/manifests/acquisition-duraark-bimdata-overlap.jsonl"
USER_AGENT = "text2ifc-dataset/1.0"
MAX_AUTO_RETAIN_BYTES = 100 * 1024 * 1024

PACKAGES = (
    {
        "family": "SGD_HiTOS",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/SGD_HiTOS_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "SGD_Blueberry",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/SGD_Blueberry_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "SGD_BARD",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/SGD_BARD_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "NBU_Duplex",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/NBU_Duplex_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "SGD_Munkerud",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/SGD_Munkerud_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "SGD_Duplex",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/SGD_Duplex_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "Academic_Autodesk",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/Academic_Autodesk_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "KIT_Smiley-West",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/KIT_Smiley-West_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "KIT_Institute",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/KIT_Institute_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "NBS_Lakeside",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/NBS_Lakeside_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "SGD_BODO",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/SGD_BODO_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
    {
        "family": "NVW_DCR-LOD",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/NVW_DCR-LOD_ifc.zip",
        "discovered_via": "bimdata-rd-index",
    },
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=180, context=context) as response, target.open("wb") as stream:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)


def _existing_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    manifest = ROOT / "dataset/manifests/ifc-files.jsonl"
    if manifest.is_file():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                result[str(record["sha256"])] = str(record["local_path"])
    if TARGET_ROOT.is_dir():
        for path in TARGET_ROOT.rglob("*.ifc"):
            result.setdefault(_sha256(path), path.relative_to(ROOT).as_posix())
    return result


def _safe_member(name: str) -> str:
    normalized = Path(name.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise RuntimeError(f"UNSAFE_ZIP_MEMBER:{name}")
    return normalized.as_posix()


def _write(records: list[dict]) -> None:
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in sorted(records, key=lambda item: (item["family"], item["member_name"].casefold()))
    )
    tmp = LEDGER_PATH.with_suffix(".jsonl.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, LEDGER_PATH)


def _read_existing_records() -> dict[tuple[str, str], dict]:
    if not LEDGER_PATH.is_file():
        return {}
    records: dict[tuple[str, str], dict] = {}
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        records[(str(record["family"]), str(record["member_name"]))] = record
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", action="append", default=[])
    args = parser.parse_args()
    selected = set(args.family)

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    hashes = _existing_hashes()
    records_by_key = _read_existing_records()
    processed: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="duraark-acquire-") as temp_dir:
        temp_root = Path(temp_dir)
        for package_def in PACKAGES:
            family = str(package_def["family"])
            if selected and family not in selected:
                continue
            url = str(package_def["url"])
            package = temp_root / f"{family}.zip"
            print(f"DOWNLOAD {family} {url}", flush=True)
            _download(url, package)
            package_sha = _sha256(package)
            package_size = package.stat().st_size
            with zipfile.ZipFile(package) as archive:
                infos = [
                    info for info in archive.infolist()
                    if not info.is_dir() and _safe_member(info.filename).lower().endswith(".ifc")
                ]
                print(f"IFC_MEMBERS {family} {len(infos)}", flush=True)
                if not infos:
                    raise RuntimeError(f"NO_IFC_IN_PACKAGE:{family}")
                for info in infos:
                    safe_name = _safe_member(info.filename)
                    extracted = temp_root / (hashlib.sha256(safe_name.encode()).hexdigest()[:16] + ".ifc")
                    with archive.open(info) as src, extracted.open("wb") as dst:
                        while True:
                            chunk = src.read(1024 * 1024)
                            if not chunk:
                                break
                            dst.write(chunk)
                    digest = _sha256(extracted)
                    existing = hashes.get(digest)
                    if existing is not None:
                        status = "exact_duplicate_existing"
                        canonical = existing
                        print(f"DEDUP {safe_name} -> {existing}", flush=True)
                    elif extracted.stat().st_size > MAX_AUTO_RETAIN_BYTES:
                        status = "manual_review_required_size_not_retained"
                        canonical = None
                        print(
                            f"REVIEW_SIZE {safe_name} {extracted.stat().st_size} bytes",
                            flush=True,
                        )
                    else:
                        target = TARGET_ROOT / family / Path(safe_name).name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if target.exists() and _sha256(target) != digest:
                            raise RuntimeError(f"TARGET_CONFLICT:{target.relative_to(ROOT).as_posix()}")
                        if not target.exists():
                            with extracted.open("rb") as src, target.open("wb") as dst:
                                while True:
                                    chunk = src.read(1024 * 1024)
                                    if not chunk:
                                        break
                                    dst.write(chunk)
                        canonical = target.relative_to(ROOT).as_posix()
                        hashes[digest] = canonical
                        status = "stored_canonical"
                        print(f"STORE {canonical} sha={digest[:12]}", flush=True)
                    record = {
                        "schema_version": "text2ifc/acquisition-record/1.0",
                        "source_id": SOURCE_ID,
                        "family": family,
                        "package_url": url,
                        "package_sha256": package_sha,
                        "package_size_bytes": package_size,
                        "member_name": safe_name,
                        "sha256": digest,
                        "size_bytes": extracted.stat().st_size,
                        "status": status,
                        "canonical_path": canonical,
                        "discovered_via": str(package_def["discovered_via"]),
                        "license": "source-open-data-model-rights-review-required",
                        "research_use": "review_required",
                        "training_use": "review_required",
                        "redistribution": "review_required",
                    }
                    records_by_key[(family, safe_name)] = record
                    processed.append(record)
                    _write(list(records_by_key.values()))
    print(json.dumps({"processed_records": len(processed), "ledger_records": len(records_by_key), "stored": sum(r["status"] == "stored_canonical" for r in processed), "deduplicated": sum(r["status"] != "stored_canonical" for r in processed)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
