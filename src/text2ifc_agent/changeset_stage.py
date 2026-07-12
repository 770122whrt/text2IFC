"""Provider-backed generation of one component-scoped BIM JSON ChangeSet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.schema import load_draft_schema

from .candidate_index import build_candidate_index
from .changesets import load_changeset_schema, validate_changeset
from .live_trace import write_live_trace
from .prompt_registry import render_prompt
from .providers import validate_provider_output


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHANGESET_TEMPLATE_ID = "bim-json-changeset.v1"
FEW_SHOT_PATHS = (
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-single-component.json",
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-coupled-dependency.json",
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-staged-package-add.json",
)


def run_changeset_stage(
    *,
    provider: Any,
    output_dir: Path | str,
    case_id: str,
    call_index: int,
    user_request: str,
    conversation: list[dict[str, Any]],
    design_brief: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
    candidate: Mapping[str, Any],
    base_revision: Mapping[str, Any],
    scope: Mapping[str, Any],
    issues: list[dict[str, Any]],
    context_issues: list[dict[str, Any]] | None = None,
    trace_level: str | None = "debug",
) -> dict[str, Any]:
    """Ask the provider for a ChangeSet or canonical Draft and validate its binding."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    changeset_schema = load_changeset_schema()
    draft_schema = load_draft_schema()
    renderer_inputs = {
        "USER_REQUEST": user_request,
        "CONVERSATION": conversation,
        "DESIGN_BRIEF": dict(design_brief),
        "EXPECTED_FACTS": dict(expected_facts),
        "SCOPED_COMPONENTS": _scoped_components(candidate, scope),
        "BASE_REVISION": dict(base_revision),
        "CHANGE_SCOPE": dict(scope),
        "ISSUES": issues,
        "CONTEXT_ISSUES": list(context_issues or []),
        "CHANGESET_SCHEMA": changeset_schema,
        "DRAFT_SCHEMA": draft_schema,
        "FEW_SHOTS": [_read_json(path) for path in FEW_SHOT_PATHS],
    }
    rendered = render_prompt(template_id=CHANGESET_TEMPLATE_ID, inputs=renderer_inputs)
    _write_json(output / "prompt-render-input.json", renderer_inputs)
    _write_text(output / "prompt-rendered.md", rendered["text"])

    result = provider.generate_live(
        session_id=f"phase6.5-{case_id}-changeset-{call_index:02d}",
        prompt=rendered["text"],
        schema=changeset_schema,
        state={"case_id": case_id, "stage": "changeset", "call_index": call_index},
    )
    validate_provider_output(result.output)
    provider_manifest = write_live_trace(
        result=result,
        output_dir=output,
        trace_level=trace_level,
        preserve_deep_evidence=trace_level == "compact",
    )
    parse_status, parsed, normalization_diagnostics = result.output.parse_json()
    diagnostics = list(normalization_diagnostics)
    classification = "invalid"
    artifact_name: str | None = None

    if parse_status != "ok" or parsed is None:
        diagnostics.append(
            _diagnostic("CHANGESET_OUTPUT_CONTRACT_ERROR", "/", "Output is not a JSON object.")
        )
    elif parsed.get("schema_version") == "text2ifc/bim-json-changeset/1.0":
        contract_issues = [_issue_payload(issue) for issue in validate_changeset(parsed)]
        diagnostics.extend(contract_issues)
        if not contract_issues:
            diagnostics.extend(_binding_diagnostics(parsed, base_revision, scope))
        if not diagnostics:
            classification = "changeset"
            artifact_name = "changeset.json"
    elif parsed.get("draft_version") == "bim-json-draft/1.0":
        diagnostics.extend(_issue_payload(issue) for issue in validate_draft(parsed))
        if not diagnostics:
            classification = "draft"
            artifact_name = "draft.json"
    else:
        diagnostics.append(
            _diagnostic(
                "CHANGESET_OUTPUT_CONTRACT_ERROR",
                "/",
                "Output must be a ChangeSet or canonical Draft Envelope.",
            )
        )

    if parsed is not None:
        _write_json(output / "parsed-output.json", parsed)
    if artifact_name is not None:
        _write_json(output / artifact_name, parsed)
    valid = artifact_name is not None
    _write_json(
        output / "validation.json",
        {"valid": valid, "issue_count": len(diagnostics), "issues": diagnostics},
    )
    metrics = {
        "case_id": case_id,
        "stage": "changeset",
        "call_index": call_index,
        "classification": classification,
        "valid": valid,
        "evidence_class": result.evidence_class,
        "response_id": result.response.get("id"),
        "model": result.response.get("model"),
        "stop_reason": result.response.get("stop_reason"),
        "usage": dict(result.response.get("usage", {})),
        "normalization_diagnostics": normalization_diagnostics,
        "issue_count": len(diagnostics),
    }
    _write_json(output / "metrics.json", metrics)
    _write_json(
        output / "trace-manifest.json",
        {
            "schema_version": "text2ifc/live-stage-trace/1.0",
            "case_id": case_id,
            "stage": "changeset",
            "template_id": rendered["metadata"]["template_id"],
            "template_hash": rendered["metadata"]["template_hash"],
            "provider": provider_manifest,
            "artifacts": {
                "renderer_inputs": "prompt-render-input.json",
                "rendered_prompt": "prompt-rendered.md",
                "parsed_output": "parsed-output.json" if parsed is not None else None,
                "accepted_document": artifact_name,
                "validation": "validation.json",
                "metrics": "metrics.json",
            },
        },
    )
    return {
        "case_id": case_id,
        "stage": "changeset",
        "classification": classification,
        "valid": valid,
        "response_id": result.response.get("id"),
        "evidence_class": result.evidence_class,
        "diagnostics": diagnostics,
        "output_dir": str(output),
    }


def _scoped_components(
    candidate: Mapping[str, Any], scope: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    index = build_candidate_index(candidate)
    components: dict[str, dict[str, Any]] = {}
    for component_id in scope.get("entity_ids", []):
        if component_id in index["entities"]:
            components[component_id] = index["entities"][component_id]
    for component_id in scope.get("relationship_ids", []):
        if component_id in index["relationships"]:
            components[component_id] = index["relationships"][component_id]
    return components


def _binding_diagnostics(
    changeset: Mapping[str, Any],
    base_revision: Mapping[str, Any],
    scope: Mapping[str, Any],
) -> list[dict[str, str]]:
    checks = (
        ("base_revision_id", base_revision.get("revision_id")),
        ("base_candidate_hash", base_revision.get("candidate_hash")),
        ("expected_facts_hash", base_revision.get("expected_facts_hash")),
        ("scope_id", scope.get("scope_id")),
    )
    diagnostics = [
        _diagnostic(
            "CHANGESET_OUTPUT_BINDING_ERROR",
            f"/{field}",
            f"ChangeSet {field} does not match the authorized input.",
        )
        for field, expected in checks
        if changeset.get(field) != expected
    ]
    if set(changeset.get("source_issue_ids", [])) != set(scope.get("source_issue_ids", [])):
        diagnostics.append(
            _diagnostic(
                "CHANGESET_OUTPUT_BINDING_ERROR",
                "/source_issue_ids",
                "ChangeSet source issues do not match the authorized scope.",
            )
        )
    return diagnostics


def _issue_payload(issue: Any) -> dict[str, str]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _diagnostic(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
