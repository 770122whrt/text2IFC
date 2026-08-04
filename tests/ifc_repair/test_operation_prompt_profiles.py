from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import (
    DEFAULT_PROFILE_DIR,
    PromptProfileError,
    compact_profile_catalog,
    load_prompt_profiles,
    select_prompt_profiles,
    validate_profile_operation_binding,
)


def test_compact_catalog_omits_full_few_shot_bodies() -> None:
    profiles = load_prompt_profiles()
    compact = compact_profile_catalog(profiles)
    assert len(compact) == 9
    serialized = json.dumps(compact, ensure_ascii=False)
    assert "user_text" not in serialized
    assert "EXAMPLE_ONLY" not in serialized


def test_door_only_and_mixed_selection_are_bounded_stable_unions() -> None:
    profiles = load_prompt_profiles()
    door_only = select_prompt_profiles(["door.add-with-opening"], profiles)
    assert door_only.profile_ids == ("door.add-with-opening",)
    assert len(door_only.few_shot_ids) == 4
    assert all(item.startswith("door.add.") for item in door_only.few_shot_ids)
    assert "window.add-with-opening" not in json.dumps(door_only.to_dict())

    mixed = select_prompt_profiles(
        [
            "window.add-with-opening",
            "door.add-with-opening",
            "door.add-with-opening",
            "occurrence.set-properties",
        ],
        profiles,
    )
    assert mixed.profile_ids == (
        "door.add-with-opening",
        "occurrence.set-properties",
        "window.add-with-opening",
    )
    assert len(mixed.few_shot_ids) == len(set(mixed.few_shot_ids)) == 4
    assert mixed.input_bytes > 0
    assert mixed.estimated_tokens > 0


def test_executable_registry_definitions_bind_matching_profiles() -> None:
    profiles = load_prompt_profiles()
    registry = create_default_registry()
    for operation_type in registry.operation_types:
        definition = registry.require(operation_type)
        assert definition.prompt_profile_id is not None
        validate_profile_operation_binding(
            profiles[definition.prompt_profile_id],
            operation_type=operation_type,
            target_ifc_classes=definition.target_ifc_classes,
        )


def test_hash_mismatch_and_operation_mismatch_fail_closed(tmp_path: Path) -> None:
    for source in DEFAULT_PROFILE_DIR.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    path = tmp_path / "door.add-with-opening.json"
    profile = json.loads(path.read_text(encoding="utf-8"))
    profile["few_shots"][0]["sha256"] = "sha256:" + "0" * 64
    path.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(PromptProfileError, match="FEW_SHOT_HASH_MISMATCH"):
        load_prompt_profiles(tmp_path)

    profiles = load_prompt_profiles()
    with pytest.raises(PromptProfileError, match="PROFILE_OPERATION_MISMATCH"):
        validate_profile_operation_binding(
            profiles["window.add-with-opening"],
            operation_type="wrong_operation",
            target_ifc_classes=("IfcWall",),
        )


def test_missing_unknown_and_empty_selection_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(PromptProfileError, match="PROFILE_DIRECTORY_MISSING"):
        load_prompt_profiles(tmp_path / "missing")
    with pytest.raises(PromptProfileError, match="UNKNOWN_PROFILE_ID"):
        select_prompt_profiles(["unknown.profile"])
    with pytest.raises(PromptProfileError, match="PROFILE_SELECTION_EMPTY"):
        select_prompt_profiles([])
