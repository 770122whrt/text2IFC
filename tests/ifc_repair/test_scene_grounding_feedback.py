"""Frozen offline feedback family: schema, retry state, limits and terminal causes.

These deterministic fixtures exercise the failed invariants, not model capability.
Cross-scene siblings use different labels/identities and translated geometry.
"""
from copy import deepcopy
import hashlib
import json

import pytest

from text2ifc_agent.prompt_registry import PROJECT_ROOT, load_prompt_registry
from text2ifc_agent.providers import ProviderOutputError
from text2ifc_ifc_repair import scene_grounding as grounding
from tests.ifc_repair.test_scene_grounding import QueueProvider, final_response, run
from tests.ifc_repair.test_scene_grounding_v03 import position_question
from tests.ifc_repair.test_scene_context import fixture_scene
from tests.ifc_repair.test_spatial_grounding import body


def read_round(path, number):
    return json.loads((path / f"round-{number:03d}" / "renderer-input.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("kind", ["intent", "clarification"])
def test_schema_feedback_uses_actual_kind_leaf_path_and_previous_proposal(tmp_path, kind):
    response = final_response() if kind == "intent" else position_question()
    del response["intent"]["operations"][0]["operation_type"]
    result = run(tmp_path, QueueProvider([response, response]), max_rounds=2)
    issue = result["attempts"][0]["issues"][0]
    assert issue["code"] == "SCENE_RESPONSE_SCHEMA_INVALID"
    assert issue["path"] == "/intent/operations/0/operation_type"
    assert "operation_type" in issue["message"] and "not valid under any" not in issue["message"]
    retry = read_round(tmp_path, 2)
    assert retry["PREVIOUS_PROPOSAL"] == response
    assert len(retry["VALIDATION_FEEDBACK"]) <= 5
    assert result["scene_diagnostics"]["rounds"][0]["stage"] == "schema"


def test_oversized_previous_proposal_is_bounded_valid_json(tmp_path):
    bad = {"kind": "query", "query": {"names": ["世" * 12000], "unknown": "x" * 12000}}
    run(tmp_path, QueueProvider([bad, bad]), max_rounds=2)
    previous = read_round(tmp_path, 2)["PREVIOUS_PROPOSAL"]
    assert previous["truncated"] is True
    assert len(json.dumps(previous, ensure_ascii=False).encode("utf-8")) <= 16 * 1024


def test_missing_position_attempt_is_invalid_before_it_is_persisted(tmp_path):
    final = {"kind": "intent", "intent": body(), "bindings": [{"operation_id": "offline-repair", "target_id": "wall"}]}
    result = run(tmp_path, QueueProvider([{"kind": "query", "query": {"ids": ["wall"]}}, final]), max_rounds=2)
    last = result["attempts"][-1]
    disk = json.loads((tmp_path / "round-002" / "attempt-002.json").read_text(encoding="utf-8"))
    assert last == disk and last["status"] == "invalid"
    assert last["issues"][0]["code"] == "SCENE_POSITION_NOT_GROUNDED"
    assert result["failure_summary"]["last_issue_codes"] == ["SCENE_POSITION_NOT_GROUNDED"]
    assert result["scene_diagnostics"]["rounds"][-1]["stage"] == "geometry"


@pytest.mark.parametrize("wall_id, shift", [("wall", 0), ("building-b-host", 20000)])
def test_success_and_query_counts_are_bounded_and_exclude_model_content(tmp_path, wall_id, shift):
    scene = fixture_scene()
    wall = scene.records[0]
    wall["id"] = wall_id
    wall["center_world_mm"][0] += shift
    wall["bounds_world_mm"]["x"] = [v + shift for v in wall["bounds_world_mm"]["x"]]
    wall["wall_axis"]["start_world_mm"][0] += shift
    scene = type(scene)(scene.records, scene.storeys, project_unit_scale=scene.project_unit_scale)
    final = {"kind": "intent", "intent": body(), "bindings": [{"operation_id": "offline-repair", "target_id": wall_id,
             "position": {"kind": "world_point", "point_world_mm": [100 + shift, 2500, 0]}}]}
    result = run(tmp_path, QueueProvider([{"kind": "query", "query": {"ids": [wall_id]}}, final]), scene=scene)
    assert result["valid"], result
    diagnostics = result["scene_diagnostics"]
    assert diagnostics["schema_version"] == "text2ifc/scene-diagnostics/0.1"
    assert diagnostics["terminal_reason"] == "repair_intent"
    assert diagnostics["rounds"][0]["returned_count"] == diagnostics["rounds"][0]["total_matches"] == 1
    assert diagnostics["rounds"][0]["query_id"] == "q1"
    encoded = json.dumps(diagnostics, ensure_ascii=False)
    assert len(encoded.encode("utf-8")) <= 12 * 1024
    assert wall_id not in encoded and "offline-repair" not in encoded and "point_world_mm" not in encoded
    assert diagnostics == json.loads((tmp_path / "scene-diagnostics.json").read_text(encoding="utf-8"))


def test_clarification_and_unsupported_keep_terminal_diagnostics(tmp_path):
    result = run(tmp_path / "clarify", QueueProvider([{"kind": "query", "query": {"ids": ["wall"]}}, position_question()]))
    assert result["scene_diagnostics"]["terminal_reason"] == "clarification_required"
    unsupported = body()
    unsupported["operations"] = []
    unsupported["unsupported_requests"] = [{"unsupported_id": "outside", "kind": "unregistered_action", "operation_id": None,
                                             "capability_id": "unregistered_operation", "source": unsupported["provenance"][0]}]
    result = run(tmp_path / "unsupported", QueueProvider([{"kind": "intent", "intent": unsupported, "bindings": []}]))
    assert result["scene_diagnostics"]["terminal_reason"] == "unsupported"


@pytest.mark.parametrize("response, stage", [('not json', "parse"), ({"kind": "query", "query": {"limit": -1}}, "schema"),
                                            (final_response(), "geometry")])
def test_failure_stage_and_eight_call_bound_are_preserved(tmp_path, response, stage):
    provider = QueueProvider([deepcopy(response) for _ in range(8)])
    result = run(tmp_path, provider)
    assert not result["valid"] and len(provider.calls) == 8
    diagnostics = result["scene_diagnostics"]
    assert len(diagnostics["rounds"]) == 8
    assert all(item["stage"] == stage for item in diagnostics["rounds"])
    assert diagnostics["terminal_reason"] == "SCENE_GROUNDING_EXHAUSTED"


def test_context_limit_still_blocks_without_a_model_call(tmp_path, monkeypatch):
    monkeypatch.setattr(grounding, "MAX_CONTEXT_BYTES", 1)
    provider = QueueProvider([])
    result = run(tmp_path, provider)
    assert result["error_code"] == "SCENE_CONTEXT_BUDGET_EXCEEDED" and not provider.calls
    assert result["scene_diagnostics"]["terminal_reason"] == "SCENE_CONTEXT_BUDGET_EXCEEDED"
    assert result["scene_diagnostics"]["rounds"] == []


@pytest.mark.parametrize("details, code", [({"http_status": 401}, "PROVIDER_HTTP_401"),
    ({"failure_class": "provider_connection_error", "exception_type": "APITimeoutError", "transport_attempts": 3}, "PROVIDER_TIMEOUT"),
    ({"failure_class": "provider_connection_error", "exception_type": "AuthenticationError"}, "PROVIDER_AUTHENTICATION_FAILED"),
    ({"failure_class": "input_token_budget_exceeded"}, "PROVIDER_INPUT_TOKEN_BUDGET_EXCEEDED")])
def test_transport_or_request_failure_does_not_spend_remaining_grounding_rounds(tmp_path, details, code):
    class BrokenProvider:
        calls = 0

        def generate_candidate(self, **kwargs):
            self.calls += 1
            raise ProviderOutputError("secret response must not be exported", details=details)

    provider = BrokenProvider()
    result = run(tmp_path, provider)
    assert provider.calls == 1 and result["error_code"] == code
    assert result["scene_diagnostics"]["terminal_reason"] == code
    assert result["scene_diagnostics"]["rounds"][0]["stage"] == "provider"
    assert "secret response" not in json.dumps(result["scene_diagnostics"])


def test_unsupported_geometry_stops_without_retrying_the_hard_boundary(tmp_path, monkeypatch):
    def unsupported(*args, **kwargs):
        raise grounding.GroundingError("PUBLIC_GEOMETRY_STRUCTURAL_ORIENTATION_UNSUPPORTED")

    monkeypatch.setattr(grounding, "bind_spatial_intent", unsupported)
    provider = QueueProvider([final_response()] * 8)
    result = run(tmp_path, provider)
    assert len(provider.calls) == 1
    assert result["error_code"] == "PUBLIC_GEOMETRY_STRUCTURAL_ORIENTATION_UNSUPPORTED"
    assert result["scene_diagnostics"]["rounds"][-1]["stage"] == "geometry"


def test_version_upgrade_preserves_registered_v03_prompt_and_schema():
    registry = load_prompt_registry()
    old_prompt = (PROJECT_ROOT / registry["ifc-scene-grounding.v0.3"]["path"]).read_bytes()
    assert "sha256:" + hashlib.sha256(old_prompt).hexdigest() == "sha256:5f2370dd8558acb41b9631fc845bc0a07c2d7604be0d0a09780153c26efaceef"
    assert grounding.TEMPLATE_ID == "ifc-scene-grounding.v0.7"
    assert "PREVIOUS_PROPOSAL" in registry[grounding.TEMPLATE_ID]["required_inputs"]
    new_schema = grounding.load_scene_response_schema()
    assert new_schema["$id"].endswith("/0.4")
    old_schema = json.loads((PROJECT_ROOT / "schemas/agent/ifc-scene-grounding-response-0.3.schema.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in new_schema.items() if k not in {"$id", "title"}} == {k: v for k, v in old_schema.items() if k not in {"$id", "title"}}


@pytest.mark.parametrize("kind", [{"value": "intent"}, ["query"], None, "anything"])
def test_invalid_kind_has_a_leaf_error_without_crashing(kind):
    issues = grounding._schema_issues({"kind": kind}, grounding.load_scene_response_schema())
    assert issues[0]["path"] == "/kind"


def test_nested_binding_schema_error_does_not_include_other_response_kinds():
    proposal = final_response()
    proposal["bindings"][0]["position"] = {"kind": "world_point", "point_world_mm": ["north", 2, 3]}
    issues = grounding._schema_issues(proposal, grounding.load_scene_response_schema())
    assert [issue["path"] for issue in issues] == ["/bindings/0/position/point_world_mm/0"]
    assert issues[0]["message"] == 'Expected type: "number"'


def test_truncated_adapter_response_retries_with_previous_excerpt(tmp_path):
    from text2ifc_agent.openai_compat import OpenAICompatError

    class TruncatedThenComplete(QueueProvider):
        def generate_candidate(self, **kwargs):
            if not self.calls:
                self.calls.append(kwargs)
                raise OpenAICompatError("truncated", evidence={"failure_class": "truncated", "content_text": '{"kind":', "usage": {"output_tokens": 5}})
            return super().generate_candidate(**kwargs)

    query = {"kind": "query", "query": {"ids": ["wall"]}}
    provider = TruncatedThenComplete([query])
    result = run(tmp_path, provider, max_rounds=2)
    assert len(provider.calls) == 2
    assert result["attempts"][0]["issues"][0]["code"] == "PROVIDER_RESPONSE_TRUNCATED"
    assert read_round(tmp_path, 2)["PREVIOUS_PROPOSAL"]["unparsed_excerpt"] == '{"kind":'


def test_diagnostic_paths_cannot_export_unknown_identity_keys():
    names = grounding._schema_property_names(grounding.load_scene_response_schema())
    assert grounding._diagnostic_path("/intent/operations/0/private-entity-identity", names) == "/intent/operations/0/_redacted"


def test_retry_keeps_only_latest_failed_proposal_then_clears_on_valid_query(tmp_path):
    first = {"kind": "query", "query": {"limit": -1}}
    second = {"kind": "query", "query": {"ids": ["wall"], "limit": -2}}
    query = {"kind": "query", "query": {"ids": ["wall"]}}
    result = run(tmp_path, QueueProvider([first, second, query, position_question()]), max_rounds=4)
    assert result["valid"] and result["classification"] == "clarification_required"
    assert read_round(tmp_path, 2)["PREVIOUS_PROPOSAL"] == first
    assert read_round(tmp_path, 3)["PREVIOUS_PROPOSAL"] == second
    assert read_round(tmp_path, 4)["PREVIOUS_PROPOSAL"] is None
