"""Versioned, opt-in neutral submission instructions; no repair-method hints."""
import copy
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from scripts.ifc_repair.repair_comparison import direct_runner as direct
from scripts.ifc_repair.repair_comparison.isolated_direct import ChatExecutor, TOOLS
from scripts.ifc_repair.repair_comparison.ledger import encode
from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway


PROFILE = 'repair-comparison-neutral-submission/0.1'
BUDGET = {'tokens': 500000, 'calls': 10, 'active_seconds': 100, 'tool_seconds': 5, 'extensions': []}
REQUEST = '\n请恢复缺失的窗。\n\n'


def make(tmp_path, arm='A', **kwargs):
    public = tmp_path/'public'
    public.mkdir(exist_ok=True)
    (public/'model.ifc').write_bytes(b'IFC fixture bytes')
    (public/'request.txt').write_text(REQUEST, encoding='utf8')
    runner = direct.DirectRunner.create(public, tmp_path/'experiment', case_id='case-001',
        arm=arm, budget=BUDGET, **kwargs)
    return runner, public


def protocol_events(runner):
    return [e for e in runner.ledger.events(runner.run_id) if e['kind']=='submission_protocol']


@pytest.mark.parametrize('arm', ['A', 'C'])
def test_new_formal_task_has_one_audited_protocol_before_first_request(tmp_path, arm):
    runner, public = make(tmp_path, arm, mode='real_runtime_fake_model',
        runtime_metadata={'stage':'repair-comparison-formal-live'})
    events = protocol_events(runner)
    assert len(events)==1
    payload = events[0]['payload']
    assert payload['profile_version']==PROFILE
    assert payload['application']=='new_task'
    assert payload['message']['role']=='system'
    assert payload['content_sha256']==hashlib.sha256(payload['message']['content'].encode('utf8')).hexdigest()
    assert runner.messages()[0]==payload['message']
    assert runner.messages()[1]['role']=='user'
    assert (public/'request.txt').read_text(encoding='utf8')==REQUEST
    assert (runner.root/'inputs/case-001/request.txt').read_bytes()==(public/'request.txt').read_bytes()
    assert runner.messages()[1]['content']==f'请按以下要求操作这个 IFC 文件：\n\n{REQUEST.strip()}\n\nIFC 文件：model.ifc'


def test_development_and_existing_ready_tasks_remain_legacy_until_explicit_opt_in(tmp_path):
    runner, _ = make(tmp_path)
    before = copy.deepcopy(runner.ledger.events(runner.run_id))
    initial = runner.messages()
    assert not protocol_events(runner)
    assert direct.DirectRunner(runner.root,runner.run_id).messages()==initial
    result = runner.enable_submission_protocol(profile=PROFILE, reason='operator scoped revision')
    assert result['status']=='ready' and not result['usage']['calls']
    events = runner.ledger.events(runner.run_id)
    assert events[:len(before)]==before
    assert runner.messages()[1:]==initial
    assert protocol_events(runner)[0]['payload']['application']=='explicit_ready_migration'
    assert protocol_events(runner)[0]['payload']['reason']=='operator scoped revision'
    runner.enable_submission_protocol(profile=PROFILE, reason='operator scoped revision')
    assert len(protocol_events(runner))==1


@pytest.mark.parametrize('state', ['running','inflight','awaiting','resumed','terminal','prior_event'])
def test_migration_refuses_any_started_call_or_runtime_history(tmp_path, state):
    runner, _ = make(tmp_path)
    ledger, rid = runner.ledger, runner.run_id
    if state=='prior_event':
        ledger.record(rid,'chat_assistant',{'message':{'role':'assistant','content':'existing'}})
    else:
        ledger.start(rid)
        if state=='inflight':ledger.reserve(rid,'old-call',10)
        if state in {'awaiting','resumed'}:
            ledger.ask(rid,question_id='question',text='在哪层？')
            if state=='resumed':ledger.answer(rid,question_id='question',text='二层',event_id='answer')
        if state=='terminal':ledger.finish(rid,'no_output')
    before = ledger.events(rid)
    messages = runner.messages()
    with pytest.raises(ValueError,match='SUBMISSION_PROTOCOL_REQUIRES_PRISTINE_READY_TASK'):
        runner.enable_submission_protocol(profile=PROFILE,reason='must refuse')
    assert ledger.events(rid)==before and runner.messages()==messages
    assert not protocol_events(runner)


@pytest.mark.parametrize('arm', ['B','D'])
def test_protocol_migration_does_not_modify_native_methods(tmp_path, arm):
    runner, _ = make(tmp_path,arm)
    with pytest.raises(ValueError,match='SUBMISSION_PROTOCOL_REQUIRES_A_OR_C'):
        runner.enable_submission_protocol(profile=PROFILE,reason='reject wrong method')
    assert not protocol_events(runner)


def test_same_neutral_instruction_for_a_c_contains_no_repair_hints(tmp_path):
    messages=[]
    for arm in ('A','C'):
        folder=tmp_path/arm;folder.mkdir()
        runner,_=make(folder,arm,submission_profile=PROFILE)
        messages.append(runner.messages()[0])
    assert messages[0]==messages[1]
    text=messages[0]['content']
    assert 'submit' in text and 'path' in text and '一次' in text and '唯一' in text
    assert all(word not in text.lower() for word in ('ifcopenshell','python','guid','name','changeset','索引','窗','门'))


@pytest.mark.parametrize('arm', ['A','C'])
def test_chat_protocol_is_once_across_question_resume_and_link_is_not_submission(tmp_path, arm):
    runner,_=make(tmp_path,arm,submission_profile=PROFILE)
    bodies=[]
    messages=[{'role':'assistant','tool_calls':[{'id':'ask','type':'function','function':{
        'name':'ask_user','arguments':'{"question":"确认位置？"}'}}]},
        {'role':'assistant','content':'完成：[结果](output/final.ifc)'}]
    def handler(request):
        bodies.append(json.loads(request.content))
        message=messages.pop(0)
        return httpx.Response(200,json={'id':'response','choices':[{'message':message,
            'finish_reason':'tool_calls' if message.get('tool_calls') else 'stop'}],
            'usage':{'prompt_tokens':10,'completion_tokens':2}})
    gateway=WireGateway(runner.ledger,tmp_path/'wire',transport=httpx.MockTransport(handler))
    token=gateway.register(runner.run_id,model='fake',api_key='unused',
        endpoints={'chat':'https://offline.test/v1/chat/completions'},evidence_class='deterministic_fake_http',max_output_tokens=100)
    def engine():return ChatExecutor(runner.root,runner.run_id,gateway_url=f'{gateway.url}/{token}/v1',
        model='fake',isolated=False,evidence_class='deterministic_fake_http',max_output_tokens=100)
    with gateway:
        state=engine().run()
        assert state['status']=='awaiting_user'
        runner.ledger.answer(runner.run_id,question_id=state['question']['question_id'],text='已确认',event_id='human')
        (runner.workspace/'output/final.ifc').write_bytes(b'unsubmitted IFC remains diagnostic')
        state=engine().run()
    assert state['status']=='no_output' and state['artifact'] is None
    assert state['usage']['calls']==2
    assert len(protocol_events(runner))==1
    assert len(bodies)==2 and all(body['tools']==TOOLS for body in bodies)
    for body in bodies:
        assert sum(m['role']=='system' for m in body['messages'])==1
        assert body['messages'][0]==protocol_events(runner)[0]['payload']['message']
    initial=next(e['payload'] for e in runner.ledger.events(runner.run_id) if e['kind']=='initial_message')
    assert protocol_events(runner)[0]['payload']['initial_message_sha256']==hashlib.sha256(encode(initial).encode('utf8')).hexdigest()
