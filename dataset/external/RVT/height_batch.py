"""Apply the evidence-only railing policy to completed, isolated failed attempts."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil

from batch import candidate_status, step
from pipeline import BASE, conversion_blocker, safe_target, sha256, write_new_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--asset-index", type=Path, default=BASE / "asset-index.json")
    parser.add_argument("--source-name", default="ResBIM")
    args = parser.parse_args()
    root = safe_target(BASE / "runs", args.run_name)
    collection = safe_target(BASE / "IFC", args.run_name)
    if root.exists() or collection.exists():
        raise ValueError("RUN_ALREADY_EXISTS")
    assets = {r["inventory_id"]: r for r in json.loads(args.asset_index.read_text(encoding="utf-8"))["assets"]}
    policies = {r["source_name"]: r for r in json.loads((BASE / "review-20260913/source-review.json").read_text(encoding="utf-8"))["sources"]}
    selected = {}
    for run in args.runs:
        for path in sorted(safe_target(BASE / "runs", run).glob("INV-*/outcome.json")):
            outcome = json.loads(path.read_text(encoding="utf-8"))
            aid = outcome["inventory_id"]
            if args.ids and aid not in args.ids:
                continue
            if (outcome["source_name"] == args.source_name and outcome["status"] == "validation_failed" and
                    not outcome.get("pending") and outcome.get("native_error_count") and outcome.get("geometry_failed") == 0):
                if aid in selected:
                    raise ValueError("MULTIPLE_PARENT_ATTEMPTS_REQUIRE_SELECTION")
                selected[aid] = path.parent
    results = []
    for aid, parent in sorted(selected.items()):
        row = assets[aid]
        if conversion_blocker(row, policies) or sha256(BASE / row["local_path"]) != row["sha256"]:
            raise ValueError("SOURCE_GATE_FAILED")
        folder = root / aid
        folder.mkdir(parents=True)
        source = parent / "normalized.ifc"
        target = folder / "height-corrected.ifc"
        report = folder / "height-correction.json"
        outcome = {"inventory_id": aid, "source_name": row["source_name"], "filename": row["filename"],
                   "rvt_sha256": row["sha256"], "parent_attempt": parent.relative_to(BASE).as_posix(),
                   "rvt_fidelity": "not_verified", "independent_building": "not_established", "canonical_manifest_admitted": False}
        code = step("height_normalize.py", [str(source), str(target), "--geometry-report", str(parent / "normalized-validation.json"),
                    "--report", str(report)], folder, "height-correction", args.timeout)
        if code != 0 or not report.is_file():
            outcome.update(status="height_evidence_insufficient", correction_returncode=code)
        else:
            norm = json.loads(report.read_text(encoding="utf-8"))
            vreport = folder / "validation.json"
            vcode = step("pipeline.py", ["validate", str(target), "--report", str(vreport)], folder, "validation", args.timeout)
            validation = json.loads(vreport.read_text(encoding="utf-8")) if vreport.is_file() else {}
            if vcode != 0:
                validation["technical_candidate"] = False
            original_attempt = json.loads((parent / "attempt.json").read_text(encoding="utf-8"))
            outcome.update(status=candidate_status(original_attempt, norm, validation), native_error_count=validation.get("native_error_count"),
                           geometry_failed=validation.get("geometry", {}).get("failed"), counts=validation.get("counts"),
                           validation_blockers=validation.get("blockers"), training_use_supported_by_source_evidence=policies[row["source_name"]]["training_use_supported_by_source_evidence"])
            if outcome["status"] == "technical_candidate":
                dest = collection / row["source_name"] / f"{aid}.ifc"
                dest.parent.mkdir(parents=True, exist_ok=True)
                with target.open("rb") as src, dest.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
                if sha256(dest) != validation["sha256"]:
                    raise ValueError("COPY_HASH_MISMATCH")
                outcome.update(ifc_path=dest.relative_to(BASE).as_posix(), ifc_sha256=sha256(dest), ifc_bytes=dest.stat().st_size)
        write_new_json(folder / "outcome.json", outcome)
        results.append(outcome)
        print(json.dumps({k: outcome.get(k) for k in ("inventory_id", "status", "native_error_count")}), flush=True)
    summary = {"schema": "rvt-conversion-collection/1.0", "parent_runs": args.runs,
               "status_counts": dict(Counter(r["status"] for r in results)), "outcomes": results, "canonical_manifest_changed": False}
    write_new_json(root / "summary.json", summary)
    write_new_json(collection / "manifest.json", summary)
    print(json.dumps(summary["status_counts"]))
    return 0 if all(r["status"] == "technical_candidate" for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
