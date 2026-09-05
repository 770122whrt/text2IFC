"""Acquire buildingSMART Community IFC2X3 sample files with exact deduplication.

This downloader intentionally does not require git-lfs. It resolves Git LFS pointer
metadata from GitHub, downloads the corresponding media objects, verifies the LFS
SHA-256 and byte size, and records every upstream path in an acquisition ledger.
Exact duplicates are represented as provenance aliases rather than duplicate files.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "buildingsmart-community"
REPO = "buildingsmart-community/Community-Sample-Test-Files"
REF = "main"
PREFIX = "IFC 2.3.0.1 (IFC 2x3)/"
TARGET_ROOT = ROOT / "dataset" / "external" / SOURCE_ID
LEDGER_PATH = ROOT / "dataset" / "manifests" / "ifc-acquisitions.jsonl"
USER_AGENT = "text2ifc-dataset/1.0"
MAX_AUTO_RETAIN_BYTES = 100 * 1024 * 1024
REJECTED_BY_USER_PATHS = {
    "IFC 2.3.0.1 (IFC 2x3)/SDK - S1/bSDD_references_example.ifc",
}
APPROVED_LARGE_PATHS: set[str] = set()


def _request(url: str):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=120
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_existing_ledger() -> list[dict]:
    if not LEDGER_PATH.is_file():
        return []
    return [
        json.loads(line)
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_ledger(records: list[dict]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(
        records,
        key=lambda item: (
            str(item.get("source_id", "")),
            str(item.get("upstream_path", "")),
        ),
    )
    text = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for item in ordered
    )
    temp = LEDGER_PATH.with_suffix(LEDGER_PATH.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, LEDGER_PATH)


def _canonical_hashes() -> dict[str, str]:
    manifest = ROOT / "dataset" / "manifests" / "ifc-files.jsonl"
    result: dict[str, str] = {}
    if not manifest.is_file():
        return result
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        result[str(record["sha256"])] = str(record["local_path"])
    return result


def _tree_paths() -> list[str]:
    url = f"https://api.github.com/repos/{REPO}/git/trees/{REF}?recursive=1"
    with _request(url) as response:
        payload = json.load(response)
    return sorted(
        item["path"]
        for item in payload["tree"]
        if item.get("type") == "blob"
        and item["path"].startswith(PREFIX)
        and item["path"].lower().endswith(".ifc")
    )


def _lfs_metadata(path: str) -> tuple[str, int]:
    encoded = urllib.parse.quote(path, safe="/")
    url = f"https://raw.githubusercontent.com/{REPO}/{REF}/{encoded}"
    with _request(url) as response:
        text = response.read(1024).decode("utf-8", errors="replace")
    oid: str | None = None
    size: int | None = None
    for line in text.splitlines():
        if line.startswith("oid sha256:"):
            oid = line.partition(":")[2].strip()
        elif line.startswith("size "):
            size = int(line.partition(" ")[2])
    if oid is None or size is None:
        raise RuntimeError(f"NOT_LFS_POINTER:{path}")
    return oid, size


def _download(path: str, target: Path, *, expected_sha256: str, expected_size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    encoded = urllib.parse.quote(path, safe="/")
    url = f"https://media.githubusercontent.com/media/{REPO}/{REF}/{encoded}"
    digest = hashlib.sha256()
    size = 0
    with _request(url) as response, part.open("wb") as stream:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)
            digest.update(chunk)
            size += len(chunk)
    actual_sha256 = digest.hexdigest()
    if size != expected_size:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"SIZE_MISMATCH:{path}:{size}!={expected_size}")
    if actual_sha256 != expected_sha256:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"SHA_MISMATCH:{path}:{actual_sha256}!={expected_sha256}")
    os.replace(part, target)


def main() -> int:
    paths = _tree_paths()
    if len(paths) != 81:
        print(f"WARNING upstream IFC2X3 path count changed: {len(paths)}", file=sys.stderr)

    existing_ledger = _read_existing_ledger()
    other_records = [item for item in existing_ledger if item.get("source_id") != SOURCE_ID]
    completed_by_path = {
        str(item["upstream_path"]): item
        for item in existing_ledger
        if item.get("source_id") == SOURCE_ID
    }
    known_hashes = _canonical_hashes()
    within_source: dict[str, str] = {}
    new_records: dict[str, dict] = {}

    # Rehydrate already-completed canonical hashes so the script is resumable.
    for item in completed_by_path.values():
        digest = str(item.get("sha256", ""))
        canonical = item.get("canonical_path")
        if len(digest) == 64 and isinstance(canonical, str):
            if (ROOT / canonical).is_file():
                within_source.setdefault(digest, canonical)
                known_hashes.setdefault(digest, canonical)

    for index, upstream_path in enumerate(paths, start=1):
        oid, expected_size = _lfs_metadata(upstream_path)
        rel = upstream_path[len(PREFIX) :]
        target = TARGET_ROOT / rel
        target_rel = target.relative_to(ROOT).as_posix()

        if upstream_path in REJECTED_BY_USER_PATHS:
            target.unlink(missing_ok=True)
            new_records[upstream_path] = {
                "schema_version": "text2ifc/ifc-acquisition/1.0",
                "source_id": SOURCE_ID,
                "repository": REPO,
                "ref": REF,
                "upstream_path": upstream_path,
                "sha256": oid,
                "size_bytes": expected_size,
                "status": "rejected_by_user_size",
                "canonical_path": None,
                "license": "CC-BY-4.0",
                "research_use": "allowed_with_attribution",
                "training_use": "review_required",
                "redistribution": "allowed_with_attribution",
            }
            _write_ledger(other_records + list(new_records.values()))
            print(f"REJECT_SIZE {index}/{len(paths)} {expected_size} {upstream_path}", flush=True)
            continue

        if expected_size > MAX_AUTO_RETAIN_BYTES and upstream_path not in APPROVED_LARGE_PATHS:
            canonical = target_rel if target.is_file() else None
            new_records[upstream_path] = {
                "schema_version": "text2ifc/ifc-acquisition/1.0",
                "source_id": SOURCE_ID,
                "repository": REPO,
                "ref": REF,
                "upstream_path": upstream_path,
                "sha256": oid,
                "size_bytes": expected_size,
                "status": "manual_review_required_size_existing" if canonical else "manual_review_required_size_not_downloaded",
                "canonical_path": canonical,
                "license": "CC-BY-4.0",
                "research_use": "allowed_with_attribution",
                "training_use": "review_required",
                "redistribution": "allowed_with_attribution",
            }
            _write_ledger(other_records + list(new_records.values()))
            print(f"REVIEW_SIZE {index}/{len(paths)} {expected_size} {upstream_path}", flush=True)
            continue

        prior = completed_by_path.get(upstream_path)
        if prior is not None:
            canonical = prior.get("canonical_path")
            if isinstance(canonical, str) and (ROOT / canonical).is_file():
                print(f"SKIP {index}/{len(paths)} {upstream_path}", flush=True)
                new_records[upstream_path] = prior
                continue

        canonical = known_hashes.get(oid) or within_source.get(oid)
        if canonical is not None:
            status = "exact_duplicate_existing"
            print(
                f"DEDUP {index}/{len(paths)} {upstream_path} -> {canonical}",
                flush=True,
            )
        else:
            if target.is_file():
                actual = _sha256(target)
                if actual != oid:
                    raise RuntimeError(f"TARGET_CONFLICT:{target_rel}:{actual}!={oid}")
            else:
                print(
                    f"DOWNLOAD {index}/{len(paths)} {expected_size} {upstream_path}",
                    flush=True,
                )
                _download(
                    upstream_path,
                    target,
                    expected_sha256=oid,
                    expected_size=expected_size,
                )
            canonical = target_rel
            status = "stored_canonical"
            known_hashes[oid] = canonical
            within_source[oid] = canonical

        new_records[upstream_path] = {
            "schema_version": "text2ifc/ifc-acquisition/1.0",
            "source_id": SOURCE_ID,
            "repository": REPO,
            "ref": REF,
            "upstream_path": upstream_path,
            "sha256": oid,
            "size_bytes": expected_size,
            "status": status,
            "canonical_path": canonical,
            "license": "CC-BY-4.0",
            "research_use": "allowed_with_attribution",
            "training_use": "review_required",
            "redistribution": "allowed_with_attribution",
        }
        _write_ledger(other_records + list(new_records.values()))

    _write_ledger(other_records + list(new_records.values()))
    stored = sum(item["status"] == "stored_canonical" for item in new_records.values())
    deduped = len(new_records) - stored
    total_bytes = sum(item["size_bytes"] for item in new_records.values())
    print(
        json.dumps(
            {
                "source_id": SOURCE_ID,
                "upstream_paths": len(new_records),
                "stored_canonical": stored,
                "deduplicated_paths": deduped,
                "upstream_bytes": total_bytes,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
