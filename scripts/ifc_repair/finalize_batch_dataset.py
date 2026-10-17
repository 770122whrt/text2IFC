"""Close draft batches by normalizing recorded empty associations, preserving failures."""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(REPOSITORY / "src"))

import ifcopenshell

from scripts.ifc_repair.dataset_batch.engine import seal_case, verify_seal, write_json
from scripts.ifc_repair.dataset_batch.reporting import summarize
from scripts.ifc_repair.dataset_batch.sampling import inspect_case, sample_dataset
from scripts.ifc_repair.dataset_batch.validation import native_validate, sha256, verify_case


def normalize_case(reference: Path, folder: Path) -> dict:
    """Only touch failed draft cases; only remove emptied, recorded associations."""
    case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
    if case["status"] == "passed":
        return case
    if not verify_seal(folder):
        raise ValueError("FAILED_CASE_RECEIPT_BINDING_FAILED")
    manifest = json.loads((folder / "private/mutation.json").read_text(encoding="utf-8"))
    preservation = json.loads((folder / "private/preservation.json").read_text(encoding="utf-8"))
    if not preservation["passed"] or not case["source_unchanged"] or case["private_identity_leakage"] or not all(case["prompt_templates"][name]["applicable"] for name in ("world", "storey_local")) or sha256(reference) != manifest["source_sha256"]:
        return case
    started = time.monotonic()
    model = ifcopenshell.open(str(folder / "public/model.ifc"))
    touched = {row["guid"] for row in manifest["affected_relationships"]}
    emptied = [rel for rel in model.by_type("IfcRelAssociates") if rel.GlobalId in touched and not rel.RelatedObjects]
    if not emptied:
        return case
    removed = sorted(rel.GlobalId for rel in emptied)
    for rel in emptied:
        model.remove(rel)
    descriptor, name = tempfile.mkstemp(prefix="normalization-", suffix=".ifc", dir=folder / "private")
    os.close(descriptor)
    candidate = Path(name)
    model.write(str(candidate))
    reopened = ifcopenshell.open(str(candidate))
    native = native_validate(reopened)
    preserved = verify_case(reference, reopened, manifest)
    if not native["passed"] or not preserved["passed"]:
        write_json(candidate.with_suffix(".json"), {"native": native, "preservation": preserved, "removed_empty_relationships": removed})
        return case
    history_root = folder / "private/normalization"
    next_index = 1 + len(list(history_root.glob("[0-9][0-9][0-9]")))
    history = history_root / f"{next_index:03d}"
    history.mkdir(parents=True)
    raw = {"public/model.ifc": "model.ifc", "case.json": "case.json", "private/mutation.json": "mutation.json", "private/recipe.json": "recipe.json", "private/validation.json": "validation.json", "private/preservation.json": "preservation.json", "private/seal.json": "seal.json"}
    raw.update({f"public/request-{frame}.txt": f"request-{frame}.txt" for frame, meta in case["prompt_templates"].items() if meta["applicable"]})
    hashes = {}
    for relative, basename in raw.items():
        target = history / basename
        shutil.copyfile(folder / relative, target)
        hashes[target.relative_to(folder).as_posix()] = sha256(target)
    manifest["normalization"] = {"procedure": "remove only empty IfcRelAssociates whose identities were recorded as touched by the specified deletions", "removed_empty_relationships": removed, "previous_artifact_hashes": hashes, "normalizer_code_sha256": sha256(Path(__file__)), "source_unchanged": sha256(reference) == manifest["source_sha256"]}
    manifest["damaged_sha256"] = sha256(candidate)
    os.replace(candidate, folder / "public/model.ifc")
    case = {**case, "status": "passed", "machine_validated": True, "damaged_sha256": manifest["damaged_sha256"], "normalization_performed": True, "normalizer_code_sha256": manifest["normalization"]["normalizer_code_sha256"], "normalization_seconds": round(time.monotonic() - started, 3)}
    write_json(folder / "private/mutation.json", manifest)
    write_json(folder / "private/validation.json", native)
    write_json(folder / "private/preservation.json", preserved)
    write_json(folder / "case.json", case)
    seal_case(folder)
    return case


def complete_sampling(root: Path, count: int, seed: int):
    sampling = root / "sampling.json"
    if not sampling.exists():
        return sample_dataset(root, count=count, seed=seed)
    previous = json.loads(sampling.read_text(encoding="utf-8"))
    candidates = []
    for path in sorted((root / "sources").glob("*/result.json")):
        candidates.extend(c for c in json.loads(path.read_text(encoding="utf-8"))["cases"] if c["status"] == "passed")
    random.Random(seed).shuffle(candidates)
    covered = {row["family"] for row in previous["results"]}
    remaining = sorted({c["family"] for c in candidates} - covered)
    additions = []
    for family in remaining:
        for prefix in ("formal-", "external-"):
            case = next((c for c in candidates if c["family"] == family and c["case_id"].startswith(prefix)), None)
            if case:
                additions.append(inspect_case(root, case))
    results = previous["results"] + additions
    report = {**previous, "requested_samples": max(count, len(results)), "checked_samples": len(results), "passed_samples": sum(row["passed"] for row in results), "passed": bool(results) and all(row["passed"] for row in results), "checked_families": sorted({row["family"] for row in results}), "results": results, "existing_passed_checks_reused": len(previous["results"]), "additional_family_checks": len(additions)}
    write_json(sampling, report)
    return report


def finalize(root: Path, count: int, seed: int) -> dict:
    root = root.resolve()
    plan = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    previous_record = json.loads((root / "finalization.json").read_text(encoding="utf-8")) if (root / "finalization.json").exists() else {}
    previous_sources = {row["source_id"]: row for row in previous_record.get("sources", [])}
    resolutions, failures = [], []
    for spec in plan["sources"]:
        source_root = root / "sources" / spec["source_id"]
        path = source_root / "result.json"
        if not path.exists():
            failures.append({"source_id": spec["source_id"], "reason": "source_generation_did_not_finish"})
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        needed = plan["cases_per_source"] - result["passed_cases"]
        if needed <= 0:
            if spec["source_id"] in previous_sources:
                resolutions.append(previous_sources[spec["source_id"]])
            continue
        previous = source_root / "private/result-before-normalization.json"
        if not previous.exists():
            shutil.copyfile(path, previous)
        changed = []
        for index, old in enumerate(result["cases"]):
            if needed <= 0:
                break
            if old["status"] == "passed":
                continue
            folder = root / old["path"]
            new = normalize_case(source_root / "private/reference.ifc", folder)
            if new["status"] == "passed":
                result["cases"][index] = {**new, "case_id": old["case_id"], "path": old["path"]}
                changed.append(old["case_id"])
                needed -= 1
        result["passed_cases"] = sum(case["status"] == "passed" for case in result["cases"])
        result["status"] = "complete" if needed == 0 and result["source_unchanged"] else "incomplete"
        result["normalization_cases"] = changed
        write_json(path, result)
        write_json(source_root / "private/progress.json", {"completed_cases": result["attempted_cases"], "passed_cases": result["passed_cases"], "target_cases": result["target_cases"], "normalization_cases": changed})
        resolutions.append({"source_id": spec["source_id"], "normalized_cases": changed, "passed_cases": result["passed_cases"], "target_cases": result["target_cases"]})
        if needed:
            failures.append({"source_id": spec["source_id"], "reason": "unresolved_shortfall", "missing_cases": needed})
    record = {"schema_version": "text2ifc/ifc-repair-dataset-finalization/1.0", "passed": not failures, "procedure_code_sha256": sha256(Path(__file__)), "normalized_cases": sum(len(row["normalized_cases"]) for row in resolutions), "sources": resolutions, "failures": failures, "provider_calls": 0, "preserved_prior_failures": "private/normalization histories and private/result-before-normalization.json; original generation failure ledger retained"}
    write_json(root / "finalization.json", record)
    if not failures:
        complete_sampling(root, count, seed)
    summary = summarize(root)
    report = root / "REPORT.md"
    with report.open("a", encoding="utf-8") as stream:
        stream.write(f"\n## 删除关系收尾\n\n{record['normalized_cases']}份原先因删空关联而被原生校验拦截的副本，经过有界关系清理后重新校验。只清理损伤记录已列出的空关联；通过副本没有改写，母本没有改写。修正前的IFC及失败记录保存在各例private/normalization中。详见[收尾记录](finalization.json)。\n")
    return {"status": summary["status"], "normalized_cases": record["normalized_cases"], "machine_validated_cases": summary["machine_validated_cases"], "target_cases": summary["target_cases"], "sampling": summary["sampling"], "failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = finalize(args.output, args.samples, args.seed)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    raise SystemExit(0 if result["status"] == "complete" else 2)
