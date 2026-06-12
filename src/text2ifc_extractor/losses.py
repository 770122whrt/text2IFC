"""Stable extraction loss records."""

from __future__ import annotations

from typing import Any


def loss(
    source_ref: str,
    path: str,
    kind: str,
    message: str,
) -> dict[str, Any]:
    return {
        "source_ref": source_ref,
        "path": path,
        "kind": kind,
        "message": message,
    }


def sort_losses(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            item["source_ref"],
            item["path"],
            item["kind"],
            item["message"],
        ),
    )
