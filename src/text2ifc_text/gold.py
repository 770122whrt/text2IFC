"""Gold-set construction helpers for Phase 3 Text-to-JSON data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class GoldSetError(ValueError):
    """Raised when Draft triage or gold-set construction is unsafe."""


def triage_extraction_audit(
    audit_path: Path | str,
    split_manifest_path: Path | str,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 Draft triage is not implemented")


def build_formal_target_from_draft(
    draft: dict[str, Any],
    *,
    source_record: dict[str, Any],
    split: str,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 formal target promotion is not implemented")


def build_gold_set(
    manifest_path: Path | str,
    split_manifest_path: Path | str,
    *,
    output_dir: Path | str,
    extractor: Callable[[str | Path], Any] | None = None,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 gold-set construction is not implemented")
