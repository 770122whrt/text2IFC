"""Multi-target HTTP contract and per-operation selection readback; no Provider calls."""
import copy
import pytest
from fastapi.testclient import TestClient
from text2ifc_web.app import create_app
from text2ifc_web.selection_guard import check_selection
from tests.web.test_repair_api import source_bytes


def prepared_body(c):
    data,wall,window=source_bytes()
    import ifcopenshell
    m=ifcopenshell.file.from_string(data.decode())
    wall2=m.create_entity('IfcWall',GlobalId=ifcopenshell.guid.new(),Name='Same wall on another side')
    r=c.post('/api/ifc-inputs',files={'file':('multi.ifc',m.to_string().encode())})
    assert r.status_code==201
    pick=lambda o:{'step_id':o.id(),'global_id':o.GlobalId,'view_version':'v1'}
    return {'input_id':r.json()['input_id'],'user_text':'在选中的两面墙上各增加一扇窗。','view_version':'v1','targets':[pick(wall),pick(wall2)],'auxiliary':pick(window)}


def test_multiple_targets_keep_exact_text_names_and_roles(tmp_path):
    with TestClient(create_app(tmp_path,allowed_hosts=('testserver',))) as c:
        body=prepared_body(c)
        r=c.post('/api/repair-requests/prepare',json=body)
        assert r.status_code==201,r.text
        p=r.json()
        assert p['user_text']==body['user_text']
        assert len(p['references']['targets'])==2
        assert p['references']['primary'] is None
        assert 'Same wall on another side' in p['selection_context_text']
        assert '对象 1' in p['selection_context_text'] and '对象 2' in p['selection_context_text']
        assert p['selection_scope']=='explicit_targets'
        assert not p['execution_enabled']


@pytest.mark.parametrize('change',['mixed','duplicate','cross_version','same_aux','too_many'])
def test_ambiguous_or_invalid_multi_contract_is_rejected(tmp_path,change):
    with TestClient(create_app(tmp_path,allowed_hosts=('testserver',))) as c:
        body=prepared_body(c)
        if change=='mixed':body['primary']=body['targets'][0]
        if change=='duplicate':body['targets'].append(body['targets'][0])
        if change=='cross_version':body['targets'][1]['view_version']='old'
        if change=='same_aux':body['auxiliary']=body['targets'][1]
        if change=='too_many':body['targets']*=9
        assert c.post('/api/repair-requests/prepare',json=body).status_code in (409,422)


def batch(targets=('A','B')):
    return {'targets':[{'global_id':x,'ifc_class':'IfcWall'} for x in targets],'primary':None,'auxiliary':None}


def ctx(targets=('A','B')):
    return {'source_ifc_path':None,'resolution':{'operations':[{'operation_id':str(i),'operation_type':'add_window_with_opening_to_wall','target_global_id':x,'parameters':{'width':900}} for i,x in enumerate(targets)]},'installation_references':{},'derivations':[]}


def test_batch_checks_missing_extra_and_duplicate_operations():
    assert check_selection(batch(),ctx())['valid']
    for actual,code in [(('A',),'PICKED_TARGET_MISSING'),(('A','B','C'),'UNSELECTED_TARGET'),(('A','B','A'),'DUPLICATE_TARGET_OPERATION')]:
        result=check_selection(batch(),ctx(actual))
        assert not result['valid']
        assert code in {x['code'] for x in result['issues']}


def test_reference_cannot_be_used_to_cover_a_missing_operation_target():
    refs=batch();refs['auxiliary']={'global_id':'W','ifc_class':'IfcWindow'}
    context=ctx(('A','C'))
    context['derivations']=[{'operation_id':'0','reference_ids':['B']}]
    context['installation_references']={'0':{'reference_global_id':'W'},'1':{'reference_global_id':'W'}}
    assert not check_selection(refs,context)['valid']


def test_multiple_legitimately_distinct_operations_on_one_target_are_allowed():
    context=ctx(('A','B','A'));context['resolution']['operations'][2]['parameters']['width']=1200
    assert check_selection(batch(),context)['valid']
