"""Text-to-BIM-JSON dataset and baseline helpers."""

from .splits import (
    SplitManifestError,
    build_scene_family_splits,
    check_scene_family_splits,
    load_bimnet_manifest,
    load_scene_families,
)
from .gold import (
    GoldSetError,
    build_formal_target_from_draft,
    build_gold_set,
    triage_extraction_audit,
)

__all__ = [
    "GoldSetError",
    "SplitManifestError",
    "build_formal_target_from_draft",
    "build_gold_set",
    "build_scene_family_splits",
    "check_scene_family_splits",
    "load_bimnet_manifest",
    "load_scene_families",
    "triage_extraction_audit",
]
