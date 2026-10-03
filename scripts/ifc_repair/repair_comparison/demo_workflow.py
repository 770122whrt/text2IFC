"""Development-only public CLI for real isolated runtimes and HTTP accounting.

`offline` uses a separately held deterministic HTTP fixture, never environment
credentials. `live` requires a current stage admission before reading keys.
The formal five-case package is deliberately outside this entry point.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import httpx
import jsonschema

from .container_tools import docker, IMAGE
from .contracts import read_json, write_json, sha256, safe_path
from .direct_runner import DirectRunner
from .isolated_b import build_runtime_bundle, IsolatedB, IsolatedBConfig
from .isolated_direct import ChatExecutor
from .isolated_dsh import NativeDSH, submitted_path, QUIESCENT_SCRIPT, IMAGE as DSH_IMAGE
from .ledger import Ledger, TERMINAL
from .wire_gateway import WireGateway
from .controller_owner import task_owner

REPO=Path(__file__).resolve().parents[3]
CASES=REPO/'dataset/processed/ifc-repair/repair-comparison/development'
ORDER=['case-001-A','case-001-B','case-001-C','case-001-D',
       'case-002-B','case-002-C','case-002-D','case-002-A']
BUDGET={'tokens':2500000,'calls':100,'active_seconds':5400,'tool_seconds':120,'extensions':[]}
MODELS={'A':'deepseek-v4-flash','B':'deepseek-v4-flash','C':'gpt-6-sol','D':'deepseek-v4-flash'}


def bindings():
    # Only executable/runtime/public-input bindings affect this development
    # stage admission. Mutable reports and human annotations are excluded.
    files=[p for p in Path(__file__).parent.rglob('*') if p.is_file() and p.suffix in {'.py','.mjs','.html'}]
    files += list((REPO/'src/text2ifc_ifc_repair').rglob('*.py'))
    files += list((REPO/'src/text2ifc_agent').rglob('*.py'))
    files += list((REPO/'prompts/agent').rglob('*.json'))
    files += list((REPO/'schemas/agent').rglob('*.json'))
    files += [CASES/case/'public'/name for case in ('case-001','case-002') for name in ('model.ifc','request.txt')]
    return {'files':{p.relative_to(REPO).as_posix():sha256(p) for p in sorted(set(files))},
            'images':{image:docker('image','inspect',image,'--format','{{.Id}}') for image in (IMAGE,DSH_IMAGE)},
            'models':MODELS,'budget':BUDGET}


def verify_admission(path):
    value=read_json(safe_path(Path(path)))
    if value.get('stage')!='repair-comparison-two-demo-live' or value.get('passed') is not True or value.get('bindings')!=bindings():
        raise ValueError('CURRENT_STAGE_ADMISSION_REQUIRED')
    return value


def initialize(root,*,mode,admission=None):
    root=safe_path(Path(root))
    if mode=='live':verify_admission(admission)
    if (root/'experiment.json').exists():raise ValueError('EXPERIMENT_EXISTS_USE_STATUS_OR_RESUME')
    root.mkdir(parents=True,exist_ok=True)
    suffix=uuid.uuid4().hex[:10]
    config={'mode':mode,'order':ORDER,'models':MODELS,'budget':BUDGET,
            'network':'repair-demo-'+suffix,'relay':'repair-relay-'+suffix,
            'admission':str(Path(admission).resolve()) if admission else None,'routes':{}}
    bundle=root/'runtime/b'
    build_runtime_bundle(REPO,bundle)
    for run_id in ORDER:
        case_id,arm=run_id.rsplit('-',1)
        config['routes'][run_id]={'token':uuid.uuid4().hex,'container':'repair-'+suffix+'-'+run_id.lower(),
                                'volume':'repair-state-'+suffix+'-'+run_id.lower()}
        DirectRunner.create(CASES/case_id/'public',root,case_id=case_id,arm=arm,budget=BUDGET,
                            mode='live_development' if mode=='live' else 'real_runtime_fake_model',
                            runtime_metadata={'model_requested':MODELS[arm],'arm':arm,'image':DSH_IMAGE if arm=='D' else IMAGE})
    write_json(root/'experiment.json',config)
    return config


def native_quiescent(name,packet=None):
    script=QUIESCENT_SCRIPT
    if packet and packet.get('sessionId'):
        script=script.replace("children=json.loads(activity.read_text()).get('active_child_sessions',[])",
            "children=[s for s in json.loads(activity.read_text()).get('active_child_sessions',[]) if s != "+repr(packet['sessionId'])+"]")
    try:return json.loads(docker('exec',name,'python','-c',script,timeout=10))['quiescent']
    except (RuntimeError,subprocess.TimeoutExpired,ValueError):return False


def serve(root):
    root=safe_path(Path(root))
    config=read_json(root/'experiment.json')
    ledger=Ledger(root/'control.sqlite')
    if config['mode']=='live':
        verify_admission(config['admission'])
        from dotenv import dotenv_values
        env=dotenv_values(REPO/'.env')
        keys={'C':env['OPENAI_API_KEY'],'deepseek':env['DEEPSEEK_API_KEY']}
        upstream={'C':env['OPENAI_EXPERIMENT_BASE_URL'].rstrip('/')+'/chat/completions',
                  'deepseek':env.get('OPENAI_BASE_URL','https://api.deepseek.com').rstrip('/')+'/chat/completions',
                  'messages':'https://api.deepseek.com/anthropic/v1/messages'}
        transport=None
    else:
        from tests.ifc_repair.repair_comparison.demo_http_fixture import FakeDemoTransport
        transport=httpx.MockTransport(FakeDemoTransport(root,config))
        keys={'C':'offline-unused','deepseek':'offline-unused'}
        upstream={'C':'https://offline.invalid','deepseek':'https://offline.invalid','messages':'https://offline.invalid'}
    token=uuid.uuid4().hex
    with WireGateway(ledger,root/'wire',transport=transport,control_token=token) as gateway:
        for run_id,row in config['routes'].items():
            arm=run_id[-1]
            key=keys['C' if arm=='C' else 'deepseek']
            endpoints={'messages':upstream['messages']} if arm=='D' else {'chat':upstream['C' if arm=='C' else 'deepseek']}
            if config['mode']=='offline':endpoints={k:'https://offline.invalid/'+run_id+'/'+k for k in endpoints}
            gateway.register(run_id,token=row['token'],model=MODELS[arm],api_key=key,
                endpoints=endpoints,evidence_class='live_provider' if config['mode']=='live' else 'real_runtime_fake_model',
                quiescent=(lambda packet,name=row['container']:native_quiescent(name,packet)) if arm=='D' else None)
        docker('network','create','--internal',config['network'])
        relay=Path(__file__).with_name('container_relay.py').resolve()
        port=gateway.server.server_port
        docker('create','--name',config['relay'],'--pull=never','--network=bridge','--read-only',
               '--user=10001:10001','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=256m',
               '--cpus=1','--pids-limit=32','--env',f'REPAIR_CONTROLLER_PORT={port}',
               '--mount',f'type=bind,source={relay},target=/opt/relay.py,readonly',IMAGE,'python','/opt/relay.py')
        docker('network','connect','--alias','repair-gateway',config['network'],config['relay'])
        docker('start',config['relay'])
        write_json(root/'service.json',{'url':gateway.url,'control_token':token,'pid':os.getpid(),
                   'network':config['network'],'relay':config['relay'],'state':'running'})
        print('REPAIR_SERVICE_READY '+gateway.url,flush=True)
        try:
            while not (root/'stop-service').exists():time.sleep(.2)
        finally:
            docker('stop','--time','2',config['relay'])
            docker('rm',config['relay'])
            docker('network','rm',config['network'])
            write_json(root/'service.json',{'url':gateway.url,'state':'stopped'})


def run(root,run_id):
    if run_id[-1] in {'A','C'}:return run_owned(root,run_id)
    with task_owner(root,run_id):return run_owned(root,run_id)


def run_owned(root,run_id):
    root=safe_path(Path(root))
    config=read_json(root/'experiment.json')
    if config['mode']=='live':verify_admission(config['admission'])
    route=config['routes'][run_id]
    service=read_json(root/'service.json')
    if service['state']!='running':raise ValueError('GATEWAY_SERVICE_NOT_RUNNING')
    runner=DirectRunner(root,run_id)
    state=runner.ledger.snapshot(run_id)
    if state['status'] in TERMINAL or state['status']=='awaiting_user':return state
    arm=state['arm']
    base='http://repair-gateway:8000/'+route['token']
    if arm in {'A','C'}:
        engine=ChatExecutor(root,run_id,gateway_url=service['url']+'/'+route['token']+'/v1',
                            model=MODELS[arm],evidence_class='live_provider' if config['mode']=='live' else 'real_runtime_fake_model')
        result=engine.run()
        write_json(root/'runtime'/(run_id+'-commands.json'),engine.tools.records)
        return result
    if state['status']=='ready':runner.ledger.start(run_id)
    if state['activities'] or any(c['state']=='inflight' for c in runner.ledger.calls(run_id)):
        raise ValueError('RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
    if arm=='B':
        cfg=IsolatedBConfig(root/'runtime/b',runner.workspace,route['volume'],config['network'],base+'/v1',
                            container_name=route['container'],evidence_class='live' if config['mode']=='live' else 'deterministic_fake_http')
        worker=IsolatedB(cfg)
        previous=state.get('native',{}).get('result')
        runner.ledger.activity(run_id,'native-worker',begin=True)
        if previous:
            question=previous.get('clarification')
            answer_event=next((e for e in reversed(runner.ledger.events(run_id)) if e['kind']=='answer'),None)
            if not question or not answer_event:raise ValueError('NATIVE_RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
            result=worker.answer(run_id,answer=answer_event['payload']['native_answer'],
                                 clarification_id=question['clarification_id'],expected_state_version=previous['state_version'])
        else:
            worker.prepare_state_volume()
            result=worker.start(run_id)
        if result.get('container_stopped') is False:
            raise RuntimeError('NATIVE_PROCESS_STOP_NOT_CONFIRMED')
        runner.ledger.activity(run_id,'native-worker',begin=False)
        runner.ledger.record(run_id,'isolated_native_return',result)
        native=result.get('result',{})
        runner.ledger.set_native(run_id,{'result':native,'state_volume':route['volume']})
        if not result['ok']:
            return runner.ledger.finish(run_id,'runtime_error',detail=result.get('error','native worker failure'))
        if native.get('clarification'):
            question=native['clarification']
            return runner.ledger.ask(run_id,question_id=question['clarification_id'],
                text=json.dumps(question,ensure_ascii=False),binding={'native_question':question,'state_version':native['state_version']})
        export=root/'runtime'/run_id
        worker.export_state(export)
        if result['artifact_relative']:return runner.submit(result['artifact_relative'])
        return runner.ledger.finish(run_id,'unsupported' if native['status']=='unsupported' else 'cancelled' if native['status']=='cancelled' else 'no_output',detail=native.get('status'))
    carrier=NativeDSH(runner.workspace,root/'runtime'/run_id,name=route['container'],
        state_volume=route['volume'],network=config['network'],base_url=base,model=MODELS['D'],session_id=run_id)
    result=carrier.run(ledger=runner.ledger,run_id=run_id)
    runner.ledger.record(run_id,'isolated_native_return',result)
    runner.ledger.set_native(run_id,{'result':result,'state_volume':route['volume']})
    if not result['ok']:
        return runner.ledger.finish(run_id,'budget_exhausted' if 'BUDGET' in result.get('error','') else 'runtime_error',detail=result.get('error'))
    native=result['result']
    if native['finish_reason']=='error':return runner.ledger.finish(run_id,'runtime_error',detail='native turn ended with error')
    try:path=submitted_path(native['final_response'])
    except ValueError as error:return runner.ledger.finish(run_id,'runtime_error',detail=str(error))
    if path:return runner.submit(path)
    return runner.ledger.finish(run_id,'no_output',detail='no explicit native IFC submission')


def answer(root,run_id,value):
    root=safe_path(Path(root))
    ledger=Ledger(root/'control.sqlite')
    state=ledger.snapshot(run_id)
    question=state['question']
    if state['status']!='awaiting_user':raise ValueError('NO_PENDING_QUESTION')
    text=value['text']
    event_id=value.get('event_id') or 'human-'+uuid.uuid4().hex
    binding=question['binding']
    if state['arm']=='D':
        packet=binding['native_packet']
        answers=value.get('answers')
        if answers is None:
            if len(packet['questions'])!=1:raise ValueError('ONE_CONFIRMED_ANSWER_PER_QUESTION_REQUIRED')
            answers=[{'id':packet['questions'][0]['id'],'selected':[],'custom':text}]
        config=read_json(root/'experiment.json'); service=read_json(root/'service.json')
        with httpx.Client(trust_env=False,timeout=30) as client:
            response=client.post(service['url']+'/control/'+service['control_token']+'/answer',json={
                'token':config['routes'][run_id]['token'],'question_id':question['question_id'],
                'answers':answers,'text':text,'event_id':event_id})
        response.raise_for_status()
        return response.json()
    native_answer=None
    if state['arm']=='B':
        native_answer=value.get('native_answer',{'kind':'add_detail','detail':text})
        native=binding['native_question']
        jsonschema.Draft202012Validator(native['answer_schema']).validate(native_answer)
        if native_answer.get('kind')=='select_candidate' and native_answer.get('candidate_token') not in {c['candidate_token'] for c in native['candidates']}:
            raise ValueError('CANDIDATE_NOT_OFFERED')
    return ledger.answer(run_id,question_id=question['question_id'],text=text,event_id=event_id,native_answer=native_answer)


def status(root):
    root=Path(root); config=read_json(root/'experiment.json'); ledger=Ledger(root/'control.sqlite')
    return [ledger.snapshot(run_id) for run_id in config['order']]


def main():
    # Windows consoles otherwise encode the Chinese JSON response as CP936,
    # while the public CLI contract and subprocess readers use UTF-8.
    sys.stdout.reconfigure(encoding='utf8')
    sys.stderr.reconfigure(encoding='utf8')
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['init','serve','run','answer','status','check','stop'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--mode',choices=['offline','live'],default='offline')
    parser.add_argument('--admission',type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--answer-file',type=Path)
    args=parser.parse_args()
    if args.command=='init':value=initialize(args.root,mode=args.mode,admission=args.admission)
    elif args.command=='serve':serve(args.root);return
    elif args.command=='run':value=run(args.root,args.run_id)
    elif args.command=='answer':value=answer(args.root,args.run_id,read_json(args.answer_file))
    elif args.command=='status':value=status(args.root)
    elif args.command=='stop':(args.root/'stop-service').write_text('stop',encoding='utf8');value={'requested':True}
    else:
        from .scoring import score
        reports=[]
        for state in status(args.root):
            result=Path(state['artifact']['path']) if state['artifact'] else None
            report=score(CASES/state['case_id'],result,terminal=state['status'],events=Ledger(args.root/'control.sqlite').events(state['run_id']))
            reports.append({'run_id':state['run_id'],'state':state,'evaluation':report})
        write_json(args.root/'checks.json',reports);value=reports
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
