"""Auditable live-provider orchestration for Phase 6.1."""

from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .context_selection import select_design_brief_context
from .design_brief import load_design_brief_schema, validate_design_brief
from .live_trace import write_live_trace
from .prompt_registry import render_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_BRIEF_TEMPLATE_ID = "design-brief.v2.1"


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
        template_id=DESIGN_BRIEF_TEMPLATE_ID,
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
