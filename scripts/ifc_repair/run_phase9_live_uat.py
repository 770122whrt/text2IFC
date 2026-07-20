"""Opt-in Phase 9 DeepSeek two-stage public repair UAT."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import load_openai_compatible_config  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.mutation import remove_window_and_opening  # noqa: E402


SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
DEFAULT_OUTPUT = ROOT / "dataset" / "processed" / "ifc-repair" / "phase9-live-uat"
TOKEN_GUARD = 65_536
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
WALL_GLOBAL_ID = "1F6umJ5H50aeL3A1As_wTm"
OPENING_GLOBAL_ID = "2cXV28XOjE6f6irhW0CO4t"
WINDOW_GLOBAL_ID = "2cXV28XOjE6f6irgi0CO4t"
WINDOW_TYPE_GLOBAL_ID = "2cXV28XOjE6f6irhu0CO_c"
WINDOW_TYPE_NAME = "M_Fixed:0915 x 1830mm"
GEOMETRY_DETAIL = (
    "开洞宽 915 毫米、高 1830 毫米、窗台高 305 毫米；"
    "窗中心距 wall_local_start 3042.5 毫米。"
)
BASE_REQUEST = (
    f"在 GlobalId 为 {WALL_GLOBAL_ID} 的 IfcWall 上恢复一扇缺失的窗，"
    f"明确使用 GlobalId 为 {WINDOW_TYPE_GLOBAL_ID} 的现有 Window Type 作为 Prototype。"
    "保留当前 damaged IFC 中可确定的 IFC2X3 关系、属性集和材料语义，不要猜测缺失事实。"
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
    check = _config_result(environment)
    if args.check_config:
        print(_compact(check))
        return 0
    args.output_root.mkdir(parents=True, exist_ok=True)
    if check["status"] != "ready":
        result = {**check, "schema_version": "text2ifc/phase9-live-uat/0.1", "mode": "live", "provider_attempts": {"stage1": 0, "stage2": 0}}
        _write(args.output_root / "live-uat-result.json", result)
        print(_compact(result))
        return 2
    unique = datetime.now(timezone.utc).strftime("uat-%Y%m%dT%H%M%S%fZ")
    output = args.output_root / unique
    output.mkdir(parents=True, exist_ok=False)
    cases = [
        _run_case(
            output / "complete-input",
            environment,
            case_id="complete-input",
            request=f"{BASE_REQUEST}{GEOMETRY_DETAIL}",
            feedback=None,
        ),
        _run_case(
            output / "incomplete-then-feedback",
            environment,
            case_id="incomplete-then-feedback",
            request=BASE_REQUEST,
            feedback=GEOMETRY_DETAIL,
        ),
        _run_case(
            output / "type-name-no-guid",
            environment,
            case_id="type-name-no-guid",
            request=(
                f"在 GlobalId 为 {WALL_GLOBAL_ID} 的 IfcWall 上恢复一扇缺失的窗，"
                f"使用名为 {WINDOW_TYPE_NAME} 的现有 Window Type；{GEOMETRY_DETAIL}"
            ),
            feedback=None,
            expected_type_clarification=False,
        ),
        _run_case(
            output / "dimensions-then-prototype-confirmation",
            environment,
            case_id="dimensions-then-prototype-confirmation",
            request=(
                f"在 GlobalId 为 {WALL_GLOBAL_ID} 的 IfcWall 上恢复一扇固定窗；"
                f"请根据 915 x 1830 mm 的类别和尺寸列出可用 Type 供我确认；{GEOMETRY_DETAIL}"
            ),
            feedback=None,
            expected_type_clarification=True,
        ),
    ]
    passed = all(case["contract_pass"] for case in cases)
    payload = {
        "schema_version": "text2ifc/phase9-live-uat/0.2",
        "mode": "live",
        "status": "passed" if passed else "failed",
        "cases": cases,
        "token_guard": {
            "max_input_tokens": TOKEN_GUARD,
            "max_completion_tokens": TOKEN_GUARD,
        },
        "evidence_class": "live_provider_uat",
    }
    exit_code = 0 if passed else 2
    _write(output / "live-uat-result.json", payload)
    print(_compact(payload))
    return exit_code


def _run_case(
    output: Path,
    environment: dict[str, str],
    *,
    case_id: str,
    request: str,
    feedback: str | None,
    expected_type_clarification: bool = False,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    fixture = output / "fixture"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=fixture,
        wall_global_id=WALL_GLOBAL_ID,
        opening_global_id=OPENING_GLOBAL_ID,
        window_global_id=WINDOW_GLOBAL_ID,
        expected_source_sha256=SOURCE_SHA256,
    )
    runtime = output / "runtime"
    try:
        api = RepairAPI.from_environment(runtime, environment)
        initial = api.start(fixture / "damaged.ifc", request)
        initial_summary = _result_summary(initial)
        clarification = initial.clarification
        clarification_summary = (
            None
            if clarification is None
            else {
                "clarification_id": clarification.clarification_id,
                "reason_code": clarification.reason_code,
                "question": clarification.question,
                "answer_modes": list(clarification.answer_modes),
            }
        )
        final = initial
        feedback_applied = False
        if feedback is not None and clarification is not None:
            final = api.continue_with_answer(
                initial.run_id,
                {"kind": "add_detail", "detail": feedback},
                clarification_id=clarification.clarification_id,
                expected_state_version=initial.state_version,
            )
            feedback_applied = True
        prototype_confirmed = False
        offered_type_candidates: list[dict[str, object]] = []
        if expected_type_clarification and clarification is not None:
            offered_type_candidates = [item.to_dict() for item in clarification.candidates]
            if (
                clarification.reason_code == "prototype_selection"
                and len(clarification.candidates) == 1
            ):
                candidate = clarification.candidates[0]
                final = api.continue_with_answer(
                    initial.run_id,
                    {
                        "kind": "authorize_prototype",
                        "candidate_token": candidate.token,
                        "authorized": True,
                    },
                    clarification_id=clarification.clarification_id,
                    expected_state_version=initial.state_version,
                )
                prototype_confirmed = True
        run_dir = runtime / final.run_directory
        attempts = _provider_attempts(run_dir)
        expected_initial_clarification = feedback is not None or expected_type_clarification
        clarification_ok = (
            clarification is not None
            and clarification.reason_code == (
                "prototype_selection"
                if expected_type_clarification
                else "missing_required_parameter"
            )
            if expected_initial_clarification
            else clarification is None
        )
        reached_stage2 = attempts["stage2"] > 0
        resolved_type_guid = _resolved_type_guid(run_dir)
        false_conflict_absent = not _contains_text(
            run_dir, "PROTOTYPE_TYPE_FACT_CONFLICT"
        )
        contract_pass = (
            clarification_ok
            and (feedback is None or feedback_applied)
            and (not expected_type_clarification or prototype_confirmed)
            and reached_stage2
            and resolved_type_guid == WINDOW_TYPE_GLOBAL_ID
            and false_conflict_absent
            and final.status not in {"provider_failed", "invalid_input"}
        )
        payload: dict[str, object] = {
            "case_id": case_id,
            "request": request,
            "feedback": feedback,
            "feedback_applied": feedback_applied,
            "prototype_confirmed": prototype_confirmed,
            "offered_type_candidates": offered_type_candidates,
            "resolved_type_guid": resolved_type_guid,
            "false_type_conflict_absent": false_conflict_absent,
            "source_sha256": _sha256(SOURCE),
            "damaged_sha256": _sha256(fixture / "damaged.ifc"),
            "initial": initial_summary,
            "clarification": clarification_summary,
            "final": _result_summary(final),
            "provider_attempts": attempts,
            "contract_pass": contract_pass,
        }
    except Exception as error:
        payload = {
            "case_id": case_id,
            "request": request,
            "feedback": feedback,
            "status": "provider_failed",
            "reason_code": str(
                getattr(error, "code", type(error).__name__)
            )[:128],
            "provider_attempts": _provider_attempts(runtime),
            "contract_pass": False,
        }
    _write(output / "case-result.json", payload)
    return payload


def _result_summary(result: object) -> dict[str, object]:
    return {
        "status": result.status,
        "reason_code": result.reason_code,
        "run_id": result.run_id,
        "state_version": result.state_version,
        "complete_repair_success": result.complete_repair_success,
        "successful_artifact_publishable": result.successful_artifact_publishable,
        "artifacts": dict(result.artifacts),
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


def _resolved_type_guid(run_dir: Path) -> str | None:
    path = run_dir / "resolution.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    for operation in payload.get("operations", ()):
        for authority in operation.get("authorized_semantics", ()):
            if authority.get("kind") in {
                "formal_type_binding", "user_authorized_prototype"
            } and authority.get("global_id") == WINDOW_TYPE_GLOBAL_ID:
                return WINDOW_TYPE_GLOBAL_ID
    return None


def _contains_text(root: Path, needle: str) -> bool:
    for path in root.rglob("*.json"):
        try:
            if needle in path.read_text(encoding="utf-8"):
                return True
        except (OSError, UnicodeError):
            continue
    return False


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config_result(environment: dict[str, str]) -> dict[str, object]:
    config = load_openai_compatible_config(environment)
    configured = bool(config.get("configured"))
    guards_ok = (
        config.get("max_input_tokens") == TOKEN_GUARD
        and config.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "schema_version": "text2ifc/phase9-live-config/0.1",
        "status": "ready" if configured and guards_ok else "not_configured",
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
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def _compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_compact(value) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
