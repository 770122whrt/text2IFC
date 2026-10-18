from pathlib import Path
import json
import ifcopenshell
from fastapi.testclient import TestClient
from text2ifc_web.app import create_app


def test_readonly_example_requests_do_not_create_tasks_or_expose_other_files(tmp_path):
    examples=tmp_path/'examples';case=examples/'test-case';case.mkdir(parents=True)
    data=ifcopenshell.file(schema='IFC2X3').to_string().encode()
    for name in ('input','result'):(case/(name+'.ifc')).write_bytes(data)
    entry={'id':'test-case','title':'Test','evidence_class':'archived_live','archived_success':True,'request':'test','new_run_executed':False}
    (examples/'catalog.json').write_text(json.dumps({'examples':[entry]}))
    with TestClient(create_app(tmp_path/'store',examples_root=examples,allowed_hosts=('testserver',))) as c:
        catalog=c.get('/api/examples');assert catalog.status_code==200
        e=c.get('/api/examples/test-case').json();assert e['new_run_executed'] is False
        assert c.get(e['input_url']).content==data and c.get(e['result_url']).content==data
        assert c.get('/api/examples/test-case/private').status_code==404
        assert c.get('/api/examples/unknown').status_code==404
        service=c.app.state.repair_service
        with service.store.connect() as db:assert db.execute('select count(*) from tasks').fetchone()[0]==0
