"""Controlled public-Brief input pair. No IFC, extracted facts, or comparator input.

Reuses the existing public controller, registered Prompt and persistent campaign
budget. Stopping at Brief is intentional; this cannot certify IFC reconstruction.
"""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.compact_campaign import budget_for, runtime, load
from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker, run_design_brief_clarification_loop
from text2ifc_agent.session_store import SessionStore
from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits

OUT=ROOT/'dataset/processed/experiments/ifc2text-attribution-20260921-v01'
PUBLIC=ROOT/'dataset/processed/experiments/ifc2text-phase1-20260917/compact-campaign-v06/closeout/hxp-description.md'
BASE_ADMISSION=ROOT/'dataset/processed/experiments/ifc2text-phase1-20260917/compact-campaign-v06/validation/admission.json'
SUFFIX='\n\n## 记录楼层与宿主关系的保留规则\n本次任务是复现记录，不是纠正源模型。构件所在章节给出的楼层归属与宿主墙归属是两种不同关系；即使不同，也必须分别保留，不得自动用宿主墙楼层替换构件的记录楼层。现有输出合同确实不能同时表达时，明确报告冲突或不支持，不静默改变归属。\n'
SCOPE=['src/text2ifc_agent','src/text2ifc_ifc2text','src/text2ifc_compiler','prompts/agent','schemas/agent/design-brief','scripts/ifc2text/attribution_probe_v01.py','scripts/ifc2text/attribute_roundtrip_v01.py','tests/ifc2text/test_attribution_probe_v01.py']

def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()


def request_for(text, arm):
    if arm not in ('original','explicit_containment'):raise ValueError('UNKNOWN_ARM')
    return text if arm=='original' else text+SUFFIX


def brief_summary(brief):
    floors=brief.get('known_facts',{}).get('storeys',[])
    return {'status':brief.get('status'),
        'storeys':[{'id':s.get('id'),'elevation_mm':s.get('elevation_mm'),'net_height_mm':s.get('net_height_mm'),
            'windows':s.get('windows',[]),
            'spaces':[{'id':r.get('id'),'has_polygon':bool(r.get('polygon')),'z_mm':r.get('z_mm'),'height_mm':r.get('height_mm')} for r in s.get('spaces',[])]} for s in floors],
        'ambiguities':brief.get('ambiguities',[]),'questions':brief.get('clarification_questions',[])}


def run_public_brief(text, output, config, client, *, evidence_kind):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    marker=output/'started.json'
    with marker.open('x',encoding='utf-8') as f:
        json.dump({'evidence_kind':evidence_kind,'text_only':True,'input_cap':config.max_input_tokens,
            'output_cap':config.max_completion_tokens},f)
    try:
        with SessionStore.open(output/'sessions.sqlite',artifact_root=output) as store:
            session=store.create_session(original_input=text)
            GenerationBudget(session.run_dir,BudgetLimits(max_calls=1,max_tokens=600000))
            dump(output/'session.json',{'id':session.session_id,'run_dir':str(session.run_dir)})
            def create_with_thinking(**request):
                request['extra_body']={**request.get('extra_body',{}),'thinking':{'type':'enabled'}}
                dump(output/'transport-controls.json',{'thinking_enabled':True,'requested_model':request['model']})
                return client.chat.completions.create(**request)
            explicit_client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_with_thinking)))
            invoke=make_openai_design_brief_invoker(config=config,run_dir=session.run_dir,
                client_factory=lambda **_:explicit_client,design_review_enabled=False,
                design_brief_schema_version='text2ifc/design-brief/2.7')
            result=run_design_brief_clarification_loop(store=store,session=session.session_id,
                invoke_design_brief=invoke,user_answers=())
            paths=list(session.run_dir.glob('calls/*/design-brief.json'))
            report={'evidence_kind':evidence_kind,'controller_status':result.status,'run_dir':str(session.run_dir),
                'generator_invoked':False,'ifc_publication':False,'same_original_text':store.get_session(session.session_id).original_input==text}
            if paths: report['brief']=brief_summary(load(paths[-1]))
            dump(output/'result.json',report)
            return report
    except Exception as exc:
        dump(output/'terminal.json',{'error_type':type(exc).__name__,'evidence_kind':evidence_kind,
            'generator_invoked':False,'ifc_publication':False})
        raise


def validate():
    base=load(BASE_ADMISSION)
    assert base['status']=='admitted'
    previous=base['code_commit']
    # Only the previously patched Generator feedback-index functions may have
    # changed since admission; the Brief transport/controller chain must match.
    old=ast.parse(git('show',previous+':src/text2ifc_agent/interactive_cli_flow.py'))
    new=ast.parse((ROOT/'src/text2ifc_agent/interactive_cli_flow.py').read_text(encoding='utf-8'))
    functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    a,b=functions(old),functions(new)
    changed={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
    assert changed<={'_feedback_resume_state','_run_ready_session_to_ifc'},changed
    assert not git('diff',previous,'--','src/text2ifc_agent/clarification.py','src/text2ifc_agent/openai_compat.py','src/text2ifc_agent/design_brief.py','src/text2ifc_agent/session_store.py','prompts/agent','schemas/agent/design-brief')
    validation=OUT/'validation'
    validation.mkdir(exist_ok=True,parents=True)
    guard_code = ('import sys,json,pytest\nfrom pathlib import Path\nfrom scripts.ifc2text.validate_goal import OfflineRecorder\ng=OfflineRecorder()\nwith g.network_guard():\n rc=pytest.main(sys.argv[1:],plugins=[g])\nPath(' + repr(str(validation/'network.json')) + ').write_text(json.dumps({"network_attempts":g.network_attempts}),encoding="utf-8")\nraise SystemExit(rc if g.network_attempts==0 else 1)')
    command=[sys.executable,'-c',guard_code,'-o','addopts=','tests/ifc2text/test_attribution_probe_v01.py',
        'tests/ifc2text/test_goal_budget_v03.py','tests/ifc2text/test_transport_retry_public.py',
        'tests/agent/test_public_brief_failure_evidence.py','tests/ifc2text/test_compact_public_v04.py',
        '-q','--basetemp='+str(validation/('tmp-'+uuid.uuid4().hex[:12])),'-p','no:cacheprovider',
        '--junitxml='+str(validation/'tests.xml')]
    started=time.time()
    result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    (validation/'pytest.log').write_bytes(result.stdout)
    import xml.etree.ElementTree as ET
    xml=ET.parse(validation/'tests.xml').getroot()
    suites=list(xml.iter('testsuite'))
    counts={k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
    compile_result=subprocess.run([sys.executable,'-m','compileall','-q',str(Path(__file__)),str(ROOT/'scripts/ifc2text/attribute_roundtrip_v01.py')],cwd=ROOT)
    clean=not git('status','--porcelain','--untracked-files=all','--',*SCOPE)
    admitted=result.returncode==0 and compile_result.returncode==0 and not any(counts[k] for k in ('failures','errors','skipped')) and clean
    record={'status':'admitted' if admitted else 'blocked','code_commit':git('rev-parse','HEAD'),
        'ancestor_admission':str(BASE_ADMISSION.relative_to(ROOT)),'ancestor_commit':previous,
        'brief_chain_unchanged':True,'generation_function_delta':sorted(changed),
        'command':command,'counts':counts,'exit_code':result.returncode,'elapsed_s':time.time()-started,
        'compileall':compile_result.returncode==0,'scope_clean':clean,'scope_paths':SCOPE,
        'network_transport_attempted':False,'public_path':'public Brief controller only; downstream generation disabled',
        'full_preflight':False,'evidence_kind':'offline replay and failure injection; not live model evidence'}
    dump(validation/'admission.json',record)
    print(json.dumps(record,ensure_ascii=True))
    return 0 if admitted else 1


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['validate','original','explicit_containment'])
    args=parser.parse_args()
    if args.command=='validate':return validate()
    admission=load(OUT/'validation/admission.json')
    assert admission['status']=='admitted','ADMISSION_REQUIRED'
    assert not git('diff',admission['code_commit'],'--',*SCOPE),'ADMISSION_CHANGED'
    assert not git('status','--porcelain','--untracked-files=all','--',*SCOPE),'EXECUTION_SCOPE_DIRTY'
    cfg=load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json')
    budget=budget_for(cfg);budget.check_capacity('reconstruction')
    original=PUBLIC.read_bytes();text=request_for(PUBLIC.read_text(encoding='utf-8'),args.command)
    conf,client,_=runtime(cfg,budget,'reconstruction',131072)
    out=OUT/('live-'+args.command)
    try:
        report=run_public_brief(text,out,conf,client,evidence_kind='live')
        dump(out/'budget-after.json',budget.snapshot())
        assert PUBLIC.read_bytes()==original,'PUBLIC_BASELINE_MUTATED'
        print(json.dumps(report,ensure_ascii=True))
    except Exception:
        budget.halt('ATTRIBUTION_BRIEF_PROBE_FAILED')
        dump(out/'budget-after.json',budget.snapshot())
        raise
    finally:
        close=getattr(getattr(client,'client',None),'close',None)
        if close is not None:
            close()
    return 0

if __name__=='__main__':raise SystemExit(main())
