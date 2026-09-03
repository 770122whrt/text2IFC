"""Run the deterministic Phase 10.3 five-Window proof for a case manifest."""

from __future__ import annotations

import argparse
import json
import runpy
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_text.splits import atomic_write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--case-manifest", type=Path, required=True)
    parser.add_argument(
        "--proof-export",
        type=Path,
        help=(
            "Copy the frozen successful inputs, ChangeSet, IFC output, and "
            "evaluation evidence before the benchmark process exits."
        ),
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        fixture_only = output / "fixture"
        if any(path != fixture_only for path in output.iterdir()):
            raise SystemExit(f"OUTPUT_ALREADY_EXISTS:{output}")
    else:
        output.mkdir(parents=True)

    case = json.loads(args.case_manifest.read_text(encoding="utf-8"))
    source = ROOT / case["source"]["local_path"]
    specification = runpy.run_path(
        str(ROOT / "tests" / "ifc_repair" / "test_phase10_3_vvo_batch_e2e.py")
    )
    test_case = specification[
        "test_vvo_one_text_one_changeset_repairs_five_windows_atomically"
    ]
    # ``runpy.run_path`` may return a mapping distinct from the globals mapping
    # retained by functions defined in the executed file. Bind the selected
    # benchmark case through the function's actual globals so a non-vvo
    # manifest cannot silently execute against the test module's vvo defaults.
    test_globals = test_case.__globals__
    test_globals["SOURCE"] = source
    test_globals["SOURCE_SHA256"] = case["source"]["sha256"]
    test_globals["CASE"] = case
    test_globals["CASE_ID"] = case["case_id"]
    test_globals["TARGETS"] = tuple(case["targets"])

    existing_fixture = output / "fixture"
    if existing_fixture.exists():
        import shutil

        shutil.rmtree(existing_fixture)
    test_case(output)

    state_paths = sorted((output / "runs" / "runs").glob("*/state.json"))
    if len(state_paths) != 1:
        raise SystemExit("OFFLINE_RUN_STATE_NOT_UNIQUE")
    state = json.loads(state_paths[0].read_text(encoding="utf-8"))
    summary = {
        "schema_version": "text2ifc/phase10.3-offline-benchmark-result/0.1",
        "case_id": case["case_id"],
        "status": state["stage"],
        "operation_count": len(case["targets"]),
        "source_ifc": case["source"]["local_path"],
        "source_sha256": case["source"]["sha256"],
        "damaged_ifc": "fixture/damaged.ifc",
        "request": "request.txt",
        "public_spec": "public-spec.json",
        "private_ground_truth_evaluation": (
            "private-ground-truth-evaluation.json"
        ),
        "pipeline_run": state_paths[0].parent.relative_to(output).as_posix(),
        "artifacts": state["result_artifacts"],
        "offline_deterministic_provider": True,
    }
    atomic_write_text(
        output / "benchmark-result.json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    if args.proof_export is not None:
        if state["stage"] != "succeeded":
            raise SystemExit("PROOF_EXPORT_REQUIRES_SUCCEEDED_RUN")
        _export_proof(
            destination=args.proof_export.resolve(),
            output=output,
            source=source,
            state_path=state_paths[0],
            state=state,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if state["stage"] == "succeeded" else 1


def _export_proof(
    *,
    destination: Path,
    output: Path,
    source: Path,
    state_path: Path,
    state: dict,
) -> None:
    if destination.exists():
        raise SystemExit(f"PROOF_EXPORT_ALREADY_EXISTS:{destination}")
    run_dir = state_path.parent
    successful_ifc = run_dir / state["result_artifacts"]["successful_ifc"]
    evaluation = run_dir / state["result_artifacts"]["evaluation"]
    copies = {
        "01-original.ifc": source,
        "02-damaged.ifc": output / "fixture" / "damaged.ifc",
        "03-repaired.ifc": successful_ifc,
        "input/request.txt": output / "request.txt",
        "agent/repair-intent.json": run_dir / "intent" / "repair-intent.json",
        "agent/provider-draft.json": (
            run_dir / "changeset" / "provider-draft.json"
        ),
        "changeset/bound-changeset.json": (
            run_dir / "changeset" / "bound-changeset.json"
        ),
        "changeset/semantic-manifests.json": (
            run_dir / "changeset" / "semantic-manifests.json"
        ),
        "validation/mutation-manifest.private.json": (
            output / "fixture" / "mutation_manifest.private.json"
        ),
        "validation/mutation-report.json": (
            output / "fixture" / "mutation_report.json"
        ),
        "validation/production-evaluation.json": evaluation,
        "validation/private-ground-truth-evaluation.json": (
            output / "private-ground-truth-evaluation.json"
        ),
        "validation/benchmark-result.json": output / "benchmark-result.json",
    }
    missing = [str(path) for path in copies.values() if not path.is_file()]
    if missing:
        raise SystemExit(f"PROOF_EXPORT_SOURCE_MISSING:{missing}")
    for relative, source_path in copies.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)


if __name__ == "__main__":
    raise SystemExit(main())
