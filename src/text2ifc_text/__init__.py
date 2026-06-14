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
from .evaluation import (
    EvaluationError,
    evaluate_pair_predictions,
    evaluate_prediction_cases,
    run_fixture_evaluation,
)

__all__ = [
    "EvaluationError",
    "GoldSetError",
    "PairGenerationError",
    "SplitManifestError",
    "build_formal_target_from_draft",
    "build_gold_set",
    "build_pair_manifest",
    "build_pair_records",
    "build_scene_family_splits",
    "check_scene_family_splits",
    "evaluate_pair_predictions",
    "evaluate_prediction_cases",
    "load_bimnet_manifest",
    "load_scene_families",
    "run_fixture_evaluation",
    "triage_extraction_audit",
]
