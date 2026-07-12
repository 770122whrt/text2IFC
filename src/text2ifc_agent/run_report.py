"""Generated human-review reports for live Phase 6.1 runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .audit import collect_revision_audit_evidence


class RunReportError(ValueError):
    """Raised when a live run lacks evidence required for report generation."""


STAGE_SIDECARS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "Design Brief Agent",
        "design-brief",
        (
            "input.txt",
            "conversation.json",
            "prompt-rendered.md",
            "request.redacted.json",
            "response.raw.json",
            "model-text.txt",
            "design-brief.json",
            "validation.json",
            "metrics.json",
        ),
    ),
    (
        "BIM JSON Generator",
        "generator",
        (
            "prompt-rendered.md",
            "response.raw.json",
            "model-text.txt",
            "candidate.json",
            "validation.json",
            "metrics.json",
        ),
    ),
    (
        "Repair Route",
        "repair",
        (
            "route.json",
            "repair-attempts.json",
            "metrics.json",
        ),
    ),
    (
        "Audit Agent",
        "audit",
        (
            "prompt-rendered.md",
            "response.raw.json",
            "model-text.txt",
            "audit-report.json",
            "validation.json",
            "metrics.json",
        ),
    ),
)

GATE_SIDECARS: tuple[str, ...] = (
    "semantic-capabilities.json",
    "semantic-coverage.json",
    "semantic-geometry-expectation.json",
    "expected-facts.json",
    "dynamic-gates.json",
    "gate-summary.json",
    "route-decision.json",
    "ifc-verification.json",
    "geometry-expectation.json",
    "geometry-feedback.json",
    "acceptance-metrics.json",
    "secret-scan.json",
)


def resolve_final_design_brief_dir(root: Path | str) -> Path:
    """Return the final Design Brief sidecar directory for a live case."""
    case_root = Path(root)
    canonical = case_root / "design-brief"
    if (canonical / "design-brief.json").is_file():
        return canonical
    calls_root = case_root / "calls"
    candidates = [
        item
        for item in sorted(calls_root.glob("*-design-brief"))
        if (item / "design-brief.json").is_file()
    ]
    if candidates:
        return candidates[-1]
    return canonical


def build_live_run_report(*, case_dir: Path | str) -> Path:
    """Render report.md from required live sidecars in a case directory."""
    root = Path(case_dir)
    _require_sidecars(root)
    report_path = root / "report.md"
    design = resolve_final_design_brief_dir(root)
    generator = root / "generator"
    repair = root / "repair"
    audit = root / "audit"
    design_relative = design.relative_to(root).as_posix()

    lines: list[str] = [
        "# Phase 6.1 Live Mimo Run Report",
        "",
        "Generated from trace sidecars. This report is not hand-authored evidence.",
        "",
        "## Original Input",
        "",
        _embed_text(design / "input.txt"),
        "",
        _source_link(f"{design_relative}/input.txt"),
        "",
        "## Conversation",
        "",
        _embed_json(design / "conversation.json"),
        "",
        _source_link(f"{design_relative}/conversation.json"),
        "",
    ]
    lines.extend(_stage_section(root, "Design Brief Agent", design))
    lines.extend(_stage_section(root, "BIM JSON Generator", generator))
    lines.extend(_repair_section(repair))
    lines.extend(_stage_section(root, "Audit Agent", audit))
    lines.extend(_semantic_coverage_section(root))
    lines.extend(_generated_ifc_gates_section(root))
    lines.extend(_revision_history_section(root))
    lines.extend(_stage_timing_section(root))
    lines.extend(_metrics_section(root))
    lines.extend(_source_sidecars_section(root))
    _write_text(report_path, "\n".join(lines).rstrip() + "\n")
    _write_run_trace_manifest(root=root, report_path=report_path)
    return report_path


def build_phase6_4_review_report(*, case_dir: Path | str) -> Path:
    """Render the Phase 6.4 human-review report from actual sidecars."""

    root = Path(case_dir)
    report_path = root / "report.md"
    case_result = _read_optional_json(root / "case-result.json") or {}
    route_decision = _read_optional_json(root / "route-decision.json") or {}
    lines: list[str] = [
        "# Phase 6.4 Feedback Routing Run Report",
        "",
        "Generated from run artifacts. This report is the human review entry point.",
        "",
        "## Original Input",
        "",
        _optional_text_block(root / "input.txt"),
        "",
        _optional_source_link("input.txt", root / "input.txt"),
        "",
        "## Transcript",
        "",
        _optional_json_block(root / "conversation.json"),
        "",
        _optional_source_link("conversation.json", root / "conversation.json"),
        "",
        "## Design Brief",
        "",
        *_phase6_4_links(root, ("design-brief/design-brief.json", "design-brief/validation.json")),
        "",
        "## BIM JSON or Draft",
        "",
        *_phase6_4_links(
            root,
            (
                "generator/candidate.json",
                "generator/draft.json",
                "generator/parsed-output.json",
            ),
        ),
        "",
        "## Validation",
        "",
        *_phase6_4_links(
            root,
            (
                "generator/validation.json",
                "semantic-coverage.json",
            ),
        ),
        "",
        "## Compiler and Reopen",
        "",
        *_phase6_4_links(root, ("ifc-verification.json", "output.ifc")),
        "",
        "## Gates",
        "",
        *_phase6_4_links(root, ("gate-summary.json", "geometry-feedback.json")),
        "",
        "## Audit",
        "",
        *_phase6_4_links(root, ("audit/audit-report.json", "audit/validation.json")),
        "",
        "## Normalized Issues",
        "",
        _optional_json_block(root / "issues.json"),
        "",
        _optional_source_link("issues.json", root / "issues.json"),
        "",
        "## Route Decision",
        "",
        f"- route: `{route_decision.get('route')}`",
        f"- target_stage: `{route_decision.get('target_stage')}`",
        f"- final_status: `{route_decision.get('final_status')}`",
        "",
        _optional_json_block(root / "route-decision.json"),
        "",
        _optional_source_link("route-decision.json", root / "route-decision.json"),
        "",
        "## Feedback Rounds",
        "",
        _optional_json_block(root / "feedback-rounds.json"),
        "",
        _optional_source_link("feedback-rounds.json", root / "feedback-rounds.json"),
        "",
        "## Final Status",
        "",
        f"- final_status: `{case_result.get('final_status', route_decision.get('final_status'))}`",
        f"- failure_owner: `{case_result.get('failure_owner')}`",
        f"- output_type: `{case_result.get('output_type')}`",
        "",
        "## Evidence Paths",
        "",
        *_phase6_4_evidence_lines(root, case_result),
        "",
    ]
    _write_text(report_path, "\n".join(line for line in lines if line is not None).rstrip() + "\n")
    return report_path


def _require_sidecars(root: Path) -> None:
    for _title, directory, files in STAGE_SIDECARS:
        stage_dir = resolve_final_design_brief_dir(root) if directory == "design-brief" else root / directory
        for name in files:
            path = _stage_sidecar_path(stage_dir, name)
            if not path.is_file():
                relative = (stage_dir / name).relative_to(root).as_posix()
                raise RunReportError(f"required sidecar is missing: {relative}")


def _stage_section(root: Path, title: str, stage_dir: Path) -> list[str]:
    raw_path = _stage_sidecar_path(stage_dir, "response.raw.json")
    model_text_path = _stage_sidecar_path(stage_dir, "model-text.txt")
    raw = _read_json(raw_path)
    metrics = _read_json(stage_dir / "metrics.json")
    response_id = raw.get("id") or metrics.get("response_id")
    stop_reason = raw.get("stop_reason") or metrics.get("stop_reason")
    relative_stage = stage_dir.relative_to(root).as_posix()
    parsed_name = _stage_parsed_artifact(stage_dir)
    lines = [
        f"## {title}",
        "",
        f"- response_id: `{response_id}`",
        f"- stop_reason: `{stop_reason}`",
        f"- evidence_class: `{metrics.get('evidence_class')}`",
        "",
        "### Prompt",
        "",
        _source_link(f"{relative_stage}/prompt-rendered.md"),
        "",
        "### Raw Model Output",
        "",
        _source_link(raw_path.relative_to(root).as_posix()),
        _source_link(model_text_path.relative_to(root).as_posix()),
        "",
    ]
    if parsed_name:
        lines.extend(
            [
                "### Parsed Output",
                "",
                _source_link(f"{relative_stage}/{parsed_name}"),
                "",
            ]
        )
    lines.extend(
        [
            "### Validation and Metrics",
            "",
            _source_link(f"{relative_stage}/validation.json")
            if (stage_dir / "validation.json").is_file()
            else "",
            _source_link(f"{relative_stage}/metrics.json"),
            "",
        ]
    )
    return [line for line in lines if line != "" or lines]


def _repair_section(repair_dir: Path) -> list[str]:
    route = _read_json(repair_dir / "route.json")
    metrics = _read_json(repair_dir / "metrics.json")
    return [
        "## Repair Route",
        "",
        f"- route: `{route.get('route')}`",
        f"- provider_call_count: `{route.get('provider_call_count')}`",
        f"- evidence_class: `{metrics.get('evidence_class')}`",
        "",
        _source_link("repair/route.json"),
        _source_link("repair/repair-attempts.json"),
        _source_link("repair/metrics.json"),
        "",
    ]


def _generated_ifc_gates_section(root: Path) -> list[str]:
    existing = [name for name in GATE_SIDECARS if (root / name).is_file()]
    if not existing:
        return []
    lines = [
        "## Generated IFC Gates",
        "",
    ]
    for name in existing:
        lines.append(_source_link(name))
    lines.append("")
    if (root / "geometry-feedback.json").is_file():
        lines.extend(
            [
                "### Geometry Feedback",
                "",
                _embed_json(root / "geometry-feedback.json"),
                "",
                _source_link("geometry-feedback.json"),
                "",
            ]
        )
    return lines


def _semantic_coverage_section(root: Path) -> list[str]:
    if not (root / "semantic-coverage.json").is_file():
        return []
    lines = [
        "## Semantic Coverage",
        "",
        _source_link("semantic-capabilities.json"),
        _source_link("semantic-coverage.json"),
        "",
        _embed_json(root / "semantic-coverage.json"),
        "",
    ]
    if (root / "semantic-geometry-expectation.json").is_file():
        lines.extend(
            [
                _source_link("semantic-geometry-expectation.json"),
                "",
            ]
        )
    return [line for line in lines if line]


def _metrics_section(root: Path) -> list[str]:
    lines = ["## Metrics", ""]
    for title, directory, _files in STAGE_SIDECARS:
        stage_dir = resolve_final_design_brief_dir(root) if directory == "design-brief" else root / directory
        metrics_path = stage_dir / "metrics.json"
        relative_stage = stage_dir.relative_to(root).as_posix()
        metrics = _read_json(metrics_path)
        lines.extend(
            [
                f"### {title}",
                "",
                _json_block(metrics),
                "",
                _source_link(f"{relative_stage}/metrics.json"),
                "",
            ]
        )
    return lines


def _revision_history_section(root: Path) -> list[str]:
    evidence = collect_revision_audit_evidence(root)
    if evidence.get("status") == "not_applicable":
        return []
    revision = evidence.get("revision", {})
    preservation = evidence.get("preservation", {})
    lines = [
        "## Revision and ChangeSet History",
        "",
        f"- evidence_status: `{evidence.get('status')}`",
        f"- revision_id: `{revision.get('revision_id')}`",
        f"- candidate_hash: `{revision.get('candidate_hash')}`",
        f"- expected_facts_hash: `{revision.get('expected_facts_hash')}`",
        f"- changed_ids: `{evidence.get('changed_ids', [])}`",
        f"- dependency_ids: `{evidence.get('dependency_ids', [])}`",
        f"- source_issue_ids: `{evidence.get('source_issue_ids', [])}`",
        "",
        "### Preservation",
        "",
        _json_block(preservation),
        "",
    ]
    for index, record in enumerate(evidence.get("changesets", []), start=1):
        payload = record.get("payload", {}) if isinstance(record, dict) else {}
        path = record.get("path") if isinstance(record, dict) else None
        lines.extend(
            [
                f"### ChangeSet {index}",
                "",
                f"- changeset_id: `{payload.get('changeset_id')}`",
                f"- source_issue_ids: `{payload.get('source_issue_ids', [])}`",
                "",
                _json_block(payload.get("operations", [])),
                "",
                _source_link(str(path)) if path else "",
                "",
            ]
        )
    for index, record in enumerate(evidence.get("scopes", []), start=1):
        payload = record.get("payload", {}) if isinstance(record, dict) else {}
        path = record.get("path") if isinstance(record, dict) else None
        lines.extend(
            [
                f"### Allowed Scope {index}",
                "",
                _json_block(payload),
                "",
                _source_link(str(path)) if path else "",
                "",
            ]
        )
    packages = evidence.get("packages", [])
    if packages:
        lines.extend(
            [
                "## Generation Packages",
                "",
                _json_block(packages),
                "",
                _source_link("generator-staged/package-records.json"),
                "",
            ]
        )
    gate_evidence = evidence.get("gate_evidence", {})
    if gate_evidence:
        lines.extend(
            [
                "### Revision Gates",
                "",
                _json_block(gate_evidence),
                "",
                _source_link("revision-gates.json"),
                "",
            ]
        )
    return [line for line in lines if line is not None]


def _stage_timing_section(root: Path) -> list[str]:
    progress_path = root / "progress.jsonl"
    if not progress_path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in progress_path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("elapsed_seconds"), (int, float)):
            events.append(payload)
    by_stage: dict[str, list[float]] = {}
    for event in events:
        by_stage.setdefault(str(event.get("stage", "unknown")), []).append(float(event["elapsed_seconds"]))
    lines = ["## Stage Timing", ""]
    for stage, values in by_stage.items():
        duration = round(max(values) - min(values), 3) if len(values) > 1 else 0.0
        lines.append(f"- {stage}: `{duration}` seconds")
    lines.extend(["", _source_link("progress.jsonl"), ""])
    return lines


def _source_sidecars_section(root: Path) -> list[str]:
    lines = ["## Source Sidecars", ""]
    for title, directory, files in STAGE_SIDECARS:
        stage_dir = resolve_final_design_brief_dir(root) if directory == "design-brief" else root / directory
        relative_stage = stage_dir.relative_to(root).as_posix()
        lines.extend([f"### {title}", ""])
        for name in files:
            path = _stage_sidecar_path(stage_dir, name)
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                lines.append(f"- [{relative}]({relative})")
        lines.append("")
    existing_gates = [name for name in GATE_SIDECARS if (root / name).is_file()]
    if existing_gates:
        lines.extend(["### Generated IFC Gates", ""])
        for name in existing_gates:
            lines.append(f"- [{name}]({name})")
        lines.append("")
    revision_sidecars = [
        path
        for path in (
            root / "candidate-revision.json",
            root / "component-preservation.json",
            root / "revision-gates.json",
            root / "generator-staged" / "package-records.json",
            root / "progress.jsonl",
        )
        if path.is_file()
    ]
    revision_sidecars.extend(sorted(root.glob("changeset-round-*/change-scope.json")))
    revision_sidecars.extend(sorted(root.glob("changeset-round-*/changeset.json")))
    if revision_sidecars:
        lines.extend(["### Revision and Package Evidence", ""])
        for path in revision_sidecars:
            relative = path.relative_to(root).as_posix()
            lines.append(f"- [{relative}]({relative})")
        lines.append("")
    return lines


def _first_existing(stage_dir: Path, names: tuple[str, ...]) -> str | None:
    for name in names:
        if (stage_dir / name).is_file():
            return name
    return None


def _stage_sidecar_path(stage_dir: Path, name: str) -> Path:
    direct = stage_dir / name
    if direct.is_file():
        return direct
    traced = stage_dir / "trace" / name
    if traced.is_file():
        return traced
    return direct


def _stage_parsed_artifact(stage_dir: Path) -> str | None:
    if stage_dir.name == "generator":
        return _first_existing(stage_dir, ("candidate.json", "draft.json", "parsed-output.json"))
    if stage_dir.name == "audit":
        return _first_existing(stage_dir, ("audit-report.json", "parsed-output.json"))
    return _first_existing(stage_dir, ("design-brief.json", "parsed-output.json"))


def _embed_text(path: Path) -> str:
    return "```text\n" + path.read_text(encoding="utf-8").rstrip() + "\n```"


def _embed_json(path: Path) -> str:
    return _json_block(_read_json(path))


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def _source_link(relative: str) -> str:
    return f"Source: [{relative}]({relative})"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> Any:
    if not path.is_file():
        return None
    return _read_json(path)


def _optional_text_block(path: Path) -> str:
    if not path.is_file():
        return "_Missing artifact._"
    return _embed_text(path)


def _optional_json_block(path: Path) -> str:
    if not path.is_file():
        return "_Missing artifact._"
    return _embed_json(path)


def _optional_source_link(relative: str, path: Path) -> str:
    if not path.is_file():
        return ""
    return f"[{relative}]({relative})"


def _phase6_4_links(root: Path, relatives: tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for relative in relatives:
        if (root / relative).is_file():
            lines.append(f"- [{relative}]({relative})")
    return lines or ["_No artifact recorded._"]


def _phase6_4_evidence_lines(
    root: Path,
    case_result: dict[str, Any],
) -> list[str]:
    paths = case_result.get("evidence_paths")
    if not isinstance(paths, list) or not paths:
        paths = [
            "issues.json",
            "route-decision.json",
            "feedback-rounds.json",
            "case-result.json",
        ]
    lines: list[str] = []
    for relative in paths:
        if isinstance(relative, str) and (root / relative).exists():
            lines.append(f"- [{relative}]({relative})")
    return lines or ["_No evidence paths recorded._"]


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_run_trace_manifest(*, root: Path, report_path: Path) -> None:
    artifacts: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "trace-manifest.json" or relative.endswith(".tmp"):
            continue
        artifacts[relative] = _file_sha256(path)
    manifest = {
        "schema_version": "text2ifc/run-trace-manifest/1.0",
        "trace_level": "compact" if any("/trace/" in key for key in artifacts) else "debug",
        "report_path": report_path.relative_to(root).as_posix(),
        "artifact_count": len(artifacts),
        "artifact_hashes": artifacts,
    }
    _write_text(
        root / "trace-manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
