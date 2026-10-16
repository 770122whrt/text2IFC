"""HTTP -> real RepairAPI -> real IfcOpenShell/validator, with ONLY Provider output frozen.
No key, transport, CLI or external task runner is used. Fixtures are not model-quality evidence.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import json
import time

import ifcopenshell
from fastapi.testclient import TestClient
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_web.app import create_app

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT/'dataset/processed/ifc-repair/repair-comparison/development'


@dataclass
class NativeFactory:
    kind: str = 'door'
    clarify: bool = False
    malformed: bool = False

    def __call__(self, output):
        # Existing deterministic Provider fixtures are test-only dependencies.
        from tests.ifc_repair.test_scene_repair_api import SceneDemoProvider
        from tests.ifc_repair.test_scene_grounding import QueueProvider
        if self.malformed:
            provider = QueueProvider(['{"kind":']*8)
        else:
            first = not any((Path(output)/'runs').glob('*/state.json'))
            provider = SceneDemoProvider(self.kind,ask_first=self.clarify and first)
        return RepairAPI(output,provider=provider,scene_grounding=True)


def wait(c, task_id, seconds=150):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        response=c.get('/api/repair-tasks/'+task_id)
        if response.status_code==409:
            time.sleep(.05);continue
        assert response.status_code==200,response.text
        result=response.json()
        if not result['busy']:
            return result
        time.sleep(.1)
    raise AssertionError('Native HTTP task did not finish within the bounded test timeout')


def begin(c, case):
    public=PUBLIC/case/'public'
    data=(public/'model.ifc').read_bytes()
    assert data.startswith(b'ISO-10303-21;'), 'Selected public fixture is not materialized'
    text=(public/'request.txt').read_text(encoding='utf-8')
    response=c.post('/api/ifc-inputs',files={'file':('input.ifc',data)})
    assert response.status_code==201,response.text
    inp=response.json()
    p=c.post('/api/repair-requests/prepare',json={'input_id':inp['input_id'],'user_text':text}).json()
    response=c.post('/api/repair-tasks',json={'prepared_request_id':p['prepared_request_id'],'client_request_id':'native-start'})
    assert response.status_code==202,response.text
    return response.json(),p,inp,data


def test_actual_door_repair_direct_api_publishes_real_geometry(tmp_path):
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(create_app(tmp_path/'web',api_factory=NativeFactory(),executor=executor,allowed_hosts=('testserver',))) as c:
            initial,prepared,inp,source=begin(c,'case-002')
            done=wait(c,initial['task_id'])
            assert done['status']=='succeeded',{'task':done,'events':c.get(done['events_url']).json()}
            assert done['successful_artifact_publishable']
            retry=c.post('/api/repair-tasks',json={'prepared_request_id':prepared['prepared_request_id'],'client_request_id':'second-click'}).json()
            assert retry['run_id']==done['run_id']
            entries=c.get(done['artifacts_url']).json()['artifacts']
            repaired=next(x for x in entries if x['role']=='successful_ifc')
            result=c.get(repaired['download_url'])
            model=ifcopenshell.file.from_string(result.content.decode('utf-8'))
            original=ifcopenshell.file.from_string(source.decode('utf-8'))
            assert model.schema=='IFC2X3'
            assert len(model.by_type('IfcDoor'))==len(original.by_type('IfcDoor'))+1
            assert c.get(inp['download_url']).content==source
            events=c.get(done['events_url']).json()
            assert events['events'][-1]['stage']=='succeeded'
            assert c.get(done['events_url']+'?after='+str(events['cursor'])).json()['events']==[]
            other=c.get('/api/repair-tasks/task-'+('0'*32)+'/artifacts/'+repaired['artifact_id'])
            assert other.status_code==404
            evaluation=next(x for x in entries if x['name']=='public-evaluation.json')
            assert c.get(evaluation['download_url']).json()['successful_artifact_publishable'] is True
            assert not list((tmp_path/'web/native/runs').glob('*/*rework*'))
            # A positive pick/readback run: take actual public grounding identities,
            # then submit those same visible objects as user references.
            run_dir=tmp_path/'web/native/runs'/done['run_id']
            grounding=json.loads((run_dir/'intent/grounding-evidence.json').read_text(encoding='utf-8'))['derivations'][0]
            opening=original.by_guid(grounding['target_id'])
            target=opening.VoidsElements[0].RelatingBuildingElement
            reference=original.by_guid(grounding['reference_occurrence_id'])
            req=c.post('/api/repair-requests/prepare',json={'input_id':inp['input_id'],'user_text':prepared['user_text'],'view_version':'selected-source',
                'primary':{'step_id':target.id(),'global_id':target.GlobalId,'view_version':'selected-source'},
                'auxiliary':{'step_id':reference.id(),'global_id':reference.GlobalId,'view_version':'selected-source'}})
            assert req.status_code==201,req.text
            started=c.post('/api/repair-tasks',json={'prepared_request_id':req.json()['prepared_request_id'],'client_request_id':'positive-picked-task'})
            assert started.status_code==202,started.text
            picked_done=wait(c,started.json()['task_id'])
            assert picked_done['status']=='succeeded',picked_done
            selection_check=json.loads((tmp_path/'web/native/runs'/picked_done['run_id']/'selection-check.json').read_text(encoding='utf-8'))
            assert selection_check['valid'] is True and len(selection_check['checks'])==2


def test_actual_clarification_answer_continues_one_run_without_duplicate(tmp_path):
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(create_app(tmp_path/'web',api_factory=NativeFactory('window',clarify=True),executor=executor,allowed_hosts=('testserver',))) as c:
            initial,p,inp,source=begin(c,'case-001')
            pending=wait(c,initial['task_id'])
            assert pending['status']=='clarification_required',pending
            q=pending['clarification']
            answer={'client_answer_id':'answer-1','clarification_id':q['clarification_id'],
                    'expected_state_version':pending['state_version'],'answer':{'kind':'add_detail','detail':'宽915毫米。'}}
            stale={**answer,'expected_state_version':0}
            assert c.post('/api/repair-tasks/'+pending['task_id']+'/answers',json=stale).status_code==409
            r=c.post('/api/repair-tasks/'+pending['task_id']+'/answers',json=answer)
            assert r.status_code==202,r.text
            repeated=c.post('/api/repair-tasks/'+pending['task_id']+'/answers',json=answer)
            assert repeated.status_code==202,repeated.text
            done=wait(c,pending['task_id'])
            assert done['run_id']==pending['run_id'] and done['status']=='succeeded',done
            assert c.get(inp['download_url']).content==source
            assert len(list((tmp_path/'web/native/runs').glob('*/state.json')))==1


def test_default_spawn_worker_calls_native_api_without_a_cli(tmp_path):
    with TestClient(create_app(tmp_path/'spawn',api_factory=NativeFactory(malformed=True),allowed_hosts=('testserver',))) as c:
        initial,p,inp,source=begin(c,'case-002')
        done=wait(c,initial['task_id'])
        assert done['status']=='provider_failed',done
        assert done['rework_enabled'] is False
        assert c.get(inp['download_url']).content==source
        attempts=list((tmp_path/'spawn/native/runs'/done['run_id']/'intent').glob('round-*/attempt-*.json'))
        assert len(attempts)==8


def test_wrong_selected_wall_is_rejected_before_any_ifc_application(tmp_path):
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(create_app(tmp_path/'guard',api_factory=NativeFactory(),executor=executor,allowed_hosts=('testserver',))) as c:
            public=PUBLIC/'case-002/public'
            source=(public/'model.ifc').read_bytes()
            model=ifcopenshell.file.from_string(source.decode('utf-8'))
            selected=model.by_type('IfcBuilding')[0]  # Real source object, but not the requested door's opening/host.
            inp=c.post('/api/ifc-inputs',files={'file':('input.ifc',source)}).json()
            p=c.post('/api/repair-requests/prepare',json={'input_id':inp['input_id'],'user_text':(public/'request.txt').read_text(encoding='utf-8'),'view_version':'s1','primary':{'step_id':selected.id(),'global_id':selected.GlobalId,'view_version':'s1'}}).json()
            response=c.post('/api/repair-tasks',json={'prepared_request_id':p['prepared_request_id'],'client_request_id':'wrong-pick'})
            assert response.status_code==202,response.text
            done=wait(c,response.json()['task_id'])
            assert done['status']=='audit_failed' and done['reason_code']=='PICKED_TARGET_MISMATCH',done
            assert not done['successful_artifact_publishable']
            assert c.get(inp['download_url']).content==source
            events=c.get(done['events_url']).json()
            assert not any(e['stage']=='application' for e in events['activity'])
            entries=c.get(done['artifacts_url']).json()['artifacts']
            guard=next(f for f in entries if f['role']=='selection_check')
            assert c.get(guard['download_url']).json()['valid'] is False
            assert not any(f['role']=='successful_ifc' for f in entries)


def test_malformed_provider_stops_without_final_rework(tmp_path):
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(create_app(tmp_path/'web',api_factory=NativeFactory(malformed=True),executor=executor,allowed_hosts=('testserver',))) as c:
            initial,p,inp,source=begin(c,'case-002')
            done=wait(c,initial['task_id'])
            assert done['status']=='provider_failed',done
            assert not done['successful_artifact_publishable']
            entries=c.get(done['artifacts_url']).json()['artifacts']
            assert not any(x['role']=='successful_ifc' for x in entries)
            assert c.get(inp['download_url']).content==source
            attempts=list((tmp_path/'web/native/runs'/done['run_id']/'intent').glob('round-*/attempt-*.json'))
            assert len(attempts)==8  # Native scene limit, not 8 post-Evaluation repairs.
            assert len(list((tmp_path/'web/native/runs').glob('*/state.json')))==1
