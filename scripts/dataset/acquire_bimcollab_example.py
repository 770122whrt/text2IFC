"""Acquire BIMcollab official example IFC package with exact deduplication."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "bimcollab-example"
TARGET_ROOT = ROOT / "dataset/external/bimcollab-example"
LEDGER_PATH = ROOT / "dataset/manifests/acquisition-bimcollab-example.jsonl"
PACKAGE_URL = "https://download.bimcollab.com/support/bc-example-project_2025.zip"
SOURCE_PAGE = "https://helpcenter.bimcollab.com/en/articles/325099-example-projects-and-templates"
USER_AGENT = "text2ifc-dataset/1.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as stream:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)


def _canonical_hashes() -> dict[str, str]:
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


def _write(records: list[dict]) -> None:
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in sorted(records, key=lambda item: item["member_name"].casefold())
    )
    tmp = LEDGER_PATH.with_suffix(".jsonl.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, LEDGER_PATH)


def _safe_member(name: str) -> str:
    normalized = Path(name.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise RuntimeError(f"UNSAFE_ZIP_MEMBER:{name}")
    return normalized.as_posix()


def main() -> int:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    hashes = _canonical_hashes()
    records: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="bimcollab-example-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        package = tmp_root / "bc-example-project_2025.zip"
        print(f"DOWNLOAD {PACKAGE_URL}", flush=True)
        _download(PACKAGE_URL, package)
        package_sha = _sha256(package)
        package_size = package.stat().st_size
        with zipfile.ZipFile(package) as archive:
            members: list[tuple[str, bytes]] = []
            for info in archive.infolist():
                if info.is_dir():
                    continue
                safe_outer = _safe_member(info.filename)
                lower = safe_outer.lower()
                if lower.endswith(".ifc"):
                    members.append((safe_outer, archive.read(info)))
                elif lower.endswith(".ifczip"):
                    with zipfile.ZipFile(io.BytesIO(archive.read(info))) as nested:
                        for nested_info in nested.infolist():
                            if nested_info.is_dir():
                                continue
                            safe_inner = _safe_member(nested_info.filename)
                            if safe_inner.lower().endswith(".ifc"):
                                members.append((f"{safe_outer}!{safe_inner}", nested.read(nested_info)))
            print(f"IFC_MEMBERS {len(members)}", flush=True)
            for safe_name, payload in members:
                extracted = tmp_root / (hashlib.sha256(safe_name.encode()).hexdigest()[:16] + ".ifc")
                extracted.write_bytes(payload)
                digest = _sha256(extracted)
                existing = hashes.get(digest)
                filename = Path(safe_name.split("!", 1)[-1]).name
                target = TARGET_ROOT / filename
                target_rel = target.relative_to(ROOT).as_posix()
                if existing is not None and existing != target_rel:
                    status = "exact_duplicate_existing"
                    canonical = existing
                    print(f"DEDUP {filename} -> {existing}", flush=True)
                else:
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
                records.append({
                    "schema_version": "text2ifc/acquisition-record/1.0",
                    "source_id": SOURCE_ID,
                    "source_page": SOURCE_PAGE,
                    "package_url": PACKAGE_URL,
                    "package_sha256": package_sha,
                    "package_size_bytes": package_size,
                    "member_name": safe_name,
                    "sha256": digest,
                    "size_bytes": extracted.stat().st_size,
                    "status": status,
                    "canonical_path": canonical,
                    "license": "review-required",
                    "research_use": "review_required",
                    "training_use": "review_required",
                    "redistribution": "review_required",
                })
                _write(records)
    print(json.dumps({"records": len(records), "stored": sum(r["status"] == "stored_canonical" for r in records), "deduplicated": sum(r["status"] != "stored_canonical" for r in records)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
