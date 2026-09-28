from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from text2ifc_ifc2text.goal_budget import GoalBudget, BudgetClient, GoalStopped


def test_budget_is_cumulative_across_stages_and_reopens(tmp_path):
    b = GoalBudget(tmp_path, writing_calls=3, reconstruction_calls=2, tokens=1000,
                   historical_writing_calls=1, historical_tokens=100)
    token = b.reserve('writing', 300)
    b.settle(token, usage={'prompt_tokens':20,'completion_tokens':30})
    reopened = GoalBudget(tmp_path)
    assert reopened.snapshot()['tokens_used_or_reserved']==150
    assert reopened.snapshot()['calls']['writing']==2
    token = reopened.reserve('reconstruction', 500)
    reopened.settle(token, usage={'prompt_tokens':100,'completion_tokens':100})
    assert GoalBudget(tmp_path).snapshot()['tokens_used_or_reserved']==350
    token = reopened.reserve('writing',100)
    reopened.settle(token, usage={'prompt_tokens':20,'completion_tokens':20})
    with pytest.raises(GoalStopped):
        reopened.reserve('writing', 1)
    assert GoalBudget(tmp_path).snapshot()['calls']['reconstruction']==1


def test_token_ceiling_and_interrupted_reservation_cannot_be_reset(tmp_path):
    b = GoalBudget(tmp_path, tokens=1000)
    b.reserve('writing', 900)
    with pytest.raises(GoalStopped):
        GoalBudget(tmp_path).reserve('reconstruction', 1)
    with pytest.raises(GoalStopped):
        GoalBudget(tmp_path, tokens=1001)


def test_truncation_stops_all_future_transport_and_saves_usage(tmp_path):
    count = []
    def create(**request):
        count.append(request)
        return {'id':'fake', 'model':'fixture', 'choices':[{'finish_reason':'length','message':{'content':'{'}}],
                'usage':{'prompt_tokens':10,'completion_tokens':20}}
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    budget = GoalBudget(tmp_path, tokens=1000)
    wrapped = BudgetClient(client, budget, 'writing')
    wrapped.chat.completions.create(messages=[{'content':'test'}],max_tokens=100)
    assert budget.snapshot()['halted']
    with pytest.raises(GoalStopped):
        wrapped.chat.completions.create(messages=[{'content':'test'}],max_tokens=100)
    assert len(count)==1
    assert budget.snapshot()['tokens_used_or_reserved']==30


def test_transport_failure_preserves_reservation_and_halts(tmp_path):
    def create(**request):
        raise RuntimeError('secret-do-not-log')
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    b = GoalBudget(tmp_path, tokens=1000)
    wrapped = BudgetClient(client,b,'reconstruction')
    with pytest.raises(RuntimeError):
        wrapped.chat.completions.create(messages=[{'content':'x'}],max_tokens=100)
    state = b.snapshot()
    assert state['halted'] and state['tokens_used_or_reserved']>=100
    assert 'secret-do-not-log' not in json.dumps(state)


def test_budget_batch_precheck_does_not_drop_batches(tmp_path):
    b = GoalBudget(tmp_path, writing_calls=2, historical_writing_calls=1)
    with pytest.raises(GoalStopped):
        b.check_capacity('writing', calls=2)
    assert b.snapshot()['calls']['writing']==1
