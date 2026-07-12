"""Human-facing Phase 6.2-fix REPL orchestration."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any, Callable, TextIO

from .clarification import ClarificationController, DesignBriefInvoker
from .interactive_cli_flow import (
    _persist_new_turns,
    _record_call,
    _write_design_brief_artifact,
    run_ready_session_to_ifc,
)
from .session_store import SessionStore


InputFunc = Callable[[str], str]
DesignBriefInvokerFactory = Callable[[Path], DesignBriefInvoker]


@dataclass(frozen=True)
class ReplChatResult:
    session_id: str
    session_hash: str
    status: str
    ifc_path: str | None = None
    report_path: str | None = None


@dataclass
class _ProgressLogger:
    path: Path
    started_at: float = field(default_factory=monotonic)
    sequence: int = 0

    def record(self, stage: str, status: str, **payload: Any) -> None:
        self.sequence += 1
        event: dict[str, Any] = {
            "sequence": self.sequence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(monotonic() - self.started_at, 3),
            "stage": stage,
            "status": status,
        }
        event.update(
            {
                key: value
                for key, value in payload.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            }
        )
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def configure_utf8_stdio(stdout: TextIO | None = None) -> dict[str, str | None]:
    """Best-effort UTF-8 configuration for Windows terminal use."""

    streams = (sys.stdin, sys.stdout, sys.stderr)
    for stream in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    active_stdout = stdout or sys.stdout
    return {
        "stdin_encoding": getattr(sys.stdin, "encoding", None),
        "stdout_encoding": getattr(active_stdout, "encoding", None),
        "stderr_encoding": getattr(sys.stderr, "encoding", None),
    }


def run_repl_chat(
    *,
    store: SessionStore,
    invoke_design_brief: DesignBriefInvoker | None = None,
    design_brief_invoker_factory: DesignBriefInvokerFactory | None = None,
    input_func: InputFunc | None = None,
    stdout: TextIO | None = None,
    stop_after: str = "ifc",
    provider_factory: Callable[[], Any] | None = None,
    terminal_metadata: dict[str, Any] | None = None,
    trace_level: str | None = None,
    generation_strategy: str = "legacy_full",
) -> ReplChatResult:
    """Run a Chinese-first REPL session.

    The key product boundary is deliberate: assistant questions are printed and
    persisted before user answers are requested.
    """

    active_stdout = stdout or sys.stdout
    metadata = terminal_metadata or {}
    original_request = _read_input(
        active_stdout,
        input_func,
        "\u8bf7\u8f93\u5165\u5efa\u7b51\u9700\u6c42\uff1a",
    )
    if _is_quit(original_request):
        active_stdout.write("\u5df2\u9000\u51fa\uff0c\u672a\u521b\u5efa\u4f1a\u8bdd\u3002\n")
        active_stdout.flush()
        return ReplChatResult(session_id="", session_hash="", status="incomplete")

    session = store.create_session(original_input=original_request)
    progress_logger = _ProgressLogger(session.run_dir / "progress.jsonl")
    progress_logger.record("session", "created", session_hash=session.session_hash)
    if invoke_design_brief is None:
        if design_brief_invoker_factory is None:
            raise ValueError("REPL requires a Design Brief invoker")
        invoke_design_brief = design_brief_invoker_factory(session.run_dir)
    store.append_event(
        session.session_id,
        event_type="repl_session_started",
        payload={
            "interaction_mode": "human_repl_live",
            "input_source": "terminal",
            "terminal_encoding": metadata,
        },
    )
    active_stdout.write(
        f"\u5df2\u521b\u5efa\u4f1a\u8bdd\uff1asession_hash={session.session_hash}\n"
    )
    active_stdout.write("\u6b63\u5728\u8bf7\u6a21\u578b\u68b3\u7406\u9700\u6c42...\n")
    active_stdout.flush()

    controller = ClarificationController.start(
        case_id=session.session_hash,
        user_request=session.original_input,
    )
    persisted_turn_count = 1
    progress_logger.record("design_brief", "started", call_index=1)
    first_call = invoke_design_brief(controller.transcript_dicts(), 1)
    controller = controller.record_model_call(first_call)
    progress_logger.record(
        "design_brief",
        controller.status,
        call_index=1,
        response_id=first_call.response_id,
    )
    _record_call(store, session.session_id, first_call)
    persisted_turn_count = _persist_new_turns(
        store=store,
        session_id=session.session_id,
        controller=controller,
        persisted_turn_count=persisted_turn_count,
    )

    while controller.status == "needs_clarification":
        _display_questions(
            store=store,
            session_id=session.session_id,
            controller=controller,
            stdout=active_stdout,
        )
        store.append_event(
            session.session_id,
            event_type="user_answer_requested",
            payload={"question_ids": list(controller.pending_question_ids)},
        )
        while True:
            answer = _read_input(
                active_stdout,
                input_func,
                "\u4f60\u7684\u56de\u7b54\uff1a",
            )
            if _is_quit(answer):
                store.append_event(
                    session.session_id,
                    event_type="user_quit",
                    payload={"status": "incomplete"},
                )
                store.mark_session_status(session.session_id, "incomplete")
                store.export_session(session.session_id)
                active_stdout.write("\u5df2\u9000\u51fa\uff0c\u4f1a\u8bdd\u5df2\u4fdd\u5b58\u4e3a\u672a\u5b8c\u6210\u3002\n")
                active_stdout.flush()
                return ReplChatResult(
                    session_id=session.session_id,
                    session_hash=session.session_hash,
                    status="incomplete",
                )
            if answer:
                break
            store.append_event(
                session.session_id,
                event_type="user_empty_answer_rejected",
                payload={"question_ids": list(controller.pending_question_ids)},
            )
            active_stdout.write(
                "\u56de\u7b54\u4e0d\u80fd\u4e3a\u7a7a\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\uff1b\u8f93\u5165 quit \u9000\u51fa\u3002\n"
            )
            active_stdout.flush()
        store.append_event(
            session.session_id,
            event_type="user_answer_received",
            payload={"question_ids": list(controller.pending_question_ids)},
        )
        active_stdout.write("\u5df2\u6536\u5230\u56de\u7b54\uff0c\u6b63\u5728\u7ee7\u7eed\u68b3\u7406\u9700\u6c42...\n")
        active_stdout.flush()
        next_call_index = len(controller.calls) + 1
        progress_logger.record("design_brief", "started", call_index=next_call_index)
        controller = controller.answer_and_rerun(
            answer=answer,
            invoke_design_brief=invoke_design_brief,
        )
        progress_logger.record(
            "design_brief",
            controller.status,
            call_index=next_call_index,
            response_id=controller.calls[-1].response_id,
        )
        _record_call(store, session.session_id, controller.calls[-1])
        persisted_turn_count = _persist_new_turns(
            store=store,
            session_id=session.session_id,
            controller=controller,
            persisted_turn_count=persisted_turn_count,
        )

    store.mark_session_status(session.session_id, controller.status)
    _write_design_brief_artifact(store, session.session_id, controller.calls[-1])
    store.export_session(session.session_id)
    if controller.status == "ready":
        active_stdout.write("\u9700\u6c42\u5df2\u660e\u786e\u3002\n")
    else:
        active_stdout.write(f"\u4f1a\u8bdd\u505c\u5728 {controller.status}\u3002\n")
    active_stdout.write(f"session_hash: {session.session_hash}\n")
    active_stdout.flush()

    if stop_after == "design-brief" or controller.status != "ready":
        return ReplChatResult(
            session_id=session.session_id,
            session_hash=session.session_hash,
            status=controller.status,
        )
    if provider_factory is None:
        raise ValueError("IFC generation requires a provider_factory")
    active_stdout.write("\u6b63\u5728\u751f\u6210 BIM JSON \u5e76\u7f16\u8bd1 IFC...\n")
    active_stdout.flush()
    ifc_result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=provider_factory,
        trace_level=trace_level or "debug",
        progress=lambda stage, payload: _record_and_print_ifc_progress(
            logger=progress_logger,
            stage=stage,
            payload=payload,
            stdout=active_stdout,
        ),
        generation_strategy=generation_strategy,
    )
    _print_ifc_stage_summary(
        store=store,
        session_id=ifc_result.session_id,
        stdout=active_stdout,
    )
    if ifc_result.ifc_path:
        if ifc_result.status == "compiled":
            active_stdout.write(f"IFC: {ifc_result.ifc_path}\n")
        else:
            active_stdout.write(f"IFC（未通过最终验收）: {ifc_result.ifc_path}\n")
    if ifc_result.report_path:
        if ifc_result.status == "compiled":
            _write_fix_repl_report_and_acceptance(
                store=store,
                session_id=ifc_result.session_id,
                ifc_path=ifc_result.ifc_path,
                report_path=ifc_result.report_path,
            )
        active_stdout.write(f"report.md: {ifc_result.report_path}\n")
    if ifc_result.status != "compiled":
        provider_error_path = (
            Path(store.get_session(ifc_result.session_id).run_dir)
            / "generator"
            / "provider-error.json"
        )
        if provider_error_path.is_file():
            active_stdout.write(f"generator/provider-error.json: {provider_error_path}\n")
        feedback_path = Path(store.get_session(ifc_result.session_id).run_dir) / "geometry-feedback.json"
        if feedback_path.is_file():
            active_stdout.write(f"geometry-feedback.json: {feedback_path}\n")
        active_stdout.write(f"最终验收未通过，状态：{ifc_result.status}\n")
    active_stdout.flush()
    return ReplChatResult(
        session_id=ifc_result.session_id,
        session_hash=ifc_result.session_hash,
        status=ifc_result.status,
        ifc_path=ifc_result.ifc_path,
        report_path=ifc_result.report_path,
    )


def _display_questions(
    *,
    store: SessionStore,
    session_id: str,
    controller: ClarificationController,
    stdout: TextIO,
) -> None:
    questions = [
        turn for turn in controller.transcript if turn.role == "assistant"
    ][-len(controller.pending_question_ids) :]
    stdout.write("\u9700\u8981\u8865\u5145\u4fe1\u606f\uff1a\n")
    for index, turn in enumerate(questions, start=1):
        stdout.write(f"{index}. {turn.content}\n")
        store.append_event(
            session_id,
            event_type="assistant_question_displayed",
            payload={
                "turn_id": turn.turn_id,
                "question_ids": list(turn.question_ids),
                "text": turn.content,
            },
        )
    stdout.flush()


def _read_input(stdout: TextIO, input_func: InputFunc | None, prompt: str) -> str:
    stdout.write(prompt)
    stdout.flush()
    if input_func is None:
        value = input()
    else:
        value = input_func(prompt)
    return value.strip()


def _is_quit(value: str) -> bool:
    return value.strip().lower() in {"quit", "exit", "\u9000\u51fa", "q"}


def _print_ifc_stage_summary(
    *,
    store: SessionStore,
    session_id: str,
    stdout: TextIO,
) -> None:
    export = store.session_export_payload(session_id)
    events = export.get("events", [])
    stage_events = {
        "generator_completed": "Generator",
        "generator_provider_failed": "Provider",
        "repair_completed": "Repair",
        "audit_completed": "Audit",
        "final_acceptance_completed": "Final",
    }
    for event in events:
        if not isinstance(event, dict):
            continue
        label = stage_events.get(str(event.get("event_type")))
        if label is None:
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        status = (
            payload.get("status")
            or payload.get("route")
            or payload.get("valid")
            or "done"
        )
        details: list[str] = [f"{label}: {status}"]
        response_id = payload.get("response_id")
        if response_id:
            details.append(f"response_id={response_id}")
        if label == "Final":
            details.append(f"compile_reopen_success={payload.get('compile_reopen_success')}")
            details.append(f"geometry_success={payload.get('geometry_success')}")
        stdout.write("；".join(details) + "\n")


def _print_ifc_live_progress(
    *,
    stage: str,
    payload: dict[str, Any],
    stdout: TextIO,
) -> None:
    labels = {
        "generator": "Generator",
        "semantic_coverage": "Semantic coverage",
        "repair": "Repair",
        "candidate_gates": "Gate",
        "audit": "Audit",
        "final_acceptance": "Final",
        "scaffold": "Scaffold",
    }
    label = labels.get(stage, stage)
    status = str(payload.get("status") or payload.get("route") or "started")
    if status == "started":
        stdout.write(f"进入 {label}...\n")
    elif stage == "repair":
        stdout.write(f"{label} 路由：{status}\n")
    else:
        stdout.write(f"{label} 完成：{status}\n")
    stdout.flush()


def _record_and_print_ifc_progress(
    *,
    logger: _ProgressLogger,
    stage: str,
    payload: dict[str, Any],
    stdout: TextIO,
) -> None:
    status = str(payload.get("status") or payload.get("route") or "started")
    logger.record(
        stage,
        status,
        **{key: value for key, value in payload.items() if key not in {"status", "route"}},
    )
    _print_ifc_live_progress(stage=stage, payload=payload, stdout=stdout)


def _write_fix_repl_report_and_acceptance(
    *,
    store: SessionStore,
    session_id: str,
    ifc_path: str | None,
    report_path: str | None,
) -> None:
    session = store.get_session(session_id)
    export_path = store.export_session(session.session_id)
    export = store.session_export_payload(session.session_id)
    events = export.get("events", [])
    started = _first_event(events, "repl_session_started")
    interaction_mode = str(started.get("payload", {}).get("interaction_mode", ""))
    input_source = str(started.get("payload", {}).get("input_source", ""))
    if report_path:
        report_file = Path(report_path)
        existing = report_file.read_text(encoding="utf-8") if report_file.is_file() else ""
        section = "\n".join(
            [
                "# Phase 6.2-fix Real REPL Acceptance",
                "",
                "## REPL Interaction Evidence",
                "",
                f"- interaction_mode: `{interaction_mode}`",
                f"- input_source: `{input_source}`",
                f"- session_hash: `{session.session_hash}`",
                "",
                "```json",
                json.dumps(events, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
        report_file.write_text(section + existing, encoding="utf-8")

    artifacts = {
        "report": f"runs/{session.session_hash}/report.md",
        "session_export": f"runs/{session.session_hash}/{export_path.name}",
    }
    if ifc_path:
        artifacts["ifc"] = f"runs/{session.session_hash}/output.ifc"
    final = {
        "schema_version": "text2ifc/phase6.2-fix-final-acceptance-v1",
        "session_id": session.session_id,
        "session_hash": session.session_hash,
        "status": store.get_session(session.session_id).status,
        "interaction_mode": interaction_mode,
        "input_source": input_source,
        "artifacts": artifacts,
    }
    (store.artifact_root / "final-acceptance.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _first_event(events: list[Any], event_type: str) -> dict[str, Any]:
    for event in events:
        if isinstance(event, dict) and event.get("event_type") == event_type:
            return event
    return {}
