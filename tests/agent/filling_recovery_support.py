"""Offline attachment-recovery fixtures, independent of retired live-run scripts.

Extracted without changing fixture values or public-loop assertions. There is
no credential loader, live-provider factory, admission bypass or CLI here.
"""
import contextlib
import copy
import dataclasses
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
from functools import partial
from types import SimpleNamespace
from tests.agent.test_c_plan_run import fixture as old_fixture, Provider, SOURCE
from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits

LIMITS = {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def fixture():
    brief,candidate=old_fixture()
    brief['schema_version']='text2ifc/design-brief/2.5'
    candidate['schema_version']='bim-json/2.2'
    for record in candidate['entities']:
        if record['ifc_class'] in {'IfcDoor', 'IfcWindow'}:
            record['part_appearance']={'frame':{'color':[.1,.2,.3]}}
            brief['known_facts']['semantic_requirements'].append({'entity_id':record['id'],'part_appearance':copy.deepcopy(record['part_appearance'])})
    brief['known_facts']['semantic_review']['appearance']['status']='specified'
    return brief,candidate

def execute(*,source,prior_budget,output,provider_factory,evidence_class,strategy='legacy_full'):
    from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits,BudgetedProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    request=(source/'request.txt').read_text(encoding='utf-8')
    record=dict(status='running',evidence_class=evidence_class,request_sha256=sha(source/'request.txt'),
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),limits=LIMITS,prior_budget_sha256=sha(prior_budget),
        preseeded_concerns=False,reused_design_brief=False,reference_ifc_supplied=False,generation_strategy=strategy)
    with (output/'run.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        store=SessionStore.open(output/'sessions.sqlite',artifact_root=output)
        try:
            session=store.create_session(original_input=request)
            shutil.copyfile(prior_budget,session.run_dir/'generation-budget.json')
            budget=GenerationBudget(session.run_dir,BudgetLimits(**LIMITS))
            assert budget.snapshot()['attempts']==read(prior_budget)['attempts']
            record.update(run_id=session.session_hash,run_dir=str(session.run_dir),budget_before=budget.snapshot())
            write(output/'execution.json',record)
            from text2ifc_agent.clarification import ClarificationController
            turns=read(source/'conversation.json') if (source/'conversation.json').exists() else ClarificationController.start(case_id=session.session_hash,user_request=request).transcript_dicts()
            assert turns[0]['content']==request
            for turn in turns[1:]:
                store.append_turn(session.session_id,role=turn['role'],text=turn['content'])
            brief=run_design_brief_stage(provider=BudgetedProvider(provider_factory(),budget),output_dir=session.run_dir/'calls/01-design-brief',
                design_brief_schema_version='text2ifc/design-brief/2.5',design_review_enabled=False,
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
            record['prior_budget_unchanged']=sha(prior_budget)==record['prior_budget_sha256']
            record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
            store.close();write(output/'execution.json',record)
    return record

def runner(tmp_path):
    budget = GenerationBudget(tmp_path/'prior', BudgetLimits(**LIMITS))
    slot = budget.reserve(stage='old-failure', reserved_tokens=100)
    budget.settle(slot, usage={'prompt_tokens':20, 'completion_tokens':30}, elapsed_seconds=3, failed=True)
    return SimpleNamespace(execute=partial(execute, source=tmp_path, prior_budget=budget.path))
