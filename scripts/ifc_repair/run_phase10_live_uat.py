"""Opt-in Phase 10 four-path DeepSeek Window UAT with honest evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
DEFAULT_OUTPUT = ROOT / "dataset" / "processed" / "ifc-repair" / "phase10-live-uat"
TOKEN_GUARD = 65_536
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"
OPENING_ID = "2cXV28XOjE6f6irhW0CO4t"
WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"
TYPE_ID = "2cXV28XOjE6f6irhu0CO_c"
TYPE_NAME = "M_Fixed:0915 x 1830mm"
GEOMETRY = "开洞宽 915 mm、高 1830 mm、窗台高 305 mm；窗中心距 wall_local_start 3042.5 mm。"


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
    args.output_root.mkdir(parents=True, exist_ok=True)
    if config["status"] != "ready":
        failed = {**config, "schema_version": "text2ifc/phase10-live-uat/0.1", "mode": "live", "status": "not_configured"}
        _write(args.output_root / "live-uat-result.json", failed)
        print(_json(failed))
        return 2

    run_root = args.output_root / datetime.now(timezone.utc).strftime("uat-%Y%m%dT%H%M%S%fZ")
    run_root.mkdir(parents=True, exist_ok=False)
    cases = [
        _run_case(
            run_root / "complete-request", environment, "complete-request",
            f"在 GlobalId 为 {WALL_ID} 的 IfcWall 上恢复缺失窗，明确使用 GlobalId 为 {TYPE_ID} 的现有 Window Type。{GEOMETRY}",
        ),
        _run_case(
            run_root / "clarification-completed", environment, "clarification-completed",
            f"在 GlobalId 为 {WALL_ID} 的 IfcWall 上恢复缺失窗，明确使用 GlobalId 为 {TYPE_ID} 的现有 Window Type。",
            feedback=GEOMETRY,
        ),
        _run_case(
            run_root / "type-name-no-guid", environment, "type-name-no-guid",
            f"在 GlobalId 为 {WALL_ID} 的 IfcWall 上恢复缺失窗，使用现有 Window Type“{TYPE_NAME}”，但不要依赖用户提供 Type GUID。{GEOMETRY}",
        ),
        _run_case(
            run_root / "dimensions-then-prototype-confirmation", environment,
            "dimensions-then-prototype-confirmation",
            f"在 GlobalId 为 {WALL_ID} 的 IfcWall 上恢复一扇 fixed window。请按 915 x 1830 mm 列出可用 Type，等我确认后再使用。{GEOMETRY}",
            confirm_prototype=True,
        ),
    ]
    passed = all(case["contract_pass"] for case in cases)
    result = {
        "schema_version": "text2ifc/phase10-live-uat/0.1",
        "mode": "live",
        "status": "passed" if passed else "failed",
        "source_sha256": _sha256(SOURCE),
        "cases": cases,
        "token_guard": {"max_input_tokens": TOKEN_GUARD, "max_completion_tokens": TOKEN_GUARD},
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
    *,
    feedback: str | None = None,
    confirm_prototype: bool = False,
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
    captured: dict[str, dict] = {}

    def capture_application(**kwargs):
        captured["application"] = apply_changeset(**kwargs)
        return captured["application"]

    try:
        provider = OpenAICompatibleLiveProvider(
            config=load_openai_compatible_runtime_config(environment)
        )
        api = RepairAPI(
            runtime,
            provider=provider,
            orchestrator_options={"apply_stage": capture_application},
        )
        initial = api.start(fixture / "damaged.ifc", request)
        final = initial
        clarification = initial.clarification
        feedback_applied = False
        prototype_confirmed = False
        if feedback is not None and clarification is not None:
            final = api.continue_with_answer(
                initial.run_id,
                {"kind": "add_detail", "detail": feedback},
                clarification_id=clarification.clarification_id,
                expected_state_version=initial.state_version,
            )
            feedback_applied = True
        elif confirm_prototype and clarification is not None and clarification.reason_code == "prototype_selection" and len(clarification.candidates) == 1:
            final = api.continue_with_answer(
                initial.run_id,
                {"kind": "authorize_prototype", "candidate_token": clarification.candidates[0].token, "authorized": True},
                clarification_id=clarification.clarification_id,
                expected_state_version=initial.state_version,
            )
            prototype_confirmed = True
        run_dir = runtime / final.run_directory
        attempts = _provider_attempts(run_dir)
        production = _read_json(run_dir / final.artifacts["evaluation"]) if "evaluation" in final.artifacts else {}
        production_levels = _levels(production)
        changeset_path = run_dir / "changeset.json"
        changeset = _read_json(changeset_path) if changeset_path.is_file() else {}
        benchmark_levels: dict[str, str] = {}
        benchmark_path: str | None = None
        if final.successful_artifact_publishable and "application" in captured and "successful_ifc" in final.artifacts:
            benchmark = evaluate_benchmark(
                BenchmarkEvaluationInputs(
                    production=ProductionEvaluationInputs(
                        damaged_ifc_path=fixture / "damaged.ifc",
                        repaired_ifc_path=run_dir / final.artifacts["successful_ifc"],
                        changeset=changeset,
                        application_result=captured["application"],
                        registry=api.registry,
                    ),
                    private_original_ifc_path=SOURCE,
                    private_mutation_mapping={"operation-1": {"wall": WALL_ID, "opening": OPENING_ID, "window": WINDOW_ID}},
                )
            )
            private_report = dict(benchmark.private_report)
            benchmark_levels = _levels(private_report)
            benchmark_file = output / "private-benchmark-evaluation.json"
            _write(benchmark_file, private_report)
            benchmark_path = benchmark_file.relative_to(output).as_posix()
        expected_clarification = feedback is not None or confirm_prototype
        clarification_ok = (
            clarification is None
            if not expected_clarification
            else clarification is not None and clarification.reason_code == (
                "prototype_selection" if confirm_prototype else "missing_required_parameter"
            )
        )
        contract_pass = (
            clarification_ok
            and (feedback is None or feedback_applied)
            and (not confirm_prototype or prototype_confirmed)
            and attempts["stage1"] > 0
            and attempts["stage2"] > 0
            and changeset.get("schema_version") == "text2ifc/ifc-repair-changeset/0.2"
            and changeset.get("binding_status") == "bound"
            and final.complete_repair_success
            and final.successful_artifact_publishable
            and production_levels == {"L1": "passed", "L2": "passed", "L3": "not_required"}
            and benchmark_levels == {"L1": "passed", "L2": "passed", "L3": "not_required"}
        )
        result = {
            "case_id": case_id,
            "status": final.status,
            "reason_code": final.reason_code,
            "run_id": final.run_id,
            "provider": _provider_metadata(run_dir),
            "provider_attempts": attempts,
            "clarification_reason": None if clarification is None else clarification.reason_code,
            "feedback_applied": feedback_applied,
            "prototype_confirmed": prototype_confirmed,
            "changeset_schema": changeset.get("schema_version"),
            "binding_status": changeset.get("binding_status"),
            "production_levels": production_levels,
            "private_benchmark_levels": benchmark_levels,
            "private_benchmark_artifact": benchmark_path,
            "successful_ifc": final.artifacts.get("successful_ifc"),
            "output_sha256": None if "successful_ifc" not in final.artifacts else _sha256(run_dir / final.artifacts["successful_ifc"]),
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


def _levels(report: dict[str, Any]) -> dict[str, str]:
    operations = report.get("operations", ())
    if not operations:
        return {}
    return {str(item["level"]): str(item["status"]) for item in operations[0].get("levels", ())}


def _provider_attempts(root: Path) -> dict[str, int]:
    return {
        "stage1": len([path for path in root.rglob("attempt-*.json") if "intent" in path.parts]),
        "stage2": len(list(root.rglob("changeset/attempt-*/provider-metadata.json"))),
    }


def _provider_metadata(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(root.rglob("provider-metadata.json")):
        payload = _read_json(path)
        result.append({
            "stage": "stage2" if "changeset" in path.parts else "stage1",
            "provider": payload.get("provider"),
            "model": payload.get("model"),
        })
    return result


def _config_result(environment: dict[str, str]) -> dict[str, Any]:
    config = load_openai_compatible_config(environment)
    ready = (
        bool(config.get("configured"))
        and config.get("max_input_tokens") == TOKEN_GUARD
        and config.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "schema_version": "text2ifc/phase10-live-config/0.1",
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
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

