import pytest
from scripts.ifc2text.rerun_material_v11 import ContinuationBudget
from text2ifc_ifc2text.goal_budget import GoalStopped

def prior():
    return {'limits': {'tokens': 2000000}, 'historical': {'writing': 21, 'tokens': 1400238},
            'halted': False, 'attempts': [
                {'stage': 'writing', 'status': 'completed', 'charged_tokens': 1741},
                {'stage': 'reconstruction', 'status': 'completed', 'charged_tokens': 87752}]}

def test_continuation_preserves_all_usage_allows_only_three_calls_and_no_writing(tmp_path):
    budget = ContinuationBudget(tmp_path, prior(), inherited_reconstruction=15)
    assert budget.snapshot()['calls'] == {'writing': 22, 'reconstruction': 15}
    assert budget.snapshot()['tokens_used_or_reserved'] == 1489731
    with pytest.raises(GoalStopped):
        budget.reserve('writing', 100)
    for _ in range(3):
        token = budget.reserve('reconstruction', 100)
        budget.settle(token, usage={'input_tokens': 30, 'output_tokens': 20})
    with pytest.raises(GoalStopped):
        budget.reserve('reconstruction', 100)
    assert budget.snapshot()['tokens_used_or_reserved'] == 1489881

@pytest.mark.parametrize('state', ['halted', 'reserved'])
def test_continuation_cannot_reset_halted_or_unsettled_usage(tmp_path, state):
    old = prior()
    if state == 'halted': old['halted'] = True
    else: old['attempts'][0]['status'] = 'reserved'
    with pytest.raises(GoalStopped):
        ContinuationBudget(tmp_path, old, inherited_reconstruction=15)
