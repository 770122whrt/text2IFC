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


def build_semantic_capability_profile_v21() -> dict[str, Any]:
    profile = build_semantic_capability_profile()
    profile['profile_id'] = 'text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0'
    profile['structural_truth'] = 'schemas/bim-json/2.1/schema.json'
    profile['supported_fact_prefixes'].append('/known_facts/semantic_requirements')
    profile['basic_filling_templates'] = ['window-single', 'window-double-vertical', 'door-left', 'door-right']
    profile['unsupported_facts'][0]['reason'] = 'Room-relative swing direction requires spatial authorization; left/right handing is supported through the basic_filling template contract.'
    profile['unsupported_facts'][0]['current_ifc_boundary'] = 'Basic filling authors SINGLE_SWING_LEFT/RIGHT DoorStyle; room-relative opening direction is not inferred.'
    profile['material_policy'] = 'explicit_only; single material or supported complete layers; reopened verification required'
    profile['type_policy'] = 'project_local_request_groups_only'
    profile['appearance_policy'] = 'explicit_user_then_type_then_material_then_coordinated_default'
    profile['profile_hash'] = _profile_hash(profile)
    return profile


def build_semantic_capability_profile_v22() -> dict[str, Any]:
    profile = build_semantic_capability_profile_v21()
    profile['profile_id'] = 'text2ifc/semantic-capabilities/ifc2x3-bim-json-2.2/1.0'
    profile['structural_truth'] = 'schemas/bim-json/2.2/schema.json'
    profile['part_appearance'] = {'IfcDoor': ['frame', 'panel'], 'IfcWindow': ['frame', 'glazing'],
        'channels': ['color', 'transparency'], 'scope': 'explicit basic_filling occurrence only',
        'unspecified': 'theme defaults', 'whole_appearance_conflict': 'clarification_required'}
    profile['profile_hash'] = _profile_hash(profile)
    return profile


def build_semantic_capability_profile_v23() -> dict[str, Any]:
    profile = build_semantic_capability_profile_v22()
    profile['profile_id'] = 'text2ifc/semantic-capabilities/ifc2x3-bim-json-2.3/1.0'
    profile['structural_truth'] = 'schemas/bim-json/2.3/schema.json'
    profile['supported_fact_prefixes'].extend(['/known_facts/columns', '/known_facts/beams', '/known_facts/railings'])
    profile['basic_railing'] = {'template_id': 'metal-picket', 'version': 'text2ifc/basic-railing/1.0',
        'scope': 'straight horizontal or signed slope; IfcRailing occurrence; single material and whole appearance',
        'geometry_authority': 'explicit world baseline endpoints, vertical height and depth; no inferred position or size'}
    profile['structural_geometry'] = 'Explicit world_axis_aligned_box in mm for columns and beams; reopened family, storey and bounds checks, no structural certification.'
    profile['profile_hash'] = _profile_hash(profile)
    return profile
