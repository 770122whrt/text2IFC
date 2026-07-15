"""Phase 6 experiment execution, trace persistence, and run reports."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Mapping

from text2ifc_compiler import compile_document
from text2ifc_quality import check_generated_ifc

from .artifact_scan import scan_path
from .audit import build_audit_report
from .failure_routing import route_generation_failure
from .generator import generate_bim_json_candidate
from .providers import FakeAgentProvider


REQUIRED_EXPERIMENT_FIELDS = (
    "case_id",
    "split",
    "prompt_template_id",
    "prompt_hash",
    "provider_mode",
    "repair_attempts",
    "metrics",
    "failure_class",
    "artifact_paths",
)
REQUIRED_REPORT_SECTIONS = (
    "## Original Input",
    "## Design Brief",
    "## Rendered Prompt",
    "## Model Raw Output",
    "## Parsed BIM JSON or Draft",
    "## Validation Feedback",
    "## Geometry Feedback",
    "## Failure Route",
    "## Audit Result",
    "## Metrics",
    "## Final Artifacts",
)


class ExperimentError(ValueError):
    """Raised when experiment evidence is incomplete or inconsistent."""


def assert_artifacts_secret_safe(path: Path | str) -> dict[str, Any]:
    result = scan_path(path)
    if result["finding_count"]:
        raise ExperimentError(
            f"artifact secret scan failed with {result['finding_count']} finding(s)"
        )
    return result


def validate_experiment_record(record: Mapping[str, Any]) -> None:
    missing = [field for field in REQUIRED_EXPERIMENT_FIELDS if field not in record]
    if missing:
        raise ExperimentError("experiment record missing: " + ", ".join(missing))
    if not str(record["prompt_hash"]).startswith("sha256:"):
        raise ExperimentError("prompt_hash must use sha256 identity")


def write_experiment_report(
    output_dir: Path | str,
    report_manifest: Mapping[str, str],
) -> Path:
    """Generate one human review document from persisted trace artifacts."""
    output = Path(output_dir)
    missing = [section for section in REQUIRED_REPORT_SECTIONS if section not in report_manifest]
    if missing:
        raise ExperimentError("report manifest missing: " + ", ".join(missing))
    lines = ["# Phase 6 Multi-agent Run Report", ""]
    for section in REQUIRED_REPORT_SECTIONS:
        relative = Path(report_manifest[section])
        source = output / relative
        if not source.is_file():
            raise ExperimentError(f"report source does not exist for {section}: {relative}")
        content = source.read_text(encoding="utf-8").rstrip()
        language = "json" if source.suffix == ".json" else "text"
        lines.extend(
            [
                section,
                "",
                f"Source: [{relative.as_posix()}]({relative.as_posix()})",
                "",
                f"```{language}",
                content,
                "```",
                "",
            ]
        )
    path = output / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_phase6_case(
    *,
    case_id: str,
    input_text: str,
    design_brief: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    raw_response: str | None = None,
    expectation: Mapping[str, Any],
    output_dir: Path | str,
    split: str = "fixture",
    audit_mismatches: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Run one deterministic fake-provider case through the complete gate chain."""
    if (candidate is None) == (raw_response is None):
        raise ExperimentError("provide exactly one of candidate or raw_response")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = _artifact_paths()
    _clean_owned_artifacts(output, artifacts)
    _write_text(output / artifacts["input"], input_text)
    _write_json(output / artifacts["design_brief"], design_brief)

    renderer_inputs = {
        "DESIGN_BRIEF": design_brief,
        "SCHEMA_SUMMARY": {"schema_version": "bim-json/2.0", "ifc_schema": "IFC2X3"},
        "CAPABILITY_PROFILE": {"profile": "architectural-generation", "ifc_schema": "IFC2X3"},
        "FEW_SHOTS": [],
        "VALIDATION_FEEDBACK": [],
        "GEOMETRY_FEEDBACK": [],
    }
    trace_paths = {
        "renderer_input_path": artifacts["prompt_render_input"],
        "rendered_prompt_path": artifacts["prompt_rendered"],
        "raw_response_path": artifacts["raw_response"],
        "parsed_response_path": artifacts["parsed_response"],
        "validation_feedback_path": artifacts["validation_feedback"],
        "metrics_path": artifacts["metrics"],
        "artifact_paths": artifacts,
    }
    provider_text = (
        raw_response
        if raw_response is not None
        else json.dumps(candidate, ensure_ascii=False)
    )
    provider = FakeAgentProvider(
        {case_id: {"text": provider_text, "metadata": {"provider": "fake"}}}
    )
    generation = generate_bim_json_candidate(
        session_id=case_id,
        provider=provider,
        design_brief=design_brief,
        schema_summary=renderer_inputs["SCHEMA_SUMMARY"],
        capability_profile=renderer_inputs["CAPABILITY_PROFILE"],
        few_shots=[],
        validation_feedback=[],
        geometry_feedback=[],
        trace_paths=trace_paths,
    )
    _write_json(output / artifacts["prompt_render_input"], renderer_inputs)
    _write_json(output / artifacts["prompt_metadata"], generation.prompt_trace)
    _write_text(output / artifacts["prompt_rendered"], generation.rendered_prompt)
    _write_text(output / artifacts["raw_response"], generation.raw_response + "\n")
    _write_json(
        output / artifacts["parsed_response"],
        {
            "status": generation.status,
            "document": generation.document,
            "diagnostics": generation.diagnostics,
        },
    )
    parsed_name = (
        artifacts["draft"]
        if generation.status == "draft"
        else artifacts["candidate"]
        if generation.document is not None
        else artifacts["parsed_response"]
    )
    if generation.document is not None:
        _write_json(output / parsed_name, generation.document)
    _write_json(output / artifacts["validation_feedback"], {"issues": generation.diagnostics})

    compilation = None
    quality = None
    if generation.status == "formal" and not generation.diagnostics:
        compilation = compile_document(generation.document or {}, output / artifacts["ifc"])
        if compilation.success:
            quality = check_generated_ifc(output / artifacts["ifc"], expectation)
    geometry_payload = {
        "attempted": quality is not None,
        "success": bool(quality and quality.success),
        "issues": quality.issues if quality else [],
        "metrics": quality.metrics if quality else {},
    }
    _write_json(output / artifacts["geometry_feedback"], geometry_payload)

    route_feedback = generation.diagnostics
    if generation.status == "draft" and generation.document is not None:
        route_feedback = _draft_route_feedback(generation.document)
    route = route_generation_failure(
        previous_candidate=generation.document,
        validation_feedback=route_feedback,
        geometry_feedback=geometry_payload["issues"],
        known_facts=design_brief["known_facts"],
    )
    _write_json(output / artifacts["repair_attempts"], route)
    deterministic_gates = {
        "design_brief": True,
        "bim_json": generation.status == "formal" and not generation.diagnostics,
        "compile_reopen": bool(compilation and compilation.success),
        "geometry": bool(quality and quality.success),
    }
    audit = build_audit_report(
        deterministic_gates=deterministic_gates,
        intent_coverage={"requested_geometry": "covered" if all(deterministic_gates.values()) else "unverified"},
        mismatches=audit_mismatches,
        unsupported_facts=[],
        evidence={
            "input": artifacts["input"],
            "design_brief": artifacts["design_brief"],
            "candidate": parsed_name,
            "validation": artifacts["validation_feedback"],
            "geometry": artifacts["geometry_feedback"],
            "raw_response": artifacts["raw_response"],
        },
    )
    _write_json(output / artifacts["audit"], audit)
    failure_class = _failure_class(generation.status, generation.diagnostics, compilation, quality, audit)
    metrics = {
        "success": failure_class is None,
        "provider_mode": "fake",
        "bim_json_status": generation.status,
        "compile_reopen_success": bool(compilation and compilation.success),
        "geometry_pass": bool(quality and quality.success),
        "audit_pass": not audit["blocking"],
        "failure_route": route["route"],
        "repair_attempt_count": len(route["repair_attempts"]),
        "failure_class": failure_class,
    }
    _write_json(output / artifacts["metrics"], metrics)
    artifact_manifest = {"artifacts": artifacts, "secret_redaction_status": "pending"}
    _write_json(output / artifacts["artifact_manifest"], artifact_manifest)
    record = {
        "case_id": case_id,
        "split": split,
        "prompt_template_id": generation.prompt_trace["template_id"],
        "prompt_hash": generation.prompt_trace["template_hash"],
        "provider_mode": "fake",
        "repair_attempts": route["repair_attempts"],
        "metrics": metrics,
        "failure_class": failure_class,
        "artifact_paths": artifacts,
    }
    validate_experiment_record(record)
    _write_json(output / artifacts["experiment_record"], record)
    report_manifest = {
        "## Original Input": artifacts["input"],
        "## Design Brief": artifacts["design_brief"],
        "## Rendered Prompt": artifacts["prompt_rendered"],
        "## Model Raw Output": artifacts["raw_response"],
        "## Parsed BIM JSON or Draft": parsed_name,
        "## Validation Feedback": artifacts["validation_feedback"],
        "## Geometry Feedback": artifacts["geometry_feedback"],
        "## Failure Route": artifacts["repair_attempts"],
        "## Audit Result": artifacts["audit"],
        "## Metrics": artifacts["metrics"],
        "## Final Artifacts": artifacts["artifact_manifest"],
    }
    write_experiment_report(output, report_manifest)
    first_scan = assert_artifacts_secret_safe(output)
    artifact_manifest["secret_redaction_status"] = "passed"
    artifact_manifest["secret_scan"] = {
        "finding_count": first_scan["finding_count"],
        "scanned_file_count": first_scan["scanned_file_count"],
    }
    _write_json(output / artifacts["artifact_manifest"], artifact_manifest)
    write_experiment_report(output, report_manifest)
    final_scan = assert_artifacts_secret_safe(output)
    _write_json(output / artifacts["secret_scan"], final_scan)
    return record


def run_phase6_matrix(
    *,
    cases: Sequence[Mapping[str, Any]],
    output_dir: Path | str,
) -> dict[str, Any]:
    """Run controlled cases and persist aggregate route/failure evidence."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for case in cases:
        case_id = str(case.get("case_id", "")).strip()
        if not case_id:
            raise ExperimentError("matrix case missing case_id")
        kwargs = dict(case)
        kwargs["case_id"] = case_id
        kwargs["output_dir"] = output / case_id
        records.append(run_phase6_case(**kwargs))
    summary = {
        "case_count": len(records),
        "failure_routes": sorted(
            {record["metrics"]["failure_route"] for record in records}
        ),
        "failure_classes": sorted(
            {record["failure_class"] or "success" for record in records}
        ),
        "records": records,
    }
    _write_json(output / "experiment-matrix.json", summary)
    return summary


def _artifact_paths() -> dict[str, str]:
    return {
        "input": "input.txt", "design_brief": "design-brief.json",
        "prompt_render_input": "prompt-render-input.json", "prompt_metadata": "prompt-metadata.json",
        "prompt_rendered": "prompt-rendered.md", "raw_response": "raw-response.txt",
        "parsed_response": "parsed-response.json",
        "candidate": "candidate.json", "draft": "draft.json",
        "validation_feedback": "validation-feedback.json", "geometry_feedback": "geometry-feedback.json",
        "repair_attempts": "repair-attempts.json", "audit": "audit-report.json",
        "metrics": "metrics.json", "artifact_manifest": "artifact-manifest.json",
        "experiment_record": "experiment-record.json", "report": "report.md",
        "secret_scan": "secret-scan.json", "ifc": "output.ifc",
    }


def _clean_owned_artifacts(output: Path, artifacts: Mapping[str, str]) -> None:
    for relative in sorted(set(artifacts.values())):
        path = output / relative
        if path.is_file():
            path.unlink()


def _draft_route_feedback(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    questions = {
        str(item.get("path")): str(item.get("question"))
        for item in document.get("clarification_targets", [])
        if item.get("path") and item.get("question")
    }
    return [
        {
            "code": str(item.get("code", "MISSING_FACT")),
            "required_fact_paths": [str(item["path"])],
            "question": questions.get(str(item["path"]), ""),
        }
        for item in document.get("missing_facts", [])
        if item.get("path")
    ]


def _failure_class(status: str, diagnostics: list[dict[str, Any]], compilation: Any, quality: Any, audit: Mapping[str, Any]) -> str | None:
    if status == "draft": return "draft"
    if status == "invalid":
        return "invalid_json" if any(item.get("code") == "JSON_DECODE_ERROR" for item in diagnostics) else "invalid_bim_json"
    if not compilation or not compilation.success: return "compile_failure"
    if not quality or not quality.success: return "geometry_failure"
    if audit["blocking"]: return "audit_mismatch"
    return None


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")
