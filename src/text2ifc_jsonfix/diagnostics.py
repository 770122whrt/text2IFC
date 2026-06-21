"""Machine-readable diagnostics for additive BIM JSON composition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, order=True)
class CompositionDiagnostic:
    severity: str
    code: str
    path: str
    message: str
    layer_id: str | None = None
    operation_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def diagnostic(
    code: str,
    path: str,
    message: str,
    *,
    severity: str = "error",
    layer_id: str | None = None,
    operation_index: int | None = None,
) -> CompositionDiagnostic:
    return CompositionDiagnostic(
        severity=severity,
        code=code,
        path=path,
        message=message,
        layer_id=layer_id,
        operation_index=operation_index,
    )
