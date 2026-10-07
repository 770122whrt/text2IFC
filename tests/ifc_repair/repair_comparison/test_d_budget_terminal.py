"""D terminal classification uses trusted controller events, not SDK text."""
import json
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import write_json
from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner


def run_native_error(tmp_path, monkeypatch, events=(), *, result=None, elapsed=False):
    public, root = tmp_path/'public', tmp_path/'experiment'
    public.mkdir()
    (public/'model.ifc').write_text('ISO-10303-21;END-ISO-10303-21;',encoding='utf8')
    (public/'request.txt').write_text('Synthetic transport classification only.',encoding='utf8')
    run_id='synthetic-D'
    runner=DirectRunner.create(public,root,case_id='synthetic',arm='D',
        budget={'tokens':1000,'calls':10,'active_seconds':60,'tool_seconds':5,'extensions':[]})
    write_json(root/'experiment.json',{'mode':'offline','models':carrier.MODELS,
        'routes':{run_id:{'token':'isolated-unit-route','container':'unit-d','volume':'unit-state'}},
        'order':[run_id],'network':'unit-network'})
    write_json(root/'service.json',{'state':'running','url':'http://127.0.0.1:1'})
    native_result=result or {'ok':True,'result':{'finish_reason':'error','final_response':'AUTH failure'}}
    stopped={'value':False}
    original_snapshot=carrier.Ledger.snapshot
    def snapshot(ledger, task):
        value=original_snapshot(ledger,task)
        if elapsed and stopped['value']:
            value['active_elapsed_s']=value['limits']['active_seconds']+1
        return value
    monkeypatch.setattr(carrier.Ledger,'snapshot',snapshot)
    class Native:
        def __init__(self,*args,**kwargs):
            pass
        def run(self,*,ledger,run_id):
            for kind,payload in events:
                ledger.record(run_id,kind,payload)
            (runner.workspace/'output/repaired.ifc').write_text('unique-unit-output',encoding='utf8')
            stopped['value']=True
            return native_result
    monkeypatch.setattr(carrier,'NativeDSH',Native)
    return carrier.run_owned(root,run_id),runner


def denied(code, origin='repair-controller'):
    return ('controller_request_rejected',{'error':code,'origin':origin,'wire_protocol':'messages'})


@pytest.mark.parametrize('code',['TOKEN_BUDGET_EXHAUSTED','CALL_BUDGET_EXHAUSTED','TIME_BUDGET_EXHAUSTED'])
def test_trusted_budget_refusal_is_not_auth_runtime_error(tmp_path,monkeypatch,code):
    state,runner=run_native_error(tmp_path,monkeypatch,[denied(code)])
    assert state['status']=='budget_exhausted'
    assert runner.ledger.events(state['run_id'])[-1]['payload']['detail']==code


@pytest.mark.parametrize('events',[
    [],
    [denied('TOKEN_BUDGET_EXHAUSTED',origin='upstream')],
    [denied('MODEL_NOT_OFFERED')],
    [denied('TOKEN_BUDGET_EXHAUSTED'),('request_reserved',{'request_id':'continued'})],
    [denied('TOKEN_BUDGET_EXHAUSTED'),denied('MODEL_NOT_OFFERED')],
])
def test_untrusted_nonbudget_or_stale_refusal_remains_runtime_error(tmp_path,monkeypatch,events):
    state,_=run_native_error(tmp_path,monkeypatch,events)
    assert state['status']=='runtime_error'


def test_failure_text_alone_does_not_make_budget_failure(tmp_path,monkeypatch):
    state,_=run_native_error(tmp_path,monkeypatch,result={'ok':False,'error':'UPSTREAM_BUDGET_DENIED'})
    assert state['status']=='runtime_error'


def test_native_clock_stop_has_corresponding_exhausted_clock(tmp_path,monkeypatch):
    state,_=run_native_error(tmp_path,monkeypatch,elapsed=True,
        result={'ok':False,'error':'ACTIVE_TIME_BUDGET_EXHAUSTED','container_stopped':True})
    assert state['status']=='budget_exhausted'


def test_native_clock_error_without_exhausted_clock_is_not_inferred(tmp_path,monkeypatch):
    state,_=run_native_error(tmp_path,monkeypatch,
        result={'ok':False,'error':'ACTIVE_TIME_BUDGET_EXHAUSTED','container_stopped':True})
    assert state['status']=='runtime_error'


def test_success_is_not_overridden_by_old_refusal(tmp_path,monkeypatch):
    result={'ok':True,'result':{'finish_reason':'end_turn',
        'final_response':json.dumps({'submitted_ifc':'output/repaired.ifc'})}}
    state,_=run_native_error(tmp_path,monkeypatch,[denied('TOKEN_BUDGET_EXHAUSTED')],result=result)
    assert state['status']=='submitted'
    assert Path(state['artifact']['path']).read_text(encoding='utf8')=='unique-unit-output'
