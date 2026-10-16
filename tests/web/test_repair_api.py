"""First HTTP seam tests. Native full-chain checks are separate; no paid Provider."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import time

import ifcopenshell
import pytest
from fastapi.testclient import TestClient
from text2ifc_web.app import create_app


def source_bytes(schema='IFC2X3'):
    m = ifcopenshell.file(schema=schema)
    project = m.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), Name='接口测试')
    storey = m.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(), Name='Level 1')
    wall = m.create_entity('IfcWall', GlobalId=ifcopenshell.guid.new(), Name='墙体 <not HTML>')
    reference = m.create_entity('IfcWindow', GlobalId=ifcopenshell.guid.new(), Name='参考窗 Same Name')
    m.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), RelatedElements=[wall, reference], RelatingStructure=storey)
    return m.to_string().encode(), wall, reference


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'web', allowed_hosts=('testserver',))) as c:
        yield c


def upload(c, content=None):
    data, wall, ref = source_bytes()
    r = c.post('/api/ifc-inputs', files={'file': ('sample.ifc', content if content is not None else data, 'application/x-step')})
    assert r.status_code == 201, r.text
    return r.json(), data, wall, ref


def prepared(c):
    inp, data, wall, ref = upload(c)
    payload = {'input_id': inp['input_id'], 'user_text': '在这面墙上加窗，尺寸参照选中的窗。', 'language': 'zh', 'view_version': 'source-1',
               'primary': {'step_id': wall.id(), 'global_id': wall.GlobalId, 'view_version': 'source-1'},
               'auxiliary': {'step_id': ref.id(), 'global_id': ref.GlobalId, 'view_version': 'source-1'}}
    r = c.post('/api/repair-requests/prepare', json=payload)
    assert r.status_code == 201, r.text
    return r.json(), payload, data


def test_upload_and_exact_source_download(client):
    inp, data, _, _ = upload(client)
    assert inp['schema'] == 'IFC2X3'
    assert 'source_path' not in inp
    r = client.get(inp['download_url'])
    assert r.status_code == 200 and r.content == data
    assert 'attachment' in r.headers['content-disposition']


def test_prepare_keeps_text_and_real_names_without_executing(client):
    p, request, _ = prepared(client)
    assert p['user_text'] == request['user_text']
    assert p['effective_repair_text'].startswith(request['user_text'])
    assert '墙体 <not HTML>' in p['selection_context_text']
    assert 'Level 1' in p['selection_context_text']
    assert '参考窗 Same Name' in p['selection_context_text']
    assert p['references']['primary']['global_id'] == request['primary']['global_id']
    assert not p['execution_enabled']
    assert client.get('/api/capabilities').json()['rework_enabled'] is False
    assert client.post('/api/repair-tasks', json={'prepared_request_id': p['prepared_request_id'], 'client_request_id': 'click-1'}).status_code == 503


def test_no_selection_is_still_a_natural_language_request(client):
    inp, *_ = upload(client)
    text = '  一层外墙增加窗户\nDo not rewrite this.  '
    r = client.post('/api/repair-requests/prepare', json={'input_id':inp['input_id'], 'user_text':text, 'language':'en'})
    assert r.status_code == 201
    assert r.json()['effective_repair_text'] == text
    assert r.json()['selection_context_text'] == ''


@pytest.mark.parametrize('mutation', ['wrong_guid','wrong_version','missing_entity','same_reference'])
def test_reference_binding_rejects_mismatch(client, mutation):
    _, payload, _ = prepared(client)
    if mutation == 'wrong_guid': payload['primary']['global_id'] = '0'*22
    if mutation == 'wrong_version': payload['primary']['view_version'] = 'source-old'
    if mutation == 'missing_entity': payload['primary']['step_id'] = 99999
    if mutation == 'same_reference': payload['auxiliary'] = dict(payload['primary'])
    assert client.post('/api/repair-requests/prepare', json=payload).status_code == 409


@pytest.mark.parametrize('data', [b'bad file', b'version https://git-lfs.github.com/spec/v1\noid test', b''])
def test_invalid_upload_rejected(client, data):
    assert client.post('/api/ifc-inputs', files={'file':('bad.ifc',data)}).status_code == 422


def test_schema_filename_origin_and_unknown_fields(client):
    data, *_ = source_bytes('IFC4')
    assert client.post('/api/ifc-inputs',files={'file':('x.ifc',data)}).status_code == 422
    data, *_ = source_bytes()
    assert client.post('/api/ifc-inputs',files={'file':('../escape.ifc',data)}).status_code == 422
    assert client.post('/api/ifc-inputs',files={'file':('x.ifc',data)},headers={'Origin':'https://evil.example'}).status_code == 403
    inp, *_ = upload(client)
    assert client.post('/api/repair-requests/prepare',json={'input_id':inp['input_id'],'user_text':'x','source_path':'secret'}).status_code == 422
    assert client.get('/api/ifc-inputs/../../AGENTS.md/source').status_code == 404


def test_openapi_is_independent_and_describes_the_actual_routes(client):
    doc = client.get('/api/openapi.json').json()
    for route in ['/api/ifc-inputs','/api/repair-requests/prepare','/api/repair-tasks','/api/repair-tasks/{task_id}/answers']:
        assert route in doc['paths']
    assert not any('rework' in p for p in doc['paths'])


def test_upload_limit(tmp_path):
    with TestClient(create_app(tmp_path/'tiny', max_upload_bytes=80, allowed_hosts=('testserver',))) as c:
        assert c.post('/api/ifc-inputs',files={'file':('big.ifc',b'x'*81)}).status_code == 413


def test_rework_is_not_accidentally_enabled(tmp_path):
    with pytest.raises(ValueError, match='REWORK_NOT_SUPPORTED'):
        create_app(tmp_path/'no-rework', rework_policy=object())


def test_active_task_poll_does_not_take_native_publication_lock(tmp_path, monkeypatch):
    from text2ifc_web.service import RepairService
    service=RepairService(tmp_path/'poll')
    task,_=service.store.claim_start('request-a','key-a')
    data, *_=source_bytes()
    source=tmp_path/'source.ifc';source.write_bytes(data)
    service.native.start_run(source_path=source,request_id='test-request',request_text='test',run_id=task['run_id'])
    def forbidden(*args,**kwargs):
        raise AssertionError('A progress GET attempted native publication recovery')
    monkeypatch.setattr(service.native,'load',forbidden)
    monkeypatch.setattr(service.native,'read_result',forbidden)
    result=service.task(task['task_id'])
    assert result['busy'] and result['native_stage']=='created'
    assert result['successful_artifact_publishable'] is False
    assert service.events(task['task_id'])['events'][0]['stage']=='created'


def test_interrupted_worker_is_not_masked_by_old_clarification(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from text2ifc_web.service import RepairService
    from text2ifc_ifc_repair.run_models import RunStage
    service=RepairService(tmp_path/'interrupted')
    task,_=service.store.claim_start('request-a','key-a')
    service.store.finish(task['task_id'],error_code='WORKER_INTERRUPTED')
    state=SimpleNamespace(stage=RunStage.CLARIFICATION_REQUIRED,state_version=2,clarification={})
    monkeypatch.setattr(service,'_native_state',lambda _:state)
    result={'status':'clarification_required','clarification':{'question':'old'},'successful_artifact_publishable':False,'complete_repair_success':False}
    monkeypatch.setattr(service.native,'read_result',lambda _:SimpleNamespace(to_dict=lambda:result))
    actual=service.task(task['task_id'])
    assert actual['status']=='interrupted' and actual['clarification'] is None


def test_start_keys_do_not_alias_a_different_prepared_request(tmp_path):
    from text2ifc_web.store import Store
    from text2ifc_web.contracts import WebError
    store = Store(tmp_path/'keys')
    first,_ = store.claim_start('request-a','key-a')
    store.claim_start('request-b','key-b')
    with pytest.raises(WebError,match='IDEMPOTENCY_CONFLICT'):
        store.claim_start('request-a','key-b')
    same,fresh = store.claim_start('request-a','key-c')
    assert same['run_id'] == first['run_id'] and fresh is False


def test_concurrent_start_is_claimed_once(tmp_path):
    from text2ifc_web.store import Store
    store = Store(tmp_path/'parallel')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda n:store.claim_start('same-prepared','key-'+str(n)),range(8)))
    assert sum(fresh for _,fresh in results)==1
    assert len({row['run_id'] for row,_ in results})==1


def test_prepared_request_survives_service_restart(tmp_path):
    root = tmp_path/'restart'
    with TestClient(create_app(root, allowed_hosts=('testserver',))) as c:
        p, _, data = prepared(c)
    with TestClient(create_app(root, allowed_hosts=('testserver',))) as c:
        r = c.get('/api/repair-requests/'+p['prepared_request_id'])
        assert r.status_code == 200 and r.json()['effective_repair_text'] == p['effective_repair_text']
        assert c.get('/api/ifc-inputs/'+p['input_id']+'/source').content == data
