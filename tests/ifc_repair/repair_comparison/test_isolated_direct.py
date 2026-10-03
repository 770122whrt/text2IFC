import json
from pathlib import Path

import httpx
import pytest

from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner
from scripts.ifc_repair.repair_comparison.ledger import Ledger


def runner(tmp_path, handler):
    from scripts.ifc_repair.repair_comparison.isolated_direct import ChatExecutor
    from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway
    public = tmp_path / 'public'
    public.mkdir()
    (public/'model.ifc').write_text('IFC test bytes')
    (public/'request.txt').write_text('请修复这扇窗。',encoding='utf8')
    raw = DirectRunner.create(public,tmp_path/'runs',case_id='demo',arm='A',budget={
        'tokens':500000,'calls':10,'active_seconds':100,'tool_seconds':10,'extensions':[]})
    gateway = WireGateway(raw.ledger,tmp_path/'wire',transport=httpx.MockTransport(handler))
    token = gateway.register(raw.run_id,model='test-model',api_key='unused',endpoints={'chat':'https://test/v1/chat/completions'},evidence_class='deterministic_fake_http',max_output_tokens=100)
    return ChatExecutor(raw.root,raw.run_id,gateway_url=f'{gateway.url}/{token}/v1',model='test-model',max_output_tokens=100,isolated=False,evidence_class='deterministic_fake_http'),gateway


def completion(message, finish='tool_calls'):
    return httpx.Response(200,json={'id':'response','model':'test-model','usage':{'prompt_tokens':10,'completion_tokens':3},'choices':[{'message':{'role':'assistant',**message},'finish_reason':finish}]})


def test_chat_tool_ids_and_reasoning_replay_are_exact_with_unique_submission(tmp_path):
    messages = []
    responses = [completion({'content':None,'reasoning_content':'returned only','tool_calls':[{'id':'api-id-1','type':'function','function':{'name':'write_file','arguments':json.dumps({'path':'output/result.ifc','text':'repaired bytes'})}}]}),
        completion({'tool_calls':[{'id':'api-id-2','type':'function','function':{'name':'submit','arguments':'{"path":"output/result.ifc"}'}}]})]
    def handler(request):
        messages.append(json.loads(request.content)['messages'])
        return responses.pop(0)
    engine,gateway = runner(tmp_path,handler)
    with gateway:
        state=engine.run()
    assert state['status']=='submitted'
    assert Path(state['artifact']['path']).read_text()=='repaired bytes'
    assert messages[1][1]['tool_calls'][0]['id']=='api-id-1'
    assert messages[1][1]['reasoning_content']=='returned only'
    assert messages[1][2]['tool_call_id']=='api-id-1'
    assert state['usage']['calls']==2


def test_human_question_waits_and_continues_same_budget(tmp_path):
    responses=[completion({'tool_calls':[{'id':'ask','type':'function','function':{'name':'ask_user','arguments':'{"question":"补在哪一层？"}'}}]}),completion({'content':'no output'},'stop')]
    engine,gateway=runner(tmp_path,lambda req:responses.pop(0))
    with gateway:
        state=engine.run()
        assert state['status']=='awaiting_user' and len(responses)==1
        engine.ledger.answer(engine.run_id,question_id=state['question']['question_id'],text='二层',event_id='human-1')
        state=engine.run()
    assert state['status']=='no_output' and state['usage']['calls']==2


@pytest.mark.parametrize('message,finish',[({'tool_calls':[{'id':'bad','type':'function','function':{'name':'write_file','arguments':'{truncated'}}]},'tool_calls'),({'content':'half response'},'length')])
def test_bad_or_truncated_response_preserves_failure_without_retry(tmp_path,message,finish):
    engine,gateway=runner(tmp_path,lambda req:completion(message,finish))
    with gateway:
        state=engine.run()
    assert state['status']=='runtime_error' and state['usage']['calls']==1
    assert not state['artifact']


def test_uncertain_request_is_not_redispatched_on_recovery(tmp_path):
    requests=[]
    engine,gateway=runner(tmp_path,lambda req:requests.append(req) or completion({'content':'done'},'stop'))
    engine.ledger.start(engine.run_id)
    engine.ledger.reserve(engine.run_id,'uncertain-request',100)
    with gateway,pytest.raises(ValueError,match='RECOVERY'):
        engine.run()
    assert not requests and engine.ledger.snapshot(engine.run_id)['status']=='running'


def test_unconfirmed_process_stop_keeps_activity_and_blocks_next_task(tmp_path):
    responses=[completion({'tool_calls':[{'id':'command','type':'function','function':{'name':'execute','arguments':'{"argv":["python","job.py"]}'}}]})]
    engine,gateway=runner(tmp_path,lambda req:responses.pop(0))
    class Unstopped:
        tool_seconds=10
        quiescent=False
        def execute(self,**kwargs):raise RuntimeError('CONTAINER_STOP_NOT_CONFIRMED')
    engine.tools=Unstopped()
    with gateway,pytest.raises(RuntimeError,match='STOP_NOT_CONFIRMED'):
        engine.run()
    state=engine.ledger.snapshot(engine.run_id)
    assert state['status']=='running' and state['activities']


def test_batched_question_emits_all_tool_results_before_confirmed_answer(tmp_path):
    bodies=[]
    tools=[{'id':'ask','type':'function','function':{'name':'ask_user','arguments':'{"question":"在哪一层？"}'}},
           {'id':'read','type':'function','function':{'name':'read_file','arguments':'{"path":"model.ifc"}'}}]
    responses=[completion({'tool_calls':tools}),completion({'content':'no output'},'stop')]
    def handler(req):bodies.append(json.loads(req.content));return responses.pop(0)
    engine,gateway=runner(tmp_path,handler)
    with gateway:
        state=engine.run()
        engine.ledger.answer(engine.run_id,question_id=state['question']['question_id'],text='二层',event_id='human')
        engine.run()
    messages=bodies[1]['messages']
    assert [m['role'] for m in messages]==['user','assistant','tool','tool','user']
    assert [m['tool_call_id'] for m in messages if m['role']=='tool']==['ask','read']


def test_second_controller_cannot_execute_the_same_task(tmp_path):
    from scripts.ifc_repair.repair_comparison.controller_owner import task_owner
    requests=[]
    engine,gateway=runner(tmp_path,lambda req:requests.append(req) or completion({'content':'done'},'stop'))
    with task_owner(engine.root,engine.run_id),gateway,pytest.raises(ValueError,match='CONTROLLER_ALREADY_ACTIVE'):
        engine.run()
    assert not requests
