"""DB-backed Phase 6.2 interactive Agent flows."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .live_pipeline import (
    run_audit_report_stage,
    run_candidate_gate_stage,
    run_final_acceptance_stage,
    run_generator_stage,
    run_repair_stage,
    run_semantic_coverage_stage,
)
from .clarification import ClarificationCall, ClarificationController, DesignBriefInvoker
from .complex_scaffold import build_scaffold_candidate
from .context_selection import select_design_brief_context
from .design_brief import load_design_brief_schema, validate_design_brief
from .expected_facts import write_expected_facts
from .gate_audit_bundle import write_gate_summary
from .generator import validate_generation_document
from .feedback_loop import write_feedback_artifacts
from .issue_normalizers import (
    normalize_generator_draft_issues,
    normalize_audit_findings,
    normalize_gate_sidecars,
    normalize_provider_failure,
    normalize_validation_issues,
    write_terminal_issues,
)
from .issues import write_issues
from .openai_compat import (
    OpenAICompatError,
    OpenAICompatRuntimeConfig,
    parse_chat_completion_evidence,
    token_limit_request,
)
from .prompt_registry import render_prompt
from .providers import ProviderOutput, ProviderOutputError
from .run_report import build_live_run_report
from .session_store import SessionStore
from .state import redact_metadata


DESIGN_BRIEF_TEMPLATE_ID = "design-brief.v2.1"
SCAFFOLD_ELIGIBLE_DYNAMIC_ISSUES = {
    "EXPECTED_ENTITY_MISSING",
    "OPENING_FILL_RELATIONSHIP_MISSING",
    "STOREY_CONTAINMENT_MISMATCH",
    "VOID_RELATIONSHIP_MISSING",
}
SCAFFOLD_ELIGIBLE_GEOMETRY_ISSUES = {
    "ROOM_ENCLOSURE_OPEN",
    "WALL_BBOX_MISMATCH",
    "WALL_ORIENTATION_MISMATCH",
}


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


def _emit_progress(
    progress: Callable[[str, dict[str, Any]], None] | None,
    stage: str,
    payload: dict[str, Any],
) -> None:
    if progress is not None:
        progress(stage, payload)


def _gate_progress_status(candidate_gates: Mapping[str, Any]) -> str:
    return "passed" if candidate_gates.get("valid") is True else "failed"


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
            "response_format": {"type": "json_object"},
        }
        request.update(token_limit_request(config))
        response = client.chat.completions.create(**request)
        payload = _object_to_dict(response)
        evidence = parse_chat_completion_evidence(
            payload,
            request=request,
            evidence_class="live",
            provider_label=config.provider_label,
        )
        provider_output = ProviderOutput(
            text=str(evidence["content_text"]),
            metadata={
                "provider": config.provider_label,
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


def _geometry_failure_requires_regeneration(
    run_dir: Path,
    audit_report: Mapping[str, Any],
) -> bool:
    gate_summary_path = run_dir / "gate-summary.json"
    if gate_summary_path.is_file():
        gate_summary = json.loads(gate_summary_path.read_text(encoding="utf-8"))
        if (
            isinstance(gate_summary, Mapping)
            and gate_summary.get("overall_status") == "failed"
        ):
            return True
    geometry_feedback_path = run_dir / "geometry-feedback.json"
    if geometry_feedback_path.is_file():
        geometry_feedback = json.loads(geometry_feedback_path.read_text(encoding="utf-8"))
        if (
            isinstance(geometry_feedback, Mapping)
            and geometry_feedback.get("success") is False
            and isinstance(geometry_feedback.get("issues"), list)
            and geometry_feedback["issues"]
        ):
            return True
    return (
        audit_report.get("recommendation") == "revise"
        and audit_report.get("blocking") is True
    )


def run_ready_session_to_ifc(
    *,
    store: SessionStore,
    session: str,
    provider_factory: Callable[[], Any],
    trace_level: str | None = "debug",
    progress: Callable[[str, dict[str, Any]], None] | None = None,
) -> SessionIfcResult:
    """Generate BIM JSON, run deterministic gates, and compile a ready session."""

    stored_session = store.get_session(session)
    if stored_session.status != "ready":
        raise ValueError("Phase 6.2 IFC generation requires a ready session")

    design_dir = _prepare_design_source(stored_session)
    design_brief = json.loads((design_dir / "design-brief.json").read_text(encoding="utf-8"))
    write_expected_facts(
        case_dir=stored_session.run_dir,
        case_id=stored_session.session_hash,
        design_brief=design_brief,
    )
    _record_existing_artifact(
        store,
        stored_session,
        kind="expected_facts",
        name="expected-facts.json",
    )
    try:
        _emit_progress(progress, "generator", {"status": "started"})
        generator = run_generator_stage(
            provider=provider_factory(),
            output_dir=stored_session.run_dir / "generator",
            design_source_dir=design_dir,
            case_id=stored_session.session_hash,
            session_prefix="phase6.2",
            trace_level=trace_level,
        )
    except ProviderOutputError as exc:
        error_payload = _record_provider_failure(
            store=store,
            stored_session=stored_session,
            stage="generator",
            exc=exc,
        )
        _write_provider_failure_issues(
            store=store,
            stored_session=stored_session,
            stage="generator",
            error_payload=error_payload,
        )
        return SessionIfcResult(
            session_id=stored_session.session_id,
            session_hash=stored_session.session_hash,
            status="provider_failed",
            generator_status=str(error_payload["status"]),
            repair_route="not_run",
            audit_status="not_run",
            ifc_path=None,
            report_path=None,
        )
    _record_stage_payloads(store, stored_session.session_id, "generator", generator)
    _emit_progress(
        progress,
        "generator",
        {"status": generator.get("status"), "response_id": generator.get("response_id")},
    )
    if generator["classification"] == "formal" and (
        stored_session.run_dir / "generator" / "candidate.json"
    ).is_file():
        _write_candidate_origin(
            stored_session.run_dir,
            candidate_origin="live_model_generator",
            live_acceptance_eligible=True,
        )
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

    generator_scaffold = _maybe_promote_scaffold_from_generator_failure(
        store=store,
        stored_session=stored_session,
        design_brief=design_brief,
        generator=generator,
    )
    if generator_scaffold is not None and generator_scaffold.get("valid") is True:
        _record_stage_payloads(
            store,
            stored_session.session_id,
            "scaffold",
            generator_scaffold,
        )
        _emit_progress(progress, "scaffold", {"status": generator_scaffold.get("route") or "promoted"})
        generator = {
            **generator,
            "status": "scaffold_promoted",
            "classification": "formal",
            "valid": True,
            "contract_valid": True,
            "strict_output_contract_valid": True,
        }

    semantic_coverage: dict[str, Any] | None = None
    if generator["classification"] == "formal" and generator["valid"]:
        _emit_progress(progress, "semantic_coverage", {"status": "started"})
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
        _emit_progress(progress, "semantic_coverage", {"status": semantic_coverage.get("status") or semantic_coverage.get("valid")})
        _record_existing_artifact(
            store,
            stored_session,
            kind="semantic_coverage",
            name="semantic-coverage.json",
        )

    _emit_progress(progress, "repair", {"status": "started"})
    repair = run_repair_stage(
        provider_factory=provider_factory,
        output_dir=stored_session.run_dir / "repair",
        generator_source_dir=stored_session.run_dir / "generator",
        case_id=stored_session.session_hash,
        trace_level=trace_level,
    )
    _record_stage_payloads(store, stored_session.session_id, "repair", repair)
    _emit_progress(progress, "repair", {"route": repair.get("route")})
    repaired_candidate = stored_session.run_dir / "repair" / "repaired-candidate.json"
    if repair["route"] == "repair_attempted" and repaired_candidate.is_file():
        _promote_repaired_candidate(stored_session.run_dir, repaired_candidate)
        promoted_validation = json.loads(
            (stored_session.run_dir / "generator" / "validation.json").read_text(
                encoding="utf-8"
            )
        )
        generator = {
            **generator,
            "status": "repaired",
            "classification": "formal",
            "valid": bool(promoted_validation["valid"]),
            "contract_valid": bool(promoted_validation["valid"]),
            "strict_output_contract_valid": bool(promoted_validation["valid"]),
        }
        _record_existing_artifact(
            store,
            stored_session,
            kind="candidate",
            name="candidate.json",
        )
        if generator["valid"]:
            _emit_progress(progress, "semantic_coverage", {"status": "started"})
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
            _emit_progress(progress, "semantic_coverage", {"status": semantic_coverage.get("status") or semantic_coverage.get("valid")})
            _record_existing_artifact(
                store,
                stored_session,
                kind="semantic_coverage",
                name="semantic-coverage.json",
            )

    if (
        generator["classification"] != "formal"
        or
        not generator["valid"]
        or (semantic_coverage is not None and not semantic_coverage["valid"])
        or repair["route"] not in {
            "no_repair_needed",
            "repair_attempted",
        }
    ):
        store.mark_session_status(stored_session.session_id, "draft_or_blocked")
        _write_terminal_non_accept_issues(store=store, stored_session=stored_session)
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

    _emit_progress(progress, "candidate_gates", {"status": "started"})
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
    _emit_progress(progress, "candidate_gates", {"status": _gate_progress_status(candidate_gates)})
    scaffold = _maybe_promote_scaffold_candidate(
        store=store,
        stored_session=stored_session,
        design_brief=design_brief,
    )
    if scaffold is not None:
        _record_stage_payloads(store, stored_session.session_id, "scaffold", scaffold)
        _emit_progress(progress, "scaffold", {"status": scaffold.get("route") or "promoted"})
        _emit_progress(progress, "semantic_coverage", {"status": "started"})
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
        _emit_progress(progress, "semantic_coverage", {"status": semantic_coverage.get("status") or semantic_coverage.get("valid")})
        _emit_progress(progress, "candidate_gates", {"status": "started"})
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
        _emit_progress(progress, "candidate_gates", {"status": _gate_progress_status(candidate_gates)})

    _emit_progress(progress, "audit", {"status": "started"})
    audit = run_audit_report_stage(
        provider=provider_factory(),
        case_dir=stored_session.run_dir,
        case_id=stored_session.session_hash,
        session_prefix="phase6.2",
        trace_level=trace_level,
    )
    _record_stage_payloads(store, stored_session.session_id, "audit", audit)
    _emit_progress(progress, "audit", {"status": audit.get("status"), "response_id": audit.get("response_id")})
    _archive_round_evidence(stored_session.run_dir, 1)
    if not audit["valid"] or audit["status"] != "accepted":
        geometry_scaffold = _maybe_promote_scaffold_after_geometry_audit(
            store=store,
            stored_session=stored_session,
            design_brief=design_brief,
        )
        if geometry_scaffold is not None and geometry_scaffold.get("valid") is True:
            _record_stage_payloads(
                store,
                stored_session.session_id,
                "scaffold",
                geometry_scaffold,
            )
            _emit_progress(progress, "scaffold", {"status": geometry_scaffold.get("route") or "promoted"})
            generator = {
                **generator,
                "status": "scaffold_promoted",
                "classification": "formal",
                "valid": True,
                "contract_valid": True,
                "strict_output_contract_valid": True,
            }
            _emit_progress(progress, "semantic_coverage", {"status": "started"})
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
            _emit_progress(progress, "semantic_coverage", {"status": semantic_coverage.get("status") or semantic_coverage.get("valid")})
            _emit_progress(progress, "candidate_gates", {"status": "started"})
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
            _emit_progress(progress, "candidate_gates", {"status": _gate_progress_status(candidate_gates)})
            _emit_progress(progress, "audit", {"status": "started"})
            audit = run_audit_report_stage(
                provider=provider_factory(),
                case_dir=stored_session.run_dir,
                case_id=stored_session.session_hash,
                session_prefix="phase6.2",
                audit_call_index=2,
                trace_level=trace_level,
            )
            _record_stage_payloads(store, stored_session.session_id, "audit", audit)
            _emit_progress(progress, "audit", {"status": audit.get("status"), "response_id": audit.get("response_id")})
    regeneration_attempted = False
    previous_issue_count: int | None = None
    for feedback_round_index in range(2):
        if (
            candidate_gates.get("valid") is True
            and audit["valid"]
            and audit["status"] == "accepted"
        ):
            break
        regeneration_attempt = _attempt_generator_regeneration_after_audit(
            store=store,
            stored_session=stored_session,
            provider_factory=provider_factory,
            design_dir=design_dir,
            trace_level=trace_level,
            progress=progress,
            feedback_round_index=feedback_round_index,
            previous_issue_count=previous_issue_count,
        )
        if regeneration_attempt is None:
            break
        regeneration_attempted = True
        generator = regeneration_attempt["generator"]
        semantic_coverage = regeneration_attempt["semantic_coverage"]
        candidate_gates = regeneration_attempt["candidate_gates"]
        audit = regeneration_attempt["audit"]
        previous_issue_count = regeneration_attempt["issue_count"]
        build_live_run_report(case_dir=stored_session.run_dir)
    if (
        (not audit["valid"] or audit["status"] != "accepted")
        and not regeneration_attempted
    ):
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
            build_live_run_report(case_dir=stored_session.run_dir)
    if (
        candidate_gates.get("valid") is not True
        or not audit["valid"]
        or audit["status"] != "accepted"
    ):
        store.mark_session_status(stored_session.session_id, "audit_blocked")
        _write_terminal_non_accept_issues(store=store, stored_session=stored_session)
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

    _emit_progress(progress, "final_acceptance", {"status": "started"})
    final = run_final_acceptance_stage(
        case_dir=stored_session.run_dir,
        output_dir=stored_session.run_dir,
        case_id=stored_session.session_hash,
    )
    _record_stage_payloads(store, stored_session.session_id, "final_acceptance", final)
    _emit_progress(progress, "final_acceptance", {"status": final.get("status") or final.get("valid")})
    if final["valid"]:
        store.mark_session_status(stored_session.session_id, "compiled")
        _write_phase6_4_accept_artifacts(store=store, stored_session=stored_session)
        _record_existing_artifact(store, stored_session, kind="ifc", name="output.ifc")
        _record_existing_artifact(store, stored_session, kind="report", name="report.md")
    else:
        store.mark_session_status(stored_session.session_id, "final_blocked")
        _write_terminal_non_accept_issues(store=store, stored_session=stored_session)
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
        _write_phase6_4_case_result(
            store=store,
            stored_session=stored_session,
            final_status="accepted",
            output_type="ifc",
            route="accepted",
            failure_owner=None,
            blocking_issue_count=0,
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


def _maybe_promote_scaffold_candidate(
    *,
    store: SessionStore,
    stored_session: Any,
    design_brief: dict[str, Any],
) -> dict[str, Any] | None:
    run_dir = stored_session.run_dir
    generator_candidate = run_dir / "generator" / "candidate.json"
    expected_facts_path = run_dir / "expected-facts.json"
    if not generator_candidate.is_file() or not expected_facts_path.is_file():
        return None

    gate_summary = write_gate_summary(
        case_dir=run_dir,
        case_id=stored_session.session_hash,
    )
    if gate_summary.get("overall_status") == "passed":
        return None

    source_issue_codes = _dynamic_gate_issue_codes(gate_summary)
    if not source_issue_codes or not source_issue_codes <= SCAFFOLD_ELIGIBLE_DYNAMIC_ISSUES:
        return None

    scaffold_dir = run_dir / "scaffold"
    scaffold_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(run_dir / "gate-summary.json", scaffold_dir / "source-gate-summary.json")
    return _build_and_promote_scaffold_candidate(
        store=store,
        stored_session=stored_session,
        design_brief=design_brief,
        route_name="scaffold_promoted",
        source_issue_codes=source_issue_codes,
        source_gate_summary="source-gate-summary.json",
    )


def _maybe_promote_scaffold_after_geometry_audit(
    *,
    store: SessionStore,
    stored_session: Any,
    design_brief: dict[str, Any],
) -> dict[str, Any] | None:
    run_dir = stored_session.run_dir
    audit_report_path = run_dir / "audit" / "audit-report.json"
    geometry_feedback_path = run_dir / "geometry-feedback.json"
    expected_facts_path = run_dir / "expected-facts.json"
    generator_candidate = run_dir / "generator" / "candidate.json"
    if (
        not audit_report_path.is_file()
        or not geometry_feedback_path.is_file()
        or not expected_facts_path.is_file()
        or not generator_candidate.is_file()
    ):
        return None

    audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
    if audit_report.get("recommendation") != "revise" or audit_report.get("blocking") is not True:
        return None

    geometry_feedback = json.loads(geometry_feedback_path.read_text(encoding="utf-8"))
    if geometry_feedback.get("success") is not False:
        return None
    source_issue_codes = {
        str(issue.get("code"))
        for issue in geometry_feedback.get("issues", [])
        if isinstance(issue, dict) and issue.get("code")
    }
    if not source_issue_codes or not source_issue_codes <= SCAFFOLD_ELIGIBLE_GEOMETRY_ISSUES:
        return None

    scaffold_dir = run_dir / "scaffold"
    scaffold_dir.mkdir(parents=True, exist_ok=True)
    gate_summary = run_dir / "gate-summary.json"
    source_gate_summary = None
    if gate_summary.is_file():
        source_gate_summary = "source-gate-summary-before-geometry-scaffold.json"
        shutil.copyfile(gate_summary, scaffold_dir / source_gate_summary)
    return _build_and_promote_scaffold_candidate(
        store=store,
        stored_session=stored_session,
        design_brief=design_brief,
        route_name="scaffold_promoted_from_geometry_audit",
        source_issue_codes=source_issue_codes,
        source_gate_summary=source_gate_summary,
    )


def _maybe_promote_scaffold_from_generator_failure(
    *,
    store: SessionStore,
    stored_session: Any,
    design_brief: dict[str, Any],
    generator: dict[str, Any],
) -> dict[str, Any] | None:
    run_dir = stored_session.run_dir
    if generator.get("valid") is True and generator.get("classification") == "formal":
        return None
    if (run_dir / "generator" / "candidate.json").is_file():
        return None
    expected_facts_path = run_dir / "expected-facts.json"
    if not expected_facts_path.is_file():
        return None
    classification = run_dir / "generator" / "classification.json"
    validation = run_dir / "generator" / "validation.json"
    if classification.is_file():
        shutil.copyfile(
            classification,
            run_dir / "generator" / "original-classification-before-scaffold.json",
        )
    if validation.is_file():
        shutil.copyfile(
            validation,
            run_dir / "generator" / "original-validation-before-scaffold.json",
        )
    source_issue_codes = {
        str(issue.get("code"))
        for issue in _read_json_issues(classification)
        if issue.get("code")
    }
    return _build_and_promote_scaffold_candidate(
        store=store,
        stored_session=stored_session,
        design_brief=design_brief,
        route_name="scaffold_promoted_from_generator_failure",
        source_issue_codes=source_issue_codes or {"GENERATOR_OUTPUT_CONTRACT_FAILED"},
        source_gate_summary=None,
    )


def _build_and_promote_scaffold_candidate(
    *,
    store: SessionStore,
    stored_session: Any,
    design_brief: dict[str, Any],
    route_name: str,
    source_issue_codes: set[str],
    source_gate_summary: str | None,
) -> dict[str, Any]:
    run_dir = stored_session.run_dir
    scaffold_dir = run_dir / "scaffold"
    scaffold_dir.mkdir(parents=True, exist_ok=True)
    expected_facts_path = run_dir / "expected-facts.json"
    expected_facts = json.loads(expected_facts_path.read_text(encoding="utf-8"))
    try:
        candidate = build_scaffold_candidate(
            case_id=stored_session.session_hash,
            design_brief=design_brief,
            expected_facts=expected_facts,
        )
    except ValueError as exc:
        route = {
            "schema_version": "text2ifc/scaffold-route/1.0",
            "route": "scaffold_blocked",
            "valid": False,
            "blocking_reason": str(exc),
            "source_issue_codes": sorted(source_issue_codes),
        }
        _write_json(scaffold_dir / "route.json", route)
        return route

    contract = validate_generation_document(candidate)
    diagnostics = list(contract["diagnostics"])
    _write_json(scaffold_dir / "candidate.json", candidate)
    _write_json(
        scaffold_dir / "validation.json",
        {
            "valid": contract["status"] == "formal" and not diagnostics,
            "status": contract["status"],
            "classification": contract["classification"],
            "issue_count": len(diagnostics),
            "issues": diagnostics,
        },
    )
    if contract["status"] != "formal" or diagnostics:
        route = {
            "schema_version": "text2ifc/scaffold-route/1.0",
            "route": "scaffold_blocked",
            "valid": False,
            "blocking_reason": "scaffold candidate failed BIM JSON contract",
            "source_issue_codes": sorted(source_issue_codes),
        }
        _write_json(scaffold_dir / "route.json", route)
        return route

    generator_candidate = run_dir / "generator" / "candidate.json"
    if generator_candidate.is_file():
        shutil.copyfile(
            generator_candidate,
            run_dir / "generator" / "original-candidate-before-scaffold.json",
        )
    _write_json(generator_candidate, candidate)
    _write_json(
        run_dir / "generator" / "validation.json",
        {
            "valid": True,
            "issue_count": 0,
            "issues": [],
            "source": "scaffold_candidate",
        },
    )
    _write_json(
        run_dir / "generator" / "classification.json",
        {
            "status": "scaffold_promoted",
            "contract_status": "formal",
            "classification": "formal",
            "schema_version": "bim-json/2.0",
            "draft_version": None,
            "target_schema_version": None,
            "diagnostics": [],
            "source": "scaffold_candidate",
        },
    )
    _write_candidate_origin(
        run_dir,
        candidate_origin="deterministic_scaffold_fallback",
        live_acceptance_eligible=False,
        route=route_name,
    )
    _copy_artifact_to_run_root(
        store,
        stored_session,
        kind="candidate",
        source=generator_candidate,
        target_name="candidate.json",
    )
    _record_existing_artifact(
        store,
        stored_session,
        kind="scaffold_candidate",
        name="scaffold/candidate.json",
    )
    route = {
        "schema_version": "text2ifc/scaffold-route/1.0",
        "route": route_name,
        "valid": True,
        "source_issue_codes": sorted(source_issue_codes),
        "source_gate_summary": source_gate_summary,
        "candidate": "candidate.json",
        "promoted_to": "generator/candidate.json",
    }
    _write_json(scaffold_dir / "route.json", route)
    _write_json(
        scaffold_dir / "metrics.json",
        {
            "stage": "scaffold",
            "route": route["route"],
            "valid": True,
            "source_issue_count": len(source_issue_codes),
            "entity_count": len(candidate.get("entities", [])),
            "relationship_count": len(candidate.get("relationships", [])),
        },
    )
    return route


def _dynamic_gate_issue_codes(gate_summary: dict[str, Any]) -> set[str]:
    return {
        str(code)
        for gate in gate_summary.get("gates", [])
        if isinstance(gate, dict)
        and str(gate.get("name", "")).startswith("dynamic_")
        for code in gate.get("issue_codes", [])
    }


def _read_json_issues(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    issues = payload.get("diagnostics") or payload.get("issues") or []
    return [issue for issue in issues if isinstance(issue, dict)]


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


def _attempt_generator_regeneration_after_audit(
    *,
    store: SessionStore,
    stored_session: Any,
    provider_factory: Callable[[], Any],
    design_dir: Path,
    trace_level: str | None,
    progress: Callable[[str, dict[str, Any]], None] | None,
    feedback_round_index: int,
    previous_issue_count: int | None,
) -> dict[str, Any] | None:
    run_dir = stored_session.run_dir
    audit_report_path = run_dir / "audit" / "audit-report.json"
    if not audit_report_path.is_file():
        return None
    audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
    if not _geometry_failure_requires_regeneration(run_dir, audit_report):
        return None

    issues = [
        *normalize_gate_sidecars(run_dir),
        *normalize_audit_findings(audit_report),
    ]
    if not issues:
        return None
    round_record = write_feedback_artifacts(
        run_dir,
        source_stage="audit",
        issues=issues,
        previous_issue_count=previous_issue_count,
        current_feedback_round=feedback_round_index,
    )
    route_decision = round_record["route_decision"]
    _record_existing_artifact(store, stored_session, kind="issues", name="issues.json")
    _record_existing_artifact(
        store,
        stored_session,
        kind="route_decision",
        name="route-decision.json",
    )
    _record_existing_artifact(
        store,
        stored_session,
        kind="feedback_rounds",
        name="feedback-rounds.json",
    )
    if (
        route_decision.get("route") != "regenerate_json"
        or route_decision.get("retry_allowed") is not True
    ):
        return None

    feedback = {
        "schema_version": "text2ifc/generator-regeneration-feedback/1.0",
        "route": route_decision["route"],
        "target_stage": route_decision["target_stage"],
        "source_stage": "audit",
        "route_decision": route_decision,
        "issues": round_record["issues"],
        "evidence_paths": [
            path
            for path in (
                "generator/candidate.json",
                "generator/validation.json",
                "geometry-feedback.json",
                "gate-summary.json",
                "audit/audit-report.json",
                "issues.json",
                "feedback-rounds.json",
            )
            if (run_dir / path).is_file()
        ],
    }
    round_number = feedback_round_index + 1
    regeneration_dir = run_dir / f"generator-regeneration-{round_number:02d}"
    regeneration_dir.mkdir(parents=True, exist_ok=True)
    _write_json(regeneration_dir / "generation-feedback.json", feedback)
    _emit_progress(
        progress,
        "generator",
        {"status": "regeneration_started", "route": "regenerate_json"},
    )
    generator = run_generator_stage(
        provider=provider_factory(),
        output_dir=regeneration_dir,
        design_source_dir=design_dir,
        case_id=stored_session.session_hash,
        session_prefix="phase6.2",
        trace_level=trace_level,
        generation_feedback=feedback,
        generator_call_index=round_number + 1,
    )
    _record_stage_payloads(
        store,
        stored_session.session_id,
        "generator_regeneration",
        generator,
    )
    _emit_progress(
        progress,
        "generator",
        {"status": generator.get("status"), "response_id": generator.get("response_id")},
    )
    if (
        generator["classification"] != "formal"
        or not generator["valid"]
        or not (regeneration_dir / "candidate.json").is_file()
    ):
        return {
            "generator": generator,
            "semantic_coverage": None,
            "candidate_gates": None,
            "audit": {"valid": False, "status": "blocked"},
            "issue_count": len(round_record["issues"]),
        }

    _promote_regenerated_generator_output(
        store=store,
        stored_session=stored_session,
        regeneration_dir=regeneration_dir,
    )
    _emit_progress(progress, "semantic_coverage", {"status": "started"})
    semantic_coverage = run_semantic_coverage_stage(
        case_dir=run_dir,
        output_dir=run_dir,
        case_id=stored_session.session_hash,
    )
    _record_stage_payloads(
        store,
        stored_session.session_id,
        "semantic_coverage",
        semantic_coverage,
    )
    _emit_progress(
        progress,
        "semantic_coverage",
        {"status": semantic_coverage.get("status") or semantic_coverage.get("valid")},
    )
    _emit_progress(progress, "candidate_gates", {"status": "started"})
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
    _emit_progress(
        progress,
        "candidate_gates",
        {"status": _gate_progress_status(candidate_gates)},
    )
    _emit_progress(progress, "audit", {"status": "started"})
    audit = run_audit_report_stage(
        provider=provider_factory(),
        case_dir=run_dir,
        case_id=stored_session.session_hash,
        session_prefix="phase6.2",
        audit_call_index=round_number + 1,
        trace_level=trace_level,
    )
    _record_stage_payloads(store, stored_session.session_id, "audit", audit)
    _emit_progress(
        progress,
        "audit",
        {"status": audit.get("status"), "response_id": audit.get("response_id")},
    )
    _archive_round_evidence(run_dir, round_number + 1)
    return {
        "generator": generator,
        "semantic_coverage": semantic_coverage,
        "candidate_gates": candidate_gates,
        "audit": audit,
        "issue_count": len(round_record["issues"]),
    }


def _promote_regenerated_generator_output(
    *,
    store: SessionStore,
    stored_session: Any,
    regeneration_dir: Path,
) -> None:
    run_dir = stored_session.run_dir
    generator_dir = run_dir / "generator"
    backup_dir = run_dir / "generator-before-regeneration-01"
    if generator_dir.is_dir() and not backup_dir.exists():
        shutil.copytree(generator_dir, backup_dir)
    for source in regeneration_dir.iterdir():
        if source.is_file():
            shutil.copyfile(source, generator_dir / source.name)
    _copy_artifact_to_run_root(
        store,
        stored_session,
        kind="candidate",
        source=generator_dir / "candidate.json",
        target_name="candidate.json",
    )
    if (generator_dir / "semantic-capabilities.json").is_file():
        _copy_artifact_to_run_root(
            store,
            stored_session,
            kind="semantic_capabilities",
            source=generator_dir / "semantic-capabilities.json",
            target_name="semantic-capabilities.json",
        )
    _write_candidate_origin(
        run_dir,
        candidate_origin="live_model_regeneration",
        live_acceptance_eligible=True,
        route="regenerate_json",
    )
    _record_existing_artifact(
        store,
        stored_session,
        kind="generator_regeneration",
        name=f"{regeneration_dir.name}/generation-feedback.json",
    )


def _archive_round_evidence(run_dir: Path, round_number: int) -> None:
    round_dir = run_dir / "evaluation-rounds" / f"round-{round_number:02d}"
    round_dir.mkdir(parents=True, exist_ok=True)
    for relative in (
        "candidate.json",
        "semantic-coverage.json",
        "ifc-verification.json",
        "geometry-feedback.json",
        "gate-summary.json",
        "dynamic-gates.json",
    ):
        source = run_dir / relative
        if source.is_file():
            shutil.copyfile(source, round_dir / source.name)
    audit_dir = run_dir / "audit"
    archived_audit = round_dir / "audit"
    if audit_dir.is_dir():
        if archived_audit.exists():
            raise ValueError(f"evaluation round {round_number} already exists")
        shutil.copytree(audit_dir, archived_audit)


def _write_candidate_origin(
    run_dir: Path,
    *,
    candidate_origin: str,
    live_acceptance_eligible: bool,
    route: str | None = None,
) -> None:
    payload = {
        "schema_version": "text2ifc/candidate-origin/1.0",
        "candidate_origin": candidate_origin,
        "live_acceptance_eligible": live_acceptance_eligible,
    }
    if route is not None:
        payload["route"] = route
    _write_json(run_dir / "candidate-origin.json", payload)


def _record_provider_failure(
    *,
    store: SessionStore,
    stored_session: Any,
    stage: str,
    exc: ProviderOutputError,
) -> dict[str, Any]:
    stage_dir = stored_session.run_dir / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    details = redact_metadata(getattr(exc, "details", {}))
    if not isinstance(details, dict):
        details = {"details": details}
    payload = {
        "schema_version": "text2ifc/provider-failure/1.0",
        "stage": stage,
        "status": "failed",
        "valid": False,
        "provider": details.get("provider", "unknown"),
        "failure_class": details.get("failure_class", "provider_error"),
        "exception_type": details.get("exception_type", type(exc).__name__),
        "details": details,
    }
    _write_json(stage_dir / "provider-error.json", payload)
    store.record_artifact(
        stored_session.session_id,
        kind="provider_error",
        path=Path("runs") / stored_session.session_hash / stage / "provider-error.json",
    )
    store.record_payload(
        stored_session.session_id,
        table="metrics",
        payload={
            "stage": stage,
            "status": "provider_failed",
            "valid": False,
            "failure_class": payload["failure_class"],
            "provider": payload["provider"],
            "error_path": f"{stage}/provider-error.json",
        },
    )
    store.append_event(
        stored_session.session_id,
        event_type=f"{stage}_provider_failed",
        payload={
            "stage": stage,
            "status": "failed",
            "valid": False,
            "failure_class": payload["failure_class"],
            "provider": payload["provider"],
            "error_path": f"{stage}/provider-error.json",
        },
    )
    store.mark_session_status(stored_session.session_id, "provider_failed")
    store.export_session(stored_session.session_id)
    return payload


def _write_provider_failure_issues(
    *,
    store: SessionStore,
    stored_session: Any,
    stage: str,
    error_payload: dict[str, Any],
) -> None:
    issues = normalize_provider_failure(error_payload, stage=stage)
    write_terminal_issues(stored_session.run_dir, issues)
    write_feedback_artifacts(
        stored_session.run_dir,
        source_stage=stage,
        issues=issues,
    )
    _record_existing_artifact(store, stored_session, kind="issues", name="issues.json")
    _record_existing_artifact(
        store,
        stored_session,
        kind="route_decision",
        name="route-decision.json",
    )
    _record_existing_artifact(
        store,
        stored_session,
        kind="feedback_rounds",
        name="feedback-rounds.json",
    )
    _write_phase6_4_case_result(
        store=store,
        stored_session=stored_session,
        final_status="blocked",
        output_type="none",
        route="provider_retry",
        failure_owner="provider",
        blocking_issue_count=len(issues),
    )


def _write_terminal_non_accept_issues(
    *,
    store: SessionStore,
    stored_session: Any,
) -> None:
    run_dir = stored_session.run_dir
    issues = []
    generator_metrics = _read_optional_json(run_dir / "generator" / "metrics.json")
    generator_draft = _read_optional_json(run_dir / "generator" / "parsed-output.json")
    if generator_metrics and generator_metrics.get("classification") != "formal" and generator_draft:
        issues.extend(normalize_generator_draft_issues(generator_draft))
    generator_validation = _read_optional_issues(run_dir / "generator" / "validation.json")
    if generator_validation:
        issues.extend(
            normalize_validation_issues(
                generator_validation,
                source="schema_validation",
            )
        )
    semantic_coverage = _read_optional_json(run_dir / "semantic-coverage.json")
    if semantic_coverage and semantic_coverage.get("valid") is False:
        issues.extend(
            normalize_validation_issues(
                _semantic_coverage_diagnostics(semantic_coverage),
                source="semantic_validation",
            )
        )
    issues.extend(normalize_gate_sidecars(run_dir))
    audit_report = _read_optional_json(run_dir / "audit" / "audit-report.json")
    if audit_report:
        issues.extend(normalize_audit_findings(audit_report))
    audit_validation = _read_optional_issues(run_dir / "audit" / "validation.json")
    if audit_validation:
        issues.extend(
            normalize_validation_issues(
                audit_validation,
                source="semantic_validation",
            )
        )
    if issues:
        write_terminal_issues(run_dir, issues)
        round_record = write_feedback_artifacts(
            run_dir,
            source_stage="workflow",
            issues=issues,
        )
        _record_existing_artifact(store, stored_session, kind="issues", name="issues.json")
        _record_existing_artifact(
            store,
            stored_session,
            kind="route_decision",
            name="route-decision.json",
        )
        _record_existing_artifact(
            store,
            stored_session,
            kind="feedback_rounds",
            name="feedback-rounds.json",
        )
        _write_phase6_4_case_result(
            store=store,
            stored_session=stored_session,
            final_status=str(round_record["route_decision"]["final_status"]),
            output_type="none",
            route=str(round_record["route_decision"]["route"]),
            failure_owner=issues[0].owner if issues else None,
            blocking_issue_count=len(issues),
        )


def _write_phase6_4_accept_artifacts(
    *,
    store: SessionStore,
    stored_session: Any,
) -> None:
    write_issues(stored_session.run_dir / "issues.json", [])
    write_feedback_artifacts(
        stored_session.run_dir,
        source_stage="final",
        issues=[],
    )
    _record_existing_artifact(store, stored_session, kind="issues", name="issues.json")
    _record_existing_artifact(
        store,
        stored_session,
        kind="route_decision",
        name="route-decision.json",
    )
    _record_existing_artifact(
        store,
        stored_session,
        kind="feedback_rounds",
        name="feedback-rounds.json",
    )


def _write_phase6_4_case_result(
    *,
    store: SessionStore,
    stored_session: Any,
    final_status: str,
    output_type: str,
    route: str,
    failure_owner: str | None,
    blocking_issue_count: int,
) -> None:
    payload = {
        "schema_version": "text2ifc/phase6.4-case-result/1.0",
        "case_id": stored_session.session_hash,
        "input_language": "zh-CN",
        "workflow_language": "en-US-control",
        "prompt_language": "zh-CN",
        "output_type": output_type,
        "schema_passed": _json_bool(stored_session.run_dir / "generator" / "validation.json", "valid"),
        "compile_reopen_passed": _json_bool(stored_session.run_dir / "ifc-verification.json", "success"),
        "deterministic_gates_passed": _json_value(stored_session.run_dir / "gate-summary.json", "overall_status") == "passed",
        "audit_passed": _json_value(stored_session.run_dir / "audit" / "audit-report.json", "recommendation") == "accept",
        "final_status": final_status,
        "route": route,
        "failure_owner": failure_owner,
        "blocking_issue_count": blocking_issue_count,
        "evidence_paths": [
            path
            for path in (
                "design-brief/design-brief.json",
                "generator/candidate.json",
                "generator/validation.json",
                "ifc-verification.json",
                "geometry-feedback.json",
                "gate-summary.json",
                "audit/audit-report.json",
                "issues.json",
                "route-decision.json",
                "feedback-rounds.json",
                "output.ifc",
            )
            if (stored_session.run_dir / path).is_file()
        ],
    }
    _write_json(stored_session.run_dir / "case-result.json", payload)
    _record_existing_artifact(
        store,
        stored_session,
        kind="case_result",
        name="case-result.json",
    )


def _json_bool(path: Path, key: str) -> bool:
    return bool(_json_value(path, key))


def _json_value(path: Path, key: str) -> Any:
    payload = _read_optional_json(path)
    if not payload:
        return None
    return payload.get(key)


def _read_optional_issues(path: Path) -> list[dict[str, Any]]:
    payload = _read_optional_json(path)
    if not payload:
        return []
    raw = payload.get("diagnostics") or payload.get("issues") or []
    return [dict(item) for item in raw if isinstance(item, dict)]


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else None


def _semantic_coverage_diagnostics(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("blocking_facts") or []
    diagnostics: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        diagnostics.append(
            {
                "code": str(item.get("coverage_state") or "SEMANTIC_COVERAGE_FAILED").upper(),
                "path": item.get("path"),
                "message": item.get("reason") or item.get("message") or "Semantic coverage failed.",
            }
        )
    return diagnostics


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

        return OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )
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
