"""Opt-in isolated Harness model transport; no model capability evidence."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import isolated_b as carrier


PROFILE_VERSION = 'isolated-harness-provider/0.1'
PROFILES = [
    {'version': PROFILE_VERSION, 'provider': 'openai', 'label': 'GPT',
     'model': 'gpt-6-sol', 'max_input_tokens': 100000, 'max_completion_tokens': 32768},
    {'version': PROFILE_VERSION, 'provider': 'qwen', 'label': 'Qwen',
     'model': 'ms-gmk85rth', 'max_input_tokens': 65536, 'max_completion_tokens': 16384},
]
LEGACY_PROFILE = {'version': PROFILE_VERSION, 'provider': 'deepseek', 'label': 'DeepSeek',
                  'model': carrier.MODEL, 'max_input_tokens': 65536,
                  'max_completion_tokens': 65536}


def config(tmp_path, profile=None, **changes):
    values = dict(bundle=tmp_path/'runtime', workspace=tmp_path/'work',
                  state_volume='model-profile-state', network='model-profile-internal',
                  base_url='http://repair-gateway:8000/v1')
    if profile is not None:
        values.update(model=profile['model'], model_profile=deepcopy(profile))
    values.update(changes)
    return carrier.IsolatedBConfig(**values)


def workspace(tmp_path):
    work = tmp_path/'work'
    work.mkdir(exist_ok=True)
    (work/'model.ifc').write_text('Transport binding fixture, never parsed.', encoding='utf8')
    (work/'task.txt').write_text('Public transport binding fixture.', encoding='utf8')
    return work


def payload(profile=None, **changes):
    value = {'action': 'start', 'run_id': 'model-profile-test',
             'base_url': 'http://127.0.0.1:8000/v1'}
    if profile is not None:
        value.update(model=profile['model'], model_profile=deepcopy(profile))
    value.update(changes)
    return value


class StopAtSDK(Exception):
    """Stop at the external SDK constructor before any transport or IFC read."""


@pytest.fixture
def stopped_sdk(monkeypatch):
    import openai
    calls = []

    def stop(**kwargs):
        calls.append(kwargs)
        raise StopAtSDK

    monkeypatch.setattr(openai, 'OpenAI', stop)
    return calls


def start_binding(tmp_path, profile, stopped_sdk):
    work = workspace(tmp_path)
    state = tmp_path/'state'
    with pytest.raises(StopAtSDK):
        carrier.worker_execute(payload(profile), workspace=work, state_root=state)
    return work, state, json.loads((state/'task.json').read_text(encoding='utf8'))


def test_legacy_config_keeps_strict_deepseek_default(tmp_path):
    value = config(tmp_path)
    assert value.model == 'deepseek-v4-flash'
    assert value.model_profile is None
    for profile in PROFILES:
        with pytest.raises(ValueError, match='FROZEN_B_MODEL_REQUIRED'):
            replace(value, model=profile['model'])


@pytest.mark.parametrize('profile', PROFILES, ids=['gpt', 'qwen'])
def test_profile_opt_in_accepts_requested_models_and_copies_input(tmp_path, profile):
    supplied = deepcopy(profile)
    value = config(tmp_path, model=profile['model'], model_profile=supplied)
    supplied['max_input_tokens'] = 1
    assert value.model == profile['model']
    assert value.model_profile == profile


@pytest.mark.parametrize('field,bad', [
    ('version', 'isolated-harness-provider/9.9'),
    ('provider', ''), ('provider', ' '), ('provider', 'openai\n'),
    ('provider', 'https://api.example.com/v1'), ('provider', 'Bearer key'),
    ('label', ''), ('label', '\tGPT'), ('label', 'GPT\nQwen'),
    ('label', 'https://api.example.com/v1'),
    ('model', ''), ('model', 'gpt 6'), ('model', 'gpt-6-sol\x00'),
    ('model', 'https://api.example.com/v1'),
    ('max_input_tokens', 0), ('max_input_tokens', -1),
    ('max_input_tokens', True), ('max_input_tokens', 1.5),
    ('max_completion_tokens', 0), ('max_completion_tokens', -1),
    ('max_completion_tokens', False), ('max_completion_tokens', '32768'),
])
def test_unsafe_or_invalid_profile_is_rejected_at_host_and_worker(tmp_path, field, bad):
    profile = {**PROFILES[0], field: bad}
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE'):
        config(tmp_path, model=profile['model'], model_profile=profile)
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE'):
        carrier.worker_execute(payload(profile), workspace=tmp_path, state_root=tmp_path/'state')
    assert not (tmp_path/'state').exists()


@pytest.mark.parametrize('mutation', [
    {'api_key': 'must-not-enter-carrier'},
    {'base_url': 'https://api.example.com/v1'},
    {'endpoint': 'https://api.example.com/v1'},
])
def test_profile_cannot_embed_credentials_or_endpoints(tmp_path, mutation):
    profile = {**PROFILES[0], **mutation}
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE'):
        config(tmp_path, profile)
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE'):
        carrier.worker_execute(payload(profile), workspace=tmp_path, state_root=tmp_path/'state')


@pytest.mark.parametrize('field', list(PROFILES[0]))
def test_profile_requires_every_declared_field(tmp_path, field):
    profile = deepcopy(PROFILES[0])
    del profile[field]
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE'):
        config(tmp_path, model=PROFILES[0]['model'], model_profile=profile)


@pytest.mark.parametrize('bad', ['gpt-6-sol', [], 1, True])
def test_profile_requires_a_dictionary(tmp_path, bad):
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE'):
        config(tmp_path, model='gpt-6-sol', model_profile=bad)


def test_profile_model_must_match_explicit_model_at_both_boundaries(tmp_path):
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE_MODEL_MISMATCH'):
        config(tmp_path, model_profile=PROFILES[0])
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE_MODEL_MISMATCH'):
        carrier.worker_execute(payload(PROFILES[0], model='ms-gmk85rth'),
                               workspace=tmp_path, state_root=tmp_path/'state')


@pytest.mark.parametrize('override', [{'model': 'gpt-6-sol'}, {'model_profile': PROFILES[0]}])
def test_execute_cannot_bypass_validated_config_with_model_overrides(tmp_path, monkeypatch, override):
    def no_docker(*args, **kwargs):
        pytest.fail('Model override reached Docker')

    monkeypatch.setattr(carrier.subprocess, 'run', no_docker)
    with pytest.raises(ValueError, match='HARNESS_MODEL_PROFILE_OVERRIDE_FORBIDDEN'):
        carrier.IsolatedB(config(tmp_path)).execute('start', 'model-profile-test', **override)


@pytest.mark.parametrize('profile', PROFILES, ids=['gpt', 'qwen'])
def test_worker_nonlegacy_model_requires_profile_before_sdk(tmp_path, stopped_sdk, profile):
    with pytest.raises(ValueError, match='FROZEN_B_MODEL_REQUIRED'):
        carrier.worker_execute(payload(model=profile['model']), workspace=tmp_path,
                               state_root=tmp_path/'state')
    assert stopped_sdk == []
    assert not (tmp_path/'state').exists()


@pytest.mark.parametrize('profile', [None, *PROFILES], ids=['legacy', 'gpt', 'qwen'])
def test_host_payload_keeps_method_settings_and_profile_opt_in(tmp_path, monkeypatch, profile):
    carrier.build_runtime_bundle(Path(__file__).resolve().parents[3], tmp_path/'runtime')
    workspace(tmp_path)
    requests = []

    def docker(command, **kwargs):
        if command[:3] == ['docker', 'network', 'inspect']:
            return SimpleNamespace(stdout='true', returncode=0)
        requests.append(json.loads(kwargs['input']))
        return SimpleNamespace(stdout=carrier.RESULT_PREFIX+'{"ok":true}', stderr='', returncode=0)

    monkeypatch.setattr(carrier.subprocess, 'run', docker)
    value = config(tmp_path, profile, scene_grounding=True, max_validation_corrections=2)
    assert carrier.IsolatedB(value).start('model-profile-test')['ok'] is True
    assert requests[0]['model'] == (carrier.MODEL if profile is None else profile['model'])
    from text2ifc_ifc_repair.scene_grounding import SCENE_GROUNDING_VERSION
    assert requests[0]['scene_grounding_version'] == SCENE_GROUNDING_VERSION
    assert requests[0]['max_validation_corrections'] == 2
    if profile is None:
        assert 'model_profile' not in requests[0]
    else:
        assert requests[0]['model_profile'] == profile


@pytest.mark.parametrize('profile', [None, *PROFILES], ids=['legacy', 'gpt', 'qwen'])
def test_worker_binding_and_same_profile_read_preserve_gateway_and_dummy_key(tmp_path, stopped_sdk, profile):
    work, state, binding = start_binding(tmp_path, profile, stopped_sdk)
    if profile is None:
        assert 'model_profile' not in binding
        assert binding['model'] == carrier.MODEL
    else:
        assert binding['model_profile'] == profile
        assert binding['model'] == profile['model']
    with pytest.raises(StopAtSDK):
        carrier.worker_execute(payload(profile, action='read'), workspace=work, state_root=state)
    assert len(stopped_sdk) == 2
    assert all(value['api_key'] == carrier.DUMMY_KEY for value in stopped_sdk)
    assert all(value['base_url'] == 'http://127.0.0.1:8000/v1' for value in stopped_sdk)


CHANGES = [
    {'model': 'gpt-6-sol-v2'}, {'provider': 'other'}, {'label': 'Other label'},
    {'max_input_tokens': 100001}, {'max_completion_tokens': 32769},
]


@pytest.mark.parametrize('changes', CHANGES)
def test_worker_rejects_changed_profile_before_sdk(tmp_path, stopped_sdk, changes):
    work, state, _ = start_binding(tmp_path, PROFILES[0], stopped_sdk)
    changed = {**PROFILES[0], **changes}
    with pytest.raises(ValueError, match='B_TASK_BINDING_MISMATCH'):
        carrier.worker_execute(payload(changed, action='read'), workspace=work, state_root=state)
    assert len(stopped_sdk) == 1


def test_worker_profile_cannot_be_removed_even_when_model_is_legacy(tmp_path, stopped_sdk):
    work, state, _ = start_binding(tmp_path, LEGACY_PROFILE, stopped_sdk)
    with pytest.raises(ValueError, match='B_TASK_BINDING_MISMATCH'):
        carrier.worker_execute(payload(action='read'), workspace=work, state_root=state)
    assert len(stopped_sdk) == 1


@pytest.mark.parametrize('changes', CHANGES)
def test_restore_rejects_changed_profile_before_docker(tmp_path, monkeypatch, stopped_sdk, changes):
    work, state, binding = start_binding(tmp_path, PROFILES[0], stopped_sdk)
    (state/'native').mkdir()
    binding['model_profile'].update(changes)
    if 'model' in changes:
        binding['model'] = changes['model']
    (state/'task.json').write_text(json.dumps(binding), encoding='utf8')

    def no_docker(*args, **kwargs):
        pytest.fail('Changed binding reached Docker')

    monkeypatch.setattr(carrier.subprocess, 'run', no_docker)
    with pytest.raises(ValueError, match='STATE_RESTORE_BINDING_MISMATCH'):
        carrier.IsolatedB(config(tmp_path, PROFILES[0])).restore_state(state)


@pytest.mark.parametrize('profile', [None, *PROFILES], ids=['legacy', 'gpt', 'qwen'])
def test_restore_preserves_matching_profile_without_model_calls(tmp_path, monkeypatch, stopped_sdk, profile):
    _, state, binding = start_binding(tmp_path, profile, stopped_sdk)
    (state/'native').mkdir()
    before = hashlib.sha256((state/'task.json').read_bytes()).hexdigest()
    commands = []

    def docker(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=1 if command[:3] == ['docker', 'volume', 'inspect'] else 0)

    monkeypatch.setattr(carrier.subprocess, 'run', docker)
    restored = carrier.IsolatedB(config(tmp_path, profile)).restore_state(state)
    assert restored['restored'] is True
    assert restored['binding'] == binding
    assert restored['model_calls'] == 0
    assert before == hashlib.sha256((state/'task.json').read_bytes()).hexdigest()
    assert len(stopped_sdk) == 1
    assert commands


@pytest.mark.parametrize('profile', PROFILES, ids=['gpt', 'qwen'])
def test_profile_does_not_allow_external_gateway(tmp_path, profile):
    with pytest.raises(ValueError, match='INTERNAL_GATEWAY_REQUIRED'):
        config(tmp_path, profile, base_url='https://api.example.com/v1')
    with pytest.raises(ValueError, match='INTERNAL_GATEWAY_REQUIRED'):
        carrier.worker_execute(payload(profile, base_url='https://api.example.com/v1'),
                               workspace=tmp_path, state_root=tmp_path/'state')


@pytest.mark.parametrize('profile', [None, *PROFILES], ids=['legacy', 'gpt', 'qwen'])
def test_real_sdk_request_uses_profile_model_and_completion_limit(tmp_path, profile):
    from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs
    from tests.ifc_repair.repair_comparison.test_isolated_b import fake_http
    cases, _, _ = _formal_public_inputs(tmp_path/'synthetic')
    work = cases/'synthetic-001/public'
    (work/'task.txt').write_text('Public synthetic transport test.', encoding='utf8')
    with fake_http(['not-json']) as (url, requests):
        result = carrier.worker_execute(payload(profile, base_url=url), workspace=work,
                                        state_root=tmp_path/'state')
    assert result['result']['successful_artifact_publishable'] is False
    assert requests
    expected_model = carrier.MODEL if profile is None else profile['model']
    expected_limit = 65536 if profile is None else profile['max_completion_tokens']
    token_field = 'max_tokens' if profile is None else 'max_completion_tokens'
    for request in requests:
        assert request['model'] == expected_model
        assert request[token_field] == expected_limit
        assert request['response_format'] == {'type': 'json_object'}
        assert request['temperature'] == 0
        assert ('thinking' in request) is (profile is None)


def test_profile_input_limit_stops_before_http_transport(tmp_path):
    from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs
    from tests.ifc_repair.repair_comparison.test_isolated_b import fake_http
    profile = {**PROFILES[0], 'max_input_tokens': 1}
    cases, _, _ = _formal_public_inputs(tmp_path/'synthetic')
    work = cases/'synthetic-001/public'
    (work/'task.txt').write_text('Public synthetic transport test.', encoding='utf8')
    with fake_http(['not-json']) as (url, requests):
        result = carrier.worker_execute(payload(profile, base_url=url), workspace=work,
                                        state_root=tmp_path/'state')
    assert result['result']['successful_artifact_publishable'] is False
    assert requests == []
