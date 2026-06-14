"""Deterministic Text-to-BIM-JSON pair generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PairGenerationError(ValueError):
    """Raised when pair generation would be unsafe or nondeterministic."""


def build_pair_records(gold_manifest_path: Path | str) -> list[dict[str, Any]]:
    raise NotImplementedError("Text-to-JSON pair generation is not implemented")


def build_pair_manifest(
    records: list[dict[str, Any]],
    *,
    source_manifest: Path | str,
) -> dict[str, Any]:
    raise NotImplementedError("Text-to-JSON pair manifesting is not implemented")
