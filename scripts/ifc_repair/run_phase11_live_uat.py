"""Real, no-fallback DeepSeek UAT for Phase 11 Door routing."""

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

from text2ifc_agent.openai_compat import load_openai_compatible_config  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.mutation import remove_door  # noqa: E402


SOURCE = (
    ROOT
    / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"
)
DOOR_ID = "2cXV28XOjE6f6irgi0COhu"
OPENING_ID = "2cXV28XOjE6f6irhW0COhu"
WALL_ID = "2cXV28XOjE6f6irgi0COfF"
TYPE_ID = "2cXV28XOjE6f6irhu0COgZ"
TYPE_NAME = "M_Single-Flush:Inside Door"
DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase11-live-uat"
TOKEN_GUARD = 65_536
DETAIL = (
    "门宽 915 mm、高 2134 mm，洞口宽 915 mm、高 2134 mm，"
    "门槛高度 0 mm，洞口中心距墙局部起点 1657.5 mm，"
    "门的 OperationType 为 SINGLE_SWING_RIGHT。"
)
BASE = (
    f"在已有洞口 {OPENING_ID} 中安装一扇门；该洞口位于墙 {WALL_ID}。"
    f"明确复用现有 Door Type “{TYPE_NAME}”（GlobalId {TYPE_ID}），"
    "保留当前 IFC 中可确定的洞口、墙和楼层关系，不猜测未提供的材料或五金。"
)


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


def _config(environment: dict[str, str]) -> dict[str, Any]:
    value = load_openai_compatible_config(environment)
    ready = (
        bool(value.get("configured"))
        and value.get("max_input_tokens") == TOKEN_GUARD
        and value.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "status": "ready" if ready else "not_configured",
        "provider": value.get("provider"),
        "model": value.get("model"),
        "max_input_tokens": value.get("max_input_tokens"),
        "max_completion_tokens": value.get("max_completion_tokens"),
        "secret_redacted": True,
    }


def _attempts(root: Path) -> dict[str, int]:
    return {
        "stage1": len(
            [item for item in root.rglob("attempt-*.json") if "intent" in item.parts]
        ),
        "stage2": len(
            list(root.rglob("changeset/attempt-*/provider-metadata.json"))
        ),
    }


def _summary(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "reason_code": result.reason_code,
        "run_id": result.run_id,
        "state_version": result.state_version,
        "complete_repair_success": result.complete_repair_success,
        "successful_artifact_publishable": result.successful_artifact_publishable,
        "artifacts": dict(result.artifacts),
    }


def _artifact_hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*.json")):
        if any(token in path.name.lower() for token in ("secret", "env")):
            continue
        result[path.relative_to(root).as_posix()] = (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
    return result


def _run_case(
    root: Path,
    environment: dict[str, str],
    *,
    case_id: str,
    request: str,
    feedback: str | None,
    expect_publish: bool,
    expect_zero_stage2: bool = False,
) -> dict[str, Any]:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    fixture = case_dir / "fixture"
    remove_door(
        source_path=SOURCE,
        output_dir=fixture,
        door_global_id=DOOR_ID,
        preserve_opening=True,
    )
    runtime = case_dir / "runtime"
    try:
        api = RepairAPI.from_environment(runtime, environment)
        initial = api.start(fixture / "damaged.ifc", request)
        clarification = initial.clarification
        clarification_payload = (
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
        attempts = _attempts(runtime)
        published = bool(
            final.complete_repair_success
            and final.successful_artifact_publishable
        )
        contract_pass = (
            published == expect_publish
            and (not expect_zero_stage2 or attempts["stage2"] == 0)
            and (feedback is None or feedback_applied)
        )
        payload = {
            "case_id": case_id,
            "status": "passed" if contract_pass else "failed",
            "request_sha256": "sha256:"
            + hashlib.sha256(request.encode("utf-8")).hexdigest(),
            "feedback_sha256": (
                None
                if feedback is None
                else "sha256:"
                + hashlib.sha256(feedback.encode("utf-8")).hexdigest()
            ),
            "initial": _summary(initial),
            "clarification": clarification_payload,
            "feedback_applied": feedback_applied,
            "final": _summary(final),
            "provider_attempts": attempts,
            "synthetic_fallback_used": False,
            "contract_pass": contract_pass,
            "artifact_hashes": _artifact_hashes(runtime),
        }
    except Exception as error:
        payload = {
            "case_id": case_id,
            "status": "provider_failed",
            "reason_code": str(getattr(error, "code", type(error).__name__))[:160],
            "provider_attempts": _attempts(runtime),
            "synthetic_fallback_used": False,
            "contract_pass": False,
            "artifact_hashes": _artifact_hashes(runtime),
        }
    (case_dir / "case-result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return payload


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
    config = _config(environment)
    if args.check_config:
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 0 if config["status"] == "ready" else 2
    if config["status"] != "ready":
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 2
    run_dir = args.output_root / datetime.now(timezone.utc).strftime(
        "uat-%Y%m%dT%H%M%S%fZ"
    )
    run_dir.mkdir(parents=True)
    cases = [
        _run_case(
            run_dir,
            environment,
            case_id="complete-door",
            request=BASE + DETAIL,
            feedback=None,
            expect_publish=True,
        ),
        _run_case(
            run_dir,
            environment,
            case_id="incomplete-then-feedback",
            request=BASE,
            feedback=DETAIL,
            expect_publish=True,
        ),
        _run_case(
            run_dir,
            environment,
            case_id="unsupported-complex-door",
            request=(
                f"在墙 {WALL_ID} 新开洞并生成一扇双扇旋转门，"
                "要求复杂门框、五金、上亮和两扇不同开启轨迹。"
            ),
            feedback=None,
            expect_publish=False,
            expect_zero_stage2=True,
        ),
    ]
    passed = all(item["contract_pass"] for item in cases)
    result = {
        "schema_version": "text2ifc/phase11-live-uat/0.1",
        "status": "passed" if passed else "failed",
        "provider": config["provider"],
        "model": config["model"],
        "token_guard": {
            "max_input_tokens": TOKEN_GUARD,
            "max_completion_tokens": TOKEN_GUARD,
        },
        "cases": cases,
        "synthetic_fallback_used": False,
    }
    (run_dir / "live-uat-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "cases": [
                    {
                        "case_id": item["case_id"],
                        "status": item["status"],
                        "provider_attempts": item["provider_attempts"],
                        "contract_pass": item["contract_pass"],
                    }
                    for item in cases
                ],
                "result": str(run_dir / "live-uat-result.json"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
