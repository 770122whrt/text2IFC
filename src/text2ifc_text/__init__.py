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
from .pairs import (
    PairGenerationError,
    build_pair_manifest,
    build_pair_records,
)

__all__ = [
    "GoldSetError",
    "PairGenerationError",
    "SplitManifestError",
    "build_formal_target_from_draft",
    "build_gold_set",
    "build_pair_manifest",
    "build_pair_records",
    "build_scene_family_splits",
    "check_scene_family_splits",
    "load_bimnet_manifest",
    "load_scene_families",
    "triage_extraction_audit",
]
