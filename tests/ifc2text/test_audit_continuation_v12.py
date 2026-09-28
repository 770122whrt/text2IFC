import pytest

from scripts.ifc2text.continue_audit_v12 import AdditionalBudget
from text2ifc_ifc2text.goal_budget import GoalStopped


def previous():
    return {'historical': {'writing': 22, 'tokens': 1489731}, 'halted': False,
            'attempts': [{'stage': 'reconstruction', 'status': 'completed', 'charged_tokens': 77621},
                         {'stage': 'reconstruction', 'status': 'completed', 'charged_tokens': 128995}]}


def test_new_authorization_adds_to_consumption_preserving_history(tmp_path):
    budget = AdditionalBudget(tmp_path, previous(), inherited_reconstruction=17)
    assert budget.snapshot()['limits']['tokens'] == 3696347
    assert budget.snapshot()['tokens_used_or_reserved'] == 1696347
    assert budget.snapshot()['calls'] == {'writing': 22, 'reconstruction': 17}
    call = budget.reserve('reconstruction', 200000)
    budget.settle(call, usage={'input_tokens': 9000, 'output_tokens': 1000})
    reopened = AdditionalBudget(tmp_path, previous(), inherited_reconstruction=17)
    assert reopened.snapshot()['tokens_used_or_reserved'] == 1706347
    assert reopened.snapshot()['calls']['reconstruction'] == 18
    with pytest.raises(GoalStopped):
        reopened.reserve('writing', 1990001)


@pytest.mark.parametrize('bad', ['halted', 'reserved'])
def test_cannot_reset_unsettled_or_halted_parent(tmp_path, bad):
    parent = previous()
    if bad == 'halted':
        parent['halted'] = True
    else:
        parent['attempts'][0]['status'] = 'reserved'
    with pytest.raises(GoalStopped):
        AdditionalBudget(tmp_path, parent, inherited_reconstruction=17)


def test_copy_continuation_includes_report_sidecars_and_preserves_existing_bytes(tmp_path):
    from scripts.ifc2text.continue_audit_v12 import copy_report_sidecars
    from text2ifc_agent.run_report import STAGE_SIDECARS
    source, target = tmp_path / 'source', tmp_path / 'target'
    expected = {}
    for _, directory, names in STAGE_SIDECARS:
        if directory == 'audit':
            continue
        for name in names:
            relative = directory + '/' + name
            path = source / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative, encoding='utf-8'); expected[relative] = path.read_bytes()
    (source / 'private-source.ifc').write_text('must not copy')
    hashes = copy_report_sidecars(source, target)
    assert set(hashes) == set(expected)
    assert all((target / name).read_bytes() == data for name, data in expected.items())
    assert not (target / 'private-source.ifc').exists()
    assert copy_report_sidecars(source, target) == hashes
    (target / 'generator/candidate.json').write_text('different')
    with pytest.raises(GoalStopped, match='EXISTING_SIDECAR_DIFFERS'):
        copy_report_sidecars(source, target)
