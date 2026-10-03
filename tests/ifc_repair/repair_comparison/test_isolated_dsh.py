import json
from pathlib import Path

import pytest


def test_dsh_submission_requires_one_explicit_relative_ifc():
    from scripts.ifc_repair.repair_comparison.isolated_dsh import submitted_path
    assert submitted_path('{"submitted_ifc":"output/result.ifc"}') == 'output/result.ifc'
    assert submitted_path('```json\n{"submitted_ifc":"model.ifc"}\n```') == 'model.ifc'
    assert submitted_path('I finished the repair.') is None
    for value in ('{"submitted_ifc":"../gold.ifc"}', '{"submitted_ifc":"/state/result.ifc"}',
                  '{"submitted_ifc":["one.ifc","two.ifc"]}', '{"submitted_ifc":"result.txt"}',
                  '{"submitted_ifc":"one.ifc","other":"two.ifc"}'):
        with pytest.raises(ValueError):
            submitted_path(value)


def test_dsh_container_preserves_native_runtime_and_exposes_only_this_task(tmp_path):
    from scripts.ifc_repair.repair_comparison.isolated_dsh import NativeDSH
    work = tmp_path/'work'
    work.mkdir()
    carrier = NativeDSH(work, tmp_path/'control', name='repair-dsh-test',
                        state_volume='repair-dsh-test-state', network='repair-internal',
                        base_url='http://repair-gateway:8000/'+'a'*32,
                        model='deepseek-v4-flash', session_id='test-session')
    args = carrier.docker_argv()
    assert '--read-only' in args and '--user=10001:10001' in args
    assert '--network=repair-internal' in args
    assert '--memory=8g' in args and '--cpus=4' in args
    assert any('target=/workspace' in item for item in args)
    assert not any('.env' in item or 'docker.sock' in item for item in args)
    assert 'text2ifc/repair-dsh:0.2.0rc1' in args
    config = json.loads((tmp_path/'control'/'runtime.json').read_text())
    assert config['base_url'].endswith('a'*32) and 'api_key' not in config
    with pytest.raises(ValueError,match='INTERNAL'):
        NativeDSH(work,tmp_path/'bad',name='bad',state_volume='bad',network='bridge',
                  base_url='https://api.deepseek.com',model='deepseek-v4-flash',session_id='test')
