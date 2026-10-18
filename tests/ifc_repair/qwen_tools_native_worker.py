"""Keyless fake Qwen service emitting native tool text for Linux acceptance."""
import json
import httpx
from tests.ifc_repair.repair_comparison.demo_http_fixture import FakeDemoTransport
from scripts.ifc_repair import qwen_tools

original = FakeDemoTransport.__call__

def native_tool_response(self, request):
    response = original(self, request)
    if request.url.path.strip('/').split('/')[0].endswith('-G') and response.status_code == 200:
        body = json.loads(request.content)
        assert 'tool_choice' in body and body['tool_choice'] is None
        payload = response.json()
        choice = payload['choices'][0]
        message = choice['message']
        blocks = []
        for call in message.pop('tool_calls', []):
            function = call['function']
            params = json.loads(function['arguments'])
            blocks.append('<tool_call>\n<function='+function['name']+'>\n'+''.join(
                '<parameter='+key+'>\n'+(value if isinstance(value,str) else json.dumps(value))+'\n</parameter>\n'
                for key,value in params.items())+'</function>\n</tool_call>')
        message['content'], choice['finish_reason'] = '\n'.join(blocks), 'stop'
        return httpx.Response(200,json=payload)
    return response

if __name__ == '__main__':
    FakeDemoTransport.__call__ = native_tool_response
    raise SystemExit(qwen_tools.main())
