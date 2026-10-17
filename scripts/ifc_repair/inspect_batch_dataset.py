"""Inspect final batch receipts and source hashes without loading any IFC model."""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(REPOSITORY / "src"))

from scripts.ifc_repair.dataset_batch.engine import verify_seal, write_json
from scripts.ifc_repair.dataset_batch.validation import program_hash, sha256


def inspect(root: Path) -> dict:
    root = root.resolve()
    plan = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    build = json.loads((root / "build.json").read_text(encoding="utf-8"))
    failures, accepted, checked, size_bytes = [], [], 0, 0
    for spec in plan["sources"]:
        source_root = root / "sources" / spec["source_id"]
        original = (REPOSITORY / spec["input_path"]).resolve()
        reference = source_root / "private/reference.ifc"
        if not original.is_relative_to(REPOSITORY) or sha256(original) != spec["source_sha256"] or sha256(reference) != spec["source_sha256"]:
            failures.append({"source_id": spec["source_id"], "reason": "mother_or_private_reference_changed"})
        result = json.loads((source_root / "result.json").read_text(encoding="utf-8"))
        source_accepted, source_hashes = 0, set()
        for case in result["cases"]:
            checked += 1
            folder = (root / case["path"]).resolve()
            if not folder.is_relative_to(source_root) or not verify_seal(folder):
                failures.append({"case_id": case["case_id"], "reason": "receipt_binding_failed"})
                continue
            actual = json.loads((folder / "case.json").read_text(encoding="utf-8"))
            if any(case[key] != actual[key] for key in actual):
                failures.append({"case_id": case["case_id"], "reason": "source_index_disagrees_with_case"})
            if case["status"] != "passed":
                continue
            native = json.loads((folder / "private/validation.json").read_text(encoding="utf-8"))
            preservation = json.loads((folder / "private/preservation.json").read_text(encoding="utf-8"))
            manifest = json.loads((folder / "private/mutation.json").read_text(encoding="utf-8"))
            for relative, expected_hash in manifest.get("normalization", {}).get("previous_artifact_hashes", {}).items():
                historical = (folder / relative).resolve()
                if not historical.is_relative_to(folder) or sha256(historical) != expected_hash:
                    failures.append({"case_id": case["case_id"], "reason": "preserved_failure_history_binding_failed"})
            valid = (native["passed"] and native["schema"] == "IFC2X3" and native["express_rules"] and native["finding_count"] == 0 and native["ifcopenshell_version"] == build["configuration"]["ifcopenshell_version"] and preservation["passed"] and case["machine_validated"] and not case["human_reviewed"] and case["source_unchanged"] and not case["private_identity_leakage"] and case["source_sha256"] == spec["source_sha256"] and manifest["source_sha256"] == spec["source_sha256"] and manifest["damaged_sha256"] == case["damaged_sha256"])
            if not valid or case["damaged_sha256"] in source_hashes:
                failures.append({"case_id": case["case_id"], "reason": "accepted_case_gate_or_uniqueness_failed"})
            source_hashes.add(case["damaged_sha256"])
            source_accepted += 1
            accepted.append(case)
            size_bytes += (folder / "public/model.ifc").stat().st_size
        if source_accepted != plan["cases_per_source"] or result["passed_cases"] != source_accepted or result["provider_calls"] != 0:
            failures.append({"source_id": spec["source_id"], "reason": "source_case_count_or_no_provider_gate_failed"})
    if build["configuration"]["code_sha256"] != program_hash():
        failures.append({"reason": "generator_code_changed_since_build"})
    report = {"schema_version": "text2ifc/ifc-repair-dataset-final-integrity/1.0", "passed": not failures, "mother_models_checked": len(plan["sources"]), "case_receipts_checked": checked, "accepted_case_receipts_checked": len(accepted), "unique_accepted_ifc_bytes": len({case["damaged_sha256"] for case in accepted}), "accepted_ifc_bytes": size_bytes, "external_upstream_sources": len({spec["upstream_source_id"] for spec in plan["sources"] if spec["kind"] == "external"}), "external_scene_families": len({spec["scene_family"] for spec in plan["sources"] if spec["kind"] == "external"}), "all_upstream_sources": len({spec["upstream_source_id"] for spec in plan["sources"]}), "family_counts": dict(collections.Counter(case["family"] for case in accepted)), "provider_calls": 0, "scope": "all source/reference SHA bindings, complete sealed case artifacts, persisted zero-finding native+EXPRESS and preservation receipts, per-mother case counts/uniqueness and generator fingerprint; no repeated model/mesh validation", "inspection_code_sha256": sha256(Path(__file__)), "failures": failures}
    write_json(root / "integrity.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inspect(args.output)
    print(json.dumps({key: result[key] for key in ("passed", "mother_models_checked", "case_receipts_checked", "accepted_case_receipts_checked", "unique_accepted_ifc_bytes", "failures")}, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 2)
