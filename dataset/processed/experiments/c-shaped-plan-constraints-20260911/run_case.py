"""One authorized public Generation loop; no preseeded design-review concern."""
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

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911'
PRIOR_BUDGET=OUT.parent/'c-shaped-wall-join-20260911/live-run/runs/916d8afe752160e3/generation-budget.json'
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
LIMITS={'max_calls':32,'max_tokens':2000000,'max_active_seconds':3600}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def execute(*,output,provider_factory,evidence_class,strategy='legacy_full'):
    from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits,BudgetedProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    request=(SOURCE/'request.txt').read_text(encoding='utf-8')
    record=dict(status='running',evidence_class=evidence_class,request_sha256=sha(SOURCE/'request.txt'),
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),limits=LIMITS,
        prior_budget_sha256=sha(PRIOR_BUDGET),preseeded_concerns=False,reused_design_brief=False,reference_ifc_supplied=False,generation_strategy=strategy)
    with (output/'run.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        store=SessionStore.open(output/'sessions.sqlite',artifact_root=output)
        try:
            session=store.create_session(original_input=request)
            shutil.copyfile(PRIOR_BUDGET,session.run_dir/'generation-budget.json')
            budget=GenerationBudget(session.run_dir,BudgetLimits(**LIMITS))
            assert budget.snapshot()['calls_used']==11 and budget.snapshot()['tokens_used_or_reserved']==831626
            record.update(run_id=session.session_hash,run_dir=str(session.run_dir),budget_before=budget.snapshot())
            write(output/'execution.json',record)
            turns=read(SOURCE/'conversation.json')
            assert turns[0]['content']==request
            for turn in turns[1:]:
                store.append_turn(session.session_id,role=turn['role'],text=turn['content'])
            brief=run_design_brief_stage(provider=BudgetedProvider(provider_factory(),budget),output_dir=session.run_dir/'calls/01-design-brief',
                design_brief_schema_version='text2ifc/design-brief/2.4',design_review_enabled=False,
                case=dict(case_id=session.session_hash,user_request=request,conversation=turns,call_index=1))
            store.record_agent_call(session.session_id,{'role':'design_brief','call_index':1,**brief})
            record['brief_result']=brief
            if brief['valid'] and brief['status']=='ready':
                store.mark_session_status(session.session_id,'ready')
                result=run_ready_session_to_ifc(store=store,session=session.session_hash,provider_factory=provider_factory,
                    generation_strategy=strategy,budget_limits=BudgetLimits(**LIMITS))
                record.update(status=result.status,result=dataclasses.asdict(result))
            else:
                record['status']=brief['status']
                store.mark_session_status(session.session_id,record['status'])
            store.export_session(session.session_id)
        except Exception as error:
            record.update(status='exception',exception_type=type(error).__name__)
            raise
        finally:
            if 'budget' in locals():record['budget_after']=budget.snapshot()
            record['prior_budget_unchanged']=sha(PRIOR_BUDGET)==record['prior_budget_sha256']
            record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
            store.close();write(output/'execution.json',record)
    return record

def verify_admission():
    admission=read(OUT/'admission.json')
    assert admission['status']=='admitted'
    for p,h in admission['files_sha256'].items():assert sha(ROOT/p)==h,p
    for package,version in admission['dependencies'].items():assert importlib.metadata.version(package)==version,package
    return admission

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    verify_admission()
    if not args.live:
        print('Offline admission verified; no credentials loaded and no network transport.');return
    approval=read(OUT/'authorization.json')
    assert approval['status']=='approved' and approval['destination']=='https://api.deepseek.com' and approval['model']=='deepseek-v4-flash'
    assert approval['request_sha256']==sha(SOURCE/'request.txt') and approval['payload_preview_sha256']==sha(OUT/'payload-preview.json')
    assert approval['limits']==LIMITS
    assert not (OUT/'live-run').exists(),'This attempt already exists; inspect it, do not restart.'
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config,OpenAICompatibleLiveProvider
    load_env_file(ROOT/'.env');config=load_openai_compatible_runtime_config(dict(os.environ))
    assert urlparse(config.base_url).hostname=='api.deepseek.com' and config.model=='deepseek-v4-flash'
    config=dataclasses.replace(config,max_completion_tokens=65536,max_input_tokens=131072)
    result=execute(output=OUT/'live-run',provider_factory=lambda:OpenAICompatibleLiveProvider(config=config,connection_max_attempts=1),evidence_class='live')
    print(json.dumps({k:result[k] for k in ['status','run_id','evidence_class']},ensure_ascii=False))

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support();main()
