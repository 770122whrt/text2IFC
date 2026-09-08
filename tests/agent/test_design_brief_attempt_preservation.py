"""Every CLI transport attempt survives failure before JSON validation."""
import json
from types import SimpleNamespace

import pytest

from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker
from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config


@pytest.mark.parametrize('kind', ['non_json', 'truncated', 'empty', 'auth', 'timeout'])
def test_failed_design_transport_retains_attempt_without_publishing(tmp_path, kind):
    response={'id':'retained-attempt','model':'fake','choices':[{'finish_reason':'length' if kind=='truncated' else 'stop','message':{'content':'' if kind=='empty' else '{"broken":' if kind=='truncated' else 'not json'}}], 'usage':{'total_tokens':11}}
    def create(**kwargs):
        if kind in {'auth','timeout'}:
            raise (PermissionError if kind=='auth' else TimeoutError)('secret-key provider-private-url')
        return SimpleNamespace(model_dump=lambda:response)
    config=load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER':'deepseek','API_KEY':'secret-key','OPENAI_BASE_URL':'https://provider-private-url','TEXT2IFC_DEEPSEEK_MODEL':'fake'})
    invoke=make_openai_design_brief_invoker(config=config,run_dir=tmp_path,client_factory=lambda **_:SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    with pytest.raises(Exception):
        invoke([{'role':'user','content':'生成一个房间。','turn_id':'turn-user-001'}],1)
    root=tmp_path/'calls/01-design-brief'
    assert (root/'request.redacted.json').is_file()
    assert (root/'prompt-rendered.md').is_file()
    if kind in {'auth','timeout'}:
        failure=json.loads((root/'transport-failure.json').read_text(encoding='utf-8'))
        assert failure['exception_type'] in {'PermissionError','TimeoutError'}
    else:
        assert json.loads((root/'response.raw.json').read_text(encoding='utf-8'))==response
    assert not (root/'design-brief.json').exists()
    text=''.join(p.read_text(encoding='utf-8') for p in root.iterdir() if p.is_file())
    assert 'secret-key' not in text
    assert 'provider-private-url' not in text


@pytest.mark.parametrize('existing', ['response.raw.json', 'request.redacted.json', 'transport-failure.json'])
def test_repeated_call_index_cannot_overwrite_any_existing_attempt(tmp_path, existing):
    root = tmp_path / 'calls/01-design-brief'
    root.mkdir(parents=True)
    (root / existing).write_bytes(b'original attempt bytes')
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        raise TimeoutError('second transport must not happen')
    config = load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER': 'deepseek', 'API_KEY': 'test',
                                                    'OPENAI_BASE_URL': 'https://example.invalid',
                                                    'TEXT2IFC_DEEPSEEK_MODEL': 'fake'})
    invoke = make_openai_design_brief_invoker(config=config, run_dir=tmp_path,
        client_factory=lambda **_: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    with pytest.raises(Exception, match='DESIGN_BRIEF_ATTEMPT_ALREADY_EXISTS'):
        invoke([{'role': 'user', 'content': '另一场景', 'turn_id': 'turn-user-001'}], 1)
    assert calls == []
    assert (root / existing).read_bytes() == b'original attempt bytes'
