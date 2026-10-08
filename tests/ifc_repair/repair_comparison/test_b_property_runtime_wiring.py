"""Scoped carrier wiring tests; mocked factories are not retrieval evidence."""
from __future__ import annotations
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import isolated_b as carrier

ROOT=Path(__file__).resolve().parents[3]
VERSION='text2ifc/isolated-b-property-runtime/0.1'
IMAGE='text2ifc/repair-tools:py312-ifc085-property-v1'


def config(tmp_path,*,enabled=True):
    bundle=tmp_path/'bundle';carrier.build_runtime_bundle(ROOT,bundle)
    work=tmp_path/'workspace';work.mkdir();(work/'output').mkdir()
    (work/'model.ifc').write_text('public synthetic placeholder',encoding='utf8')
    (work/'task.txt').write_text('Set the selected public beam load bearing.',encoding='utf8')
    model=tmp_path/'model-cache';model.mkdir()
    (model/'config.json').write_text('{}',encoding='utf8')
    (model/'modules.json').write_text('[]',encoding='utf8')
    options={'image':IMAGE,'property_model_directory':model} if enabled else {}
    return carrier.IsolatedBConfig(bundle,work,'property-unit-state','property-unit-internal',
        'http://repair-gateway:8000/v1',**options)


def test_property_bundle_keeps_real_factory_policy_and_no_data(tmp_path):
    c=config(tmp_path,enabled=False)
    names=carrier.verify_runtime_bundle(c.bundle)
    assert 'src/text2ifc_knowledge/property_runtime.py' in names
    assert 'src/text2ifc_knowledge/property_search.py' in names
    assert 'schemas/ifc/knowledge/property_resolution_policy.v0.2.json' in names
    assert not any(n.startswith(('dataset/','.cache/','.env','tests/')) for n in names)


def test_property_model_mount_is_readonly_and_qdrant_remains_task_local(tmp_path):
    c=config(tmp_path)
    argv=carrier.IsolatedB(c).docker_argv()
    mounts=[argv[i+1] for i,item in enumerate(argv) if item=='--mount']
    assert f'type=bind,source={c.property_model_directory.absolute()},target=/models/bge-m3,readonly' in mounts
    assert len(mounts)==6
    assert '--memory=8g' in argv and '--cpus=4' in argv and '--read-only' in argv
    assert '--env=HF_HUB_OFFLINE=1' in argv and '--env=TRANSFORMERS_OFFLINE=1' in argv
    assert not any('QDRANT_URL' in a or 'API_KEY' in a or '.env' in a for a in argv)
    assert not any(str(ROOT)==a or f'source={ROOT},' in a for a in argv)
    assert IMAGE in argv


@pytest.mark.parametrize('fault',['missing_directory','wrong_image','comma_path'])
def test_property_mount_rejects_unusable_or_unreviewed_config(tmp_path,fault):
    c=config(tmp_path)
    with pytest.raises(ValueError,match='PROPERTY_'):
        if fault=='missing_directory': c=replace(c,property_model_directory=tmp_path/'missing')
        elif fault=='wrong_image': c=replace(c,image='text2ifc/repair-tools:py312-ifc085-v2')
        else:
            path=tmp_path/'models,unsafe';path.mkdir()
            c=replace(c,property_model_directory=path)
        carrier.IsolatedB(c).docker_argv()


def test_legacy_config_has_no_property_mount_or_new_runtime_requirement(tmp_path):
    c=config(tmp_path,enabled=False)
    argv=carrier.IsolatedB(c).docker_argv()
    assert len([a for a in argv if a=='--mount'])==5
    assert not any('/models/bge-m3' in a for a in argv)
    assert c.image=='text2ifc/repair-tools:py312-ifc085-v2'


def worker_fixture(tmp_path,monkeypatch,*,ready=True):
    import text2ifc_knowledge
    import text2ifc_ifc_repair.api as api
    import text2ifc_agent.openai_compat as transport
    work=tmp_path/'work';work.mkdir();(work/'output').mkdir()
    (work/'model.ifc').write_text('public synthetic source',encoding='utf8')
    (work/'task.txt').write_text('Set load bearing to true.',encoding='utf8')
    events=[];factories=[];api_kwargs=[]
    runtime=SimpleNamespace(health=SimpleNamespace(status='ready' if ready else 'not_ready',
        reason_code=None if ready else 'BGE_M3_UNAVAILABLE',acceptance_eligible=ready),
        vector_index=SimpleNamespace(close=lambda:events.append('runtime_closed')))
    def factory(environment=None,*,project_root=None):
        factories.append((environment,project_root));events.append('factory');return runtime
    result=SimpleNamespace(successful_artifact_publishable=False,to_dict=lambda:{'status':'invalid_input'})
    class API:
        def __init__(self,root,**kw):api_kwargs.append(kw)
        def start(self,*args,**kw):events.append('start');return result
        def read_result(self,*args,**kw):events.append('read');return result
    monkeypatch.setattr(text2ifc_knowledge,'create_property_runtime_from_environment',factory)
    monkeypatch.setattr(api,'RepairAPI',API)
    monkeypatch.setattr(transport,'OpenAICompatibleLiveProvider',lambda **kw:SimpleNamespace(client=SimpleNamespace(close=lambda:events.append('provider_closed'))))
    # If environment were copied blindly this sentinel would escape the carrier.
    monkeypatch.setenv('TEXT2IFC_PROPERTY_QDRANT_URL','http://unoffered.invalid:6333')
    monkeypatch.setenv('B_PROPERTY_SECRET_SENTINEL','must-not-be-forwarded')
    payload={'action':'start','run_id':'property-offline','base_url':'http://127.0.0.1:8000/v1',
             'evidence_class':'deterministic_fake_http','property_runtime_version':VERSION}
    return work,payload,runtime,events,factories,api_kwargs


def test_worker_injects_real_factory_contract_without_host_environment(tmp_path,monkeypatch):
    work,payload,runtime,events,factories,api_kwargs=worker_fixture(tmp_path,monkeypatch)
    state=tmp_path/'state'
    carrier.worker_execute(payload,workspace=work,state_root=state)
    assert len(factories)==1
    env,root=factories[0]
    assert root==Path(carrier.__file__).resolve().parents[3]
    assert env=={
        'TEXT2IFC_PROPERTY_BGE_MODEL_PATH':'/models/bge-m3',
        'TEXT2IFC_PROPERTY_BGE_DEVICE':'cpu',
        'TEXT2IFC_PROPERTY_QDRANT_PATH':str(state.resolve()/'property-runtime/qdrant'),
    }
    assert api_kwargs[0]['property_knowledge_runtime'] is runtime
    assert json.loads((state/'task.json').read_text(encoding='utf8'))['property_runtime_version']==VERSION
    assert events==['factory','start','runtime_closed','provider_closed']


def test_worker_missing_runtime_fails_closed_and_closes_resources(tmp_path,monkeypatch):
    work,payload,_,events,_,_=worker_fixture(tmp_path,monkeypatch,ready=False)
    with pytest.raises(ValueError,match='PROPERTY_RUNTIME_NOT_READY'):
        carrier.worker_execute(payload,workspace=work,state_root=tmp_path/'state')
    assert 'start' not in events
    assert 'runtime_closed' in events and events[-1]=='provider_closed'
    assert not list((work/'output').iterdir())


def test_read_does_not_initialize_embedding_and_runtime_cannot_be_silently_disabled(tmp_path,monkeypatch):
    work,payload,_,events,factories,_=worker_fixture(tmp_path,monkeypatch)
    state=tmp_path/'state'
    carrier.worker_execute(payload,workspace=work,state_root=state)
    count=len(factories)
    carrier.worker_execute({**payload,'action':'read'},workspace=work,state_root=state)
    assert len(factories)==count and 'read' in events
    changed={**payload,'action':'read'};changed.pop('property_runtime_version')
    with pytest.raises(ValueError,match='B_TASK_BINDING_MISMATCH'):
        carrier.worker_execute(changed,workspace=work,state_root=state)


def test_unrecognized_runtime_version_rejected_before_task_claim(tmp_path,monkeypatch):
    work,payload,_,events,_,_=worker_fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='PROPERTY_RUNTIME_VERSION_UNSUPPORTED'):
        carrier.worker_execute({**payload,'property_runtime_version':'unregistered'},workspace=work,state_root=tmp_path/'state')
    assert not (tmp_path/'state/task.json').exists() and not events


def test_enabled_execute_binds_runtime_version_before_launch(tmp_path,monkeypatch):
    c=config(tmp_path)
    calls=[]
    def run(argv,**kwargs):
        calls.append((argv,kwargs))
        if argv[:3]==['docker','network','inspect']:return SimpleNamespace(stdout='true',returncode=0)
        return SimpleNamespace(stdout=carrier.RESULT_PREFIX+'{"ok":true,"artifact_relative":null}',stderr='',returncode=0)
    monkeypatch.setattr(carrier.subprocess,'run',run)
    carrier.IsolatedB(c).start('property-task')
    payload=json.loads(calls[-1][1]['input'])
    assert payload['property_runtime_version']==VERSION
    assert str(c.property_model_directory) not in json.dumps(payload)


def test_property_state_restore_checks_runtime_binding_before_docker(tmp_path,monkeypatch):
    c=config(tmp_path)
    snapshot=tmp_path/'snapshot';snapshot.mkdir();(snapshot/'native').mkdir();(snapshot/'property-runtime').mkdir()
    binding={'run_id':'property-task','source_sha256':carrier._sha(c.workspace/'model.ifc'),
             'request_sha256':carrier._sha(c.workspace/'task.txt'),'model':c.model,
             'evidence_class':c.evidence_class,'property_runtime_version':VERSION}
    (snapshot/'task.json').write_text(json.dumps(binding),encoding='utf8')
    monkeypatch.setattr(carrier.subprocess,'run',lambda *a,**k:pytest.fail('must reject before Docker'))
    with pytest.raises(ValueError,match='STATE_RESTORE_METHOD_MISMATCH'):
        carrier.IsolatedB(replace(c,property_model_directory=None,image='text2ifc/repair-tools:py312-ifc085-v2')).restore_state(snapshot)
