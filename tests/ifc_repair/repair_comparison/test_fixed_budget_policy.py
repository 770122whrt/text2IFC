"""The fixed policy governs new real experiments, not historical or offline budgets."""
import pytest

from scripts.ifc_repair.repair_comparison import budget


@pytest.mark.parametrize('level,tokens,calls,seconds', [
    ('S1', 750_000, 48, 1800),
    ('S2', 1_000_000, 64, 2400),
    ('S3', 1_250_000, 80, 3000),
])
def test_fixed_profiles(level, tokens, calls, seconds):
    profile = budget.fixed_budget_profile(level)
    assert profile == {'tokens': tokens, 'calls': calls, 'active_seconds': seconds,
                       'tool_seconds': 120, 'extensions': []}
    assert budget.FIXED_BUDGET_POLICY_VERSION == 'repair-comparison-fixed-budget-policy/0.2'


@pytest.mark.parametrize('count,level', [(1, 'S1'), (2, 'S2'), (3, 'S3'), (4, 'S3'), (100, 'S3')])
def test_primary_target_count_selects_level(count, level):
    assert budget.budget_level_for_primary_targets(count) == level
    budget.validate_fixed_budget_policy(budget.fixed_budget_profile(level), primary_target_count=count)


def test_profile_copy_is_isolated():
    first = budget.fixed_budget_profile('S1')
    first['tokens'] = 1
    first['extensions'].append({'id': 'changed'})
    assert budget.fixed_budget_profile('S1')['tokens'] == 750_000
    assert budget.fixed_budget_profile('S1')['extensions'] == []


@pytest.mark.parametrize('level', ['S0', 's1', '', None, 1, []])
def test_unknown_level_rejected(level):
    with pytest.raises(ValueError, match='UNKNOWN_FIXED_BUDGET_LEVEL'):
        budget.fixed_budget_profile(level)


@pytest.mark.parametrize('count', [0, -1, True, False, 1.0, '2', None, [], float('inf')])
def test_invalid_primary_count_rejected(count):
    with pytest.raises(ValueError, match='INVALID_PRIMARY_TARGET_COUNT'):
        budget.budget_level_for_primary_targets(count)


def test_wrong_level_and_unknown_version_rejected():
    with pytest.raises(ValueError, match='FIXED_BUDGET_POLICY_MISMATCH'):
        budget.validate_fixed_budget_policy(budget.fixed_budget_profile('S1'), primary_target_count=2)
    with pytest.raises(ValueError, match='UNKNOWN_FIXED_BUDGET_POLICY_VERSION'):
        budget.validate_fixed_budget_policy(budget.fixed_budget_profile('S1'), primary_target_count=1,
                                           policy_version='future/99')


@pytest.mark.parametrize('field,value', [
    ('tokens', 1), ('tokens', 1_500_000.0), ('calls', True),
    ('active_seconds', 10), ('tool_seconds', 121), ('extensions', None),
    ('extensions', [{'id': 'extra', 'min_calls': 1, 'tokens': 1, 'active_seconds': 1}]),
])
def test_non_policy_limits_rejected(field, value):
    profile = budget.fixed_budget_profile('S1')
    profile[field] = value
    with pytest.raises(ValueError):
        budget.validate_fixed_budget_policy(profile, primary_target_count=1)


@pytest.mark.parametrize('profile', [None, [], {}, {'unknown': 1}])
def test_illegal_profile_rejected(profile):
    with pytest.raises(ValueError):
        budget.validate_fixed_budget_policy(profile, primary_target_count=1)


def test_offline_budget_and_usage_interfaces_are_preserved():
    budget.validate_budget({'tokens': 10, 'calls': 1, 'active_seconds': 1,
                            'tool_seconds': 1, 'extensions': []})
    assert budget.normalize_usage({'prompt_tokens': 2, 'completion_tokens': 3}) == {
        'input_tokens': 2, 'output_tokens': 3, 'total_tokens': 5}
    assert budget.normalize_usage({'input_tokens': 2, 'output_tokens': 3,
                                   'cache_read_input_tokens': 4}, protocol='messages') == {
        'input_tokens': 6, 'output_tokens': 3, 'total_tokens': 9}
    assert budget.normalize_usage({}, complete=False) is None


@pytest.mark.parametrize('level,tokens', [('S1', 1_500_000), ('S2', 2_000_000), ('S3', 2_500_000)])
def test_historical_policy_remains_available_unchanged(level, tokens):
    old = budget.fixed_budget_profile(level, policy_version='repair-comparison-fixed-budget-policy/0.1')
    assert old['tokens'] == tokens
    budget.validate_fixed_budget_policy(old, primary_target_count=int(level[-1]),
                                       policy_version='repair-comparison-fixed-budget-policy/0.1')
