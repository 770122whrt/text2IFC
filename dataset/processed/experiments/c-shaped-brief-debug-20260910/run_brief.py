"""Single-stage, single-response diagnostic; inherits the frozen C task budget."""
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SOURCE = OUT.parent / 'c-shaped-teaching-building-20260910'
OLD = SOURCE / 'live-run/runs/41edcb4296d1b826'
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from text2ifc_agent.generation_budget import GenerationBudget, BudgetedProvider, BudgetLimits
from text2ifc_agent.live_pipeline import run_design_brief_stage
from text2ifc_agent.providers import ProviderOutputError


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class OneResponse:
    def __init__(self, provider):
        self.provider = provider
        self.calls = 0

    def generate_live(self, **kwargs):
        if self.calls:
            raise ProviderOutputError('Single-response diagnostic stops before additional semantic correction.',
                details={'failure_class': 'diagnostic_call_limit', 'transport_attempted': False})
        frozen = (OLD / 'calls/01-design-brief/prompt-rendered.md').read_text(encoding='utf-8')
        assert kwargs['prompt'] == frozen, 'Diagnostic must preserve the previous rendered prompt.'
        self.calls += 1
        return self.provider.generate_live(**kwargs)


def execute(output, provider, evidence_class):
    output = Path(output)
    output.mkdir(exist_ok=False)
    original = OLD / 'generation-budget.json'
    old_hash = sha(original)
    shutil.copyfile(original, output / 'generation-budget.json')
    budget = GenerationBudget(output, BudgetLimits(max_calls=32, max_tokens=2000000, max_active_seconds=3600))
    before = budget.snapshot()
    assert before['calls_used'] == 1 and before['tokens_used_or_reserved'] == 83996
    assert all(row['status'] != 'reserved' for row in before['attempts'])
    stage = output / 'design-brief'
    record = dict(status='running', evidence_class=evidence_class, started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        budget_before=before, historical_budget_sha256=old_hash, request_sha256=sha(SOURCE / 'request.txt'),
        generation_attempted=False, audit_attempted=False, max_new_provider_responses=1)
    write(output / 'execution.json', record)
    gate = OneResponse(BudgetedProvider(provider, budget))
    try:
        result = run_design_brief_stage(provider=gate, output_dir=stage,
            design_brief_schema_version='text2ifc/design-brief/2.3', design_review_enabled=False,
            case=dict(case_id='41edcb4296d1b826', call_index=1,
                user_request=(SOURCE / 'request.txt').read_text(encoding='utf-8'),
                conversation=read(OLD / 'calls/01-design-brief/conversation.json')))
        record.update(status=result['status'], brief_result=result)
    except Exception as error:
        record.update(status='exception', exception_type=type(error).__name__)
    finally:
        record.update(budget_after=budget.snapshot(), finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                      historical_budget_unchanged=sha(original) == old_hash)
        write(output / 'execution.json', record)
    assert record['historical_budget_unchanged']
    assert budget.snapshot()['calls_used'] == 2
    assert (stage / 'response.raw.json').exists() or (stage / 'provider-error.json').exists()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    admission = read(OUT / 'admission.json')
    assert admission['status'] == 'admitted'
    for name, value in admission['files_sha256'].items():
        assert sha(ROOT / name) == value, name
    for name, value in admission['dependencies'].items():
        assert importlib.metadata.version(name) == value
    if not args.live:
        print('Admission verified; no credential access or network.'); return
    authorization = read(OUT / 'authorization.json')
    assert authorization['status'] == 'approved'
    assert authorization['request_sha256'] == sha(SOURCE / 'request.txt')
    assert authorization['prior_authorization_sha256'] == sha(SOURCE / 'authorization.json')
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, OpenAICompatibleLiveProvider
    load_env_file(ROOT / '.env')
    config = load_openai_compatible_runtime_config(dict(os.environ))
    assert urlparse(config.base_url).hostname == 'api.deepseek.com' and config.model == 'deepseek-v4-flash'
    assert config.max_completion_tokens == 65536, 'Keep original single-response output allowance.'
    record = execute(OUT / 'live-attempt', OpenAICompatibleLiveProvider(config=config), 'live')
    print(json.dumps({key:record[key] for key in ['status','budget_after','historical_budget_unchanged']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
