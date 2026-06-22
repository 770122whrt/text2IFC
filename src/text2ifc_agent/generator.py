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
    classification: str
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
            classification="unparsed",
            document=None,
            diagnostics=parse_diagnostics,
            prompt_trace=prompt_trace,
            rendered=rendered["text"],
            output=output,
        )

    classification, discriminator_diagnostics = _classify_document(document)
    if classification == "unknown_contract":
        return _result(
            status="blocked_failure",
            classification=classification,
            document=document,
            diagnostics=[*parse_diagnostics, *discriminator_diagnostics],
            prompt_trace=prompt_trace,
            rendered=rendered["text"],
            output=output,
        )
    if classification == "draft":
        issues = validate_draft(document)
        status = "draft" if not issues else "invalid"
    else:
        issues = validate_v2_document(document)
        status = "formal" if not issues else "invalid"
    return _result(
        status=status,
        classification=classification,
        document=document,
        diagnostics=[
            *parse_diagnostics,
            *[_issue_payload(issue) for issue in issues],
        ],
        prompt_trace=prompt_trace,
        rendered=rendered["text"],
        output=output,
    )


def _result(
    *,
    status: str,
    classification: str,
    document: dict[str, Any] | None,
    diagnostics: list[dict[str, str]],
    prompt_trace: dict[str, Any],
    rendered: str,
    output: Any,
) -> GenerationResult:
    return GenerationResult(
        status=status,
        classification=classification,
        document=document,
        diagnostics=diagnostics,
        prompt_trace=prompt_trace,
        rendered_prompt=rendered,
        raw_response=output.text,
        provider_metadata=dict(output.metadata),
    )


def _issue_payload(issue: ValidationIssue) -> dict[str, str]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _classify_document(
    document: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    has_formal = "schema_version" in document
    has_draft = "draft_version" in document
    if has_formal and has_draft:
        return (
            "unknown_contract",
            [
                _diagnostic(
                    "CONFLICTING_OUTPUT_DISCRIMINATORS",
                    "",
                    "Output contains both schema_version and draft_version.",
                )
            ],
        )
    if has_draft:
        draft_version = document.get("draft_version")
        if draft_version != "bim-json-draft/1.0":
            return (
                "unknown_contract",
                [
                    _diagnostic(
                        "UNKNOWN_DRAFT_VERSION",
                        "/draft_version",
                        f"Unknown Draft version: {draft_version!r}.",
                    )
                ],
            )
        target_version = document.get("target_schema_version")
        if target_version != "bim-json/2.0":
            return (
                "unknown_contract",
                [
                    _diagnostic(
                        "INVALID_DRAFT_TARGET_VERSION",
                        "/target_schema_version",
                        f"Draft target must be 'bim-json/2.0', got {target_version!r}.",
                    )
                ],
            )
        return "draft", []
    if has_formal:
        formal_version = document.get("schema_version")
        if formal_version != "bim-json/2.0":
            return (
                "unknown_contract",
                [
                    _diagnostic(
                        "UNKNOWN_FORMAL_VERSION",
                        "/schema_version",
                        f"Unknown Formal version: {formal_version!r}.",
                    )
                ],
            )
        return "formal", []
    return (
        "unknown_contract",
        [
            _diagnostic(
                "MISSING_OUTPUT_DISCRIMINATOR",
                "",
                "Output must contain exactly one canonical version discriminator.",
            )
        ],
    )


def _diagnostic(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}
