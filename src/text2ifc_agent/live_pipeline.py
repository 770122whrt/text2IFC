"""Auditable live-provider orchestration for Phase 6.1."""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from typing import Any

from text2ifc_compiler import compile_document
from text2ifc_quality import check_generated_ifc

from .artifact_scan import scan_path
from .context_selection import select_design_brief_context
from .clarification import (
    ClarificationCall,
    ClarificationController,
    ClarificationError,
)
from .design_brief import load_design_brief_schema, validate_design_brief
from .live_trace import write_live_trace
from .prompt_registry import render_prompt
from .generator import validate_generation_document
from .failure_routing import route_generation_failure
from .fact_delta import evaluate_repair_fact_delta
from .providers import validate_provider_output
from .run_report import build_live_run_report, resolve_final_design_brief_dir


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_BRIEF_TEMPLATE_ID = "design-brief.v2.1"
GENERATOR_TEMPLATE_ID = "bim-json-generator.v2"
REPAIR_TEMPLATE_ID = "bim-json-generator-repair.v2"
AUDIT_TEMPLATE_ID = "audit.v2"
FORMAL_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "bim-json" / "2.0" / "schema.json"
DRAFT_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "bim-json" / "draft" / "1.0" / "schema.json"
)
GENERATOR_FEW_SHOT_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "geometry-gate"
    / "simple-room-fixed"
    / "candidate.json"
)


def complete_room_case() -> dict[str, Any]:
    """Return the versioned Chinese room case used for v1/v2 comparison."""
    user_request = (
        "请创建一个单层矩形房间，长6米、宽4米、高3米；四面墙闭合，"
        "南墙中央设置一扇宽0.9米、高2.1米的门，北墙中央设置一扇"
        "宽1.2米、高1.5米、窗台高0.9米的窗。"
    )
    return {
        "case_id": "complete-room",
        "user_request": user_request,
        "conversation": [
            {
                "turn_id": "turn-user-001",
                "role": "user",
                "content": user_request,
            },
            {
                "turn_id": "turn-assistant-002",
                "role": "assistant",
                "content": "为了生成具有明确实体厚度的墙体，请问墙体厚度是多少？",
            },
            {
                "turn_id": "turn-user-003",
                "role": "user",
                "content": "厚度为300毫米。",
            },
        ],
    }


def clarified_room_case() -> dict[str, Any]:
    """Return the incomplete room case whose wall thickness needs clarification."""
    base = complete_room_case()
    return {
        "case_id": "clarified-room",
        "user_request": base["user_request"],
        "conversation": [
            {
                "turn_id": "turn-user-001",
                "role": "user",
                "content": base["user_request"],
                "question_ids": [],
            }
        ],
    }


def unknown_answer_case() -> dict[str, Any]:
    """Return the same missing-thickness case with a distinct matrix id."""
    base = clarified_room_case()
    return {**base, "case_id": "unknown-answer"}


def run_design_brief_stage(
    *,
    provider: Any,
    output_dir: Path | str,
    case: dict[str, Any],
) -> dict[str, Any]:
    """Run one Design Brief v2 call and preserve all input/output evidence."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    user_request = str(case["user_request"])
    conversation = list(case["conversation"])
    selection = select_design_brief_context(
        user_request=user_request,
        conversation=conversation,
    )
    schema = load_design_brief_schema("text2ifc/design-brief/2.0")
    renderer_inputs = {
        "USER_REQUEST": user_request,
        "CONVERSATION": conversation,
        "DESIGN_BRIEF_SCHEMA": schema,
        "EVIDENCE_CATALOG": selection["evidence"],
        "FEW_SHOTS": selection["few_shots"],
    }
    rendered = render_prompt(
        template_id=DESIGN_BRIEF_TEMPLATE_ID,
        inputs=renderer_inputs,
    )

    _write_text(output / "input.txt", user_request + "\n")
    _write_json(output / "conversation.json", conversation)
    _write_json(output / "context-selection.json", selection)
    _write_json(output / "prompt-render-input.json", renderer_inputs)
    _write_text(output / "prompt-rendered.md", rendered["text"])

    call_index = case.get("call_index")
    session_id = (
        f"phase6.1-{case['case_id']}-design-brief-{int(call_index):02d}"
        if call_index is not None
        else f"phase6.1-{case['case_id']}-design-brief-v2"
    )
    result = provider.generate_live(
        session_id=session_id,
        prompt=rendered["text"],
        schema=schema,
        state={"case_id": case["case_id"], "stage": "design-brief"},
    )
    provider_manifest = write_live_trace(result=result, output_dir=output)
    parse_status, parsed, parse_diagnostics = result.output.parse_json()
    issues = []
    if parse_status == "ok" and parsed is not None:
        _write_json(output / "parsed-output.json", parsed)
        issues = validate_design_brief(
            parsed,
            evidence_catalog=selection["evidence"],
        )

    serialized_issues = [asdict(issue) for issue in issues]
    if parse_status != "ok":
        serialized_issues = list(parse_diagnostics)
    schema_semantic_valid = parse_status == "ok" and not serialized_issues
    strict_output_contract_valid = (
        parse_status == "ok" and not parse_diagnostics
    )
    validation = {
        "valid": schema_semantic_valid,
        "issue_count": len(serialized_issues),
        "issues": serialized_issues,
    }
    _write_json(output / "validation.json", validation)

    if schema_semantic_valid and parsed is not None:
        _write_json(output / "design-brief.json", parsed)
        if strict_output_contract_valid:
            stage_status = str(parsed["status"])
        else:
            stage_status = "blocked_output_contract"
    else:
        stage_status = "blocked_prompt_defect"

    acceptance_valid = schema_semantic_valid and strict_output_contract_valid

    metrics = {
        "case_id": case["case_id"],
        "stage": "design-brief",
        "evidence_class": result.evidence_class,
        "parse_valid": parse_status == "ok",
        "schema_semantic_valid": schema_semantic_valid,
        "strict_output_contract_valid": strict_output_contract_valid,
        "normalization_diagnostics": parse_diagnostics,
        "response_id": result.response.get("id"),
        "model": result.response.get("model"),
        "stop_reason": result.response.get("stop_reason"),
        "usage": dict(result.response.get("usage", {})),
        "design_status": (
            parsed.get("status") if schema_semantic_valid and parsed else None
        ),
        "question_count": (
            len(parsed.get("clarification_questions", []))
            if schema_semantic_valid and parsed
            else None
        ),
    }
    _write_json(output / "metrics.json", metrics)

    trace_manifest = {
        "schema_version": "text2ifc/live-stage-trace/1.0",
        "case_id": case["case_id"],
        "stage": "design-brief",
        "template_id": rendered["metadata"]["template_id"],
        "template_hash": rendered["metadata"]["template_hash"],
        "request_sha256": selection["request_sha256"],
        "selected_evidence": [
            {
                "evidence_id": item["evidence_id"],
                "source_path": item["source_path"],
                "source_sha256": item["source_sha256"],
                "json_pointer": item["json_pointer"],
            }
            for item in selection["evidence"]
        ],
        "few_shot_ids": [
            item["few_shot_id"] for item in selection["few_shots"]
        ],
        "provider": provider_manifest,
        "artifacts": {
            "input": "input.txt",
            "conversation": "conversation.json",
            "context_selection": "context-selection.json",
            "renderer_inputs": "prompt-render-input.json",
            "rendered_prompt": "prompt-rendered.md",
            "model_text": "model-text.txt",
            "parsed_output": "parsed-output.json" if parsed is not None else None,
            "design_brief": (
                "design-brief.json" if schema_semantic_valid else None
            ),
            "validation": "validation.json",
            "metrics": "metrics.json",
        },
    }
    _write_json(output / "trace-manifest.json", trace_manifest)
    return {
        "case_id": case["case_id"],
        "stage": "design-brief",
        "status": stage_status,
        "valid": acceptance_valid,
        "schema_semantic_valid": schema_semantic_valid,
        "strict_output_contract_valid": strict_output_contract_valid,
        "output_dir": portable_artifact_path(output),
        "response_id": result.response.get("id"),
        "evidence_class": result.evidence_class,
    }


def run_clarification_case(
    *,
    provider: Any,
    output_dir: Path | str,
    case: dict[str, Any],
    answers: list[str],
) -> dict[str, Any]:
    """Run model-authored clarification rounds with append-only user answers."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    calls_dir = output / "calls"
    states_dir = output / "states"
    calls_dir.mkdir(parents=True, exist_ok=True)
    states_dir.mkdir(parents=True, exist_ok=True)
    event_path = output / "events.jsonl"
    if event_path.exists():
        event_path.unlink()

    user_request = str(case["user_request"])
    _write_text(output / "input.txt", user_request + "\n")
    _write_json(output / "answers.json", {"answers": list(answers)})
    controller = ClarificationController.start(
        case_id=str(case["case_id"]),
        user_request=user_request,
    )

    def invoke(transcript: list[dict[str, Any]], call_index: int) -> ClarificationCall:
        call_dir = calls_dir / f"{call_index:02d}-design-brief"
        _append_event(
            event_path,
            {
                "event": "design_brief_call_started",
                "case_id": case["case_id"],
                "call_index": call_index,
                "turn_count": len(transcript),
            },
        )
        stage_result = run_design_brief_stage(
            provider=provider,
            output_dir=call_dir,
            case={
                "case_id": case["case_id"],
                "call_index": call_index,
                "user_request": user_request,
                "conversation": transcript,
            },
        )
        _append_event(
            event_path,
            {
                "event": "design_brief_call_completed",
                "case_id": case["case_id"],
                "call_index": call_index,
                "response_id": stage_result.get("response_id"),
                "status": stage_result.get("status"),
                "schema_semantic_valid": stage_result.get(
                    "schema_semantic_valid"
                ),
                "strict_output_contract_valid": stage_result.get(
                    "strict_output_contract_valid"
                ),
            },
        )
        if not stage_result["valid"]:
            raise ClarificationError(
                "live Design Brief call failed acceptance gates: "
                + str(stage_result["status"])
            )
        brief = json.loads(
            (call_dir / "design-brief.json").read_text(encoding="utf-8")
        )
        selection = json.loads(
            (call_dir / "context-selection.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (call_dir / "trace-manifest.json").read_text(encoding="utf-8")
        )
        return ClarificationCall(
            call_index=call_index,
            response_id=str(stage_result["response_id"]),
            prompt_template_id=str(manifest["template_id"]),
            prompt_template_hash=str(manifest["template_hash"]),
            artifact_dir=portable_artifact_path(call_dir),
            brief=brief,
            evidence_catalog=list(selection["evidence"]),
        )

    first_call = invoke(controller.transcript_dicts(), 1)
    controller = controller.record_model_call(first_call)
    _write_json(states_dir / "after-call-01.json", controller.to_dict())

    answer_index = 0
    while controller.status == "needs_clarification" and answer_index < len(answers):
        answer = answers[answer_index]
        answer_index += 1
        _append_event(
            event_path,
            {
                "event": "user_answer_appended",
                "case_id": case["case_id"],
                "answer_index": answer_index,
                "question_ids": list(controller.pending_question_ids),
            },
        )
        controller = controller.answer_and_rerun(
            answer=answer,
            invoke_design_brief=invoke,
        )
        _write_json(
            states_dir / f"after-call-{len(controller.calls):02d}.json",
            controller.to_dict(),
        )

    terminal_statuses = {"ready", "draft_required", "blocked"}
    terminal = controller.status in terminal_statuses
    final_brief = controller.calls[-1].brief
    _write_json(output / "conversation.json", controller.transcript_dicts())
    _write_json(output / "state.json", controller.to_dict())
    _write_json(output / "design-brief.json", final_brief)

    call_metrics = [
        json.loads(
            (
                calls_dir
                / f"{call.call_index:02d}-design-brief"
                / "metrics.json"
            ).read_text(encoding="utf-8")
        )
        for call in controller.calls
    ]
    metrics = {
        "case_id": case["case_id"],
        "evidence_class": "live" if all(
            item.get("evidence_class") == "live" for item in call_metrics
        ) else "unit_or_replay",
        "live_call_count": len(controller.calls),
        "response_ids": [call.response_id for call in controller.calls],
        "design_statuses": [call.brief["status"] for call in controller.calls],
        "answer_turn_count": sum(
            1 for turn in controller.transcript if turn.role == "user"
        ) - 1,
        "terminal_status": controller.status,
        "terminal": terminal,
        "all_end_turn": all(
            item.get("stop_reason") == "end_turn" for item in call_metrics
        ),
        "all_strict_output_contract_valid": all(
            item.get("strict_output_contract_valid") is True
            for item in call_metrics
        ),
    }
    _write_json(output / "metrics.json", metrics)
    _write_json(
        output / "call-manifest.json",
        {
            "schema_version": "text2ifc/live-clarification-manifest/1.0",
            "case_id": case["case_id"],
            "calls": [
                {
                    "call_index": call.call_index,
                    "response_id": call.response_id,
                    "prompt_template_id": call.prompt_template_id,
                    "prompt_template_hash": call.prompt_template_hash,
                    "artifact_dir": call.artifact_dir,
                    "design_status": call.brief["status"],
                }
                for call in controller.calls
            ],
            "final_design_brief": "design-brief.json",
            "conversation": "conversation.json",
            "metrics": "metrics.json",
        },
    )
    _append_event(
        event_path,
        {
            "event": "clarification_terminal",
            "case_id": case["case_id"],
            "status": controller.status,
            "terminal": terminal,
            "live_call_count": len(controller.calls),
        },
    )
    return {
        "case_id": case["case_id"],
        "stage": "clarify",
        "status": controller.status,
        "valid": terminal,
        "live_call_count": len(controller.calls),
        "response_ids": [call.response_id for call in controller.calls],
        "evidence_class": metrics["evidence_class"],
        "output_dir": portable_artifact_path(output),
    }


def run_generator_stage(
    *,
    provider: Any,
    output_dir: Path | str,
    design_source_dir: Path | str,
    case_id: str,
    session_prefix: str = "phase6.1",
) -> dict[str, Any]:
    """Run one real Generator call with exact Formal and Draft contracts."""
    output = Path(output_dir)
    source = Path(design_source_dir)
    output.mkdir(parents=True, exist_ok=True)
    user_request = (source / "input.txt").read_text(encoding="utf-8").rstrip("\r\n")
    conversation = json.loads(
        (source / "conversation.json").read_text(encoding="utf-8")
    )
    design_brief = json.loads(
        (source / "design-brief.json").read_text(encoding="utf-8")
    )
    design_context = json.loads(
        (source / "context-selection.json").read_text(encoding="utf-8")
    )
    if design_brief.get("status") != "ready":
        raise ValueError("Generator requires a ready Design Brief")
    formal_schema = json.loads(FORMAL_SCHEMA_PATH.read_text(encoding="utf-8"))
    draft_schema = json.loads(DRAFT_SCHEMA_PATH.read_text(encoding="utf-8"))
    generator_context = _select_generator_context(design_context)
    renderer_inputs = {
        "USER_REQUEST": user_request,
        "CONVERSATION": conversation,
        "DESIGN_BRIEF": design_brief,
        "FORMAL_SCHEMA": formal_schema,
        "DRAFT_SCHEMA": draft_schema,
        "CAPABILITY_PROFILE": generator_context["capability_profile"],
        "FEW_SHOTS": generator_context["few_shots"],
    }
    rendered = render_prompt(
        template_id=GENERATOR_TEMPLATE_ID,
        inputs=renderer_inputs,
    )

    _write_text(output / "input.txt", user_request + "\n")
    _write_json(output / "conversation.json", conversation)
    _write_json(output / "design-brief.json", design_brief)
    _write_json(output / "generator-context.json", generator_context)
    _write_json(output / "prompt-render-input.json", renderer_inputs)
    _write_text(output / "prompt-rendered.md", rendered["text"])

    result = provider.generate_live(
        session_id=f"{session_prefix}-{case_id}-generator-01",
        prompt=rendered["text"],
        schema=formal_schema,
        state={"case_id": case_id, "stage": "generate"},
    )
    validate_provider_output(result.output)
    provider_manifest = write_live_trace(result=result, output_dir=output)
    parse_status, parsed, normalization_diagnostics = result.output.parse_json()
    if parse_status == "ok" and parsed is not None:
        _write_json(output / "parsed-output.json", parsed)
        contract = validate_generation_document(parsed)
    else:
        contract = {
            "status": "invalid",
            "classification": "unparsed",
            "diagnostics": [],
        }
    contract_diagnostics = list(contract["diagnostics"])
    diagnostics = [*normalization_diagnostics, *contract_diagnostics]
    strict_output_contract_valid = (
        parse_status == "ok" and not normalization_diagnostics
    )
    contract_valid = contract["status"] in {"formal", "draft"} and not contract_diagnostics
    acceptance_valid = contract_valid and strict_output_contract_valid

    if contract_valid and parsed is not None:
        artifact_name = "candidate.json" if contract["classification"] == "formal" else "draft.json"
        _write_json(output / artifact_name, parsed)
    else:
        artifact_name = None
    stage_status = (
        str(contract["status"])
        if strict_output_contract_valid
        else "blocked_output_contract"
    )
    classification_record = {
        "status": stage_status,
        "contract_status": contract["status"],
        "classification": contract["classification"],
        "schema_version": parsed.get("schema_version") if parsed else None,
        "draft_version": parsed.get("draft_version") if parsed else None,
        "target_schema_version": (
            parsed.get("target_schema_version") if parsed else None
        ),
        "diagnostics": diagnostics,
    }
    _write_json(output / "classification.json", classification_record)
    _write_json(
        output / "validation.json",
        {
            "valid": contract_valid,
            "issue_count": len(contract_diagnostics),
            "issues": contract_diagnostics,
        },
    )
    metrics = {
        "case_id": case_id,
        "stage": "generate",
        "evidence_class": result.evidence_class,
        "response_id": result.response.get("id"),
        "model": result.response.get("model"),
        "stop_reason": result.response.get("stop_reason"),
        "usage": dict(result.response.get("usage", {})),
        "parse_valid": parse_status == "ok",
        "classification": contract["classification"],
        "contract_status": contract["status"],
        "contract_valid": contract_valid,
        "strict_output_contract_valid": strict_output_contract_valid,
        "normalization_diagnostics": normalization_diagnostics,
        "issue_count": len(contract_diagnostics),
    }
    _write_json(output / "metrics.json", metrics)
    _write_json(
        output / "trace-manifest.json",
        {
            "schema_version": "text2ifc/live-stage-trace/1.0",
            "case_id": case_id,
            "stage": "generate",
            "template_id": rendered["metadata"]["template_id"],
            "template_hash": rendered["metadata"]["template_hash"],
            "source_design_brief": portable_artifact_path(
                source / "design-brief.json"
            ),
            "formal_schema": {
                "path": portable_artifact_path(FORMAL_SCHEMA_PATH),
                "sha256": _file_sha256(FORMAL_SCHEMA_PATH),
            },
            "draft_schema": {
                "path": portable_artifact_path(DRAFT_SCHEMA_PATH),
                "sha256": _file_sha256(DRAFT_SCHEMA_PATH),
            },
            "provider": provider_manifest,
            "artifacts": {
                "input": "input.txt",
                "conversation": "conversation.json",
                "design_brief": "design-brief.json",
                "generator_context": "generator-context.json",
                "renderer_inputs": "prompt-render-input.json",
                "rendered_prompt": "prompt-rendered.md",
                "model_text": "model-text.txt",
                "parsed_output": "parsed-output.json" if parsed else None,
                "accepted_document": artifact_name,
                "classification": "classification.json",
                "validation": "validation.json",
                "metrics": "metrics.json",
            },
        },
    )
    return {
        "case_id": case_id,
        "stage": "generate",
        "status": stage_status,
        "classification": contract["classification"],
        "valid": acceptance_valid,
        "contract_valid": contract_valid,
        "strict_output_contract_valid": strict_output_contract_valid,
        "response_id": result.response.get("id"),
        "evidence_class": result.evidence_class,
        "output_dir": portable_artifact_path(output),
    }


def run_invalid_contract_replay_stage(
    *,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Write an auditable replay fixture for an unknown contract response."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    replay_response = {
        "id": "replay-invalid-contract-001",
        "type": "message",
        "role": "assistant",
        "model": "replay-fixture",
        "stop_reason": "end_turn",
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "draft_version": "text2ifc/draft-envelope/1.0",
                        "target_schema_version": "bim-json/2.0",
                        "partial_document": {},
                    },
                    ensure_ascii=False,
                ),
            }
        ],
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }
    model_text = str(replay_response["content"][0]["text"])
    parsed = json.loads(model_text)
    contract = validate_generation_document(parsed)
    diagnostics = list(contract["diagnostics"])
    classification = {
        "status": "blocked_replay",
        "contract_status": contract["status"],
        "classification": contract["classification"],
        "schema_version": parsed.get("schema_version"),
        "draft_version": parsed.get("draft_version"),
        "target_schema_version": parsed.get("target_schema_version"),
        "diagnostics": diagnostics,
    }
    metrics = {
        "case_id": "invalid-contract",
        "stage": "invalid-contract",
        "evidence_class": "replay",
        "response_id": replay_response["id"],
        "model": replay_response["model"],
        "stop_reason": replay_response["stop_reason"],
        "parse_valid": True,
        "classification": contract["classification"],
        "contract_status": contract["status"],
        "contract_valid": False,
        "strict_output_contract_valid": True,
        "issue_count": len(diagnostics),
        "excluded_from_live_quality": True,
        "writes_ifc": False,
    }

    _write_json(output / "response.raw.json", replay_response)
    _write_text(output / "model-text.txt", model_text + "\n")
    _write_json(output / "parsed-output.json", parsed)
    _write_json(output / "classification.json", classification)
    _write_json(
        output / "validation.json",
        {"valid": False, "issue_count": len(diagnostics), "issues": diagnostics},
    )
    _write_json(output / "metrics.json", metrics)
    _write_text(
        output / "report.md",
        "\n".join(
            [
                "# Phase 6.1 Invalid Contract Replay",
                "",
                "Generated from a saved replay fixture. This artifact is excluded from live provider quality metrics.",
                "",
                "## Result",
                "",
                "- status: `blocked_replay`",
                "- evidence_class: `replay`",
                "- writes_ifc: `false`",
                "",
                "## Source Sidecars",
                "",
                "- [response.raw.json](response.raw.json)",
                "- [model-text.txt](model-text.txt)",
                "- [parsed-output.json](parsed-output.json)",
                "- [classification.json](classification.json)",
                "- [validation.json](validation.json)",
                "- [metrics.json](metrics.json)",
            ]
        )
        + "\n",
    )
    return {
        "case_id": "invalid-contract",
        "stage": "invalid-contract",
        "status": "blocked_replay",
        "classification": contract["classification"],
        "valid": True,
        "evidence_class": "replay",
        "writes_ifc": False,
        "excluded_from_live_quality": True,
        "output_dir": portable_artifact_path(output),
    }


def run_repair_stage(
    *,
    provider_factory: Any,
    output_dir: Path | str,
    generator_source_dir: Path | str,
    case_id: str,
) -> dict[str, Any]:
    """Route a generator result through bounded repair or no-repair evidence."""
    output = Path(output_dir)
    source = Path(generator_source_dir)
    output.mkdir(parents=True, exist_ok=True)

    user_request = (source / "input.txt").read_text(encoding="utf-8").rstrip("\r\n")
    conversation = json.loads(
        (source / "conversation.json").read_text(encoding="utf-8")
    )
    design_brief = json.loads(
        (source / "design-brief.json").read_text(encoding="utf-8")
    )
    validation = json.loads((source / "validation.json").read_text(encoding="utf-8"))
    source_metrics = json.loads((source / "metrics.json").read_text(encoding="utf-8"))
    generator_context_path = source / "generator-context.json"
    generator_context = (
        json.loads(generator_context_path.read_text(encoding="utf-8"))
        if generator_context_path.is_file()
        else {"capability_profile": [], "few_shots": []}
    )
    candidate_path = source / "candidate.json"
    candidate = (
        json.loads(candidate_path.read_text(encoding="utf-8"))
        if candidate_path.is_file()
        else None
    )
    validation_issues = list(validation.get("issues", []))
    route = route_generation_failure(
        previous_candidate=candidate,
        validation_feedback=validation_issues,
        geometry_feedback=[],
        known_facts=design_brief.get("known_facts", {}),
    )

    _write_text(output / "input.txt", user_request + "\n")
    _write_json(output / "conversation.json", conversation)
    _write_json(output / "design-brief.json", design_brief)
    if candidate is not None:
        _write_json(output / "candidate.json", candidate)
    _write_json(output / "source-validation.json", validation)
    _write_json(output / "generator-context.json", generator_context)

    provider_call_count = 0
    evidence_class = "deterministic-no-call"
    valid = False
    provider_manifest: dict[str, Any] | None = None
    repaired_document: dict[str, Any] | None = None
    repaired_artifact_name: str | None = None
    fact_delta: dict[str, Any] | None = None
    repair_diagnostics: list[dict[str, Any]] = []
    if route["route"] == "no_repair_needed":
        evidence_class = "live-derived-no-call"
        valid = bool(validation.get("valid")) and candidate is not None
    elif route["route"] == "repair_attempted" and candidate is not None:
        formal_schema = json.loads(FORMAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        draft_schema = json.loads(DRAFT_SCHEMA_PATH.read_text(encoding="utf-8"))
        allowed_change_paths = _repair_allowed_change_paths(validation_issues)
        evidence_by_path = _repair_evidence_by_path(
            validation_issues,
            allowed_change_paths,
        )
        renderer_inputs = {
            "USER_REQUEST": user_request,
            "CONVERSATION": conversation,
            "DESIGN_BRIEF": design_brief,
            "CANDIDATE": candidate,
            "FORMAL_SCHEMA": formal_schema,
            "DRAFT_SCHEMA": draft_schema,
            "CAPABILITY_PROFILE": generator_context.get("capability_profile", []),
            "VALIDATION_FEEDBACK": validation_issues,
            "GEOMETRY_FEEDBACK": [],
            "ALLOWED_CHANGE_PATHS": allowed_change_paths,
            "EVIDENCE_BY_PATH": evidence_by_path,
        }
        rendered = render_prompt(
            template_id=REPAIR_TEMPLATE_ID,
            inputs=renderer_inputs,
        )
        _write_json(output / "prompt-render-input.json", renderer_inputs)
        _write_text(output / "prompt-rendered.md", rendered["text"])
        provider = provider_factory()
        provider_call_count = 1
        live_result = provider.generate_live(
            session_id=f"phase6.1-{case_id}-repair-01",
            prompt=rendered["text"],
            schema=formal_schema,
            state={"case_id": case_id, "stage": "repair"},
        )
        validate_provider_output(live_result.output)
        provider_manifest = write_live_trace(result=live_result, output_dir=output)
        evidence_class = live_result.evidence_class
        parse_status, parsed, normalization_diagnostics = live_result.output.parse_json()
        if parse_status == "ok" and parsed is not None:
            _write_json(output / "parsed-output.json", parsed)
            contract = validate_generation_document(parsed)
        else:
            contract = {
                "status": "invalid",
                "classification": "unparsed",
                "diagnostics": [],
            }
        repair_diagnostics = [
            *normalization_diagnostics,
            *list(contract["diagnostics"]),
        ]
        if parsed is not None and contract["status"] in {"formal", "draft"}:
            repaired_document = parsed
            repaired_artifact_name = (
                "repaired-candidate.json"
                if contract["classification"] == "formal"
                else "repaired-draft.json"
            )
            _write_json(output / repaired_artifact_name, repaired_document)
            fact_delta = evaluate_repair_fact_delta(
                before=candidate,
                after=repaired_document,
                allowed_change_paths=allowed_change_paths,
                evidence_by_path=evidence_by_path,
            )
            _write_json(output / "fact-delta.json", fact_delta)
        route = route_generation_failure(
            previous_candidate=candidate,
            validation_feedback=validation_issues,
            geometry_feedback=[],
            known_facts=design_brief.get("known_facts", {}),
            repaired_candidate=repaired_document,
            repaired_feedback=repair_diagnostics,
        )
        if fact_delta is not None and not fact_delta["valid"]:
            route = {
                "route": "blocked_failure",
                "repair_attempts": route.get("repair_attempts", []),
                "blocking_reason": "repair fact-delta gate failed",
                "fact_delta_issues": fact_delta["issues"],
            }
        valid = (
            route["route"] == "repair_attempted"
            and repaired_document is not None
            and contract["status"] in {"formal", "draft"}
            and not repair_diagnostics
            and (fact_delta is None or fact_delta["valid"])
        )
    else:
        route = {
            **route,
            "blocking_reason": route.get(
                "blocking_reason",
                "repair orchestration is only enabled after an eligible failure",
            ),
        }

    route_record = {
        "schema_version": "text2ifc/repair-route/1.0",
        "case_id": case_id,
        "route": route["route"],
        "valid": valid,
        "provider_call_count": provider_call_count,
        "repair_attempts": list(route.get("repair_attempts", [])),
        "source_generator_response_id": source_metrics.get("response_id"),
        "source_generator_dir": portable_artifact_path(source),
        "validation_issue_count": len(validation_issues),
        "repair_diagnostics": repair_diagnostics,
        "fact_delta": "fact-delta.json" if fact_delta is not None else None,
        **{
            key: value
            for key, value in route.items()
            if key not in {"route", "repair_attempts"}
        },
    }
    _write_json(output / "route.json", route_record)
    _write_json(output / "repair-attempts.json", route_record["repair_attempts"])

    metrics = {
        "case_id": case_id,
        "stage": "repair",
        "route": route_record["route"],
        "valid": valid,
        "evidence_class": evidence_class,
        "provider_call_count": provider_call_count,
        "repair_attempt_count": len(route_record["repair_attempts"]),
        "source_generator_response_id": source_metrics.get("response_id"),
        "source_generator_evidence_class": source_metrics.get("evidence_class"),
        "source_generator_contract_valid": source_metrics.get("contract_valid"),
        "repair_diagnostic_count": len(repair_diagnostics),
        "repaired_artifact": repaired_artifact_name,
        "fact_delta_valid": fact_delta.get("valid") if fact_delta else None,
    }
    _write_json(output / "metrics.json", metrics)
    _write_json(
        output / "trace-manifest.json",
        {
            "schema_version": "text2ifc/live-stage-trace/1.0",
            "case_id": case_id,
            "stage": "repair",
            "template_id": REPAIR_TEMPLATE_ID,
            "source_generator": portable_artifact_path(source),
            "provider": provider_manifest,
            "provider_call_count": provider_call_count,
            "artifacts": {
                "input": "input.txt",
                "conversation": "conversation.json",
                "design_brief": "design-brief.json",
                "candidate": "candidate.json" if candidate is not None else None,
                "source_validation": "source-validation.json",
                "renderer_inputs": (
                    "prompt-render-input.json" if provider_call_count else None
                ),
                "rendered_prompt": (
                    "prompt-rendered.md" if provider_call_count else None
                ),
                "model_text": "model-text.txt" if provider_call_count else None,
                "parsed_output": "parsed-output.json" if repaired_document else None,
                "repaired_document": repaired_artifact_name,
                "fact_delta": "fact-delta.json" if fact_delta is not None else None,
                "route": "route.json",
                "repair_attempts": "repair-attempts.json",
                "metrics": "metrics.json",
            },
        },
    )
    return {
        "case_id": case_id,
        "stage": "repair",
        "route": route_record["route"],
        "valid": valid,
        "provider_call_count": provider_call_count,
        "repair_attempts": route_record["repair_attempts"],
        "evidence_class": evidence_class,
        "source_generator_response_id": source_metrics.get("response_id"),
        "output_dir": portable_artifact_path(output),
    }


def run_audit_report_stage(
    *,
    provider: Any,
    case_dir: Path | str,
    case_id: str,
    session_prefix: str = "phase6.1",
) -> dict[str, Any]:
    """Run real Audit v2 and generate the case report from sidecars."""
    root = Path(case_dir)
    output = root / "audit"
    output.mkdir(parents=True, exist_ok=True)
    design = resolve_final_design_brief_dir(root)
    generator = root / "generator"
    repair = root / "repair"
    user_request = (design / "input.txt").read_text(encoding="utf-8").rstrip("\r\n")
    conversation = json.loads(
        (design / "conversation.json").read_text(encoding="utf-8")
    )
    design_brief = json.loads(
        (design / "design-brief.json").read_text(encoding="utf-8")
    )
    terminal_document_path = _first_existing_path(
        generator,
        ("candidate.json", "draft.json", "parsed-output.json"),
    )
    if terminal_document_path is None:
        raise ValueError("Audit requires a terminal Generator document")
    terminal_document = json.loads(terminal_document_path.read_text(encoding="utf-8"))
    generator_validation = json.loads(
        (generator / "validation.json").read_text(encoding="utf-8")
    )
    generator_metrics = json.loads(
        (generator / "metrics.json").read_text(encoding="utf-8")
    )
    repair_route = json.loads((repair / "route.json").read_text(encoding="utf-8"))
    repair_metrics = json.loads((repair / "metrics.json").read_text(encoding="utf-8"))
    deterministic_gates = {
        "bim_json_validation": bool(generator_validation.get("valid")),
        "repair_route_terminal": repair_route.get("route")
        in {"no_repair_needed", "repair_attempted", "draft_required"},
    }
    evidence_paths = _audit_evidence_paths(root)
    renderer_inputs = {
        "USER_REQUEST": user_request,
        "CONVERSATION": conversation,
        "DESIGN_BRIEF": design_brief,
        "TERMINAL_DOCUMENT": terminal_document,
        "DETERMINISTIC_GATES": deterministic_gates,
        "REPAIR_ROUTE": repair_route,
        "METRICS": {
            "generator": generator_metrics,
            "repair": repair_metrics,
        },
        "EVIDENCE_PATHS": evidence_paths,
    }
    rendered = render_prompt(template_id=AUDIT_TEMPLATE_ID, inputs=renderer_inputs)
    _write_json(output / "prompt-render-input.json", renderer_inputs)
    _write_text(output / "prompt-rendered.md", rendered["text"])
    result = provider.generate_live(
        session_id=f"{session_prefix}-{case_id}-audit-01",
        prompt=rendered["text"],
        schema={"schema_version": "text2ifc/audit/2.0"},
        state={"case_id": case_id, "stage": "audit"},
    )
    validate_provider_output(result.output)
    provider_manifest = write_live_trace(result=result, output_dir=output)
    parse_status, parsed, normalization_diagnostics = result.output.parse_json()
    issues: list[dict[str, Any]] = []
    if parse_status == "ok" and parsed is not None:
        _write_json(output / "parsed-output.json", parsed)
        issues = _validate_live_audit_output(
            parsed,
            case_dir=root,
            deterministic_gates=deterministic_gates,
        )
    else:
        issues = list(normalization_diagnostics)
    schema_semantic_valid = parse_status == "ok" and parsed is not None and not issues
    strict_output_contract_valid = (
        parse_status == "ok" and not normalization_diagnostics
    )
    valid = schema_semantic_valid and strict_output_contract_valid
    if parsed is not None:
        _write_json(output / "audit-report.json", parsed)
    _write_json(
        output / "validation.json",
        {"valid": valid, "issue_count": len(issues), "issues": issues},
    )
    metrics = {
        "case_id": case_id,
        "stage": "audit",
        "valid": valid,
        "evidence_class": result.evidence_class,
        "response_id": result.response.get("id"),
        "model": result.response.get("model"),
        "stop_reason": result.response.get("stop_reason"),
        "usage": dict(result.response.get("usage", {})),
        "normalization_diagnostics": normalization_diagnostics,
        "schema_semantic_valid": schema_semantic_valid,
        "strict_output_contract_valid": strict_output_contract_valid,
        "issue_count": len(issues),
    }
    _write_json(output / "metrics.json", metrics)
    _write_json(
        output / "trace-manifest.json",
        {
            "schema_version": "text2ifc/live-stage-trace/1.0",
            "case_id": case_id,
            "stage": "audit",
            "template_id": rendered["metadata"]["template_id"],
            "template_hash": rendered["metadata"]["template_hash"],
            "provider": provider_manifest,
            "evidence_paths": evidence_paths,
            "artifacts": {
                "renderer_inputs": "prompt-render-input.json",
                "rendered_prompt": "prompt-rendered.md",
                "model_text": "model-text.txt",
                "parsed_output": "parsed-output.json" if parsed else None,
                "audit_report": "audit-report.json" if parsed else None,
                "validation": "validation.json",
                "metrics": "metrics.json",
            },
        },
    )
    report_path = build_live_run_report(case_dir=root)
    return {
        "case_id": case_id,
        "stage": "audit-report",
        "status": (
            "blocked_output_contract"
            if schema_semantic_valid and not strict_output_contract_valid
            else "accepted"
            if valid and parsed and not parsed.get("blocking")
            else "blocked"
        ),
        "valid": valid,
        "response_id": result.response.get("id"),
        "evidence_class": result.evidence_class,
        "report_path": portable_artifact_path(report_path),
        "output_dir": portable_artifact_path(root),
    }


def run_final_acceptance_stage(
    *,
    case_dir: Path | str,
    output_dir: Path | str,
    case_id: str,
) -> dict[str, Any]:
    """Compile the accepted live Formal candidate to the canonical IFC artifact."""
    case_root = Path(case_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate_path = case_root / "generator" / "candidate.json"
    audit_report_path = case_root / "audit" / "audit-report.json"
    audit_metrics_path = case_root / "audit" / "metrics.json"
    if not candidate_path.is_file():
        raise ValueError("Final acceptance requires generator/candidate.json")
    if not audit_report_path.is_file() or not audit_metrics_path.is_file():
        raise ValueError("Final acceptance requires accepted audit artifacts")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
    audit_metrics = json.loads(audit_metrics_path.read_text(encoding="utf-8"))
    if audit_report.get("blocking") is not False or audit_report.get("recommendation") != "accept":
        raise ValueError("Final acceptance requires a non-blocking accepted audit")
    if audit_metrics.get("strict_output_contract_valid") is not True:
        raise ValueError("Final acceptance requires strict Audit output contract")

    output_ifc = output / "output.ifc"
    compilation = compile_document(candidate, output_ifc)
    ifc_verification = {
        "success": compilation.success,
        "output_path": str(output_ifc) if compilation.success else None,
        "input_issues": [_issue_to_dict(issue) for issue in compilation.input_issues],
        "ifc_issues": [_issue_to_dict(issue) for issue in compilation.ifc_issues],
    }
    _write_json(output / "ifc-verification.json", ifc_verification)

    expectation = _wall_geometry_expectation_from_candidate(case_id, candidate)
    _write_json(output / "geometry-expectation.json", expectation)
    if compilation.success:
        quality = check_generated_ifc(output_ifc, expectation)
        geometry_feedback = {
            "success": quality.success,
            "issues": quality.issues,
            "metrics": quality.metrics,
        }
    else:
        geometry_feedback = {
            "success": False,
            "issues": [
                {
                    "code": "COMPILE_REOPEN_FAILED",
                    "path": "/output.ifc",
                    "message": "IFC compilation or reopen verification failed.",
                }
            ],
            "metrics": {},
        }
    _write_json(output / "geometry-feedback.json", geometry_feedback)

    secret_scan = scan_path(output)
    _write_json(output / "secret-scan.json", secret_scan)
    metrics = {
        "case_id": case_id,
        "stage": "final-acceptance",
        "valid": bool(
            compilation.success
            and geometry_feedback["success"]
            and secret_scan["finding_count"] == 0
        ),
        "compile_reopen_success": compilation.success,
        "geometry_success": geometry_feedback["success"],
        "secret_finding_count": secret_scan["finding_count"],
        "audit_response_id": audit_metrics.get("response_id"),
        "audit_evidence_class": audit_metrics.get("evidence_class"),
        "audit_strict_output_contract_valid": audit_metrics.get(
            "strict_output_contract_valid"
        ),
        "source_case_dir": portable_artifact_path(case_root),
        "ifc_path": "output.ifc" if compilation.success else None,
    }
    _write_json(output / "acceptance-metrics.json", metrics)
    _write_final_report(
        output / "report.md",
        case_id=case_id,
        case_dir=case_root,
        metrics=metrics,
        ifc_verification=ifc_verification,
        geometry_feedback=geometry_feedback,
        secret_scan=secret_scan,
    )
    return {
        "case_id": case_id,
        "stage": "final-acceptance",
        "valid": metrics["valid"],
        "ifc_path": str(output_ifc),
        "report_path": str(output / "report.md"),
        "output_dir": str(output),
        "compile_reopen_success": compilation.success,
        "geometry_success": geometry_feedback["success"],
        "secret_finding_count": secret_scan["finding_count"],
    }


def _select_generator_context(design_context: dict[str, Any]) -> dict[str, Any]:
    capabilities = [
        record
        for record in design_context.get("evidence", [])
        if isinstance(record, dict)
        and record.get("kind") == "ifc_generation_capability"
    ]
    example = json.loads(GENERATOR_FEW_SHOT_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": "text2ifc/generator-context/1.0",
        "capability_profile": capabilities,
        "few_shots": [
            {
                "few_shot_id": "generator-v2.formal-rectangular-room",
                "condition": (
                    "A complete rectangular room request needs a Formal semantic "
                    "graph; example values are not defaults and must not be copied."
                ),
                "source_path": portable_artifact_path(GENERATOR_FEW_SHOT_PATH),
                "source_sha256": _file_sha256(GENERATOR_FEW_SHOT_PATH),
                "output": example,
            }
        ],
    }


def _repair_allowed_change_paths(
    validation_issues: list[dict[str, Any]],
) -> list[str]:
    paths: list[str] = []
    for issue in validation_issues:
        issue_path = issue.get("path")
        if isinstance(issue_path, str) and issue_path:
            paths.append(issue_path)
        for fact_path in issue.get("required_fact_paths", []):
            if isinstance(fact_path, str) and fact_path:
                paths.append(fact_path)
    return sorted(set(paths))


def _repair_evidence_by_path(
    validation_issues: list[dict[str, Any]],
    allowed_change_paths: list[str],
) -> dict[str, list[str]]:
    by_path = {path: ["schema:bim-json-v2"] for path in allowed_change_paths}
    for issue in validation_issues:
        code = str(issue.get("code", "UNKNOWN"))
        issue_path = issue.get("path")
        if isinstance(issue_path, str) and issue_path:
            by_path.setdefault(issue_path, ["schema:bim-json-v2"]).append(
                f"validation:{code}"
            )
    return by_path


def _audit_evidence_paths(root: Path) -> list[str]:
    design = resolve_final_design_brief_dir(root)
    design_relative = design.relative_to(root).as_posix()
    paths = [
        f"{design_relative}/input.txt",
        f"{design_relative}/conversation.json",
        f"{design_relative}/design-brief.json",
        f"{design_relative}/response.raw.json",
        "generator/candidate.json",
        "generator/validation.json",
        "generator/metrics.json",
        "repair/route.json",
        "repair/metrics.json",
    ]
    return [path for path in paths if (root / path).is_file()]


def _validate_live_audit_output(
    payload: dict[str, Any],
    *,
    case_dir: Path,
    deterministic_gates: dict[str, bool],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if payload.get("schema_version") != "text2ifc/audit/2.0":
        issues.append(
            {
                "code": "UNSUPPORTED_AUDIT_VERSION",
                "path": "/schema_version",
                "message": "Audit output must use text2ifc/audit/2.0.",
            }
        )
    if payload.get("recommendation") not in {"accept", "revise", "reject"}:
        issues.append(
            {
                "code": "INVALID_AUDIT_RECOMMENDATION",
                "path": "/recommendation",
                "message": "Audit recommendation is not canonical.",
            }
        )
    if not all(deterministic_gates.values()) and payload.get("blocking") is False:
        issues.append(
            {
                "code": "DETERMINISTIC_GATE_OVERRIDE",
                "path": "/blocking",
                "message": "Audit cannot pass failed deterministic gates.",
            }
        )
    evidence_paths = payload.get("evidence_paths", [])
    if not isinstance(evidence_paths, list):
        issues.append(
            {
                "code": "INVALID_AUDIT_EVIDENCE_PATHS",
                "path": "/evidence_paths",
                "message": "Audit evidence_paths must be a list.",
            }
        )
        return issues
    for index, relative in enumerate(evidence_paths):
        if not isinstance(relative, str) or not (case_dir / relative).is_file():
            issues.append(
                {
                    "code": "AUDIT_EVIDENCE_PATH_MISSING",
                    "path": f"/evidence_paths/{index}",
                    "message": f"Audit evidence path does not exist: {relative!r}.",
                }
            )
    return issues


def _wall_geometry_expectation_from_candidate(
    case_id: str,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    walls = {}
    for entity in candidate.get("entities", []):
        if not isinstance(entity, dict) or not str(entity.get("id", "")).startswith("wall-"):
            continue
        attributes = entity.get("attributes", {})
        placement = attributes.get("ObjectPlacement", {})
        representation = attributes.get("Representation", {})
        profile = representation.get("profile", {})
        origin = placement.get("origin", [0, 0, 0])
        ref_direction = placement.get("ref_direction", [1, 0, 0])
        length_mm = float(profile.get("x", 0))
        thickness_mm = float(profile.get("y", 0))
        depth_mm = float(representation.get("depth", 0))
        origin_x = float(origin[0])
        origin_y = float(origin[1])
        origin_z = float(origin[2]) if len(origin) > 2 else 0.0
        axis = "y" if abs(float(ref_direction[1])) > abs(float(ref_direction[0])) else "x"
        if axis == "x":
            bbox = {
                "x": _metre_range(origin_x - length_mm / 2, origin_x + length_mm / 2),
                "y": _metre_range(origin_y - thickness_mm / 2, origin_y + thickness_mm / 2),
                "z": _metre_range(origin_z, origin_z + depth_mm),
            }
        else:
            bbox = {
                "x": _metre_range(origin_x - thickness_mm / 2, origin_x + thickness_mm / 2),
                "y": _metre_range(origin_y - length_mm / 2, origin_y + length_mm / 2),
                "z": _metre_range(origin_z, origin_z + depth_mm),
            }
        walls[str(entity["id"])] = {"axis": axis, "bbox": bbox}
    return {
        "case_id": case_id,
        "tolerance": 0.05,
        "units": "METRE",
        "walls": walls,
    }


def _metre_range(start_mm: float, end_mm: float) -> list[float]:
    return [round(start_mm / 1000, 6), round(end_mm / 1000, 6)]


def _write_final_report(
    path: Path,
    *,
    case_id: str,
    case_dir: Path,
    metrics: dict[str, Any],
    ifc_verification: dict[str, Any],
    geometry_feedback: dict[str, Any],
    secret_scan: dict[str, Any],
) -> None:
    case_link = f"{case_id}/report.md"
    lines = [
        "# Phase 6.1 Final Acceptance Report",
        "",
        "Generated from live trace sidecars and deterministic IFC gates.",
        "",
        "## Accepted Live Case",
        "",
        f"- case_id: `{case_id}`",
        f"- source_case_dir: `{portable_artifact_path(case_dir)}`",
        f"- case_report: [{case_link}]({case_link})",
        "",
        "## Final IFC",
        "",
        "- [output.ifc](output.ifc)",
        "- [ifc-verification.json](ifc-verification.json)",
        "- [geometry-feedback.json](geometry-feedback.json)",
        "",
        "## Acceptance Metrics",
        "",
        "```json",
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## IFC Verification",
        "",
        "```json",
        json.dumps(ifc_verification, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Geometry Feedback",
        "",
        "```json",
        json.dumps(geometry_feedback, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Secret Scan",
        "",
        "```json",
        json.dumps(secret_scan, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ]
    _write_text(path, "\n".join(lines))


def _issue_to_dict(issue: Any) -> dict[str, Any]:
    return {
        "code": getattr(issue, "code", ""),
        "path": getattr(issue, "path", getattr(issue, "entity", "")),
        "message": getattr(issue, "message", str(issue)),
    }


def _first_existing_path(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = root / name
        if path.is_file():
            return path
    return None


def compare_design_brief_runs(
    *,
    v1_dir: Path | str,
    v2_dir: Path | str,
    output_path: Path | str,
) -> dict[str, Any]:
    """Compare v1/v2 from persisted traces without semantic overrides."""
    baseline = Path(v1_dir)
    current = Path(v2_dir)
    v1_text_path = baseline / "model-text.txt"
    v1_metadata_path = baseline / "response-metadata.json"
    v1_text = v1_text_path.read_text(encoding="utf-8")
    from .providers import ProviderOutput

    v1_parse_status, v1_payload, v1_normalization = ProviderOutput(
        text=v1_text,
        metadata={},
    ).parse_json()
    v1_issues = (
        validate_design_brief(v1_payload)
        if v1_parse_status == "ok" and v1_payload is not None
        else []
    )
    v1_metadata = json.loads(v1_metadata_path.read_text(encoding="utf-8"))
    v2_metrics = json.loads((current / "metrics.json").read_text(encoding="utf-8"))
    v2_validation = json.loads(
        (current / "validation.json").read_text(encoding="utf-8")
    )
    v2_manifest = json.loads(
        (current / "trace-manifest.json").read_text(encoding="utf-8")
    )
    evidence_valid = _trace_evidence_is_current(v2_manifest)

    v1_record = {
        "source_dir": portable_artifact_path(baseline),
        "model_text_sha256": _file_sha256(v1_text_path),
        "metadata_sha256": _file_sha256(v1_metadata_path),
        "response_id": v1_metadata.get("response_id", v1_metadata.get("id")),
        "model": v1_metadata.get("model"),
        "stop_reason": v1_metadata.get("stop_reason"),
        "parse_valid": v1_parse_status == "ok",
        "schema_semantic_valid": v1_parse_status == "ok" and not v1_issues,
        "normalization_codes": [
            item.get("code") for item in v1_normalization if item.get("code")
        ],
        "question_count": (
            len(v1_payload.get("clarification_questions", []))
            if isinstance(v1_payload, dict)
            else None
        ),
        "evidence_valid": False,
        "design_status": None,
    }
    v2_record = {
        "source_dir": portable_artifact_path(current),
        "trace_manifest_sha256": _file_sha256(current / "trace-manifest.json"),
        "response_id": v2_metrics.get("response_id"),
        "model": v2_metrics.get("model"),
        "stop_reason": v2_metrics.get("stop_reason"),
        "parse_valid": bool(v2_metrics.get("parse_valid")),
        "schema_semantic_valid": bool(v2_validation.get("valid")),
        "strict_output_contract_valid": bool(
            v2_metrics.get("strict_output_contract_valid")
        ),
        "normalization_codes": [
            item.get("code")
            for item in v2_metrics.get("normalization_diagnostics", [])
            if isinstance(item, dict) and item.get("code")
        ],
        "question_count": v2_metrics.get("question_count"),
        "evidence_valid": evidence_valid,
        "design_status": v2_metrics.get("design_status"),
    }

    improvements: list[str] = []
    regressions: list[str] = []
    if v1_record["normalization_codes"] and not v2_record["normalization_codes"]:
        improvements.append("bare_json_without_outer_markdown_fence")
    if not v1_record["evidence_valid"] and v2_record["evidence_valid"]:
        improvements.append("hash_verified_evidence_grounding")
    if _lower_number(v2_record["question_count"], v1_record["question_count"]):
        improvements.append("fewer_clarification_questions")

    if v1_record["parse_valid"] and not v2_record["parse_valid"]:
        regressions.append("parse_validity_regressed")
    if v1_record["schema_semantic_valid"] and not v2_record["schema_semantic_valid"]:
        regressions.append("schema_semantic_validity_regressed")
    if _higher_number(v2_record["question_count"], v1_record["question_count"]):
        regressions.append("clarification_question_count_increased")
    if not v2_record["evidence_valid"]:
        regressions.append("v2_evidence_hash_or_path_invalid")
    if not v2_record["strict_output_contract_valid"]:
        regressions.append("strict_output_contract_violated")

    comparison = {
        "schema_version": "text2ifc/design-brief-comparison/1.0",
        "comparison_basis": "persisted_trace_artifacts_only",
        "v1": v1_record,
        "v2": v2_record,
        "improvements": improvements,
        "regressions": regressions,
    }
    _write_json(Path(output_path), comparison)
    return comparison


def _trace_evidence_is_current(manifest: dict[str, Any]) -> bool:
    evidence = manifest.get("selected_evidence", [])
    if not isinstance(evidence, list) or not evidence:
        return False
    for record in evidence:
        if not isinstance(record, dict):
            return False
        source_path = PROJECT_ROOT / str(record.get("source_path", ""))
        if not source_path.is_file():
            return False
        if record.get("source_sha256") != _file_sha256(source_path):
            return False
    return True


def _file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def portable_artifact_path(path: Path | str) -> str:
    """Return repository-relative paths when the artifact is in this worktree."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _lower_number(left: Any, right: Any) -> bool:
    return isinstance(left, int) and isinstance(right, int) and left < right


def _higher_number(left: Any, right: Any) -> bool:
    return isinstance(left, int) and isinstance(right, int) and left > right


def _write_json(path: Path, payload: Any) -> None:
    _write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _append_event(path: Path, payload: dict[str, Any]) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
