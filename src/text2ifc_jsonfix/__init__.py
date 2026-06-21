"""IFCx-inspired additive repair tools for BIM JSON."""

from .composer import CompositionResult, compose_patches
from .validation import load_patch_schema, validate_patch_document

__all__ = [
    "CompositionResult",
    "compose_patches",
    "load_patch_schema",
    "validate_patch_document",
]
