"""Public carrier for isolated runtimes and configuration-bound admission.

`offline` uses a separately held deterministic HTTP fixture, never environment
credentials. `live` requires a current stage admission before reading keys.
Defaults remain the two development demos. Explicit batches require their own
configuration and stage admission; formal orchestration supplies the frozen plan.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import uuid

import httpx
import jsonschema

from .container_tools import docker, IMAGE
from .contracts import PUBLIC_FILES, read_json, write_json, sha256, safe_path
from .budget import validate_budget
from .direct_runner import DirectRunner
from .isolated_b import build_runtime_bundle, IsolatedB, IsolatedBConfig
from .isolated_direct import ChatExecutor
from .isolated_dsh import NativeDSH, submitted_path, QUIESCENT_SCRIPT, IMAGE as DSH_IMAGE
from .ledger import Ledger, TERMINAL
from .wire_gateway import WireGateway
from .controller_owner import task_owner
from text2ifc_ifc_repair.scene_grounding import SCENE_GROUNDING_VERSION

REPO=Path(__file__).resolve().parents[3]
CASES=REPO/'dataset/processed/ifc-repair/repair-comparison/development'
ORDER=['case-001-A','case-001-B','case-001-C','case-001-D',
       'case-002-B','case-002-C','case-002-D','case-002-A']
BUDGET={'tokens':2500000,'calls':100,'active_seconds':5400,'tool_seconds':120,'extensions':[]}
MODELS={'A':'deepseek-v4-flash','B':'deepseek-v4-flash','C':'gpt-6-sol','D':'deepseek-v4-flash'}
DEMO_STAGE='repair-comparison-two-demo-live'
FORMAL_STAGE='repair-comparison-formal-live'


def batch_configuration(*, cases_root, case_ids, budgets, stage, models=None, scene_grounding=False):
    """Normalize the exact public task/configuration contract for an admission."""
    if stage not in {DEMO_STAGE, FORMAL_STAGE}:
        raise ValueError('UNKNOWN_EXPERIMENT_STAGE')
    ids=list(case_ids)
    if not ids or any(not isinstance(c,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,60}',c) for c in ids) or len(set(ids))!=len(ids):
        raise ValueError('INVALID_BATCH_CASE_IDS')
    if not isinstance(budgets,dict) or set(budgets)!=set(ids):
        raise ValueError('ONE_BUDGET_PER_CASE_REQUIRED')
    for budget in budgets.values():validate_budget(budget)
    model_config=deepcopy(MODELS if models is None else models)
    if set(model_config)!=set('ABCD') or any(not isinstance(v,str) or not v.strip() for v in model_config.values()):
        raise ValueError('FOUR_MODEL_CONFIGURATIONS_REQUIRED')
    # B's unmodified carrier only supports this frozen DeepSeek alias.
    if any(model_config[a]!=MODELS['B'] for a in 'ABD'):
        raise ValueError('FROZEN_SHARED_DEEPSEEK_MODEL_REQUIRED')
    order=[]
    for i,case in enumerate(ids):
        rotation='ABCD'[i%4:]+'ABCD'[:i%4]
        order.extend(case+'-'+arm for arm in rotation)
    return {'stage':stage,'cases_root':str(safe_path(Path(cases_root))), 'case_ids':ids,
            'order':order,'budgets':deepcopy(budgets),'models':model_config,
            'scene_grounding_version':SCENE_GROUNDING_VERSION if scene_grounding else None}


def bindings(configuration=None):
    # Only executable/runtime/public-input bindings affect this development
    # stage admission. Mutable reports and human annotations are excluded.
    files=[p for p in Path(__file__).parent.rglob('*') if p.is_file() and p.suffix in {'.py','.mjs','.html'}]
    files += list((REPO/'src/text2ifc_ifc_repair').rglob('*.py'))
    files += list((REPO/'src/text2ifc_agent').rglob('*.py'))
    files += list((REPO/'prompts/agent').rglob('*.json'))
    files += list((REPO/'schemas/agent').rglob('*.json'))
    file_bindings={p.relative_to(REPO).as_posix():sha256(p) for p in sorted(set(files))}
    cases_root=Path(configuration['cases_root']) if configuration else CASES
    case_ids=configuration['case_ids'] if configuration else ('case-001','case-002')
    for case in case_ids:
        for name in sorted(PUBLIC_FILES):
            path=safe_path(cases_root/case/'public'/name)
            key=f'public/{case}/{name}' if configuration else path.relative_to(REPO).as_posix()
            file_bindings[key]=sha256(path)
    return {'files':file_bindings,
            'images':{image:docker('image','inspect',image,'--format','{{.Id}}') for image in (IMAGE,DSH_IMAGE)},
            'models':configuration['models'] if configuration else MODELS,
            **({'budgets':configuration['budgets']} if configuration else {'budget':BUDGET})}


def verify_admission(path, configuration=None):
    if path is None:raise ValueError('CURRENT_STAGE_ADMISSION_REQUIRED')
    value=read_json(safe_path(Path(path)))
    stage=configuration['stage'] if configuration else DEMO_STAGE
    if value.get('stage')!=stage or value.get('passed') is not True:
        raise ValueError('CURRENT_STAGE_ADMISSION_REQUIRED')
    if configuration is not None and value.get('configuration')!=configuration:
        raise ValueError('CURRENT_CONFIGURATION_ADMISSION_REQUIRED')
    if value.get('bindings')!=(bindings(configuration) if configuration else bindings()):
        raise ValueError('CURRENT_STAGE_ADMISSION_REQUIRED')
    return value


def validate_configuration(config):
    """Reject drift between persisted batch authority and runtime convenience fields."""
    configuration=config.get('configuration')
    if config.get('mode') not in {'offline','live'}:raise ValueError('INVALID_EXPERIMENT_MODE')
    if configuration is None:
        if config.get('stage',DEMO_STAGE)!=DEMO_STAGE:
            raise ValueError('BATCH_CONFIGURATION_REQUIRED')
        return None
    normalized=batch_configuration(cases_root=configuration['cases_root'],case_ids=configuration['case_ids'],
        budgets=configuration['budgets'],stage=configuration['stage'],models=configuration['models'],
        scene_grounding=configuration.get('scene_grounding_version')==SCENE_GROUNDING_VERSION)
    if normalized!=configuration or any(config.get(k)!=configuration[k] for k in ('stage','cases_root','case_ids','order','budgets','models')):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    if config.get('scene_grounding_version')!=configuration['scene_grounding_version'] or set(config['routes'])!=set(configuration['order']):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    return configuration


def initialize(root,*,mode,admission=None,scene_grounding=False,arms=None,
               cases_root=None,case_ids=None,budgets=None,stage=DEMO_STAGE,models=None):
    root=safe_path(Path(root))
    if mode not in {'offline','live'}:raise ValueError('INVALID_EXPERIMENT_MODE')
    explicit=any(v is not None for v in (cases_root,case_ids,budgets,models)) or stage!=DEMO_STAGE
    configuration=None
    if explicit:
        if any(v is None for v in (cases_root,case_ids,budgets)):
            raise ValueError('COMPLETE_BATCH_CONFIGURATION_REQUIRED')
        if arms is not None and list(arms)!=list('ABCD'):
            raise ValueError('BATCH_REQUIRES_FOUR_ARMS')
        configuration=batch_configuration(cases_root=cases_root,case_ids=case_ids,budgets=budgets,
            stage=stage,models=models,scene_grounding=scene_grounding)
    if mode=='live':
        admitted=verify_admission(admission,configuration) if configuration else verify_admission(admission)
        if configuration is None and scene_grounding and admitted.get('scene_grounding_version')!=SCENE_GROUNDING_VERSION:
            raise ValueError('SCENE_METHOD_ADMISSION_REQUIRED')
    selected=list('ABCD') if arms is None else list(arms)
    if not selected or len(set(selected))!=len(selected) or set(selected)-set('ABCD'):
        raise ValueError('INVALID_EXPERIMENT_ARMS')
    order=configuration['order'] if configuration else [r for r in ORDER if r[-1] in selected]
    if mode=='live' and admitted.get('authorized_arms') and set(selected)-set(admitted['authorized_arms']):
        raise ValueError('ARM_OUTSIDE_STAGE_ADMISSION')
    if (root/'experiment.json').exists():raise ValueError('EXPERIMENT_EXISTS_USE_STATUS_OR_RESUME')
    public_root=Path(configuration['cases_root']) if configuration else CASES
    for case_id in (configuration['case_ids'] if configuration else sorted({r.rsplit('-',1)[0] for r in order})):
        public=safe_path(public_root/case_id/'public')
        if set(p.name for p in public.iterdir())!=PUBLIC_FILES:
            raise ValueError('PUBLIC_FILE_ALLOWLIST_MISMATCH')
        for name in PUBLIC_FILES:safe_path(public/name)
    root.mkdir(parents=True,exist_ok=True)
    suffix=uuid.uuid4().hex[:10]
    config={'mode':mode,'order':order,'models':MODELS,'budget':BUDGET,
            'network':'repair-demo-'+suffix,'relay':'repair-relay-'+suffix,
            'admission':str(Path(admission).resolve()) if admission else None,'routes':{}}
    if scene_grounding:
        config['scene_grounding_version']=SCENE_GROUNDING_VERSION
    if configuration:
        config.update(deepcopy(configuration))
        config['configuration']=deepcopy(configuration)
        config.pop('budget')
    bundle=root/'runtime/b'
    build_runtime_bundle(REPO,bundle)
    for run_id in order:
        case_id,arm=run_id.rsplit('-',1)
        config['routes'][run_id]={'token':uuid.uuid4().hex,'container':'repair-'+suffix+'-'+run_id.lower(),
                                'volume':'repair-state-'+suffix+'-'+run_id.lower()}
        budget=configuration['budgets'][case_id] if configuration else BUDGET
        DirectRunner.create(public_root/case_id/'public',root,case_id=case_id,arm=arm,budget=budget,
                            mode=('live_formal' if stage==FORMAL_STAGE else 'live_development') if mode=='live' else 'real_runtime_fake_model',
                            runtime_metadata={'model_requested':config['models'][arm],'arm':arm,'image':DSH_IMAGE if arm=='D' else IMAGE,
                                'stage':stage,
                                **({'scene_grounding_version':SCENE_GROUNDING_VERSION} if scene_grounding and arm=='B' else {})})
    write_json(root/'experiment.json',config)
    return config


def native_quiescent(name,packet=None):
    script=QUIESCENT_SCRIPT
    if packet and packet.get('sessionId'):
        script=script.replace("children=json.loads(activity.read_text()).get('active_child_sessions',[])",
            "children=[s for s in json.loads(activity.read_text()).get('active_child_sessions',[]) if s != "+repr(packet['sessionId'])+"]")
    try:return json.loads(docker('exec',name,'python','-c',script,timeout=10))['quiescent']
    except (RuntimeError,subprocess.TimeoutExpired,ValueError):return False


def _service_idle(config,ledger):
    for run_id in config['order']:
        state=ledger.snapshot(run_id)
        if state['arm']=='D' and state['status']=='awaiting_user':
            raise ValueError('D_COLD_RESUME_UNSUPPORTED_KEEP_WARM_SERVICE')
        if state['status']=='running' or state['activities'] or any(c['state']=='inflight' for c in ledger.calls(run_id)):
            raise ValueError('ACTIVE_TASK_PREVENTS_SERVICE_RESTART_OR_STOP')


def prepare_service_start(root,config,ledger):
    """Consume a completed service's stop marker, never an active task's state."""
    root=Path(root)
    with task_owner(root,'service-transition'):
        _service_idle(config,ledger)
        prior=read_json(root/'service.json') if (root/'service.json').exists() else None
        if prior and prior.get('state')!='stopped':
            raise ValueError('SERVICE_RECOVERY_REQUIRED_NO_AUTOMATIC_RESTART')
        marker=safe_path(root/'stop-service')
        if marker.exists():marker.unlink()


def request_service_stop(root):
    """Stop an idle gateway; this deliberately does not cancel a task."""
    root=safe_path(Path(root))
    config=read_json(root/'experiment.json')
    validate_configuration(config)
    with task_owner(root,'service-transition'):
        _service_idle(config,Ledger(root/'control.sqlite'))
        (root/'stop-service').write_text('stop',encoding='utf8')
    return {'requested':True}


def serve(root):
    root=safe_path(Path(root))
    with task_owner(root,'gateway-service'):
        return _serve_owned(root)


def _serve_owned(root):
    config=read_json(root/'experiment.json')
    configuration=validate_configuration(config)
    ledger=Ledger(root/'control.sqlite')
    if config['mode']=='live':
        verify_admission(config['admission'],configuration) if configuration else verify_admission(config['admission'])
    prepare_service_start(root,config,ledger)
    if config['mode']=='live':
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
            gateway.register(run_id,token=row['token'],model=config['models'][arm],api_key=key,
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


def d_failure_terminal(ledger, run_id, detail):
    """Classify native failure from task-bound controller evidence only.

    DSH exposes a controller HTTP 403 as an authentication error. A recent
    budget refusal is therefore authoritative; an SDK error string is not.
    A later reservation makes an earlier refusal stale for this purpose.
    """
    for event in reversed(ledger.events(run_id)):
        if event['kind'] == 'request_reserved':
            break
        if event['kind'] == 'controller_request_rejected':
            payload = event['payload']
            if (payload.get('origin') == 'repair-controller'
                and payload.get('wire_protocol') == 'messages'
                and payload.get('error') in {
                    'TOKEN_BUDGET_EXHAUSTED', 'CALL_BUDGET_EXHAUSTED',
                    'TIME_BUDGET_EXHAUSTED'}):
                return 'budget_exhausted', payload['error']
            break
    if detail == 'ACTIVE_TIME_BUDGET_EXHAUSTED':
        state = ledger.snapshot(run_id)
        if state['active_elapsed_s'] >= state['limits']['active_seconds']:
            return 'budget_exhausted', detail
    return 'runtime_error', detail


def run_owned(root,run_id):
    root=safe_path(Path(root))
    config=read_json(root/'experiment.json')
    configuration=validate_configuration(config)
    if config['mode']=='live':
        verify_admission(config['admission'],configuration) if configuration else verify_admission(config['admission'])
    route=config['routes'][run_id]
    service=read_json(root/'service.json')
    if service['state']!='running':raise ValueError('GATEWAY_SERVICE_NOT_RUNNING')
    runner=DirectRunner(root,run_id)
    state=runner.ledger.snapshot(run_id)
    expected_mode=('live_formal' if config.get('stage')==FORMAL_STAGE else 'live_development') if config['mode']=='live' else 'real_runtime_fake_model'
    if configuration and (state['budget']!=configuration['budgets'][state['case_id']]
                          or state['metadata']['runtime']['model_requested']!=configuration['models'][state['arm']]
                          or state['mode']!=expected_mode):
        raise ValueError('LEDGER_CONFIGURATION_CHANGED')
    if state['status'] in TERMINAL or state['status']=='awaiting_user':return state
    arm=state['arm']
    with task_owner(root,'service-transition'):
        if (root/'stop-service').exists():raise ValueError('SERVICE_STOPPING_NO_NEW_TASK')
        if state['status']=='ready':runner.ledger.start(run_id)
    base='http://repair-gateway:8000/'+route['token']
    if arm in {'A','C'}:
        engine=ChatExecutor(root,run_id,gateway_url=service['url']+'/'+route['token']+'/v1',
                            model=config['models'][arm],evidence_class='live_provider' if config['mode']=='live' else 'real_runtime_fake_model')
        result=engine.run()
        write_json(root/'runtime'/(run_id+'-commands.json'),engine.tools.records)
        return result
    state=runner.ledger.snapshot(run_id)
    if state['activities'] or any(c['state']=='inflight' for c in runner.ledger.calls(run_id)):
        raise ValueError('RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
    if arm=='B':
        remaining=state['limits']['active_seconds']-state['active_elapsed_s']
        if remaining<=0:return runner.ledger.finish(run_id,'budget_exhausted',detail='TIME_BUDGET_EXHAUSTED')
        cfg=IsolatedBConfig(root/'runtime/b',runner.workspace,route['volume'],config['network'],base+'/v1',
                            container_name=route['container'],evidence_class='live' if config['mode']=='live' else 'deterministic_fake_http',
                            timeout_seconds=remaining,model=config['models']['B'],
                            scene_grounding=config.get('scene_grounding_version')==SCENE_GROUNDING_VERSION)
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
            status='budget_exhausted' if result.get('error')=='WORKER_TIMEOUT' else 'runtime_error'
            return runner.ledger.finish(run_id,status,detail=result.get('error','native worker failure'))
        if native.get('clarification'):
            question=native['clarification']
            return runner.ledger.ask(run_id,question_id=question['clarification_id'],
                text=json.dumps(question,ensure_ascii=False),binding={'native_question':question,'state_version':native['state_version']})
        export=root/'runtime'/run_id
        worker.export_state(export)
        if result['artifact_relative']:return runner.submit(result['artifact_relative'])
        return runner.ledger.finish(run_id,'unsupported' if native['status']=='unsupported' else 'cancelled' if native['status']=='cancelled' else 'no_output',detail=native.get('status'))
    if any(e['kind']=='d_native_started' for e in runner.ledger.events(run_id)):
        raise ValueError('D_COLD_RESUME_UNSUPPORTED_NO_AUTOMATIC_RESTART')
    runner.ledger.record(run_id,'d_native_started',{'state_volume':route['volume']},event_id='d-native-started')
    carrier=NativeDSH(runner.workspace,root/'runtime'/run_id,name=route['container'],
        state_volume=route['volume'],network=config['network'],base_url=base,model=config['models']['D'],session_id=run_id)
    result=carrier.run(ledger=runner.ledger,run_id=run_id)
    runner.ledger.record(run_id,'isolated_native_return',result)
    runner.ledger.set_native(run_id,{'result':result,'state_volume':route['volume']})
    if not result['ok']:
        status, detail = d_failure_terminal(runner.ledger, run_id, result.get('error'))
        return runner.ledger.finish(run_id, status, detail=detail)
    native=result['result']
    if native['finish_reason']=='error':
        status, detail = d_failure_terminal(runner.ledger, run_id, 'native turn ended with error')
        return runner.ledger.finish(run_id, status, detail=detail)
    try:path=submitted_path(native['final_response'])
    except ValueError as error:return runner.ledger.finish(run_id,'runtime_error',detail=str(error))
    if path:return runner.submit(path)
    return runner.ledger.finish(run_id,'no_output',detail='no explicit native IFC submission')


def answer(root,run_id,value):
    root=safe_path(Path(root))
    config=read_json(root/'experiment.json')
    configuration=validate_configuration(config)
    if config['mode']=='live':
        verify_admission(config['admission'],configuration) if configuration else verify_admission(config['admission'])
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
        service=read_json(root/'service.json')
        if service.get('state')!='running' or (root/'stop-service').exists():
            raise ValueError('D_COLD_RESUME_UNSUPPORTED_KEEP_WARM_SERVICE')
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
    with task_owner(root,'service-transition'):
        if (root/'stop-service').exists():raise ValueError('SERVICE_STOPPING_NO_NEW_TASK')
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
    parser.add_argument('--scene-grounding',action='store_true')
    parser.add_argument('--arms',nargs='+',choices=list('ABCD'))
    parser.add_argument('--cases-root',type=Path)
    parser.add_argument('--case-ids',nargs='+')
    parser.add_argument('--budgets',type=Path)
    parser.add_argument('--models',type=Path)
    parser.add_argument('--stage',choices=[DEMO_STAGE,FORMAL_STAGE],default=DEMO_STAGE)
    args=parser.parse_args()
    if args.command=='init':value=initialize(args.root,mode=args.mode,admission=args.admission,
                                          scene_grounding=args.scene_grounding,arms=args.arms,
                                          cases_root=args.cases_root,case_ids=args.case_ids,
                                          budgets=read_json(args.budgets) if args.budgets else None,
                                          models=read_json(args.models) if args.models else None,stage=args.stage)
    elif args.command=='serve':serve(args.root);return
    elif args.command=='run':value=run(args.root,args.run_id)
    elif args.command=='answer':value=answer(args.root,args.run_id,read_json(args.answer_file))
    elif args.command=='status':value=status(args.root)
    elif args.command=='stop':value=request_service_stop(args.root)
    else:
        from .scoring import score
        config=read_json(args.root/'experiment.json')
        validate_configuration(config)
        if config.get('stage')==FORMAL_STAGE:
            raise ValueError('FORMAL_SCORING_REQUIRES_FROZEN_EVALUATOR_USE_FORMAL_WORKFLOW')
        reports=[]
        for state in status(args.root):
            result=Path(state['artifact']['path']) if state['artifact'] else None
            report=score(Path(config.get('cases_root',CASES))/state['case_id'],result,terminal=state['status'],events=Ledger(args.root/'control.sqlite').events(state['run_id']))
            reports.append({'run_id':state['run_id'],'state':state,'evaluation':report})
        write_json(args.root/'checks.json',reports);value=reports
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
