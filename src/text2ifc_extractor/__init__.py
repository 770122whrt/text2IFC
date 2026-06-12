"""Public IFC2X3 extraction API."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractionResult:
    source_path: Path
    source_sha256: str = ""
    document: dict[str, Any] | None = None
    draft: dict[str, Any] | None = None
    inventory: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def losses(self) -> list[dict[str, Any]]:
        if self.draft is None:
            return []
        return list(self.draft.get("losses", []))


def extract_ifc2x3(path: str | Path) -> ExtractionResult:
    return ExtractionResult(source_path=Path(path).resolve())


__all__ = ["ExtractionResult", "extract_ifc2x3"]
