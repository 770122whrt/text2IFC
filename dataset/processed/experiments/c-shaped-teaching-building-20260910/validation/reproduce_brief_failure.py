"""Offline diagnosis only: real Brief stage with a synthetic SDK transport."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from text2ifc_agent.generation_budget import BudgetedProvider, BudgetLimits, GenerationBudget
from text2ifc_agent.live_pipeline import run_design_brief_stage
from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider, load_openai_compatible_runtime_config


def main():
    output = Path(sys.argv[1])
    output.mkdir(exist_ok=False)
    rows = []
    config = load_openai_compatible_runtime_config(dict(TEXT2IFC_PROVIDER='deepseek',
        API_KEY='fixture', OPENAI_BASE_URL='https://example.invalid', TEXT2IFC_DEEPSEEK_MODEL='fixture'))
    for kind, request in [('truncated', '请生成一间矩形教室。'), ('empty', '生成一个仓库。'),
                          ('no_choices', '创建两层住宅。'), ('connection', '创建一间办公室。')]:
        payload = dict(id='synthetic-response', model='fixture', usage=dict(prompt_tokens=11, completion_tokens=7),
            choices=[] if kind == 'no_choices' else [dict(finish_reason='length' if kind == 'truncated' else 'stop',
                message=dict(content='{"status":' if kind == 'truncated' else ''))])
        calls = []
        def create(**kwargs):
            calls.append(True)
            if kind == 'connection':
                raise TimeoutError('synthetic connection failure')
            return payload
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        provider = OpenAICompatibleLiveProvider(config=config, client_factory=lambda **_: client,
                                               connection_max_attempts=1)
        budget = GenerationBudget(output / kind / 'budget', BudgetLimits(max_calls=2, max_tokens=1000000, max_active_seconds=100))
        stage = output / kind / 'stage'
        try:
            result = run_design_brief_stage(provider=BudgetedProvider(provider, budget), output_dir=stage,
                design_brief_schema_version='text2ifc/design-brief/2.3', case=dict(case_id=kind,
                user_request=request, conversation=[dict(turn_id='turn-user-001', role='user', content=request)]))
            assert not result['valid']
            rows.append(dict(kind=kind, calls=len(calls), exception_type=None,
                stage_status=result['status'], response_in_exception=False,
                response_on_disk=(stage / 'response.raw.json').exists(),
                failure_on_disk=(stage / 'provider-error.json').exists(),
                published_brief=(stage / 'design-brief.json').exists(), budget=budget.snapshot()))
        except (AssertionError, KeyboardInterrupt):
            raise
        except Exception as error:
            evidence = getattr(error, 'evidence', getattr(error, 'details', {}))
            rows.append(dict(kind=kind, calls=len(calls), exception_type=type(error).__name__,
                response_in_exception=isinstance(evidence.get('response'), dict),
                response_on_disk=(stage / 'response.raw.json').exists(),
                failure_on_disk=(stage / 'provider-error.json').exists(),
                published_brief=(stage / 'design-brief.json').exists(), budget=budget.snapshot()))
    assert all(r['calls'] == 1 and not r['published_brief'] for r in rows)
    result = dict(evidence_class='synthetic_offline_diagnosis', observations=rows,
        defect_reproduced=all(not r['failure_on_disk'] for r in rows if r['exception_type']),
        expected_invariant='Provider failure evidence must be persisted by the public Brief stage before propagation.',
        product_fix_applied=False)
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['evidence_class', 'defect_reproduced', 'product_fix_applied']}))


if __name__ == '__main__':
    main()
