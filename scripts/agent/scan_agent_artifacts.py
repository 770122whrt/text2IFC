"""Scan Agent demo artifacts for persisted secret-like values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "text2ifc/agent-artifact-scan-v1"
TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".log",
    ".yaml",
    ".yml",
}
ALLOWED_ENV_NAMES = {
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "TEXT2IFC_MIMO_MODEL",
}
SECRET_PATTERNS = [
    (
        "SECRET_LIKE_PATTERN",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    ),
    (
        "SECRET_LIKE_PATTERN",
        re.compile(r"\btp-[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    ),
    (
        "PRIVATE_PROVIDER_URL",
        re.compile(r"https?://[^\s\"']*token-plan[^\s\"']*", re.IGNORECASE),
    ),
    (
        "SECRET_LIKE_PATTERN",
        re.compile(
            r'(?i)\b(api[_-]?key|auth[_-]?token|authorization|x-api-key)\b'
            r'\s*[:=]\s*["\']?(?!ANTHROPIC_AUTH_TOKEN\b|TEXT2IFC_MIMO_MODEL\b)'
            r'[A-Za-z0-9._~+/=-]{8,}'
        ),
    ),
]


def _iter_scan_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return [
        item
        for item in sorted(path.rglob("*"))
        if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES
    ]


def _line_findings(relative_path: str, line_number: int, line: str) -> list[dict[str, Any]]:
    scrubbed = line
    for env_name in ALLOWED_ENV_NAMES:
        scrubbed = scrubbed.replace(env_name, "")
    findings = []
    for code, pattern in SECRET_PATTERNS:
        if pattern.search(scrubbed):
            findings.append(
                {
                    "code": code,
                    "path": relative_path,
                    "line": line_number,
                }
            )
    return findings


def scan_path(path: Path) -> dict[str, Any]:
    root = path.resolve()
    findings: list[dict[str, Any]] = []
    for item in _iter_scan_files(root):
        try:
            text = item.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = item.read_text(encoding="utf-8", errors="ignore")
        try:
            relative_path = str(item.resolve().relative_to(root))
        except ValueError:
            relative_path = str(item)
        for line_number, line in enumerate(text.splitlines(), start=1):
            findings.extend(_line_findings(relative_path, line_number, line))
    return {
        "schema_version": SCHEMA_VERSION,
        "scanned_path": str(path),
        "scanned_file_count": len(_iter_scan_files(root)),
        "finding_count": len(findings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    arguments = parser.parse_args()
    result = scan_path(arguments.path)
    print(json.dumps(result, sort_keys=True))
    return 2 if result["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
