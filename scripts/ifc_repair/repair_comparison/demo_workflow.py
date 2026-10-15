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
from .isolated_b import build_runtime_bundle, IsolatedB, IsolatedBConfig, PROPERTY_RUNTIME_IMAGE
from .isolated_direct import ChatExecutor
from .isolated_dsh import NativeDSH, submitted_path, QUIESCENT_SCRIPT, IMAGE as DSH_IMAGE, validate_web_access, CLARIFICATION_FAILURE
from .ledger import Ledger, TERMINAL
from .wire_gateway import WireGateway
from .dsh_search import validate_search_configuration, search_configuration, search_api_key
from .controller_owner import task_owner
from .group_config import SCALABLE_STAGE, executor, provider as group_provider, harness_profile
from text2ifc_ifc_repair.scene_grounding import SCENE_GROUNDING_VERSION

REPO=Path(__file__).resolve().parents[3]
CASES=REPO/'dataset/processed/ifc-repair/repair-comparison/development'
ORDER=['case-001-A','case-001-B','case-001-C','case-001-D',
       'case-002-B','case-002-C','case-002-D','case-002-A']
BUDGET={'tokens':2500000,'calls':100,'active_seconds':5400,'tool_seconds':120,'extensions':[]}
MODELS={'A':'deepseek-v4-flash','B':'deepseek-v4-flash','C':'gpt-6-sol','D':'deepseek-v4-flash'}
DEMO_STAGE='repair-comparison-two-demo-live'
FORMAL_STAGE='repair-comparison-formal-live'


def batch_configuration(*, cases_root, case_ids, budgets, stage, models=None, scene_grounding=False,
                        b=None, d_web_search=None, b_validation_corrections=None, d_web_access=None,
                        providers=None, case_groups=None):
    """Normalize the exact public task/configuration contract for an admission."""
    if stage == SCALABLE_STAGE:
        from .group_config import scalable_configuration
        return scalable_configuration(cases_root=cases_root,case_ids=case_ids,budgets=budgets,
            providers=providers,case_groups=case_groups,models=models,scene_grounding=scene_grounding,
            b=b,d_web_search=d_web_search,d_web_access=d_web_access,
            b_validation_corrections=2 if b_validation_corrections is None else b_validation_corrections)
    if providers is not None or case_groups is not None:
        raise ValueError('SCALABLE_STAGE_CONFIGURATION_REQUIRED')
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
    result = {'stage':stage,'cases_root':str(safe_path(Path(cases_root))), 'case_ids':ids,
            'order':order,'budgets':deepcopy(budgets),'models':model_config,
            'scene_grounding_version':SCENE_GROUNDING_VERSION if scene_grounding else None}
    if d_web_search is not None:
        result['d_web_search']=validate_search_configuration(d_web_search)
        if result['d_web_search']['model']!=model_config['D']:
            raise ValueError('FROZEN_SEARCH_MODEL_REQUIRED')
    if validate_web_access(d_web_access) is not None:
        result['d_web_access']=d_web_access
    if b_validation_corrections is not None:
        if type(b_validation_corrections) is not int or not 0 <= b_validation_corrections <= 2:
            raise ValueError('VALIDATION_CORRECTION_LIMIT_INVALID')
        result['b_validation_corrections']=b_validation_corrections
    if b is not None:
        if (not isinstance(b,dict) or set(b)!={'image','property_model_directory'}
                or b['image']!=PROPERTY_RUNTIME_IMAGE):
            raise ValueError('PROPERTY_RUNTIME_CONFIGURATION_REQUIRED')
        model=safe_path(Path(b['property_model_directory']))
        if not model.is_dir() or any(not (model/name).is_file() for name in ('config.json','modules.json')):
            raise ValueError('PROPERTY_RUNTIME_MODEL_REQUIRED')
        result['b']={'image':PROPERTY_RUNTIME_IMAGE,'property_model_directory':str(model)}
    return result


def bindings(configuration=None):
    # Only executable/runtime/public-input bindings affect this development
    # stage admission. Mutable reports and human annotations are excluded.
    files=[p for p in Path(__file__).parent.rglob('*') if p.is_file() and p.suffix in {'.py','.mjs','.html'}]
    files += list((REPO/'src/text2ifc_ifc_repair').rglob('*.py'))
    files += list((REPO/'src/text2ifc_agent').rglob('*.py'))
    files += list((REPO/'prompts/agent').rglob('*.json'))
    files += list((REPO/'schemas/agent').rglob('*.json'))
    if configuration and configuration.get('b'):
        files += list((REPO/'src/text2ifc_knowledge').rglob('*.py'))
        files += list((REPO/'schemas/ifc/knowledge').rglob('*.json'))
    file_bindings={p.relative_to(REPO).as_posix():sha256(p) for p in sorted(set(files))}
    cases_root=Path(configuration['cases_root']) if configuration else CASES
    case_ids=configuration['case_ids'] if configuration else ('case-001','case-002')
    for case in case_ids:
        for name in sorted(PUBLIC_FILES):
            path=safe_path(cases_root/case/'public'/name)
            key=f'public/{case}/{name}' if configuration else path.relative_to(REPO).as_posix()
            file_bindings[key]=sha256(path)
    images=[IMAGE,DSH_IMAGE]
    if configuration and configuration.get('b'):
        images.append(configuration['b']['image'])
        model=Path(configuration['b']['property_model_directory'])
        for name in ('config.json','modules.json'):
            file_bindings['b-property-model/'+name]=sha256(model/name)
    return {'files':file_bindings,
            'images':{image:docker('image','inspect',image,'--format','{{.Id}}') for image in images},
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
        scene_grounding=configuration.get('scene_grounding_version')==SCENE_GROUNDING_VERSION,
        b=configuration.get('b'),d_web_search=configuration.get('d_web_search'),d_web_access=configuration.get('d_web_access'),
        b_validation_corrections=configuration.get('b_validation_corrections'),
        providers=configuration.get('providers'),case_groups=configuration.get('case_groups'))
    if normalized!=configuration or any(config.get(k)!=configuration[k] for k in ('stage','cases_root','case_ids','order','budgets','models')):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    if config.get('scene_grounding_version')!=configuration['scene_grounding_version'] or set(config['routes'])!=set(configuration['order']):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    if config.get('b')!=configuration.get('b'):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    if config.get('d_web_search')!=configuration.get('d_web_search'):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    if config.get('d_web_access')!=configuration.get('d_web_access'):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    if config.get('b_validation_corrections')!=configuration.get('b_validation_corrections'):
        raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    for field in ('providers','case_groups','configuration_version'):
        if config.get(field)!=configuration.get(field):raise ValueError('EXPERIMENT_CONFIGURATION_CHANGED')
    return configuration


def initialize(root,*,mode,admission=None,scene_grounding=False,arms=None,
               cases_root=None,case_ids=None,budgets=None,stage=DEMO_STAGE,models=None,b=None,
               d_web_search=None,b_validation_corrections=None,d_web_access=None,providers=None,case_groups=None):
    root=safe_path(Path(root))
    if mode not in {'offline','live'}:raise ValueError('INVALID_EXPERIMENT_MODE')
    explicit=any(v is not None for v in (cases_root,case_ids,budgets,models,b,d_web_search,b_validation_corrections,d_web_access,providers,case_groups)) or stage!=DEMO_STAGE
    configuration=None
    if explicit:
        if any(v is None for v in (cases_root,case_ids,budgets)):
            raise ValueError('COMPLETE_BATCH_CONFIGURATION_REQUIRED')
        if arms is not None and list(arms)!=list('ABCD') and stage!=SCALABLE_STAGE:
            raise ValueError('BATCH_REQUIRES_FOUR_ARMS')
        configuration=batch_configuration(cases_root=cases_root,case_ids=case_ids,budgets=budgets,
            stage=stage,models=models,scene_grounding=scene_grounding,b=b,d_web_search=d_web_search,
            b_validation_corrections=b_validation_corrections,d_web_access=d_web_access,
            providers=providers,case_groups=case_groups)
    if mode=='live':
        admitted=verify_admission(admission,configuration) if configuration else verify_admission(admission)
        if configuration is None and scene_grounding and admitted.get('scene_grounding_version')!=SCENE_GROUNDING_VERSION:
            raise ValueError('SCENE_METHOD_ADMISSION_REQUIRED')
    selected=sorted({r[-1] for r in configuration['order']}) if stage==SCALABLE_STAGE else list('ABCD') if arms is None else list(arms)
    if not selected or len(set(selected))!=len(selected) or set(selected)-set('ABCDEFG' if stage==SCALABLE_STAGE else 'ABCD'):
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
                            runtime_metadata={'model_requested':config['models'][arm],'arm':arm,
                                'image':DSH_IMAGE if arm=='D' else (configuration['b']['image'] if executor(config,arm)=='harness' and configuration and configuration.get('b') else IMAGE),
                                'stage':stage,
                                **({'scene_grounding_version':SCENE_GROUNDING_VERSION} if scene_grounding and executor(config,arm)=='harness' else {})})
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
    with task_owner(root,'service-transition',wait_seconds=10):
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
    with task_owner(root,'service-transition',wait_seconds=10):
        _service_idle(config,Ledger(root/'control.sqlite'))
        (root/'stop-service').write_text('stop',encoding='utf8')
    return {'requested':True}


def serve(root, *, start_id=None):
    root=safe_path(Path(root))
    with task_owner(root,'gateway-service'):
        return _serve_owned(root, start_id=start_id)


def _serve_owned(root, *, start_id=None):
    config=read_json(root/'experiment.json')
    configuration=validate_configuration(config)
    ledger=Ledger(root/'control.sqlite')
    if config['mode']=='live':
        verify_admission(config['admission'],configuration) if configuration else verify_admission(config['admission'])
    prepare_service_start(root,config,ledger)
    if config['mode']=='live':
        from dotenv import dotenv_values
        env=dotenv_values(REPO/'.env')
        keys={'C':env.get('OPENAI_API_KEY'),'deepseek':env.get('DEEPSEEK_API_KEY')}
        upstream={'C':env.get('OPENAI_EXPERIMENT_BASE_URL','').rstrip('/')+'/chat/completions',
                  'deepseek':env.get('OPENAI_BASE_URL','https://api.deepseek.com').rstrip('/')+'/chat/completions',
                  'messages':'https://api.deepseek.com/anthropic/v1/messages'}
        transport=None
        search_key=search_api_key(env,config['d_web_search']) if config.get('d_web_search') else None
    else:
        from tests.ifc_repair.repair_comparison.demo_http_fixture import FakeDemoTransport
        transport=httpx.MockTransport(FakeDemoTransport(root,config))
        keys={'C':'offline-unused','deepseek':'offline-unused'}
        upstream={'C':'https://offline.invalid','deepseek':'https://offline.invalid','messages':'https://offline.invalid'}
        search_key='offline-search-unused'
    token=uuid.uuid4().hex
    with WireGateway(ledger,root/'wire',transport=transport,control_token=token) as gateway:
        for run_id,row in config['routes'].items():
            arm=run_id[-1]
            profile=group_provider(config,arm) if config.get('stage')==SCALABLE_STAGE else None
            if profile:
                key=None if profile['key_env'] is None else ('offline-unused' if config['mode']=='offline' else env.get(profile['key_env']))
                if config['mode']=='live' and profile['key_env'] and not key:
                    raise ValueError('PROVIDER_KEY_REQUIRED:'+profile['key_env'])
                endpoints={'messages':profile['messages_endpoint']} if arm=='D' else {'chat':profile['chat_endpoint']}
            else:
                key=keys['C' if arm=='C' else 'deepseek']
                endpoints={'messages':upstream['messages']} if arm=='D' else {'chat':upstream['C' if arm=='C' else 'deepseek']}
            if config['mode']=='offline':endpoints={k:'https://offline.invalid/'+run_id+'/'+k for k in endpoints}
            search_settings=deepcopy(config.get('d_web_search')) if arm=='D' else None
            if search_settings and config['mode']=='offline':
                search_settings['endpoint']='https://offline.invalid/'+run_id+'/search/messages'
            gateway.register(run_id,token=row['token'],model=config['models'][arm],api_key=key,
                endpoints=endpoints,evidence_class='live_provider' if config['mode']=='live' else 'real_runtime_fake_model',
                max_output_tokens=profile['max_output_tokens'] if profile else 65536,
                request_options=profile['request_options'] if profile else None,
                quiescent=(lambda packet,name=row['container']:native_quiescent(name,packet)) if arm=='D' else None,
                web_search=search_settings,search_api_key=search_key if search_settings else None)
        docker('network','create','--internal',config['network'])
        relay=Path(__file__).with_name('container_relay.py').resolve()
        page_proxy=Path(__file__).parent/'dsh/web_proxy.py'
        proxy_environment=['--env=REPAIR_WEB_PROXY=1'] if config.get('d_web_access')=='proxy' else []
        port=gateway.server.server_port
        docker('create','--name',config['relay'],'--pull=never','--network=bridge','--read-only',
               '--user=10001:10001','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=256m',
               '--cpus=1','--pids-limit=32','--env',f'REPAIR_CONTROLLER_PORT={port}',
               *proxy_environment,'--mount',f'type=bind,source={page_proxy},target=/opt/web_proxy.py,readonly',
               '--mount',f'type=bind,source={relay},target=/opt/relay.py,readonly',IMAGE,'python','/opt/relay.py')
        docker('network','connect','--alias','repair-gateway',config['network'],config['relay'])
        docker('start',config['relay'])
        write_json(root/'service.json',{'url':gateway.url,'control_token':token,'pid':os.getpid(),
                   'network':config['network'],'relay':config['relay'],'state':'running',
                   **({'start_id':start_id} if start_id is not None else {})})
        print('REPAIR_SERVICE_READY '+gateway.url,flush=True)
        try:
            while not (root/'stop-service').exists():time.sleep(.2)
        finally:
            docker('stop','--time','2',config['relay'])
            docker('rm',config['relay'])
            docker('network','rm',config['network'])
            write_json(root/'service.json',{'url':gateway.url,'state':'stopped'})


def run(root,run_id):
    config=read_json(Path(root)/'experiment.json')
    if executor(config,run_id[-1])=='direct':return run_owned(root,run_id)
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


def _harness_native_record(result, volume):
    from text2ifc_ifc_repair.scene_diagnostics import checked_scene_diagnostics
    diagnostics = checked_scene_diagnostics(result.get('scene_diagnostics'))
    return {'result': result.get('result', {}), 'state_volume': volume,
            **({'scene_diagnostics': diagnostics} if diagnostics is not None else {})}


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
    with task_owner(root,'service-transition',wait_seconds=10):
        if (root/'stop-service').exists():raise ValueError('SERVICE_STOPPING_NO_NEW_TASK')
        if state['status']=='ready':runner.ledger.start(run_id)
    base='http://repair-gateway:8000/'+route['token']
    if executor(config,arm)=='direct':
        engine=ChatExecutor(root,run_id,gateway_url=service['url']+'/'+route['token']+'/v1',
                            model=config['models'][arm],evidence_class='live_provider' if config['mode']=='live' else 'real_runtime_fake_model',
                            max_output_tokens=group_provider(config,arm)['max_output_tokens'] if config.get('stage')==SCALABLE_STAGE else 65536)
        result=engine.run()
        write_json(root/'runtime'/(run_id+'-commands.json'),engine.tools.records)
        return result
    state=runner.ledger.snapshot(run_id)
    if state['activities'] or any(c['state']=='inflight' for c in runner.ledger.calls(run_id)):
        raise ValueError('RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
    if executor(config,arm)=='harness':
        remaining=state['limits']['active_seconds']-state['active_elapsed_s']
        if remaining<=0:return runner.ledger.finish(run_id,'budget_exhausted',detail='TIME_BUDGET_EXHAUSTED')
        cfg=IsolatedBConfig(root/'runtime/b',runner.workspace,route['volume'],config['network'],base+'/v1',
                            image=config.get('b',{}).get('image','text2ifc/repair-tools:py312-ifc085-v2'),
                            property_model_directory=config.get('b',{}).get('property_model_directory'),
                            container_name=route['container'],evidence_class='live' if config['mode']=='live' else 'deterministic_fake_http',
                            timeout_seconds=remaining,model=config['models'][arm],
                            model_profile=harness_profile(config,arm) if config.get('stage')==SCALABLE_STAGE else None,
                            max_validation_corrections=config.get('b_validation_corrections',0),
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
        runner.ledger.set_native(run_id,_harness_native_record(result,route['volume']))
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
        state_volume=route['volume'],network=config['network'],base_url=base,model=config['models']['D'],session_id=run_id,
        web_search=config.get('d_web_search'),web_access=config.get('d_web_access'))
    result=carrier.run(ledger=runner.ledger,run_id=run_id)
    runner.ledger.record(run_id,'isolated_native_return',result)
    if result.get('error') == CLARIFICATION_FAILURE:
        state=runner.ledger.snapshot(run_id)
        if (result.get('container_stopped') is True and state['status']=='awaiting_user'
                and result.get('question_id') == (state.get('question') or {}).get('question_id')):
            return runner.ledger.finish(run_id,'no_output',detail=CLARIFICATION_FAILURE)
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


def request_clarification_stop(root,run_id,question_id):
    """Ask the warm D owner to stop; do not answer or mark an active task done."""
    root=safe_path(Path(root))
    ledger=Ledger(root/'control.sqlite')
    state=ledger.snapshot(run_id)
    if (state['arm']!='D' or state['status']!='awaiting_user'
            or (state.get('question') or {}).get('question_id')!=question_id):
        raise ValueError('CLARIFICATION_STOP_QUESTION_BINDING_CHANGED')
    if state['activities'] or any(c['state']=='inflight' for c in ledger.calls(run_id)):
        raise ValueError('CLARIFICATION_STOP_REQUIRES_QUIESCENCE')
    marker=safe_path(root/'runtime'/run_id/'stop-clarification.json')
    payload={'run_id':run_id,'question_id':question_id,'reason':CLARIFICATION_FAILURE}
    if marker.exists():
        if read_json(marker)!=payload:
            raise ValueError('CLARIFICATION_STOP_QUESTION_BINDING_CHANGED')
        return
    marker.parent.mkdir(parents=True,exist_ok=True)
    pending=safe_path(marker.with_suffix('.pending.json'))
    write_json(pending,payload)
    ledger.record(run_id,'clarification_stop_requested',payload,
                  event_id='clarification-stop:'+question_id)
    pending.replace(marker)


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
    if executor(config,state['arm'])=='harness':
        native_answer=value.get('native_answer',{'kind':'add_detail','detail':text})
        native=binding['native_question']
        jsonschema.Draft202012Validator(native['answer_schema']).validate(native_answer)
        if native_answer.get('kind')=='select_candidate' and native_answer.get('candidate_token') not in {c['candidate_token'] for c in native['candidates']}:
            raise ValueError('CANDIDATE_NOT_OFFERED')
    with task_owner(root,'service-transition',wait_seconds=10):
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
    parser.add_argument('--service-start-id', help=argparse.SUPPRESS)
    parser.add_argument('--answer-file',type=Path)
    parser.add_argument('--scene-grounding',action='store_true')
    parser.add_argument('--arms',nargs='+',choices=list('ABCD'))
    parser.add_argument('--cases-root',type=Path)
    parser.add_argument('--case-ids',nargs='+')
    parser.add_argument('--budgets',type=Path)
    parser.add_argument('--models',type=Path)
    parser.add_argument('--d-web-search',action='store_true',help='Freeze native DSH search settings for this new batch')
    parser.add_argument('--d-web-access',choices=['proxy'],help='Enable native DSH public-page access for this new batch')
    parser.add_argument('--b-validation-corrections',type=int,choices=(0,1,2),
        help='Explicit final-validation correction allowance; legacy batches remain unchanged')
    parser.add_argument('--stage',choices=[DEMO_STAGE,FORMAL_STAGE],default=DEMO_STAGE)
    args=parser.parse_args()
    if args.command=='init':value=initialize(args.root,mode=args.mode,admission=args.admission,
                                          scene_grounding=args.scene_grounding,arms=args.arms,
                                          cases_root=args.cases_root,case_ids=args.case_ids,
                                          budgets=read_json(args.budgets) if args.budgets else None,
                                          models=read_json(args.models) if args.models else None,stage=args.stage,
                                          d_web_search=search_configuration(os.environ)
                                              if args.d_web_search else None,
                                          b_validation_corrections=args.b_validation_corrections,d_web_access=args.d_web_access)
    elif args.command=='serve':serve(args.root,start_id=args.service_start_id);return
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
