"""Resume the existing public Brief with an audited restatement of its own text.

The existing local content check reads frozen facts but never sends them to the
Provider. Transport receives only the description and its restatement. Provenance
identifies an agent restatement, never a human verification claim.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.compact_campaign import load, admission, budget_for, runtime, verify_text
from text2ifc_ifc2text.llm_pipeline import _write_json
from text2ifc_ifc2text.goal_budget import GoalStopped


def checked_restatement(payload, text, available_questions):
    required = {'origin','question_ids','source_quotes','answer'}
    if set(payload) != required or payload['origin'] != 'agent_restatement_of_public_description':
        raise ValueError('RESTATEMENT_PROVENANCE_REQUIRED')
    if not payload['question_ids'] or not set(payload['question_ids']).issubset(available_questions):
        raise ValueError('QUESTION_NOT_IN_CURRENT_BRIEF')
    quotes = payload['source_quotes']
    if not quotes or any(not isinstance(q,str) or not q or q not in text for q in quotes):
        raise ValueError('EXACT_PUBLIC_TEXT_QUOTES_REQUIRED')
    if not isinstance(payload['answer'],str) or not payload['answer'].strip():
        raise ValueError('RESTATEMENT_REQUIRED')
    return payload['answer']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='scripts/ifc2text/compact-campaign-v0.6.json')
    parser.add_argument('--case',default='hxp'); parser.add_argument('--answer-file',required=True)
    parser.add_argument('--extended',action='store_true')
    args=parser.parse_args(); cfg=load(ROOT/args.config); record=admission(cfg)
    out=ROOT/cfg['output']/args.case
    attempt=out/('reconstruction-128k' if args.extended else 'reconstruction-64k')
    output_cap=cfg['extended_brief_output_tokens'] if args.extended else cfg['brief_output_tokens']
    prior=load(attempt/'brief-result.json')
    if prior['status']!='needs_clarification': raise GoalStopped('PENDING_CLARIFICATION_REQUIRED')
    text=verify_text(out); session_info=load(attempt/'session.json')
    latest=load(Path(session_info['run_dir'])/'design-brief.json')
    answer_payload=load(ROOT/args.answer_file)
    answer=checked_restatement(answer_payload,text,{q['id'] for q in latest['clarification_questions']})
    marker=attempt/'text-restatement.json'
    if marker.exists(): raise GoalStopped('RESTATEMENT_ATTEMPT_ALREADY_EXISTS')
    _write_json(marker,{'code_commit':record['code_commit'],'payload':answer_payload,
                       'not_human_verification':True,'prior_brief_result':prior})
    budget=budget_for(cfg)
    conf,client,_=runtime(cfg,budget,'reconstruction',output_cap)
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker,run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    try:
        with SessionStore.open(attempt/'sessions.sqlite',artifact_root=attempt) as store:
            session=store.get_session(session_info['id'])
            if session.original_input!=text: raise GoalStopped('SESSION_TEXT_CHANGED')
            invoker=make_openai_design_brief_invoker(config=conf,run_dir=session.run_dir,
                client_factory=lambda **_:client,design_review_enabled=False,
                design_brief_schema_version=cfg['design_brief_schema'])
            result=run_design_brief_clarification_loop(store=store,session=session.session_id,
                invoke_design_brief=invoker,user_answers=[answer])
            report={'status':result.status,'session_id':session.session_id,'session_hash':session.session_hash,
                    'same_text_entered_session':True,'restatement_origin':answer_payload['origin'],
                    'output_cap':output_cap,'budget':budget.snapshot()}
        _write_json(attempt/'brief-result-after-restatement.json',report)
        _write_json(attempt/'brief-result.json',report)
        print(json.dumps({'status':report['status'],'calls':report['budget']['calls'],
                          'tokens':report['budget']['tokens_used_or_reserved']},ensure_ascii=False))
    except Exception as error:
        budget.halt('BRIEF_FAILED')
        _write_json(attempt/'restatement-terminal.json',{'status':'failed','error_type':type(error).__name__})
        raise
    return 0

if __name__=='__main__': raise SystemExit(main())
