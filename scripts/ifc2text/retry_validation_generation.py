"""One real retry through the public API, with preserved failed graph and feedback."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.compact_campaign import load,admission,budget_for,runtime,verify_text,compare
from scripts.ifc2text.retry_transport_generation import restore_ready_public
from text2ifc_ifc2text.llm_pipeline import _write_json
from text2ifc_ifc2text.goal_budget import GoalStopped


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='scripts/ifc2text/compact-campaign-v0.6.json')
    parser.add_argument('--case',default='hxp')
    args=parser.parse_args(); cfg=load(ROOT/args.config); code=admission(cfg)
    out=ROOT/cfg['output']/args.case; verify_text(out)
    attempt=out/'reconstruction-128k'; prior=load(attempt/'generation-result.json')
    if prior['generator_status']!='invalid': raise GoalStopped('INVALID_GENERATOR_REQUIRED')
    info=load(attempt/'session.json'); run_dir=Path(info['run_dir'])
    validation=load(run_dir/'generator/validation.json')
    if validation['valid'] or not validation['issues']: raise GoalStopped('VALIDATOR_FAILURE_REQUIRED')
    if (run_dir/'output.ifc').exists(): raise GoalStopped('EXISTING_IFC_MUST_NOT_BE_REPLACED')
    history=attempt/'validation-retry-01'
    if history.exists(): raise GoalStopped('VALIDATION_RETRY_ALREADY_EXISTS')
    budget=budget_for(cfg); budget.check_capacity('reconstruction')
    feedback={**load(ROOT/'scripts/ifc2text/encoding-feedback-v0.1.json'),
        'validation_issues':validation['issues'],
        'previous_generated_document':load(run_dir/'generator/parsed-output.json')}
    shutil.copytree(run_dir,history/'prior-run')
    _write_json(history/'previous-result.json',prior)
    _write_json(history/'generation-feedback.json',feedback)
    _write_json(history/'version.json',{'code_commit':code['code_commit'],'public_text_only':True,
                                       'source_facts_sent':False,'generation_call_index':2})
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.generation_budget import BudgetLimits
    _,_,provider=runtime(cfg,budget,'reconstruction',cfg['generation_output_tokens'])
    try:
        with SessionStore.open(attempt/'sessions.sqlite',artifact_root=attempt) as store:
            restore_ready_public(store,info['id'])
            result=run_ready_session_to_ifc(store=store,session=info['id'],provider_factory=lambda:provider,
                generation_strategy=cfg['generation_strategy'],trace_level='debug',
                budget_limits=BudgetLimits(max_calls=cfg['max_reconstruction_calls'],max_tokens=cfg['max_total_tokens']),
                generation_feedback=feedback,generator_call_index=2)
            report={'status':result.status,'session_hash':result.session_hash,
                'ifc_path':str(result.ifc_path) if result.ifc_path else None,
                'generator_status':result.generator_status,'audit_status':result.audit_status,
                'validation_retry':1,'budget':budget.snapshot()}
        _write_json(history/'result.json',report); _write_json(attempt/'generation-result.json',report)
        if (run_dir/'output.ifc').is_file():
            comparison=compare(cfg,{'id':args.case,'source':next(c['source'] for c in cfg['cases'] if c['id']==args.case)},extended=True)
            report['comparison']=comparison
        print(json.dumps({k:report[k] for k in ['status','ifc_path','generator_status','audit_status']},ensure_ascii=False))
        return 0
    except Exception as exc:
        budget.halt('VALIDATION_RETRY_FAILED')
        _write_json(history/'terminal.json',{'status':'failed','error_type':type(exc).__name__})
        raise

if __name__=='__main__': raise SystemExit(main())
