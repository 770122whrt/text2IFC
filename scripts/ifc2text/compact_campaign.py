"""Synchronous compact IFC2Text campaign with frozen source and prompt versions."""
from __future__ import annotations
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.run_goal import git, SCOPE
from text2ifc_ifc2text.llm_pipeline import _write_json
from text2ifc_ifc2text.goal_budget import BudgetClient, GoalStopped
from text2ifc_ifc2text.campaign_budget import CampaignBudget
from text2ifc_ifc2text.compact_pipeline import prepare_compact, write_compact
from text2ifc_ifc2text.compact import compact_description, validate_narration, narrative_context
from text2ifc_ifc2text.roundtrip_compare import compare_roundtrip
from text2ifc_text.splits import atomic_write_text


def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))


def budget_for(cfg):
    limit=cfg['max_total_tokens']
    return CampaignBudget(ROOT/cfg['budget_root'],predecessor=ROOT/cfg['predecessor_ledger'],
        tokens=limit,writing_calls=cfg['max_writing_calls'],reconstruction_calls=cfg['max_reconstruction_calls'])


def admission(cfg):
    record=load(ROOT/cfg['output']/'validation/admission.json')
    if record.get('status')!='admitted': raise GoalStopped('ADMISSION_REQUIRED')
    if git('status','--porcelain','--untracked-files=all','--',*SCOPE): raise GoalStopped('EXECUTION_SCOPE_DIRTY')
    if git('diff',record['code_commit'],'--',*SCOPE): raise GoalStopped('ADMISSION_SCOPE_CHANGED')
    if cfg!=load(ROOT/cfg['output']/'config.json'): raise GoalStopped('CONFIG_CHANGED')
    return record


def runtime(cfg,budget,stage,cap):
    from scripts.agent.run_phase6_2_cli import load_env_file,DEFAULT_ENV_FILE
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, _create_openai_client, OpenAICompatibleLiveProvider
    load_env_file(DEFAULT_ENV_FILE)
    config=load_openai_compatible_runtime_config(dict(os.environ))
    limit=cfg['provider_input_tokens']
    config=replace(config,max_input_tokens=limit,max_completion_tokens=cap,timeout_seconds=cfg['provider_timeout_seconds'])
    client=BudgetClient(_create_openai_client(config=config,client_factory=None),budget,stage)
    provider=OpenAICompatibleLiveProvider(config=config,client_factory=lambda **_:client,connection_max_attempts=1)
    return config,client,provider


def prepare(cfg):
    reports=[]
    for case in cfg['cases']:
        out=ROOT/cfg['output']/case['id']
        if (out/'prepared.json').exists():
            reports.append(load(out/'prepared.json')); continue
        reports.append(prepare_compact(ROOT/case['source'],out))
    if len(set(c['source'] for c in cfg['cases']))!=len(cfg['cases']): raise GoalStopped('DISTINCT_SOURCE_REQUIRED')
    _write_json(ROOT/cfg['output']/'preparation-summary.json',reports)
    return reports


def write(cfg,case):
    record=admission(cfg); budget=budget_for(cfg)
    conf,client,provider=runtime(cfg,budget,'writing',cfg['writing_output_tokens'])
    out=ROOT/cfg['output']/case['id']
    cap=conf.max_completion_tokens
    _write_json(out/'runtime-writing.json',{'requested_model':conf.model,'provider':conf.provider_label,
       'code_commit':record['code_commit'],'output_cap':cap,'sdk_retries':0,'provider_retries':0})
    return write_compact(output=out,provider=provider,budget=budget)


def verify_text(out):
    facts=load(out/'source-facts.json'); narrative=load(out/'writing/narration/parsed-response.json')
    validate_narration(narrative,narrative_context(facts))
    text=(out/'design-description.md').read_text(encoding='utf-8')
    if compact_description(facts,narrative)!=text: raise GoalStopped('TEXT_MODIFIED')
    review=load(out/'content-review.json')
    if review.get('decision')!='allow_diagnostic_reconstruction': raise GoalStopped('AGENT_CONTENT_REVIEW_REQUIRED')
    return text


def brief(cfg,case,extended=False):
    record=admission(cfg); budget=budget_for(cfg)
    out=ROOT/cfg['output']/case['id']; text=verify_text(out)
    attempt=out/('reconstruction-128k' if extended else 'reconstruction-64k')
    if (attempt/'started.json').exists(): raise GoalStopped('BRIEF_ATTEMPT_EXISTS')
    budget.check_capacity('reconstruction')
    cap=cfg['extended_brief_output_tokens'] if extended else cfg['brief_output_tokens']
    conf,client,provider=runtime(cfg,budget,'reconstruction',cap)
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker,run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits
    limit=cfg['max_total_tokens']
    limits=BudgetLimits(max_calls=cfg['max_reconstruction_calls'],max_tokens=limit)
    _write_json(attempt/'started.json',{'stage':'brief','requested_model':conf.model,'output_cap':cap,
           'code_commit':record['code_commit'],'source_building_input':'design-description.md only'})
    try:
        with SessionStore.open(attempt/'sessions.sqlite',artifact_root=attempt) as store:
            session=store.create_session(original_input=text)
            GenerationBudget(session.run_dir,limits=limits)
            _write_json(attempt/'session.json',{'id':session.session_id,'hash':session.session_hash,'run_dir':str(session.run_dir)})
            invoker=make_openai_design_brief_invoker(config=conf,run_dir=session.run_dir,client_factory=lambda **_:client,
                     design_review_enabled=False,design_brief_schema_version=cfg['design_brief_schema'])
            result=run_design_brief_clarification_loop(store=store,session=session.session_id,invoke_design_brief=invoker,user_answers=())
            if store.get_session(session.session_id).original_input!=text: raise GoalStopped('SESSION_TEXT_CHANGED')
            report={'status':result.status,'session_id':session.session_id,'session_hash':session.session_hash,
                    'same_text_entered_session':True,'output_cap':cap,'budget':budget.snapshot()}
            _write_json(attempt/'brief-result.json',report)
            return report
    except Exception as error:
        budget.halt('BRIEF_FAILED')
        _write_json(attempt/'brief-terminal.json',{'status':'failed','error_type':type(error).__name__,
              'message':str(error) if isinstance(error,GoalStopped) else 'See preserved provider evidence',
              'budget':budget.snapshot()})
        raise


def generate(cfg,case,extended=False):
    record=admission(cfg); budget=budget_for(cfg)
    out=ROOT/cfg['output']/case['id']; verify_text(out)
    attempt=out/('reconstruction-128k' if extended else 'reconstruction-64k')
    if load(attempt/'brief-result.json')['status']!='ready': raise GoalStopped('READY_BRIEF_REQUIRED')
    if (attempt/'generation-started.json').exists(): raise GoalStopped('GENERATION_ATTEMPT_EXISTS')
    conf,client,provider=runtime(cfg,budget,'reconstruction',cfg['generation_output_tokens'])
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.generation_budget import BudgetLimits
    cap=conf.max_completion_tokens; limit=cfg['max_total_tokens']
    _write_json(attempt/'generation-started.json',{'code_commit':record['code_commit'],'output_cap':cap})
    try:
        with SessionStore.open(attempt/'sessions.sqlite',artifact_root=attempt) as store:
            result=run_ready_session_to_ifc(store=store,session=load(attempt/'session.json')['id'],provider_factory=lambda:provider,
                generation_strategy=cfg['generation_strategy'],trace_level='debug',
                budget_limits=BudgetLimits(max_calls=cfg['max_reconstruction_calls'],max_tokens=limit))
            report={'status':result.status,'session_hash':result.session_hash,
                   'ifc_path':str(result.ifc_path) if result.ifc_path else None,
                   'generator_status':result.generator_status,'audit_status':result.audit_status,'budget':budget.snapshot()}
            _write_json(attempt/'generation-result.json',report)
            return report
    except Exception as error:
        budget.halt('GENERATION_FAILED')
        _write_json(attempt/'generation-terminal.json',{'status':'failed','error_type':type(error).__name__,'budget':budget.snapshot()})
        raise


def compare(cfg,case,extended=False):
    out=ROOT/cfg['output']/case['id']; attempt=out/('reconstruction-128k' if extended else 'reconstruction-64k')
    session=load(attempt/'session.json'); ifc=Path(session['run_dir'])/'output.ifc'
    if not ifc.is_file(): raise GoalStopped('NO_REAL_RECONSTRUCTED_IFC')
    source=ROOT/case['source']; before=source.read_bytes()
    report=compare_roundtrip(source,ifc,position_mm=cfg['position_tolerance_mm'],dimension_mm=cfg['dimension_tolerance_mm'])
    if source.read_bytes()!=before: raise GoalStopped('SOURCE_CHANGED')
    generation=load(attempt/'generation-result.json') if (attempt/'generation-result.json').exists() else {'status':'incomplete'}
    report['generation_publication_status']=generation['status']
    report['comparison_role']='diagnostic comparison; IFC existence does not mean generation acceptance'
    _write_json(attempt/'compare.json',report)
    lines=['# 重建差异报告',f"源模型：{case['id']}；生成状态：{generation['status']}",
           '比较源IFC与真实Provider输出编译的IFC；不使用相同GUID匹配。',
           '## 汇总',json.dumps(report.get('summary',report.get('status')),ensure_ascii=False),'## 按构件定位']
    for category,content in report.get('components',{}).items():
        lines.append('### '+category)
        for row in content.get('missing',[]): lines.append('- 缺失：'+str(row))
        for row in content.get('extra',[]): lines.append('- 多余：'+str(row))
        for row in content.get('matched',[]):
            if row['outside_tolerance']: lines.append('- 偏差：'+json.dumps(row,ensure_ascii=False))
    lines+=['## 未评估与限制',json.dumps(report.get('unassessed',[]),ensure_ascii=False),'；'.join(report.get('limitations',[]))]
    atomic_write_text(attempt/'COMPARE.md','\n\n'.join(lines)+'\n')
    return {'status':report['status'],'summary':report.get('summary'),'generation_status':generation['status']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','write','brief','generate','compare','status'])
    parser.add_argument('--case',default='hxp'); parser.add_argument('--extended',action='store_true')
    parser.add_argument('--config',default='scripts/ifc2text/compact-campaign-v0.4.json')
    args=parser.parse_args(); cfg=load(ROOT/args.config)
    case=next((c for c in cfg['cases'] if c['id']==args.case),None)
    if case is None: raise ValueError('CASE_NOT_CONFIGURED')
    try:
        if args.command=='prepare': result=prepare(cfg)
        elif args.command=='status': result=budget_for(cfg).snapshot()
        elif args.command=='write': result=write(cfg,case)
        else: result={'brief':brief,'generate':generate,'compare':compare}[args.command](cfg,case,args.extended)
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except Exception as error:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(error).__name__,
              'reason':str(error) if isinstance(error,(GoalStopped,ValueError)) else 'See saved evidence'},ensure_ascii=False)); return 1

if __name__=='__main__': raise SystemExit(main())
