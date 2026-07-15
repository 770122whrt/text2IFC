import importlib
import importlib.util
import json
from pathlib import Path

import pytest


def _run_report():
    name = "text2ifc_agent.run_report"
    assert importlib.util.find_spec(name) is not None, "live run report module is missing"
    return importlib.import_module(name)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_minimal_case(case_dir: Path) -> Path:
    design = case_dir / "design-brief"
    generator = case_dir / "generator"
    repair = case_dir / "repair"
    audit = case_dir / "audit"
    _write_text(design / "input.txt", "创建一个6米乘4米的房间。\n")
    _write_json(design / "conversation.json", [{"role": "user", "content": "创建一个6米乘4米的房间。"}])
    _write_text(design / "prompt-rendered.md", "Design Brief prompt")
    _write_json(design / "request.redacted.json", {"request": {"model": "mimo-v2.5-pro"}})
    _write_json(design / "response.raw.json", {"id": "msg_design", "stop_reason": "end_turn"})
    _write_text(design / "model-text.txt", '{"status":"ready"}')
    _write_json(design / "design-brief.json", {"status": "ready"})
    _write_json(design / "validation.json", {"valid": True, "issues": []})
    _write_json(design / "metrics.json", {"response_id": "msg_design", "evidence_class": "live"})

    _write_text(generator / "prompt-rendered.md", "Generator prompt")
    _write_json(generator / "response.raw.json", {"id": "msg_generator", "stop_reason": "end_turn"})
    _write_text(generator / "model-text.txt", '{"schema_version":"bim-json/2.0"}')
    _write_json(generator / "design-brief.json", {"status": "ready"})
    _write_json(generator / "candidate.json", {"schema_version": "bim-json/2.0"})
    _write_json(generator / "validation.json", {"valid": True, "issues": []})
    _write_json(generator / "metrics.json", {"response_id": "msg_generator", "evidence_class": "live"})

    _write_json(repair / "route.json", {"route": "no_repair_needed", "provider_call_count": 0})
    _write_json(repair / "repair-attempts.json", [])
    _write_json(repair / "metrics.json", {"route": "no_repair_needed", "evidence_class": "live-derived-no-call"})

    _write_text(audit / "prompt-rendered.md", "Audit prompt")
    _write_json(audit / "response.raw.json", {"id": "msg_audit", "stop_reason": "end_turn"})
    _write_text(audit / "model-text.txt", '{"recommendation":"accept"}')
    _write_json(audit / "audit-report.json", {"recommendation": "accept", "blocking": False})
    _write_json(audit / "validation.json", {"valid": True, "issues": []})
    _write_json(audit / "metrics.json", {"response_id": "msg_audit", "evidence_class": "live"})
    return case_dir


def test_live_report_is_generated_from_stage_sidecars_and_links_every_stage(tmp_path: Path):
    run_report = _run_report()
    case_dir = _write_minimal_case(tmp_path / "complete-room")

    report_path = run_report.build_live_run_report(case_dir=case_dir)

    report = report_path.read_text(encoding="utf-8")
    for heading in (
        "## Original Input",
        "## Conversation",
        "## Design Brief Agent",
        "## BIM JSON Generator",
        "## Repair Route",
        "## Audit Agent",
        "## Metrics",
        "## Source Sidecars",
    ):
        assert heading in report
    for relative in (
        "design-brief/prompt-rendered.md",
        "design-brief/response.raw.json",
        "generator/candidate.json",
        "repair/route.json",
        "audit/audit-report.json",
    ):
        assert f"({relative})" in report
    assert "msg_design" in report
    assert "msg_generator" in report
    assert "msg_audit" in report
    assert "Source: [generator/candidate.json](generator/candidate.json)" in report
    assert "Source: [generator/design-brief.json](generator/design-brief.json)" not in report


def test_live_report_rejects_missing_material_sidecar(tmp_path: Path):
    run_report = _run_report()
    case_dir = _write_minimal_case(tmp_path / "complete-room")
    (case_dir / "generator" / "model-text.txt").unlink()

    with pytest.raises(run_report.RunReportError, match="generator/model-text.txt"):
        run_report.build_live_run_report(case_dir=case_dir)
