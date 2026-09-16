"""Versioned IFC2Text outline -> section writing -> deterministic merge pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import ProviderOutput, ProviderOutputError, redact_provider_payload
from text2ifc_text.splits import atomic_write_text

from .facts import extract_building_facts
from .writing import assemble_sectioned_description, build_fact_index


LLM_RUN_SCHEMA_VERSION = "text2ifc/ifc2text-llm-run/0.1"
DEFAULT_OUTLINE_TEMPLATE = "ifc2text-outline.v0.1"
DEFAULT_SECTION_TEMPLATE = "ifc2text-section-writer.v0.1"
DEFAULT_MERGE_TEMPLATE = "ifc2text-merge.v0.1"


class IFC2TextLLMError(RuntimeError):
    """A versioned IFC2Text LLM stage failed its deterministic contract."""


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((_root() / "schemas" / "ifc2text" / name).read_text(encoding="utf-8"))


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, _json_text(value))


def _safe_building_context(facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "building": facts.get("building", {}),
        "units": facts.get("units", {}),
        "coordinate_system": facts.get("coordinate_system", {}),
        "capability": facts.get("capability", {}),
    }


def _provider_output(provider: Any, *, session_id: str, prompt: str, schema: dict[str, Any], state: dict[str, Any]) -> tuple[ProviderOutput, dict[str, Any]]:
    if hasattr(provider, "generate_live"):
        live = provider.generate_live(
            session_id=session_id,
            prompt=prompt,
            schema=schema,
            state=state,
        )
        return live.output, {
            "evidence_class": getattr(live, "evidence_class", "live"),
            "http_status": getattr(live, "http_status", None),
            "request": redact_provider_payload(getattr(live, "request", {})),
            "response": redact_provider_payload(getattr(live, "response", {})),
            "events": list(getattr(live, "events", ())),
        }
    if hasattr(provider, "generate_candidate"):
        output = provider.generate_candidate(
            session_id=session_id,
            prompt=prompt,
            schema=schema,
            state=state,
        )
        return output, {
            "evidence_class": str(output.metadata.get("evidence_class", "offline_fake")),
            "provider_metadata": redact_provider_payload(output.metadata),
        }
    raise IFC2TextLLMError("IFC2TEXT_PROVIDER_INTERFACE_UNSUPPORTED")


def _parse_and_validate(output: ProviderOutput, schema: dict[str, Any], *, stage: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    status, payload, diagnostics = output.parse_json()
    if status != "ok" or payload is None:
        raise IFC2TextLLMError(f"IFC2TEXT_{stage.upper()}_{status.upper()}")
    issues = [
        {
            "path": "/" + "/".join(str(part) for part in error.absolute_path),
            "message": error.message,
        }
        for error in Draft202012Validator(schema).iter_errors(payload)
    ]
    if issues:
        raise IFC2TextLLMError(f"IFC2TEXT_{stage.upper()}_SCHEMA_INVALID:" + json.dumps(issues, ensure_ascii=False))
    return payload, diagnostics


def _run_stage(
    *,
    provider: Any,
    output_dir: Path,
    stage: str,
    session_id: str,
    template_id: str,
    inputs: dict[str, Any],
    schema: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = render_prompt(template_id=template_id, inputs=inputs)
    _write_json(output_dir / "renderer-input.json", rendered["inputs"])
    atomic_write_text(output_dir / "prompt-rendered.md", rendered["text"])
    started = time.perf_counter()
    try:
        provider_output, evidence = _provider_output(
            provider,
            session_id=session_id,
            prompt=rendered["text"],
            schema=schema,
            state=state,
        )
    except (ProviderOutputError, IFC2TextLLMError) as error:
        failure = {
            "stage": stage,
            "session_id": session_id,
            "error_type": type(error).__name__,
            "message": str(error),
            "details": redact_provider_payload(getattr(error, "details", {})),
        }
        _write_json(output_dir / "failure.json", failure)
        raise
    elapsed = time.perf_counter() - started
    atomic_write_text(output_dir / "raw-response.txt", provider_output.text)
    _write_json(output_dir / "provider-evidence.json", evidence)
    try:
        payload, normalization = _parse_and_validate(provider_output, schema, stage=stage)
    except IFC2TextLLMError as error:
        _write_json(
            output_dir / "validation.json",
            {"valid": False, "stage": stage, "message": str(error)},
        )
        raise
    _write_json(output_dir / "parsed-response.json", payload)
    _write_json(
        output_dir / "validation.json",
        {"valid": True, "stage": stage, "normalization_diagnostics": normalization},
    )
    metrics = {
        "stage": stage,
        "session_id": session_id,
        "template_id": rendered["metadata"]["template_id"],
        "template_hash": rendered["metadata"]["template_hash"],
        "elapsed_seconds": round(elapsed, 6),
        "provider_metadata": redact_provider_payload(provider_output.metadata),
    }
    _write_json(output_dir / "metrics.json", metrics)
    _write_json(
        output_dir / "trace-manifest.json",
        {
            "template_id": rendered["metadata"]["template_id"],
            "template_hash": rendered["metadata"]["template_hash"],
            "renderer_input_path": "renderer-input.json",
            "rendered_prompt_path": "prompt-rendered.md",
            "raw_response_path": "raw-response.txt",
            "parsed_response_path": "parsed-response.json",
            "validation_feedback_path": "validation.json",
            "metrics_path": "metrics.json",
            "artifact_paths": ["provider-evidence.json"],
        },
    )
    return payload


def _validate_outline(outline: dict[str, Any], fact_index: dict[str, Any]) -> None:
    records = fact_index["records"]
    fact_refs = {record["fact_ref"] for record in records}
    issue_refs = {issue["issue_ref"] for issue in fact_index["issues"]}
    sections = outline["sections"]
    section_ids = [section["section_id"] for section in sections]
    if len(section_ids) != len(set(section_ids)):
        raise IFC2TextLLMError("IFC2TEXT_OUTLINE_DUPLICATE_SECTION_ID")
    if sections[0]["kind"] != "opening_overview" or sections[-1]["kind"] != "closing_summary":
        raise IFC2TextLLMError("IFC2TEXT_OUTLINE_TOTAL_PART_TOTAL_ORDER_REQUIRED")
    if sum(section["kind"] == "opening_overview" for section in sections) != 1:
        raise IFC2TextLLMError("IFC2TEXT_OUTLINE_SINGLE_OPENING_REQUIRED")
    if sum(section["kind"] == "closing_summary" for section in sections) != 1:
        raise IFC2TextLLMError("IFC2TEXT_OUTLINE_SINGLE_CLOSING_REQUIRED")
    primary_seen: set[str] = set()
    covered: set[str] = set()
    for section in sections:
        allowed = set(section["allowed_fact_refs"])
        required = set(section["required_fact_refs"])
        primary = set(section["primary_owned_fact_refs"])
        limitations = set(section["required_limitations"])
        if not allowed.issubset(fact_refs):
            raise IFC2TextLLMError("IFC2TEXT_OUTLINE_UNKNOWN_ALLOWED_FACT")
        if not required.issubset(allowed):
            raise IFC2TextLLMError("IFC2TEXT_OUTLINE_REQUIRED_OUTSIDE_ALLOWED")
        if not primary.issubset(allowed):
            raise IFC2TextLLMError("IFC2TEXT_OUTLINE_PRIMARY_OUTSIDE_ALLOWED")
        if primary_seen.intersection(primary):
            raise IFC2TextLLMError("IFC2TEXT_OUTLINE_DUPLICATE_PRIMARY_OWNER")
        if not limitations.issubset(issue_refs):
            raise IFC2TextLLMError("IFC2TEXT_OUTLINE_UNKNOWN_LIMITATION")
        primary_seen.update(primary)
        covered.update(allowed)
    unresolved = set(outline["unresolved_fact_refs"])
    if not unresolved.issubset(fact_refs.union(issue_refs)):
        raise IFC2TextLLMError("IFC2TEXT_OUTLINE_UNKNOWN_UNRESOLVED_REF")
    reconstructable = {
        record["fact_ref"]
        for record in records
        if record["kind"] in {
            "building",
            "storey",
            "ifc_space",
            "derived_enclosed_region",
            "wall",
            "opening",
            "door",
            "window",
            "stair",
        }
    }
    if not reconstructable.issubset(covered.union(unresolved)):
        missing = sorted(reconstructable.difference(covered, unresolved))
        raise IFC2TextLLMError("IFC2TEXT_OUTLINE_FACT_COVERAGE_MISSING:" + ",".join(missing))


def _validate_section(result: dict[str, Any], plan: dict[str, Any], fact_index: dict[str, Any]) -> None:
    if result["section_id"] != plan["section_id"]:
        raise IFC2TextLLMError("IFC2TEXT_SECTION_ID_MISMATCH")
    allowed = set(plan["allowed_fact_refs"])
    required = set(plan["required_fact_refs"])
    used = set(result["used_fact_refs"])
    omitted = set(result["omitted_required_fact_refs"])
    unresolved = set(result["unresolved_fact_refs"])
    known_refs = {record["fact_ref"] for record in fact_index["records"]}.union(
        issue["issue_ref"] for issue in fact_index["issues"]
    )
    if not used.issubset(allowed):
        raise IFC2TextLLMError("IFC2TEXT_SECTION_USED_FACT_OUTSIDE_ALLOWED")
    if not omitted.issubset(required):
        raise IFC2TextLLMError("IFC2TEXT_SECTION_OMITTED_FACT_NOT_REQUIRED")
    if required.difference(used, omitted):
        raise IFC2TextLLMError("IFC2TEXT_SECTION_REQUIRED_FACT_UNACCOUNTED")
    if not unresolved.issubset(known_refs):
        raise IFC2TextLLMError("IFC2TEXT_SECTION_UNKNOWN_UNRESOLVED_REF")


def _validate_merge(merge: dict[str, Any], outline: dict[str, Any], section_results: list[dict[str, Any]]) -> None:
    planned = {section["section_id"] for section in outline["sections"]}
    available = {section["section_id"] for section in section_results}
    order = set(merge["section_order"])
    blocked = set(merge["blocked_sections"])
    if order.union(blocked) != planned or order.intersection(blocked):
        raise IFC2TextLLMError("IFC2TEXT_MERGE_SECTION_ACCOUNTING_INVALID")
    if not order.issubset(available):
        raise IFC2TextLLMError("IFC2TEXT_MERGE_SECTION_RESULT_MISSING")
    for result in section_results:
        if result["section_id"] in order and result["omitted_required_fact_refs"]:
            raise IFC2TextLLMError("IFC2TEXT_MERGE_OMITTED_REQUIRED_FACT_ORDERED")
    transition_targets = {item["before_section_id"] for item in merge["transition_text"]}
    if not transition_targets.issubset(order):
        raise IFC2TextLLMError("IFC2TEXT_MERGE_UNKNOWN_TRANSITION_TARGET")


def run_llm_description(
    *,
    facts: dict[str, Any],
    output_dir: str | Path,
    provider: Any,
    run_id: str,
    outline_template_id: str = DEFAULT_OUTLINE_TEMPLATE,
    section_template_id: str = DEFAULT_SECTION_TEMPLATE,
    merge_template_id: str = DEFAULT_MERGE_TEMPLATE,
) -> dict[str, Any]:
    """Run the complete IFC2Text writing pipeline from deterministic facts to text."""
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    fact_index = build_fact_index(facts)
    _write_json(output / "prompt-safe-fact-index.json", fact_index)
    _write_json(output / "source-facts.json", facts)
    outline_schema = _load_schema("outline-0.1.schema.json")
    section_schema = _load_schema("section-0.1.schema.json")
    merge_schema = _load_schema("merge-0.1.schema.json")
    outline = _run_stage(
        provider=provider,
        output_dir=output / "outline",
        stage="outline",
        session_id=f"{run_id}:outline",
        template_id=outline_template_id,
        inputs={
            "BUILDING_FACTS": _safe_building_context(facts),
            "FACT_INDEX": fact_index,
            "EXTRACTION_ISSUES": fact_index["issues"],
            "OUTLINE_SCHEMA": outline_schema,
        },
        schema=outline_schema,
        state={"run_id": run_id, "stage": "outline"},
    )
    _validate_outline(outline, fact_index)
    _write_json(output / "outline" / "semantic-validation.json", {"valid": True})

    records_by_ref = {record["fact_ref"]: record for record in fact_index["records"]}
    issues_by_ref = {issue["issue_ref"]: issue for issue in fact_index["issues"]}
    section_results: list[dict[str, Any]] = []
    for index, plan in enumerate(outline["sections"], 1):
        section_id = str(plan["section_id"])
        section_facts = [records_by_ref[ref] for ref in plan["allowed_fact_refs"]]
        limitations = [issues_by_ref[ref] for ref in plan["required_limitations"]]
        result = _run_stage(
            provider=provider,
            output_dir=output / "sections" / f"{index:02d}-{section_id}",
            stage="section",
            session_id=f"{run_id}:section:{section_id}",
            template_id=section_template_id,
            inputs={
                "SECTION_PLAN": plan,
                "SECTION_FACTS": section_facts,
                "WRITING_CONTEXT": _safe_building_context(facts),
                "SECTION_LIMITATIONS": limitations,
                "SECTION_SCHEMA": section_schema,
            },
            schema=section_schema,
            state={"run_id": run_id, "stage": "section", "section_id": section_id},
        )
        _validate_section(result, plan, fact_index)
        _write_json(
            output / "sections" / f"{index:02d}-{section_id}" / "semantic-validation.json",
            {"valid": True},
        )
        section_results.append(result)
    _write_json(output / "section-results.json", section_results)

    merge = _run_stage(
        provider=provider,
        output_dir=output / "merge",
        stage="merge",
        session_id=f"{run_id}:merge",
        template_id=merge_template_id,
        inputs={
            "OUTLINE": outline,
            "SECTION_RESULTS": section_results,
            "GLOBAL_FACTS_AND_LIMITATIONS": {
                "building": _safe_building_context(facts),
                "issues": fact_index["issues"],
            },
            "MERGE_SCHEMA": merge_schema,
        },
        schema=merge_schema,
        state={"run_id": run_id, "stage": "merge"},
    )
    _validate_merge(merge, outline, section_results)
    _write_json(output / "merge" / "semantic-validation.json", {"valid": True})
    description = assemble_sectioned_description(
        outline=outline,
        section_results=section_results,
        merge_result=merge,
    )
    description_path = output / "design-description-llm.md"
    atomic_write_text(description_path, description)
    manifest = {
        "schema_version": LLM_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "status": "completed",
        "templates": {
            "outline": outline_template_id,
            "section": section_template_id,
            "merge": merge_template_id,
        },
        "fact_index_path": str(output / "prompt-safe-fact-index.json"),
        "outline_path": str(output / "outline" / "parsed-response.json"),
        "section_results_path": str(output / "section-results.json"),
        "merge_path": str(output / "merge" / "parsed-response.json"),
        "description_path": str(description_path),
        "section_count": len(section_results),
        "truth_boundary": {
            "writing_model_receives_source_ifc": False,
            "writing_model_receives_source_global_ids": False,
            "reconstruction_input": "design-description-llm.md",
        },
    }
    _write_json(output / "run.json", manifest)
    return manifest


def run_ifc_llm_description(
    *,
    source_ifc: str | Path,
    output_dir: str | Path,
    provider: Any,
    run_id: str,
    infer_spaces: bool = True,
) -> dict[str, Any]:
    facts = extract_building_facts(source_ifc, infer_spaces=infer_spaces)
    return run_llm_description(
        facts=facts,
        output_dir=output_dir,
        provider=provider,
        run_id=run_id,
    )
