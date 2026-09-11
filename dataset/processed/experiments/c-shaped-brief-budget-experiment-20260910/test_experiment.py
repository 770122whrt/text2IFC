import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider,load_openai_compatible_runtime_config

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('budget_experiment',OUT/'run_experiment.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


@pytest.mark.parametrize('kind',['ready','truncated','malformed','connection'])
def test_caps_are_local_and_shared_budget_preserves_history(tmp_path,kind):
    calls=[]
    brief=json.loads((OUT.parent/'c-shaped-brief-debug-20260910/live-attempt/design-brief/design-brief.json').read_text(encoding='utf-8'))
    config=load_openai_compatible_runtime_config(dict(TEXT2IFC_PROVIDER='deepseek',API_KEY='fixture',
        OPENAI_BASE_URL='https://example.invalid',TEXT2IFC_DEEPSEEK_MODEL='fixture'))
    def factory(arm_config):
        def create(**kwargs):
            calls.append(kwargs)
            if kind=='connection':raise TimeoutError('offline')
            return dict(id='offline',model='fixture',usage=dict(prompt_tokens=11,completion_tokens=7,total_tokens=18),
                choices=[dict(finish_reason='length' if kind=='truncated' else 'stop',message=dict(
                    content='{"status":' if kind=='truncated' else 'not JSON' if kind=='malformed' else json.dumps(brief,ensure_ascii=False)))])
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        return OpenAICompatibleLiveProvider(config=arm_config,client_factory=lambda **_:client,connection_max_attempts=1)
    result=runner.execute(tmp_path/'run',config,factory,evidence_class='synthetic_offline')
    assert config.max_completion_tokens==65536
    assert [c['max_tokens'] for c in calls]==([98304] if kind=='connection' else [98304,65536])
    assert len(calls)==len(result['arms'])
    assert result['budget_after']['calls_used']==2+len(calls)
    assert result['budget_after']['attempts'][:2]==result['budget_before']['attempts']
    assert result['historical_budget_unchanged']
    if kind!='connection':
        first,second=[{k:v for k,v in c.items() if k!='max_tokens'} for c in calls]
        assert first==second
        assert result['budget_after']['tokens_used_or_reserved']==147630+18*len(calls)
    if kind=='ready':assert all(r['valid'] and r['status']=='ready' for r in result['arms'])
    else:assert all(not r['valid'] for r in result['arms'])
    assert not list(tmp_path.rglob('*.ifc'))


def test_existing_output_cannot_be_overwritten(tmp_path):
    output=tmp_path/'run';output.mkdir();(output/'original').write_bytes(b'kept')
    with pytest.raises(FileExistsError):runner.execute(output,None,None,evidence_class='synthetic_offline')
    assert (output/'original').read_bytes()==b'kept'
