"""Report-only state/fact rendering; no geometry re-audit or model execution."""
from copy import deepcopy

import pytest

from scripts.ifc_repair.repair_comparison.review_materials import render_formal_review


@pytest.fixture
def review_input():
    task={'case_id':'formal-013','source':{'source_role':'preselected_reference_from_registered_original',
          'task_proposal':{'description':'补窗'}},'request':'在指定墙面补一扇窗，其他部分保持原样。',
          'review':{'status':'pending_human_review','reviewer':None},
          'metrics':{'formal_scoring_frozen':False},'required_product_count':1,
          'damage_profile':{'level':'S1'},'clarification':{'required_user_facts':[],'facts':{}}}
    checks={'targets':[{'source_step_id':1,'target':{'name':'Actual Window:321','class':'IfcWindow'},
                       'opening':{'bounds_world_m':[[1.,2.],[3.,4.],[0.,1.]]},'preserve_opening':False}]}
    return task,checks,[{'name':'Retained Window:654','class':'IfcWindow'}]


def delegated(task):
    task['review']={'status':'accepted_by_delegation','kind':'delegated_technical','reviewer':'Codex',
        'human_viewed':False,'technical_review_passed':True,'reviewed_at':'2026-10-08T01:00:00Z',
        'authorization':{'user_quote':'审题托付给你先 我后续再审 你先做实验吧 如果没问题我就不审题了',
                         'at':'2026-10-07T17:27:34Z'}}


def test_delegated_acceptance_is_not_rendered_as_pending_or_human_viewed(review_input):
    task,checks,refs=review_input;delegated(task)
    text=render_formal_review(task,checks,refs)
    assert 'accepted_by_delegation' in text and 'Codex' in text
    assert 'human_viewed=false' in text
    assert task['review']['authorization']['user_quote'] in text
    assert task['review']['authorization']['at'] in text
    assert '**待人工审阅（pending_human_review）**' not in text
    assert '未调用模型' not in text
    assert '本批拟为信息充分题' not in text


def test_pending_remains_pending_and_does_not_invent_delegation(review_input):
    text=render_formal_review(*review_input)
    assert 'pending_human_review' in text
    assert 'accepted_by_delegation' not in text
    assert '审题托付' not in text
    assert '尚未正式冻结' in text


@pytest.mark.parametrize('frozen',[False,True])
def test_frozen_scoring_state_comes_from_task_metrics(review_input,frozen):
    task,checks,refs=review_input
    task['metrics']={'formal_scoring_frozen':frozen,'policy_version':'formal-policy-test-1'}
    text=render_formal_review(task,checks,refs)
    assert ('评分合同已冻结' in text) is frozen
    assert ('尚未正式冻结' in text) is (not frozen)
    if frozen:
        assert 'formal-policy-test-1' in text
        assert '具体评分与容差待冻结' not in text


@pytest.mark.parametrize('case_id',['formal-013','formal-016','formal-020'])
def test_private_clarification_review_shows_omission_and_preauthored_answer(review_input,case_id):
    task,checks,refs=review_input;delegated(task);task['case_id']=case_id
    answer='第 1 处窗洞下沿距该层标高 850.0 毫米，世界标高 0.850 米。'
    task['clarification']={'required_user_facts':['target_1_sill'],
        'facts':{'target_1_sill':{'target_id':'target-1','field':'opening_bottom_world_m',
             'why_needed':'公开请求省略第1处窗洞下沿高度，现有墙允许不止一个高度。',
             'answer':answer,'basis':'事前编写的用户意图，不在执行时查 G。'}}}
    before=deepcopy(task)
    text=render_formal_review(task,checks,refs)
    assert 'target_1_sill' in text and '公开请求省略第1处窗洞下沿高度' in text
    assert answer in text and '事前认可答复' in text
    assert '只回答实际问到的事实' in text
    assert text.split('## 公开请求',1)[1].split('## 开发侧数值核验',1)[0].strip()==task['request']
    assert task==before


def test_names_coordinates_roles_and_validator_limits_are_preserved(review_input):
    text=render_formal_review(*review_input)
    assert '|Actual Window:321|IfcWindow|' in text
    assert '1.500000, 3.500000' in text and 'Retained Window:654' in text
    assert 'preselected_reference_from_registered_original' in text
    assert '不代表' in text and 'usBIM' in text
    assert 'schema／EXPRESS' in text


def test_missing_fact_card_is_reported_not_replaced_by_an_assumed_answer(review_input):
    task,checks,refs=review_input
    task['clarification']={'required_user_facts':['missing_fact'],'facts':{}}
    text=render_formal_review(task,checks,refs)
    assert 'missing_fact' in text and '答复未记录' in text
    assert '事前认可答复' not in text
