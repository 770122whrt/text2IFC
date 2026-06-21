"""Registry-rendered BIM JSON generation through provider adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.validation import ValidationIssue
from text2ifc_contract.validation_v2 import validate_v2_document

from .design_brief import validate_design_brief
from .prompt_registry import render_prompt, validate_prompt_trace


class AgentProvider(Protocol):
    def generate_candidate(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> Any: ...


@dataclass(frozen=True)
class GenerationResult:
    status: str
    document: dict[str, Any] | None
    diagnostics: list[dict[str, str]]
    prompt_trace: dict[str, Any]
    rendered_prompt: str
    raw_response: str
    provider_metadata: dict[str, Any]


def generate_bim_json_candidate(
    *,
    session_id: str,
    provider: AgentProvider,
    design_brief: dict[str, Any],
    schema_summary: dict[str, Any],
    capability_profile: dict[str, Any],
    few_shots: list[Any],
    validation_feedback: list[dict[str, Any]],
    geometry_feedback: list[dict[str, Any]],
    trace_paths: Mapping[str, Any],
    template_id: str = "bim-json-generator.v1",
) -> GenerationResult:
    """Render, call, parse, and validate one BIM JSON provider response."""
    brief_issues = validate_design_brief(design_brief)
    if brief_issues:
        raise ValueError("Design Brief must validate before BIM JSON generation")

    rendered = render_prompt(
        template_id=template_id,
        inputs={
            "DESIGN_BRIEF": design_brief,
            "SCHEMA_SUMMARY": schema_summary,
            "CAPABILITY_PROFILE": capability_profile,
            "FEW_SHOTS": few_shots,
            "VALIDATION_FEEDBACK": validation_feedback,
            "GEOMETRY_FEEDBACK": geometry_feedback,
        },
    )
    prompt_trace = {**dict(trace_paths), **rendered["metadata"]}
    validate_prompt_trace(prompt_trace)

    output = provider.generate_candidate(
        session_id=session_id,
        prompt=rendered["text"],
        schema=schema_summary,
        state=design_brief,
    )
    parse_status, document, parse_diagnostics = output.parse_json()
    if parse_status != "ok" or document is None:
        return _result(
            status="invalid",
            document=None,
            diagnostics=parse_diagnostics,
            prompt_trace=prompt_trace,
            rendered=rendered["text"],
            output=output,
        )

    if document.get("draft_version") == "bim-json-draft/1.0":
        issues = validate_draft(document)
        status = "draft" if not issues else "invalid"
    else:
        issues = validate_v2_document(document)
        status = "formal" if not issues else "invalid"
    return _result(
        status=status,
        document=document,
        diagnostics=[_issue_payload(issue) for issue in issues],
        prompt_trace=prompt_trace,
        rendered=rendered["text"],
        output=output,
    )


def _result(
    *,
    status: str,
    document: dict[str, Any] | None,
    diagnostics: list[dict[str, str]],
    prompt_trace: dict[str, Any],
    rendered: str,
    output: Any,
) -> GenerationResult:
    return GenerationResult(
        status=status,
        document=document,
        diagnostics=diagnostics,
        prompt_trace=prompt_trace,
        rendered_prompt=rendered,
        raw_response=output.text,
        provider_metadata=dict(output.metadata),
    )


def _issue_payload(issue: ValidationIssue) -> dict[str, str]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}
