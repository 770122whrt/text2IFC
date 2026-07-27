import copy
import importlib
import inspect
import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import ProviderOutput, ProviderOutputError
from text2ifc_ifc_repair.operations import create_default_registry


PRIVATE_CANARY = "mutation_manifest.private.json"


def _intent_module():
    return importlib.import_module("text2ifc_ifc_repair.repair_intent")


def _stage_module():
    return importlib.import_module("text2ifc_ifc_repair.request_stage")


class SequentialProvider:
    def __init__(self, responses: list[dict | str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        response = self.responses[len(self.calls) - 1]
        text = response if isinstance(response, str) else json.dumps(response)
        return ProviderOutput(
            text=text,
            metadata={"provider": "recording", "model": "recording-model-v1"},
        )


class FailingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        del kwargs
        self.calls += 1
        raise ProviderOutputError("private provider failure")


def _source(excerpt: str = "add a window") -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": excerpt,
    }


def _valid_response(request_text: str, *, operation_id: str = "intent-op-001") -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.1",
        "operations": [
            {
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
                    }
                ],
                "prototype_intent": {
                    "reference_kind": "type_name",
                    "reference": "WindowType-A",
                    "source": _source("use WindowType-A"),
                },
                "provenance": [_source()],
            }
        ],
        "provenance": [_source(request_text)],
    }


def _semantic_body(request_text: str, *, parameters: dict | None = None) -> dict:
    """Provider-authored content excludes system-owned envelope bindings."""

    response = _valid_response(request_text)
    if parameters is not None:
        response["operations"][0]["parameters"] = parameters
    return response


def _run(tmp_path: Path, provider: SequentialProvider, request_text: str):
    return _stage_module().generate_repair_intent(
        provider=provider,
        request_id="request-public-001",
        repair_request=request_text,
        registry=create_default_registry(),
        output_dir=tmp_path,
    )


def test_stage_wraps_semantic_body_with_system_owned_bindings(tmp_path: Path) -> None:
    request_text = "Add a 915 x 1830 mm window to North wall."
    provider = SequentialProvider([_semantic_body(request_text)])

    result = _run(tmp_path, provider, request_text)

    assert result["valid"] is True
    assert result["classification"] == "repair_intent"
    assert result["intent"].request_id == "request-public-001"
    assert result["intent"].source_request_hash == _intent_module().hash_request(
        request_text
    )
    assert result["intent"].model_fingerprint == _intent_module().fingerprint_text(
        "recording-model-v1"
    )
    assert result["intent"].prompt_fingerprint == result["prompt"]["template_hash"]
    assert provider.calls[0]["schema"]["$id"] == (
        "text2ifc/ifc-repair-intent-body/0.1"
    )
    assert "model_fingerprint" not in provider.calls[0]["prompt"]


def test_missing_window_parameters_are_valid_clarification_not_retry(
    tmp_path: Path,
) -> None:
    request_text = "Add a window to North wall."
    partial = _semantic_body(request_text, parameters={})
    provider = SequentialProvider([partial, partial])

    result = _run(tmp_path, provider, request_text)

    assert result["valid"] is True
    assert result["classification"] == "clarification_required"
    assert len(provider.calls) == 1
    assert result["missing_parameters"] == [
        {
            "operation_id": "intent-op-001",
            "paths": [
                "/opening/height_mm",
                "/opening/sill_height_mm",
                "/opening/width_mm",
                "/position/center_offset_mm",
            ],
        }
    ]
    parameters = result["intent"].operations[0].to_dict()["parameters"]
    assert parameters == {
        "position": {"reference": "wall_local_start"},
        "window": {"fit_opening": True},
    }
    completeness = json.loads(
        (tmp_path / "repair-intent-completeness.json").read_text(encoding="utf-8")
    )
    assert completeness["status"] == "clarification_required"


def test_stage_signature_and_provider_request_are_public_only(tmp_path: Path) -> None:
    stage = _stage_module()
    forbidden = {
        "original_ifc",
        "private_original",
        "gold",
        "mutation",
        "mutation_mapping",
        "resolved_context",
    }
    assert forbidden.isdisjoint(inspect.signature(stage.generate_repair_intent).parameters)

    request_text = "Add a window to North wall using WindowType-A."
    provider = SequentialProvider([_valid_response(request_text)])
    result = _run(tmp_path, provider, request_text)

    assert result["valid"] is True
    assert result["classification"] == "repair_intent"
    assert result["intent"].operations[0].target_query.global_id is None
    assert result["intent"].operations[0].prototype_intent.reference == "WindowType-A"
    assert result["prompt"]["template_id"] == "ifc-repair-intent.v0.1"
    assert len(result["attempts"]) == 1

    serialized_call = json.dumps(provider.calls[0], sort_keys=True)
    assert PRIVATE_CANARY not in serialized_call
    assert "resolved_target_id" not in serialized_call
    assert provider.calls[0]["state"] == {
        "request_id": "request-public-001",
        "stage": "ifc_repair_intent",
        "attempt": 1,
    }
    renderer_input = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )
    supported = next(
        item
        for item in renderer_input["SUPPORTED_OPERATIONS"]
        if item["operation_type"] == "add_window_with_opening_to_wall"
    )
    assert supported["operation_type"] == "add_window_with_opening_to_wall"
    assert supported["target_ifc_classes"] == ["IfcWall"]
    assert supported["prototype_ifc_classes"] == [
        "IfcWindowStyle",
        "IfcWindowType",
    ]
    assert supported["prototype_dimension_paths"] == {
        "height_mm": ["opening", "height_mm"],
        "width_mm": ["opening", "width_mm"],
    }
    assert supported["parameter_schema"]["required"] == [
        "position",
        "opening",
        "window",
    ]


def test_current_prompt_preserves_non_guid_target_selectors(tmp_path: Path) -> None:
    request_text = (
        "在 Level 1 东侧名为 North wall 的 IfcWall 上添加一个窗户。"
    )
    response = _valid_response(request_text)
    response["schema_version"] = "text2ifc/ifc-repair-intent-body/0.3"
    response["operations"][0]["target_query"] = {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
        "names": ["North wall"],
        "storey_name": "Level 1",
        "direction": "east",
    }
    response["operations"][0]["property_intents"] = []
    provider = SequentialProvider([response])

    result = _stage_module().generate_repair_intent(
        provider=provider,
        request_id="request-public-no-guid-001",
        repair_request=request_text,
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version="text2ifc/ifc-repair-intent/0.3",
    )

    assert result["valid"] is True
    target = result["intent"].operations[0].target_query
    assert target.global_id is None
    assert target.names == ("North wall",)
    assert target.storey_name == "Level 1"
    assert target.direction == "east"
    rendered_prompt = provider.calls[0]["prompt"]
    assert "A GUID is optional" in rendered_prompt
    assert "preserve every compatible selector" in rendered_prompt
    assert '"storey_name": "Level 1"' in rendered_prompt


def test_multi_operation_output_retains_provider_order(tmp_path: Path) -> None:
    request_text = "Add matching windows to West wall then North wall."
    response = _valid_response(request_text, operation_id="intent-op-west")
    second = copy.deepcopy(response["operations"][0])
    second["operation_id"] = "intent-op-north"
    second["target_query"]["names"] = ["North wall"]
    response["operations"][0]["target_query"]["names"] = ["West wall"]
    response["operations"].append(second)
    result = _run(tmp_path, SequentialProvider([response]), request_text)
    assert [item.operation_id for item in result["intent"].operations] == [
        "intent-op-west",
        "intent-op-north",
    ]


def _v04_split_created_window_response(request_text: str) -> dict:
    response = _valid_response(request_text, operation_id="add-window-001")
    response["schema_version"] = "text2ifc/ifc-repair-intent-body/0.4"
    response["semantic_bundles"] = []
    addition = response["operations"][0]
    addition["target_query"] = {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
        "global_id": "1PublicWallGuid",
    }
    addition["property_intents"] = []
    addition["semantic_bundle_refs"] = []
    addition["quantity_intents"] = []
    addition["occurrence_reuse_intent"] = None
    property_operation = {
        "operation_id": "set-window-properties-001",
        "operation_type": "set_occurrence_properties",
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWindow"],
            "host_global_id": "1PublicWallGuid",
        },
        "parameters": {},
        "attribute_intents": [],
        "property_intents": [
            {
                "intent_kind": "exact_property",
                "set_name": "Pset_WindowCommon",
                "property_name": "AcousticRating",
                "raw_value": "Rw 35",
                "raw_unit": None,
                "requested_value_type": "IfcLabel",
                "scope": "occurrence_direct",
                "source": _source("Pset_WindowCommon.AcousticRating is Rw 35"),
            }
        ],
        "semantic_bundle_refs": [],
        "quantity_intents": [
            {
                "scope": "opening_occurrence",
                "set_name": "BaseQuantities",
                "quantity_name": "Depth",
                "value": 200.0,
                "value_type": "IfcQuantityLength",
                "unit": "mm",
                "source": _source("Opening BaseQuantities.Depth is 200 mm"),
            }
        ],
        "occurrence_reuse_intent": None,
        "prototype_intent": copy.deepcopy(addition["prototype_intent"]),
        "provenance": [_source("set the stated properties on the new window")],
    }
    response["operations"].append(property_operation)
    return response


def test_v04_folds_unbound_properties_into_unique_created_window(
    tmp_path: Path,
) -> None:
    request_text = "Add one Window to wall 1PublicWallGuid and set its rating."
    response = _v04_split_created_window_response(request_text)
    provider = SequentialProvider([response, response])

    result = _stage_module().generate_repair_intent(
        provider=provider,
        request_id="request-fold-created-window-001",
        repair_request=request_text,
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version="text2ifc/ifc-repair-intent/0.4",
    )

    assert result["valid"] is True, result
    assert [item.operation_id for item in result["intent"].operations] == [
        "add-window-001"
    ]
    assert (
        result["intent"].operations[0].property_intents[0].property_name
        == "AcousticRating"
    )
    assert (
        result["intent"].operations[0].quantity_intents[0].quantity_name
        == "Depth"
    )
    assert result["attempts"][0]["normalizations"] == [
        "FOLD_CREATED_WINDOW_OCCURRENCE_PROPERTIES:"
        "set-window-properties-001->add-window-001"
    ]
    stored = json.loads(
        (tmp_path / "attempt-001.json").read_text(encoding="utf-8")
    )
    assert stored["normalizations"] == result["attempts"][0]["normalizations"]


def test_v04_does_not_fold_explicit_or_ambiguous_window_property_target() -> None:
    stage = _stage_module()
    request_text = "Add one Window and update an existing Window."
    explicit = _v04_split_created_window_response(request_text)
    explicit["operations"][1]["target_query"]["global_id"] = "ExistingWindowGuid"
    normalized, codes = stage._fold_created_window_property_operations(explicit)
    assert len(normalized["operations"]) == 2
    assert codes == []

    ambiguous = _v04_split_created_window_response(request_text)
    second_addition = copy.deepcopy(ambiguous["operations"][0])
    second_addition["operation_id"] = "add-window-002"
    ambiguous["operations"].insert(1, second_addition)
    normalized, codes = stage._fold_created_window_property_operations(ambiguous)
    assert len(normalized["operations"]) == 3
    assert codes == []


def test_invalid_output_is_corrected_once_with_bounded_redacted_evidence(
    tmp_path: Path,
) -> None:
    request_text = "Add a window to North wall."
    invalid = _valid_response(request_text)
    invalid["operations"][0]["operation_type"] = "invented_operation"
    invalid["provenance"][0]["excerpt"] = PRIVATE_CANARY
    valid = _valid_response(request_text)
    provider = SequentialProvider([invalid, valid])

    result = _run(tmp_path, provider, request_text)

    assert result["valid"] is True
    assert len(provider.calls) == 2
    assert [attempt["status"] for attempt in result["attempts"]] == [
        "invalid",
        "valid",
    ]
    assert provider.calls[1]["state"]["attempt"] == 2
    assert "REPAIR_INTENT_UNSUPPORTED_OPERATION" in provider.calls[1]["prompt"]
    stored_attempt = (tmp_path / "attempt-001.json").read_text(encoding="utf-8")
    assert PRIVATE_CANARY not in stored_attempt
    assert "[REDACTED_PRIVATE]" in stored_attempt


def test_retry_exhaustion_has_stable_typed_failure_and_byte_stable_evidence(
    tmp_path: Path,
) -> None:
    request_text = "Add a window to North wall."
    invalid = _valid_response(request_text)
    invalid["operations"][0]["target_query"] = {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
    }
    result = _run(tmp_path, SequentialProvider([invalid, invalid]), request_text)

    assert result["valid"] is False
    assert result["classification"] == "invalid"
    assert result["error_code"] == "REPAIR_INTENT_RETRY_EXHAUSTED"
    assert len(result["attempts"]) == 2
    first = (tmp_path / "attempt-001.json").read_bytes()

    second_dir = tmp_path / "repeat"
    repeated = _run(second_dir, SequentialProvider([invalid, invalid]), request_text)
    assert repeated["attempts"] == result["attempts"]
    assert (second_dir / "attempt-001.json").read_bytes() == first


def test_unknown_fields_resolved_guid_and_oversized_output_fail_closed(
    tmp_path: Path,
) -> None:
    stage = _stage_module()
    request_text = "Add a window to North wall."
    response = _valid_response(request_text)
    response["operations"][0]["resolved_target_guid"] = "secret-wall-guid"
    result = _run(tmp_path / "resolved", SequentialProvider([response, response]), request_text)
    assert result["error_code"] == "REPAIR_INTENT_RETRY_EXHAUSTED"
    assert all(
        issue["code"] == "REPAIR_INTENT_SCHEMA_INVALID"
        for attempt in result["attempts"]
        for issue in attempt["issues"]
    )

    oversized = "{" + "x" * (stage.MAX_PROVIDER_RESPONSE_BYTES + 1)
    result = _run(tmp_path / "oversized", SequentialProvider([oversized, oversized]), request_text)
    assert result["error_code"] == "REPAIR_INTENT_RETRY_EXHAUSTED"
    assert result["attempts"][0]["issues"][0]["code"] == "PROVIDER_RESPONSE_TOO_LARGE"


def test_request_text_and_attempt_counts_are_bounded_before_provider_call(
    tmp_path: Path,
) -> None:
    stage = _stage_module()
    provider = SequentialProvider([])
    result = stage.generate_repair_intent(
        provider=provider,
        request_id="request-public-001",
        repair_request="x" * (stage.MAX_REQUEST_BYTES + 1),
        registry=create_default_registry(),
        output_dir=tmp_path,
    )
    assert result["valid"] is False
    assert result["error_code"] == "REPAIR_REQUEST_TOO_LARGE"
    assert provider.calls == []


def test_provider_failures_use_the_same_bounded_typed_attempt_protocol(
    tmp_path: Path,
) -> None:
    stage = _stage_module()
    provider = FailingProvider()
    result = stage.generate_repair_intent(
        provider=provider,
        request_id="request-public-001",
        repair_request="Add a window to North wall.",
        registry=create_default_registry(),
        output_dir=tmp_path,
    )
    assert result["error_code"] == "REPAIR_INTENT_RETRY_EXHAUSTED"
    assert provider.calls == stage.MAX_CORRECTION_ATTEMPTS
    assert [attempt["issues"][0]["code"] for attempt in result["attempts"]] == [
        "REPAIR_INTENT_PROVIDER_FAILED",
        "REPAIR_INTENT_PROVIDER_FAILED",
    ]
    assert "private provider failure" not in (
        tmp_path / "attempt-001.json"
    ).read_text(encoding="utf-8")
