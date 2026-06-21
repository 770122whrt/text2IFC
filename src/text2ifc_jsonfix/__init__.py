"""IFCx-inspired additive repair tools for BIM JSON."""

from .composer import CompositionResult, compose_patches
from .handoff import (
    RepairHandoffResult,
    render_repair_prompt,
    run_repair_handoff,
)
from .provenance import build_provenance_report
from .repair_cases import build_repair_case, repair_case
from .validation import load_patch_schema, validate_patch_document

__all__ = [
    "CompositionResult",
    "RepairHandoffResult",
    "build_provenance_report",
    "build_repair_case",
    "compose_patches",
    "load_patch_schema",
    "repair_case",
    "render_repair_prompt",
    "run_repair_handoff",
    "validate_patch_document",
]
