"""Phase 6.4 live DeepSeek UAT harness."""

from __future__ import annotations

import argparse
import io
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
from scripts.agent import run_text2ifc_chat  # noqa: E402
from text2ifc_agent.adaptive_uat import (  # noqa: E402
    AdaptiveAnswerPolicy,
    build_config_check_result,
    build_live_uat_result,
)
from text2ifc_agent.feedback_loop import write_feedback_artifacts  # noqa: E402
from text2ifc_agent.issues import Issue, write_issues  # noqa: E402
from text2ifc_agent.openai_compat import (  # noqa: E402
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
    run_openai_sdk_chat_smoke,
)
from text2ifc_agent.run_report import build_phase6_4_review_report  # noqa: E402
from text2ifc_agent.session_store import SessionStore  # noqa: E402


DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.4-live-deepseek"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--smoke-json", action="store_true")
    parser.add_argument("--live-accepted-ifc", action="store_true")
    parser.add_argument("--live-nonaccept-route", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)

    load_env_file(args.env_file)
    args.output_root.mkdir(parents=True, exist_ok=True)
    if args.check_config:
        result = build_config_check_result(load_openai_compatible_config(dict(os.environ)))
        _write_json(args.output_root / "live-uat-result.json", result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.smoke_json:
        result = _run_smoke_json(args.output_root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.live_accepted_ifc:
        result = _run_live_workflow(
            output_root=args.output_root,
            mode="live_accepted_ifc",
            initial_prompt=_accepted_prompt(),
            expected_terminal={"compiled"},
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["status"] in {"compiled", "accepted"} else 2
    if args.live_nonaccept_route:
        result = _run_live_workflow(
            output_root=args.output_root,
            mode="live_nonaccept_route",
            initial_prompt=_nonaccept_prompt(),
            expected_terminal={"draft_required", "audit_blocked", "draft_or_blocked", "final_blocked", "provider_failed"},
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    parser.error("Phase 6.4 live UAT currently requires --check-config or Wave 5 live execution.")
    return 2


def _run_smoke_json(output_root: Path) -> dict[str, Any]:
    config = load_openai_compatible_runtime_config(dict(os.environ))
    smoke = run_openai_sdk_chat_smoke(config)
    result = {
        "schema_version": "text2ifc/phase6.4-live-uat/1.0",
        "mode": "smoke_json",
        "provider": config.provider_label,
        "status": smoke.get("status"),
        "response_id": smoke.get("response_id"),
        "model": smoke.get("model"),
        "finish_reason": smoke.get("finish_reason"),
        "usage": smoke.get("usage", {}),
        "config": {"api_key": "[REDACTED]", "base_url": "[REDACTED]"},
    }
    _write_json(output_root / "smoke-json.json", result)
    _write_json(output_root / "live-uat-result.json", result)
    return result


def _run_live_workflow(
    *,
    output_root: Path,
    mode: str,
    initial_prompt: str,
    expected_terminal: set[str],
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    transcript = io.StringIO()
    input_driver = _AdaptiveInputDriver(initial_prompt=initial_prompt, stdout=transcript)
    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--env-file",
            str(ROOT / ".env"),
            "--output-root",
            str(output_root),
            "--db",
            str(output_root / "sessions.sqlite"),
            "--trace-level",
            "compact",
        ],
        input_func=input_driver,
        stdout=transcript,
    )
    store = SessionStore.open(output_root / "sessions.sqlite", artifact_root=output_root)
    try:
        session = store.list_sessions()[-1]
        export = store.session_export_payload(session.session_id)
    finally:
        store.close()
    run_dir = output_root / "runs" / session.session_hash
    _ensure_phase6_4_terminal_artifacts(
        run_dir=run_dir,
        session_hash=session.session_hash,
        original_input=initial_prompt,
        session_export=export,
        status=session.status,
    )
    if (run_dir / "case-result.json").is_file():
        build_phase6_4_review_report(case_dir=run_dir)
    response_ids, finish_reasons, usage = _collect_provider_metadata(run_dir)
    result = build_live_uat_result(
        provider="deepseek-openai-compatible",
        model=_first_model(run_dir),
        response_ids=response_ids,
        finish_reasons=finish_reasons,
        usage=usage,
        interaction_mode="adaptive_semantic_uat",
        input_source="adaptive_driver",
        used_answers_json=False,
        used_fake_or_replay_provider=False,
        artifacts={
            "session_export": f"runs/{session.session_hash}/session-export.json",
            "report": f"runs/{session.session_hash}/report.md",
            "ifc": f"runs/{session.session_hash}/output.ifc"
            if (run_dir / "output.ifc").is_file()
            else "",
        },
    )
    result.update(
        {
            "mode": mode,
            "status": session.status,
            "exit_code": exit_code,
            "session_hash": session.session_hash,
            "expected_terminal_matched": session.status in expected_terminal,
            "adaptive_answer_intents": input_driver.answer_intents,
            "events_count": len(export.get("events", [])),
        }
    )
    _write_json(output_root / f"{mode}-result.json", result)
    _write_json(output_root / "live-uat-result.json", result)
    if mode == "live_accepted_ifc" and session.status == "compiled":
        _write_json(
            output_root / "final-acceptance.json",
            {
                "schema_version": "text2ifc/phase6.4-final-acceptance/1.0",
                "session_hash": session.session_hash,
                "status": session.status,
                "artifacts": result["artifacts"],
                "live_uat_result": f"{mode}-result.json",
            },
        )
    return result


def _ensure_phase6_4_terminal_artifacts(
    *,
    run_dir: Path,
    session_hash: str,
    original_input: str,
    session_export: dict[str, Any],
    status: str,
) -> None:
    if not (run_dir / "input.txt").is_file():
        _write_text(run_dir / "input.txt", original_input)
    if not (run_dir / "conversation.json").is_file():
        _write_json(run_dir / "conversation.json", session_export.get("turns", []))
    if (run_dir / "issues.json").is_file() and (run_dir / "case-result.json").is_file():
        return
    issues = _issues_from_design_brief(run_dir, status)
    write_issues(run_dir / "issues.json", issues)
    round_record = write_feedback_artifacts(
        run_dir,
        source_stage="design_brief" if status in {"draft_required", "blocked"} else "final",
        issues=issues,
    )
    route_decision = round_record["route_decision"]
    _write_json(
        run_dir / "case-result.json",
        {
            "schema_version": "text2ifc/phase6.4-case-result/1.0",
            "case_id": session_hash,
            "input_language": "zh-CN",
            "workflow_language": "en-US-control",
            "prompt_language": "zh-CN",
            "output_type": "ifc" if status == "compiled" else "none",
            "schema_passed": (run_dir / "generator" / "validation.json").is_file(),
            "compile_reopen_passed": (run_dir / "output.ifc").is_file(),
            "deterministic_gates_passed": status == "compiled",
            "audit_passed": status == "compiled",
            "final_status": route_decision["final_status"],
            "route": route_decision["route"],
            "failure_owner": issues[0].owner if issues else None,
            "blocking_issue_count": len(issues),
            "evidence_paths": [
                path
                for path in (
                    "input.txt",
                    "conversation.json",
                    "design-brief.json",
                    "issues.json",
                    "route-decision.json",
                    "feedback-rounds.json",
                    "output.ifc",
                )
                if (run_dir / path).is_file()
            ],
        },
    )
    build_phase6_4_review_report(case_dir=run_dir)


def _issues_from_design_brief(run_dir: Path, status: str) -> list[Issue]:
    if status == "compiled":
        return []
    brief_path = run_dir / "design-brief.json"
    brief = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.is_file() else {}
    issues: list[Issue] = []
    for index, fact in enumerate(brief.get("missing_facts", []) or [], start=1):
        issues.append(
            Issue(
                issue_id=f"issue_design_brief_missing_{index:04d}",
                source="semantic_validation",
                severity="blocking",
                owner="user",
                issue_type="draft_unresolved_path",
                actual_ref=str(fact.get("path", "/missing_facts")),
                evidence=str(fact.get("message") or fact.get("reason") or "Design Brief has unresolved missing facts."),
                suggested_route="ask_user",
                retryable=True,
            )
        )
    for index, item in enumerate(brief.get("unsupported_requests", []) or [], start=1):
        issues.append(
            Issue(
                issue_id=f"issue_design_brief_unsupported_{index:04d}",
                source="semantic_validation",
                severity="blocking",
                owner="schema",
                issue_type="unsupported_schema_capability",
                actual_ref=str(item.get("path", "/unsupported_requests")),
                evidence=str(item.get("message") or item.get("reason") or "Design Brief has unsupported requests."),
                suggested_route="blocked_as_unsupported",
                retryable=False,
            )
        )
    if issues:
        return issues
    return [
        Issue(
            issue_id="issue_design_brief_terminal_0001",
            source="semantic_validation",
            severity="blocking",
            owner="user" if status == "draft_required" else "design_brief",
            issue_type="draft_unresolved_path" if status == "draft_required" else "semantic_mismatch",
            evidence=f"Design Brief terminal status is {status}.",
            suggested_route="ask_user" if status == "draft_required" else "revise_design_brief",
            retryable=status == "draft_required",
        )
    ]


class _AdaptiveInputDriver:
    def __init__(self, *, initial_prompt: str, stdout: io.StringIO) -> None:
        self.initial_prompt = initial_prompt
        self.stdout = stdout
        self.call_count = 0
        self.policy = AdaptiveAnswerPolicy(
            answers_by_intent={
                "height": "房间净高为 3000 mm。",
                "wall_thickness": "墙厚为 200 mm。",
                "slab_thickness": "地板厚度为 150 mm。",
                "door_host": "门放在南墙中央。",
                "door_dimensions": "门宽 900 mm，高 2100 mm。",
                "window_dimensions": "窗宽 1200 mm，高 1000 mm，窗台高 900 mm。",
                "unknown": "这个信息暂时不知道。",
            }
        )
        self.answer_intents: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.call_count += 1
        if self.call_count == 1:
            return self.initial_prompt
        question_text = self.stdout.getvalue().split("需要补充信息：")[-1]
        planned = self.policy.answer_question(question_text)
        self.answer_intents.append(planned.intent)
        return planned.answer


def _collect_provider_metadata(run_dir: Path) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    response_ids: list[str] = []
    finish_reasons: list[str] = []
    usage: list[dict[str, Any]] = []
    for metrics_path in sorted(run_dir.rglob("metrics.json")):
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        response_id = payload.get("response_id")
        if response_id:
            response_ids.append(str(response_id))
        finish = payload.get("finish_reason") or payload.get("stop_reason")
        if finish:
            finish_reasons.append(str(finish))
        if isinstance(payload.get("usage"), dict):
            usage.append(dict(payload["usage"]))
    if not response_ids:
        response_ids.append("missing_response_id")
    if not finish_reasons:
        finish_reasons.append("missing_finish_reason")
    return response_ids, finish_reasons, usage


def _first_model(run_dir: Path) -> str | None:
    for metrics_path in sorted(run_dir.rglob("metrics.json")):
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        model = payload.get("model")
        if model:
            return str(model)
    return os.environ.get("TEXT2IFC_DEEPSEEK_MODEL")


def _accepted_prompt() -> str:
    return (
        "创建一个名为Phase6.4验收房间的单层建筑。建筑首层标高为0米，层高为3米。"
        "创建一个矩形房间，内部净尺寸为东西方向6米、南北方向4米。"
        "房间四周使用厚度0.2米、高度3米的混凝土墙，墙体位于房间边界外侧。"
        "在南侧墙体中央设置一扇门，门宽0.9米，高2.1米。"
        "创建厚度0.15米的钢筋混凝土地板，地板顶面标高为0米。"
        "将内部空间定义为IfcSpace，空间名称为房间101。"
    )


def _nonaccept_prompt() -> str:
    return "创建一个两层住宅，但我还不知道楼梯位置、墙厚、楼板厚度和门窗尺寸。"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
