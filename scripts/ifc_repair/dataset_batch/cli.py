"""Batch controller owns queues, waits, logs, admission and aggregate reports."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import platform
import sys
from pathlib import Path

import ifcopenshell

from .engine import write_json
from .reporting import summarize
from .sampling import sample_dataset
from .sources import discover_sources
from .validation import program_hash, sha256
from .workflow import prepare_source, process_source


def code_hash():
    return program_hash()


def build(args):
    root, repository = args.output.resolve(), args.repository_root.resolve()
    if not root.is_relative_to(repository) or root == repository or root.is_relative_to(repository / "dataset/processed/ifc-repair/repair-comparison/formal"):
        raise ValueError("OUTPUT_MUST_BE_A_NEW_BATCH_DIRECTORY_INSIDE_REPOSITORY")
    root.mkdir(parents=True, exist_ok=True)
    signature = {"cases_per_source": args.cases, "seed": args.seed, "additional_sources": args.additional_sources, "source_ids": args.source_ids, "code_sha256": code_hash(), "ifcopenshell_version": ifcopenshell.version}
    info_path = root / "build.json"
    if info_path.exists():
        previous = json.loads(info_path.read_text(encoding="utf-8"))
        if previous["configuration"] != signature:
            raise ValueError("EXISTING_BATCH_CONFIGURATION_CHANGED_USE_A_NEW_OUTPUT")
    else:
        write_json(info_path, {"schema_version": "text2ifc/ifc-repair-dataset-build/1.0", "configuration": signature, "python_version": platform.python_version(), "platform": platform.platform(), "provider_calls": 0, "system_pilot": "deferred_by_user"})
    selected_path = root / "sources.json"
    if selected_path.exists():
        discovery = json.loads(selected_path.read_text(encoding="utf-8"))
        specs = discovery["sources"]
    else:
        discovery = discover_sources(repository, additional_count=args.additional_sources)
        if args.source_ids:
            selected_ids = set(args.source_ids)
            discovery["sources"] = [spec for spec in discovery["sources"] if spec["source_id"] in selected_ids]
            if {spec["source_id"] for spec in discovery["sources"]} != selected_ids:
                raise ValueError("UNKNOWN_SOURCE_ID")
        required_sources = len(discovery["sources"])
        write_json(root / "private/discovery.json", discovery)
        pending_specs = list(discovery["sources"])
        reserves = iter(discovery["reserve_candidates"])
        specs, admissions, used = [], [], {spec["source_sha256"] for spec in pending_specs}
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(prepare_source, spec, str(repository), str(root / "private/admissions"), args.cases, args.seed): spec for spec in pending_specs}
            while futures:
                finished, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in finished:
                    spec = futures.pop(future)
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {"passed": False, "source_id": spec["source_id"], "reason": f"{type(exc).__name__}: {exc}"}
                    admissions.append({"source": spec, "result": result})
                    write_json(root / "private/admission-results.json", {"attempts": admissions})
                    if result["passed"]:
                        specs.append(spec)
                    elif spec["kind"] == "external":
                        replacement = next((item for item in reserves if item["source_sha256"] not in used), None)
                        if replacement:
                            replacement = {**replacement, "source_id": spec["source_id"]}
                            used.add(replacement["source_sha256"])
                            futures[pool.submit(prepare_source, replacement, str(repository), str(root / "private/admissions"), args.cases, args.seed)] = replacement
                    print(json.dumps({"stage": "source_admission", "accepted": len(specs), "required": required_sources, "attempts": len(admissions)}, ensure_ascii=False), flush=True)
        specs.sort(key=lambda spec: (spec["kind"] != "formal", spec["source_id"]))
        if len(specs) != required_sources:
            write_json(root / "summary.json", {"status": "blocked", "stage": "source_admission", "admitted_sources": len(specs), "required_sources": required_sources, "provider_calls": 0})
            return 2
        discovery = {**discovery, "sources": specs, "cases_per_source": args.cases, "seed": args.seed, "fresh_admission": "all selected sources passed schema+EXPRESS and candidate geometry/recipe capacity checks; this is not an independent all-product mesh certification"}
        write_json(selected_path, discovery)
    failures = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_source, spec, str(repository), str(root), args.cases, args.seed): spec for spec in specs}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            spec = futures[future]
            try:
                result = future.result()
                if result["status"] != "complete":
                    failures.append({"source_id": spec["source_id"], "reason": "case_shortfall"})
            except Exception as exc:
                failures.append({"source_id": spec["source_id"], "reason": f"{type(exc).__name__}: {exc}"})
            completed += 1
            write_json(root / "private/worker-failures.json", {"failures": failures})
            print(json.dumps({"stage": "damage_generation", "completed_models": completed, "total_models": len(specs), "failed_models": len(failures)}, ensure_ascii=False), flush=True)
    if not failures and args.samples:
        sample_dataset(root, count=args.samples, seed=args.seed)
    summary = summarize(root)
    print(json.dumps({key: summary[key] for key in ("status", "source_models", "machine_validated_cases", "target_cases", "failed_cases", "prompt_counts", "sampling", "provider_calls")}, ensure_ascii=False), flush=True)
    return 0 if summary["status"] == "complete" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build", help="discover/admit/copy/mutate/validate/sample/report; no model calls")
    create.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[3])
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--additional-sources", type=int, default=20)
    create.add_argument("--source-ids", nargs="+", help="bounded prototype subset of discovered source ids")
    create.add_argument("--cases", type=int, choices=range(1, 31), default=25)
    create.add_argument("--seed", type=int, default=42)
    create.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    create.add_argument("--samples", type=int, default=24)
    for name in ("report", "sample", "status"):
        command = sub.add_parser(name)
        command.add_argument("output", type=Path)
        if name == "sample":
            command.add_argument("--count", type=int, default=24)
            command.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.command == "build":
        return build(args)
    if args.command == "sample":
        result = sample_dataset(args.output, count=args.count, seed=args.seed)
        summarize(args.output)
        print(json.dumps({key: result[key] for key in ("passed", "checked_samples", "passed_samples", "checked_families")}, ensure_ascii=False))
        return 0 if result["passed"] else 2
    if args.command == "report":
        result = summarize(args.output)
    else:
        result = json.loads((args.output / "summary.json").read_text(encoding="utf-8"))
    print(json.dumps({key: result[key] for key in ("status", "source_models", "machine_validated_cases", "target_cases", "failed_cases", "prompt_counts", "sampling", "provider_calls")}, ensure_ascii=False))
    return 0
