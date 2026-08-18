import copy
import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.repair_intent import (
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6,
    REPAIR_INTENT_SCHEMA_VERSION_0_6,
    RepairIntent,
    RepairIntentError,
    fingerprint_text,
    hash_request,
    load_repair_intent_body_schema,
    load_repair_intent_schema,
)
from text2ifc_ifc_repair.request_stage import generate_repair_intent


CASES_PATH = (
    Path(__file__).parent / "fixtures" / "phase12_stage1_scope_cases.json"
)
SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "EXAMPLE_ONLY",
}


class SequentialProvider:
    def __init__(self, responses: list[dict | str]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        value = self.responses[len(self.calls) - 1]
        return ProviderOutput(
            text=value if isinstance(value, str) else json.dumps(value),
            metadata={"provider": "test", "model": "stage1-contract-test"},
        )


def _routing(family: str) -> dict:
    return {
        "component_family": family,
        "action": "add",
        "operation_profile": f"{family}.add.v0.2",
        "source": SOURCE,
    }


def _beam_operation(*, shape: str = "rectangle", target: dict | None = None) -> dict:
    return {
        "operation_id": "beam-1",
        "operation_type": "add_beam",
        "routing_intent": _routing("beam"),
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            **(target or {"names": ["Level 1"]}),
        },
        "parameters": {
            "axis": {
                "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
                "end": {"x_mm": 6000, "y_mm": 0, "z_mm": 3000},
            },
            "section": {"shape": shape, "width_mm": 300, "height_mm": 500},
        },
        "attribute_intents": [],
        "property_intents": [],
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": None,
        "provenance": [SOURCE],
    }


def _body(*operations: dict, unsupported_requests: list[dict] | None = None) -> dict:
    return {
        "schema_version": REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6,
        "operations": list(operations),
        "unsupported_requests": list(unsupported_requests or ()),
        "semantic_bundles": [],
        "provenance": [SOURCE],
    }


def _unsupported(
    *,
    capability_id: str,
    operation_id: str | None = "beam-1",
    kind: str = "registered_capability",
) -> dict:
    return {
        "unsupported_id": "unsupported-1",
        "kind": kind,
        "operation_id": operation_id,
        "capability_id": capability_id,
        "source": SOURCE,
    }


def _envelope(body: dict) -> dict:
    return {
        "schema_version": REPAIR_INTENT_SCHEMA_VERSION_0_6,
        "request_id": "request-1",
        "source_request_hash": hash_request("EXAMPLE_ONLY"),
        "model_fingerprint": fingerprint_text("model"),
        "prompt_fingerprint": fingerprint_text("prompt"),
        "operations": body["operations"],
        "unsupported_requests": body["unsupported_requests"],
        "semantic_bundles": body["semantic_bundles"],
        "provenance": body["provenance"],
    }


def test_failure_family_is_frozen_and_covers_both_cross_scene_labels() -> None:
    matrix = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    case_ids = [case["case_id"] for case in matrix["cases"]]

    assert len(case_ids) == 16
    assert len(case_ids) == len(set(case_ids))
    assert {case["scene"] for case in matrix["cases"]} == {"d7n", "vvo"}
    assert {
        "analysis-member",
        "analysis-node",
        "analysis-load",
        "analysis-port",
        "analysis-connection",
        "pure-unregistered-render",
        "mixed-repair-and-render",
        "forbidden-rectangular-alias",
        "forbidden-storey-filter-selector",
        "malformed-truncated-json",
    }.issubset(case_ids)


def test_v06_schemas_are_new_exact_contracts_and_old_versions_remain_loadable() -> None:
    assert load_repair_intent_schema(REPAIR_INTENT_SCHEMA_VERSION_0_6)["$id"] == (
        REPAIR_INTENT_SCHEMA_VERSION_0_6
    )
    body_schema = load_repair_intent_body_schema(
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6
    )
    assert body_schema["$id"] == REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6
    assert "unsupported_requests" in body_schema["required"]
    assert load_repair_intent_schema("text2ifc/ifc-repair-intent/0.5")["$id"] == (
        "text2ifc/ifc-repair-intent/0.5"
    )


def test_v06_round_trips_registered_and_pure_unregistered_unsupported_requests() -> None:
    registry = create_default_registry()
    registered = RepairIntent.from_dict(
        _envelope(
            _body(
                _beam_operation(),
                unsupported_requests=[
                    _unsupported(capability_id="structural_analysis_node")
                ],
            )
        ),
        registry=registry,
        require_complete=False,
    )
    assert registered.to_dict()["unsupported_requests"] == [
        _unsupported(capability_id="structural_analysis_node")
    ]

    pure = RepairIntent.from_dict(
        _envelope(
            _body(
                unsupported_requests=[
                    _unsupported(
                        capability_id="unregistered_operation",
                        operation_id=None,
                        kind="unregistered_action",
                    )
                ]
            )
        ),
        registry=registry,
        require_complete=False,
    )
    assert pure.operations == ()
    assert pure.unsupported_requests[0].operation_id is None


@pytest.mark.parametrize(
    ("mutation", "path_fragment"),
    [
        (lambda body: body.update(operations=[], unsupported_requests=[]), "/"),
        (
            lambda body: body["unsupported_requests"][0].update(
                capability_id="unknown_alias"
            ),
            "/unsupported_requests/0/capability_id",
        ),
        (
            lambda body: body["unsupported_requests"][0].update(extra=True),
            "/unsupported_requests/0",
        ),
    ],
)
def test_v06_rejects_empty_or_noncanonical_unsupported_contract(
    mutation, path_fragment: str
) -> None:
    body = _body(
        _beam_operation(),
        unsupported_requests=[
            _unsupported(capability_id="structural_analysis_node")
        ],
    )
    mutation(body)
    with pytest.raises(RepairIntentError) as captured:
        RepairIntent.from_dict(
            _envelope(body),
            registry=create_default_registry(),
            require_complete=False,
        )
    assert path_fragment in captured.value.path or path_fragment == "/"


@pytest.mark.parametrize(
    ("shape", "target", "accepted"),
    [
        ("rectangle", {"names": ["Level 1"]}, True),
        ("rectangular", {"names": ["Level 1"]}, False),
        ("rectangle", {"storey_name": "Level 1"}, False),
    ],
)
def test_v06_beam_shape_and_storey_target_are_exact(
    shape: str, target: dict, accepted: bool
) -> None:
    document = _envelope(_body(_beam_operation(shape=shape, target=target)))
    if accepted:
        intent = RepairIntent.from_dict(
            document, registry=create_default_registry(), require_complete=False
        )
        assert intent.operations[0].target_query.names == ("Level 1",)
        return
    with pytest.raises(RepairIntentError):
        RepairIntent.from_dict(
            document, registry=create_default_registry(), require_complete=False
        )


@pytest.mark.parametrize(
    "capability_id",
    [
        "structural_analysis_member",
        "structural_analysis_node",
        "structural_analysis_load",
        "structural_analysis_port",
        "structural_analysis_connection",
    ],
)
def test_stage1_registered_analysis_family_stops_before_completeness(
    tmp_path: Path, capability_id: str
) -> None:
    body = _body(
        _beam_operation(),
        unsupported_requests=[_unsupported(capability_id=capability_id)],
    )
    body["operations"][0]["parameters"] = {}
    provider = SequentialProvider([body])

    result = generate_repair_intent(
        provider=provider,
        request_id="scope-1",
        repair_request="EXAMPLE_ONLY",
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_6,
    )

    assert result["valid"] is True
    assert result["classification"] == "unsupported"
    assert result["reason_code"] == "STRUCTURAL_ANALYSIS_UNSUPPORTED"
    assert result["missing_parameters"] == []
    assert len(provider.calls) == 1


def test_stage1_pure_and_mixed_unregistered_actions_have_distinct_reasons(
    tmp_path: Path,
) -> None:
    pure = _body(
        unsupported_requests=[
            _unsupported(
                capability_id="unregistered_operation",
                operation_id=None,
                kind="unregistered_action",
            )
        ]
    )
    mixed = _body(
        _beam_operation(),
        unsupported_requests=[
            _unsupported(
                capability_id="unregistered_operation",
                operation_id=None,
                kind="unregistered_action",
            )
        ],
    )
    for label, body, expected in (
        ("pure", pure, "REPAIR_REQUEST_OUT_OF_SCOPE"),
        ("mixed", mixed, "REPAIR_REQUEST_CONTAINS_UNSUPPORTED_ACTIONS"),
    ):
        result = generate_repair_intent(
            provider=SequentialProvider([body]),
            request_id=f"scope-{label}",
            repair_request="EXAMPLE_ONLY",
            registry=create_default_registry(),
            output_dir=tmp_path / label,
            intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_6,
        )
        assert result["valid"] is True
        assert result["classification"] == "unsupported"
        assert result["reason_code"] == expected


def test_stage1_malformed_output_retries_but_never_normalizes_it(tmp_path: Path) -> None:
    malformed = '{"schema_version":'
    provider = SequentialProvider([malformed, malformed])
    result = generate_repair_intent(
        provider=provider,
        request_id="scope-malformed",
        repair_request="EXAMPLE_ONLY",
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_6,
    )
    assert result["valid"] is False
    assert result["error_code"] == "REPAIR_INTENT_RETRY_EXHAUSTED"
    assert len(provider.calls) == 2
    assert all(attempt["normalizations"] == [] for attempt in result["attempts"])


def test_stage1_compact_catalog_exposes_target_schema_but_no_full_few_shots(
    tmp_path: Path,
) -> None:
    body = _body(_beam_operation())
    provider = SequentialProvider([body])
    result = generate_repair_intent(
        provider=provider,
        request_id="scope-compact",
        repair_request="EXAMPLE_ONLY",
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_6,
    )
    assert result["valid"] is True
    catalog = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )["SUPPORTED_OPERATIONS"]
    beam = next(item for item in catalog if item["operation_type"] == "add_beam")
    assert beam["profile_id"] == "beam.add.v0.2"
    assert beam["intent_target_schema"]["properties"]["allowed_ifc_classes"] == {
        "const": ["IfcBuildingStorey"]
    }
    assert "few_shots" not in beam
    assert "EXAMPLE_ONLY" not in json.dumps(catalog)


def test_stage1_does_not_mutate_provider_body_or_import_private_inputs(
    tmp_path: Path,
) -> None:
    body = _body(_beam_operation())
    before = copy.deepcopy(body)
    provider = SequentialProvider([body])
    result = generate_repair_intent(
        provider=provider,
        request_id="scope-isolation",
        repair_request="EXAMPLE_ONLY",
        registry=create_default_registry(),
        output_dir=tmp_path,
        intent_schema_version=REPAIR_INTENT_SCHEMA_VERSION_0_6,
    )
    assert result["valid"] is True
    assert body == before
    call_text = json.dumps(provider.calls, sort_keys=True)
    assert "private_original_ifc" not in call_text
    assert "mutation_manifest.private.json" not in call_text
