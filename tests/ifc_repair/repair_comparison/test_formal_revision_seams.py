"""Five real Docker/SDK paths; only the controller upstream is deterministic.

B cleanup is delayed only long enough to inspect each genuinely stopped worker.
No repair runtime, SDK, tool, request, or publication result is mocked.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import httpx
import ifcopenshell
import ifcopenshell.validate
import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json, sha256
from scripts.ifc_repair.repair_comparison.direct_runner import SUBMISSION_PROFILE, SUBMISSION_PROFILES
from scripts.ifc_repair.repair_comparison.formal_admission import capture_sources, file_ref
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider, scene
from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs, _FormalHTTPTransport


B_REQUEST = 'Fill one of the two empty openings with a 900 by 2100 mm door. Use the retained door as the frame and finish reference; align the door base with the opening base.'
B_ANSWER = 'Fill the opening whose plan centre is X=1950, Y=2075 millimetres. Leave the other empty opening unchanged.'


class ClarifyingDoorProvider(PublicOnlyProvider):
    """Authored public confirmation, then the ordinary offered-reference fixture."""
    def __init__(self):
        super().__init__()
        self.asked = False

    def generate_candidate(self, **kwargs):
        from text2ifc_agent.providers import ProviderOutput
        result = super().generate_candidate(**kwargs)
        value = json.loads(result.text)
        if value.get('kind') == 'intent':
            from scripts.ifc_repair.repair_comparison.ours_adapter import _section
            records = _section(kwargs['prompt'],'Read-only query results so far')[0]['records']
            candidates = [r for r in records if r['ifc_class']=='IfcOpeningElement' and not r['filling_ids']]
            assert len(candidates)==2
            if not self.asked:
                self.asked = True
                value['intent']['operations'][0]['target_query']['names'] = [candidates[0]['name']]
                value = {'kind':'clarification', 'intent':value['intent'], 'reason':'ambiguous_target',
                    'question':'Should I fill the opening centred at X=1950, Y=2075 mm or X=3450, Y=2075 mm?',
                    'candidate_ids':[r['id'] for r in candidates]}
            else:
                assert '1950' in kwargs['prompt']
                target = next(r for r in candidates if r['center_world_mm'][0]==pytest.approx(1950.))
                value['bindings'][0]['target_id'] = target['id']
            return ProviderOutput(text=json.dumps(value), metadata=result.metadata)
        return result


def _door_source(folder):
    folder.mkdir(parents=True, exist_ok=True)
    model, opening, reference, _, unit = scene(overhang=60., sign=1., angle=0., millimetres=False)
    from ifcopenshell.util.element import copy, copy_deep
    from text2ifc_ifc_repair.operations.hosted_opening import local_placement
    wall=opening.VoidsElements[0].RelatingBuildingElement
    other=copy(model,opening)
    other.Representation=copy_deep(model,opening.Representation,exclude=('IfcGeometricRepresentationContext',))
    other.ObjectPlacement=local_placement(model,relative_to=wall.ObjectPlacement,location=(2000*unit,0.,0.))
    model.createIfcRelVoidsElement(ifcopenshell.guid.new(),opening.OwnerHistory,None,None,wall,other)
    model.write(str(folder/'model.ifc'))
    (folder/'request.txt').write_text(B_REQUEST, encoding='utf8')
    return {'opening':opening.GlobalId, 'reference':reference.GlobalId, 'unit':unit}


def _inspect_door(path, bindings):
    model = ifcopenshell.open(str(path))
    created = [d for d in model.by_type('IfcDoor') if d.GlobalId != bindings['reference']]
    assert len(created) == 1
    door = created[0]
    assert door.FillsVoids[0].RelatingOpeningElement.GlobalId == bindings['opening']
    offset = door.ObjectPlacement.RelativePlacement.Location.Coordinates[1]/bindings['unit']
    assert offset == pytest.approx(75.), 'Asymmetric hardware must not shift the frame to 45 mm.'
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    assert not logger.statements, logger.statements[:3]
    return {'frame_normal_offset_mm':offset, 'native_schema_express':True}


def test_revision_door_public_api_fixture_confirms_then_preserves_anchor(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    public = tmp_path/'public'
    binding = _door_source(public)
    source = public/'model.ifc'
    before = sha256(source)
    api = RepairAPI(tmp_path/'native', provider=ClarifyingDoorProvider(), scene_grounding=True)
    waiting = api.start(source, B_REQUEST)
    assert waiting.status == 'clarification_required', waiting.to_dict()
    result = api.continue_with_answer(waiting.run_id, {'kind':'add_detail','detail':B_ANSWER},
        clarification_id=waiting.clarification.clarification_id, expected_state_version=waiting.state_version)
    assert result.successful_artifact_publishable, result.to_dict()
    _inspect_door(tmp_path/'native'/result.run_directory/result.artifacts['successful_ifc'], binding)
    assert sha256(source) == before


class RevisionTransport(_FormalHTTPTransport):
    def __call__(self, request):
        from tests.ifc_repair.repair_comparison.dsh_fake_gateway import chunks
        run_id = request.url.path.strip('/').split('/')[0]
        body = json.loads(request.content)
        case, arm = run_id.rsplit('-', 1)
        if arm in {'A','C'}:
            system = [m for m in body['messages'] if m['role']=='system']
            assert system == [SUBMISSION_PROFILES[SUBMISSION_PROFILE]]
            response = super().__call__(request)
        elif arm == 'B':
            provider = self.providers.setdefault(run_id, ClarifyingDoorProvider())
            value = provider.generate_candidate(prompt=body['messages'][0]['content']).text
            response = httpx.Response(200, json={'id':'offline-anchor', 'model':body['model'],
                'choices':[{'index':0,'message':{'role':'assistant','content':value},'finish_reason':'stop'}],
                'usage':{'prompt_tokens':11,'completion_tokens':7,'total_tokens':18}})
        elif case == 'synthetic-003':
            assert self.counts.get(run_id,0) == 0, 'The second Messages request must be refused by the controller.'
            self.counts[run_id] = 1
            events = chunks(tool=('bash', {'command':'mkdir -p work && printf NATIVE_TOOL_DONE > work/native-tool-completed.txt',
                'description':'Offline native tool completion before call-budget refusal','timeoutMs':30000}, 'native-budget-tool'))
            response = httpx.Response(200, headers={'Content-Type':'text/event-stream'},
                content=''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode())
        else:
            assert case == 'synthetic-004' and arm == 'D'
            response = httpx.Response(403,json={'type':'error','error':{'type':'authentication_error','message':'OFFLINE_UPSTREAM_FORBIDDEN'}})
        path = self.root/'runtime/revision-upstream.jsonl'
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a',encoding='utf8') as handle:
            handle.write(json.dumps({'run_id':run_id,'request':body,'response_status':response.status_code,
                'response_body':response.content.decode('utf8'),'evidence_class':'deterministic_controller_upstream'},ensure_ascii=False)+'\n')
        return response


def revision_fixture_cli():
    """Original public CLI with one fake upstream and delayed B cleanup."""
    from scripts.ifc_repair.repair_comparison.isolated_b import IsolatedB
    from tests.ifc_repair.repair_comparison import test_batch_workflow as base
    original_argv, original_execute = IsolatedB.docker_argv, IsolatedB.execute
    def retained_argv(worker):
        argv = original_argv(worker)
        assert argv.count('--rm') == 1
        return [arg for arg in argv if arg != '--rm']
    def observed_execute(worker, action, run_id, **kwargs):
        result = original_execute(worker, action, run_id, **kwargs)
        info = json.loads(carrier.docker('inspect', worker.config.container_name))[0]
        path = Path(worker.config.workspace).parents[1]/'runtime'/f'{run_id}-{action}-container.json'
        write_json(path, info)
        assert not info['State']['Running'] and info['State']['Pid']==0
        carrier.docker('rm', worker.config.container_name)
        return result
    IsolatedB.docker_argv, IsolatedB.execute = retained_argv, observed_execute
    base._FormalHTTPTransport = RevisionTransport
    base._formal_fixture_cli()


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER')!='1',reason='explicit keyless revision Docker/SDK validation')
def test_formal_revision_real_native_five_paths(tmp_path):
    before = capture_sources('admission')
    cases, ids, budgets = _formal_public_inputs(tmp_path)
    door_binding = _door_source(cases/'synthetic-002/public')
    shutil.copytree(cases/'synthetic-001', cases/'synthetic-004')
    ids.append('synthetic-004')
    budgets['synthetic-003'] = {**budgets['synthetic-003'], 'calls':1,'active_seconds':180,'tool_seconds':30}
    budgets['synthetic-004'] = {**budgets['synthetic-001'], 'active_seconds':180}
    budget_path = tmp_path/'budgets.json'
    write_json(budget_path, budgets)
    root = tmp_path/'experiment'
    logs = tmp_path/'logs';logs.mkdir()
    command = [sys.executable,'-c','from tests.ifc_repair.repair_comparison.test_formal_revision_seams import revision_fixture_cli; revision_fixture_cli()']
    commands = []
    def call(action, *arguments, timeout=600):
        argv = command+[action,'--root',str(root),*map(str,arguments)]
        response = subprocess.run(argv,cwd=carrier.REPO,capture_output=True,text=True,encoding='utf8',timeout=timeout)
        log = logs/f'{len(commands):02d}-{action}.log'
        log.write_text(response.stdout+'\nSTDERR\n'+response.stderr,encoding='utf8')
        commands.append({'argv':argv,'exit_code':response.returncode,'log':file_ref(log)})
        assert response.returncode==0, (action,response.stdout[-3000:],response.stderr[-3000:])
        return json.loads(response.stdout)
    config = call('init','--mode','offline','--cases-root',cases,'--case-ids',*ids,'--budgets',budget_path,
        '--stage',carrier.FORMAL_STAGE,'--scene-grounding')
    report = {'schema_version':'repair-comparison-revision-seams/0.1','real_models_called':False,
        'source_bindings':before,'configuration':config['configuration'],
        'images':carrier.bindings(config['configuration'])['images'],'runs':[],
        'instrumentation':'B docker --rm delayed until real stopped-container inspect, then fixture cleanup; all worker commands/network/runtime unchanged.'}
    evidence = tmp_path/'revision-native-seams.json'
    write_json(evidence,report)
    service_log = (logs/'service.log').open('wb')
    service = subprocess.Popen(command+['serve','--root',str(root)],cwd=carrier.REPO,stdout=service_log,stderr=subprocess.STDOUT)
    ledger = Ledger(root/'control.sqlite')
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists() or read_json(root/'service.json').get('state')!='running':
            assert service.poll() is None and time.monotonic()<deadline, 'Fixture service failed to start.'
            time.sleep(.25)
        for run_id in ['synthetic-001-A','synthetic-001-C','synthetic-002-B','synthetic-003-D','synthetic-004-D']:
            state = call('run','--run-id',run_id,timeout=300)
            case,arm=run_id.rsplit('-',1)
            row={'family':{'A':'AC','C':'AC','B':'B','D':'D'}[arm], 'run_id':run_id,
                'experiment_root':str(root.resolve()),'public_source':file_ref(cases/case/'public/model.ifc')}
            if arm=='B':
                assert state['status']=='awaiting_user',state
                native_id=state['native']['result']['run_id'];calls=state['usage']['calls']
                question=state['question']['question_id']
                answer=tmp_path/'confirmed-answer.json'
                write_json(answer,{'text':B_ANSWER,'event_id':'preauthored-public-confirmation'})
                call('answer','--run-id',run_id,'--answer-file',answer)
                state=call('run','--run-id',run_id,timeout=300)
                assert state['status']=='submitted' and state['native']['result']['successful_artifact_publishable'],state
                assert state['native']['result']['run_id']==native_id and state['usage']['calls']>calls
                assert any(e['kind']=='answer' and e['payload']['question_id']==question for e in ledger.events(run_id))
                row.update(_inspect_door(Path(state['artifact']['path']),door_binding))
                row['container_state']=file_ref(root/'runtime'/f'{run_id}-answer-container.json')
                row['same_native_run_after_answer']=native_id
            elif arm in {'A','C'}:
                assert state['status']=='submitted',state
                assert len(ifcopenshell.open(state['artifact']['path']).by_type('IfcWindow'))==2
                events=[e for e in ledger.events(run_id) if e['kind']=='submission_protocol']
                assert len(events)==1 and events[0]['payload']['profile_version']==SUBMISSION_PROFILE
                row['command_records']=file_ref(root/'runtime'/f'{run_id}-commands.json')
                row['submission_profile']=SUBMISSION_PROFILE
            else:
                expected='budget_exhausted' if case=='synthetic-003' else 'runtime_error'
                assert state['status']==expected and state['artifact'] is None,state
                rejected=[e for e in ledger.events(run_id) if e['kind']=='controller_request_rejected']
                if case=='synthetic-003':
                    assert state['usage']['calls']==1
                    assert any(e['payload'].get('origin')=='repair-controller' and e['payload'].get('error')=='CALL_BUDGET_EXHAUSTED' for e in rejected)
                    assert (root/'workspaces'/run_id/'work/native-tool-completed.txt').read_text()=='NATIVE_TOOL_DONE'
                else:
                    assert not rejected and state['usage']['calls']>=1
                row['container_state']=file_ref(root/'runtime'/run_id/'container.json')
            assert state['mode']=='real_runtime_fake_model' and not state['activities']
            assert sum(e['kind']=='started' for e in ledger.events(run_id))==1
            assert sha256(Path(state['metadata']['input_dir'])/'model.ifc')==row['public_source']['sha256']
            row['expected_status']=state['status'];report['runs'].append(row)
            write_json(evidence,report)
        call('stop');service.wait(timeout=40)
        assert before==capture_sources('admission'),'Source changed during native seam execution.'
        report.update(commands=commands,upstream_records=file_ref(root/'runtime/revision-upstream.jsonl'))
        write_json(evidence,report)
        print('REVISION_NATIVE_SEAMS',str(evidence.resolve()),flush=True)
    except BaseException as error:
        report['error']=f'{type(error).__name__}: {error}'
        report['commands']=commands
        write_json(evidence,report)
        raise
    finally:
        if service.poll() is None:
            service.terminate();service.wait(timeout=30)
            for name in [r['container'] for r in config['routes'].values()]+[config['relay']]:
                inspected=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
                if inspected.returncode==0:
                    carrier.docker('stop','--time','2',name)
                    if name==config['relay']:carrier.docker('rm',name)
            subprocess.run(['docker','network','rm',config['network']],capture_output=True)
        service_log.close()


def seal_revision_evidence(evidence, suite_receipt):
    """Bind the genuine passing test capture after pytest has actually exited."""
    from scripts.ifc_repair.repair_comparison.formal_admission import validate_revision_suite, validate_revision_seams
    validate_revision_suite(suite_receipt,phase='green')
    report=read_json(Path(evidence))
    assert 'error' not in report and len(report['runs'])==5
    report['suite_receipt']=file_ref(Path(suite_receipt))
    validate_revision_seams(report,current_bindings=carrier.bindings(report['configuration']),families={'AC','B','D'})
    write_json(Path(evidence),report)
    return report


class LegacyRectangleTransport(_FormalHTTPTransport):
    """Only fake HTTP responses; real Linux B handles its legacy geometry path."""
    def __call__(self, request):
        from tests.ifc_repair.test_door_installation_legacy_compatibility import CompatibilityProvider
        run_id=request.url.path.strip('/').split('/')[0]
        assert run_id=='synthetic-legacy-B'
        body=json.loads(request.content)
        provider=self.providers.setdefault(run_id,CompatibilityProvider())
        value=provider.generate_candidate(prompt=body['messages'][0]['content']).text
        response=httpx.Response(200,json={'id':'offline-legacy-rectangle','model':body['model'],
            'choices':[{'index':0,'message':{'role':'assistant','content':value},'finish_reason':'stop'}],
            'usage':{'prompt_tokens':11,'completion_tokens':7,'total_tokens':18}})
        path=self.root/'runtime/legacy-upstream.jsonl'
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a',encoding='utf8') as handle:
            handle.write(json.dumps({'run_id':run_id,'request':body,'response_status':response.status_code,
                'response_body':response.content.decode('utf8'),
                'evidence_class':'deterministic_controller_upstream'},ensure_ascii=False)+'\n')
        return response


def legacy_revision_fixture_cli():
    """Reuse the same actual CLI and approved B delayed-cleanup instrumentation."""
    # Each CLI call is a fresh process. Only its controller fake changes; the
    # original mapped/AC/D seam and its evidence remain untouched.
    global RevisionTransport
    RevisionTransport=LegacyRectangleTransport
    revision_fixture_cli()


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER')!='1',reason='explicit keyless legacy B Linux validation')
def test_formal_revision_legacy_rectangle_real_linux_public_cli(tmp_path):
    from tests.ifc_repair.test_door_installation_legacy_compatibility import direct_rectangle_scene, REQUEST
    from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm
    before=capture_sources('admission')
    helper=Path(__file__).resolve().parents[1]/'test_door_installation_legacy_compatibility.py'
    helper_binding=file_ref(helper)
    case_id='synthetic-legacy';run_id=case_id+'-B'
    cases=tmp_path/'public-cases';public=cases/case_id/'public';public.mkdir(parents=True)
    model,opening,reference,_=direct_rectangle_scene(millimetres=False,angle=0.)
    # Replacing the synthetic reference Body leaves its old product wrapper
    # unattached. Drop their unshared representation subgraphs before freezing D.
    from ifcopenshell.util.element import remove_deep2
    unattached=[shape for shape in model.by_type('IfcProductDefinitionShape') if not model.get_inverse(shape)]
    for shape in unattached:
        remove_deep2(model,shape)
    source=public/'model.ifc';model.write(str(source))
    (public/'request.txt').write_text(REQUEST,encoding='utf8')
    reference_id=reference.GlobalId;opening_id=opening.GlobalId
    type_id=reference.IsDefinedBy[0].RelatingType.GlobalId
    assert reference.IsDefinedBy[0].RelatingType.RepresentationMaps is None
    assert reference.Representation.Representations[0].RepresentationType=='SweptSolid'
    source_hash=sha256(source)
    source_log=ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model,source_log,express_rules=True)
    assert not source_log.statements,source_log.statements[:3]
    budgets={case_id:{'tokens':2500000,'calls':50,'active_seconds':600,'tool_seconds':120,'extensions':[]}}
    budget_path=tmp_path/'budgets.json';write_json(budget_path,budgets)
    root=tmp_path/'experiment';logs=tmp_path/'logs';logs.mkdir()
    command=[sys.executable,'-c','from tests.ifc_repair.repair_comparison.test_formal_revision_seams import legacy_revision_fixture_cli; legacy_revision_fixture_cli()']
    commands=[]
    def call(action,*arguments,timeout=600):
        argv=command+[action,'--root',str(root),*map(str,arguments)]
        response=subprocess.run(argv,cwd=carrier.REPO,capture_output=True,text=True,encoding='utf8',timeout=timeout)
        log=logs/f'{len(commands):02d}-{action}.log'
        log.write_text(response.stdout+'\nSTDERR\n'+response.stderr,encoding='utf8')
        commands.append({'argv':argv,'exit_code':response.returncode,'log':file_ref(log)})
        assert response.returncode==0,(action,response.stdout[-3000:],response.stderr[-3000:])
        return json.loads(response.stdout)
    config=call('init','--mode','offline','--cases-root',cases,'--case-ids',case_id,'--budgets',budget_path,
        '--stage',carrier.FORMAL_STAGE,'--scene-grounding')
    report={'schema_version':'repair-comparison-legacy-door-native-seam/0.1','real_models_called':False,
        'source_bindings':before,'configuration':config['configuration'],
        'images':carrier.bindings(config['configuration'])['images'],'fixture_helper':helper_binding,
        'fixture_normalization':{'unattached_product_definition_shapes_removed':len(unattached)},
        'runs':[],'checks':{},'instrumentation':'Same delayed B --rm cleanup as mapped seam; actual worker, SDK, CLI, network and publication.'}
    evidence=tmp_path/'legacy-native-seam.json';write_json(evidence,report)
    service_log=(logs/'service.log').open('wb')
    service=subprocess.Popen(command+['serve','--root',str(root)],cwd=carrier.REPO,stdout=service_log,stderr=subprocess.STDOUT)
    ledger=Ledger(root/'control.sqlite')
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists() or read_json(root/'service.json').get('state')!='running':
            assert service.poll() is None and time.monotonic()<deadline,'Legacy fixture service failed to start.'
            time.sleep(.25)
        state=call('run','--run-id',run_id,timeout=300)
        assert state['status']=='submitted' and state['native']['result']['successful_artifact_publishable'],state
        assert state['mode']=='real_runtime_fake_model' and not state['activities']
        assert state['usage']['calls']>=3
        assert sum(e['kind']=='started' for e in ledger.events(run_id))==1
        assert not any(c['state']=='inflight' for c in ledger.calls(run_id))
        assert sha256(source)==source_hash==sha256(Path(state['metadata']['input_dir'])/'model.ifc')
        assert sha256(root/'workspaces'/run_id/'model.ifc')==source_hash
        repaired=ifcopenshell.open(state['artifact']['path'])
        created=[d for d in repaired.by_type('IfcDoor') if d.GlobalId!=reference_id]
        assert len(created)==1
        door=created[0];target=repaired.by_guid(opening_id)
        assert door.FillsVoids[0].RelatingOpeningElement.GlobalId==opening_id
        assert door.IsDefinedBy[0].RelatingType.GlobalId==type_id
        assert door.IsDefinedBy[0].RelatingType.RepresentationMaps is None
        bounds=product_geometry_bounds_in_host_mm(door,target)
        for axis,expected in {'x':[0.,900.],'y':[50.,100.],'z':[0.,2100.]}.items():
            assert bounds[axis]==pytest.approx(expected,abs=1e-5)
        output_log=ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(repaired,output_log,express_rules=True)
        assert not output_log.statements,output_log.statements[:3]
        native_root=root/'runtime'/run_id/'state/native'/state['native']['result']['run_directory']
        resolution_path=native_root/'resolution.json';resolution=read_json(resolution_path)
        assert len(resolution['operations'])==1
        assert 'door_installation_anchor' not in resolution['operations'][0]['parameters']
        context=read_json(native_root/'api-context.json')
        assert context['installation_references']['offline-repair-0']['reference_global_id']==reference_id
        manifest=read_json(native_root/state['native']['result']['artifacts']['manifest'])
        public_evidence=next(a['path'] for a in manifest['artifacts'] if a['role']=='public_evidence')
        application=read_json(native_root/public_evidence)['evidence']['application']
        assert application['published'] and application['valid']
        report['runs']=[{'family':'B','run_id':run_id,'experiment_root':str(root.resolve()),
            'expected_status':'submitted','public_source':file_ref(source),
            'container_state':file_ref(root/'runtime'/f'{run_id}-start-container.json'),
            'resolution':file_ref(resolution_path),'artifact':file_ref(Path(state['artifact']['path']))}]
        report['checks']={'legacy_rectangle_supported':True,'source_unchanged':True,'exact_type_reused':True,
            'type_representation_maps_absent':True,'installation_anchor_absent':True,
            'source_schema_express_errors':0,'result_schema_express_errors':0,'bounds_in_opening_mm':bounds,
            'native_publication_valid':True}
        call('stop');service.wait(timeout=40)
        assert before==capture_sources('admission'),'Source changed during legacy native seam execution.'
        assert helper_binding==file_ref(helper),'Legacy fixture helper changed during execution.'
        report.update(commands=commands,upstream_records=file_ref(root/'runtime/legacy-upstream.jsonl'))
        write_json(evidence,report)
        print('LEGACY_NATIVE_SEAM',str(evidence.resolve()),flush=True)
    except BaseException as error:
        report.update(error=f'{type(error).__name__}: {error}',commands=commands)
        write_json(evidence,report)
        raise
    finally:
        if service.poll() is None:
            service.terminate();service.wait(timeout=30)
            for name in [r['container'] for r in config['routes'].values()]+[config['relay']]:
                inspected=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
                if inspected.returncode==0:
                    carrier.docker('stop','--time','2',name)
                    if name==config['relay']:carrier.docker('rm',name)
            subprocess.run(['docker','network','rm',config['network']],capture_output=True)
        service_log.close()


def seal_revision_with_legacy(mapped_evidence,legacy_evidence,suite_receipt,output):
    """Create a new combined certificate; never rewrite prior mapped evidence."""
    from scripts.ifc_repair.repair_comparison.formal_admission import validate_revision_suite, validate_revision_seams
    validate_revision_suite(suite_receipt,phase='green')
    report=read_json(Path(mapped_evidence));legacy=read_json(Path(legacy_evidence))
    assert 'error' not in report and 'error' not in legacy
    assert len(report['runs'])==5 and len(legacy['runs'])==1
    assert report['source_bindings']==legacy['source_bindings']==capture_sources('admission')
    assert report['images']==legacy['images']
    assert legacy['checks']['legacy_rectangle_supported'] and legacy['checks']['installation_anchor_absent']
    report['suite_receipt']=file_ref(Path(suite_receipt))
    report['runs']=[*report['runs'],*legacy['runs']]
    report['checks']={**report.get('checks',{}),'legacy_direct_sweptsolid_door':file_ref(Path(legacy_evidence))}
    validate_revision_seams(report,current_bindings=carrier.bindings(report['configuration']),families={'AC','B','D'})
    assert not Path(output).exists(),'Combined evidence destination must be new.'
    write_json(Path(output),report)
    return report
