"""DB-backed Phase 6.2 interactive Agent flows."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .live_pipeline import (
    run_audit_report_stage,
    run_candidate_gate_stage,
    run_final_acceptance_stage,
    run_generator_stage,
    run_repair_stage,
    run_semantic_coverage_stage,
)
from .clarification import ClarificationCall, ClarificationController, DesignBriefInvoker
from .context_selection import select_design_brief_context
from .design_brief import load_design_brief_schema, validate_design_brief
from .generator import validate_generation_document
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


@dataclass(frozen=True)
class SessionIfcResult:
    session_id: str
    session_hash: str
    status: str
    generator_status: str
    repair_route: str
    audit_status: str
    ifc_path: str | None
    report_path: str | None


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
            "response_format": {"type": "json_object"},
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
            _write_design_brief_trace(
                call_dir=call_dir,
                transcript=transcript,
                selection=selection,
                renderer_inputs=renderer_inputs,
                rendered_text=rendered["text"],
                request=evidence["request"],
                response=payload,
                model_text=str(evidence["content_text"]),
                parsed=parsed,
                validation={
                    "valid": False,
                    "issue_count": len(diagnostics),
                    "issues": diagnostics,
                },
                metrics={
                    "response_id": evidence["response_id"],
                    "model": evidence["model"],
                    "finish_reason": evidence["finish_reason"],
                    "usage": evidence["usage"],
                    "prompt_template_id": rendered["metadata"]["template_id"],
                    "prompt_template_hash": rendered["metadata"]["template_hash"],
                    "parse_valid": True,
                    "schema_semantic_valid": False,
                    "strict_output_contract_valid": False,
                    "design_status": parsed.get("status"),
                    "question_count": len(parsed.get("clarification_questions", [])),
                },
            )
            raise OpenAICompatError(
                "OpenAI-compatible Design Brief violated strict JSON output contract",
                evidence={"parse_status": parse_status, "diagnostics": diagnostics},
            )
        issues = validate_design_brief(
            parsed,
            evidence_catalog=selection["evidence"],
        )
        serialized_issues = [
            {
                "code": issue.code,
                "path": issue.path,
                "message": issue.message,
            }
            for issue in issues
        ]
        metrics = {
            "response_id": evidence["response_id"],
            "model": evidence["model"],
            "finish_reason": evidence["finish_reason"],
            "usage": evidence["usage"],
            "prompt_template_id": rendered["metadata"]["template_id"],
            "prompt_template_hash": rendered["metadata"]["template_hash"],
            "parse_valid": True,
            "schema_semantic_valid": not issues,
            "strict_output_contract_valid": True,
            "design_status": parsed.get("status"),
            "question_count": len(parsed.get("clarification_questions", [])),
        }
        _write_design_brief_trace(
            call_dir=call_dir,
            transcript=transcript,
            selection=selection,
            renderer_inputs=renderer_inputs,
            rendered_text=rendered["text"],
            request=evidence["request"],
            response=payload,
            model_text=str(evidence["content_text"]),
            parsed=parsed,
            validation={
                "valid": not issues,
                "issue_count": len(serialized_issues),
                "issues": serialized_issues,
            },
            metrics=metrics,
        )
        if issues:
            raise OpenAICompatError(
                "OpenAI-compatible Design Brief failed schema validation",
                evidence={"issues": serialized_issues},
            )

        _write_json(call_dir / "design-brief.json", parsed)
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


def _write_design_brief_trace(
    *,
    call_dir: Path,
    transcript: list[dict[str, Any]],
    selection: dict[str, Any],
    renderer_inputs: dict[str, Any],
    rendered_text: str,
    request: dict[str, Any],
    response: dict[str, Any],
    model_text: str,
    parsed: dict[str, Any],
    validation: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    _write_json(call_dir / "conversation.json", transcript)
    _write_json(call_dir / "context-selection.json", selection)
    _write_json(call_dir / "prompt-render-input.json", renderer_inputs)
    (call_dir / "prompt-rendered.md").write_text(rendered_text, encoding="utf-8")
    _write_json(call_dir / "request.redacted.json", request)
    _write_json(call_dir / "response.raw.json", response)
    (call_dir / "model-text.txt").write_text(model_text, encoding="utf-8")
    _write_json(call_dir / "parsed-output.json", parsed)
    _write_json(call_dir / "validation.json", validation)
    _write_json(call_dir / "metrics.json", metrics)


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


def run_ready_session_to_ifc(
    *,
    store: SessionStore,
    session: str,
    provider_factory: Callable[[], Any],
) -> SessionIfcResult:
    """Generate BIM JSON, run deterministic gates, and compile a ready session."""

    stored_session = store.get_session(session)
    if stored_session.status != "ready":
        raise ValueError("Phase 6.2 IFC generation requires a ready session")

    design_dir = _prepare_design_source(stored_session)
    generator = run_generator_stage(
        provider=provider_factory(),
        output_dir=stored_session.run_dir / "generator",
        design_source_dir=design_dir,
        case_id=stored_session.session_hash,
        session_prefix="phase6.2",
    )
    _record_stage_payloads(store, stored_session.session_id, "generator", generator)
    if generator["classification"] == "formal" and (
        stored_session.run_dir / "generator" / "candidate.json"
    ).is_file():
        _copy_artifact_to_run_root(
            store,
            stored_session,
            kind="candidate",
            source=stored_session.run_dir / "generator" / "candidate.json",
            target_name="candidate.json",
        )
        if (stored_session.run_dir / "generator" / "semantic-capabilities.json").is_file():
            _copy_artifact_to_run_root(
                store,
                stored_session,
                kind="semantic_capabilities",
                source=stored_session.run_dir / "generator" / "semantic-capabilities.json",
                target_name="semantic-capabilities.json",
            )

    semantic_coverage: dict[str, Any] | None = None
    if generator["classification"] == "formal" and generator["valid"]:
        semantic_coverage = run_semantic_coverage_stage(
            case_dir=stored_session.run_dir,
            output_dir=stored_session.run_dir,
            case_id=stored_session.session_hash,
        )
        _record_stage_payloads(
            store,
            stored_session.session_id,
            "semantic_coverage",
            semantic_coverage,
        )
        _record_existing_artifact(
            store,
            stored_session,
            kind="semantic_coverage",
            name="semantic-coverage.json",
        )

    repair = run_repair_stage(
        provider_factory=provider_factory,
        output_dir=stored_session.run_dir / "repair",
        generator_source_dir=stored_session.run_dir / "generator",
        case_id=stored_session.session_hash,
    )
    _record_stage_payloads(store, stored_session.session_id, "repair", repair)

    if (
        not generator["valid"]
        or (semantic_coverage is not None and not semantic_coverage["valid"])
        or repair["route"] not in {
            "no_repair_needed",
            "repair_attempted",
        }
    ):
        store.mark_session_status(stored_session.session_id, "draft_or_blocked")
        store.export_session(stored_session.session_id)
        return SessionIfcResult(
            session_id=stored_session.session_id,
            session_hash=stored_session.session_hash,
            status="draft_or_blocked",
            generator_status=str(generator["status"]),
            repair_route=str(repair["route"]),
            audit_status="not_run",
            ifc_path=None,
            report_path=None,
        )

    candidate_gates = run_candidate_gate_stage(
        case_dir=stored_session.run_dir,
        output_dir=stored_session.run_dir,
        case_id=stored_session.session_hash,
    )
    _record_stage_payloads(
        store,
        stored_session.session_id,
        "candidate_gates",
        candidate_gates,
    )

    audit = run_audit_report_stage(
        provider=provider_factory(),
        case_dir=stored_session.run_dir,
        case_id=stored_session.session_hash,
        session_prefix="phase6.2",
    )
    _record_stage_payloads(store, stored_session.session_id, "audit", audit)
    if not audit["valid"] or audit["status"] != "accepted":
        repair_attempt = _attempt_geometry_repair_after_audit(
            store=store,
            stored_session=stored_session,
            provider_factory=provider_factory,
            repair_attempt_count=len(repair.get("repair_attempts", [])),
        )
        if repair_attempt is not None:
            repair = repair_attempt["repair"]
            candidate_gates = repair_attempt["candidate_gates"]
            audit = repair_attempt["audit"]
    if not audit["valid"] or audit["status"] != "accepted":
        store.mark_session_status(stored_session.session_id, "audit_blocked")
        if (stored_session.run_dir / "output.ifc").is_file():
            _record_existing_artifact(store, stored_session, kind="ifc", name="output.ifc")
        if (stored_session.run_dir / "report.md").is_file():
            _record_existing_artifact(store, stored_session, kind="report", name="report.md")
        store.export_session(stored_session.session_id)
        return SessionIfcResult(
            session_id=stored_session.session_id,
            session_hash=stored_session.session_hash,
            status="audit_blocked",
            generator_status=str(generator["status"]),
            repair_route=str(repair["route"]),
            audit_status=str(audit["status"]),
            ifc_path=(
                str(stored_session.run_dir / "output.ifc")
                if (stored_session.run_dir / "output.ifc").is_file()
                else None
            ),
            report_path=(
                str(stored_session.run_dir / "report.md")
                if (stored_session.run_dir / "report.md").is_file()
                else str(audit.get("report_path")) if audit.get("report_path") else None
            ),
        )

    final = run_final_acceptance_stage(
        case_dir=stored_session.run_dir,
        output_dir=stored_session.run_dir,
        case_id=stored_session.session_hash,
    )
    _record_stage_payloads(store, stored_session.session_id, "final_acceptance", final)
    if final["valid"]:
        store.mark_session_status(stored_session.session_id, "compiled")
        _record_existing_artifact(store, stored_session, kind="ifc", name="output.ifc")
        _record_existing_artifact(store, stored_session, kind="report", name="report.md")
    else:
        store.mark_session_status(stored_session.session_id, "final_blocked")
        if (stored_session.run_dir / "output.ifc").is_file():
            _record_existing_artifact(store, stored_session, kind="ifc", name="output.ifc")
        if (stored_session.run_dir / "report.md").is_file():
            _record_existing_artifact(store, stored_session, kind="report", name="report.md")
    export_path = store.export_session(stored_session.session_id)
    if final["valid"]:
        _write_phase6_2_session_report(
            store=store,
            session=stored_session,
            export_path=export_path,
            final=final,
        )
        _write_final_acceptance_index(store, stored_session, export_path)
    return SessionIfcResult(
        session_id=stored_session.session_id,
        session_hash=stored_session.session_hash,
        status="compiled" if final["valid"] else "final_blocked",
        generator_status=str(generator["status"]),
        repair_route=str(repair["route"]),
        audit_status=str(audit["status"]),
        ifc_path=(
            str(stored_session.run_dir / "output.ifc")
            if (stored_session.run_dir / "output.ifc").is_file()
            else None
        ),
        report_path=(
            str(stored_session.run_dir / "report.md")
            if (stored_session.run_dir / "report.md").is_file()
            else None
        ),
    )


def _attempt_geometry_repair_after_audit(
    *,
    store: SessionStore,
    stored_session: Any,
    provider_factory: Callable[[], Any],
    repair_attempt_count: int,
) -> dict[str, Any] | None:
    run_dir = stored_session.run_dir
    audit_report_path = run_dir / "audit" / "audit-report.json"
    geometry_feedback_path = run_dir / "geometry-feedback.json"
    if not audit_report_path.is_file() or not geometry_feedback_path.is_file():
        return None
    audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
    if audit_report.get("recommendation") != "revise" or audit_report.get("blocking") is not True:
        return None
    geometry_feedback = json.loads(geometry_feedback_path.read_text(encoding="utf-8"))
    if geometry_feedback.get("success") is not False or not geometry_feedback.get("issues"):
        return None

    repair = run_repair_stage(
        provider_factory=provider_factory,
        output_dir=run_dir / "repair",
        generator_source_dir=run_dir / "generator",
        case_id=stored_session.session_hash,
        geometry_feedback=list(geometry_feedback.get("issues", [])),
        prior_attempt_count=repair_attempt_count,
    )
    _record_stage_payloads(store, stored_session.session_id, "repair", repair)
    repaired_candidate = run_dir / "repair" / "repaired-candidate.json"
    if repair["route"] != "repair_attempted" or not repaired_candidate.is_file():
        return {"repair": repair, "candidate_gates": None, "audit": {"valid": False, "status": "blocked"}}

    _promote_repaired_candidate(run_dir, repaired_candidate)
    candidate_gates = run_candidate_gate_stage(
        case_dir=run_dir,
        output_dir=run_dir,
        case_id=stored_session.session_hash,
    )
    _record_stage_payloads(
        store,
        stored_session.session_id,
        "candidate_gates",
        candidate_gates,
    )
    audit = run_audit_report_stage(
        provider=provider_factory(),
        case_dir=run_dir,
        case_id=stored_session.session_hash,
        session_prefix="phase6.2",
        audit_call_index=2,
    )
    _record_stage_payloads(store, stored_session.session_id, "audit", audit)
    return {"repair": repair, "candidate_gates": candidate_gates, "audit": audit}


def _promote_repaired_candidate(run_dir: Path, repaired_candidate: Path) -> None:
    generator_dir = run_dir / "generator"
    candidate = json.loads(repaired_candidate.read_text(encoding="utf-8"))
    contract = validate_generation_document(candidate)
    shutil.copyfile(repaired_candidate, generator_dir / "candidate.json")
    shutil.copyfile(repaired_candidate, run_dir / "candidate.json")
    _write_json(
        generator_dir / "validation.json",
        {
            "valid": contract["status"] == "formal",
            "issue_count": len(contract["diagnostics"]),
            "issues": contract["diagnostics"],
        },
    )
    metrics_path = generator_dir / "metrics.json"
    metrics = (
        json.loads(metrics_path.read_text(encoding="utf-8"))
        if metrics_path.is_file()
        else {}
    )
    metrics.update(
        {
            "contract_status": contract["status"],
            "classification": contract["classification"],
            "contract_valid": contract["status"] == "formal",
            "issue_count": len(contract["diagnostics"]),
            "repaired_candidate_promoted": True,
        }
    )
    _write_json(metrics_path, metrics)


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


def _prepare_design_source(session: Any) -> Path:
    design_dir = session.run_dir / "design-brief"
    design_dir.mkdir(parents=True, exist_ok=True)
    final_call_dir = _latest_design_brief_call_dir(session.run_dir)
    for source in final_call_dir.iterdir():
        if source.is_file():
            shutil.copyfile(source, design_dir / source.name)
    for name in ("conversation.json", "context-selection.json", "design-brief.json"):
        if not (design_dir / name).is_file():
            raise ValueError(
                f"ready session is missing Design Brief artifact: {design_dir / name}"
            )
    (design_dir / "input.txt").write_text(session.original_input + "\n", encoding="utf-8")
    if not (design_dir / "validation.json").is_file():
        brief = json.loads((design_dir / "design-brief.json").read_text(encoding="utf-8"))
        issues = validate_design_brief(brief)
        _write_json(
            design_dir / "validation.json",
            {
                "valid": not issues,
                "issue_count": len(issues),
                "issues": [
                    {
                        "code": issue.code,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in issues
                ],
            },
        )
    return design_dir


def _latest_design_brief_call_dir(run_dir: Path) -> Path:
    calls = sorted((run_dir / "calls").glob("*-design-brief"))
    for call_dir in reversed(calls):
        if (call_dir / "design-brief.json").is_file():
            return call_dir
    if (run_dir / "design-brief.json").is_file():
        return run_dir
    raise ValueError("ready session has no Design Brief call artifacts")


def _record_stage_payloads(
    store: SessionStore,
    session_id: str,
    stage: str,
    payload: dict[str, Any],
) -> None:
    store.record_payload(session_id, table="metrics", payload={"stage": stage, **payload})
    store.append_event(session_id, event_type=f"{stage}_completed", payload=payload)


def _copy_artifact_to_run_root(
    store: SessionStore,
    session: Any,
    *,
    kind: str,
    source: Path,
    target_name: str,
) -> None:
    target = session.run_dir / target_name
    shutil.copyfile(source, target)
    _record_existing_artifact(store, session, kind=kind, name=target_name)


def _record_existing_artifact(
    store: SessionStore,
    session: Any,
    *,
    kind: str,
    name: str,
) -> None:
    if (session.run_dir / name).is_file():
        store.record_artifact(
            session.session_id,
            kind=kind,
            path=Path("runs") / session.session_hash / name,
        )


def _write_final_acceptance_index(
    store: SessionStore,
    session: Any,
    export_path: Path,
) -> None:
    payload = {
        "schema_version": "text2ifc/phase6.2-final-acceptance-v1",
        "session_id": session.session_id,
        "session_hash": session.session_hash,
        "status": "compiled",
        "artifacts": {
            "ifc": f"runs/{session.session_hash}/output.ifc",
            "report": f"runs/{session.session_hash}/report.md",
            "session_export": f"runs/{session.session_hash}/{export_path.name}",
        },
    }
    _write_json(store.artifact_root / "final-acceptance.json", payload)


def _write_phase6_2_session_report(
    *,
    store: SessionStore,
    session: Any,
    export_path: Path,
    final: dict[str, Any],
) -> None:
    export = store.session_export_payload(session.session_id)
    turns = export.get("turns", [])
    events = export.get("events", [])
    artifacts = export.get("artifacts", [])
    relative_export = Path("runs") / session.session_hash / export_path.name
    lines = [
        "# Phase 6.2 Interactive CLI Run Report",
        "",
        "Generated from SQLite session records and linked trace artifacts.",
        "",
        "## Original Input",
        "",
        "```text",
        session.original_input,
        "```",
        "",
        "## Transcript",
        "",
        _json_block(turns),
        "",
        "## Design Brief Agent",
        "",
        *_report_links(
            session.run_dir,
            (
                "design-brief/input.txt",
                "design-brief/conversation.json",
                "design-brief/prompt-rendered.md",
                "design-brief/request.redacted.json",
                "design-brief/response.raw.json",
                "design-brief/model-text.txt",
                "design-brief/design-brief.json",
                "design-brief/validation.json",
                "design-brief/metrics.json",
            ),
        ),
        "",
        "## BIM JSON Generator",
        "",
        *_report_links(
            session.run_dir,
            (
                "generator/prompt-rendered.md",
                "generator/request.redacted.json",
                "generator/response.raw.json",
                "generator/model-text.txt",
                "generator/candidate.json",
                "generator/validation.json",
                "generator/metrics.json",
            ),
        ),
        "",
        "## Repair Route",
        "",
        *_report_links(
            session.run_dir,
            (
                "repair/route.json",
                "repair/repair-attempts.json",
                "repair/source-validation.json",
                "repair/metrics.json",
            ),
        ),
        "",
        "## Audit Agent",
        "",
        *_report_links(
            session.run_dir,
            (
                "audit/prompt-rendered.md",
                "audit/request.redacted.json",
                "audit/response.raw.json",
                "audit/model-text.txt",
                "audit/audit-report.json",
                "audit/validation.json",
                "audit/metrics.json",
            ),
        ),
        "",
        "## Semantic Coverage",
        "",
        *_report_links(
            session.run_dir,
            (
                "semantic-capabilities.json",
                "semantic-coverage.json",
                "semantic-geometry-expectation.json",
            ),
        ),
        "",
        "## Deterministic Gates",
        "",
        *_report_links(
            session.run_dir,
            (
                "acceptance-metrics.json",
                "ifc-verification.json",
                "geometry-feedback.json",
                "secret-scan.json",
            ),
        ),
        "",
        "```json",
        json.dumps(final, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Final Artifacts",
        "",
        *_report_links(
            session.run_dir,
            (
                "output.ifc",
                "candidate.json",
                "report.md",
            ),
        ),
        "",
        "## Session Export",
        "",
        f"- [{relative_export.as_posix()}]({relative_export.as_posix()})",
        "",
        "## Session DB Evidence",
        "",
        "### Events",
        "",
        _json_block(events),
        "",
        "### Artifact Index",
        "",
        _json_block(artifacts),
        "",
    ]
    (session.run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _report_links(root: Path, relatives: tuple[str, ...]) -> list[str]:
    lines = []
    for relative in relatives:
        if (root / relative).is_file():
            lines.append(f"- [{relative}]({relative})")
    return lines


def _json_block(payload: Any) -> str:
    return "```json\n" + json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n```"


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
