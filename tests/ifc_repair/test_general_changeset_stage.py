from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry


MODEL = "sha256:" + "a" * 64
REQUEST = "sha256:" + "b" * 64


def _api():
    module = importlib.import_module("text2ifc_ifc_repair.provider_stage")
    if not hasattr(module, "generate_bound_changeset"):
        pytest.fail("resolved-context Stage 2 is not implemented")
    return module


class Provider:
    def __init__(self, responses: list[dict | str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        text = response if isinstance(response, str) else json.dumps(response)
        return ProviderOutput(text=text, metadata={"provider": "fixture"})


def _definition(operation_type: str) -> OperationDefinition:
    return OperationDefinition(
        operation_type=operation_type,
        target_ifc_classes=("IfcWall",),
        parameter_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["marker"],
            "properties": {"marker": {"type": "string"}},
        },
        target_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["wall_global_id"],
            "properties": {"wall_global_id": {"type": "string"}},
        },
        context_adapter=lambda **kwargs: kwargs,
        precondition_checker=lambda **kwargs: (),
        applicator=lambda **kwargs: kwargs,
        postcondition_checker=lambda **kwargs: (),
        comparison_adapter=lambda **kwargs: kwargs,
        capability_constraints={"fixture": True},
        precondition_names=("target_exists",),
        postcondition_names=("target_updated",),
    )


def _registry() -> OperationRegistry:
    registry = OperationRegistry()
    registry.register(_definition("fixture_move"))
    registry.register(_definition("fixture_resize"))
    return registry


def _resolved() -> tuple[dict, ...]:
    return (
        {
            "operation_id": "intent-a",
            "operation_type": "fixture_move",
            "target_global_id": "0AAAAAAAAAAAAAAAAAAAAA",
            "scope_ids": ["0AAAAAAAAAAAAAAAAAAAAA"],
            "evidence_pointers": ["resolved:/operations/intent-a/context/candidate_targets/0"],
            "parameters": {"marker": "move"},
            "authorized_semantics": [{"kind": "formal_type_binding", "global_id": "0TYPEAAAAAAAAAAAAAAAAA"}],
            "context": {
                "model_fingerprint": MODEL,
                "candidate_targets": [{"ifc_global_id": "0AAAAAAAAAAAAAAAAAAAAA", "ifc_class": "IfcWall"}],
            },
        },
        {
            "operation_id": "intent-b",
            "operation_type": "fixture_resize",
            "target_global_id": "0BBBBBBBBBBBBBBBBBBBBB",
            "scope_ids": ["0BBBBBBBBBBBBBBBBBBBBB"],
            "evidence_pointers": ["resolved:/operations/intent-b/context/candidate_targets/0"],
            "parameters": {"marker": "resize"},
            "authorized_semantics": [],
            "context": {
                "model_fingerprint": MODEL,
                "candidate_targets": [{"ifc_global_id": "0BBBBBBBBBBBBBBBBBBBBB", "ifc_class": "IfcWall"}],
            },
        },
    )


def _changeset() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-general-001",
        "base_model_fingerprint": MODEL,
        "source_request_hash": REQUEST,
        "scope": {"target_ids": ["0AAAAAAAAAAAAAAAAAAAAA", "0BBBBBBBBBBBBBBBBBBBBB"], "forbidden_ids": []},
        "evidence_refs": [
            "resolved:/operations/intent-a/context/candidate_targets/0",
            "resolved:/operations/intent-b/context/candidate_targets/0",
        ],
        "preconditions": ["target_exists"],
        "postconditions": ["target_updated"],
        "operations": [
            {
                "operation_id": "intent-a",
                "operation_type": "fixture_move",
                "target": {"wall_global_id": "0AAAAAAAAAAAAAAAAAAAAA"},
                "parameters": {"marker": "move"},
                "evidence_refs": ["resolved:/operations/intent-a/context/candidate_targets/0"],
            },
            {
                "operation_id": "intent-b",
                "operation_type": "fixture_resize",
                "target": {"wall_global_id": "0BBBBBBBBBBBBBBBBBBBBB"},
                "parameters": {"marker": "resize"},
                "evidence_refs": ["resolved:/operations/intent-b/context/candidate_targets/0"],
            },
        ],
    }


def _run(tmp_path: Path, response: dict | str, *, resolved=None, max_attempts: int = 1):
    provider = Provider([response] * max_attempts)
    result = _api().generate_bound_changeset(
        provider=provider,
        case_id="general-001",
        repair_request="repair both walls",
        source_request_hash=REQUEST,
        resolved_operations=_resolved() if resolved is None else resolved,
        model_fingerprint=MODEL,
        registry=_registry(),
        output_dir=tmp_path,
        max_attempts=max_attempts,
    )
    return result, provider


def test_multiple_resolved_operations_produce_one_fully_bound_changeset(tmp_path: Path) -> None:
    result, provider = _run(tmp_path, _changeset())

    assert result["valid"] is True
    assert result["changeset"] == _changeset()
    assert result["prompt"] == {
        "template_id": "ifc-repair-changeset.v0.2",
        "template_hash": load_prompt_registry()["ifc-repair-changeset.v0.2"]["sha256"],
    }
    assert len(provider.calls) == 1
    request = provider.calls[0]
    serialized = json.dumps(request, sort_keys=True)
    assert "candidate search" not in serialized.lower()
    assert "PRIVATE_ORIGINAL" not in serialized
    assert request["state"]["stage"] == "ifc_repair_bound_changeset"
    assert "Single-operation shape" in request["prompt"]
    assert "Multiple-operation shape" in request["prompt"]


@pytest.mark.parametrize(
    ("case", "mutate"),
    [
        ("partial", lambda value: value["operations"].pop()),
        ("duplicate", lambda value: value["operations"].append(copy.deepcopy(value["operations"][0]))),
        ("foreign-target", lambda value: value["operations"][0]["target"].update(wall_global_id="0FOREIGNAAAAAAAAAAAAAA")),
        ("cross-operation-target", lambda value: value["operations"][0]["target"].update(wall_global_id="0BBBBBBBBBBBBBBBBBBBBB")),
        ("cross-operation-evidence", lambda value: value["operations"][0].update(evidence_refs=["resolved:/operations/intent-b/context/candidate_targets/0"])),
        ("stale-request", lambda value: value.update(source_request_hash="sha256:" + "c" * 64)),
        ("stale-model", lambda value: value.update(base_model_fingerprint="sha256:" + "c" * 64)),
        ("unsupported-operation", lambda value: value["operations"][0].update(operation_type="not_registered")),
        ("changed-parameters", lambda value: value["operations"][0].update(parameters={"marker": "guessed"})),
        ("unknown-field", lambda value: value["operations"][0].update(search_query="find another wall")),
        ("prototype-choice", lambda value: value["operations"][0].update(prototype_global_id="0TYPEBBBBBBBBBBBBBBBBB")),
        ("step-output", lambda value: value["operations"][0].update(parameters={"marker": "ISO-10303-21;"})),
    ],
)
def test_adversarial_or_partial_output_fails_closed(tmp_path: Path, case: str, mutate) -> None:
    response = _changeset()
    mutate(response)
    result, _ = _run(tmp_path / case, response)

    assert result["valid"] is False
    assert result["changeset"] is None
    assert result["issues"], case


def test_reordered_operation_id_substitution_cannot_cross_contexts(tmp_path: Path) -> None:
    response = _changeset()
    response["operations"][0]["operation_id"] = "intent-b"
    response["operations"][1]["operation_id"] = "intent-a"
    result, _ = _run(tmp_path, response)

    assert result["valid"] is False
    assert {issue["code"] for issue in result["issues"]} >= {"OPERATION_TYPE_MISMATCH", "OPERATION_TARGET_OUTSIDE_CONTEXT"}


def test_private_canary_or_unresolved_context_never_reaches_provider(tmp_path: Path) -> None:
    resolved = list(_resolved())
    resolved[0] = {**resolved[0], "context": {**resolved[0]["context"], "private_original": "PRIVATE_ORIGINAL"}}
    result, provider = _run(tmp_path, _changeset(), resolved=tuple(resolved))

    assert result["valid"] is False
    assert len(provider.calls) == 0
    assert {issue["code"] for issue in result["issues"]} >= {"PRIVATE_CONTEXT_FORBIDDEN"}


def test_invalid_output_has_one_finite_corrected_attempt(tmp_path: Path) -> None:
    provider = Provider([{"unsupported_reason": "bad"}, _changeset()])
    result = _api().generate_bound_changeset(
        provider=provider,
        case_id="retry-001",
        repair_request="repair both walls",
        source_request_hash=REQUEST,
        resolved_operations=_resolved(),
        model_fingerprint=MODEL,
        registry=_registry(),
        output_dir=tmp_path,
        max_attempts=2,
    )

    assert result["valid"] is True
    assert len(provider.calls) == 2
    assert (tmp_path / "attempt-001" / "diagnostics.json").is_file()
    assert (tmp_path / "attempt-002" / "diagnostics.json").is_file()
