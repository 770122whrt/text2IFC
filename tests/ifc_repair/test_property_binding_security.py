from __future__ import annotations

from copy import deepcopy

import pytest

from text2ifc_ifc_repair.property_intent import AuthorizedPropertyFact
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_ifc_repair.run_models import hash_json
from text2ifc_ifc_repair.semantic_authoring import (
    SemanticManifestError,
    parse_semantic_manifest,
)


def _authorized() -> dict:
    return AuthorizedPropertyFact(
        operation_id="window-1",
        target_global_id="0TARGETAAAAAAAAAAAAAAAA",
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
        set_name="Custom_Asset",
        property_name="AssetCode",
        value="W-007",
        value_type="IfcLabel",
        unit=None,
        ownership="occurrence_direct",
        source=PublicProvenance(
            "user_request", "request:/properties/0", "set AssetCode W-007"
        ),
        confirmation_ref="run:repair-1/property-confirmation-4",
        confirmation_hash="sha256:" + "c" * 64,
        classification="custom_confirmed",
    ).to_dict()


def test_normalized_property_hash_detects_every_executable_field_tamper() -> None:
    fact = _authorized()
    assert fact["property_hash"] == hash_json(
        {key: value for key, value in fact.items() if key != "property_hash"}
    )
    for field, value in (
        ("operation_id", "window-2"),
        ("target_global_id", "0OTHERAAAAAAAAAAAAAAAAA"),
        ("model_fingerprint", "sha256:" + "d" * 64),
        ("property_name", "Other"),
        ("value", "W-008"),
        ("value_type", "IfcIdentifier"),
        ("unit", "unit"),
        ("ownership", "type_inherited"),
        ("confirmation_hash", "sha256:" + "e" * 64),
    ):
        changed = deepcopy(fact)
        changed[field] = value
        assert changed["property_hash"] != hash_json(
            {key: item for key, item in changed.items() if key != "property_hash"}
        )


def test_manifest_rejects_type_owned_occurrence_write() -> None:
    document = {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.1",
        "manifest_id": "manifest-window-1",
        "operation_id": "window-1",
        "operation_type": "add_window_with_opening_to_wall",
        "base_model_fingerprint": "sha256:" + "a" * 64,
        "policy": {
            "policy_id": "window.add-with-opening.l2",
            "policy_version": "0.2",
        },
        "assignments": [
            {
                "operation_id": "window-1",
                "fact_key": "pset:Custom_Asset.AssetCode",
                "source_fact_key": "pset:Custom_Asset.AssetCode",
                "value": "W-007",
                "value_type": "IfcLabel",
                "unit": None,
                "ownership": "type_inherited",
                "applicability": "required",
                "source_kind": "explicit_request",
                "source_ref": "request:/properties/0",
                "provenance": ["property-hash:sha256:fixture"],
                "authoring_action": "set_occurrence_pset",
            }
        ],
    }
    with pytest.raises(SemanticManifestError, match="SEMANTIC_OWNERSHIP_ACTION_MISMATCH"):
        parse_semantic_manifest(document)
