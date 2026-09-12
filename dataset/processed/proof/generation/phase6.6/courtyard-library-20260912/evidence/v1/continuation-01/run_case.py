"""Declared stage continuation: unchanged live Generator, bounded attachments, real Audit.

No replay Provider impersonates a new Generator. Source failed run is immutable;
only production deterministic recovery creates a derived candidate in a new folder.
"""
import argparse
import contextlib
import dataclasses
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
BASE = OUT.parent
ROOT = OUT.parents[4]
ORIGIN = BASE/'rerun-04/live-run/runs/3cd339b0be4fd872'
LIMITS = {'max_calls':32, 'max_tokens':2000000, 'max_active_seconds':3600}
sys.path[:0] = [str(ROOT), str(ROOT/'src')]

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value): p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def snapshot(root): return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}


def execute(*, output, provider_factory, evidence_class):
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits, BudgetedProvider
    from text2ifc_agent.live_pipeline import (run_repair_stage, run_semantic_coverage_stage,
        run_candidate_gate_stage, run_audit_report_stage, run_final_acceptance_stage)
    from text2ifc_agent.interactive_cli_flow import _promote_repaired_candidate
    from text2ifc_agent.expected_facts import write_expected_facts
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    before = snapshot(ORIGIN)
    metadata = read(ORIGIN/'generator/response-metadata.json')
    raw = read(ORIGIN/'generator/response.raw.json')
    parsed = read(ORIGIN/'generator/parsed-output.json')
    assert metadata['evidence_class'] == 'live'
    assert raw['id'] == metadata['response_id'] and raw['choices'][0]['finish_reason'] == 'stop'
    assert json.loads(raw['choices'][0]['message']['content']) == parsed
    assert (ORIGIN/'generator/input.txt').read_text(encoding='utf-8').rstrip() == (BASE/'request.txt').read_text(encoding='utf-8').rstrip()
    record = {'status':'running', 'evidence_class':evidence_class,
        'execution_mode':'explicit_stage_continuation', 'source_run_id':ORIGIN.name,
        'source_generator_response_id':raw['id'], 'source_files_sha256':before,
        'new_brief_calls':0, 'new_generator_calls':0,
        'started_at':dt.datetime.now(dt.timezone.utc).isoformat()}
    for directory in ['design-brief','generator']:
        shutil.copytree(ORIGIN/directory, output/directory)
    shutil.copyfile(ORIGIN/'generation-budget.json',output/'generation-budget.json')
    budget = GenerationBudget(output, BudgetLimits(**LIMITS)); record['budget_before'] = budget.snapshot()
    write(output/'execution.json',record)
    case_id = ORIGIN.name
    def forbidden(): raise AssertionError('Attachment recovery must not call Provider')
    with (output/'run.log').open('x',encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            brief = read(output/'design-brief/design-brief.json')
            write_expected_facts(case_dir=output,case_id=case_id,design_brief=brief)
            repair = run_repair_stage(provider_factory=forbidden,output_dir=output/'repair',
                generator_source_dir=output/'generator',case_id=case_id)
            record['repair'] = repair
            assert repair['valid'] and repair['provider_call_count'] == 0
            repaired = read(output/'repair/repaired-candidate.json')
            assert repaired['entities'] == parsed['entities']
            assert repaired['relationships'][:len(parsed['relationships'])] == parsed['relationships']
            _promote_repaired_candidate(output,output/'repair/repaired-candidate.json')
            coverage = run_semantic_coverage_stage(case_dir=output,output_dir=output,case_id=case_id)
            gates = run_candidate_gate_stage(case_dir=output,output_dir=output,case_id=case_id)
            record['candidate_checks'] = {k:gates[k] for k in ['valid','compile_reopen_success','geometry_success','deterministic_gates_passed']}
            assert coverage['valid'] and gates['valid']
            record['status'] = 'awaiting_audit'; write(output/'execution.json',record)
            audit = run_audit_report_stage(provider=BudgetedProvider(provider_factory(),budget),
                case_dir=output,case_id=case_id)
            record['audit'] = audit
            assert audit['valid'], 'Audit did not accept; preserve findings and stop this bounded continuation.'
            accepted = run_final_acceptance_stage(case_dir=output,output_dir=output/'final-acceptance',case_id=case_id)
            record['acceptance'] = accepted
            assert accepted['valid'], 'Final acceptance blocked'
            record['status'] = 'compiled'
        except Exception as error:
            record.update(status='exception',exception_type=type(error).__name__,exception_message=str(error))
            raise
        finally:
            record.update(budget_after=budget.snapshot(),source_unchanged=snapshot(ORIGIN)==before,
                          finished_at=dt.datetime.now(dt.timezone.utc).isoformat())
            write(output/'execution.json',record)
    return record


def verify_admission():
    a = read(OUT/'admission.json'); assert a['status']=='admitted'
    for p,h in a['files_sha256'].items(): assert sha(ROOT/p)==h,p
    for p,v in a['dependencies'].items(): assert importlib.metadata.version(p)==v,p


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    verify_admission()
    if not args.live: print('Offline admission valid; no credentials loaded.'); return
    approval=read(OUT/'authorization.json')
    assert approval['status']=='approved' and approval['limits']==LIMITS
    assert approval['destination']=='https://api.deepseek.com' and approval['model']=='deepseek-v4-flash'
    assert approval['request_sha256']==sha(BASE/'request.txt')
    assert approval['payload_preview_sha256']==sha(OUT/'payload-preview.json')
    assert not (OUT/'live-run').exists(), 'Inspect the existing attempt; do not restart it.'
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config,OpenAICompatibleLiveProvider
    load_env_file(ROOT/'.env');config=load_openai_compatible_runtime_config(dict(os.environ))
    assert urlparse(config.base_url).hostname=='api.deepseek.com' and config.model=='deepseek-v4-flash'
    config=dataclasses.replace(config,max_completion_tokens=98304,max_input_tokens=131072)
    r=execute(output=OUT/'live-run',provider_factory=lambda:OpenAICompatibleLiveProvider(config=config,connection_max_attempts=1),
              evidence_class='live_generator_with_deterministic_recovery_and_new_live_audit')
    print(json.dumps({k:r[k] for k in ['status','source_generator_response_id','source_unchanged']}))

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support();main()
