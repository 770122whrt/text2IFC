"""Shared secret-like value scanning for Agent trace artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "text2ifc/agent-artifact-scan-v1"
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".log", ".yaml", ".yml"}
ALLOWED_ENV_NAMES = {
    "API_KEY",
    "MIMO_API_KEY",
    "DEEPSEEK_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "TEXT2IFC_MIMO_MODEL",
    "TEXT2IFC_DEEPSEEK_MODEL",
    "TEXT2IFC_DEEPSEEK_MAX_TOKENS",
    "TEXT2IFC_PROVIDER",
}
SECRET_PATTERNS = (
    ("SECRET_LIKE_PATTERN", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE)),
    ("SECRET_LIKE_PATTERN", re.compile(r"\btp-[A-Za-z0-9_-]{12,}", re.IGNORECASE)),
    ("PRIVATE_PROVIDER_URL", re.compile(r"https?://[^\s\"']*token-plan[^\s\"']*", re.IGNORECASE)),
    (
        "SECRET_LIKE_PATTERN",
        re.compile(
            r"(?i)\b(api[_-]?key|auth[_-]?token|authorization|x-api-key)\b"
            r"\s*[:=]\s*[\"']?(?!API_KEY\b|MIMO_API_KEY\b|DEEPSEEK_API_KEY\b|ANTHROPIC_AUTH_TOKEN\b|TEXT2IFC_MIMO_MODEL\b|TEXT2IFC_DEEPSEEK_MODEL\b)"
            r"[A-Za-z0-9._~+/=-]{8,}"
        ),
    ),
)


def scan_path(path: Path | str) -> dict[str, Any]:
    root = Path(path).resolve()
    files = _iter_scan_files(root)
    findings: list[dict[str, Any]] = []
    for item in files:
        text = item.read_text(encoding="utf-8", errors="ignore")
        relative = item.name if root.is_file() else item.relative_to(root).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            scrubbed = line
            for env_name in ALLOWED_ENV_NAMES:
                scrubbed = scrubbed.replace(env_name, "")
            for code, pattern in SECRET_PATTERNS:
                if pattern.search(scrubbed):
                    findings.append({"code": code, "path": relative, "line": line_number})
    return {
        "schema_version": SCHEMA_VERSION,
        "scanned_path": str(path),
        "scanned_file_count": len(files),
        "finding_count": len(findings),
        "findings": findings,
    }


def _iter_scan_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return [item for item in sorted(path.rglob("*")) if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES]
