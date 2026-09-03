"""Opt-in Phase 10.1 two-case DeepSeek exact-property UAT.

This runner never substitutes an offline Provider response. A Provider, schema,
clarification, application, or validation failure is retained as the real
terminal result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    evaluate_benchmark,
)
from text2ifc_ifc_repair.mutation import remove_window_and_opening  # noqa: E402


SOURCE = (
    ROOT
    / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"
)
DEFAULT_OUTPUT = (
    ROOT / "dataset/processed/ifc-repair/phase10.1-live-uat"
)
TOKEN_GUARD = 65_536
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"
OPENING_ID = "2cXV28XOjE6f6irhW0CO4t"
WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"
TYPE_NAME = "M_Fixed:0915 x 1830mm"
GEOMETRY = (
    "Create a 915 mm wide and 1830 mm high window, with a 305 mm sill. "
    "Its center offset is 3042.5 mm from wall_local_start."
)
CASES = (
    (
        "exact-standard-occurrence",
        f"On IfcWall GlobalId {WALL_ID}, restore the missing window. {GEOMETRY} "
        f"Reuse the existing Window Type named '{TYPE_NAME}'. "
        "Set the occurrence property Pset_WindowCommon.FireRating to EI30.",
        "Pset_WindowCommon",
        "FireRating",
        "EI30",
    ),
    (
        "custom-property-confirmation",
        f"On IfcWall GlobalId {WALL_ID}, restore the missing window. {GEOMETRY} "
        "Set the occurrence property Custom_Asset.AssetCode to W-007.",
        "Custom_Asset",
        "AssetCode",
        "W-007",
    ),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.check_config == args.live:
        parser.error("choose exactly one of --check-config or --live")

    environment = _environment(args.env_file)
    config = _config_result(environment)
    if args.check_config:
        print(_json(config))
        return 0 if config["status"] == "ready" else 2
    if config["status"] != "ready":
        print(_json(config))
        return 2

    run_root = args.output_root / datetime.now(timezone.utc).strftime(
        "uat-%Y%m%dT%H%M%S%fZ"
    )
    run_root.mkdir(parents=True, exist_ok=False)
    results = [
        _run_case(
            run_root / case_id,
            environment,
            case_id,
            request,
            set_name,
            property_name,
            expected_value,
        )
        for case_id, request, set_name, property_name, expected_value in CASES
    ]
    passed = all(item["contract_pass"] for item in results)
    result = {
        "schema_version": "text2ifc/phase10.1-live-uat/0.1",
        "mode": "live",
        "status": "passed" if passed else "failed",
        "source_sha256": _sha256(SOURCE),
        "cases": results,
        "token_guard": {
            "max_input_tokens": TOKEN_GUARD,
            "max_completion_tokens": TOKEN_GUARD,
        },
        "synthetic_fallback": False,
        "evidence_class": "live_provider_uat",
    }
    _write(run_root / "live-uat-result.json", result)
    print(_json(result))
    return 0 if passed else 2


def _run_case(
    output: Path,
    environment: dict[str, str],
    case_id: str,
    request: str,
    set_name: str,
    property_name: str,
    expected_value: str,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
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
    captured: dict[str, dict[str, Any]] = {}

    def capture_application(**kwargs):
        captured["application"] = apply_changeset(**kwargs)
        return captured["application"]

    try:
        api = RepairAPI(
            runtime,
            provider=OpenAICompatibleLiveProvider(
                config=load_openai_compatible_runtime_config(environment)
            ),
            intent_schema_version="text2ifc/ifc-repair-intent/0.2",
            orchestrator_options={"apply_stage": capture_application},
        )
        initial = api.start(fixture / "damaged.ifc", request)
        final = initial
        preview_hash = None
        confirmation_applied = False
        if case_id == "custom-property-confirmation":
            if (
                initial.clarification is not None
                and initial.clarification.reason_code == "property_confirmation"
            ):
                preview_hash = initial.clarification.property_preview["preview_hash"]
                final = api.continue_with_answer(
                    initial.run_id,
                    {"kind": "confirm_property", "preview_hash": preview_hash},
                    clarification_id=initial.clarification.clarification_id,
                    expected_state_version=initial.state_version,
                )
                confirmation_applied = True

        run_dir = runtime / final.run_directory
        attempts = _provider_attempts(run_dir)
        evaluation = (
            _read_json(run_dir / final.artifacts["evaluation"])
            if "evaluation" in final.artifacts
            else {}
        )
        changeset_path = run_dir / "changeset.json"
        changeset = _read_json(changeset_path) if changeset_path.is_file() else {}
        actual = None
        private_levels: dict[str, str] = {}
        private_path = None
        if (
            final.successful_artifact_publishable
            and "successful_ifc" in final.artifacts
            and "application" in captured
        ):
            repaired_path = run_dir / final.artifacts["successful_ifc"]
            repaired = ifcopenshell.open(str(repaired_path))
            new_window_id = next(
                item["global_id"]
                for item in captured["application"]["operations"][0]["changes"]["created"]
                if item["role"] == "window"
            )
            actual = _direct_property(
                repaired.by_guid(new_window_id), set_name, property_name
            )
            benchmark = evaluate_benchmark(
                BenchmarkEvaluationInputs(
                    production=ProductionEvaluationInputs(
                        damaged_ifc_path=fixture / "damaged.ifc",
                        repaired_ifc_path=repaired_path,
                        changeset=changeset,
                        application_result=captured["application"],
                        registry=api.registry,
                    ),
                    private_original_ifc_path=SOURCE,
                    private_mutation_mapping={
                        str(changeset["operations"][0]["operation_id"]): {
                            "wall": WALL_ID,
                            "opening": OPENING_ID,
                            "window": WINDOW_ID,
                        }
                    },
                )
            )
            private_report = dict(benchmark.private_report)
            private_levels = _levels(private_report)
            private_file = output / "private-benchmark-evaluation.json"
            _write(private_file, private_report)
            private_path = private_file.relative_to(output).as_posix()

        production_levels = _levels(evaluation)
        clarification_ok = (
            initial.clarification is None
            if case_id == "exact-standard-occurrence"
            else confirmation_applied and preview_hash is not None
        )
        contract_pass = (
            clarification_ok
            and attempts["stage1"] > 0
            and attempts["stage2"] > 0
            and changeset.get("schema_version")
            == "text2ifc/ifc-repair-changeset/0.2"
            and changeset.get("binding_status") == "bound"
            and final.successful_artifact_publishable
            and production_levels
            == {"L1": "passed", "L2": "passed", "L3": "not_required"}
            and private_levels.get("L1") == "passed"
            and private_levels.get("L3") == "not_required"
            and private_levels.get("L2")
            == (
                "passed"
                if case_id == "exact-standard-occurrence"
                else "failed"
            )
            and actual == {
                "value": expected_value,
                "value_type": "IfcLabel",
                "ownership": "occurrence_direct",
            }
        )
        result = {
            "case_id": case_id,
            "status": final.status,
            "reason_code": final.reason_code,
            "run_id": final.run_id,
            "provider_attempts": attempts,
            "provider": _provider_metadata(run_dir),
            "clarification_reason": (
                None
                if initial.clarification is None
                else initial.clarification.reason_code
            ),
            "preview_hash_sha256": (
                None
                if preview_hash is None
                else hashlib.sha256(preview_hash.encode("utf-8")).hexdigest()
            ),
            "confirmation_applied": confirmation_applied,
            "intent_schema": "text2ifc/ifc-repair-intent/0.2",
            "changeset_schema": changeset.get("schema_version"),
            "binding_status": changeset.get("binding_status"),
            "production_levels": production_levels,
            "private_benchmark_levels": private_levels,
            "private_benchmark_artifact": private_path,
            "requested_property_actual": actual,
            "successful_ifc": final.artifacts.get("successful_ifc"),
            "output_sha256": (
                None
                if "successful_ifc" not in final.artifacts
                else _sha256(run_dir / final.artifacts["successful_ifc"])
            ),
            "contract_pass": contract_pass,
            "synthetic_fallback": False,
        }
    except Exception as error:
        result = {
            "case_id": case_id,
            "status": "provider_failed",
            "reason_code": str(getattr(error, "code", type(error).__name__))[:128],
            "provider_attempts": _provider_attempts(runtime),
            "contract_pass": False,
            "synthetic_fallback": False,
        }
    _write(output / "case-result.json", result)
    return result


def _direct_property(element: Any, set_name: str, property_name: str) -> dict[str, Any] | None:
    matches = []
    for relation in element.IsDefinedBy:
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        pset = relation.RelatingPropertyDefinition
        if pset.is_a("IfcPropertySet") and pset.Name == set_name:
            matches.extend(
                prop for prop in pset.HasProperties if prop.Name == property_name
            )
    if len(matches) != 1 or matches[0].NominalValue is None:
        return None
    return {
        "value": matches[0].NominalValue.wrappedValue,
        "value_type": matches[0].NominalValue.is_a(),
        "ownership": "occurrence_direct",
    }


def _levels(report: dict[str, Any]) -> dict[str, str]:
    operations = report.get("operations", ())
    if not operations:
        return {}
    return {
        str(item["level"]): str(item["status"])
        for item in operations[0].get("levels", ())
    }


def _provider_attempts(root: Path) -> dict[str, int]:
    return {
        "stage1": len(
            [path for path in root.rglob("attempt-*.json") if "intent" in path.parts]
        ),
        "stage2": len(
            list(root.rglob("changeset/attempt-*/provider-metadata.json"))
        ),
    }


def _provider_metadata(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(root.rglob("intent/attempt-*.json")):
        payload = _read_json(path).get("provider_metadata", {})
        if payload.get("provider") or payload.get("model"):
            result.append(
                {
                    "stage": "stage1",
                    "provider": payload.get("provider"),
                    "model": payload.get("model"),
                }
            )
    for path in sorted(root.rglob("provider-metadata.json")):
        payload = _read_json(path)
        result.append(
            {
                "stage": "stage2" if "changeset" in path.parts else "stage1",
                "provider": payload.get("provider"),
                "model": payload.get("model"),
            }
        )
    return result


def _config_result(environment: dict[str, str]) -> dict[str, Any]:
    config = load_openai_compatible_config(environment)
    ready = (
        bool(config.get("configured"))
        and config.get("max_input_tokens") == TOKEN_GUARD
        and config.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "schema_version": "text2ifc/phase10.1-live-config/0.1",
        "status": "ready" if ready else "not_configured",
        "provider": config.get("provider", "deepseek-openai-compatible"),
        "model": config.get("model"),
        "max_input_tokens": config.get("max_input_tokens"),
        "max_completion_tokens": config.get("max_completion_tokens"),
        "missing": list(config.get("missing", [])),
        "secret_redacted": True,
    }


def _environment(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
