"""Verify Phase 6.2-fix real REPL acceptance artifacts."""

from __future__ import annotations

import argparse
import json
import site
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))
USER_SITE = Path(site.getusersitepackages())
try:
    if USER_SITE.exists() or str(USER_SITE) not in sys.path:
        sys.path.append(str(USER_SITE))
except OSError:
    pass


DEFAULT_ROOT = ROOT / "dataset/processed/agent-demo/phase6.2-fix-repl"
REQUIRED_REPORT_SECTIONS = (
    "## REPL Interaction Evidence",
    "## Semantic Coverage",
    "## Final Artifacts",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--session-from", type=Path)
    args = parser.parse_args(argv)
    session_from = args.session_from or (args.root / "final-acceptance.json")
    result = verify(args.root, session_from=session_from)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


def verify(root: Path | str, *, session_from: Path | str) -> dict[str, Any]:
    active_root = Path(root)
    final_path = Path(session_from)
    if not final_path.is_absolute():
        final_path = active_root / final_path
    db_path = active_root / "sessions.sqlite"
    issues: list[str] = []
    missing: list[str] = []
    for label, path in (
        ("final-acceptance.json", final_path),
        ("sessions.sqlite", db_path),
    ):
        if not path.is_file():
            missing.append(label)

    final = _read_json(final_path) if final_path.is_file() else {}
    session_id = str(final.get("session_id", ""))
    session_hash = str(final.get("session_hash", ""))
    session_row = _load_session_row(db_path, session_id, session_hash) if db_path.is_file() else None
    if session_row is None:
        issues.append("session_missing_from_db")

    artifacts = final.get("artifacts", {}) if isinstance(final.get("artifacts"), dict) else {}
    report_path = active_root / str(artifacts.get("report", ""))
    export_path = active_root / str(artifacts.get("session_export", ""))
    run_dir = active_root / "runs" / session_hash if session_hash else report_path.parent
    semantic_coverage_path = run_dir / "semantic-coverage.json"
    if not report_path.is_file():
        missing.append("report.md")
    if not export_path.is_file():
        missing.append("session-export.json")
    export = _read_json(export_path) if export_path.is_file() else {}
    events = export.get("events", []) if isinstance(export, dict) else []
    started = _first_event(events, "repl_session_started")
    interaction_mode = str(started.get("payload", {}).get("interaction_mode", ""))
    input_source = str(started.get("payload", {}).get("input_source", ""))
    if interaction_mode != "human_repl_live":
        issues.append("human_repl_live")
    if input_source != "terminal":
        issues.append("terminal_input_required")
    if not _question_before_answer(events):
        issues.append("assistant_question_displayed_before_answer")

    report_text = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
    missing_report_sections = [
        section for section in REQUIRED_REPORT_SECTIONS if section not in report_text
    ]
    if missing_report_sections:
        issues.append("report_missing_repl_sections")

    output_ifc_reopenable = False
    if final.get("status") == "compiled":
        ifc_path = active_root / str(artifacts.get("ifc", ""))
        if not ifc_path.is_file():
            missing.append("output.ifc")
        output_ifc_reopenable = _ifc_reopens_as_ifc2x3(ifc_path)
        if ifc_path.is_file() and not output_ifc_reopenable:
            issues.append("output_ifc_not_reopenable")
        semantic_coverage = (
            _read_json(semantic_coverage_path)
            if semantic_coverage_path.is_file()
            else {}
        )
        if not semantic_coverage_path.is_file():
            issues.append("semantic_coverage_required")
        elif semantic_coverage.get("valid") is not True:
            issues.append("semantic_coverage_blocking_facts")
    elif artifacts.get("ifc"):
        issues.append("ifc_written_for_non_formal_outcome")

    metrics = _latest_metric(
        export,
        stages={"acceptance", "final-acceptance", "final_acceptance"},
    )
    audit_evidence_class = metrics.get("audit_evidence_class")
    if final.get("status") == "compiled" and audit_evidence_class not in {"live", "live-derived-no-call"}:
        issues.append("live_mimo_evidence_required")

    valid = bool(
        not missing
        and not issues
        and final.get("schema_version") == "text2ifc/phase6.2-fix-final-acceptance-v1"
        and session_row is not None
        and final.get("status") == "compiled"
        and output_ifc_reopenable
    )
    return {
        "valid": valid,
        "root": str(active_root),
        "session_id": session_id,
        "session_hash": session_hash,
        "missing": sorted(set(missing)),
        "issues": sorted(set(issues)),
        "interaction_mode": interaction_mode,
        "input_source": input_source,
        "output_ifc_reopenable": output_ifc_reopenable,
        "audit_evidence_class": audit_evidence_class,
        "missing_report_sections": missing_report_sections,
    }


def _first_event(events: list[Any], event_type: str) -> dict[str, Any]:
    for event in events:
        if isinstance(event, dict) and event.get("event_type") == event_type:
            return event
    return {}


def _question_before_answer(events: list[Any]) -> bool:
    ordered = [
        event.get("event_type")
        for event in events
        if isinstance(event, dict)
        and event.get("event_type")
        in {
            "assistant_question_displayed",
            "user_answer_requested",
            "user_answer_received",
        }
    ]
    if "user_answer_requested" not in ordered and "user_answer_received" not in ordered:
        return True
    try:
        question = ordered.index("assistant_question_displayed")
        requested = ordered.index("user_answer_requested")
        received = ordered.index("user_answer_received")
    except ValueError:
        return False
    return question < requested < received


def _latest_metric(export: dict[str, Any], *, stages: set[str]) -> dict[str, Any]:
    metrics = export.get("metrics", []) if isinstance(export, dict) else []
    for record in reversed(metrics):
        payload = record.get("payload", {}) if isinstance(record, dict) else {}
        if payload.get("stage") in stages:
            return payload
    return {}


def _load_session_row(db_path: Path, session_id: str, session_hash: str) -> dict[str, Any] | None:
    try:
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                """
                SELECT * FROM sessions
                WHERE session_id = ? OR session_hash = ?
                """,
                (session_id, session_hash),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            connection.close()
    except sqlite3.Error:
        return None


def _ifc_reopens_as_ifc2x3(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        import ifcopenshell

        model = ifcopenshell.open(str(path))
    except Exception:
        return False
    return model.schema == "IFC2X3"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
