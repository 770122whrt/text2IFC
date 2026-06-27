"""Fact-level semantic support profile for current text2IFC generation."""

from __future__ import annotations

import hashlib
import json
from typing import Any


PROFILE_ID = "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0"


def build_semantic_capability_profile() -> dict[str, Any]:
    """Return the current fact-level support contract for model/gate use."""
    profile: dict[str, Any] = {
        "schema_version": "text2ifc/semantic-capability-profile/1.0",
        "profile_id": PROFILE_ID,
        "structural_truth": "schemas/bim-json/2.0/schema.json",
        "ifc_schema": "IFC2X3",
        "supported_fact_prefixes": [
            "/known_facts/building",
            "/known_facts/space",
            "/known_facts/walls",
            "/known_facts/slab",
            "/known_facts/door/host",
            "/known_facts/door/alignment",
            "/known_facts/door/height_mm",
            "/known_facts/door/width_mm",
            "/known_facts/window",
        ],
        "compiler_generated_fact_prefixes": [
            "/compiler_generated/owner_history",
            "/compiler_generated/local_placement_helpers",
            "/compiler_generated/void_fill_low_level_ifc",
        ],
        "unsupported_facts": [
            {
                "path": "/known_facts/door/opening_direction",
                "state": "unsupported",
                "reason": (
                    "Current BIM JSON 2.0 generation profile supports IfcDoor "
                    "dimensions and placement, but does not generate IfcDoorStyle "
                    "OperationType or door swing semantics."
                ),
                "current_ifc_boundary": "IfcDoorStyle.OperationType is not generated",
                "draft_required_unless_waived": True,
            }
        ],
        "custom_property_policy": {
            "state": "preserved_text_only",
            "counts_as_semantic_support": False,
        },
    }
    profile["profile_hash"] = _profile_hash(profile)
    return profile


def _profile_hash(profile: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in profile.items() if key != "profile_hash"
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
