import hashlib
import json
from pathlib import Path
import pytest
from text2ifc_web.live_runtime import local_live_factory,read_approval


def admitted_workspace(root, **limits):
    """A temporary code workspace with the generator's real source-binding shape."""
    sources = {
        'src/text2ifc_web/__init__.py': '# Offline fixture package.\n',
        'src/text2ifc_web/live_runtime.py': 'LIVE_ENABLED = False\n',
        'src/text2ifc_ifc_repair/api.py': '# Offline native API fixture.\n',
        'src/text2ifc_ifc_repair/orchestrator.py': '# Offline orchestrator fixture.\n',
    }
    for relative, content in sources.items():
        source = root/relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content, encoding='utf-8')
    record = {'scope':'repair-ui-local', 'status':'passed',
              'checks':[{'name':'offline_fixture_test_only', 'exit_code':0, 'passed':True}],
              'source_files':{relative:hashlib.sha256((root/relative).read_bytes()).hexdigest()
                              for relative in sources}}
    admission = root/'admission.json'
    admission.write_text(json.dumps(record), encoding='utf-8')
    data = {'scope':'repair-ui-local', 'approved':True, 'approval_id':'fixture',
            'max_calls':8, 'max_tokens':500000, 'max_active_seconds':1200,
            'admission_file':'admission.json', **limits}
    approval = root/'approval.json'
    approval.write_text(json.dumps(data), encoding='utf-8')
    return approval, admission, record, data


def test_live_disabled_does_not_read_credentials_or_create_a_provider(tmp_path):
    factory,status=local_live_factory(tmp_path,{})
    assert factory is None and status['enabled'] is False


def test_live_requires_explicit_budget_and_passed_stage_record(tmp_path):
    path=tmp_path/'approval.json'
    path.write_text(json.dumps({'scope':'repair-ui-local','approved':True,'approval_id':'round1'}))
    with pytest.raises(ValueError):read_approval(path,tmp_path)
    admission=tmp_path/'admission.json';admission.write_text(json.dumps({'scope':'repair-ui-local','status':'failed','checks':[]}))
    data={'scope':'repair-ui-local','approved':True,'approval_id':'round1','max_calls':8,'max_tokens':500000,'max_active_seconds':1200,'admission_file':'admission.json'}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):read_approval(path,tmp_path)


def test_factory_reuses_native_api_and_a_shared_budget_without_real_transport(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from text2ifc_web.live_runtime import LocalLiveFactory
    from text2ifc_ifc_repair.api import RepairAPI
    from text2ifc_agent.generation_budget import GenerationBudgetExceeded
    approval,_,_,_=admitted_workspace(tmp_path,max_calls=1,max_tokens=1000,max_active_seconds=60)
    calls=[]
    class Provider:
        config=SimpleNamespace(max_completion_tokens=20)
        def generate_live(self,**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(response={'usage':{'prompt_tokens':10,'completion_tokens':5}},output=object())
    monkeypatch.setattr('text2ifc_web.live_runtime.load_local_provider_environment',lambda root:{'DEEPSEEK_API_KEY':'[REDACTED_SECRET]'})
    monkeypatch.setattr(RepairAPI,'from_environment',lambda root,scene_grounding,environment:SimpleNamespace(provider=Provider()))
    factory=LocalLiveFactory(str(tmp_path),str(approval))
    first=factory(tmp_path/'data/native');first.provider.generate_live(prompt='test',state={'stage':'unit'})
    second=factory(tmp_path/'data/native')
    with pytest.raises(GenerationBudgetExceeded):second.provider.generate_live(prompt='next',state={'stage':'unit'})
    assert len(calls)==1 and second.integration_budget.snapshot()['calls_used']==1


def test_only_a_stage_record_with_completed_passing_checks_can_be_referenced(tmp_path):
    path,_,_,data=admitted_workspace(tmp_path)
    config=read_approval(path,tmp_path);assert config['max_calls']==8
    data['approved']=False;path.write_text(json.dumps(data))
    with pytest.raises(ValueError):read_approval(path,tmp_path)


@pytest.mark.parametrize('relative', [
    'src/text2ifc_web/__init__.py',
    'src/text2ifc_web/live_runtime.py',
    'src/text2ifc_ifc_repair/api.py',
    'src/text2ifc_ifc_repair/orchestrator.py',
])
def test_changed_admitted_source_blocks_execution(tmp_path, relative):
    approval,_,_,_=admitted_workspace(tmp_path)
    (tmp_path/relative).write_text('# Changed after admission.\n', encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_SOURCE_CHANGED'):
        read_approval(approval,tmp_path)


def test_missing_admitted_source_blocks_execution(tmp_path):
    approval,_,_,_=admitted_workspace(tmp_path)
    (tmp_path/'src/text2ifc_ifc_repair/api.py').unlink()
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_SOURCE_MISSING'):
        read_approval(approval,tmp_path)


@pytest.mark.parametrize('relative', [
    'src/text2ifc_web/__init__.py',
    'src/text2ifc_web/live_runtime.py',
    'src/text2ifc_ifc_repair/api.py',
    'src/text2ifc_ifc_repair/orchestrator.py',
])
def test_admission_cannot_omit_a_current_source_binding(tmp_path, relative):
    approval,admission,record,_=admitted_workspace(tmp_path)
    record['source_files'].pop(relative)
    admission.write_text(json.dumps(record), encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_BINDINGS_INCOMPLETE'):
        read_approval(approval,tmp_path)


def test_new_web_source_requires_its_own_admission_binding(tmp_path):
    approval,_,_,_=admitted_workspace(tmp_path)
    (tmp_path/'src/text2ifc_web/new_endpoint.py').write_text('# New public path.\n', encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_BINDINGS_INCOMPLETE'):
        read_approval(approval,tmp_path)


@pytest.mark.parametrize('bindings', [None, {}, []])
def test_missing_or_empty_source_bindings_do_not_authorize_live_use(tmp_path, bindings):
    approval,admission,record,_=admitted_workspace(tmp_path)
    if bindings is None:
        record.pop('source_files')
    else:
        record['source_files']=bindings
    admission.write_text(json.dumps(record), encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_BINDINGS_REQUIRED'):
        read_approval(approval,tmp_path)


@pytest.mark.parametrize('kind', ['traversal', 'absolute_outside', 'absolute_inside', 'drive_relative'])
def test_unsafe_source_binding_cannot_read_outside_the_workspace(tmp_path, kind):
    root=tmp_path/'workspace'
    approval,admission,record,_=admitted_workspace(root)
    outside=tmp_path/'outside.py'
    outside.write_text('# Outside the approved workspace.\n', encoding='utf-8')
    relative={'traversal':'../outside.py', 'absolute_outside':str(outside),
              'absolute_inside':str(root/'src/text2ifc_web/__init__.py'),
              'drive_relative':'C:outside.py'}[kind]
    record['source_files'][relative]=hashlib.sha256(outside.read_bytes()).hexdigest()
    admission.write_text(json.dumps(record), encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_SOURCE_PATH_INVALID'):
        read_approval(approval,root)


@pytest.mark.parametrize('digest', [None, 64, 'bad-hash', 'sha256:'+'a'*64])
def test_source_bindings_require_generator_sha256_digests(tmp_path, digest):
    approval,admission,record,_=admitted_workspace(tmp_path)
    record['source_files']['src/text2ifc_web/__init__.py']=digest
    admission.write_text(json.dumps(record), encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_SOURCE_HASH_INVALID'):
        read_approval(approval,tmp_path)


def test_every_declared_source_binding_is_checked(tmp_path):
    approval,admission,record,_=admitted_workspace(tmp_path)
    extra=tmp_path/'operator_helper.py'
    extra.write_text('# Additional admitted helper.\n', encoding='utf-8')
    record['source_files']['operator_helper.py']=hashlib.sha256(extra.read_bytes()).hexdigest()
    admission.write_text(json.dumps(record), encoding='utf-8')
    assert read_approval(approval,tmp_path)['approved'] is True
    extra.write_text('# Changed admitted helper.\n', encoding='utf-8')
    with pytest.raises(ValueError, match='LIVE_STAGE_ADMISSION_SOURCE_CHANGED'):
        read_approval(approval,tmp_path)


def test_stale_admission_is_rejected_before_loading_credentials(tmp_path, monkeypatch):
    approval,_,_,_=admitted_workspace(tmp_path)
    (tmp_path/'src/text2ifc_ifc_repair/orchestrator.py').write_text('# Changed.\n', encoding='utf-8')
    def forbidden(*args):
        raise AssertionError('Stale admission must fail before loading provider configuration')
    monkeypatch.setattr('text2ifc_web.live_runtime.load_local_provider_environment',forbidden)
    factory,status=local_live_factory(tmp_path,{
        'TEXT2IFC_UI_LIVE':'1', 'TEXT2IFC_UI_LIVE_APPROVAL':str(approval)})
    assert factory is None and status['enabled'] is False
    assert status['reason']=='LIVE_APPROVAL_OR_CONFIG_INVALID'
