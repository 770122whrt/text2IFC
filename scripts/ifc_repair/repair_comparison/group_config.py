"""Versioned, secret-free group configuration for new scalable batches.

Legacy frozen four-arm configurations keep their original normalization.
Credentials are referenced by environment name and resolved only after admission.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from urllib.parse import urlsplit

from .budget import validate_budget
from .contracts import safe_path

SCALABLE_STAGE = 'repair-comparison-scalable-live'
CONFIGURATION_VERSION = 'repair-comparison-scalable-configuration/0.1'
EXTENDED_CONFIGURATION_VERSION = 'repair-comparison-scalable-configuration/0.2'
GROUPS = {
    'A': ('deepseek', 'direct'), 'B': ('deepseek', 'harness'),
    'C': ('gpt', 'direct'), 'D': ('deepseek', 'dsh'),
    'E': ('gpt', 'harness'), 'F': ('qwen', 'harness'), 'G': ('qwen', 'direct'),
}
QWEN_ENDPOINT = ('https://ms-gmk85rth-100034032793-sw.gw.ap-zhongwei.ti.tencentcs.com/'
                 'ms-gmk85rth/v1/chat/completions')
REQUEST_OPTIONS = frozenset({'temperature', 'top_p', 'enable_thinking', 'thinking',
                             'reasoning_effort', 'store', 'chat_template_kwargs'})


def validate_request_options(options):
    if not isinstance(options, dict) or set(options) - REQUEST_OPTIONS:
        raise ValueError('PROVIDER_REQUEST_OPTIONS_INVALID')
    if 'chat_template_kwargs' in options:
        template = options['chat_template_kwargs']
        if (not isinstance(template, dict) or set(template) != {'enable_thinking'}
                or type(template['enable_thinking']) is not bool):
            raise ValueError('PROVIDER_REQUEST_OPTIONS_INVALID')
    import json
    try:
        encoded = json.dumps(options, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ValueError('PROVIDER_REQUEST_OPTIONS_INVALID') from exc
    if len(encoded) > 2048:
        raise ValueError('PROVIDER_REQUEST_OPTIONS_TOO_LARGE')
    return deepcopy(options)


def default_providers():
    return {
        'deepseek': {'model': 'deepseek-v4-flash', 'label': 'DeepSeek',
            'chat_endpoint': 'https://api.deepseek.com/chat/completions',
            'messages_endpoint': 'https://api.deepseek.com/anthropic/v1/messages',
            'key_env': 'DEEPSEEK_API_KEY', 'max_input_tokens': 65536,
            'max_output_tokens': 65536, 'request_options': {}},
        'gpt': {'model': 'gpt-6-sol', 'label': 'GPT',
            'chat_endpoint': 'http://179.255.159.53:8080/v1/chat/completions',
            'key_env': 'OPENAI_API_KEY', 'max_input_tokens': 65536,
            'max_output_tokens': 65536, 'request_options': {'store': False}},
        'qwen': {'model': 'ms-gmk85rth', 'label': 'Qwen3.5-35B-A3B',
            'chat_endpoint': QWEN_ENDPOINT, 'key_env': None, 'max_input_tokens': 65536,
            'max_output_tokens': 8192, 'request_options': {}},
    }


def _endpoint(value):
    if not isinstance(value, str):
        raise ValueError('PROVIDER_ENDPOINT_REQUIRED')
    parts = urlsplit(value)
    if (parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username
            or parts.password or parts.query or parts.fragment):
        raise ValueError('PROVIDER_ENDPOINT_INVALID')
    return value


def normalize_providers(providers):
    if not isinstance(providers, dict) or set(providers) != {'deepseek', 'gpt', 'qwen'}:
        raise ValueError('THREE_PROVIDER_CONFIGURATIONS_REQUIRED')
    result = deepcopy(providers)
    required = {'model', 'label', 'chat_endpoint', 'key_env', 'max_input_tokens',
                'max_output_tokens', 'request_options'}
    for name, value in result.items():
        expected = required | ({'messages_endpoint'} if name == 'deepseek' else set())
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError('PROVIDER_CONFIGURATION_FIELDS_INVALID')
        for key in ('model', 'label'):
            if (not isinstance(value[key], str) or not value[key].strip()
                    or len(value[key]) > 160 or any(ord(c) < 32 for c in value[key])):
                raise ValueError('PROVIDER_MODEL_OR_LABEL_INVALID')
        _endpoint(value['chat_endpoint'])
        if name == 'deepseek':
            _endpoint(value['messages_endpoint'])
        key = value['key_env']
        if key is not None and (not isinstance(key, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key)):
            raise ValueError('PROVIDER_KEY_REFERENCE_INVALID')
        for key in ('max_input_tokens', 'max_output_tokens'):
            ceiling = 256000 if name == 'qwen' and key == 'max_input_tokens' else 128000
            if type(value[key]) is not int or not 1 <= value[key] <= ceiling:
                raise ValueError('PROVIDER_TOKEN_LIMIT_INVALID')
        value['request_options'] = validate_request_options(value['request_options'])
    return result


def provider(config, arm):
    return config['providers'][GROUPS[arm][0]]


def executor(config, arm):
    if config.get('stage') == SCALABLE_STAGE:
        return GROUPS[arm][1]
    return 'direct' if arm in {'A', 'C'} else 'harness' if arm == 'B' else 'dsh'


def harness_profile(config, arm):
    value = provider(config, arm)
    return {'version': 'isolated-harness-provider/0.1', 'provider': 'openai' if GROUPS[arm][0]=='gpt' else GROUPS[arm][0],
            'label': value['label'], 'model': value['model'],
            'max_input_tokens': value['max_input_tokens'],
            'max_completion_tokens': value['max_output_tokens']}


def scalable_configuration(*, cases_root, case_ids, budgets, providers, case_groups,
                           models=None, scene_grounding=True, b=None,
                           d_web_search=None, b_validation_corrections=2, d_web_access=None):
    from text2ifc_ifc_repair.scene_grounding import SCENE_GROUNDING_VERSION
    providers = normalize_providers(providers)
    ids = list(case_ids)
    if (not ids or len(set(ids)) != len(ids)
            or any(not isinstance(c, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', c) for c in ids)):
        raise ValueError('INVALID_BATCH_CASE_IDS')
    if not isinstance(budgets, dict) or set(budgets) != set(ids):
        raise ValueError('ONE_BUDGET_PER_CASE_REQUIRED')
    for value in budgets.values():
        validate_budget(value)
    if not isinstance(case_groups, dict) or set(case_groups) != set(ids):
        raise ValueError('ONE_GROUP_LIST_PER_CASE_REQUIRED')
    order = []
    for i, case in enumerate(ids):
        arms = case_groups[case]
        if (not isinstance(arms, list) or not arms or len(set(arms)) != len(arms)
                or set(arms) - set(GROUPS)):
            raise ValueError('INVALID_EXPERIMENT_ARMS')
        rotation = i % len(arms)
        selected = arms[rotation:] + arms[:rotation]
        if i == 0 and 'F' in selected:
            selected = ['F'] + [a for a in selected if a != 'F']
        order.extend(case + '-' + arm for arm in selected)
    model_config = {a: providers[GROUPS[a][0]]['model'] for a in GROUPS}
    if models is not None and models != model_config:
        raise ValueError('GROUP_PROVIDER_MODEL_MISMATCH')
    version = (EXTENDED_CONFIGURATION_VERSION if providers['qwen']['max_input_tokens'] > 128000
               else CONFIGURATION_VERSION)
    result = {'configuration_version': version, 'stage': SCALABLE_STAGE,
              'cases_root': str(safe_path(Path(cases_root))), 'case_ids': ids,
              'order': order, 'budgets': deepcopy(budgets), 'models': model_config,
              'providers': providers, 'case_groups': deepcopy(case_groups),
              'scene_grounding_version': SCENE_GROUNDING_VERSION if scene_grounding else None}
    if type(b_validation_corrections) is not int or not 0 <= b_validation_corrections <= 2:
        raise ValueError('VALIDATION_CORRECTION_LIMIT_INVALID')
    result['b_validation_corrections'] = b_validation_corrections
    if b is not None:
        from .isolated_b import PROPERTY_RUNTIME_IMAGE
        if not isinstance(b, dict) or set(b) != {'image', 'property_model_directory'} or b['image'] != PROPERTY_RUNTIME_IMAGE:
            raise ValueError('PROPERTY_RUNTIME_CONFIGURATION_REQUIRED')
        directory = safe_path(Path(b['property_model_directory']))
        if any(not (directory / n).is_file() for n in ('config.json', 'modules.json')):
            raise ValueError('PROPERTY_RUNTIME_MODEL_REQUIRED')
        result['b'] = {'image': b['image'], 'property_model_directory': str(directory)}
    if d_web_search is not None:
        from .dsh_search import validate_search_configuration
        result['d_web_search'] = validate_search_configuration(d_web_search)
        if result['d_web_search']['model'] != model_config['D']:
            raise ValueError('FROZEN_SEARCH_MODEL_REQUIRED')
    if d_web_access is not None:
        from .isolated_dsh import validate_web_access
        result['d_web_access'] = validate_web_access(d_web_access)
    return result
