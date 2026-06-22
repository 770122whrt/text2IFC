"""Auditable live-provider orchestration for Phase 6.1."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .context_selection import select_design_brief_context
from .design_brief import load_design_brief_schema, validate_design_brief
from .live_trace import write_live_trace
from .prompt_registry import render_prompt


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
        template_id="design-brief.v2",
        inputs=renderer_inputs,
    )

    _write_text(output / "input.txt", user_request + "\n")
    _write_json(output / "conversation.json", conversation)
    _write_json(output / "context-selection.json", selection)
    _write_json(output / "prompt-render-input.json", renderer_inputs)
    _write_text(output / "prompt-rendered.md", rendered["text"])

    result = provider.generate_live(
        session_id=f"phase6.1-{case['case_id']}-design-brief-v2",
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
    valid = parse_status == "ok" and not serialized_issues
    validation = {
        "valid": valid,
        "issue_count": len(serialized_issues),
        "issues": serialized_issues,
    }
    _write_json(output / "validation.json", validation)

    if valid and parsed is not None:
        _write_json(output / "design-brief.json", parsed)
        stage_status = str(parsed["status"])
    else:
        stage_status = "blocked_prompt_defect"

    metrics = {
        "case_id": case["case_id"],
        "stage": "design-brief",
        "evidence_class": result.evidence_class,
        "parse_valid": parse_status == "ok",
        "schema_semantic_valid": valid,
        "normalization_diagnostics": parse_diagnostics,
        "response_id": result.response.get("id"),
        "model": result.response.get("model"),
        "stop_reason": result.response.get("stop_reason"),
        "usage": dict(result.response.get("usage", {})),
        "design_status": parsed.get("status") if valid and parsed else None,
        "question_count": (
            len(parsed.get("clarification_questions", []))
            if valid and parsed
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
            "design_brief": "design-brief.json" if valid else None,
            "validation": "validation.json",
            "metrics": "metrics.json",
        },
    }
    _write_json(output / "trace-manifest.json", trace_manifest)
    return {
        "case_id": case["case_id"],
        "stage": "design-brief",
        "status": stage_status,
        "valid": valid,
        "output_dir": str(output),
        "response_id": result.response.get("id"),
    }


def _write_json(path: Path, payload: Any) -> None:
    _write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
