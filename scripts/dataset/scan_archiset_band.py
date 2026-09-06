"""Scan one Archiset ZIP part and size band using concurrent Range fetches."""

from __future__ import annotations

import argparse
import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_SCRIPT = ROOT / "scripts/dataset/scan_archiset_ifc2x3_lt10.py"


def load_base():
    spec = importlib.util.spec_from_file_location("archiset_scan_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Archiset scanner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", choices=("ifc1", "ifc2", "ifc3"), required=True)
    parser.add_argument("--min-mib", type=float, default=3.0)
    parser.add_argument("--max-mib", type=float, default=10.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base = load_base()
    url = base.URLS[args.part]
    minimum = int(args.min_mib * base.MIB)
    maximum = int(args.max_mib * base.MIB)
    entries = [
        entry
        for entry in base.list_zip_entries(url)
        if entry["path"].lower().endswith(".ifc")
        and minimum <= entry["size_bytes"] < maximum
    ]
    entries.sort(key=lambda entry: (entry["size_bytes"], entry["path"]))
    local = base.local_sha_map()
    seen: dict[str, str] = {}
    rows: list[dict] = []

    batch_size = max(args.workers, args.workers * 2)
    for batch_start in range(0, len(entries), batch_size):
        batch = entries[batch_start : batch_start + batch_size]
        with ThreadPoolExecutor(max_workers=min(args.workers, len(batch))) as executor:
            futures = [executor.submit(base.extract_entry, url, entry) for entry in batch]
            payloads = []
            for future in futures:
                try:
                    payloads.append(future.result())
                except Exception as exc:
                    payloads.append(exc)
        for offset, (entry, payload) in enumerate(zip(batch, payloads), start=1):
            index = batch_start + offset
            row = {
                "source_id": "archiset-performance-floorplans",
                "part": args.part,
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
                digest = base.sha256(data)
                info = base.inspect_ifc(data)
                metrics = info["metrics"]
                row.update(info)
                row["sha256"] = digest
                row["local_exact_duplicate"] = local.get(digest)
                row["batch_exact_duplicate"] = seen.get(digest)
                if info["schema"] != "IFC2X3":
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
                seen.setdefault(digest, entry["path"])
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
            print(
                f"{args.part} {index}/{len(entries)} {row['status']} "
                f"{entry['size_bytes'] / base.MIB:.3f} MiB {entry['path']}",
                flush=True,
            )

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"part": args.part, "rows": len(rows), "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
