"""DB-backed Phase 6.2 interactive Agent flows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .clarification import ClarificationCall, ClarificationController, DesignBriefInvoker
from .context_selection import select_design_brief_context
from .design_brief import load_design_brief_schema, validate_design_brief
from .openai_compat import (
    OpenAICompatError,
    OpenAICompatRuntimeConfig,
    parse_chat_completion_evidence,
)
from .prompt_registry import render_prompt
from .providers import ProviderOutput
from .session_store import SessionStore


DESIGN_BRIEF_TEMPLATE_ID = "design-brief.v2.1"


@dataclass(frozen=True)
class DesignBriefLoopResult:
    session_id: str
    session_hash: str
    status: str
    call_count: int


def make_openai_design_brief_invoker(
    *,
    config: OpenAICompatRuntimeConfig,
    run_dir: Path | str,
    client_factory: Callable[..., Any] | None = None,
) -> DesignBriefInvoker:
    """Create a Design Brief invoker backed by OpenAI-compatible Chat Completions."""

    root = Path(run_dir)
    client = _openai_client(config=config, client_factory=client_factory)

    def invoke(transcript: list[dict[str, Any]], call_index: int) -> ClarificationCall:
        if not transcript:
            raise ValueError("Design Brief invocation requires transcript")
        original_request = str(transcript[0].get("content", ""))
        call_dir = root / "calls" / f"{call_index:02d}-design-brief"
        call_dir.mkdir(parents=True, exist_ok=True)
        selection = select_design_brief_context(
            user_request=original_request,
            conversation=transcript,
        )
        schema = load_design_brief_schema("text2ifc/design-brief/2.0")
        renderer_inputs = {
            "USER_REQUEST": original_request,
            "CONVERSATION": transcript,
            "DESIGN_BRIEF_SCHEMA": schema,
            "EVIDENCE_CATALOG": selection["evidence"],
            "FEW_SHOTS": selection["few_shots"],
        }
        rendered = render_prompt(
            template_id=DESIGN_BRIEF_TEMPLATE_ID,
            inputs=renderer_inputs,
        )
        request = {
            "model": config.model,
            "messages": [{"role": "user", "content": rendered["text"]}],
            "temperature": 0,
            "max_completion_tokens": config.max_completion_tokens,
        }
        response = client.chat.completions.create(**request)
        payload = _object_to_dict(response)
        evidence = parse_chat_completion_evidence(
            payload,
            request=request,
            evidence_class="live",
        )
        provider_output = ProviderOutput(
            text=str(evidence["content_text"]),
            metadata={
                "provider": "mimo-openai-compatible",
                "response_id": evidence["response_id"],
                "finish_reason": evidence["finish_reason"],
                "model": evidence["model"],
            },
        )
        parse_status, parsed, diagnostics = provider_output.parse_json()
        if parse_status != "ok" or parsed is None:
            raise OpenAICompatError(
                "OpenAI-compatible Design Brief response is not valid JSON",
                evidence={"parse_status": parse_status, "diagnostics": diagnostics},
            )
        if diagnostics:
            raise OpenAICompatError(
                "OpenAI-compatible Design Brief violated strict JSON output contract",
                evidence={"parse_status": parse_status, "diagnostics": diagnostics},
            )
        issues = validate_design_brief(
            parsed,
            evidence_catalog=selection["evidence"],
        )
        if issues:
            raise OpenAICompatError(
                "OpenAI-compatible Design Brief failed schema validation",
                evidence={
                    "issues": [
                        {
                            "code": issue.code,
                            "path": issue.path,
                            "message": issue.message,
                        }
                        for issue in issues
                    ]
                },
            )

        _write_json(call_dir / "conversation.json", transcript)
        _write_json(call_dir / "context-selection.json", selection)
        _write_json(call_dir / "prompt-render-input.json", renderer_inputs)
        (call_dir / "prompt-rendered.md").write_text(rendered["text"], encoding="utf-8")
        _write_json(call_dir / "request.redacted.json", evidence["request"])
        _write_json(call_dir / "response.raw.json", payload)
        (call_dir / "model-text.txt").write_text(str(evidence["content_text"]), encoding="utf-8")
        _write_json(call_dir / "parsed-output.json", parsed)
        _write_json(call_dir / "design-brief.json", parsed)
        _write_json(
            call_dir / "metrics.json",
            {
                "response_id": evidence["response_id"],
                "model": evidence["model"],
                "finish_reason": evidence["finish_reason"],
                "usage": evidence["usage"],
                "prompt_template_id": rendered["metadata"]["template_id"],
                "prompt_template_hash": rendered["metadata"]["template_hash"],
                "parse_valid": True,
                "schema_semantic_valid": True,
                "strict_output_contract_valid": True,
                "design_status": parsed.get("status"),
                "question_count": len(parsed.get("clarification_questions", [])),
            },
        )
        return ClarificationCall(
            call_index=call_index,
            response_id=str(evidence["response_id"]),
            prompt_template_id=str(rendered["metadata"]["template_id"]),
            prompt_template_hash=str(rendered["metadata"]["template_hash"]),
            artifact_dir=str(call_dir),
            brief=parsed,
            evidence_catalog=list(selection["evidence"]),
        )

    return invoke


def run_design_brief_clarification_loop(
    *,
    store: SessionStore,
    session: str,
    invoke_design_brief: DesignBriefInvoker,
    user_answers: Iterable[str],
) -> DesignBriefLoopResult:
    """Run Design Brief clarification while persisting all turns in the DB."""

    stored_session = store.get_session(session)
    controller = ClarificationController.start(
        case_id=stored_session.session_hash,
        user_request=stored_session.original_input,
    )
    persisted_turn_count = 1

    first_call = invoke_design_brief(controller.transcript_dicts(), 1)
    controller = controller.record_model_call(first_call)
    _record_call(store, stored_session.session_id, first_call)
    persisted_turn_count = _persist_new_turns(
        store=store,
        session_id=stored_session.session_id,
        controller=controller,
        persisted_turn_count=persisted_turn_count,
    )

    answers = iter(user_answers)
    while controller.status == "needs_clarification":
        try:
            answer = next(answers)
        except StopIteration:
            break
        controller = controller.answer_and_rerun(
            answer=answer,
            invoke_design_brief=invoke_design_brief,
        )
        _record_call(store, stored_session.session_id, controller.calls[-1])
        persisted_turn_count = _persist_new_turns(
            store=store,
            session_id=stored_session.session_id,
            controller=controller,
            persisted_turn_count=persisted_turn_count,
        )

    store.mark_session_status(stored_session.session_id, controller.status)
    _write_design_brief_artifact(store, stored_session.session_id, controller.calls[-1])
    return DesignBriefLoopResult(
        session_id=stored_session.session_id,
        session_hash=stored_session.session_hash,
        status=controller.status,
        call_count=len(controller.calls),
    )


def _record_call(store: SessionStore, session_id: str, call: ClarificationCall) -> None:
    store.record_agent_call(
        session_id,
        {
            "role": "design_brief",
            "call_index": call.call_index,
            "response_id": call.response_id,
            "prompt_template_id": call.prompt_template_id,
            "prompt_template_hash": call.prompt_template_hash,
            "artifact_dir": call.artifact_dir,
            "status": call.brief.get("status"),
        },
    )


def _persist_new_turns(
    *,
    store: SessionStore,
    session_id: str,
    controller: ClarificationController,
    persisted_turn_count: int,
) -> int:
    for turn in controller.transcript[persisted_turn_count:]:
        store.append_turn(session_id, role=turn.role, text=turn.content)
    return len(controller.transcript)


def _write_design_brief_artifact(
    store: SessionStore,
    session_id: str,
    call: ClarificationCall,
) -> None:
    session = store.get_session(session_id)
    artifact_path = session.run_dir / "design-brief.json"
    artifact_path.write_text(
        json.dumps(call.brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    store.record_artifact(
        session.session_id,
        kind="design_brief",
        path=Path("runs") / session.session_hash / "design-brief.json",
    )


def _openai_client(
    *,
    config: OpenAICompatRuntimeConfig,
    client_factory: Callable[..., Any] | None,
) -> Any:
    if client_factory is None:
        from openai import OpenAI

        client_factory = OpenAI
    return client_factory(api_key=config.api_key, base_url=config.base_url)


def _object_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
