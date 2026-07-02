"""Trace-level policy for Phase 6.3."""

from __future__ import annotations

from typing import Literal


TraceLevel = Literal["compact", "debug", "full"]
DEFAULT_TRACE_LEVEL: TraceLevel = "compact"
TRACE_LEVELS: tuple[TraceLevel, ...] = ("compact", "debug", "full")


class TraceLevelError(ValueError):
    """Raised for unsupported trace-level values."""


def normalize_trace_level(value: str | None) -> TraceLevel:
    if value is None or value == "":
        return DEFAULT_TRACE_LEVEL
    if value not in TRACE_LEVELS:
        raise TraceLevelError("trace level must be one of compact|debug|full")
    return value  # type: ignore[return-value]


def should_preserve_deep_evidence(
    *,
    route: str | None,
    validation_valid: bool | None,
) -> bool:
    """Return whether compact mode must keep deep evidence for auditability."""
    if validation_valid is False:
        return True
    return route not in {None, "", "accept"}
