"""IFCx-inspired additive repair tools for BIM JSON."""

from .artifact_audit import audit_jsonfix_artifacts
from .composer import CompositionResult, compose_patches
from .demo import run_missing_piece_demo
from .handoff import (
    RepairHandoffResult,
    render_repair_prompt,
    run_repair_handoff,
)
from .ifc_artifact import check_ifc2x3_artifact, parse_step_schema
from .provenance import build_provenance_report
from .repair_cases import build_repair_case, repair_case
from .validation import load_patch_schema, validate_patch_document

__all__ = [
    "CompositionResult",
    "RepairHandoffResult",
    "audit_jsonfix_artifacts",
    "build_provenance_report",
    "build_repair_case",
    "check_ifc2x3_artifact",
    "compose_patches",
    "load_patch_schema",
    "parse_step_schema",
    "repair_case",
    "render_repair_prompt",
    "run_missing_piece_demo",
    "run_repair_handoff",
    "validate_patch_document",
]
