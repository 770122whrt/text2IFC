"""Scan Kaggle IFC examples for strict meaningful IFC2X3 models below 10 MiB.

Discovery only. Candidate IFC bytes are kept in .tmp and never written to dataset/external.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import re
import tempfile
import urllib.parse
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
LOCAL_MANIFEST = ROOT / "dataset/manifests/ifc-files.jsonl"
TMP_ROOT = ROOT / ".tmp/dataset-acquisition/kaggle-ifc-examples"
OUTPUT = ROOT / ".tmp/dataset-acquisition/kaggle-ifc-examples-small-ifc2x3.jsonl"
REPORT = ROOT / "docs/reports/kaggle-ifc-examples-small-ifc2x3.md"
MAX_BYTES = 10 * 1024 * 1024
MIB = 1024 * 1024
BASE = "https://www.kaggle.com/api/v1/datasets"
DATASET = "claytonmiller/example-ifc-file"
USER_AGENT = "text2ifc-dataset/1.0"
SCHEMA_RE = re.compile(rb"FILE_SCHEMA\s*\(\s*\(\s*['\"]([^'\"]+)", re.I)
KEY_CLASSES = (
    "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcOpeningElement",
    "IfcBeam", "IfcColumn", "IfcStair", "IfcRoof", "IfcSpace",
    "IfcFlowTerminal", "IfcFlowSegment", "IfcFlowFitting",
)


def _local_hashes() -> dict[str, str]:
    result = {}
    for line in LOCAL_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result[str(row["sha256"])] = str(row["local_path"])
    return result


def _files() -> list[dict[str, Any]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    result: list[dict[str, Any]] = []
    token = None
    while True:
        params = {"pageToken": token} if token else {}
        response = session.get(f"{BASE}/list/{DATASET}", params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        result.extend(payload.get("datasetFiles", []))
        token = payload.get("nextPageToken") if payload.get("hasNextPageToken") else None
        if not token:
            return result


def _count(model, cls: str) -> int:
    try:
        return len(model.by_type(cls))
    except RuntimeError:
        return 0


def _analyze_file(meta: dict[str, Any], known: dict[str, str]) -> dict[str, Any]:
    name = str(meta["name"])
    size = int(meta.get("totalBytes") or 0)
    url = f"{BASE}/download/{DATASET}/{urllib.parse.quote(name, safe='')}"
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        response.raise_for_status()
        data = response.content
        if data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                members = [i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith(".ifc")]
                if len(members) != 1:
                    return {"path": name, "size_bytes": size, "status": "ambiguous_zip_payload", "zip_ifc_members": len(members)}
                data = archive.read(members[0])
        if len(data) >= MAX_BYTES:
            return {"path": name, "size_bytes": len(data), "status": "oversize_after_download"}
        digest = hashlib.sha256(data).hexdigest()
        schema_match = SCHEMA_RE.search(data[: min(len(data), MIB)])
        schema = schema_match.group(1).decode("ascii", errors="replace").upper() if schema_match else "UNKNOWN"
        if schema != "IFC2X3":
            return {
                "path": name,
                "size_bytes": len(data),
                "size_mib": round(len(data) / MIB, 6),
                "sha256": digest,
                "schema": schema,
                "status": "not_ifc2x3",
            }
        with tempfile.TemporaryDirectory(prefix="kaggle-ifc-scan-") as temp_dir:
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
            if metrics["element_count"] <= 2:
                status = "single_component"
            elif (
                metrics["project_count"] < 1
                or metrics["building_count"] < 1
                or metrics["storey_count"] < 1
                or metrics["containment_rel_count"] < 1
                or metrics["element_count"] < 10
                or metrics["key_class_diversity"] < 3
            ):
                status = "fragment_or_narrow_fixture"
            else:
                status = "meaningful_model"
            return {
                "source_id": "kaggle-claytonmiller-ifc-examples",
                "dataset": DATASET,
                "dataset_license": "CC-BY-4.0",
                "path": name,
                "size_bytes": len(data),
                "size_mib": round(len(data) / MIB, 6),
                "sha256": digest,
                "schema": schema,
                "status": status,
                "metrics": metrics,
                "local_exact_duplicate": known.get(digest),
                "upstream_family": "open-ifc-model-repository" if name.startswith("Open IFC Model Repository ") else "intro-python-bim",
                "training_use": "review_required",
                "redistribution": "review_required",
            }
    except Exception as exc:
        return {
            "path": name,
            "size_bytes": size,
            "status": "download_or_parse_error",
            "error": f"{type(exc).__name__}:{exc}",
        }


def main() -> int:
    all_files = _files()
    small = [
        row for row in all_files
        if str(row.get("name", "")).lower().endswith(".ifc")
        and 0 < int(row.get("totalBytes") or 0) < MAX_BYTES
    ]
    known = _local_hashes()
    print(f"FILES total={len(all_files)} under10_ifc={len(small)}", flush=True)
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_analyze_file, row, known) for row in small]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            records.append(future.result())
            if index % 20 == 0:
                print(f"SCAN {index}/{len(futures)}", flush=True)

    meaningful = [r for r in records if r.get("status") == "meaningful_model"]
    local_dups = [r for r in meaningful if r.get("local_exact_duplicate")]
    new = [r for r in meaningful if not r.get("local_exact_duplicate")]
    by_sha: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in new:
        by_sha[str(row["sha256"])].append(row)
    unique = []
    for digest, group in by_sha.items():
        representative = sorted(group, key=lambda r: (r["size_bytes"], r["path"]))[0]
        representative["batch_exact_aliases"] = [r["path"] for r in group if r is not representative]
        unique.append(representative)

    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in sorted(records, key=lambda r: (r.get("status", ""), r.get("size_bytes", 0), r.get("path", "")))),
        encoding="utf-8",
    )

    counts = Counter(r.get("status", "unknown") for r in records)
    lines = [
        "# Kaggle IFC Examples — Strict Small IFC2X3 Scan",
        "",
        "> Discovery-only scan of `claytonmiller/example-ifc-file`. The Kaggle dataset is CC BY 4.0; original model training/redistribution rights remain review-required where upstream provenance is Open IFC Model Repository.",
        "",
        f"- Listed files: **{len(all_files)}**",
        f"- IFC files `<10 MiB`: **{len(small)}**",
        f"- Meaningful IFC2X3 paths: **{len(meaningful)}**",
        f"- Meaningful exact duplicates already local: **{len(local_dups)}**",
        f"- New unique meaningful SHA candidates: **{len(unique)}**",
        f"- `<1 MiB` new unique: **{sum(r['size_bytes'] < MIB for r in unique)}**",
        f"- `1–3 MiB` new unique: **{sum(MIB <= r['size_bytes'] < 3*MIB for r in unique)}**",
        f"- `3–10 MiB` new unique: **{sum(3*MIB <= r['size_bytes'] < 10*MIB for r in unique)}**",
        "",
        "## Scan outcomes",
        "",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- `{key}`: **{value}**")
    lines += [
        "",
        "## New meaningful unique candidates",
        "",
        "| MiB | Upstream | Elements | Storeys | Classes | Path |",
        "| ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for row in sorted(unique, key=lambda r: (r["size_bytes"], r["path"])):
        m = row["metrics"]
        lines.append(f"| {row['size_mib']:.3f} | `{row['upstream_family']}` | {m['element_count']} | {m['storey_count']} | {m['key_class_diversity']} | `{row['path']}` |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "scanned": len(records),
        "outcomes": dict(sorted(counts.items())),
        "meaningful_paths": len(meaningful),
        "meaningful_local_duplicates": len(local_dups),
        "new_unique_meaningful": len(unique),
        "new_lt1": sum(r["size_bytes"] < MIB for r in unique),
        "new_1to3": sum(MIB <= r["size_bytes"] < 3*MIB for r in unique),
        "new_3to10": sum(3*MIB <= r["size_bytes"] < 10*MIB for r in unique),
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
