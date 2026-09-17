"""Retry a transport-only Generator failure while preserving its complete snapshot.

Restores the already-recorded ready Brief through the public controller. No manual
status promotion, replayed Generator response, or source facts enter the Provider.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.compact_campaign import load,admission,budget_for,runtime,verify_text
from text2ifc_ifc2text.llm_pipeline import _write_json
from text2ifc_ifc2text.goal_budget import GoalStopped


def restore_ready_public(store, session_id):
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    def forbidden(*args, **kwargs):
        raise GoalStopped('RECOVERY_MUST_NOT_INVOKE_NEW_BRIEF')
    result=run_design_brief_clarification_loop(store=store,session=session_id,
        invoke_design_brief=forbidden,user_answers=())
    if result.status!='ready': raise GoalStopped('RECORDED_BRIEF_NOT_READY')
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='scripts/ifc2text/compact-campaign-v0.6.json')
    parser.add_argument('--case',default='hxp')
    args=parser.parse_args(); cfg=load(ROOT/args.config); code=admission(cfg)
    out=ROOT/cfg['output']/args.case; text=verify_text(out)
    attempt=out/'reconstruction-128k'
    prior=load(attempt/'generation-result.json')
    if prior['status']!='provider_failed': raise GoalStopped('TRANSPORT_FAILURE_REQUIRED')
    info=load(attempt/'session.json'); run_dir=Path(info['run_dir'])
    if (run_dir/'output.ifc').exists() or (run_dir/'generator/candidate.json').exists():
        raise GoalStopped('TRANSPORT_RETRY_CANNOT_REPLACE_EXISTING_CANDIDATE')
    error=load(run_dir/'generator/provider-error.json')
    if error.get('failure_class') != 'provider_connection_error' or error.get('stage') != 'generator':
        raise GoalStopped('CONNECTION_FAILURE_EVIDENCE_REQUIRED')
    history=attempt/'transport-retry-01'
    if history.exists(): raise GoalStopped('TRANSPORT_RETRY_ALREADY_EXISTS')
    budget=budget_for(cfg); budget.check_capacity('reconstruction')
    shutil.copytree(run_dir,history/'prior-run')
    _write_json(history/'prior-generation-result.json',prior)
    _write_json(history/'retry.json',{'code_commit':code['code_commit'],
        'reason':'recorded transport-only failure; retry under same cumulative limits',
        'ready_brief_reused':True,'new_generator_response_required':True})
    conf,client,provider=runtime(cfg,budget,'reconstruction',cfg['generation_output_tokens'])
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.generation_budget import BudgetLimits
    try:
        with SessionStore.open(attempt/'sessions.sqlite',artifact_root=attempt) as store:
            session=store.get_session(info['id'])
            if session.original_input!=text: raise GoalStopped('SOURCE_TEXT_CHANGED')
            restore_ready_public(store,session.session_id)
            result=run_ready_session_to_ifc(store=store,session=session.session_id,provider_factory=lambda:provider,
                generation_strategy=cfg['generation_strategy'],trace_level='debug',
                budget_limits=BudgetLimits(max_calls=cfg['max_reconstruction_calls'],max_tokens=cfg['max_total_tokens']))
            report={'status':result.status,'session_hash':result.session_hash,
                    'ifc_path':str(result.ifc_path) if result.ifc_path else None,
                    'generator_status':result.generator_status,'audit_status':result.audit_status,
                    'transport_retry':1,'budget':budget.snapshot()}
        _write_json(history/'result.json',report)
        _write_json(attempt/'generation-result.json',report)
        print(json.dumps({k:report[k] for k in ('status','session_hash','ifc_path','generator_status','audit_status')},ensure_ascii=False))
        return 0
    except Exception as exc:
        budget.halt('GENERATION_RETRY_FAILED')
        _write_json(history/'terminal.json',{'status':'failed','error_type':type(exc).__name__})
        raise

if __name__=='__main__': raise SystemExit(main())
