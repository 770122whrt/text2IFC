"""Provider-backed generation of one component-scoped BIM JSON ChangeSet."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Mapping

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.schema import load_draft_schema, _load_schema_path

from .candidate_index import build_candidate_index
from .authoring_contract import build_authoring_contract
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
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-staged-door-opening.json",
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-staged-orthogonal-walls.json",
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-staged-linear-railing.json",
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-staged-cross-storey.json",
    PROJECT_ROOT / "prompts" / "agent" / "few-shot" / "changeset-staged-negative-y-stair.json",
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
    field_recovery: bool = False,
    field_recovery_values: Mapping[str, Any] | None = None,
    generation_package: Mapping[str, Any] | None = None,
    semantic_correction: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Ask the provider for a ChangeSet or canonical Draft and validate its binding."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    field_removal = any(e.get('remove_paths') for e in (semantic_correction or {}).get('edits', {}).values())
    changeset_version = 'text2ifc/bim-json-changeset/1.3' if candidate.get('schema_version') in {'bim-json/2.3', 'bim-json/2.4', 'bim-json/2.5', 'bim-json/2.6'} else 'text2ifc/bim-json-changeset/1.2' if any('/part_appearance' in e.get('remove_paths', []) for e in (semantic_correction or {}).get('edits', {}).values()) else 'text2ifc/bim-json-changeset/1.1' if field_removal else 'text2ifc/bim-json-changeset/1.0'
    changeset_schema = load_changeset_schema(changeset_version)
    draft_schema = load_draft_schema()
    new_semantics = candidate.get('schema_version') in {'bim-json/2.1', 'bim-json/2.2', 'bim-json/2.3', 'bim-json/2.4', 'bim-json/2.5', 'bim-json/2.6'}
    if new_semantics:
        from .generation_contract import draft_schema_relative_path
        draft_schema = _load_schema_path(PROJECT_ROOT / draft_schema_relative_path(candidate['schema_version']))
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
    if new_semantics:
        renderer_inputs['FORMAL_SCHEMA'] = _load_schema_path(PROJECT_ROOT / f"schemas/{candidate['schema_version']}/schema.json")
        from .changeset_context import select_changeset_context
        selection = select_changeset_context(candidate=candidate, scope=scope,
            field_recovery=field_recovery, package=generation_package)
        renderer_inputs['IFC_AUTHORING_CONTRACT'] = selection['authoring_contract']
        renderer_inputs['READ_ONLY_COMPONENTS'] = selection['read_only_components']
        renderer_inputs['FEW_SHOTS'] = [_read_json(PROJECT_ROOT/'prompts/agent/few-shot'/name)
                                       for name in selection['few_shot_names']]
        _write_json(output/'context-selection.json', selection)
    if semantic_correction:
        renderer_inputs['SEMANTIC_CORRECTION'] = dict(semantic_correction)
    template_id = ('bim-json-changeset.v1.7' if field_removal else
                   'bim-json-changeset.v1.6' if semantic_correction else
                   'bim-json-changeset.v1.8' if field_recovery else
                   'bim-json-changeset.v1.5' if new_semantics else CHANGESET_TEMPLATE_ID)
    if candidate.get('schema_version') == 'bim-json/2.2':
        template_id = 'bim-json-changeset.v1.9'
        renderer_inputs.setdefault('SEMANTIC_CORRECTION', {})
    if candidate.get('schema_version') in {'bim-json/2.3', 'bim-json/2.4', 'bim-json/2.5', 'bim-json/2.6'}:
        template_id = 'bim-json-changeset.v1.13' if candidate.get('schema_version') == 'bim-json/2.6' else 'bim-json-changeset.v1.12' if candidate.get('schema_version') == 'bim-json/2.5' else 'bim-json-changeset.v1.11' if candidate.get('schema_version') == 'bim-json/2.4' else 'bim-json-changeset.v1.10'
        renderer_inputs.setdefault('SEMANTIC_CORRECTION', {})
    if field_recovery and candidate.get('schema_version') == 'bim-json/2.6':
        template_id = 'bim-json-changeset.v1.14'
        renderer_inputs['FIELD_RECOVERY_VALUES'] = dict(field_recovery_values or {})
    rendered = render_prompt(template_id=template_id, inputs=renderer_inputs)
    _write_json(output / "prompt-render-input.json", renderer_inputs)
    _write_text(output / "prompt-rendered.md", rendered["text"])

    from .openai_compat import OpenAICompatError
    from .providers import ProviderOutputError
    from .generation_budget import GenerationBudgetExceeded
    result = None
    try:
        result = provider.generate_live(
            session_id=f"phase6.5-{case_id}-changeset-{call_index:02d}",
            prompt=rendered["text"], schema=changeset_schema,
            state={"case_id": case_id, "stage": "changeset", "call_index": call_index},
        )
        validate_provider_output(result.output)
    except GenerationBudgetExceeded:
        raise
    except (OpenAICompatError, ProviderOutputError) as error:
        if result is not None and isinstance(error, ProviderOutputError):
            error.live_result = result
        from .live_trace import write_provider_failure_trace
        failure = write_provider_failure_trace(error=error, output_dir=output, stage='changeset')
        diagnostics = [_diagnostic('CHANGESET_PROVIDER_FAILED', '/',
                                  f"Provider response unavailable or unusable: {failure['failure_class']}.")]
        result = {'case_id': case_id, 'stage': 'changeset', 'call_index': call_index,
            'classification': 'provider_failed', 'valid': False, 'diagnostics': diagnostics,
            'response_id': failure['details'].get('response_id'),
            'evidence_class': failure['details'].get('evidence_class', 'unavailable'),
            'output_dir': str(output), 'usage': failure['details'].get('usage', {})}
        _write_json(output/'validation.json', {'valid': False, 'issues': diagnostics})
        _write_json(output/'metrics.json', result)
        return result
    provider_manifest = write_live_trace(
        result=result,
        output_dir=output,
        trace_level=trace_level,
        preserve_deep_evidence=trace_level == "compact",
    )
    parse_status, parsed, parse_diagnostics = result.output.parse_json()
    provider_parsed = copy.deepcopy(parsed)
    control_normalizations: list[dict[str, str]] = []
    if isinstance(parsed, Mapping) and parsed.get("schema_version") == changeset_version:
        parsed, control_normalizations = _bind_malformed_hashes(parsed, base_revision)
    normalization_diagnostics = [*parse_diagnostics, *control_normalizations]
    diagnostics = list(parse_diagnostics)
    classification = "invalid"
    artifact_name: str | None = None

    if parse_status != "ok" or parsed is None:
        diagnostics.append(
            _diagnostic("CHANGESET_OUTPUT_CONTRACT_ERROR", "/", "Output is not a JSON object.")
        )
    elif parsed.get("schema_version") == changeset_version:
        contract_issues = [_issue_payload(issue) for issue in validate_changeset(parsed)]
        diagnostics.extend(contract_issues)
        if not contract_issues:
            diagnostics.extend(_binding_diagnostics(parsed, base_revision, scope))
        if not diagnostics:
            classification = "changeset"
            artifact_name = "changeset.json"
    elif parsed.get("draft_version") in {"bim-json-draft/1.0", "bim-json-draft/1.1", "bim-json-draft/1.2", 'bim-json-draft/1.3', 'bim-json-draft/1.4', 'bim-json-draft/1.5', 'bim-json-draft/1.6'}:
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

    if provider_parsed is not None and provider_parsed != parsed:
        _write_json(output / "provider-parsed-output.json", provider_parsed)
    if parsed is not None:
        _write_json(output / "parsed-output.json", parsed)
    if artifact_name is not None:
        _write_json(output / artifact_name, parsed)
    valid = artifact_name is not None
    _write_json(
        output / "validation.json",
        {
            "valid": valid,
            "issue_count": len(diagnostics),
            "issues": diagnostics,
            "normalizations": control_normalizations,
        },
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
                "provider_parsed_output": (
                    "provider-parsed-output.json"
                    if provider_parsed is not None and provider_parsed != parsed
                    else None
                ),
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


def retry_candidate_key(output_dir):
    """Ignore new trace/operation IDs when detecting the same failed patch."""
    from .revisions import hash_json_value
    root = Path(output_dir)
    parsed = root/'parsed-output.json'
    if parsed.is_file():
        value = _read_json(parsed)
        if isinstance(value, dict) and isinstance(value.get('operations'), list):
            value = [{k:v for k,v in op.items() if k not in {'operation_id', 'evidence_refs'}}
                     if isinstance(op, dict) else op for op in value['operations']]
        return hash_json_value(value)
    text_path = root/'model-text.txt'
    return hash_json_value(text_path.read_text(encoding='utf-8') if text_path.is_file() else None)


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
    source_issue_ids = set(changeset.get("source_issue_ids", []))
    authorized_issue_ids = set(scope.get("source_issue_ids", []))
    if not source_issue_ids or not source_issue_ids.issubset(authorized_issue_ids):
        diagnostics.append(
            _diagnostic(
                "CHANGESET_OUTPUT_BINDING_ERROR",
                "/source_issue_ids",
                "ChangeSet source issues must be a non-empty subset of the authorized scope.",
            )
        )
    return diagnostics


def _bind_malformed_hashes(
    changeset: Mapping[str, Any], base_revision: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    bound = copy.deepcopy(dict(changeset))
    diagnostics: list[dict[str, str]] = []
    for field in ("base_candidate_hash", "expected_facts_hash"):
        value = bound.get(field)
        if isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            continue
        expected = base_revision.get(
            "candidate_hash" if field == "base_candidate_hash" else "expected_facts_hash"
        )
        if not isinstance(expected, str):
            continue
        bound[field] = expected
        diagnostics.append(
            _diagnostic(
                "CONTROL_FIELD_BOUND",
                f"/{field}",
                "Malformed system control field was bound to the authorized value.",
            )
        )
    return bound, diagnostics


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
