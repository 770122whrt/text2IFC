"""Scan Archiset IFC ZIP parts without downloading the multi-GB archives.

The Archiset release stores IFCs in three very large ZIP files. This scanner
reads each central directory with HTTP Range requests, downloads only IFC
entries below 10 MiB, and applies the current project-level IFC2X3 gate.
"""

from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ifcopenshell
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/dataset-acquisition/archiset-ifc2x3-lt10-scan.jsonl"
MIB = 1024 * 1024
LIMIT = 10 * MIB
HEADERS = {"User-Agent": "text2ifc-dataset/1.0"}
URLS = {
    "ifc1": "https://media.githubusercontent.com/media/pinjusicmatea-23/performance-data-enriched-floorplan-datasets/main/datasets/ifc1.zip",
    "ifc2": "https://media.githubusercontent.com/media/pinjusicmatea-23/performance-data-enriched-floorplan-datasets/main/datasets/ifc2.zip",
    "ifc3": "https://media.githubusercontent.com/media/pinjusicmatea-23/performance-data-enriched-floorplan-datasets/main/datasets/ifc3.zip",
}
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
    "IfcMember",
    "IfcPlate",
    "IfcFooting",
    "IfcPile",
    "IfcReinforcingBar",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def range_get(url: str, start: int, end: int) -> bytes:
    response = requests.get(
        url,
        headers={**HEADERS, "Range": f"bytes={start}-{end}"},
        timeout=90,
    )
    response.raise_for_status()
    if response.status_code != 206:
        raise RuntimeError(f"range request not honored: {response.status_code} {url}")
    return response.content


def list_zip_entries(url: str) -> list[dict]:
    head = requests.head(url, headers=HEADERS, timeout=45, allow_redirects=True)
    head.raise_for_status()
    total = int(head.headers["content-length"])
    tail_size = min(total, 262144)
    tail = range_get(url, total - tail_size, total - 1)
    eocd_offset = tail.rfind(b"PK\x05\x06")
    if eocd_offset < 0:
        raise RuntimeError(f"ZIP EOCD not found: {url}")
    _, _, _, _, _, cd_size, cd_offset, _ = struct.unpack(
        "<4s4H2LH", tail[eocd_offset : eocd_offset + 22]
    )
    central = range_get(url, cd_offset, cd_offset + cd_size - 1)
    entries: list[dict] = []
    pos = 0
    while pos + 46 <= len(central) and central[pos : pos + 4] == b"PK\x01\x02":
        values = struct.unpack("<4s6H3L5H2L", central[pos : pos + 46])
        method = values[4]
        compressed_size = values[8]
        uncompressed_size = values[9]
        name_len = values[10]
        extra_len = values[11]
        comment_len = values[12]
        local_offset = values[16]
        name = central[pos + 46 : pos + 46 + name_len].decode("utf-8", "replace")
        entries.append(
            {
                "path": name,
                "method": method,
                "compressed_size": compressed_size,
                "size_bytes": uncompressed_size,
                "local_offset": local_offset,
            }
        )
        pos += 46 + name_len + extra_len + comment_len
    return entries


def extract_entry(url: str, entry: dict) -> bytes:
    local_offset = int(entry["local_offset"])
    local_header = range_get(url, local_offset, local_offset + 4095)
    values = struct.unpack("<4s5H3L2H", local_header[:30])
    name_len = values[-2]
    extra_len = values[-1]
    start = local_offset + 30 + name_len + extra_len
    compressed_size = int(entry["compressed_size"])
    payload = range_get(url, start, start + compressed_size - 1)
    method = int(entry["method"])
    if method == 8:
        data = zlib.decompress(payload, -15)
    elif method == 0:
        data = payload
    else:
        raise RuntimeError(f"unsupported ZIP compression method {method}")
    if len(data) != int(entry["size_bytes"]):
        raise RuntimeError(
            f"size mismatch {entry['path']}: {len(data)} != {entry['size_bytes']}"
        )
    return data


def local_sha_map() -> dict[str, str]:
    path = ROOT / "dataset/manifests/ifc-files.jsonl"
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        result[record["sha256"]] = record["local_path"]
    return result


def inspect_ifc(data: bytes) -> dict:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "model.ifc"
        path.write_bytes(data)
        model = ifcopenshell.open(str(path))
        count = lambda entity: len(model.by_type(entity))
        key_counts = {name: count(name) for name in KEY_CLASSES}
        metrics = {
            "project_count": count("IfcProject"),
            "site_count": count("IfcSite"),
            "building_count": count("IfcBuilding"),
            "storey_count": count("IfcBuildingStorey"),
            "containment_rel_count": count("IfcRelContainedInSpatialStructure"),
            "element_count": count("IfcElement"),
            "key_class_diversity": sum(value > 0 for value in key_counts.values()),
            "key_class_counts": key_counts,
        }
        schema = str(model.schema).upper()
        return {"schema": schema, "metrics": metrics}


def main() -> int:
    local = local_sha_map()
    seen: dict[str, str] = {}
    rows: list[dict] = []
    selected_total = 0
    for part, url in URLS.items():
        entries = [
            entry
            for entry in list_zip_entries(url)
            if entry["path"].lower().endswith(".ifc") and 0 < entry["size_bytes"] < LIMIT
        ]
        entries.sort(key=lambda entry: (entry["size_bytes"], entry["path"]))
        print(f"{part}: {len(entries)} IFC entries below 10 MiB", flush=True)
        batch_size = 12
        for batch_start in range(0, len(entries), batch_size):
            batch = entries[batch_start : batch_start + batch_size]
            with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
                futures = [executor.submit(extract_entry, url, entry) for entry in batch]
                payloads: list[bytes | Exception] = []
                for future in futures:
                    try:
                        payloads.append(future.result())
                    except Exception as exc:
                        payloads.append(exc)
            for offset, (entry, payload) in enumerate(zip(batch, payloads), start=1):
                index = batch_start + offset
                row = {
                    "source_id": "archiset-performance-floorplans",
                    "part": part,
                    "upstream_path": entry["path"],
                    "size_bytes": entry["size_bytes"],
                    "compressed_size": entry["compressed_size"],
                    "status": "error",
                    "error": None,
                }
                try:
                    if isinstance(payload, Exception):
                        raise payload
                    data = payload
                    digest = sha256(data)
                    row["sha256"] = digest
                    row["local_exact_duplicate"] = local.get(digest)
                    row["batch_exact_duplicate"] = seen.get(digest)
                    details = inspect_ifc(data)
                    row.update(details)
                    metrics = details["metrics"]
                    if details["schema"] != "IFC2X3":
                        row["status"] = "not_ifc2x3"
                    elif row["local_exact_duplicate"] or row["batch_exact_duplicate"]:
                        row["status"] = "exact_duplicate"
                    elif metrics["element_count"] <= 1:
                        row["status"] = "single_component"
                    elif not (
                        metrics["project_count"] >= 1
                        and metrics["building_count"] >= 1
                        and metrics["storey_count"] >= 1
                        and metrics["containment_rel_count"] >= 1
                        and metrics["element_count"] >= 10
                        and metrics["key_class_diversity"] >= 2
                    ):
                        row["status"] = "below_current_semantic_gate"
                    else:
                        row["status"] = "admit_candidate"
                        selected_total += 1
                    seen.setdefault(digest, entry["path"])
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"
                rows.append(row)
                print(
                    f"{part} {index}/{len(entries)} {row['status']} "
                    f"{entry['size_bytes'] / MIB:.3f} MiB {entry['path']}",
                    flush=True,
                )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"rows": len(rows), "counts": counts, "admit": selected_total}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
