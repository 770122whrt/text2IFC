"""Security and source-overwrite audit for persisted jsonfix artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = {
    "input.txt",
    "base.json",
    "patch.json",
    "composed.json",
    "diagnostics.json",
    "metrics.json",
    "report.md",
    "output.ifc",
    "provenance.json",
    "external-inventory.json",
}
TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".log",
    ".yaml",
    ".yml",
}
SECRET_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"\btp-[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    re.compile(
        r"https?://[^\s\"']*token-plan[^\s\"']*",
        re.IGNORECASE,
    ),
    re.compile(
        r'(?i)\b(api[_-]?key|auth[_-]?token|authorization|x-api-key)\b'
        r'\s*[:=]\s*["\']?[A-Za-z0-9._~+/=-]{8,}'
    ),
)


def _secret_findings(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in SECRET_PATTERNS):
                findings.append(
                    {
                        "code": "SECRET_LIKE_ARTIFACT_CONTENT",
                        "path": path.relative_to(root).as_posix(),
                        "line": line_number,
                    }
                )
    return findings


def _overwrite_findings(root: Path) -> list[dict[str, Any]]:
    provenance_path = root / "provenance.json"
    diagnostics_path = root / "diagnostics.json"
    if not provenance_path.is_file() or not diagnostics_path.is_file():
        return []
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    declared = {
        item.get("code")
        for item in diagnostics.get("composition", [])
        if isinstance(item, dict)
    }
    findings = []
    for fact in provenance.get("facts", []):
        if fact.get("origin") != "patch":
            continue
        changed_existing = bool(fact.get("overwrote_existing")) or (
            fact.get("previous_value") is not None
            and fact.get("previous_value") != fact.get("value")
        )
        if changed_existing and "SOURCE_FACT_OVERWRITTEN" not in declared:
            findings.append(
                {
                    "code": "UNDECLARED_SOURCE_OVERWRITE",
                    "path": fact.get("path", ""),
                    "layer_id": fact.get("layer_id"),
                }
            )
    return findings


def audit_jsonfix_artifacts(path: Path | str) -> dict[str, Any]:
    root = Path(path)
    present = {item.name for item in root.iterdir() if item.is_file()}
    missing = sorted(REQUIRED_ARTIFACTS - present)
    findings = [
        {
            "code": "MISSING_REQUIRED_ARTIFACT",
            "path": name,
        }
        for name in missing
    ]
    secret_findings = _secret_findings(root)
    overwrite_findings = _overwrite_findings(root)
    findings.extend(secret_findings)
    findings.extend(overwrite_findings)
    return {
        "schema_version": "text2ifc/jsonfix-artifact-audit-v1",
        "success": not findings,
        "scanned_path": str(root),
        "missing_required_artifact_count": len(missing),
        "secret_finding_count": len(secret_findings),
        "silent_overwrite_count": len(overwrite_findings),
        "findings": findings,
    }
