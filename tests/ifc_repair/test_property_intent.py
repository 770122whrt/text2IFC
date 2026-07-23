import copy
import importlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry


INTENT_VERSION = "text2ifc/ifc-repair-intent/0.2"
BODY_VERSION = "text2ifc/ifc-repair-intent-body/0.2"


def _module():
    return importlib.import_module("text2ifc_ifc_repair.repair_intent")


def _source(excerpt: str = "设置防火等级 EI30") -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": excerpt,
    }


def _property(
    *,
    set_name: str | None = "Pset_WindowCommon",
    property_name: str | None = "FireRating",
    value: object = "EI30",
    scope: str | None = None,
) -> dict:
    return {
        "intent_kind": "pset_property",
        "set_name": set_name,
        "property_name": property_name,
        "value": value,
        "requested_value_type": None,
        "requested_unit": None,
        "scope": scope,
        "source": _source(),
    }


def _operation(*, properties: list[dict] | None = None, prototype: dict | None = None) -> dict:
    return {
        "operation_id": "property-operation-1",
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
        "attribute_intents": [],
        "property_intents": list(properties or [_property()]),
        "prototype_intent": prototype,
        "provenance": [_source("在 North wall 添加窗口")],
    }


def _payload(*, operation: dict | None = None) -> dict:
    module = _module()
    return {
        "schema_version": INTENT_VERSION,
        "request_id": "property-request-1",
        "source_request_hash": module.hash_request("property request"),
        "model_fingerprint": module.fingerprint_text("recording-model-v1"),
        "prompt_fingerprint": module.fingerprint_text("prompt-v0.2"),
        "operations": [operation or _operation()],
        "provenance": [_source("property request")],
    }


def test_v02_schemas_are_exact_draft_2020_12_contracts() -> None:
    project_root = Path(__file__).resolve().parents[2]
    envelope = json.loads(
        (project_root / "schemas/agent/ifc-repair-intent-0.2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    body = json.loads(
        (
            project_root
            / "schemas/agent/ifc-repair-intent-body-0.2.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(envelope)
    Draft202012Validator.check_schema(body)
    assert envelope["$id"] == INTENT_VERSION
    assert body["$id"] == BODY_VERSION
    assert envelope["additionalProperties"] is False
    assert body["additionalProperties"] is False


def test_v02_complete_standard_and_custom_properties_round_trip_immutably() -> None:
    module = _module()
    operation = _operation(
        properties=[
            _property(),
            {
                **_property(
                    set_name="Custom_Asset",
                    property_name="AssetCode",
                    value="W-007",
                ),
                "source": _source("设置 Custom_Asset.AssetCode 为 W-007"),
            },
        ]
    )
    payload = _payload(operation=operation)

    intent = module.RepairIntent.from_dict(
        payload,
        registry=create_default_registry(),
    )

    assert intent.to_dict() == payload
    assert intent.schema_version == INTENT_VERSION
    assert intent.operations[0].property_intents[0].set_name == "Pset_WindowCommon"
    assert intent.operations[0].property_intents[1].property_name == "AssetCode"
    with pytest.raises(TypeError):
        intent.operations[0].property_intents[0].source.excerpt = "changed"


@pytest.mark.parametrize(
    "field",
    [
        "standard_status",
        "applicable",
        "confirmed",
        "authorized",
        "resolved_target_id",
        "resolved_type_id",
    ],
)
def test_v02_provider_property_claim_forbids_authority_fields(field: str) -> None:
    schema = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "schemas/agent/ifc-repair-intent-body-0.2.schema.json"
        ).read_text(encoding="utf-8")
    )
    body = {
        "schema_version": BODY_VERSION,
        "operations": [_operation()],
        "provenance": [_source()],
    }
    body["operations"][0]["property_intents"][0][field] = True
    errors = list(Draft202012Validator(schema).iter_errors(body))
    assert errors


@pytest.mark.parametrize("value", [[], {}, [1], {"value": "EI30"}])
def test_v02_property_claim_rejects_non_scalar_values(value: object) -> None:
    module = _module()
    with pytest.raises(module.RepairIntentError) as error:
        module.RepairIntent.from_dict(
            _payload(operation=_operation(properties=[_property(value=value)])),
            registry=create_default_registry(),
        )
    assert error.value.code == "REPAIR_INTENT_SCHEMA_INVALID"


def test_v02_incomplete_property_is_clarification_ready_without_guessing(
    tmp_path: Path,
) -> None:
    request_text = "在 North wall 添加窗口，并设置 FireRating。"
    body = {
        "schema_version": BODY_VERSION,
        "operations": [
            _operation(
                properties=[
                    _property(set_name=None, property_name="FireRating", value=None)
                ]
            )
        ],
        "provenance": [_source(request_text)],
    }

    class Provider:
        def generate_candidate(self, **kwargs) -> ProviderOutput:
            assert kwargs["schema"]["$id"] == BODY_VERSION
            return ProviderOutput(
                text=json.dumps(body, ensure_ascii=False),
                metadata={"provider": "recording", "model": "recording-model-v1"},
            )

    result = importlib.import_module(
        "text2ifc_ifc_repair.request_stage"
    ).generate_repair_intent(
        provider=Provider(),
        request_id="property-request-1",
        repair_request=request_text,
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version=INTENT_VERSION,
    )

    assert result["valid"] is True
    assert result["classification"] == "clarification_required"
    assert result["missing_properties"] == [
        {
            "operation_id": "property-operation-1",
            "property_index": 0,
            "fields": ["set_name", "value"],
        }
    ]
    assert result["intent"].operations[0].property_intents[0].set_name is None


def test_v02_omitted_type_stays_null_and_explicit_type_is_preserved() -> None:
    module = _module()
    without_type = module.RepairIntent.from_dict(
        _payload(operation=_operation(prototype=None)),
        registry=create_default_registry(),
    )
    assert without_type.operations[0].prototype_intent is None

    prototype = {
        "reference_kind": "type_name",
        "reference": "M_Fixed:0915 x 1830mm",
        "source": _source("复用 M_Fixed:0915 x 1830mm"),
    }
    with_type = module.RepairIntent.from_dict(
        _payload(operation=_operation(prototype=prototype)),
        registry=create_default_registry(),
    )
    assert with_type.operations[0].prototype_intent.reference == prototype["reference"]


def test_historical_v01_payload_still_uses_original_model_and_schema() -> None:
    module = _module()
    schema = module.load_repair_intent_schema()
    assert schema["$id"] == "text2ifc/ifc-repair-intent/0.1"
    assert module.REPAIR_INTENT_SCHEMA_VERSION == "text2ifc/ifc-repair-intent/0.1"
