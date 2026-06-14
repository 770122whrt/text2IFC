"""Supported-scope projection for Phase 3 formal Text-to-JSON targets."""

from __future__ import annotations

from typing import Any


class ProjectionError(ValueError):
    """Raised when a Draft partial document cannot be projected safely."""


def project_supported_scope_target(
    document: dict[str, Any],
    *,
    source_record: dict[str, Any],
) -> dict[str, Any]:
    raise NotImplementedError("supported-scope projection is not implemented")
