"""Frozen offline localization family; no live language-capability claims."""
from copy import deepcopy
import json

import pytest

from text2ifc_agent.prompt_registry import load_prompt_registry
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.scene_grounding import generate_scene_repair_intent
from tests.ifc_repair.test_scene_context import fixture_scene
from tests.ifc_repair.test_scene_grounding import QueueProvider, final_response
from tests.ifc_repair.test_spatial_grounding import body


def run(tmp_path, responses, request="在这面墙上补窗，宽900高1800毫米，窗台300毫米。"):
    provider = QueueProvider(responses)
    result = generate_scene_repair_intent(
        provider=provider, request_id="localization-family", repair_request=request,
        registry=create_default_registry(), output_dir=tmp_path, scene=fixture_scene(),
        max_rounds=len(responses),
    )
    return result, provider


def test_new_prompt_preserves_registered_v02_bytes_and_changes_version():
    registry = load_prompt_registry()
    assert registry["ifc-scene-grounding.v0.2"]["sha256"] == (
        "sha256:cc0c2c9000a9ad249b373e85fd995c683472f676e5a84dc60eb4ef7260a5da46"
    )
    assert "ifc-scene-grounding.v0.3" in registry


def position_question(*, kind="user_design", path="/position/center_offset_mm"):
    intent = body()
    intent["operations"][0]["target_query"]["global_id"] = "wall"
    return {"kind": "clarification", "intent": intent, "reason": "missing_user_fact",
            "question": "新窗的中心要距这面墙的南端多少毫米？", "candidate_ids": [],
            "missing_facts": [{"operation_id": "offline-repair", "path": path,
                               "source": kind, "description": "用户未指定新窗的位置，也未指定参照。"}]}


def test_genuine_new_location_is_a_user_choice_not_an_internal_offset(tmp_path):
    result, _ = run(tmp_path, [{"kind": "query", "query": {"ids": ["wall"]}}, position_question()])
    assert result["valid"] and result["classification"] == "clarification_required"
    assert result["scene_question"] == position_question()["question"]


@pytest.mark.parametrize("change", [{"source": "public_ifc"}, {"path": "/invented"},
                                   {"operation_id": "other-operation"}])
def test_missing_fact_must_be_an_actual_user_parameter(tmp_path, change):
    response = position_question()
    response["missing_facts"][0].update(change)
    result, _ = run(tmp_path, [{"kind": "query", "query": {"ids": ["wall"]}}, response])
    assert not result["valid"] and "scene_question" not in result


def test_derived_position_still_cannot_be_sent_back_as_an_internal_question(tmp_path):
    response = position_question()
    response["question"] = "请提供程序所需的局部偏移。"
    result, _ = run(tmp_path, [{"kind": "query", "query": {"ids": ["wall"]}}, response])
    assert not result["valid"] and "scene_question" not in result


def test_internal_coordinate_reference_cannot_be_relabelled_user_design(tmp_path):
    response = position_question(path="/position/reference")
    response["intent"]["operations"][0]["parameters"]["position"] = {"center_offset_mm": 5000}
    response["question"] = "Which coordinate reference should the program use?"
    result, _ = run(tmp_path, [{"kind": "query", "query": {"ids": ["wall"]}}, response])
    assert not result["valid"] and "scene_question" not in result


def test_internal_reference_is_rejected_at_clarification_seam():
    from types import SimpleNamespace
    from text2ifc_ifc_repair.scene_grounding import _validate_clarification
    from text2ifc_ifc_repair.spatial_grounding import GroundingError
    response = position_question(path="/position/reference")
    operation = response["intent"]["operations"][0]
    operation["parameters"]["position"] = {"center_offset_mm": 5000}
    response["question"] = "Which coordinate reference should the program use?"
    scene = fixture_scene()
    scene.query({"ids": ["wall"]})
    intent = SimpleNamespace(operations=[SimpleNamespace(operation_id="offline-repair",
        to_dict=lambda: operation, target_query=SimpleNamespace(global_id="wall"))])
    with pytest.raises(GroundingError, match="SCENE_CLARIFICATION_NOT_A_USER_FACT"):
        _validate_clarification(response, intent, scene, create_default_registry())


def test_response_query_contract_matches_runtime_grammar():
    from text2ifc_ifc_repair.scene_grounding import load_scene_response_schema
    from text2ifc_ifc_repair.scene_query import query_properties
    actual = load_scene_response_schema()["oneOf"][0]["properties"]["query"]["properties"]
    assert all(actual[key] == value for key, value in query_properties().items())


def test_frame_ambiguity_can_be_asked_without_inventing_a_missing_dimension(tmp_path):
    response = position_question()
    response.pop("missing_facts")
    response.update(reason="ambiguous_frame", question="你说的左侧，是从室内朝外看，还是从室外朝内看？",
                    frame_issue={"phrase": "左侧", "alternatives": ["从室内朝外看", "从室外朝内看"]})
    result, _ = run(tmp_path, [{"kind": "query", "query": {"ids": ["wall"]}}, response],
                    request="在这面墙的左侧补一扇窗。")
    assert result["valid"] and result["classification"] == "clarification_required"


def test_rank_certificate_avoids_serving_every_member(tmp_path):
    response = final_response()
    result, provider = run(tmp_path, [
        {"kind": "query", "query": {"ids": ["wall"], "detail": "summary"}},
        {"kind": "query", "query": {"ifc_classes": ["IfcWindow"], "host_id": "wall",
            "detail": "summary", "select": {"order_by": "world_y", "descending": True, "ranks": [2, 3]}}},
        response,
    ])
    assert result["valid"], result
    assert result["intent"].operations[0].parameters["position"]["center_offset_mm"] == 5000
    evidence = json.loads((tmp_path / "grounding-evidence.json").read_text(encoding="utf-8"))
    assert "window-0" not in evidence["offered_ids"] and "window-3" not in evidence["offered_ids"]
    assert "window-1" in provider.calls[-1]["prompt"]


def test_repeated_query_yields_useful_feedback_not_duplicate_context(tmp_path):
    query = {"kind": "query", "query": {"ids": ["wall"], "detail": "summary"}}
    result, provider = run(tmp_path, [query, deepcopy(query), deepcopy(query)])
    assert not result["valid"]
    assert "SCENE_QUERY_NO_NEW_EVIDENCE" in provider.calls[-1]["prompt"]
    assert result["failure_summary"]["last_issue_codes"]
