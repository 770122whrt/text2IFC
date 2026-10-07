"""A/C Chat Completions executor, sharing generic tools and task protocol."""
from __future__ import annotations

import json
import httpx

from .container_tools import ContainerTools
from .direct_runner import DirectRunner, submission_messages
from .controller_owner import task_owner


def function(name,description,properties,required=()):
    return {'type':'function','function':{'name':name,'description':description,
        'parameters':{'type':'object','properties':properties,'required':list(required),'additionalProperties':False}}}


S={'type':'string'}
TOOLS=[
    function('list_files','List files in the working directory.',{'pattern':S}),
    function('read_file','Read a UTF-8 file; offsets are characters.',{'path':S,'offset':{'type':'integer'},'limit':{'type':'integer'}},['path']),
    function('write_file','Write a UTF-8 file.',{'path':S,'text':S},['path','text']),
    function('replace_text','Replace exactly one matching text occurrence.',{'path':S,'old':S,'new':S},['path','old','new']),
    function('execute','Execute a command in the working directory.',{'argv':{'type':'array','items':S},'timeout_s':{'type':'number'}},['argv']),
    function('ask_user','Ask the user for information.',{'question':S},['question']),
    function('submit','Submit one IFC file from the working directory.',{'path':S},['path']),
]


class ChatExecutor(DirectRunner):
    def __init__(self,root,run_id,*,gateway_url,model,max_output_tokens=65536,
                 isolated=True,evidence_class='live_provider',request_timeout_s=1800):
        super().__init__(root,run_id)
        self.gateway_url,self.model=gateway_url,model
        self.max_output_tokens,self.request_timeout_s=max_output_tokens,request_timeout_s
        self.evidence_class=evidence_class
        if isolated:
            self.tools=ContainerTools(self.workspace,tool_seconds=self.ledger.snapshot(run_id)['limits']['tool_seconds'])

    def messages(self):
        events=self.ledger.events(self.run_id)
        results={e['payload']['action_id']:e['payload'] for e in events if e['kind']=='chat_tool_result'}
        messages=submission_messages(events)
        for event in events:
            kind,p=event['kind'],event['payload']
            if kind=='initial_message':messages.append(p)
            elif kind=='chat_assistant':
                message=p['message']
                messages.append({k:message[k] for k in ('role','content','tool_calls','reasoning_content','reasoning','refusal') if k in message})
                for index,_ in enumerate(message.get('tool_calls',[]) or []):
                    result=results.get(f'chat-{event["seq"]}-{index}')
                    if result:messages.append({'role':'tool','tool_call_id':result['api_id'],'content':json.dumps(result['result'],ensure_ascii=False)})
                for answer in events:
                    if answer['kind']=='answer' and answer['payload']['question_id'].startswith(f'chat-{event["seq"]}-'):
                        messages.append({'role':'user','content':answer['payload']['text']})
        return messages

    def pending(self):
        events=self.ledger.events(self.run_id)
        done={e['payload']['action_id'] for e in events if e['kind']=='chat_tool_result'}
        started={e['payload']['action_id'] for e in events if e['kind']=='chat_tool_started'}
        for event in events:
            if event['kind']!='chat_assistant':continue
            for index,tool in enumerate(event['payload']['message'].get('tool_calls',[])):
                action_id=f'chat-{event["seq"]}-{index}'
                if action_id in done:continue
                if action_id in started:
                    raise ValueError('TOOL_RECOVERY_REQUIRED_NO_AUTOMATIC_REEXECUTION')
                claimed=self.ledger.record(self.run_id,'chat_tool_started',{'action_id':action_id,'tool':tool},event_id='start:'+action_id)
                if not claimed:raise ValueError('TOOL_RECOVERY_REQUIRED_ALREADY_CLAIMED')
                args=json.loads(tool['function']['arguments'])
                name=tool['function']['name']
                result=None
                if name=='ask_user':
                    result={'status':'awaiting_user'}
                    self.ledger.ask(self.run_id,question_id=action_id,text=args['question'])
                elif name=='submit':
                    result={'status':self.submit(args['path'])['status']}
                else:
                    state=self.ledger.snapshot(self.run_id)
                    remaining=state['limits']['active_seconds']-state['active_elapsed_s']
                    if remaining<=0:
                        return self.ledger.finish(self.run_id,'budget_exhausted')
                    self.tools.tool_seconds=min(state['limits']['tool_seconds'],remaining)
                    self.ledger.activity(self.run_id,action_id,begin=True)
                    try:
                        if name not in {'read_file','write_file','replace_text','list_files','execute'}:
                            raise ValueError('UNKNOWN_TOOL')
                        result=getattr(self.tools,name)(**args)
                        if name=='execute' and not result['quiescent']:
                            raise RuntimeError('PROCESS_STOP_NOT_CONFIRMED')
                    except (OSError,ValueError,KeyError,TypeError) as error:
                        result={'error':type(error).__name__,'detail':str(error)}
                    finally:
                        if name!='execute' or (result and result.get('quiescent')) or getattr(self.tools,'quiescent',False):
                            self.ledger.activity(self.run_id,action_id,begin=False)
                self.ledger.record(self.run_id,'chat_tool_result',{'action_id':action_id,'api_id':tool['id'],'result':result},event_id='result:'+action_id)
                if name in {'ask_user','submit'}:
                    return self.ledger.snapshot(self.run_id)
        return self.ledger.snapshot(self.run_id)

    def run(self):
        with task_owner(self.root,self.run_id):
            return self._run_owned()

    def _run_owned(self):
        state=self.ledger.snapshot(self.run_id)
        if state['arm'] not in {'A','C'}:raise ValueError('DIRECT_REQUIRES_A_OR_C')
        if state['status']=='ready':self.ledger.start(self.run_id)
        while self.ledger.snapshot(self.run_id)['status']=='running':
            current=self.ledger.snapshot(self.run_id)
            if current['activities'] or any(c['state']=='inflight' for c in self.ledger.calls(self.run_id)):
                raise ValueError('RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
            try:
                state=self.pending()
                if state['status']!='running':return state
                body={'model':self.model,'messages':self.messages(),'tools':TOOLS,'stream':False}
                if state['arm']=='A':
                    body.update(max_tokens=self.max_output_tokens,thinking={'type':'enabled'})
                else:
                    body.update(max_completion_tokens=self.max_output_tokens,reasoning_effort='high',store=False)
                with httpx.Client(timeout=self.request_timeout_s,trust_env=False) as client:
                    response=client.post(self.gateway_url+'/chat/completions',json=body)
                if response.status_code == 403:
                    try:
                        denial = response.json()
                    except ValueError:
                        denial = None
                    if isinstance(denial, dict) and denial.get('origin') == 'repair-controller' and denial.get('error') in {
                            'TOKEN_BUDGET_EXHAUSTED', 'CALL_BUDGET_EXHAUSTED', 'TIME_BUDGET_EXHAUSTED'}:
                        raise ValueError(denial['error'])
                response.raise_for_status()
                payload=response.json()
                choice=payload['choices'][0]
                if choice['finish_reason'] not in {'stop','tool_calls'}:
                    raise ValueError('TRUNCATED_OR_UNSUPPORTED_FINISH')
                message=choice['message']
                if message.get('role')!='assistant':raise ValueError('ASSISTANT_ROLE_REQUIRED')
                ids=set()
                for tool in message.get('tool_calls',[]) or []:
                    if not isinstance(tool['id'],str) or tool['id'] in ids:raise ValueError('INVALID_TOOL_CALL_ID')
                    ids.add(tool['id'])
                    if tool.get('type')!='function' or not isinstance(json.loads(tool['function']['arguments']),dict):
                        raise ValueError('INVALID_TOOL_ARGUMENTS')
                self.ledger.record(self.run_id,'chat_assistant',{'message':message,'response_id':payload.get('id'),
                    'model_observed':payload.get('model'),'finish_reason':choice['finish_reason'],'evidence_class':self.evidence_class})
                if not message.get('tool_calls'):
                    return self.ledger.finish(self.run_id,'no_output')
            except Exception as error:
                current=self.ledger.snapshot(self.run_id)
                if 'RECOVERY' in str(error) or current['activities'] or any(c['state']=='inflight' for c in self.ledger.calls(self.run_id)):
                    raise
                return self.ledger.finish(self.run_id,'budget_exhausted' if 'BUDGET' in str(error) else 'runtime_error',detail=f'{type(error).__name__}: {error}')
        return self.ledger.snapshot(self.run_id)
