from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import (
    DEFAULT_PROFILE_DIR,
    PromptProfileError,
    compact_profile_catalog,
    load_prompt_profiles,
    select_prompt_profiles,
    validate_profile_operation_binding,
)
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry
from text2ifc_ifc_repair.request_stage import generate_repair_intent


STRUCTURAL_PROFILE_IDS = ("beam.add", "column.add")


class _Provider:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={"provider": "fixture", "model": "fixture-model"},
        )


def _noop(**_kwargs):
    return None


def _point_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["x_mm", "y_mm", "z_mm"],
        "properties": {
            axis: {"type": "number"} for axis in ("x_mm", "y_mm", "z_mm")
        },
    }


def _structural_registry() -> OperationRegistry:
    registry = OperationRegistry()
    for family in ("beam", "column"):
        endpoints = ("start", "end") if family == "beam" else ("base", "top")
        dimensions = (
            ("width_mm", "height_mm")
            if family == "beam"
            else ("width_mm", "depth_mm")
        )
        parameter_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["axis", "section"],
            "properties": {
                "axis": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(endpoints),
                    "properties": {
                        endpoint: _point_schema() for endpoint in endpoints
                    },
                },
                "section": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["shape", *dimensions],
                    "properties": {
                        "shape": {"const": "rectangle"},
                        **{
                            dimension: {"type": "number", "exclusiveMinimum": 0}
                            for dimension in dimensions
                        },
                    },
                },
            },
        }
        registry.register(
            OperationDefinition(
                operation_type=f"add_{family}",
                target_ifc_classes=("IfcBuildingStorey",),
                parameter_schema=parameter_schema,
                context_adapter=_noop,
                precondition_checker=_noop,
                applicator=_noop,
                postcondition_checker=_noop,
                comparison_adapter=_noop,
                capability_constraints={},
                prompt_profile_id=f"{family}.add",
            )
        )
    return registry


def _structural_intent_body(family: str) -> dict:
    source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": f"add one {family} on Level 1",
    }
    if family == "beam":
        axis = {
            "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
            "end": {"x_mm": 5000, "y_mm": 0, "z_mm": 3000},
        }
        section = {"shape": "rectangle", "width_mm": 300, "height_mm": 500}
    else:
        axis = {
            "base": {"x_mm": 1000, "y_mm": 2000, "z_mm": 0},
            "top": {"x_mm": 1000, "y_mm": 2000, "z_mm": 3000},
        }
        section = {"shape": "rectangle", "width_mm": 500, "depth_mm": 500}
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
        "operations": [
            {
                "operation_id": f"{family}-1",
                "operation_type": f"add_{family}",
                "routing_intent": {
                    "component_family": family,
                    "action": "add",
                    "operation_profile": f"{family}.add",
                    "source": source,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcBuildingStorey"],
                    "names": ["Level 1"],
                },
                "parameters": {"axis": axis, "section": section},
                "attribute_intents": [],
                "property_intents": [],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": None,
                "provenance": [source],
            }
        ],
        "semantic_bundles": [],
        "provenance": [source],
    }


def _structural_profile_path(profile_id: str) -> Path:
    path = DEFAULT_PROFILE_DIR / f"{profile_id}.json"
    assert path.is_file(), f"missing reserved structural profile: {path.name}"
    return path


def test_structural_profiles_are_hash_bound_and_completed_families_are_executable() -> None:
    for profile_id in STRUCTURAL_PROFILE_IDS:
        _structural_profile_path(profile_id)

    profiles = load_prompt_profiles()
    prompt_registry = load_prompt_registry()
    executable_operations = set(create_default_registry().operation_types)

    assert set(STRUCTURAL_PROFILE_IDS).issubset(profiles)
    assert set(STRUCTURAL_PROFILE_IDS).issubset(prompt_registry)
    assert {"add_beam", "add_column"}.issubset(executable_operations)
    for profile_id in STRUCTURAL_PROFILE_IDS:
        profile = profiles[profile_id]
        registry_record = prompt_registry[profile_id]
        assert registry_record["path"] == (
            f"prompts/agent/ifc-repair-profiles/{profile_id}.json"
        )
        assert registry_record["sha256"] == profile.profile_hash


@pytest.mark.parametrize("family", ("beam", "column"))
def test_stage1_structural_routing_extracts_in_one_compact_call(
    family: str,
    tmp_path: Path,
) -> None:
    provider = _Provider(_structural_intent_body(family))
    result = generate_repair_intent(
        provider=provider,
        request_id=f"structural-profile-{family}",
        repair_request=f"add one {family} on Level 1",
        registry=_structural_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )

    assert result["valid"] is True
    assert result["classification"] == "repair_intent"
    assert len(provider.calls) == 1
    catalog = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )["SUPPORTED_OPERATIONS"]
    assert [item["profile_id"] for item in catalog] == ["beam.add", "column.add"]
    serialized = json.dumps(catalog, ensure_ascii=False)
    assert "EXAMPLE_ONLY" not in serialized
    assert "user_text" not in serialized


def test_structural_compact_profiles_expose_only_canonical_public_slots() -> None:
    profiles = load_prompt_profiles()
    compact = {
        item["profile_id"]: item
        for item in compact_profile_catalog(
            profiles, include_profile_ids=STRUCTURAL_PROFILE_IDS
        )
    }

    assert tuple(compact) == STRUCTURAL_PROFILE_IDS
    beam = compact["beam.add"]
    column = compact["column.add"]
    assert beam["operation_type"] == "add_beam"
    assert column["operation_type"] == "add_column"
    assert beam["target_ifc_classes"] == ["IfcBuildingStorey"]
    assert column["target_ifc_classes"] == ["IfcBuildingStorey"]
    assert set(beam["required_slots"]) == {
        "/target_query",
        "/parameters/axis/start",
        "/parameters/axis/end",
        "/parameters/section/shape",
        "/parameters/section/width_mm",
        "/parameters/section/height_mm",
    }
    assert set(column["required_slots"]) == {
        "/target_query",
        "/parameters/axis/base",
        "/parameters/axis/top",
        "/parameters/section/shape",
        "/parameters/section/width_mm",
        "/parameters/section/depth_mm",
    }
    assert "/parameters/section/orientation" in column["conditional_slots"]

    serialized = json.dumps(compact, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "placement_matrix",
        "IfcLocalPlacement",
        "generated_global_id",
        "generated_type_id",
        "center_offset_from_wall_start_mm",
        "length_mm",
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    ("profile_id", "family", "other_family"),
    (("beam.add", "beam", "column"), ("column.add", "column", "beam")),
)
def test_stage2_selected_structural_profile_excludes_unrelated_full_payloads(
    profile_id: str,
    family: str,
    other_family: str,
) -> None:
    selected = select_prompt_profiles([profile_id])
    payload = json.dumps(selected.to_dict(), ensure_ascii=False, sort_keys=True)

    assert selected.profile_ids == (profile_id,)
    assert len(selected.few_shot_ids) == 4
    assert all(item.startswith(f"{family}.add.") for item in selected.few_shot_ids)
    assert f'"component_family": "{family}"' in payload
    assert f'"component_family": "{other_family}"' not in payload
    assert "window.add-with-opening.v0.2" not in payload
    assert "door.add-with-opening" not in payload


def test_mixed_structural_selection_is_a_deterministic_hash_bound_union() -> None:
    selected = select_prompt_profiles(
        ["column.add", "beam.add", "column.add"]
    )

    assert selected.profile_ids == STRUCTURAL_PROFILE_IDS
    assert len(selected.profile_hashes) == 2
    assert len(set(selected.profile_hashes)) == 2
    assert len(selected.few_shot_ids) == len(set(selected.few_shot_ids)) == 8
    assert selected.few_shot_ids == tuple(sorted(selected.few_shot_ids))
    assert all(value.startswith("sha256:") for value in selected.profile_hashes)
    assert all(value.startswith("sha256:") for value in selected.few_shot_hashes)


def test_selected_structural_profile_rejects_profile_hash_tampering(
    tmp_path: Path,
) -> None:
    for source in DEFAULT_PROFILE_DIR.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    path = tmp_path / "beam.add.json"
    assert path.is_file(), "missing reserved structural profile: beam.add.json"
    profile = json.loads(path.read_text(encoding="utf-8"))
    profile["slot_summary"] += " tampered"
    path.write_text(json.dumps(profile), encoding="utf-8")

    profiles = load_prompt_profiles(tmp_path)
    with pytest.raises(PromptProfileError, match="PROFILE_HASH_MISMATCH"):
        select_prompt_profiles(["beam.add"], profiles)


def test_structural_profile_schema_and_binding_fail_closed(tmp_path: Path) -> None:
    for source in DEFAULT_PROFILE_DIR.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    path = tmp_path / "column.add.json"
    assert path.is_file(), "missing reserved structural profile: column.add.json"
    profile = json.loads(path.read_text(encoding="utf-8"))
    profile["axis"] = {"base": "wrong nesting"}
    path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(PromptProfileError, match="PROFILE_SCHEMA_INVALID"):
        load_prompt_profiles(tmp_path)

    profiles = load_prompt_profiles()
    with pytest.raises(PromptProfileError, match="PROFILE_OPERATION_MISMATCH"):
        validate_profile_operation_binding(
            profiles["beam.add"],
            operation_type="add_column",
            target_ifc_classes=("IfcBuildingStorey",),
        )
    with pytest.raises(PromptProfileError, match="PROFILE_TARGET_CLASS_MISMATCH"):
        validate_profile_operation_binding(
            profiles["column.add"],
            operation_type="add_column",
            target_ifc_classes=("IfcWall",),
        )
