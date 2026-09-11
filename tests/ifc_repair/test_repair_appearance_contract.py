from __future__ import annotations

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_ifc_repair.changesets import (
    BOUND_CHANGESET_SCHEMA_VERSION_0_5,
    BOUND_CHANGESET_SCHEMA_VERSION_0_6,
    DRAFT_CHANGESET_SCHEMA_VERSION_0_3,
    DRAFT_CHANGESET_SCHEMA_VERSION_0_4,
    _assignment_payload,
    _require_exact_draft_authority,
    load_bound_changeset_schema,
    load_changeset_draft_schema,
)
from text2ifc_ifc_repair.production_evidence import _request_fact
from text2ifc_ifc_repair.repair_intent import (
    AttributeIntent,
    PublicProvenance,
    REPAIR_INTENT_SCHEMA_VERSION_0_8,
    REPAIR_INTENT_SCHEMA_VERSION_0_9,
    load_repair_intent_schema,
)


def test_appearance_contract_versions_are_additive() -> None:
    defs = "$defs"
    legacy_intent = load_repair_intent_schema(REPAIR_INTENT_SCHEMA_VERSION_0_8)
    appearance_intent = load_repair_intent_schema(REPAIR_INTENT_SCHEMA_VERSION_0_9)
    legacy_draft = load_changeset_draft_schema(DRAFT_CHANGESET_SCHEMA_VERSION_0_3)
    appearance_draft = load_changeset_draft_schema(DRAFT_CHANGESET_SCHEMA_VERSION_0_4)
    legacy_bound = load_bound_changeset_schema(BOUND_CHANGESET_SCHEMA_VERSION_0_5)
    appearance_bound = load_bound_changeset_schema(BOUND_CHANGESET_SCHEMA_VERSION_0_6)

    assert "appearance_intent" not in legacy_intent[defs]["operation"]["properties"]
    assert "appearance_intent" in appearance_intent[defs]["operation"]["properties"]
    assert "appearance" not in legacy_draft[defs]["beam"]["properties"]
    assert "appearance" in appearance_draft[defs]["operation"]["properties"]
    assert "appearance" not in legacy_bound[defs]["operation"]["properties"]
    assert "appearance" in appearance_bound[defs]["operation"]["properties"]


def test_appearance_draft_04_accepts_generic_operation_families() -> None:
    schema = load_changeset_draft_schema(DRAFT_CHANGESET_SCHEMA_VERSION_0_4)
    validator = Draft202012Validator(schema)
    common = {
        "schema_version": DRAFT_CHANGESET_SCHEMA_VERSION_0_4,
        "draft_id": "draft-1",
        "base_model_fingerprint": "sha256:" + "a" * 64,
        "source_request_hash": "sha256:" + "b" * 64,
        "semantic_manifest_ref": "manifest:/mixed",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "semantic_summary": {"required": 1, "conditional": 0, "not_required": 0},
        "scope": {"target_ids": ["target-1"], "forbidden_ids": []},
        "evidence_refs": ["resolved:/target-1"],
        "preconditions": [],
        "postconditions": [],
    }
    for operation_type, target in (
        ("add_window_with_opening_to_wall", {"wall_global_id": "wall-1"}),
        ("fill_existing_opening_with_door", {"opening_global_id": "opening-1"}),
        ("add_beam", {"storey_global_id": "storey-1"}),
        ("add_column", {"storey_global_id": "storey-1"}),
    ):
        document = {
            **common,
            "operations": [
                {
                    "operation_id": "operation-1",
                    "operation_type": operation_type,
                    "target": target,
                    "parameters": {"example": True},
                    "evidence_refs": ["resolved:/target-1"],
                    "appearance": {
                        "intent_kind": "surface_color_rgb",
                        "red": 0.1,
                        "green": 0.2,
                        "blue": 0.3,
                    },
                }
            ],
        }
        assert not list(validator.iter_errors(document))


def test_bound_06_normalizes_legacy_assignment_shape() -> None:
    payload = _assignment_payload(
        {
            "operation_id": "operation-1",
            "scope": "window_occurrence",
            "fact_key": "material:example",
            "source_fact_key": "material:example",
            "value": "Example Material",
            "value_type": "IfcMaterial",
            "unit": None,
            "ownership": "occurrence_direct",
            "applicability": "conditional",
            "source_kind": "explicit_request",
            "source_ref": "request:/text",
            "provenance": ["request-evidence:request:/text"],
            "derivation": None,
            "authoring_action": "reuse_material",
        },
        bound_schema_version=BOUND_CHANGESET_SCHEMA_VERSION_0_6,
    )

    assert "scope" not in payload
    assert "derivation" not in payload
    schema = load_bound_changeset_schema(BOUND_CHANGESET_SCHEMA_VERSION_0_6)
    validator = Draft202012Validator(
        {"$defs": schema["$defs"], "$ref": "#/$defs/legacyAssignment"}
    )
    assert not list(validator.iter_errors(payload))


def test_intent_v012_prompt_is_registered_without_beam_profile_version_change() -> None:
    registry = load_prompt_registry()

    assert "ifc-repair-intent.v0.12" in registry
    assert registry["ifc-repair-intent.v0.12"]["path"] == (
        "prompts/agent/ifc-repair-intent-v0.12.md"
    )


def test_intent_09_requires_canonical_user_request_reference() -> None:
    schema = load_repair_intent_schema(REPAIR_INTENT_SCHEMA_VERSION_0_9)
    provenance_schema = schema["$defs"]["provenance"]
    validator = Draft202012Validator(provenance_schema)

    valid = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "恢复梁",
    }
    invalid_references = ("other:/text", "request:/other", "provider-local-label")

    assert not list(validator.iter_errors(valid))
    for reference in invalid_references:
        invalid = {
            "source_kind": "user_request",
            "reference": reference,
            "excerpt": "恢复梁",
        }
        assert list(validator.iter_errors(invalid))


def test_intent_09_material_contract_is_structural_and_type_specific() -> None:
    schema = load_repair_intent_schema(REPAIR_INTENT_SCHEMA_VERSION_0_9)
    validator = Draft202012Validator(
        {"$defs": schema["$defs"], "$ref": "#/$defs/attribute_intent"}
    )
    source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "Reuse the existing IFC material Example Material.",
    }
    valid_material = {
        "intent_kind": "material",
        "name": "Material",
        "value": "Example Material",
        "source": source,
    }
    invalid_materials = (
        {**valid_material, "name": "Example Material"},
        {**valid_material, "value": True},
        {**valid_material, "value": 42},
        {**valid_material, "value": ""},
    )
    valid_boolean_attribute = {
        "intent_kind": "attribute",
        "name": "IsExternal",
        "value": True,
        "source": source,
    }

    assert not list(validator.iter_errors(valid_material))
    assert all(list(validator.iter_errors(item)) for item in invalid_materials)
    assert not list(validator.iter_errors(valid_boolean_attribute))


def test_stage2_authority_rejects_provider_rgb_drift() -> None:
    authority = {
        "scope": {"target_ids": ["storey-1"], "forbidden_ids": []},
        "evidence_refs": ["resolved:/operations/beam-1/context/candidate_targets/0"],
        "operations": [
            {
                "operation_id": "beam-1",
                "operation_type": "add_beam",
                "target": {"storey_global_id": "storey-1"},
                "parameters": {"axis": {}, "section": {}},
                "appearance": {
                    "intent_kind": "surface_color_rgb",
                    "red": 0.92,
                    "green": 0.12,
                    "blue": 0.18,
                },
                "evidence_refs": [
                    "resolved:/operations/beam-1/context/candidate_targets/0"
                ],
            }
        ],
    }
    draft = deepcopy(authority)
    draft["operations"][0]["appearance"]["green"] = 0.13

    with pytest.raises(ValueError, match="DRAFT_AUTHORITY_APPEARANCE_MISMATCH"):
        _require_exact_draft_authority(draft, authority)


def test_explicit_material_authority_uses_canonical_request_locator() -> None:
    intent = AttributeIntent(
        intent_kind="material",
        name="Material",
        value="C_钢筋砼C30",
        source=PublicProvenance(
            source_kind="user_request",
            reference="request:/text",
            excerpt="复用现有 IfcMaterial C_钢筋砼C30",
        ),
    )

    fact = _request_fact("beam-1", intent)

    assert fact.source_ref == "request:/text"
    assert "request-evidence:request:/text" in fact.provenance
    assert fact.fact_key.startswith("material:")
    assert fact.value == "C_钢筋砼C30"


def test_appearance_prompt_preserves_published_v05_identity() -> None:
    registry = load_prompt_registry()
    assert registry["ifc-repair-changeset.v0.5"]["sha256"] == (
        "sha256:f354db4172fe177dfbed8ded156d5c62aec7aead33302ffe996050c57f20885f"
    )
    assert registry["ifc-repair-changeset.v0.6"]["path"] == (
        "prompts/agent/ifc-repair-changeset-v0.6.md"
    )


@pytest.mark.parametrize(
    "appearance,v03,v02,expected",
    [(True, True, False, "0.6"), (True, False, True, "0.6"),
     (False, True, False, "0.5"), (False, False, True, "0.3"),
     (False, False, False, "0.2")],
)
def test_bound_prompt_selection_keeps_nonappearance_versions(
    appearance: bool, v03: bool, v02: bool, expected: str
) -> None:
    from text2ifc_ifc_repair import provider_stage
    assert provider_stage._bound_template_id(
        appearance_contract=appearance,
        semantic_contract_v03=v03,
        semantic_contract_v02=v02,
    ) == "ifc-repair-changeset.v" + expected


@pytest.mark.parametrize("appearance", [None, {"intent_kind": "surface_color_rgb", "red": 0.2, "green": 0.3, "blue": 0.4}])
def test_resolution_serialization_preserves_nonappearance_contract(appearance) -> None:
    from text2ifc_ifc_repair.resolution_flow import ResolvedOperation
    operation = ResolvedOperation(
        operation_id="beam-1", operation_type="add_beam", target_global_id="storey-1",
        scope_ids=("storey-1",), evidence_pointers=(), parameters={}, context={},
        appearance=appearance,
    )
    document = operation.to_dict()
    if appearance is None:
        assert "appearance" not in document
    else:
        assert document["appearance"] == appearance
