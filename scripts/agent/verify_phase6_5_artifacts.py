"""Verify deterministic Phase 6.5 matrix artifacts and secret safety."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|auth[_-]?token)\s*[:=]\s*[^\s\"']{8,}"),
    re.compile(r"(?i)bearer\s+[a-z0-9._-]{12,}"),
)
TEXT_SUFFIXES = {".json", ".md", ".txt", ".jsonl"}


def verify(root: Path | str) -> dict[str, Any]:
    output = Path(root)
    matrix_path = output / "matrix-result.json"
    issues: list[str] = []
    matrix = _read_json(matrix_path) if matrix_path.is_file() else {}
    if not matrix:
        issues.append("MATRIX_RESULT_MISSING")
    rows = matrix.get("cases", []) if isinstance(matrix, dict) else []
    accepted_multistorey = 0
    false_accept = 0
    for row in rows:
        case_id = str(row.get("case_id", ""))
        case_path = output / case_id / "case-result.json"
        stored = _read_json(case_path) if case_path.is_file() else {}
        if stored != row:
            issues.append("CASE_RESULT_MISMATCH")
        evidence_row = stored or row
        accepted = row.get("outcome") == "accepted"
        gates = row.get("gates", {})
        if accepted and not all(gates.values()):
            false_accept += 1
            issues.append("FALSE_ACCEPT_BLOCKING_GATE")
        if accepted and case_id in {"two-storey-accepted", "three-storey-accepted"}:
            accepted_multistorey += 1
            if not (output / case_id / "output.ifc").is_file():
                issues.append("ACCEPTED_IFC_MISSING")
        if accepted and float(evidence_row.get("preservation_rate", 0.0)) != 1.0:
            issues.append("PRESERVATION_EVIDENCE_INVALID")
    findings = _secret_findings(output)
    if findings:
        issues.append("SECRET_FINDING")
    result = {
        "schema_version": "text2ifc/phase6.5-verification/1.0",
        "valid": not issues,
        "issue_codes": sorted(set(issues)),
        "case_count": len(rows),
        "accepted_multistorey_count": accepted_multistorey,
        "false_accept_count": false_accept,
        "secret_finding_count": len(findings),
        "secret_findings": findings,
    }
    _write_json(output / "final-verification.json", result)
    return result


def _secret_findings(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append({"path": path.relative_to(root).as_posix(), "code": "SECRET_LIKE_TEXT"})
    return findings


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify(args.root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
