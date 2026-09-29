"""Explicit offline budgets; no prices, live quotas, or invented default limits."""
from __future__ import annotations

import math


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


def normalize_usage(raw):
    """Only input + output are additive; cached/reasoning may be subsets."""
    if not isinstance(raw, dict):
        return None
    input_tokens = raw.get('input_tokens', raw.get('prompt_tokens'))
    output_tokens = raw.get('output_tokens', raw.get('completion_tokens'))
    if any(type(value) is not int or value < 0 for value in (input_tokens, output_tokens)):
        return None
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
