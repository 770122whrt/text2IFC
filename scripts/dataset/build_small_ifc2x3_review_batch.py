"""Build the pre-review batch of meaningful public IFC2X3 models below 10 MiB.

This script is discovery-only: it never writes candidate IFC files into dataset/external.
Raw discovery evidence is written under .tmp/ (gitignored), while the review report is
written under docs/reports/.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import ssl
import tempfile
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import certifi
import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
LOCAL_MANIFEST = ROOT / "dataset/manifests/ifc-files.jsonl"
TMP_OUTPUT = ROOT / ".tmp/dataset-acquisition/ifc2x3-small-review-batch.jsonl"
REPORT = ROOT / "docs/reports/ifc2x3-small-model-review-batch.md"
MAX_BYTES = 10 * 1024 * 1024
MIB = 1024 * 1024
USER_AGENT = "text2ifc-dataset-review-batch/1.0"
SCHEMA_RE = re.compile(rb"FILE_SCHEMA\s*\(\s*\(\s*['\"]([^'\"]+)", re.I)

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

GITHUB_REPOS = (
    "xeokit/xeokit-model-conversion-tests",
    "viktor-platform/ifc-sample-models",
    "youshengCode/IfcSampleFiles",
    "bo-codes/ifc-examples",
)


def _local_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in LOCAL_MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result[str(row["sha256"])] = str(row["local_path"])
    return result


def _count(model: Any, ifc_class: str) -> int:
    try:
        return len(model.by_type(ifc_class))
    except RuntimeError:
        return 0


def _meaningfulness(data: bytes) -> tuple[str, dict[str, Any], str | None]:
    try:
        with tempfile.TemporaryDirectory(prefix="ifc2x3-review-") as temp_dir:
            path = Path(temp_dir) / "candidate.ifc"
            path.write_bytes(data)
            model = ifcopenshell.open(str(path))
            schema = str(model.schema).upper()
            if schema != "IFC2X3":
                return "not_ifc2x3", {}, None
            key_counts = {name: _count(model, name) for name in KEY_CLASSES}
            metrics = {
                "entity_count": sum(1 for _ in model),
                "project_count": _count(model, "IfcProject"),
                "site_count": _count(model, "IfcSite"),
                "building_count": _count(model, "IfcBuilding"),
                "storey_count": _count(model, "IfcBuildingStorey"),
                "product_count": _count(model, "IfcProduct"),
                "element_count": _count(model, "IfcElement"),
                "containment_rel_count": _count(model, "IfcRelContainedInSpatialStructure"),
                "aggregate_rel_count": _count(model, "IfcRelAggregates"),
                "key_class_counts": key_counts,
                "key_class_diversity": sum(value > 0 for value in key_counts.values()),
            }
            if metrics["element_count"] <= 2:
                return "single_component", metrics, None
            if (
                metrics["project_count"] < 1
                or metrics["building_count"] < 1
                or metrics["storey_count"] < 1
                or metrics["containment_rel_count"] < 1
                or metrics["element_count"] < 10
                or metrics["key_class_diversity"] < 3
            ):
                return "fragment_or_narrow_fixture", metrics, None
            return "meaningful_model", metrics, None
    except Exception as exc:
        return "invalid", {}, f"{type(exc).__name__}:{exc}"


def _schema(data: bytes) -> str:
    match = SCHEMA_RE.search(data[: min(len(data), MIB)])
    return match.group(1).decode("ascii", errors="replace").upper() if match else "UNKNOWN"


def _github_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        return json.load(response)


def _download(url: str, *, limit: int = MAX_BYTES + 1) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        return response.read(limit)


def _scan_github_repo(repo: str, known: dict[str, str]) -> list[dict[str, Any]]:
    meta = _github_json(f"https://api.github.com/repos/{repo}")
    branch = str(meta["default_branch"])
    tree = _github_json(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1")
    license_info = meta.get("license") or {}
    records: list[dict[str, Any]] = []
    members = [
        item
        for item in tree.get("tree", [])
        if item.get("type") == "blob"
        and str(item.get("path", "")).lower().endswith(".ifc")
        and isinstance(item.get("size"), int)
        and 0 < int(item["size"]) < MAX_BYTES
    ]
    print(f"GITHUB {repo} under10_ifc={len(members)}", flush=True)
    for item in members:
        path = str(item["path"])
        encoded_path = urllib.parse.quote(path, safe="/")
        raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{encoded_path}"
        try:
            data = _download(raw_url)
            if len(data) > MAX_BYTES:
                continue
            schema = _schema(data)
            if schema != "IFC2X3":
                continue
            digest = hashlib.sha256(data).hexdigest()
            local = known.get(digest)
            meaningfulness, metrics, error = _meaningfulness(data)
            records.append(
                {
                    "source_kind": "github",
                    "source_id": repo.replace("/", "--"),
                    "repository": repo,
                    "repository_license_spdx": license_info.get("spdx_id"),
                    "repository_license_name": license_info.get("name"),
                    "path": path,
                    "download_url": raw_url,
                    "size_bytes": len(data),
                    "size_mib": round(len(data) / MIB, 6),
                    "schema": schema,
                    "sha256": digest,
                    "local_exact_duplicate": local,
                    "meaningfulness": meaningfulness,
                    "metrics": metrics,
                    "error": error,
                    "model_rights": "review_required_unless_source_explicitly_covers_model_contents",
                }
            )
        except Exception as exc:
            records.append(
                {
                    "source_kind": "github",
                    "source_id": repo.replace("/", "--"),
                    "repository": repo,
                    "path": path,
                    "size_bytes": int(item["size"]),
                    "meaningfulness": "download_error",
                    "error": f"{type(exc).__name__}:{exc}",
                }
            )
    return records


class HTTPRangeFile(io.RawIOBase):
    """Minimal seekable HTTP reader for zipfile using Range requests."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        head = self.session.head(url, allow_redirects=True, timeout=60)
        head.raise_for_status()
        self.size = int(head.headers["Content-Length"])
        self.pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            new = offset
        elif whence == os.SEEK_CUR:
            new = self.pos + offset
        elif whence == os.SEEK_END:
            new = self.size + offset
        else:
            raise ValueError(whence)
        if new < 0:
            raise ValueError("negative seek")
        self.pos = min(new, self.size)
        return self.pos

    def read(self, size: int = -1) -> bytes:
        if self.pos >= self.size:
            return b""
        if size is None or size < 0:
            end = self.size - 1
        else:
            end = min(self.size - 1, self.pos + size - 1)
        response = self.session.get(
            self.url,
            headers={"Range": f"bytes={self.pos}-{end}"},
            timeout=120,
            allow_redirects=True,
        )
        response.raise_for_status()
        data = response.content
        requested = end - self.pos + 1
        if len(data) > requested:
            data = data[:requested]
        self.pos += len(data)
        return data


def _zenodo_gni_files() -> list[dict[str, Any]]:
    response = requests.get(
        "https://zenodo.org/api/records/19722012",
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    result = []
    for item in payload.get("files", []):
        key = str(item.get("key", ""))
        if key not in {"2025_BIMfundamentals.zip", "2026_BIMprojects.zip"}:
            continue
        links = item.get("links") or {}
        url = links.get("content") or links.get("self")
        if url:
            result.append({"key": key, "url": str(url), "size": item.get("size")})
    return result


def _scan_gni(known: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for package in _zenodo_gni_files():
        print(f"GNI_INDEX {package['key']} remote_bytes={package.get('size')}", flush=True)
        remote = HTTPRangeFile(package["url"])
        with zipfile.ZipFile(remote) as archive:
            members = [
                info
                for info in archive.infolist()
                if not info.is_dir()
                and info.filename.lower().endswith(".ifc")
                and 0 < info.file_size < MAX_BYTES
            ]
            print(f"GNI {package['key']} under10_ifc={len(members)}", flush=True)
            for index, info in enumerate(members, start=1):
                try:
                    data = archive.read(info)
                    schema = _schema(data)
                    if schema != "IFC2X3":
                        continue
                    digest = hashlib.sha256(data).hexdigest()
                    local = known.get(digest)
                    meaningfulness, metrics, error = _meaningfulness(data)
                    records.append(
                        {
                            "source_kind": "zenodo",
                            "source_id": "gni-bim-dataset",
                            "repository": "ZijianWang-ZW/GNI-BIM-Dataset",
                            "zenodo_record": "19722012",
                            "package": package["key"],
                            "path": info.filename,
                            "size_bytes": len(data),
                            "size_mib": round(len(data) / MIB, 6),
                            "schema": schema,
                            "sha256": digest,
                            "local_exact_duplicate": local,
                            "meaningfulness": meaningfulness,
                            "metrics": metrics,
                            "error": error,
                            "license": "CC-BY-4.0",
                            "model_rights": "explicit_dataset_license_cc_by_4_0",
                        }
                    )
                except Exception as exc:
                    records.append(
                        {
                            "source_kind": "zenodo",
                            "source_id": "gni-bim-dataset",
                            "package": package["key"],
                            "path": info.filename,
                            "size_bytes": info.file_size,
                            "meaningfulness": "download_error",
                            "error": f"{type(exc).__name__}:{exc}",
                        }
                    )
                if index % 25 == 0:
                    print(f"GNI_PROGRESS {package['key']} {index}/{len(members)}", flush=True)
    return records


def _structural_signature(row: dict[str, Any]) -> tuple[Any, ...] | None:
    metrics = row.get("metrics") or {}
    if not metrics:
        return None
    counts = metrics.get("key_class_counts") or {}
    return (
        metrics.get("element_count"),
        metrics.get("storey_count"),
        metrics.get("key_class_diversity"),
        tuple(sorted((str(k), int(v)) for k, v in counts.items())),
    )


def _write_outputs(records: list[dict[str, Any]]) -> None:
    meaningful = [
        row
        for row in records
        if row.get("schema") == "IFC2X3" and row.get("meaningfulness") == "meaningful_model"
    ]
    exact_duplicates = [row for row in meaningful if row.get("local_exact_duplicate")]
    new = [row for row in meaningful if not row.get("local_exact_duplicate")]

    by_sha: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in new:
        by_sha[str(row["sha256"])].append(row)
    sha_unique = [sorted(group, key=lambda r: (r["size_bytes"], r["source_id"], r["path"]))[0] for group in by_sha.values()]
    for row in sha_unique:
        group = by_sha[str(row["sha256"])]
        row["batch_exact_aliases"] = [f"{x['source_id']}:{x['path']}" for x in group if x is not row]

    by_signature: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in sha_unique:
        signature = _structural_signature(row)
        if signature is not None:
            by_signature[signature].append(row)
    for group_id, group in enumerate((g for g in by_signature.values() if len(g) > 1), start=1):
        for row in group:
            row["near_duplicate_group"] = f"structure-{group_id:03d}"

    TMP_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    TMP_OUTPUT.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for row in sorted(records, key=lambda r: (r.get("source_id", ""), r.get("size_bytes", 0), r.get("path", "")))
        ),
        encoding="utf-8",
    )

    size_counts = {
        "lt1": sum(row["size_bytes"] < MIB for row in sha_unique),
        "1to3": sum(MIB <= row["size_bytes"] < 3 * MIB for row in sha_unique),
        "3to10": sum(3 * MIB <= row["size_bytes"] < 10 * MIB for row in sha_unique),
    }
    source_counts = Counter(row["source_id"] for row in sha_unique)
    excluded_counts = Counter(row.get("meaningfulness", "unknown") for row in records if row.get("meaningfulness") != "meaningful_model")

    lines = [
        "# IFC2X3 Small Model Review Batch",
        "",
        "> Pre-admission review batch. No IFC in this report is canonical unless `local_exact_duplicate` points to an existing canonical file. New candidates remain outside `dataset/external/` until human review.",
        "",
        "## Summary",
        "",
        f"- New meaningful IFC2X3 SHA candidates `<10 MiB`: **{len(sha_unique)}**",
        f"- `<1 MiB`: **{size_counts['lt1']}**",
        f"- `1–3 MiB`: **{size_counts['1to3']}**",
        f"- `3–10 MiB`: **{size_counts['3to10']}**",
        f"- Meaningful exact duplicates already canonical locally: **{len(exact_duplicates)}**",
        f"- Batch exact duplicate aliases collapsed: **{sum(len(v) - 1 for v in by_sha.values())}**",
        f"- Structural near-duplicate groups: **{sum(len(v) > 1 for v in by_signature.values())}**",
        "- Raw discovery evidence: `.tmp/dataset-acquisition/ifc2x3-small-review-batch.jsonl` (gitignored)",
        "",
        "### New candidates by source",
        "",
    ]
    for source_id, count in sorted(source_counts.items()):
        lines.append(f"- `{source_id}`: **{count}**")
    lines += ["", "### Excluded during discovery", ""]
    for label, count in sorted(excluded_counts.items()):
        lines.append(f"- `{label}`: **{count}**")

    lines += [
        "",
        "## New meaningful candidates",
        "",
        "| Size (MiB) | Source | Model rights | Elements | Storeys | Classes | Near-dup | Path |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in sorted(sha_unique, key=lambda r: (r["size_bytes"], r["source_id"], r["path"])):
        metrics = row.get("metrics") or {}
        rights = row.get("model_rights") or row.get("repository_license_spdx") or "review_required"
        lines.append(
            f"| {row['size_mib']:.3f} | `{row['source_id']}` | `{rights}` | {metrics.get('element_count', '')} | {metrics.get('storey_count', '')} | {metrics.get('key_class_diversity', '')} | `{row.get('near_duplicate_group', '')}` | `{row['path']}` |"
        )

    lines += [
        "",
        "## Meaningful exact duplicates already local",
        "",
        "| Size (MiB) | Source path | Local canonical path |",
        "| ---: | --- | --- |",
    ]
    for row in sorted(exact_duplicates, key=lambda r: (r["size_bytes"], r["source_id"], r["path"])):
        lines.append(
            f"| {row['size_mib']:.3f} | `{row['source_id']}:{row['path']}` | `{row['local_exact_duplicate']}` |"
        )
    lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "records_scanned": len(records),
                "new_meaningful_sha": len(sha_unique),
                "new_lt1": size_counts["lt1"],
                "new_1to3": size_counts["1to3"],
                "new_3to10": size_counts["3to10"],
                "meaningful_local_duplicates": len(exact_duplicates),
                "structural_near_duplicate_groups": sum(len(v) > 1 for v in by_signature.values()),
                "by_source": dict(sorted(source_counts.items())),
                "excluded": dict(sorted(excluded_counts.items())),
            },
            sort_keys=True,
        )
    )


def main() -> int:
    known = _local_hashes()
    records: list[dict[str, Any]] = []
    try:
        records.extend(_scan_gni(known))
    except Exception as exc:
        print(f"GNI_SCAN_ERROR {type(exc).__name__}:{exc}", flush=True)
    for repo in GITHUB_REPOS:
        try:
            records.extend(_scan_github_repo(repo, known))
        except Exception as exc:
            print(f"GITHUB_SCAN_ERROR {repo} {type(exc).__name__}:{exc}", flush=True)
    _write_outputs(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
