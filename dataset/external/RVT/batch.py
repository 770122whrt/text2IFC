"""Serial, isolated DDC attempts and fixed-policy normalization; no source overwrite.

Failed files remain in runs. Only individually passing outputs are copied into
IFC/<run-name>; that collection is a technical dataset, not a fidelity guarantee.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys

from pipeline import BASE, conversion_blocker, ddc_command, run_attempt, safe_target, sha256, write_new_json


def candidate_status(attempt: dict, normalization: dict, validation: dict) -> str:
    if attempt.get("status") == "source_mutation_detected":
        return "source_mutation_detected"
    if not attempt.get("conversion_completed"):
        return attempt.get("status", "conversion_failed")
    if normalization.get("pending"):
        return "manual_review_required"
    preservation = normalization.get("preservation", {})
    if not all(preservation.get(k) is True for k in ("source_unchanged", "product_guids_unchanged", "unchanged_entities_equal")):
        return "preservation_failed"
    return "technical_candidate" if validation.get("technical_candidate") else "validation_failed"


def step(script: str, args: list[str], folder: Path, name: str, timeout: int) -> int | None:
    with (folder / f"{name}.stdout.log").open("xb") as stdout, (folder / f"{name}.stderr.log").open("xb") as stderr:
        try:
            return subprocess.run([sys.executable, "-B", str(BASE / script), *args],
                                  stdout=stdout, stderr=stderr, timeout=timeout,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).returncode
        except subprocess.TimeoutExpired:
            return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="+", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--converter", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--asset-index", type=Path, default=BASE / "asset-index.json")
    args = parser.parse_args()
    assets = {r["inventory_id"]: r for r in json.loads(args.asset_index.read_text(encoding="utf-8"))["assets"]}
    policies = {r["source_name"]: r for r in json.loads((BASE / "review-20260913/source-review.json").read_text(encoding="utf-8"))["sources"]}
    if len(args.ids) != len(set(args.ids)) or any(i not in assets for i in args.ids):
        raise ValueError("UNKNOWN_OR_DUPLICATE_ID")
    run_root = safe_target(BASE / "runs", args.run_name)
    collection = safe_target(BASE / "IFC", args.run_name)
    if run_root.exists() or collection.exists():
        raise ValueError("RUN_OR_COLLECTION_ALREADY_EXISTS")
    executable = args.converter.resolve(strict=True)
    run_root.mkdir(parents=True)
    outcomes = []
    for aid in args.ids:
        row = assets[aid]
        folder = run_root / aid
        outcome = {"inventory_id": aid, "source_name": row["source_name"], "filename": row["filename"],
                   "rvt_sha256": row["sha256"], "independent_building": "not_established",
                   "rvt_fidelity": "not_verified", "canonical_manifest_admitted": False}
        blocker = conversion_blocker(row, policies)
        if blocker:
            outcome.update(status=blocker, dependencies=row.get("dependencies", []))
        else:
            attempt = run_attempt(ddc_command(executable, Path("{input}"), Path("{output}")),
                                  BASE / row["local_path"], folder, expected_sha256=row["sha256"],
                                  timeout=args.timeout, validation_timeout=args.timeout, cwd=executable.parent)
            outcome["raw_status"] = attempt["status"]
            if not attempt["conversion_completed"] or attempt["status"] == "source_mutation_detected":
                outcome["status"] = attempt["status"]
            else:
                report = folder / "normalization.json"
                normalized = folder / "normalized.ifc"
                code = step("normalize.py", [str(folder / "converted.ifc"), str(normalized),
                            "--converter-label", "DDC RVT2IFC Community 18.4.1", "--report", str(report)], folder, "normalization", args.timeout)
                if code not in (0, 2) or not report.is_file() or not normalized.is_file():
                    outcome.update(status="normalization_process_failed", normalization_returncode=code)
                else:
                    norm = json.loads(report.read_text(encoding="utf-8"))
                    vreport = folder / "normalized-validation.json"
                    vcode = step("pipeline.py", ["validate", str(normalized), "--report", str(vreport)], folder, "normalized-validation", args.timeout)
                    validation = json.loads(vreport.read_text(encoding="utf-8")) if vreport.is_file() else {}
                    if vcode != 0:
                        validation["technical_candidate"] = False
                    outcome.update(status=candidate_status(attempt, norm, validation), pending=norm["pending"],
                                   native_error_count=validation.get("native_error_count"),
                                   geometry_failed=validation.get("geometry", {}).get("failed"),
                                   counts=validation.get("counts"), validation_blockers=validation.get("blockers"),
                                   training_use_supported_by_source_evidence=policies[row["source_name"]].get("training_use_supported_by_source_evidence", False))
                    if outcome["status"] == "technical_candidate":
                        dest = safe_target(collection, f"{row['source_name']}/{aid}.ifc")
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with normalized.open("rb") as src, dest.open("xb") as dst:
                            shutil.copyfileobj(src, dst)
                        if sha256(dest) != validation["sha256"]:
                            raise ValueError("COLLECTION_COPY_HASH_MISMATCH")
                        outcome.update(ifc_path=dest.relative_to(BASE).as_posix(), ifc_sha256=sha256(dest), ifc_bytes=dest.stat().st_size)
        write_new_json(folder / "outcome.json", outcome)
        outcomes.append(outcome)
        print(json.dumps({k: outcome.get(k) for k in ("inventory_id", "status", "native_error_count", "geometry_failed")}), flush=True)
        if outcome["status"] == "source_mutation_detected":
            break
    summary = {"schema": "rvt-conversion-collection/1.0", "requested_ids": args.ids,
               "status_counts": dict(Counter(r["status"] for r in outcomes)), "outcomes": outcomes,
               "unattempted_ids": args.ids[len(outcomes):], "canonical_manifest_changed": False}
    write_new_json(run_root / "summary.json", summary)
    write_new_json(collection / "manifest.json", summary)
    print(json.dumps(summary["status_counts"]), flush=True)
    return 0 if all(r["status"] == "technical_candidate" for r in outcomes) else 2


if __name__ == "__main__":
    raise SystemExit(main())
