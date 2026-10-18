"""Real Linux generic tools with fake HTTP native Qwen text; no credentials."""
import os
from pathlib import Path
import sys
import pytest
from scripts.ifc_repair import qwen_batch as qwen, qwen_tools
from scripts.ifc_repair.repair_comparison import batch_workflow as batch, demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json, sha256
from scripts.ifc_repair.repair_comparison.formal_admission import file_ref
from tests.ifc_repair.repair_comparison import test_scalable_native as native
from tests.ifc_repair.test_qwen_batch_native import unchanged_stop_sources

@pytest.mark.skipif(os.environ.get('REPAIR_QWEN_DOCKER')!='1',reason='explicit real Linux fake Qwen tools gate')
def test_g_native_tool_text_executes_and_publishes(tmp_path,request,monkeypatch):
    policy=qwen.load_policy_file(os.environ['REPAIR_QWEN_POLICY_FILE'])
    root=tmp_path/'runtime'
    qwen_tools.install(root,policy)
    original=carrier.initialize
    def initialize(*args,**kwargs):
        kwargs['providers']=qwen.limited_providers(kwargs['providers'],policy)
        config=original(*args,**kwargs)
        write_json(root/'qwen-policy.json',qwen.policy_document(policy))
        return config
    monkeypatch.setattr(carrier,'initialize',initialize)
    providers=qwen.limited_providers(qwen.default_providers(),policy)
    monkeypatch.setattr(native,'default_providers',lambda:providers)
    monkeypatch.setattr(native,'CLI',[sys.executable,'-m','tests.ifc_repair.qwen_tools_native_worker','worker'])
    previous_path=Path(os.environ['REPAIR_QWEN_PRIOR_NATIVE'])
    previous=read_json(previous_path)
    stop=previous['timeout_stop']
    assert stop['container_stopped'] and stop['quiescent'] and stop['timed_out']
    assert sha256(Path(stop['evidence']['path']))==stop['evidence']['sha256']
    def reuse_timeout(_):
        current=batch._runtime_bindings(carrier.bindings(read_json(root/'experiment.json')['configuration']))
        unchanged_stop_sources(current,batch._runtime_bindings(previous['runtime_bindings_after']))
        return {**stop,'reused_from':file_ref(previous_path)}
    monkeypatch.setattr(native,'_native_timeout_check',reuse_timeout)
    native._native_grid(tmp_path,request,case_groups={'case-001':['G'],'case-002':['G']})
    receipt=read_json(tmp_path/'native-stage.json')
    receipt['test_file']=file_ref(Path(__file__))
    receipt['helper_file']=file_ref(Path(native.__file__))
    receipt['native_text_worker']=file_ref(Path(__file__).with_name('qwen_tools_native_worker.py'))
    ledger=qwen.Ledger(root/'control.sqlite')
    for run in receipt['configuration']['order']:
        names=[name for e in ledger.events(run) if e['kind']=='qwen_tool_decoded' for name in e['payload']['names']]
        assert names==['write_file','execute','submit']
        assert all(c['response']['body']['choices'][0]['message']['content'].startswith('<tool_call>') for c in ledger.calls(run))
    receipt['native_tool_text_verified']=True
    write_json(tmp_path/'native-stage.json',receipt)
    batch._verify_native(tmp_path/'native-stage.json',receipt['configuration'],groups=['G'])
