"""Integration boundary: active profiles must preserve current explicit-input policy."""
from pathlib import Path
import hashlib
import pytest
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import load_prompt_profiles
from text2ifc_ifc_repair.request_stage import _INTENT_CONTRACTS
from text2ifc_ifc_repair.repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_8, REPAIR_INTENT_SCHEMA_VERSION_0_9

@pytest.mark.parametrize("operation,profile_id", [
    ("add_door_with_opening_to_wall", "door.add-with-opening.v0.4"),
    ("fill_existing_opening_with_door", "door.fill-existing-opening.v0.4"),
    ("add_window_with_opening_to_wall", "window.add-with-opening.v0.3"),
])
def test_current_profile_preserves_explicit_tolerance(operation, profile_id):
    selected = create_default_registry().require(operation).prompt_profile_id
    assert selected == profile_id
    doc = load_prompt_profiles()[selected].document
    summary = doc["slot_summary"]
    assert "Omit unstated tolerance_mm" in summary
    assert "explicit zero" in summary
    assert "0.1 mm" in summary
    assert "never 0" not in summary
    assert "tolerance_mm of 0 on any geometry constraint" not in doc["forbidden_inferences"]

def test_schema_08_and_09_keep_distinct_published_prompts():
    assert _INTENT_CONTRACTS[REPAIR_INTENT_SCHEMA_VERSION_0_8][1] == "ifc-repair-intent.v0.11"
    assert _INTENT_CONTRACTS[REPAIR_INTENT_SCHEMA_VERSION_0_9][1] == "ifc-repair-intent.v0.12"


@pytest.mark.parametrize("version", ["0.5", "0.6", "0.7", "0.8", "0.9"])
@pytest.mark.parametrize("current,legacy", [
    ("door.add-with-opening.v0.4", "door.add-with-opening.v0.2"),
    ("door.fill-existing-opening.v0.4", "door.fill-existing-opening.v0.2"),
    ("window.add-with-opening.v0.3", "window.add-with-opening"),
])
def test_old_intent_contracts_keep_current_branch_routing(version, current, legacy):
    from text2ifc_ifc_repair.request_stage import _profile_id_for_intent_contract
    assert _profile_id_for_intent_contract(current, intent_schema_version=f"text2ifc/ifc-repair-intent/{version}") == legacy
