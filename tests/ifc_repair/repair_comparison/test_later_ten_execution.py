"""Execution-only contracts; no repair scores or real Provider calls."""
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison import formal_workflow as formal
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json


def draft(tmp_path):
    base = tmp_path / 'cases'
    for number in (11, 15):
        case = base / f'formal-{number:03d}'
        (case / 'public').mkdir(parents=True)
        (case / 'private/mutation').mkdir(parents=True)
        (case / 'public/model.ifc').write_text(f'public synthetic D {number}', encoding='utf8')
        (case / 'public/request.txt').write_text('Restore the reviewed instance property.', encoding='utf8')
        (case / 'private/reference.ifc').write_text(f'private synthetic G {number}', encoding='utf8')
        (case / 'private/mutation/damaged.ifc').write_bytes((case / 'public/model.ifc').read_bytes())
        write_json(case / 'private/checks.json', {'checks': {'prepared': True}})
        write_json(case / 'private/answer-card.json', {'status': 'accepted_by_delegation', 'required_user_facts': [], 'facts': {}})
        write_json(case / 'private/task.json', {
            'case_id': case.name, 'source_sha256': sha256(case / 'private/reference.ifc'),
            'damaged_sha256': sha256(case / 'public/model.ifc'), 'source': {'asset_id': str(number)},
            'request': 'Restore the reviewed instance property.',
            'damage_scale': 'S1',
            'review': {'status': 'accepted_by_delegation', 'kind': 'delegated_technical',
                       'human_viewed': False, 'technical_review_passed': True,
                       'authorization': {'user_quote': 'Run the ten cases in four arms.'}},
            'clarification': {'required_user_facts': [], 'facts': {}},
        })
    return base


def limits(base):
    from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
    return {p.name: fixed_budget_profile('S1') for p in base.iterdir()}


def test_execution_freeze_supports_structure_and_properties_without_scores(tmp_path):
    base = draft(tmp_path)
    path = tmp_path / 'plan.json'
    result = formal.freeze_execution(base, path, case_ids=['formal-011', 'formal-015'], budgets=limits(base),
                                     total_token_limit=20000000)
    assert result['metrics']['status'] == 'deferred'
    assert len(result['configuration']['order']) == 8
    assert formal.verify_plan(path) == result
    with pytest.raises(ValueError, match='PLAN_EXISTS'):
        formal.freeze_execution(base, path, case_ids=['formal-011', 'formal-015'], budgets=limits(base), total_token_limit=20000000)
    (base / 'formal-015/private/answer-card.json').write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='FROZEN_TASK'):
        formal.verify_plan(path)


def test_execution_freeze_rejects_review_or_total_budget_violation(tmp_path):
    base = draft(tmp_path)
    with pytest.raises(ValueError, match='TOTAL_TOKEN'):
        formal.freeze_execution(base, tmp_path / 'plan.json', case_ids=['formal-011', 'formal-015'],
                                budgets=limits(base), total_token_limit=1000)
    task_path = base / 'formal-011/private/task.json'
    task = read_json(task_path); task['review']['status'] = 'pending_human_review'; write_json(task_path, task)
    with pytest.raises(ValueError, match='REVIEW'):
        formal.freeze_execution(base, tmp_path / 'plan.json', case_ids=['formal-011', 'formal-015'], budgets=limits(base), total_token_limit=20000000)


def test_card_answers_only_asked_axes_with_authored_answer_text():
    card = {'status': 'accepted_by_delegation', 'required_user_facts': ['x', 'y'], 'facts': {
        'x': {'question_keywords': ['X坐标'], 'answer_text': '柱中心X=-12.549米。'},
        'y': {'question_keywords': ['Y坐标'], 'answer_text': '柱中心Y=5.24米。'},
    }}
    result = formal.card_answer({'text': '柱的X坐标是多少？'}, card)
    assert result['text'] == '柱中心X=-12.549米。'
    assert result['answered_fact_ids'] == ['x']
    assert formal.card_answer({'text': '梁的材料是什么？'}, card) is None


def test_property_runtime_is_configuration_bound(tmp_path):
    model = tmp_path / 'model'; model.mkdir()
    (model / 'config.json').write_text('{}', encoding='utf8')
    (model / 'modules.json').write_text('[]', encoding='utf8')
    b = {'image': 'text2ifc/repair-tools:py312-ifc085-property-v1', 'property_model_directory': str(model)}
    profile = {'tokens': 450000, 'calls': 48, 'active_seconds': 2400, 'tool_seconds': 120, 'extensions': []}
    config = carrier.batch_configuration(cases_root=tmp_path, case_ids=['formal-011'], budgets={'formal-011': profile},
                                         stage=carrier.FORMAL_STAGE, b=b)
    assert config['b'] == b
    bad = deepcopy(config); bad['b']['image'] = 'unreviewed-image'
    with pytest.raises(ValueError, match='PROPERTY_RUNTIME'):
        carrier.batch_configuration(cases_root=tmp_path, case_ids=['formal-011'], budgets=bad['budgets'], stage=carrier.FORMAL_STAGE, b=bad['b'])


def test_usage_ticks_do_not_wake_operator_but_questions_do():
    from scripts.ifc_repair.repair_comparison import batch_operator as operator
    first={'terminal':0,'tasks':40,'active':{'run_id':'formal-011-A','status':'running'},
           'question_id':None,'known_tokens':100,'reserved_tokens':0,'unknown_calls':0}
    second={**first,'known_tokens':900,'reserved_tokens':300}
    assert operator.change_key(first)==operator.change_key(second)
    assert operator.change_key(first)!=operator.change_key({**second,'question_id':'question-1'})


def test_grouped_d_answers_remain_per_question_and_do_not_inject_whole_card():
    from scripts.ifc_repair.repair_comparison import batch_operator as operator
    card={'status':'accepted_by_delegation','required_user_facts':['x','y','unused'],'facts':{
        'x':{'question_keywords':['X坐标'],'answer_text':'X=-12.549米'},
        'y':{'question_keywords':['Y坐标'],'answer_text':'Y=5.24米'},
        'unused':{'question_keywords':['材料'],'answer_text':'不可自动注入的材料事实'},
    }}
    state={'arm':'D','question':{'question_id':'q','text':'请提供柱的X坐标和Y坐标。',
            'binding':{'native_packet':{'questions':[{'id':'x','question':'柱的X坐标？'},
                                                    {'id':'y','question':'柱的Y坐标？'}]}}}}
    result=operator.card_proposal(state,card)
    assert result['answers']==[{'id':'x','selected':[],'custom':'X=-12.549米'},
                               {'id':'y','selected':[],'custom':'Y=5.24米'}]
    assert '材料' not in result['text']


def test_repeated_b_failures_alert_but_normal_budget_stops_do_not():
    from scripts.ifc_repair.repair_comparison import batch_operator as operator
    failed={'arm':'B','status':'no_output','native':{'result':{'status':'not_publishable'}},'detail':None}
    states=[{**failed,'run_id':case+'-B'} for case in ('formal-011','formal-012')]
    alert=operator.common_candidates(states)
    assert list(alert.values())==[['formal-011-B','formal-012-B']]
    assert not operator.common_candidates(states,list(alert))
    assert not operator.failure_signature({**states[0],'status':'budget_exhausted'})
    assert not operator.failure_signature({**states[0],'arm':'A'})


def test_unknown_usage_and_rechecks_share_total_budget(tmp_path,monkeypatch):
    from scripts.ifc_repair.repair_comparison import batch_operator as operator
    state={'usage':{'known_total_tokens':100,'reserved_tokens':450000,'unknown_calls':1}}
    other=tmp_path/'recheck';other.mkdir();(tmp_path/'operator').mkdir()
    write_json(tmp_path/'operator/additional-attempts.json',{'roots':[str(other)]})
    monkeypatch.setattr(carrier,'status',lambda root:[state])
    result=operator.accounted_usage(tmp_path,[state])
    assert result=={'known_tokens':200,'reserved_tokens':900000,'unknown_calls':2}
    assert operator.budget_allows_next(result,450000,1350200)
    assert not operator.budget_allows_next(result,450000,1350199)


def test_execution_plan_cannot_accidentally_run_legacy_scores(tmp_path,monkeypatch):
    monkeypatch.setattr(formal,'experiment_plan',lambda root:{'schema_version':formal.EXECUTION_SCHEMA})
    with pytest.raises(ValueError,match='METRICS_DEFERRED'):
        formal.evaluate(tmp_path)


def test_execution_admission_refuses_missing_safety_coverage(tmp_path,monkeypatch):
    from scripts.ifc_repair.repair_comparison import formal_admission as admission
    monkeypatch.setattr(formal,'verify_execution_plan',lambda path:{'configuration':{}})
    monkeypatch.setattr(carrier,'bindings',lambda config:{})
    with pytest.raises(ValueError,match='MISSING_EXECUTION_CONTRACTS'):
        admission.build_execution_admission(tmp_path/'plan.json',suite_receipts=[],native_report=tmp_path/'native.json')
