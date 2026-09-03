"""Real DeepSeek UAT for text-authorized effective Window property replication."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
from typing import Any

import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = str(ROOT / "src")
sys.path[:] = [
    item
    for item in sys.path
    if str(Path(item).resolve()) != str(Path(SOURCE_ROOT).resolve())
]
sys.path.insert(0, SOURCE_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ifc_repair.run_phase10_1_live_uat import (  # noqa: E402
    GEOMETRY,
    OPENING_ID,
    SOURCE,
    SOURCE_SHA256,
    TYPE_NAME,
    WALL_ID,
    WINDOW_ID,
    _config_result,
    _environment,
    _levels,
    _provider_attempts,
    _provider_metadata,
    _read_json,
    _sha256,
    _write,
)
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
import text2ifc_ifc_repair.occurrence_fidelity as occurrence_fidelity_module  # noqa: E402
from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    evaluate_benchmark,
    evaluate_production,
)
from text2ifc_ifc_repair.evaluation import EvaluationExecutionPolicy  # noqa: E402
from text2ifc_ifc_repair.compare import (  # noqa: E402
    compare_ifc_with_ifcdiff,
    compare_mapped_elements,
)
from text2ifc_ifc_repair.mutation import remove_window_and_opening  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT / "dataset/processed/ifc-repair/phase10.1-full-property-replication"
)
PROPERTY_FACTS = (
    ("Constraints", "Level", "Level: Level 1", "IfcLabel", None),
    ("Constraints", "Sill Height", 305.000000000004, "IfcLengthMeasure", "mm"),
    ("Custom_Pset", "NetArea", 3.17875400000013, "IfcAreaMeasure", "mm2"),
    ("Custom_Pset", "SillHeight", 305.000000000004, "IfcLengthMeasure", "mm"),
    ("Custom_Pset", "StatusConstruction", "New Construction", "IfcLabel", None),
    ("Custom_Pset", "StoreyName", "Level: Level 1", "IfcText", None),
    ("Dimensions", "Area", 3.17875400000013, "IfcAreaMeasure", "mm2"),
    ("Dimensions", "Volume", 0.0561146700000025, "IfcVolumeMeasure", "mm3"),
    ("Identity Data", "Mark", "7", "IfcText", None),
    ("Other", "Family", "M_Fixed: 0915 x 1830mm", "IfcLabel", None),
    ("Other", "Family and Type", "M_Fixed: 0915 x 1830mm", "IfcLabel", None),
    ("Other", "Head Height", 2135.0, "IfcLengthMeasure", "mm"),
    ("Other", "Host Id", "Basic Wall: Outside wall", "IfcLabel", None),
    ("Other", "Type", "M_Fixed: 0915 x 1830mm", "IfcLabel", None),
    ("Other", "Type Id", "M_Fixed: 0915 x 1830mm", "IfcLabel", None),
    ("Phasing", "Phase Created", "New Construction", "IfcLabel", None),
)
OPENING_QUANTITY_FACTS = (
    ("Depth", 200.0, "IfcQuantityLength", "mm"),
    ("Height", 915.0, "IfcQuantityLength", "mm"),
    ("Width", 1830.0, "IfcQuantityLength", "mm"),
)


def _request() -> str:
    lines = [
        f"On IfcWall GlobalId {WALL_ID}, restore the missing window.",
        GEOMETRY,
        f"Reuse the existing Window Type named '{TYPE_NAME}'.",
        (
            "The following occurrence-direct IfcPropertySingleValue facts are "
            "explicitly authorized. Preserve set/property spelling exactly:"
        ),
    ]
    for set_name, property_name, value, value_type, unit in PROPERTY_FACTS:
        lines.append(
            "- "
            + json.dumps(
                {
                    "set_name": set_name,
                    "property_name": property_name,
                    "value": value,
                    "requested_value_type": value_type,
                    "requested_unit": unit,
                    "scope": "occurrence_direct",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    lines.append(
        "Also author these exact BaseQuantities on the new "
        "IfcOpeningElement occurrence:"
    )
    for quantity_name, value, value_type, unit in OPENING_QUANTITY_FACTS:
        lines.append(
            "- "
            + json.dumps(
                {
                    "scope": "opening_occurrence",
                    "set_name": "BaseQuantities",
                    "quantity_name": quantity_name,
                    "value": value,
                    "value_type": value_type,
                    "unit": unit,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--intent-schema-version",
        choices=(
            "text2ifc/ifc-repair-intent/0.2",
            "text2ifc/ifc-repair-intent/0.4",
        ),
        default="text2ifc/ifc-repair-intent/0.2",
        help=(
            "Keep 0.2 as the Phase 10.1 compatibility default; Phase 10.5 "
            "must explicitly request 0.4."
        ),
    )
    args = parser.parse_args(argv)
    if args.check_config == args.live:
        parser.error("choose exactly one of --check-config or --live")
    environment = _environment(args.env_file)
    config = _config_result(environment)
    if args.check_config:
        print(json.dumps(config, ensure_ascii=False))
        return 0 if config["status"] == "ready" else 2
    if config["status"] != "ready":
        print(json.dumps(config, ensure_ascii=False))
        return 2

    output = args.output_root / datetime.now(timezone.utc).strftime(
        "uat-%Y%m%dT%H%M%S%fZ"
    )
    output.mkdir(parents=True, exist_ok=False)
    result = _run(
        output,
        environment,
        intent_schema_version=args.intent_schema_version,
    )
    _write(output / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["contract_pass"] else 2


def _runtime_source_evidence() -> dict[str, Any]:
    source = Path(occurrence_fidelity_module.__file__).resolve()
    return {
        "occurrence_fidelity_path": source.as_posix(),
        "occurrence_fidelity_sha256": f"sha256:{_sha256(source)}",
        "production_evaluation_mode": "sequential",
    }


def _evaluate_live_production(inputs: ProductionEvaluationInputs):
    """Run the small live UAT with full checks but deterministic scheduling."""

    return evaluate_production(
        replace(
            inputs,
            execution_policy=EvaluationExecutionPolicy(mode="sequential"),
        )
    )


def _run(
    output: Path,
    environment: dict[str, str],
    *,
    intent_schema_version: str = "text2ifc/ifc-repair-intent/0.2",
) -> dict[str, Any]:
    fixture = output / "fixture"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=fixture,
        wall_global_id=WALL_ID,
        opening_global_id=OPENING_ID,
        window_global_id=WINDOW_ID,
        expected_source_sha256=SOURCE_SHA256,
    )
    runtime = output / "runtime"
    captured: dict[str, Any] = {}

    def capture_application(**kwargs):
        captured["application"] = apply_changeset(**kwargs)
        return captured["application"]

    def capture_evaluation(inputs: ProductionEvaluationInputs):
        captured["expected_facts_by_operation"] = (
            inputs.expected_facts_by_operation
        )
        return _evaluate_live_production(inputs)

    request = _request()
    _write(output / "user-request.json", {"text": request})
    try:
        api = RepairAPI(
            runtime,
            provider=OpenAICompatibleLiveProvider(
                config=load_openai_compatible_runtime_config(environment)
            ),
            intent_schema_version=intent_schema_version,
            orchestrator_options={
                "apply_stage": capture_application,
                "evaluation_stage": capture_evaluation,
            },
        )
        initial = api.start(fixture / "damaged.ifc", request)
        final = initial
        confirmation = None
        if (
            initial.clarification is not None
            and initial.clarification.reason_code == "property_confirmation"
        ):
            preview = initial.clarification.property_preview
            confirmation = {
                "preview_kind": preview.get("preview_kind", "property_single"),
                "item_count": len(preview.get("items", [preview])),
                "preview_hash": preview["preview_hash"],
            }
            final = api.continue_with_answer(
                initial.run_id,
                {
                    "kind": "confirm_property",
                    "preview_hash": preview["preview_hash"],
                },
                clarification_id=initial.clarification.clarification_id,
                expected_state_version=initial.state_version,
            )
        run_dir = runtime / final.run_directory
        attempts = _provider_attempts(run_dir)
        if not (
            final.successful_artifact_publishable
            and "successful_ifc" in final.artifacts
            and "application" in captured
        ):
            return {
                "schema_version": "text2ifc/phase10.1-full-replication/0.1",
                "status": final.status,
                "reason_code": final.reason_code,
                "provider_attempts": attempts,
                "provider": _provider_metadata(run_dir),
                "contract_versions": {
                    "requested_repair_intent": intent_schema_version,
                    "expected_bound_changeset": (
                        "text2ifc/ifc-repair-changeset/0.3"
                        if intent_schema_version
                        == "text2ifc/ifc-repair-intent/0.4"
                        else "text2ifc/ifc-repair-changeset/0.2"
                    ),
                },
                "confirmation": confirmation,
                "artifacts": dict(final.artifacts),
                "contract_pass": False,
                "synthetic_fallback": False,
                "runtime_source": _runtime_source_evidence(),
            }

        repaired_path = run_dir / final.artifacts["successful_ifc"]
        application = captured["application"]
        new_window_id = next(
            item["global_id"]
            for item in application["operations"][0]["changes"]["created"]
            if item["role"] == "window"
        )
        changeset = _read_json(run_dir / "changeset.json")
        intent_document = _read_json(run_dir / "intent" / "repair-intent.json")
        benchmark_expected_facts = captured[
            "expected_facts_by_operation"
        ]
        expected_changeset_version = (
            "text2ifc/ifc-repair-changeset/0.3"
            if intent_schema_version == "text2ifc/ifc-repair-intent/0.4"
            else "text2ifc/ifc-repair-changeset/0.2"
        )
        production = _read_json(run_dir / final.artifacts["evaluation"])
        benchmark = evaluate_benchmark(
            BenchmarkEvaluationInputs(
                production=ProductionEvaluationInputs(
                    damaged_ifc_path=fixture / "damaged.ifc",
                    repaired_ifc_path=repaired_path,
                    changeset=changeset,
                    application_result=application,
                    registry=api.registry,
                    expected_facts_by_operation=benchmark_expected_facts,
                ),
                private_original_ifc_path=SOURCE,
                private_mutation_mapping={
                    changeset["operations"][0]["operation_id"]: {
                        "wall": WALL_ID,
                        "opening": OPENING_ID,
                        "window": WINDOW_ID,
                    }
                },
            )
        )
        mapped = compare_mapped_elements(
            SOURCE,
            repaired_path,
            mappings=(
                {
                    "role": "window",
                    "before_global_id": WINDOW_ID,
                    "after_global_id": new_window_id,
                },
            ),
        )
        official = compare_ifc_with_ifcdiff(SOURCE, repaired_path)
        _write(output / "mapped-window-comparison.json", mapped)
        _write(output / "official-ifcdiff.json", official)
        _write(output / "private-benchmark-evaluation.json", benchmark.private_report)
        shutil.copy2(SOURCE, output / "original-ground-truth.ifc")
        shutil.copy2(fixture / "damaged.ifc", output / "damaged.ifc")
        shutil.copy2(repaired_path, output / "repaired.ifc")
        window_comparison = mapped["elements"][0]
        effective_match = window_comparison["effective_properties"][
            "complete_match"
        ]
        contract_pass = (
            attempts["stage1"] > 0
            and attempts["stage2"] > 0
            and intent_document.get("schema_version") == intent_schema_version
            and changeset.get("schema_version") == expected_changeset_version
            and confirmation is not None
            and confirmation["item_count"] == len(PROPERTY_FACTS)
            and final.successful_artifact_publishable
            and _levels(production)
            == {"L1": "passed", "L2": "passed", "L3": "not_required"}
            and _levels(dict(benchmark.private_report))
            == {"L1": "passed", "L2": "passed", "L3": "not_required"}
            and effective_match
        )
        return {
            "schema_version": "text2ifc/phase10.1-full-replication/0.1",
            "status": final.status,
            "reason_code": final.reason_code,
            "run_id": final.run_id,
            "provider_attempts": attempts,
            "provider": _provider_metadata(run_dir),
            "contract_versions": {
                "requested_repair_intent": intent_schema_version,
                "actual_repair_intent": intent_document.get("schema_version"),
                "expected_bound_changeset": expected_changeset_version,
                "actual_bound_changeset": changeset.get("schema_version"),
            },
            "confirmation": confirmation,
            "property_fact_count": len(PROPERTY_FACTS),
            "original_window_global_id": WINDOW_ID,
            "repaired_window_global_id": new_window_id,
            "production_levels": _levels(production),
            "private_benchmark_levels": _levels(dict(benchmark.private_report)),
            "mapped_effective_properties_complete_match": effective_match,
            "mapped_direct_properties_complete_match": window_comparison[
                "direct_properties"
            ]["complete_match"],
            "mapped_attribute_complete_match": window_comparison["attributes"][
                "complete_match"
            ],
            "official_added_count": len(official["added_ids"]),
            "official_deleted_count": len(official["deleted_ids"]),
            "official_changed_count": len(official["changed"]),
            "source_sha256": _sha256(SOURCE),
            "damaged_sha256": _sha256(fixture / "damaged.ifc"),
            "repaired_sha256": _sha256(repaired_path),
            "contract_pass": contract_pass,
            "synthetic_fallback": False,
            "runtime_source": _runtime_source_evidence(),
        }
    except Exception as error:
        return {
            "schema_version": "text2ifc/phase10.1-full-replication/0.1",
            "status": "provider_failed",
            "reason_code": str(getattr(error, "code", type(error).__name__))[:128],
            "detail": str(error)[:1000],
            "provider_attempts": _provider_attempts(runtime),
            "contract_versions": {
                "requested_repair_intent": intent_schema_version,
                "expected_bound_changeset": (
                    "text2ifc/ifc-repair-changeset/0.3"
                    if intent_schema_version
                    == "text2ifc/ifc-repair-intent/0.4"
                    else "text2ifc/ifc-repair-changeset/0.2"
                ),
            },
            "contract_pass": False,
            "synthetic_fallback": False,
            "runtime_source": _runtime_source_evidence(),
        }


if __name__ == "__main__":
    raise SystemExit(main())
