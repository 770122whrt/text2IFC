"""Acquire current KIT IFC examples from IFC Wiki with isolated provenance ledger."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "kit-examples"
TARGET_ROOT = ROOT / "dataset/external/kit-examples"
LEDGER_PATH = ROOT / "dataset/manifests/acquisition-kit-examples.jsonl"
USER_AGENT = "text2ifc-dataset/1.0"
PAGE = "https://www.ifcwiki.org/index.php?title=KIT_IFC_Examples&oldid=552"

ARTIFACTS = (
    ("FZK Haus", "https://www.ifcwiki.org/images/e/e3/AC20-FZK-Haus.ifc", "ifc"),
    ("Office Building", "https://www.ifcwiki.org/images/9/98/AC20-Institute-Var-2.ifc", "ifc"),
    ("Smiley West", "https://www.ifcwiki.org/images/c/c8/AC-20-Smiley-West-10-Bldg.zip", "zip"),
    ("KIT Bridge", "https://www.ifcwiki.org/images/0/09/KIT-Bridge.zip", "zip"),
    ("KIT Simple Road", "https://www.ifcwiki.org/images/2/24/KIT-Simple-Road-Test-Web-IFC4x3_RC2.zip", "zip"),
)


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


def _write_ledger(records: list[dict]) -> None:
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in sorted(records, key=lambda item: (item["artifact"], item["member_name"]))
    )
    temp = LEDGER_PATH.with_suffix(".jsonl.tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, LEDGER_PATH)


def _safe_member(name: str) -> str:
    normalized = Path(name.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise RuntimeError(f"UNSAFE_ZIP_MEMBER:{name}")
    return normalized.as_posix()


def main() -> int:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    canonical = _canonical_hashes()
    records: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="kit-ifc-acquire-") as temp_dir:
        temp_root = Path(temp_dir)
        for artifact, url, kind in ARTIFACTS:
            package = temp_root / Path(url).name
            print(f"DOWNLOAD {artifact}: {url}", flush=True)
            _download(url, package)
            package_sha = _sha256(package)
            package_size = package.stat().st_size

            members: list[tuple[str, Path]] = []
            if kind == "ifc":
                members.append((package.name, package))
            else:
                with zipfile.ZipFile(package) as archive:
                    for info in archive.infolist():
                        safe_name = _safe_member(info.filename)
                        if info.is_dir() or not safe_name.lower().endswith(".ifc"):
                            continue
                        extracted = temp_root / (hashlib.sha256(safe_name.encode()).hexdigest()[:12] + ".ifc")
                        with archive.open(info) as source, extracted.open("wb") as target:
                            while True:
                                chunk = source.read(1024 * 1024)
                                if not chunk:
                                    break
                                target.write(chunk)
                        members.append((safe_name, extracted))

            if not members:
                raise RuntimeError(f"NO_IFC_IN_ARTIFACT:{artifact}")

            for member_name, source in members:
                digest = _sha256(source)
                existing = canonical.get(digest)
                filename = Path(member_name).name
                target = TARGET_ROOT / artifact.replace(" ", "-").lower() / filename
                if existing is not None:
                    status = "exact_duplicate_existing"
                    canonical_path = existing
                    print(f"DEDUP {artifact}/{member_name} -> {existing}", flush=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists() and _sha256(target) != digest:
                        raise RuntimeError(f"TARGET_CONFLICT:{target.relative_to(ROOT).as_posix()}")
                    if not target.exists():
                        with source.open("rb") as src, target.open("wb") as dst:
                            while True:
                                chunk = src.read(1024 * 1024)
                                if not chunk:
                                    break
                                dst.write(chunk)
                    canonical_path = target.relative_to(ROOT).as_posix()
                    canonical[digest] = canonical_path
                    status = "stored_canonical"
                    print(f"STORE {canonical_path} sha={digest[:12]}", flush=True)

                records.append(
                    {
                        "schema_version": "text2ifc/acquisition-record/1.0",
                        "source_id": SOURCE_ID,
                        "source_page": PAGE,
                        "source_revision": "ifcwiki-oldid-552",
                        "artifact": artifact,
                        "artifact_url": url,
                        "artifact_sha256": package_sha,
                        "artifact_size_bytes": package_size,
                        "member_name": member_name,
                        "sha256": digest,
                        "size_bytes": source.stat().st_size,
                        "status": status,
                        "canonical_path": canonical_path,
                        "license": "source-states-unrestricted-use-with-publication-attribution",
                        "research_use": "allowed_with_attribution",
                        "training_use": "review_required",
                        "redistribution": "review_required",
                    }
                )
                _write_ledger(records)

    print(json.dumps({"records": len(records), "stored": sum(r["status"] == "stored_canonical" for r in records), "deduplicated": sum(r["status"] != "stored_canonical" for r in records)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
