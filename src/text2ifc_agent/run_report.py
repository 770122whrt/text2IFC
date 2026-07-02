"""Generated human-review reports for live Phase 6.1 runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
    lines.extend(_metrics_section(root))
    lines.extend(_source_sidecars_section(root))
    _write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return report_path


def _require_sidecars(root: Path) -> None:
    for _title, directory, files in STAGE_SIDECARS:
        stage_dir = resolve_final_design_brief_dir(root) if directory == "design-brief" else root / directory
        for name in files:
            path = stage_dir / name
            if not path.is_file():
                relative = path.relative_to(root).as_posix()
                raise RunReportError(f"required sidecar is missing: {relative}")


def _stage_section(root: Path, title: str, stage_dir: Path) -> list[str]:
    raw = _read_json(stage_dir / "response.raw.json")
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
        _source_link(f"{relative_stage}/response.raw.json"),
        _source_link(f"{relative_stage}/model-text.txt"),
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


def _source_sidecars_section(root: Path) -> list[str]:
    lines = ["## Source Sidecars", ""]
    for title, directory, files in STAGE_SIDECARS:
        stage_dir = resolve_final_design_brief_dir(root) if directory == "design-brief" else root / directory
        relative_stage = stage_dir.relative_to(root).as_posix()
        lines.extend([f"### {title}", ""])
        for name in files:
            relative = f"{relative_stage}/{name}"
            if (root / relative).is_file():
                lines.append(f"- [{relative}]({relative})")
        lines.append("")
    existing_gates = [name for name in GATE_SIDECARS if (root / name).is_file()]
    if existing_gates:
        lines.extend(["### Generated IFC Gates", ""])
        for name in existing_gates:
            lines.append(f"- [{name}]({name})")
        lines.append("")
    return lines


def _first_existing(stage_dir: Path, names: tuple[str, ...]) -> str | None:
    for name in names:
        if (stage_dir / name).is_file():
            return name
    return None


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


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
