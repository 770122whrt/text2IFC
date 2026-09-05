"""Acquire selected STEP Tools IFC2X3 samples for local research validation."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "steptools-samples"
TARGET_ROOT = ROOT / "dataset/external/steptools-samples"
LEDGER_PATH = ROOT / "dataset/manifests/acquisition-steptools-samples.jsonl"
USER_AGENT = "text2ifc-dataset/1.0"
BASE = "https://downloads.steptools.com/docs/stpfiles/ifc/"
FILES = (
    ("aisc_sculpture_brep.ifc", "NIST CIS/2 steel design conversion; brep solids"),
    ("aisc_sculpture_param.ifc", "NIST CIS/2 steel design conversion; parameterized swept solids"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as stream:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)


def _write(records: list[dict]) -> None:
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in sorted(records, key=lambda item: item["filename"])
    )
    tmp = LEDGER_PATH.with_suffix(".jsonl.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, LEDGER_PATH)


def main() -> int:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    hashes = _existing_hashes()
    records: list[dict] = []
    for filename, notes in FILES:
        url = BASE + filename
        target = TARGET_ROOT / filename
        if not target.exists():
            print(f"DOWNLOAD {filename}", flush=True)
            _download(url, target)
        digest = _sha256(target)
        existing = hashes.get(digest)
        if existing is not None and existing != target.relative_to(ROOT).as_posix():
            target.unlink()
            status = "exact_duplicate_existing"
            canonical = existing
            print(f"DEDUP {filename} -> {existing}", flush=True)
        else:
            canonical = target.relative_to(ROOT).as_posix()
            hashes[digest] = canonical
            status = "stored_canonical"
            print(f"STORE {canonical} sha={digest[:12]}", flush=True)
        records.append(
            {
                "schema_version": "text2ifc/acquisition-record/1.0",
                "source_id": SOURCE_ID,
                "source_page": BASE,
                "filename": filename,
                "download_url": url,
                "sha256": digest,
                "size_bytes": (ROOT / canonical).stat().st_size,
                "status": status,
                "canonical_path": canonical,
                "declared_by_source": "IFC2X3",
                "notes": notes,
                "license": "review-required",
                "research_use": "review_required",
                "training_use": "review_required",
                "redistribution": "review_required",
            }
        )
        _write(records)
    print(json.dumps({"records": len(records), "stored": sum(r["status"] == "stored_canonical" for r in records)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
