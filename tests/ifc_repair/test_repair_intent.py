import copy
import hashlib
import importlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.operations import create_default_registry


SCHEMA_VERSION = "text2ifc/ifc-repair-intent/0.1"


def _module():
    return importlib.import_module("text2ifc_ifc_repair.repair_intent")


def _source(excerpt: str = "add a window") -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": excerpt,
    }


def _operation(operation_id: str = "operation-intent-001") -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_window_with_opening_to_wall",
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWall"],
            "names": ["North wall"],
        },
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": 1000.0,
            },
            "opening": {
                "width_mm": 915.0,
                "height_mm": 1830.0,
                "sill_height_mm": 305.0,
            },
            "window": {"fit_opening": True},
        },
        "attribute_intents": [
            {
                "intent_kind": "attribute",
                "name": "Name",
                "value": "W-01",
                "source": _source("named W-01"),
            },
            {
                "intent_kind": "pset",
                "name": "Pset_WindowCommon.FireRating",
                "value": "60min",
                "source": _source("FireRating 60min"),
            },
            {
                "intent_kind": "material",
                "name": "FrameMaterial",
                "value": "Aluminium",
                "source": _source("aluminium frame"),
            },
        ],
        "prototype_intent": {
            "reference_kind": "type_name",
            "reference": "WindowType-A",
            "source": _source("use WindowType-A"),
        },
        "provenance": [_source()],
    }


def _payload(*operations: dict) -> dict:
    repair_intent = _module()
    request_text = "Add a 915 x 1830 window named W-01 to North wall."
    prompt_fingerprint = "sha256:" + "b" * 64
    model_fingerprint = repair_intent.fingerprint_text("recording-model-v1")
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": "request-public-001",
        "source_request_hash": repair_intent.hash_request(request_text),
        "model_fingerprint": model_fingerprint,
        "prompt_fingerprint": prompt_fingerprint,
        "operations": list(operations or (_operation(),)),
        "provenance": [_source(request_text)],
    }


def test_schema_is_exact_draft_2020_12_contract() -> None:
    repair_intent = _module()
    schema = repair_intent.load_repair_intent_schema()
    Draft202012Validator.check_schema(schema)
    assert schema["$id"] == SCHEMA_VERSION
    assert schema["additionalProperties"] is False
    body_schema = repair_intent.load_repair_intent_body_schema()
    Draft202012Validator.check_schema(body_schema)
    assert body_schema["$id"] == "text2ifc/ifc-repair-intent-body/0.1"
    assert body_schema["additionalProperties"] is False


def test_single_operation_round_trips_with_canonical_hash_and_evidence() -> None:
    repair_intent = _module()
    payload = _payload(_operation())
    intent = repair_intent.RepairIntent.from_dict(
        payload, registry=create_default_registry()
    )

    assert intent.to_dict() == payload
    assert intent.operations[0].target_query.names == ("North wall",)
    assert intent.operations[0].attribute_intents[1].source.source_kind == "user_request"
    assert intent.operations[0].prototype_intent.reference == "WindowType-A"
    assert intent.canonical_json() == json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    assert intent.intent_hash == "sha256:" + hashlib.sha256(
        intent.canonical_json().encode("utf-8")
    ).hexdigest()
    with pytest.raises(TypeError):
        intent.operations[0].parameters["invented"] = True
    with pytest.raises(TypeError):
        intent.operations[0].parameters["opening"]["width_mm"] = 1.0


def test_geometry_signature_is_a_valid_target_selector_without_names() -> None:
    repair_intent = _module()
    operation = _operation()
    operation["target_query"] = {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
        "direction": "north",
        "geometry_capabilities": ["straight_wall"],
        "geometry_constraints": [
            {
                "field": "storey_elevation_mm",
                "value": 4570.0,
                "tolerance_mm": 1.0,
            },
            {
                "field": "wall_length_mm",
                "value": 40577.0,
                "tolerance_mm": 1.0,
            },
        ],
    }

    intent = repair_intent.RepairIntent.from_dict(
        _payload(operation), registry=create_default_registry()
    )

    query = intent.operations[0].target_query
    assert query.global_id is None
    assert query.names == ()
    assert len(query.geometry_constraints) == 2


def test_public_source_kinds_and_all_stage_limits_have_one_authority() -> None:
    repair_intent = _module()
    limits = repair_intent.DEFAULT_REPAIR_INTENT_LIMITS
    assert limits.public_source_kinds == (
        "user_request",
        "public_capability",
        "public_clarification",
    )
    assert repair_intent.MAX_OPERATIONS == limits.max_operations
    assert repair_intent.MAX_PROVENANCE_EXCERPT_CHARS == (
        limits.max_provenance_excerpt_chars
    )


def test_multiple_operations_preserve_declared_order_and_stable_ids() -> None:
    repair_intent = _module()
    first = _operation("operation-intent-002")
    first["target_query"]["names"] = ["West wall"]
    second = _operation("operation-intent-001")
    intent = repair_intent.RepairIntent.from_dict(
        _payload(first, second), registry=create_default_registry()
    )

    assert [item.operation_id for item in intent.operations] == [
        "operation-intent-002",
        "operation-intent-001",
    ]
    assert repair_intent.RepairIntent.from_dict(
        json.loads(intent.canonical_json()), registry=create_default_registry()
    ).canonical_json() == intent.canonical_json()


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda value: value["operations"].append(
                copy.deepcopy(value["operations"][0])
            ),
            "REPAIR_INTENT_DUPLICATE_OPERATION_ID",
        ),
        (
            lambda value: value["operations"][0].update(
                {"operation_type": "invented_operation"}
            ),
            "REPAIR_INTENT_UNSUPPORTED_OPERATION",
        ),
        (
            lambda value: value["operations"][0].update(
                {
                    "target_query": {
                        "schema_version": "text2ifc/ifc-target-query/0.1",
                        "allowed_ifc_classes": ["IfcWall"],
                    }
                }
            ),
            "REPAIR_INTENT_TARGET_SELECTOR_REQUIRED",
        ),
        (
            lambda value: value["operations"][0]["target_query"].update(
                {"resolved_target_id": "ifc:wall-secret"}
            ),
            "REPAIR_INTENT_SCHEMA_INVALID",
        ),
        (
            lambda value: value["operations"][0]["attribute_intents"][0][
                "source"
            ].update({"source_kind": "model_default"}),
            "REPAIR_INTENT_SCHEMA_INVALID",
        ),
        (
            lambda value: value.update({"schema_version": "0.2"}),
            "REPAIR_INTENT_SCHEMA_INVALID",
        ),
        (
            lambda value: value.update({"private_original_ifc": "gold.ifc"}),
            "REPAIR_INTENT_SCHEMA_INVALID",
        ),
    ],
)
def test_invalid_or_unauthorized_intents_fail_closed(mutate, code: str) -> None:
    repair_intent = _module()
    payload = _payload(_operation())
    mutate(payload)
    with pytest.raises(repair_intent.RepairIntentError) as error:
        repair_intent.RepairIntent.from_dict(
            payload, registry=create_default_registry()
        )
    assert error.value.code == code


def test_content_and_count_bounds_are_enforced_before_model_construction() -> None:
    repair_intent = _module()
    payload = _payload(_operation())
    payload["provenance"][0]["excerpt"] = "x" * (
        repair_intent.MAX_PROVENANCE_EXCERPT_CHARS + 1
    )
    with pytest.raises(repair_intent.RepairIntentError) as error:
        repair_intent.RepairIntent.from_dict(
            payload, registry=create_default_registry()
        )
    assert error.value.code == "REPAIR_INTENT_SCHEMA_INVALID"

    payload = _payload(
        *(
            _operation(f"operation-intent-{index:03d}")
            for index in range(repair_intent.MAX_OPERATIONS + 1)
        )
    )
    with pytest.raises(repair_intent.RepairIntentError) as error:
        repair_intent.RepairIntent.from_dict(
            payload, registry=create_default_registry()
        )
    assert error.value.code == "REPAIR_INTENT_SCHEMA_INVALID"


def test_schema_file_lives_at_the_versioned_public_path() -> None:
    repair_intent = _module()
    assert repair_intent.REPAIR_INTENT_SCHEMA_PATH == Path(
        "schemas/agent/ifc-repair-intent-0.1.schema.json"
    )
    assert repair_intent.REPAIR_INTENT_BODY_SCHEMA_PATH == Path(
        "schemas/agent/ifc-repair-intent-body-0.1.schema.json"
    )
