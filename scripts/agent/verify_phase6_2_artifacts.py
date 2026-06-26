"""Verify Phase 6.2 DB-backed interactive CLI acceptance artifacts."""

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
    user_site_exists = USER_SITE.exists()
except OSError:
    user_site_exists = False
if user_site_exists or str(USER_SITE) not in sys.path:
    sys.path.append(str(USER_SITE))

import ifcopenshell  # noqa: E402


DEFAULT_ROOT = ROOT / "dataset/processed/agent-demo/phase6.2-interactive-cli"
REQUIRED_REPORT_SECTIONS = (
    "## Original Input",
    "## Transcript",
    "## Design Brief Agent",
    "## BIM JSON Generator",
    "## Repair Route",
    "## Audit Agent",
    "## Deterministic Gates",
    "## Final Artifacts",
    "## Session Export",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--session-from", type=Path, default=None)
    args = parser.parse_args(argv)
    session_from = args.session_from or (args.root / "final-acceptance.json")
    result = verify(args.root, session_from=session_from)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


def verify(root: Path | str, *, session_from: Path | str) -> dict[str, Any]:
    active_root = Path(root)
    final_path = Path(session_from)
    db_path = active_root / "sessions.sqlite"
    missing = []
    for label, path in (
        ("final-acceptance.json", final_path),
        ("sessions.sqlite", db_path),
    ):
        if not path.is_file():
            missing.append(label)

    final = _read_json(final_path) if final_path.is_file() else {}
    session_hash = str(final.get("session_hash", ""))
    session_id = str(final.get("session_id", ""))
    artifacts = final.get("artifacts", {}) if isinstance(final.get("artifacts"), dict) else {}
    run_dir = active_root / "runs" / session_hash if session_hash else active_root / "runs"
    required_artifacts = {
        "output.ifc": active_root / str(artifacts.get("ifc", "")),
        "report.md": active_root / str(artifacts.get("report", "")),
        "session-export.json": active_root / str(artifacts.get("session_export", "")),
        "acceptance-metrics.json": run_dir / "acceptance-metrics.json",
        "geometry-feedback.json": run_dir / "geometry-feedback.json",
        "ifc-verification.json": run_dir / "ifc-verification.json",
        "secret-scan.json": run_dir / "secret-scan.json",
    }
    for label, path in required_artifacts.items():
        if not path.is_file():
            missing.append(label)

    session_row = _load_session_row(db_path, session_id, session_hash) if db_path.is_file() else None
    session_in_db = session_row is not None
    session_status_matches = bool(session_row and session_row["status"] == final.get("status"))
    export_payload = (
        _read_json(required_artifacts["session-export.json"])
        if required_artifacts["session-export.json"].is_file()
        else {}
    )
    export_session = export_payload.get("session", {}) if isinstance(export_payload, dict) else {}
    export_matches_db_session = bool(
        session_row
        and export_session.get("session_id") == session_row["session_id"]
        and export_session.get("session_hash") == session_row["session_hash"]
    )

    output_ifc_reopenable = _ifc_reopens_as_ifc2x3(required_artifacts["output.ifc"])
    metrics = _read_json(required_artifacts["acceptance-metrics.json"]) if required_artifacts["acceptance-metrics.json"].is_file() else {}
    geometry = _read_json(required_artifacts["geometry-feedback.json"]) if required_artifacts["geometry-feedback.json"].is_file() else {}
    ifc_verification = _read_json(required_artifacts["ifc-verification.json"]) if required_artifacts["ifc-verification.json"].is_file() else {}
    secret_scan = _read_json(required_artifacts["secret-scan.json"]) if required_artifacts["secret-scan.json"].is_file() else {}
    report_text = (
        required_artifacts["report.md"].read_text(encoding="utf-8")
        if required_artifacts["report.md"].is_file()
        else ""
    )
    missing_report_sections = [
        section for section in REQUIRED_REPORT_SECTIONS if section not in report_text
    ]
    report_has_required_sections = not missing_report_sections
    artifact_paths = {
        record.get("path")
        for record in export_payload.get("artifacts", [])
        if isinstance(record, dict)
    }
    export_links_required_artifacts = all(
        value in artifact_paths
        for value in (
            artifacts.get("ifc"),
            artifacts.get("report"),
            artifacts.get("session_export"),
        )
    )

    valid = bool(
        not missing
        and final.get("schema_version") == "text2ifc/phase6.2-final-acceptance-v1"
        and final.get("status") == "compiled"
        and session_in_db
        and session_status_matches
        and export_matches_db_session
        and export_links_required_artifacts
        and output_ifc_reopenable
        and metrics.get("valid") is True
        and metrics.get("audit_evidence_class") == "live"
        and metrics.get("compile_reopen_success") is True
        and metrics.get("geometry_success") is True
        and geometry.get("success") is True
        and ifc_verification.get("success") is True
        and secret_scan.get("finding_count") == 0
        and report_has_required_sections
    )
    return {
        "valid": valid,
        "root": str(active_root),
        "session_id": session_id,
        "session_hash": session_hash,
        "missing": sorted(set(missing)),
        "session_in_db": session_in_db,
        "session_status_matches": session_status_matches,
        "export_matches_db_session": export_matches_db_session,
        "export_links_required_artifacts": export_links_required_artifacts,
        "output_ifc_reopenable": output_ifc_reopenable,
        "geometry_success": geometry.get("success") is True,
        "compile_reopen_success": ifc_verification.get("success") is True,
        "metrics_valid": metrics.get("valid") is True,
        "audit_evidence_class": metrics.get("audit_evidence_class"),
        "secret_finding_count": secret_scan.get("finding_count"),
        "report_has_required_sections": report_has_required_sections,
        "missing_report_sections": missing_report_sections,
    }


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
        model = ifcopenshell.open(str(path))
    except Exception:
        return False
    return model.schema == "IFC2X3"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
