"""Extraction output verification."""

from __future__ import annotations

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.validation_v2 import validate_v2_document

from .inventory import verify_inventory


def verify_output(document, draft, inventory) -> None:
    verify_inventory(inventory)
    issues = validate_draft(draft) if draft is not None else validate_v2_document(document)
    if issues:
        rendered = "; ".join(f"{item.code} {item.path}" for item in issues[:10])
        raise ValueError(f"invalid extraction output: {rendered}")
