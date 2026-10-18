import json

import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.scene_grounding import generate_scene_repair_intent
from text2ifc_ifc_repair.operations import create_default_registry
from tests.ifc_repair.test_scene_context import fixture_scene
from tests.ifc_repair.test_spatial_grounding import body, binding


class QueueProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_candidate(self, **kwargs):
        self.calls.append(kwargs)
        value = self.responses.pop(0)
        return ProviderOutput(text=value if isinstance(value, str) else json.dumps(value),
                              metadata={"provider": "fixture", "model": "offline-scene-fixture",
                                        "usage": {"input_tokens": 12, "output_tokens": 8}})


def final_response():
    return {"kind": "intent", "intent": body(), "bindings": [binding(kind="between_ranked",
                    ifc_class="IfcWindow", order_by="world_y", descending=True, ranks=[2, 3],
                    reference_ids=["window-1", "window-2"])]}


def run(tmp_path, provider, **kwargs):
    scene = kwargs.pop('scene', fixture_scene())
    return generate_scene_repair_intent(provider=provider, request_id="request-fixture",
                repair_request="底层西侧长墙上，从北到南第二与第三扇窗中间补一扇宽900高1800的窗，窗台300毫米。",
                registry=create_default_registry(), output_dir=tmp_path, scene=scene, **kwargs)


def test_request_scene_queries_and_all_raw_calls_are_retained(tmp_path):
    provider = QueueProvider([
        {"kind": "query", "query": {"ids": ["wall"]}},
        {"kind": "query", "query": {"ifc_classes": ["IfcWindow"], "host_id": "wall", "order_by": "world_y", "descending": True}},
        final_response()])
    result = run(tmp_path, provider)
    assert result["valid"] and result["classification"] == "repair_intent"
    assert result["intent"].operations[0].parameters["position"]["center_offset_mm"] == 5000
    assert "Ground East" in provider.calls[0]["prompt"] and "第二与第三" in provider.calls[0]["prompt"]
    assert "window-2" in provider.calls[2]["prompt"]
    assert len(list(tmp_path.glob("round-*/attempt-*.json"))) == 3
    assert (tmp_path / "grounding-evidence.json").is_file()
    assert (tmp_path / "scene-queries.json").is_file()


@pytest.mark.parametrize("response", ['{"kind":', {"kind": "query", "query": {"path": "../G.ifc"}}, final_response()])
def test_malformed_query_and_unoffered_id_stop_without_intent(tmp_path, response):
    result = run(tmp_path, QueueProvider([response, response]), max_rounds=2)
    assert not result["valid"] and not (tmp_path / "repair-intent.json").exists()
    assert result["error_code"] == "SCENE_GROUNDING_EXHAUSTED"


def test_query_budget_exhaustion_is_not_a_user_question(tmp_path):
    result = run(tmp_path, QueueProvider([{"kind": "query", "query": {"ids": ["wall"]}}]), max_rounds=1)
    assert not result["valid"] and result["error_code"] == "SCENE_GROUNDING_EXHAUSTED"
    assert "scene_question" not in result


def test_genuine_missing_fact_may_pause_after_public_scene_seen(tmp_path):
    partial = body()
    partial["operations"][0]["target_query"]["global_id"] = "wall"
    partial["operations"][0]["parameters"]["opening"].pop("width_mm")
    response = {"kind": "clarification", "intent": partial, "reason": "missing_user_fact",
                "question": "要补的窗宽度是多少毫米？", "candidate_ids": []}
    result = run(tmp_path, QueueProvider([{"kind": "query", "query": {"ids": ["wall"]}}, response]))
    assert result["valid"] and result["classification"] == "clarification_required"
    assert result["scene_question"] == response["question"]


def test_unresolved_local_position_is_system_failure_not_human_question(tmp_path):
    final={'kind':'intent','intent':body(), 'bindings':[{'operation_id':'offline-repair','target_id':'wall'}]}
    provider=QueueProvider([{'kind':'query','query':{'ids':['wall']}},final,final])
    result=run(tmp_path,provider,max_rounds=3)
    assert not result['valid'] and 'scene_question' not in result
    assert 'SCENE_POSITION_NOT_GROUNDED' in provider.calls[-1]['prompt']
    assert not (tmp_path/'repair-intent.json').exists()


def test_actual_ambiguity_retains_candidates_without_choosing_first(tmp_path):
    from copy import deepcopy
    from text2ifc_ifc_repair.scene_context import PublicScene
    first=fixture_scene().records[0]
    first['name']='west-long-wall'
    other=deepcopy(first)
    other.update(id='other-wall',name='east-long-wall')
    other['center_world_mm'][0]=10100
    other['bounds_world_mm']['x']=[10000,10200]
    scene=PublicScene([first,other],fixture_scene().storeys,project_unit_scale=.001)
    partial=body()
    partial['operations'][0]['target_query']['names']=['west-long-wall','east-long-wall']
    provider=QueueProvider([{'kind':'query','query':{'ifc_classes':['IfcWall']}},
        {'kind':'clarification','intent':partial,'reason':'ambiguous_target',
         'question':'要补窗的是西侧长墙，还是东侧长墙？',
         'candidate_ids':['wall','other-wall']}])
    result=run(tmp_path,provider,scene=scene)
    assert result['valid'] and result['scene_question']
    assert result['classification']=='clarification_required'


def test_pure_unsupported_request_is_terminal_without_scene_queries(tmp_path):
    partial=body()
    partial['operations']=[]
    partial['unsupported_requests']=[{'unsupported_id':'outside','kind':'unregistered_action',
        'operation_id':None,'capability_id':'unregistered_operation','source':partial['provenance'][0]}]
    provider=QueueProvider([{'kind':'intent','intent':partial,'bindings':[]}])
    result=run(tmp_path,provider)
    assert result['valid'] and result['classification']=='unsupported'
    assert result['scene_grounding_version']


def test_human_cannot_be_asked_to_supply_an_internal_identity(tmp_path):
    partial=body()
    partial['operations'][0]['target_query']['global_id']='wall'
    partial['operations'][0]['parameters']['opening'].pop('width_mm')
    bad={'kind':'clarification','intent':partial,'reason':'missing_user_fact',
         'question':'请提供要补窗那面墙的GUID。','candidate_ids':[]}
    result=run(tmp_path,QueueProvider([{'kind':'query','query':{'ids':['wall']}},bad]),max_rounds=2)
    assert not result['valid'] and 'scene_question' not in result
