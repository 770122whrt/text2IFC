"""Provider-independent natural-language to semantic patch handoff."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from text2ifc_agent.providers import ProviderOutputError

from .composer import compose_patches
from .validation import load_patch_schema, validate_patch_document


ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = ROOT / "prompts" / "jsonfix" / "semantic-patch-v1.md"
FEW_SHOT_PATH = (
    ROOT / "prompts" / "jsonfix" / "semantic-patch-fewshot.md"
)


@dataclass(frozen=True)
class RepairHandoffResult:
    status: str
    patch: dict[str, Any] | None
    document: dict[str, Any] | None
    diagnostics: tuple[dict[str, Any], ...]
    provider_metadata: dict[str, Any]
    prompt: str

    @property
    def success(self) -> bool:
        return self.status == "formal_ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "patch": self.patch,
            "document": self.document,
            "diagnostics": list(self.diagnostics),
            "provider_metadata": copy.deepcopy(self.provider_metadata),
        }


def _render_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )


def render_repair_prompt(
    *,
    user_request: str,
    base_document: dict[str, Any],
    validation_feedback: list[dict[str, Any]] | None = None,
) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    few_shot = FEW_SHOT_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{USER_REQUEST}}": user_request,
        "{{BASE_DOCUMENT_ID}}": str(
            base_document.get("provenance", {}).get("document_id", "")
        ),
        "{{BASE_DOCUMENT_SUMMARY}}": _render_json(base_document),
        "{{VALIDATION_FEEDBACK}}": _render_json(
            validation_feedback or []
        ),
        "{{PATCH_SCHEMA}}": _render_json(load_patch_schema()),
        "{{FEW_SHOT_EXAMPLES}}": few_shot,
    }
    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def _issue_dict(issue: Any) -> dict[str, Any]:
    return {
        "code": issue.code,
        "path": issue.path,
        "message": issue.message,
    }


def _contains_missing(patch: dict[str, Any]) -> bool:
    return any(
        operation["op"] == "mark_missing"
        for layer in patch["layers"]
        for operation in layer["operations"]
    )


def run_repair_handoff(
    *,
    provider: Any,
    session_id: str,
    user_request: str,
    base_document: dict[str, Any],
    validation_feedback: list[dict[str, Any]] | None = None,
) -> RepairHandoffResult:
    prompt = render_repair_prompt(
        user_request=user_request,
        base_document=base_document,
        validation_feedback=validation_feedback,
    )
    schema = load_patch_schema()
    try:
        output = provider.generate_candidate(
            session_id=session_id,
            prompt=prompt,
            schema=schema,
            state={
                "base_document_id": base_document.get(
                    "provenance", {}
                ).get("document_id"),
                "target_schema_version": "bim-json/2.0",
                "target_ifc_schema": "IFC2X3",
            },
        )
    except ProviderOutputError as exc:
        return RepairHandoffResult(
            status="provider_error",
            patch=None,
            document=None,
            diagnostics=(
                {
                    "code": "PROVIDER_OUTPUT_REJECTED",
                    "path": "/provider",
                    "message": str(exc),
                },
            ),
            provider_metadata={},
            prompt=prompt,
        )

    parse_status, payload, parse_diagnostics = output.parse_json()
    if parse_status != "ok" or payload is None:
        return RepairHandoffResult(
            status="provider_parse_error",
            patch=None,
            document=None,
            diagnostics=tuple(parse_diagnostics),
            provider_metadata=copy.deepcopy(output.metadata),
            prompt=prompt,
        )

    patch_issues = validate_patch_document(payload)
    if patch_issues:
        return RepairHandoffResult(
            status="patch_invalid",
            patch=payload,
            document=None,
            diagnostics=tuple(_issue_dict(issue) for issue in patch_issues),
            provider_metadata=copy.deepcopy(output.metadata),
            prompt=prompt,
        )

    composition = compose_patches(base_document, [payload])
    diagnostics = tuple(
        item.to_dict() for item in composition.diagnostics
    )
    if not composition.valid:
        return RepairHandoffResult(
            status="composition_invalid",
            patch=payload,
            document=composition.document,
            diagnostics=diagnostics,
            provider_metadata=copy.deepcopy(output.metadata),
            prompt=prompt,
        )
    return RepairHandoffResult(
        status="draft" if _contains_missing(payload) else "formal_ready",
        patch=payload,
        document=composition.document,
        diagnostics=diagnostics,
        provider_metadata=copy.deepcopy(output.metadata),
        prompt=prompt,
    )
