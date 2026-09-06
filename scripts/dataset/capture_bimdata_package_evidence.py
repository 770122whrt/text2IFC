"""Capture package-level evidence for unresolved BIMData/DURAARK source packages."""

from __future__ import annotations

import hashlib
import json
import ssl
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import certifi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dataset/manifests/candidates/bimdata-rd-package-evidence.jsonl"
USER_AGENT = "text2ifc-dataset/1.0"
PACKAGES = (
    {
        "family": "LTU_AHouse",
        "url": "https://tib.eu/data/duraark/BuildingData/03_IFC_E57/LTU_A-House_2014-09-25_ifc.zip",
    },
    {
        "family": "NBU_MedicalClinic",
        "url": "https://tib.eu/data/duraark/BuildingData/01_IFC/NBU_MedicalClinic_ifc.zip",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="bimdata-package-evidence-") as td:
        temp = Path(td)
        for package in PACKAGES:
            family = package["family"]
            url = package["url"]
            target = temp / f"{family}.zip"
            request = Request(url, headers={"User-Agent": USER_AGENT})
            context = ssl.create_default_context(cafile=certifi.where())
            with urlopen(request, timeout=180, context=context) as response, target.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
            with zipfile.ZipFile(target) as archive:
                members = [
                    {
                        "member_name": info.filename,
                        "size_bytes": info.file_size,
                        "compressed_size_bytes": info.compress_size,
                    }
                    for info in archive.infolist()
                    if not info.is_dir() and info.filename.lower().endswith(".ifc")
                ]
            rows.append(
                {
                    "schema_version": "text2ifc/source-package-evidence/1.0",
                    "source_id": "duraark-public",
                    "discovered_via": "bimdata-rd-index",
                    "family": family,
                    "package_url": url,
                    "package_size_bytes": target.stat().st_size,
                    "package_sha256": sha256(target),
                    "verification_method": "full_download_zip_inventory",
                    "ifc_member_count": len(members),
                    "ifc_members": members,
                    "license": "source-open-data-model-rights-review-required",
                    "research_use": "review_required",
                    "training_use": "review_required",
                    "redistribution": "review_required",
                }
            )
            print(f"{family}: {target.stat().st_size} bytes, {len(members)} IFC members", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"packages": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
