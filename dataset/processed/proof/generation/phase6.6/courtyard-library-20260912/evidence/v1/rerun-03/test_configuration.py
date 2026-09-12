"""A per-response cap experiment keeps production and the full-loop limits fixed."""
import ast
import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, OpenAICompatibleLiveProvider

OUT = Path(__file__).resolve().parent


def test_execution_path_matches_already_verified_runner():
    def body(path):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
    before, after = body(OUT.parent / 'rerun-02/run_case.py'), body(OUT / 'run_case.py')
    assert before.keys() == after.keys()
    assert all(before[k] == after[k] for k in before if k != 'main')
    old = (OUT.parent / 'rerun-02/run_case.py').read_text(encoding='utf-8')
    expected = old.replace('rerun-01/live-run/runs/0b57f15f4af1b7c7/generation-budget.json',
                           'rerun-02/live-run/runs/5e0a62ff38ef73c1/generation-budget.json')
    expected = expected.replace('max_completion_tokens=65536,max_input_tokens=131072',
                                'max_completion_tokens=98304,max_input_tokens=131072')
    assert expected == (OUT / 'run_case.py').read_text(encoding='utf-8')


def test_raised_cap_reaches_adapter_with_same_thinking_and_json_contract():
    requests = []
    def create(**request):
        requests.append(request)
        return SimpleNamespace(model_dump=lambda: {'id': 'offline-cap', 'model': 'fake',
            'choices': [{'finish_reason': 'stop', 'message': {'content': '{"ok":true}'}}],
            'usage': {'prompt_tokens': 5, 'completion_tokens': 5, 'total_tokens': 10}})
    config = load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER': 'deepseek', 'API_KEY': 'offline-test',
        'OPENAI_BASE_URL': 'https://example.invalid', 'TEXT2IFC_DEEPSEEK_MODEL': 'fake'})
    config = dataclasses.replace(config, max_completion_tokens=98304, max_input_tokens=131072)
    provider = OpenAICompatibleLiveProvider(config=config, connection_max_attempts=1,
        client_factory=lambda **_: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    provider.generate_live(session_id='offline-cap', prompt='Return JSON.', schema={}, state={})
    assert len(requests) == 1
    assert requests[0]['max_tokens'] == 98304
    assert requests[0]['response_format'] == {'type': 'json_object'}
    assert requests[0]['extra_body']['thinking'] == {'type': 'enabled'}


def test_prior_truncation_remains_charged():
    ledger = json.loads((OUT.parent / 'rerun-02/live-run/runs/5e0a62ff38ef73c1/generation-budget.json').read_text(encoding='utf-8'))
    assert ledger['limits'] == {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600}
    assert len(ledger['attempts']) == 4
    assert ledger['attempts'][-1]['status'] == 'failed'
    assert sum(a['tokens_charged'] for a in ledger['attempts']) == 310268
