"""Scene-family split helpers for Phase 3 Text-to-JSON data."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SplitManifestError(ValueError):
    """Raised when a split manifest or source manifest is unsafe."""


def load_bimnet_manifest(path: Path | str) -> list[dict[str, Any]]:
    raise NotImplementedError("Phase 3 split manifest loading is not implemented")


def load_scene_families(path: Path | str) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 scene family loading is not implemented")


def build_scene_family_splits(
    manifest_path: Path | str,
    families_path: Path | str,
    *,
    seed: int = 20260614,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 scene-family split builder is not implemented")


def check_scene_family_splits(payload: dict[str, Any]) -> None:
    raise NotImplementedError("Phase 3 split checker is not implemented")
