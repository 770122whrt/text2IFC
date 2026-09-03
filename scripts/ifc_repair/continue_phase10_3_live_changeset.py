"""Apply and evaluate a saved live batch ChangeSet without calling Provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.benchmark_evaluation import (
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    evaluate_benchmark,
    evaluate_production,
)
from text2ifc_ifc_repair.evaluation import evaluation_to_dict
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.semantic_authoring import (
    parse_semantic_manifest,
    semantic_manifest_expected_facts,
)
from text2ifc_text.splits import atomic_write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--case-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--production-only", action="store_true")
    args = parser.parse_args()

    live = args.live_root.resolve()
    run = live / "runs" / args.run_id
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    damaged = live / "fixture" / "damaged.ifc"
    repaired = output / "repaired.ifc"
    request = (live / "request.txt").read_text(encoding="utf-8")
    changeset = json.loads((run / "changeset.json").read_text(encoding="utf-8"))
    registry = create_default_registry()
    application = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=repaired,
        registry=registry,
    )
    atomic_write_text(
        output / "application.json",
        json.dumps(application, ensure_ascii=False, indent=2) + "\n",
    )
    expected_facts = {}
    for operation in changeset["operations"]:
        operation_id = operation["operation_id"]
        manifest = json.loads(
            (
                run
                / "changeset"
                / f"semantic-manifest-{operation_id}.json"
            ).read_text(encoding="utf-8")
        )
        expected_facts[operation_id] = semantic_manifest_expected_facts(
            parse_semantic_manifest(manifest)
        )
    case = json.loads(args.case_manifest.read_text(encoding="utf-8"))
    mapping = {
        operation["operation_id"]: {
            "wall": target["wall_global_id"],
            "opening": target["opening_global_id"],
            "window": target["window_global_id"],
        }
        for operation, target in zip(changeset["operations"], case["targets"])
    }
    production_inputs = ProductionEvaluationInputs(
        damaged_ifc_path=damaged,
        repaired_ifc_path=repaired,
        changeset=changeset,
        application_result=application,
        registry=registry,
        expected_facts_by_operation=expected_facts,
    )
    if args.production_only:
        production = evaluation_to_dict(evaluate_production(production_inputs))
        atomic_write_text(
            output / "production-evaluation.json",
            json.dumps(production, ensure_ascii=False, indent=2) + "\n",
        )
        print(json.dumps({"production_status": production["status"]}, indent=2))
        return 0 if production["status"] == "passed" else 1
    result = evaluate_benchmark(
        BenchmarkEvaluationInputs(
            production=production_inputs,
            private_original_ifc_path=ROOT / case["source"]["local_path"],
            private_mutation_mapping=mapping,
        )
    )
    production = dict(result.production_report)
    private = dict(result.private_report)
    atomic_write_text(
        output / "production-evaluation.json",
        json.dumps(production, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_text(
        output / "private-ground-truth-evaluation.json",
        json.dumps(private, ensure_ascii=False, indent=2) + "\n",
    )
    summary = {
        "schema_version": "text2ifc/live-deterministic-continuation/0.1",
        "case_id": case["case_id"],
        "live_run_id": args.run_id,
        "provider_stages_completed": 2,
        "operation_count": len(changeset["operations"]),
        "application_valid": application["valid"],
        "application_published": application["published"],
        "production_status": production["status"],
        "private_status": private["status"],
        "repaired_ifc": "repaired.ifc",
    }
    atomic_write_text(
        output / "result.json",
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (
        application["valid"]
        and application["published"]
        and production["status"] == "passed"
        and private["status"] == "passed"
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
