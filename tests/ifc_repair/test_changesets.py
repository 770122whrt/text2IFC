from copy import deepcopy

from jsonschema import Draft202012Validator
import pytest

from text2ifc_ifc_repair.changesets import (
    bind_repair_changeset,
    canonical_changeset_json,
    load_bound_changeset_schema,
    load_changeset_draft_schema,
    load_changeset_schema,
    validate_changeset,
)
from text2ifc_ifc_repair.semantic_authoring import parse_semantic_manifest


def valid_window_changeset() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-window-repair-001",
        "base_model_fingerprint": "sha256:" + "a" * 64,
        "source_request_hash": "sha256:" + "b" * 64,
        "scope": {
            "target_ids": ["1F6umJ5H50aeL3A1As_wTm"],
            "forbidden_ids": [],
        },
        "evidence_refs": [
            "spec:/opening",
            "context:/candidate_targets/0",
        ],
        "preconditions": [
            "base_model_fingerprint_matches",
            "target_exists",
        ],
        "postconditions": [
            "opening_voids_wall",
            "window_fills_opening",
        ],
        "operations": [
            {
                "operation_id": "operation-window-001",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {
                    "wall_global_id": "1F6umJ5H50aeL3A1As_wTm",
                },
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 3042.5,
                    },
                    "opening": {
                        "width_mm": 915.0,
                        "height_mm": 1830.0,
                        "sill_height_mm": 305.0,
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": [
                    "spec:/opening",
                    "context:/candidate_targets/0",
                ],
            }
        ],
    }


def test_unified_changeset_schema_is_meta_valid_and_accepts_window_operation() -> None:
    schema = load_changeset_schema()

    Draft202012Validator.check_schema(schema)
    document = valid_window_changeset()
    assert validate_changeset(document) == []
    assert canonical_changeset_json(document) == canonical_changeset_json(document)


def test_changeset_rejects_low_level_fields_outside_operation_contract() -> None:
    document = deepcopy(valid_window_changeset())
    document["operations"][0]["IfcLocalPlacement"] = {"secret": "topology"}

    issues = validate_changeset(document)

    assert [(issue.code, issue.path) for issue in issues] == [
        ("SCHEMA_VALIDATION_ERROR", "/operations/0"),
    ]


def test_changeset_rejects_duplicate_operation_ids() -> None:
    document = valid_window_changeset()
    document["operations"].append(deepcopy(document["operations"][0]))

    issues = validate_changeset(document)

    assert [(issue.code, issue.path) for issue in issues] == [
        ("DUPLICATE_CHANGESET_OPERATION_ID", "/operations/1/operation_id"),
    ]


def _manifest():
    return parse_semantic_manifest(
        {
            "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.1",
            "manifest_id": "semantic-manifest-window-001",
            "operation_id": "operation-window-001",
            "operation_type": "add_window_with_opening_to_wall",
            "base_model_fingerprint": "sha256:" + "a" * 64,
            "policy": {"policy_id": "window.add-with-opening.l2", "policy_version": "0.2"},
            "assignments": [{
                "operation_id": "operation-window-001",
                "fact_key": "attribute:OverallWidth",
                "source_fact_key": "request:/opening/width_mm",
                "value": 915.0,
                "value_type": "IfcPositiveLengthMeasure",
                "unit": "mm",
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_request",
                "source_ref": "request:/opening/width_mm",
                "provenance": ["request:fixture"],
                "authoring_action": "set_attribute",
            }],
        }
    )


def _draft() -> dict:
    base = valid_window_changeset()
    base.update({
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.2",
        "draft_id": base.pop("changeset_id"),
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "semantic_summary": {"required": 1, "conditional": 0, "not_required": 0},
    })
    return base


def test_draft_and_bound_02_schemas_are_exact_and_meta_valid() -> None:
    Draft202012Validator.check_schema(load_changeset_draft_schema())
    Draft202012Validator.check_schema(load_bound_changeset_schema())


def test_binder_alone_expands_manifest_into_self_contained_changeset() -> None:
    draft = _draft()
    bound = bind_repair_changeset(
        draft=draft,
        semantic_manifests=(_manifest(),),
        semantic_manifest_hashes={"operation-window-001": "sha256:" + "c" * 64},
        source_request_hash="sha256:" + "b" * 64,
        base_model_fingerprint="sha256:" + "a" * 64,
    )

    assert bound["schema_version"] == "text2ifc/ifc-repair-changeset/0.2"
    assert bound["binding_status"] == "bound"
    assert bound["operations"][0]["semantic_assignments"][0]["value"] == 915.0
    assert validate_changeset(bound) == []


def test_binder_rejects_stale_manifest_or_provider_semantic_payload() -> None:
    draft = _draft()
    draft["operations"][0]["semantic_assignments"] = [{"value": "invented"}]
    with pytest.raises(ValueError, match="DRAFT_SCHEMA_INVALID"):
        bind_repair_changeset(
            draft=draft,
            semantic_manifests=(_manifest(),),
            semantic_manifest_hashes={"operation-window-001": "sha256:" + "c" * 64},
            source_request_hash="sha256:" + "b" * 64,
            base_model_fingerprint="sha256:" + "a" * 64,
        )
