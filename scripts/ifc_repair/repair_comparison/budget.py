"""Explicit budgets and the versioned policy for new real repair experiments.

Historical frozen budgets remain unchanged. Offline fixtures may still supply
their own limits through validate_budget; they do not establish policy compliance.
"""
from __future__ import annotations

from copy import deepcopy
import math


LEGACY_BUDGET_POLICY_VERSION = 'repair-comparison-fixed-budget-policy/0.1'
FIXED_BUDGET_POLICY_VERSION = 'repair-comparison-fixed-budget-policy/0.2'
_LEGACY_BUDGET_PROFILES = {
    'S1': {'tokens': 1_500_000, 'calls': 48, 'active_seconds': 1800,
           'tool_seconds': 120, 'extensions': []},
    'S2': {'tokens': 2_000_000, 'calls': 64, 'active_seconds': 2400,
           'tool_seconds': 120, 'extensions': []},
    'S3': {'tokens': 2_500_000, 'calls': 80, 'active_seconds': 3000,
           'tool_seconds': 120, 'extensions': []},
}
_FIXED_BUDGET_PROFILES = {level: {**deepcopy(profile), 'tokens': profile['tokens']//2}
                          for level, profile in _LEGACY_BUDGET_PROFILES.items()}
_BUDGET_POLICIES = {LEGACY_BUDGET_POLICY_VERSION: _LEGACY_BUDGET_PROFILES,
                    FIXED_BUDGET_POLICY_VERSION: _FIXED_BUDGET_PROFILES}


def fixed_budget_profile(level: str, *, policy_version: str = FIXED_BUDGET_POLICY_VERSION) -> dict:
    """Return independent limits for one policy level, shared across case arms."""
    if policy_version not in _BUDGET_POLICIES:
        raise ValueError('UNKNOWN_FIXED_BUDGET_POLICY_VERSION')
    profiles = _BUDGET_POLICIES[policy_version]
    if not isinstance(level, str) or level not in profiles:
        raise ValueError('UNKNOWN_FIXED_BUDGET_LEVEL')
    return deepcopy(profiles[level])


def budget_level_for_primary_targets(primary_target_count: int) -> str:
    """Select by major requested repair targets, never IFC relationship count.

    The task author supplies this count; this helper does not infer it from IFC
    entities or mutation operations. One target is S1, two S2, three or more S3.
    """
    if type(primary_target_count) is not int or primary_target_count < 1:
        raise ValueError('INVALID_PRIMARY_TARGET_COUNT')
    return 'S1' if primary_target_count == 1 else 'S2' if primary_target_count == 2 else 'S3'


def validate_fixed_budget_policy(profile: dict, *, primary_target_count: int,
                                 policy_version: str = FIXED_BUDGET_POLICY_VERSION) -> None:
    """Fail closed for new real experiments; generic/offline limits use validate_budget."""
    expected = fixed_budget_profile(budget_level_for_primary_targets(primary_target_count),
                                    policy_version=policy_version)
    if not isinstance(profile, dict) or not isinstance(profile.get('extensions'), list):
        raise ValueError('INVALID_BUDGET_FIELDS')
    if profile['extensions']:
        raise ValueError('FIXED_BUDGET_POLICY_MISMATCH')
    validate_budget(profile)
    if profile != expected:
        raise ValueError('FIXED_BUDGET_POLICY_MISMATCH')


def positive(value, *, integer=False):
    return type(value) in ((int,) if integer else (int, float)) and math.isfinite(value) and value > 0


def validate_budget(profile: dict) -> None:
    if set(profile) != {'tokens', 'calls', 'active_seconds', 'tool_seconds', 'extensions'}:
        raise ValueError('INVALID_BUDGET_FIELDS')
    if not all(positive(profile[k], integer=k in {'tokens', 'calls'}) for k in ('tokens', 'calls', 'active_seconds', 'tool_seconds')):
        raise ValueError('INVALID_BUDGET_LIMIT')
    ids = set()
    for rule in profile['extensions']:
        if set(rule) != {'id', 'min_calls', 'tokens', 'active_seconds'} or not isinstance(rule['id'], str) or not rule['id'] or rule['id'] in ids:
            raise ValueError('INVALID_EXTENSION_RULE')
        if not all(positive(rule[k], integer=k != 'active_seconds') for k in ('min_calls', 'tokens', 'active_seconds')):
            raise ValueError('INVALID_EXTENSION_LIMIT')
        ids.add(rule['id'])


def normalize_usage(raw, *, protocol='chat', complete=True):
    """Normalize returned counts using the wire protocol, retaining unknowns.

    Chat prompt_tokens includes cache hits. Messages input_tokens excludes
    cache reads/creation; its stream-start output count is not final usage.
    """
    if not isinstance(raw, dict) or not complete:
        return None
    input_tokens = raw.get('input_tokens', raw.get('prompt_tokens'))
    output_tokens = raw.get('output_tokens', raw.get('completion_tokens'))
    if any(type(value) is not int or value < 0 for value in (input_tokens, output_tokens)):
        return None
    if protocol == 'messages':
        cached = [raw.get(key, 0) for key in ('cache_read_input_tokens', 'cache_creation_input_tokens')]
        if any(type(value) is not int or value < 0 for value in cached):
            return None
        input_tokens += sum(cached)
    return {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'total_tokens': input_tokens + output_tokens}


def usage_summary(calls, limit):
    known = [call for call in calls if call['normalized_usage'] is not None]
    total = sum(call['normalized_usage']['total_tokens'] for call in known)
    unknown = len(calls) - len(known)
    reserved = sum(call['reservation'] for call in calls if call['normalized_usage'] is None)
    return {'total_tokens': total if not unknown else None, 'known_total_tokens': total,
            'reserved_tokens': reserved, 'unknown_calls': unknown, 'calls': len(calls),
            'coverage': 'complete' if not unknown else 'partial' if known else 'unavailable',
            'token_overrun': max(0, total - limit),
            'accounting': 'actual returned usage; unresolved calls retain their reservation'}
