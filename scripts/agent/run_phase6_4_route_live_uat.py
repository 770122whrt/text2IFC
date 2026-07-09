"""Run Phase 6.4 route-level live UAT with an OpenAI-compatible provider."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.agent.run_phase6_2_cli import load_env_file  # noqa: E402
from text2ifc_agent.openai_compat import (  # noqa: E402
    load_openai_compatible_runtime_config,
    parse_chat_completion_evidence,
    token_limit_request,
)
from text2ifc_agent.providers import redact_provider_payload  # noqa: E402
from text2ifc_agent.route_live_uat import (  # noqa: E402
    AUTO_RESOLVED_STATUS,
    CASE_SCHEMA_VERSION,
    CORRECT_TERMINAL_STATUS,
    RETRY_CONTROL_STATUS,
    build_route_live_uat_summary,
)


DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.4-route-live-uat"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--case", choices=sorted(_cases()), action="append")
    args = parser.parse_args(argv)

    load_env_file(args.env_file)
    config = load_openai_compatible_runtime_config(dict(os.environ))
    from openai import OpenAI

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    args.output_root.mkdir(parents=True, exist_ok=True)
    case_ids = args.case or list(_cases())
    for case_id in case_ids:
        _run_case(client=client, config=config, output_root=args.output_root, case=_cases()[case_id])
    summary = build_route_live_uat_summary(args.output_root)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_required_routes_live_checked"] else 2


def _run_case(*, client: Any, config: Any, output_root: Path, case: dict[str, Any]) -> None:
    case_dir = output_root / "cases" / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    prompt = _render_prompt(case)
    request = {
        "model": config.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request.update(token_limit_request(config))
    response = client.chat.completions.create(**request)
    payload = _object_to_dict(response)
    evidence = parse_chat_completion_evidence(
        payload,
        request=request,
        evidence_class="live_route_uat",
        provider_label=config.provider_label,
    )
    parsed = _parse_model_json(str(evidence["content_text"]))
    valid = _valid_case_output(parsed, case)
    case_result = {
        "schema_version": CASE_SCHEMA_VERSION,
        "case_id": case["case_id"],
        "route": case["route"],
        "status": case["expected_status"] if valid else "invalid_live_output",
        "provider": config.provider_label,
        "model": evidence.get("model"),
        "response_id": evidence.get("response_id"),
        "finish_reason": evidence.get("finish_reason"),
        "model_output_valid": valid,
        "model_output": parsed,
        "evidence_paths": [
            f"cases/{case['case_id']}/request.redacted.json",
            f"cases/{case['case_id']}/response.raw.json",
            f"cases/{case['case_id']}/parsed-output.json",
        ],
    }
    _write_json(case_dir / "request.redacted.json", redact_provider_payload(request))
    _write_json(case_dir / "response.raw.json", redact_provider_payload(payload))
    _write_json(case_dir / "parsed-output.json", parsed)
    _write_json(output_root / "cases" / f"{case['case_id']}.json", case_result)


def _render_prompt(case: dict[str, Any]) -> str:
    return (
        "You are the text2IFC Phase 6.4 route UAT agent. "
        "Return one bare JSON object only. Do not include Markdown. "
        "You must not output IFC, STEP text, tokens, secrets, or provider URLs.\n\n"
        f"Route under test: {case['route']}\n"
        f"Expected status: {case['expected_status']}\n"
        f"Issue feedback: {json.dumps(case['issue'], ensure_ascii=False, sort_keys=True)}\n\n"
        "Return exactly these fields:\n"
        "{\n"
        '  "route": string,\n'
        '  "target_stage": string,\n'
        '  "resolution_status": string,\n'
        '  "action_summary": string,\n'
        '  "should_continue_pipeline": boolean,\n'
        '  "should_ask_user": boolean,\n'
        '  "should_block": boolean\n'
        "}\n\n"
        f"The route must be {case['route']}. "
        f"The resolution_status must be {case['resolution_status']}. "
        "For auto-fix routes, describe the correction action. "
        "For terminal routes, explain why the system must not fabricate a fix."
    )


def _valid_case_output(payload: dict[str, Any], case: dict[str, Any]) -> bool:
    if payload.get("route") != case["route"]:
        return False
    if payload.get("resolution_status") != case["resolution_status"]:
        return False
    for key in ("target_stage", "action_summary"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            return False
    for key in ("should_continue_pipeline", "should_ask_user", "should_block"):
        if not isinstance(payload.get(key), bool):
            return False
    return True


def _parse_model_json(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("route live UAT output must be a JSON object")
    return payload


def _cases() -> dict[str, dict[str, Any]]:
    return {
        "ask_user": {
            "case_id": "ask_user",
            "route": "ask_user",
            "expected_status": CORRECT_TERMINAL_STATUS,
            "resolution_status": "needs_user_answer",
            "issue": {
                "owner": "user",
                "issue_type": "missing_required_fact",
                "evidence": "Wall thickness and floor thickness are missing.",
            },
        },
        "regenerate_json": {
            "case_id": "regenerate_json",
            "route": "regenerate_json",
            "expected_status": AUTO_RESOLVED_STATUS,
            "resolution_status": "generator_feedback_ready",
            "issue": {
                "owner": "generator",
                "issue_type": "missing_vertical_connection",
                "evidence": "The Design Brief asks for two storeys and a stair, but the candidate is missing a vertical connection.",
            },
        },
        "revise_design_brief": {
            "case_id": "revise_design_brief",
            "route": "revise_design_brief",
            "expected_status": AUTO_RESOLVED_STATUS,
            "resolution_status": "design_brief_feedback_ready",
            "issue": {
                "owner": "design_brief",
                "issue_type": "changed_original_request",
                "evidence": "The Design Brief added a room that the original user request did not contain.",
            },
        },
        "repair_json": {
            "case_id": "repair_json",
            "route": "repair_json",
            "expected_status": AUTO_RESOLVED_STATUS,
            "resolution_status": "repair_feedback_ready",
            "issue": {
                "owner": "repair",
                "issue_type": "schema_mismatch",
                "evidence": "The candidate is parseable but has a repairable schema mismatch.",
            },
        },
        "provider_retry": {
            "case_id": "provider_retry",
            "route": "provider_retry",
            "expected_status": RETRY_CONTROL_STATUS,
            "resolution_status": "provider_retry_ready",
            "issue": {
                "owner": "provider",
                "issue_type": "provider_truncation",
                "evidence": "The previous provider response was truncated with finish_reason=length.",
            },
        },
        "blocked_as_unsupported": {
            "case_id": "blocked_as_unsupported",
            "route": "blocked_as_unsupported",
            "expected_status": CORRECT_TERMINAL_STATUS,
            "resolution_status": "unsupported_blocked",
            "issue": {
                "owner": "compiler",
                "issue_type": "compiler_unsupported_feature",
                "evidence": "The requested feature is outside the current compiler support boundary.",
            },
        },
        "gate_issue": {
            "case_id": "gate_issue",
            "route": "gate_issue",
            "expected_status": CORRECT_TERMINAL_STATUS,
            "resolution_status": "gate_review_required",
            "issue": {
                "owner": "gate",
                "issue_type": "gate_false_positive",
                "evidence": "The gate applicability is disputed and must not be overridden by Audit wording.",
            },
        },
        "runtime_blocked": {
            "case_id": "runtime_blocked",
            "route": "runtime_blocked",
            "expected_status": CORRECT_TERMINAL_STATUS,
            "resolution_status": "runtime_blocked",
            "issue": {
                "owner": "runtime",
                "issue_type": "runtime_error",
                "evidence": "The run hit an unexpected local exception after a session directory existed.",
            },
        },
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _object_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        return dumped if isinstance(dumped, dict) else {}
    return {}


if __name__ == "__main__":
    raise SystemExit(main())
