"""Assemble one checked IFC per RVT, with all source and failure states retained."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import shutil

from pipeline import BASE, conversion_blocker, safe_target, sha256, write_new_json


def choose_passes(outcomes: list[dict]) -> dict[str, dict]:
    chosen = {}
    for row in outcomes:
        if row["status"] != "technical_candidate":
            continue
        aid = row["inventory_id"]
        if aid in chosen and chosen[aid]["ifc_sha256"] != row["ifc_sha256"]:
            raise ValueError(f"COMPETING_PASSING_OUTPUTS:{aid}")
        chosen.setdefault(aid, row)
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collections", nargs="+", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--asset-index", type=Path, default=BASE / "asset-index-expanded.json")
    args = parser.parse_args()
    output = safe_target(BASE / "IFC", args.name)
    if output.exists():
        raise ValueError("COLLECTION_ALREADY_EXISTS")
    index = json.loads(args.asset_index.read_text(encoding="utf-8"))
    assets = {r["inventory_id"]: r for r in index["assets"]}
    policies = {r["source_name"]: r for r in json.loads((BASE / "review-20260913/source-review-expanded.json").read_text(encoding="utf-8"))["sources"]}
    outcomes = []
    history = defaultdict(list)
    for run in args.collections:
        manifest = safe_target(BASE / "IFC", run) / "manifest.json"
        for r in json.loads(manifest.read_text(encoding="utf-8"))["outcomes"]:
            enriched = {**r, "selected_collection": run}
            outcomes.append(enriched)
            history[r["inventory_id"]].append({"run": run, "status": r["status"]})
    selected = choose_passes(outcomes)
    checks = {}
    # Check every original RVT and every selected IFC/report before copying.
    for aid, row in assets.items():
        if sha256(safe_target(BASE, row["local_path"])) != row["sha256"]:
            raise ValueError(f"RVT_SOURCE_CHANGED:{aid}")
    for aid, chosen in selected.items():
        asset = assets[aid]
        if conversion_blocker(asset, policies):
            raise ValueError(f"SOURCE_NOT_ELIGIBLE:{aid}")
        src = safe_target(BASE, chosen["ifc_path"])
        if sha256(src) != chosen["ifc_sha256"]:
            raise ValueError(f"IFC_HASH_MISMATCH:{aid}")
        folder = BASE / "runs" / chosen["selected_collection"] / aid
        if chosen.get("validation_report"):
            report = safe_target(BASE, chosen["validation_report"])
        else:
            report = folder / ("validation.json" if chosen.get("parent_attempt") else "normalized-validation.json")
        v = json.loads(report.read_text(encoding="utf-8"))
        geometry = v.get("geometry", {})
        if not (v.get("technical_candidate") and v.get("schema") == "IFC2X3" and v.get("native_error_count") == 0
                and v["sha256"] == chosen["ifc_sha256"] and geometry.get("failed") == 0
                and geometry.get("checked", 0) == geometry.get("represented_products") and geometry.get("checked", 0) > 0
                and v.get("building_body_elements", 0) > 0 and v.get("memory_roundtrip_reopen")):
            raise ValueError(f"VALIDATION_GATE_FAILED:{aid}")
        checks[aid] = {"report": report.relative_to(BASE).as_posix(), "data": v}
    rows = []
    for aid, asset in assets.items():
        policy = policies[asset["source_name"]]
        record = {"inventory_id": aid, "source_name": asset["source_name"], "original_filename": asset["filename"],
                  "rvt_path_from_RVT_directory": asset["local_path"], "rvt_sha256": asset["sha256"],
                  "source_url": policy["source_url"], "license": policy["license"],
                  "source_training_rights_supported": policy["training_use_supported_by_source_evidence"],
                  "independent_building": "not_established", "rvt_fidelity": "not_verified", "training_split_assigned": False,
                  "provisional_leakage_group": asset["source_name"], "group_basis": "conservative_source_group_not_a_building_count",
                  "attempts": history.get(aid, []), "dependencies": asset.get("dependencies", [])}
        if asset["source_name"] == "UFH":
            record["provisional_leakage_group"] = "UFH/" + asset["filename"].split("_")[0].split(".")[0]
        if aid in selected:
            chosen = selected[aid]
            dest = safe_target(output, f"{asset['source_name']}/{aid}.ifc")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with safe_target(BASE, chosen["ifc_path"]).open("rb") as src, dest.open("xb") as dst:
                shutil.copyfileobj(src, dst)
            if sha256(dest) != chosen["ifc_sha256"]:
                raise ValueError(f"ASSEMBLED_COPY_MISMATCH:{aid}")
            v = checks[aid]["data"]
            record.update(status="technical_candidate", ifc_path=dest.relative_to(output).as_posix(),
                          ifc_sha256=chosen["ifc_sha256"], ifc_bytes=dest.stat().st_size,
                          validation_report_from_RVT_directory=checks[aid]["report"],
                          selected_attempt_from_RVT_directory=f"runs/{chosen['selected_collection']}/{aid}",
                          native_error_count=0, geometry_checked=v["geometry"]["checked"], geometry_failed=0,
                          counts=v["counts"], building_body_elements=v["building_body_elements"])
        else:
            record["status"] = conversion_blocker(asset, policies) or (history[aid][-1]["status"] if history.get(aid) else "not_attempted")
        rows.append(record)
    passing = [r for r in rows if r["status"] == "technical_candidate"]
    summary = {"schema": "text2ifc/local-ifc-dataset/1.0", "source_inventory": args.asset_index.name,
               "rvt_unique_count": len(rows), "ifc_file_count": len(passing),
               "ifc_unique_sha256_count": len({r["ifc_sha256"] for r in passing}),
               "ifc_bytes": sum(r["ifc_bytes"] for r in passing), "independent_building_count": None,
               "ifc_by_source": dict(Counter(r["source_name"] for r in passing)),
               "status_counts": dict(Counter(r["status"] for r in rows)),
               "source_rights_supported_ifc_count": sum(r["source_training_rights_supported"] for r in passing),
               "geometry_products_checked": sum(r["geometry_checked"] for r in passing),
               "scope": "IFC2X3 schema+EXPRESS, all represented products geometry, reopen and explicit normalization preservation. Not MVD/design-code certification or RVT completeness proof.",
               "canonical_manifests_changed": False, "assets": rows}
    write_new_json(output / "manifest.json", summary)
    columns = ["inventory_id", "source_name", "original_filename", "status", "ifc_path", "ifc_bytes", "ifc_sha256", "source_training_rights_supported", "provisional_leakage_group", "validation_report_from_RVT_directory"]
    with (output / "inventory.csv").open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({k: v for k, v in summary.items() if k != "assets"}), flush=True)


if __name__ == "__main__":
    main()
