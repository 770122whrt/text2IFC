"""Relay exposes only task-scoped endpoints to the fixed host controller."""
import io
import importlib

import pytest


@pytest.mark.parametrize('endpoint',['v1/messages','v1/chat/completions','questions','v1/search/messages'])
def test_task_route_forwards_only_to_fixed_controller(monkeypatch,endpoint):
    monkeypatch.setenv('REPAIR_CONTROLLER_PORT','1836')
    relay=importlib.import_module('scripts.ifc_repair.repair_comparison.container_relay')
    requests=[]
    class Response:
        status=200
        def getheader(self,*args):return 'application/json'
        def read1(self,*args):return b''
    class Connection:
        def __init__(self,host,port,**kwargs):
            assert host=='host.docker.internal' and port==1836
        def request(self,*args):requests.append(args)
        def getresponse(self):return Response()
        def close(self):pass
    monkeypatch.setattr(relay.http.client,'HTTPConnection',Connection)
    handler=object.__new__(relay.Handler)
    handler.path='/'+32*'a'+'/'+endpoint
    handler.headers={'Content-Length':'2'}
    handler.rfile=io.BytesIO(b'{}')
    handler.wfile=io.BytesIO()
    statuses=[]
    handler.send_response=lambda status:statuses.append(status)
    handler.send_error=lambda status:statuses.append(status)
    handler.send_header=lambda *args:None
    handler.end_headers=lambda:None
    handler.do_POST()
    assert statuses==[200]
    assert requests[0][:3]==('POST',handler.path,b'{}')


@pytest.mark.parametrize('path',[
    '/control/'+32*'a'+'/answer','https://example.invalid/messages',
    '/'+32*'a'+'/v1/search/other','/'+32*'a'+'/v1/search/messages?url=https://example.invalid',
    '/'+32*'a'+'/v1/search/../messages','/bad-token/v1/search/messages',
])
def test_unoffered_routes_are_rejected_before_body_read(monkeypatch,path):
    monkeypatch.setenv('REPAIR_CONTROLLER_PORT','1836')
    relay=importlib.import_module('scripts.ifc_repair.repair_comparison.container_relay')
    handler=object.__new__(relay.Handler)
    handler.path=path
    statuses=[]
    handler.send_error=lambda status:statuses.append(status)
    handler.do_POST()
    assert statuses==[404]
