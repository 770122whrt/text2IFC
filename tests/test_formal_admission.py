"""Fail-closed formal admission aggregation; fixtures are not stage evidence."""
from pathlib import Path
import json

import pytest

from scripts.ifc_repair.repair_comparison.contracts import write_json, sha256


def module():
    from scripts.ifc_repair.repair_comparison import formal_admission
    return formal_admission


def test_no_admission_without_frozen_twenty_task_plan(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        module().build_admission(tmp_path/'absent.json', runtime_evidence=tmp_path/'runtime.json',
            runtime_log=tmp_path/'runtime.log', suite_receipts=[], public_path_receipt=tmp_path/'public.json',
            output=tmp_path/'admission.json')
    assert not (tmp_path/'admission.json').exists()


def test_suite_receipt_requires_actual_success_log_and_current_sources(tmp_path, monkeypatch):
    m=module()
    log=tmp_path/'pytest.log'; log.write_text('68 passed in 325.80s (0:05:25)\n')
    monkeypatch.setattr(m,'capture_sources',lambda scope: {'current.py':'a'*64})
    target='tests/ifc_repair/repair_comparison/test_ours_adapter.py'
    receipt=m.make_suite_receipt(log,command=['python','-m','pytest',target,'-q'],exit_code=0,
        scope='runtime',source_bindings={'current.py':'a'*64},capture_source='tool-output transcript')
    assert {'clarification','resume','malformed'} <= m.validate_suite_receipt(receipt)
    receipt['source_bindings']['current.py']='b'*64
    with pytest.raises(ValueError,match='STALE'):
        m.validate_suite_receipt(receipt)


@pytest.mark.parametrize('summary',['1 failed, 68 passed','68 passed, 1 skipped','no tests ran','0 passed'])
def test_unsuccessful_or_partial_suite_cannot_supply_contracts(tmp_path,summary):
    log=tmp_path/'log'; log.write_text(summary)
    with pytest.raises(ValueError,match='PYTEST'):
        module().make_suite_receipt(log,command=['python','-m','pytest','tests/test_formal_admission.py'],
            exit_code=0,scope='admission',source_bindings={},capture_source='unit test fixture')


def test_test_selection_cannot_claim_whole_file_coverage(tmp_path):
    log=tmp_path/'log'; log.write_text('1 passed')
    with pytest.raises(ValueError,match='SELECTION'):
        module().make_suite_receipt(log,command=['python','-m','pytest','tests/test_formal_admission.py','-k','one'],
            exit_code=0,scope='admission',source_bindings={},capture_source='unit test fixture')


def test_changed_log_and_missing_coverage_are_rejected(tmp_path,monkeypatch):
    m=module(); monkeypatch.setattr(m,'capture_sources',lambda scope:{})
    log=tmp_path/'log'; log.write_text('1 passed')
    receipt=m.make_suite_receipt(log,command=['python','-m','pytest','tests/test_formal_admission.py'],
            exit_code=0,scope='admission',source_bindings={},capture_source='unit fixture')
    log.write_text('1 failed')
    with pytest.raises(ValueError,match='EVIDENCE_CHANGED'):
        m.validate_suite_receipt(receipt)
    with pytest.raises(ValueError,match='MISSING_CONTRACTS'):
        m.require_contracts({'complete'})


def test_public_scene_unsupported_is_terminal_and_keeps_source(tmp_path):
    from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs
    from tests.ifc_repair.test_scene_grounding import QueueProvider
    from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent
    from text2ifc_ifc_repair.api import RepairAPI
    cases,ids,_=_formal_public_inputs(tmp_path)
    source=cases/ids[0]/'public/model.ifc'; before=source.read_bytes()
    body=fixture_intent('window',{'allowed_ifc_classes':['IfcWall']},{})
    body['operations']=[]
    body['unsupported_requests']=[{'unsupported_id':'outside','kind':'unregistered_action',
        'operation_id':None,'capability_id':'unregistered_operation','source':body['provenance'][0]}]
    result=RepairAPI(tmp_path/'native',provider=QueueProvider([{'kind':'intent','intent':body,'bindings':[]}]),
                     scene_grounding=True).start(source,'执行尚未注册的修复操作。')
    assert result.status=='unsupported' and not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts and source.read_bytes()==before


def _technical_fixture(tmp_path, monkeypatch):
    """Fabricated review evidence solely for testing aggregation rejection logic."""
    m=module()
    from tests.ifc_repair.repair_comparison.test_formal_workflow import cases
    from scripts.ifc_repair.repair_comparison.task_review import _binding
    base=cases(tmp_path,monkeypatch,count=20)
    for case in sorted(base.iterdir()):
        path=case/'private/task.json'; task=json.loads(path.read_text(encoding='utf8'))
        (case/'private/mutation').mkdir(exist_ok=True)
        (case/'private/mutation/damaged.ifc').write_bytes((case/'public/model.ifc').read_bytes())
        task['source_sha256']=sha256(case/'private/reference.ifc')
        binding=_binding(case,task)
        task['review']['input_bindings']=binding
        write_json(path,task)
        write_json(case/'private/technical-review.json',{
            'schema_version':'repair-comparison-technical-review/0.1','case_id':case.name,
            'passed':True,'accepted':True,'errors':[],'input_bindings':binding,
            'checks':{k:True for k in m.TECHNICAL_CHECKS},
            'native_validation':{role:{'passed':True,'express_rules':True,'diagnostic_count':0} for role in ('G','D')}})
    path=tmp_path/'plan.json'
    m.formal.freeze(base,path)
    return path


def test_technical_receipts_bind_twenty_distinct_sources_and_reject_mutation(tmp_path,monkeypatch):
    m=module(); plan_path=_technical_fixture(tmp_path,monkeypatch)
    plan,technical=m.validate_technical_plan(plan_path)
    assert len(technical)==20 and len(plan['configuration']['order'])==80
    private=Path(plan['configuration']['cases_root'])/'formal-001/private'
    (private/'reference.ifc').write_text('changed after review')
    with pytest.raises(ValueError,match='FROZEN_TASK_CHANGED|TECHNICAL_REVIEW_STALE'):
        m.validate_technical_plan(plan_path)


def test_technical_receipts_reject_missing_native_and_check_evidence(tmp_path,monkeypatch):
    m=module(); plan_path=_technical_fixture(tmp_path,monkeypatch)
    plan=json.loads(plan_path.read_text(encoding='utf8'))
    report=Path(plan['configuration']['cases_root'])/'formal-001/private/technical-review.json'
    payload=json.loads(report.read_text(encoding='utf8')); payload['checks'].pop('wall_closure_recomputed')
    write_json(report,payload)
    # Re-sealing cannot turn an incomplete technical review into valid evidence.
    plan['cases'][0]['files']['private/technical-review.json']=sha256(report)
    write_json(plan_path,plan)
    with pytest.raises(ValueError,match='TECHNICAL_CHECKS'):
        m.validate_technical_plan(plan_path)


def test_aggregator_requires_each_validator_and_only_then_writes(tmp_path,monkeypatch):
    m=module(); plan_path=_technical_fixture(tmp_path,monkeypatch)
    plan,_=m.validate_technical_plan(plan_path)
    monkeypatch.setattr(m.carrier,'bindings',lambda config:{'bound':config})
    observed=[]
    monkeypatch.setattr(m,'validate_runtime_evidence',lambda *a,**k: observed.append('runtime') or {'receipt':'runtime fixture'})
    monkeypatch.setattr(m,'validate_suite_receipt',lambda receipt: m.REQUIRED_CONTRACTS)
    monkeypatch.setattr(m,'validate_public_path',lambda receipt: observed.append('public') or {'receipt':'public fixture'})
    output=tmp_path/'admission.json'
    result=m.build_admission(plan_path,runtime_evidence='runtime',runtime_log='log',suite_receipts=[{}],public_path_receipt={},output=output)
    assert observed==['runtime','public'] and result['passed']
    assert result['configuration']==plan['configuration']
    assert result['bindings']=={'bound':plan['configuration']}
    assert json.loads(output.read_text(encoding='utf8'))['real_models_called'] is False
    with pytest.raises(ValueError,match='ADMISSION_EXISTS'):
        m.build_admission(plan_path,runtime_evidence='runtime',runtime_log='log',suite_receipts=[{}],public_path_receipt={},output=output)


def test_failed_public_path_never_writes_passed_admission(tmp_path,monkeypatch):
    m=module(); path=_technical_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m.carrier,'bindings',lambda config:{})
    monkeypatch.setattr(m,'validate_runtime_evidence',lambda *a,**k:{})
    monkeypatch.setattr(m,'validate_suite_receipt',lambda receipt:m.REQUIRED_CONTRACTS)
    def fail(_): raise ValueError('PUBLIC_PATH_EVALUATOR_FAILED')
    monkeypatch.setattr(m,'validate_public_path',fail)
    with pytest.raises(ValueError,match='PUBLIC_PATH_EVALUATOR_FAILED'):
        m.build_admission(path,runtime_evidence='runtime',runtime_log='log',suite_receipts=[{}],public_path_receipt={},output=tmp_path/'admission.json')
    assert not (tmp_path/'admission.json').exists()


def test_formal_suite_cannot_bind_only_unchanged_runtime_sources(tmp_path,monkeypatch):
    m=module(); monkeypatch.setattr(m,'capture_sources',lambda scope:{})
    log=tmp_path/'log'; log.write_text('6 passed')
    receipt=m.make_suite_receipt(log,command=['python','-m','pytest','tests/ifc_repair/repair_comparison/test_formal_workflow.py'],
        exit_code=0,scope='runtime',source_bindings={},capture_source='unit fixture')
    with pytest.raises(ValueError,match='FORMAL_SUITE_SCOPE_REQUIRED'):
        m.validate_suite_receipt(receipt)


@pytest.mark.parametrize('override',[
    {'stage':'repair-comparison-demo-live'},
    {'real_models_called':True},
    {'error':'runtime failed'},
])
def test_runtime_receipt_rejects_wrong_stage_live_or_failed_evidence(tmp_path,override):
    m=module()
    report={'stage':m.carrier.FORMAL_STAGE,'real_models_called':False,
            'evidence_class':'real_runtime_fake_model',**override}
    write_json(tmp_path/'runtime.json',report)
    (tmp_path/'log').write_text('1 passed',encoding='utf8')
    with pytest.raises(ValueError,match='REAL_RUNTIME_OFFLINE_RECEIPT_REQUIRED'):
        m.validate_runtime_evidence(tmp_path/'runtime.json',tmp_path/'log',configuration={},current_bindings={})


def test_public_path_cannot_relabel_stale_code_as_current(monkeypatch):
    m=module(); monkeypatch.setattr(m,'capture_sources',lambda scope:{'source.py':'current'})
    with pytest.raises(ValueError,match='PUBLIC_PATH_SOURCE_BINDING_STALE'):
        m.validate_public_path({'schema_version':'repair-comparison-formal-public-path/0.1',
                               'mode':'offline','source_bindings':{'source.py':'old'}})


def test_revision_changes_require_exact_supported_source_and_same_contracts():
    m=module()
    path=m.HERE+'isolated_direct.py'
    old={'files':{path:'old'},'images':{'tools':'fixed'},'models':{'A':'fixed'},'budgets':{'case':1}}
    new=json.loads(json.dumps(old)); new['files'][path]='new'
    changes,families=m.revision_changes(old,new)
    assert changes=={path:{'before':'old','after':'new'}} and families=={'AC'}
    new['images']['tools']='changed'
    with pytest.raises(ValueError,match='REVISION_CONTRACT_CHANGED'): m.revision_changes(old,new)


@pytest.mark.parametrize('path',['public/formal-001/model.ifc','src/text2ifc_ifc_repair/unmapped.py',
                                'schemas/agent/changed.json'])
def test_revision_cannot_cover_arbitrary_changes_with_passing_tests(path):
    m=module()
    with pytest.raises(ValueError,match='UNCOVERED_REVISION_SOURCE'):
        m.revision_changes({'files':{path:'old'}},{'files':{path:'new'}})


def test_revision_scoped_receipt_cannot_just_recapture_old_suite(tmp_path):
    m=module(); log=tmp_path/'old.log'; log.write_text('1 passed',encoding='utf8')
    old=m.make_suite_receipt(log,command=['python','-m','pytest','tests/test_formal_admission.py'],
        exit_code=0,scope='admission',source_bindings={},capture_source='old actual run')
    with pytest.raises(ValueError,match='REVISION_RUN_RECEIPT_REQUIRED'):
        m.validate_revision_suite(old,phase='green')


def test_revision_runner_captures_actual_invocation_and_refuses_stale_green(tmp_path,monkeypatch):
    import subprocess
    m=module(); sources={m.HERE+'formal_admission.py':'current'}
    monkeypatch.setattr(m,'capture_sources',lambda scope:dict(sources))
    called=[]
    def execute(command,**kwargs):
        called.append(command)
        return subprocess.CompletedProcess(command,0,'2 passed in 0.1s\n','')
    monkeypatch.setattr(m.subprocess,'run',execute)
    command=['python','-m','pytest','tests/test_formal_admission.py','-q']
    receipt=m.run_revision_suite(command,tmp_path/'green.log')
    assert called==[command]
    assert m.validate_revision_suite(receipt,phase='green')['families']=={'admission'}
    sources[m.HERE+'formal_admission.py']='changed'
    with pytest.raises(ValueError,match='REVISION_GREEN_SOURCE_STALE'):
        m.validate_revision_suite(receipt,phase='green')
    with pytest.raises(ValueError,match='REVISION_LOG_EXISTS'):
        m.run_revision_suite(command,tmp_path/'green.log')


def test_external_red_preserves_original_source_scope_and_missing_times(tmp_path):
    m=module(); target=m.TESTS+'test_submission_protocol.py'
    log=tmp_path/'original.log'; log.write_text('14 failed in 0.1s\n',encoding='utf8')
    capture=tmp_path/'original.json'
    bindings={m.HERE+'isolated_direct.py':'old-source',target:'old-test'}
    write_json(capture,{'argv':['python','-m','pytest',target], 'exit_code':1,
        'source_bindings_before':bindings,'source_bindings_after':bindings,'log':m.file_ref(log)})
    original=sha256(capture)
    normalized=m.import_red_receipt(capture,tmp_path/'normalized.json')
    result=m.validate_revision_suite(normalized,phase='red')
    assert result['families']=={'AC'} and result['receipt']['started_at'] is None
    assert result['receipt']['source_bindings_before']=={m.HERE+'isolated_direct.py':'old-source'}
    assert sha256(capture)==original
    log.write_text('not the original failure',encoding='utf8')
    with pytest.raises(ValueError,match='EVIDENCE_CHANGED'):
        m.validate_revision_suite(normalized,phase='red')


def _revision_fixture(tmp_path,monkeypatch):
    """Unit-only inherited evidence; runtime validation is independently tested."""
    m=module(); path=m.HERE+'isolated_direct.py'
    config={'stage':m.carrier.FORMAL_STAGE,'case_ids':[f'case-{i:03}' for i in range(20)]}
    plan=tmp_path/'plan.json'; write_json(plan,{'configuration':config})
    old={'files':{path:'old'},'images':{},'models':{},'budgets':{}}
    current={**old,'files':{path:'new'}}
    parent={'schema_version':m.SCHEMA,'stage':m.carrier.FORMAL_STAGE,'passed':True,
        'configuration':config,'bindings':old,'plan':m.file_ref(plan),
        'covered_contracts':sorted(m.REQUIRED_CONTRACTS),
        'technical_reviews':[{'case_id':case} for case in config['case_ids']],
        'runtime_evidence':{'fixture':True},'public_path_evidence':{'fixture':True},'suite_receipts':[{'fixture':True}]}
    file=tmp_path/'parent.json'; write_json(file,parent)
    monkeypatch.setattr(m.carrier,'bindings',lambda c:current)
    monkeypatch.setattr(m.formal,'verify_plan',lambda p:{'configuration':config})
    def suite(receipt,phase):
        return {'families':set(receipt['families']),'targets':[],'receipt':receipt}
    monkeypatch.setattr(m,'validate_revision_suite',suite)
    green={'families':['AC']}
    red={'families':['AC'],'source_bindings_before':{path:'old'},'source_bindings_after':{path:'old'}}
    return m,file,current,green,red


def test_revision_inherits_immutable_parent_and_requires_new_native_seam(tmp_path,monkeypatch):
    m,parent,current,green,red=_revision_fixture(tmp_path,monkeypatch)
    digest=sha256(parent); observed=[]
    monkeypatch.setattr(m,'validate_revision_seams',lambda *a,**k:observed.append(k['families']) or {'unit_fixture':True})
    result=m.build_revision(parent,suite_receipts=[green],red_receipts=[red],seam_receipt={},output=tmp_path/'revision.json')
    assert observed==[{'AC'}] and result['bindings']==current and sha256(parent)==digest
    assert result['parent_admission']['sha256']==digest and result['base_admission']['sha256']==digest
    assert result['changed_sources']=={m.HERE+'isolated_direct.py':{'before':'old','after':'new'}}
    with pytest.raises(ValueError,match='ADMISSION_EXISTS'):
        m.build_revision(parent,suite_receipts=[green],red_receipts=[red],seam_receipt={},output=tmp_path/'revision.json')


@pytest.mark.parametrize('missing',['green','red','seam'])
def test_revision_does_not_write_if_affected_path_has_no_current_evidence(tmp_path,monkeypatch,missing):
    m,parent,current,green,red=_revision_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'validate_revision_seams',lambda *a,**k: {})
    with pytest.raises(ValueError,match='REVISION_'):
        m.build_revision(parent,suite_receipts=[] if missing=='green' else [green],
            red_receipts=[] if missing=='red' else [red],seam_receipt=None if missing=='seam' else {},
            output=tmp_path/'revision.json')
    assert not (tmp_path/'revision.json').exists()


def test_revision_rejects_unrelated_red_and_mutated_parent_plan(tmp_path,monkeypatch):
    m,parent,current,green,red=_revision_fixture(tmp_path,monkeypatch)
    red['source_bindings_after'][m.HERE+'isolated_direct.py']='not parent'
    with pytest.raises(ValueError,match='REVISION_RED_PARENT_REPRODUCTION_MISSING'):
        m.build_revision(parent,suite_receipts=[green],red_receipts=[red],seam_receipt={})
    (tmp_path/'plan.json').write_text('changed after parent admission',encoding='utf8')
    with pytest.raises(ValueError,match='EVIDENCE_CHANGED'):
        m.build_revision(parent,suite_receipts=[green],red_receipts=[red],seam_receipt={})


def test_revision_native_receipt_cannot_assert_pass_without_current_sources(monkeypatch):
    m=module(); monkeypatch.setattr(m,'capture_sources',lambda scope:{'current':'hash'})
    with pytest.raises(ValueError,match='REVISION_NATIVE_BINDING_STALE'):
        m.validate_revision_seams({'schema_version':'repair-comparison-revision-seams/0.1',
            'real_models_called':False,'source_bindings':{},'images':{}},current_bindings={'images':{}},families={'D'})


def test_revision_family_keeps_honest_capture_but_ignores_other_registered_owner(tmp_path,monkeypatch):
    import subprocess
    m=module(); other='src/text2ifc_ifc_repair/door_geometry.py'; shared=m.HERE+'ledger.py'
    sources={m.HERE+'isolated_direct.py':'AC-current',other:'B-before',shared:'shared-current'}
    monkeypatch.setattr(m,'capture_sources',lambda scope:dict(sources))
    def execute(command,**kwargs):
        sources[other]='B-after'
        return subprocess.CompletedProcess(command,0,'14 passed in 0.1s\n','')
    monkeypatch.setattr(m.subprocess,'run',execute)
    target=m.TESTS+'test_submission_protocol.py'
    path=m.run_revision_suite(['python','-m','pytest',target],tmp_path/'green.log')
    receipt=json.loads(path.read_text(encoding='utf8'))
    assert receipt['source_bindings_before'][other]=='B-before'
    assert receipt['source_bindings_after'][other]=='B-after'
    assert m.validate_revision_suite(path,phase='green')['families']=={'AC'}
    sources[shared]='changed shared dependency'
    with pytest.raises(ValueError,match='REVISION_GREEN_SOURCE_STALE'):
        m.validate_revision_suite(path,phase='green')
