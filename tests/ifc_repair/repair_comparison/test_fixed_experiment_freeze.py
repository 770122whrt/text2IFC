"""New batch policy does not replace historical limits or assume all caps spent."""
from copy import deepcopy

import pytest

from scripts.ifc_repair.repair_comparison import formal_workflow as formal, demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile, FIXED_BUDGET_POLICY_VERSION
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison.dsh_search import search_configuration
from tests.ifc_repair.repair_comparison.test_later_ten_execution import draft


def authored_cases(tmp_path):
    base = draft(tmp_path)
    for case in base.iterdir():
        path = case/'private/task.json'
        task = read_json(path)
        task['damage_scale'] = 'S1'
        task['metrics'] = {'status':'deferred','formal_scoring_frozen':False}
        write_json(path, task)
    return base


def test_fixed_freeze_uses_policy_and_separate_batch_limit(tmp_path):
    base = authored_cases(tmp_path)
    path = tmp_path/'plan.json'
    plan = formal.freeze_execution(base, path, case_ids=['formal-011','formal-015'],
        total_token_limit=2_000_000, d_web_search=search_configuration({}))
    assert plan['schema_version'] == 'repair-comparison-execution-plan/0.2'
    assert plan['budget_policy_version'] == FIXED_BUDGET_POLICY_VERSION
    assert plan['configuration']['b_validation_corrections'] == 2
    assert all(p == fixed_budget_profile('S1') for p in plan['configuration']['budgets'].values())
    assert plan['maximum_task_caps_tokens'] == 12_000_000
    assert plan['authorization']['total_api_token_limit'] == 2_000_000
    assert plan['reserved_for_exceptions_tokens'] == 0
    assert formal.verify_plan(path) == plan
    old = deepcopy(plan)
    old['schema_version'] = 'repair-comparison-execution-plan/0.1'
    old.pop('budget_policy_version')
    old['configuration'].pop('b_validation_corrections')
    for name in old['configuration']['budgets']:
        old['configuration']['budgets'][name] = {**fixed_budget_profile('S1'), 'tokens':450000}
    assert formal.verify_execution_plan(path, plan=old) == old


def test_fixed_freeze_refuses_changed_task_policy_before_writing(tmp_path):
    base = authored_cases(tmp_path)
    before = (base/'formal-011/private/task.json').read_bytes()
    budgets = {name: {**fixed_budget_profile('S1'), 'tokens':450000}
               for name in ['formal-011','formal-015']}
    with pytest.raises(ValueError, match='FIXED_BUDGET_POLICY'):
        formal.freeze_execution(base, tmp_path/'plan.json', case_ids=list(budgets),
            budgets=budgets, total_token_limit=20_000_000)
    assert (base/'formal-011/private/task.json').read_bytes() == before


def test_d_search_settings_are_frozen_and_old_configs_stay_unchanged(tmp_path):
    budgets={'test':fixed_budget_profile('S1')}
    plain=carrier.batch_configuration(cases_root=tmp_path,case_ids=['test'],budgets=budgets,
        stage=carrier.FORMAL_STAGE)
    assert 'd_web_search' not in plain
    settings=search_configuration({})
    searched=carrier.batch_configuration(cases_root=tmp_path,case_ids=['test'],budgets=budgets,
        stage=carrier.FORMAL_STAGE,d_web_search=settings)
    assert searched['d_web_search'] == settings
    settings['max_uses']=1
    assert searched['d_web_search']['max_uses']==5


@pytest.mark.parametrize('prior_metrics',['deferred','frozen'])
def test_new_execution_plan_keeps_reviewed_card_bytes_unchanged(tmp_path,prior_metrics):
    base=authored_cases(tmp_path)
    for name in ['formal-011','formal-015']:
        card_path=base/name/'private/task.json'
        card=read_json(card_path)
        card['metrics']={'status':prior_metrics,'formal_scoring_frozen':prior_metrics=='frozen'}
        card['budget']={'status':'frozen','limits':{**fixed_budget_profile('S1'),'tokens':450000}}
        write_json(card_path,card)
    originals={name:(base/name/'private/task.json').read_bytes() for name in ['formal-011','formal-015']}
    path=tmp_path/'new-batch/plan.json'
    plan=formal.freeze_execution(base,path,case_ids=list(originals),total_token_limit=20_000_000)
    assert formal.verify_plan(path)==plan
    assert all((base/name/'private/task.json').read_bytes()==data for name,data in originals.items())
    changed=deepcopy(plan)
    changed['metrics']['status']='frozen'
    with pytest.raises(ValueError,match='FROZEN_REVIEW_OR_METRICS_CHANGED'):
        formal.verify_execution_plan(path,plan=changed)
