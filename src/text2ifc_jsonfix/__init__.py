"""IFCx-inspired additive repair tools for BIM JSON."""

from .validation import load_patch_schema, validate_patch_document

__all__ = ["load_patch_schema", "validate_patch_document"]
