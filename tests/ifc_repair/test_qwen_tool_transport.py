"""Native Qwen tool text is a wire format, never a trusted executable."""
import json
import httpx
import pytest
from scripts.ifc_repair.qwen_tools import decode_tools, ToolGateway
from scripts.ifc_repair.repair_comparison.isolated_direct import TOOLS
from scripts.ifc_repair.qwen_batch import QwenPolicy
from tests.ifc_repair.test_qwen_batch import make_ledger

def text(name, params):
    return '<tool_call>\n<function='+name+'>\n'+''.join('<parameter='+k+'>\n'+v+'\n</parameter>\n' for k,v in params.items())+'</function>\n</tool_call>'

def test_read_typed_arguments():
    content=text('read_file',{'path':'request.txt','offset':'0','limit':'4096'})
    result=decode_tools(content,TOOLS)
    assert result[0]['function']['name']=='read_file'
    assert json.loads(result[0]['function']['arguments'])=={'path':'request.txt','offset':0,'limit':4096}
    assert result==decode_tools(content,TOOLS)

@pytest.mark.parametrize('name,params,expected', [
    ('execute', {'argv':'["python", "check.py"]','timeout_s':'10.5'}, {'argv':['python','check.py'],'timeout_s':10.5}),
    ('write_file', {'path':'a.py','text':'if x < 2:\n    print("<&")'}, {'path':'a.py','text':'if x < 2:\n    print("<&")'}),
    ('submit', {'path':'repaired.ifc'}, {'path':'repaired.ifc'}),
])
def test_types_and_literal_code(name,params,expected):
    assert json.loads(decode_tools(text(name,params),TOOLS)[0]['function']['arguments'])==expected

@pytest.mark.parametrize('content', [text('delete_everything',{}),text('submit',{}),text('execute',{'argv':'bad'}),text('read_file',{'path':'a','offset':'true'}),text('read_file',{'path':'a','extra':'b'}),'<tool_call><function=read_file>','<tool_call>{broken}</tool_call>'])
def test_invalid_calls_fail_closed(content):
    with pytest.raises(ValueError): decode_tools(content,TOOLS)

def test_multiple_calls_and_final_text():
    calls=decode_tools('Checking.\n'+text('list_files',{})+text('read_file',{'path':'request.txt'}),TOOLS)
    assert len(calls)==2 and len({c['id'] for c in calls})==2
    assert decode_tools('Unable to repair.',TOOLS)==[]
    calls=decode_tools('<tool_call>{"name":"submit","arguments":{"path":"done.ifc"}}</tool_call>',TOOLS)
    assert calls[0]['function']['name']=='submit'

@pytest.mark.parametrize('arm', ['F','G'])
def test_gateway_preserves_raw_usage_and_f_route(tmp_path,arm):
    ledger=make_ledger(tmp_path,arm)
    received=[]
    native=text('read_file',{'path':'request.txt'})
    def transport(request):
        received.append(json.loads(request.content))
        return httpx.Response(200,json={'id':'test','model':'qwen','choices':[{'message':{'role':'assistant','content':native},'finish_reason':'stop'}], 'usage':{'prompt_tokens':100,'completion_tokens':30,'total_tokens':130}})
    with ToolGateway(ledger,tmp_path/'wire',policy=QwenPolicy(),transport=httpx.MockTransport(transport)) as gateway:
        token=gateway.register('case-'+arm,model='qwen',api_key=None,endpoints={'chat':'https://fake.test/chat'},evidence_class='fake',max_output_tokens=512)
        request={'model':'qwen','messages':[{'role':'user','content':'Read the public request.'}],'max_tokens':512,'stream':False}
        if arm=='G':request['tools']=TOOLS
        response=httpx.post(gateway.url+'/'+token+'/v1/chat/completions',json=request,trust_env=False)
    assert response.status_code==200
    assert ledger.snapshot('case-'+arm)['usage']['known_total_tokens']==130
    if arm=='G':
        assert received[0]['tool_choice'] is None and received[0]['tools']==TOOLS
        assert response.json()['choices'][0]['finish_reason']=='tool_calls'
        assert response.json()['choices'][0]['message']['tool_calls']
        assert ledger.calls('case-G')[0]['response']['body']['choices'][0]['message']['content']==native
    else:
        assert 'tool_choice' not in received[0]
        assert response.json()['choices'][0]['message']['content']==native
