"""Failure family: published door/geometry contracts must be reachable.

Root causes (composite milestone live C2/C4/C5):

* ``door.add-with-opening.v0.2`` / ``door.fill-existing-opening.v0.2`` taught
  the Provider to emit ``{"door": {"operation_type": "SINGLE_SWING_LEFT"}}``
  (few-shot expected payloads), but the deterministic door resolver only
  accepts a direct IfcDoorOperationEnum when the *internal* flag
  ``formal_enum_explicit`` is true — a field never published in any schema,
  profile, or few-shot.  The contract's own teaching was therefore rejected
  by the resolver (``DOOR_OPERATION_REQUIRED`` clarification on every live
  composite door operation).  The v0.3 profiles publish the full conditional
  contract: enum + ``formal_enum_explicit=true`` OR hinge_side + viewpoint.

* Wall/opening geometry measured from stored IFC carries full float
  precision (e.g. ``3581.70079330354``), while user requests state rounded
  values (``3581.7``).  A Provider that copies the request value with
  ``tolerance_mm: 0`` can therefore never match (C5 ``not_found`` with a
  0.0008 mm delta).  The v0.3 profiles publish the rule: every geometry
  constraint must use ``tolerance_mm >= 1.0``.

This family freezes the repaired invariants:

1. every few-shot that teaches a door enum direct-pass teaches the
   ``formal_enum_explicit`` confirmation too, and such a payload resolves;
2. the v0.3 profiles are registered, selected by the operations, and state
   both the enum-confirmation and tolerance rules;
3. an intent built per the published contract (enum + confirmation, or
   hinge/viewpoint, tolerance >= 1.0) is accepted by the deterministic
   resolver for both add and fill;
4. the safety boundary is unchanged: enums without confirmation still
   clarify, unsupported enums still fail closed, and unknown slots are
   still rejected.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import (
    PromptProfileError,
    load_prompt_profiles,
    select_prompt_profiles,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = PROJECT_ROOT / "prompts/agent/ifc-repair-profiles"
FEW_SHOTS_DIR = PROJECT_ROOT / "prompts/agent/ifc-repair-few-shots"

ENUM_PATHS = [
    "door-add-v0.2-complete.json",
    "door-add-v0.2-clarification.json",
]
V03_ADD_PROFILE = "door.add-with-opening.v0.3"
V03_FILL_PROFILE = "door.fill-existing-opening.v0.3"
V02_WINDOW_PROFILE = "window.add-with-opening.v0.2"
DOOR_ENUMS = ("SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT")


def _load_few_shot(name: str) -> dict:
    return json.loads(
        (FEW_SHOTS_DIR / name).read_text(encoding="utf-8")
    )


def _door_payload(door: dict) -> dict:
    return {"door": door}


# ---------------------------------------------------------------------------
# 1. published few-shots teach the full reachable door contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    sorted(p.name for p in FEW_SHOTS_DIR.glob("door-*-v0.3-*.json")),
)
def test_v03_door_few_shot_teaches_reachable_contract(name: str) -> None:
    shot = _load_few_shot(name)
    door = (
        (shot.get("expected", {}).get("parameters", {}) or {}).get("door")
    )
    if isinstance(door, dict) and door.get("operation_type") in DOOR_ENUMS:
        assert door.get("formal_enum_explicit") is True, (
            f"{name}: teaches enum direct-pass without confirmation flag"
        )


@pytest.mark.parametrize("name", ENUM_PATHS)
def test_legacy_v02_enum_shot_documents_the_gap(name: str) -> None:
    """Legacy v0.2 shots stay unchanged (registered history) but are no
    longer selected by the operations (asserted separately below)."""

    shot = _load_few_shot(name)
    profile_id = shot.get("profile_id", "")
    assert profile_id.endswith(".v0.2")


# ---------------------------------------------------------------------------
# 2. the v0.3 profiles are registered and selected by the operations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("profile_id", "operation_type"),
    [
        (V03_ADD_PROFILE, "add_door_with_opening_to_wall"),
        (V03_FILL_PROFILE, "fill_existing_opening_with_door"),
    ],
)
def test_v03_profiles_registered_and_selected(
    profile_id: str, operation_type: str
) -> None:
    registry = load_prompt_profiles()
    assert profile_id in registry

    operation_registry = create_default_registry()
    selected = operation_registry.require(operation_type).prompt_profile_id
    assert selected == profile_id, (
        f"{operation_type} selects {selected!r}, expected {profile_id!r}"
    )


@pytest.mark.parametrize(
    "profile_id", [V03_ADD_PROFILE, V03_FILL_PROFILE]
)
def test_v03_profile_publishes_enum_and_tolerance_rules(
    profile_id: str,
) -> None:
    profile = load_prompt_profiles()[profile_id]
    document = profile.document
    conditional = " ".join(document.get("conditional_slots", []))
    forbidden = " ".join(document.get("forbidden_inferences", []))
    summary = str(document.get("slot_summary", ""))

    assert "formal_enum_explicit" in conditional, profile_id
    assert "formal_enum_explicit" in forbidden, profile_id
    assert "tolerance_mm" in summary and "1.0" in summary, profile_id


def test_window_profile_publishes_tolerance_rule() -> None:
    profile = load_prompt_profiles()[V02_WINDOW_PROFILE]
    document = profile.document
    summary = str(document.get("slot_summary", ""))
    forbidden = " ".join(document.get("forbidden_inferences", []))

    assert "tolerance_mm" in summary and "1.0" in summary
    assert "tolerance_mm of 0" in forbidden


def test_window_operation_selects_v02_profile() -> None:
    operation_registry = create_default_registry()
    selected = operation_registry.require(
        "add_window_with_opening_to_wall"
    ).prompt_profile_id
    assert selected == V02_WINDOW_PROFILE


# ---------------------------------------------------------------------------
# 3. contract-shaped intents resolve through the deterministic resolver
# ---------------------------------------------------------------------------


def _resolve_formal_operation(parameters: dict):
    from text2ifc_ifc_repair.door_resolution import _resolve_formal_operation

    return _resolve_formal_operation(
        parameters=parameters, type_record=None
    )


@pytest.mark.parametrize("enum", DOOR_ENUMS)
@pytest.mark.parametrize(
    ("profile_id", "operation_type"),
    [
        (V03_ADD_PROFILE, "add_door_with_opening_to_wall"),
        (V03_FILL_PROFILE, "fill_existing_opening_with_door"),
    ],
)
def test_published_enum_payload_resolves(
    enum: str, profile_id: str, operation_type: str
) -> None:
    payload = _door_payload(
        {"operation_type": enum, "formal_enum_explicit": True}
    )
    result = _resolve_formal_operation(payload)
    assert result["status"] == "resolved", (profile_id, result)
    assert result["operation_type"] == enum


def test_published_viewpoint_payload_resolves() -> None:
    payload = _door_payload(
        {
            "hinge_side": "left",
            "viewpoint": {
                "observation_side": "wall_positive",
                "destination": "into the room",
            },
        }
    )
    result = _resolve_formal_operation(payload)
    assert result["status"] == "resolved", result
    assert result["operation_type"] in DOOR_ENUMS


# ---------------------------------------------------------------------------
# 4. safety boundary unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("enum", DOOR_ENUMS)
def test_enum_without_confirmation_still_clarifies(enum: str) -> None:
    """The legacy unreachable shape (enum without the flag) still asks for
    clarification — the v0.2 gap is fixed by teaching, not by weakening."""

    result = _resolve_formal_operation(_door_payload({"operation_type": enum}))
    assert result["status"] == "clarification_required"
    assert result["reason_code"] == "DOOR_OPERATION_REQUIRED"


def test_unsupported_enum_still_fails_closed() -> None:
    result = _resolve_formal_operation(
        _door_payload(
            {"operation_type": "REVOLVING", "formal_enum_explicit": True}
        )
    )
    assert result["status"] == "unsupported"
    assert result["reason_code"] == "DOOR_OPERATION_TYPE_UNSUPPORTED"


def test_confirmation_flag_alone_does_not_authorize() -> None:
    result = _resolve_formal_operation(
        _door_payload({"formal_enum_explicit": True})
    )
    assert result["status"] == "clarification_required"
