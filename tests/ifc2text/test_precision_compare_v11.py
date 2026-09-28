"""The user-approved current policy accepts linear errors up to 1 mm."""
import copy
import json
from pathlib import Path
import pytest
from tests.ifc2text.test_diagnostic_review import facts,item

@pytest.mark.parametrize('category',['walls','openings','doors','windows','spaces','stairs','slabs','coverings'])
@pytest.mark.parametrize('shift,changed',[(.1,False),(.9996,False),(1.,False),(1.001,True)])
def test_all_categories_accept_up_to_one_mm(category,shift,changed):
    from text2ifc_ifc2text.precision_compare_v11 import compare_observations
    r=compare_observations(facts(**{category:[item('A')]}),facts(**{category:[item('B',shift)]}))
    assert r['categories'][category]['matched'][0]['geometry_outside_tolerance'] is changed
    assert r['tolerances']['linear_mm']==1.

@pytest.mark.parametrize('delta,changed',[(1.,False),(1.001,True)])
def test_material_thickness_and_storey_elevation_share_policy(delta,changed):
    from text2ifc_ifc2text.precision_compare_v11 import compare_observations
    a=facts(walls=[item('A')]);b=copy.deepcopy(a)
    a['storeys'][0]['walls'][0]['materials']=[{'kind':'material_layer_set','layers':[{'name':'Brick','thickness_mm':200.}]}]
    b['storeys'][0]['walls'][0]['materials']=[{'kind':'material_layer_set','layers':[{'name':'Brick','thickness_mm':200.+delta}]}]
    b['storeys'][0]['elevation_mm']+=delta
    r=compare_observations(a,b)
    assert r['summary']['material_content_differences']==int(changed)
    assert r['summary']['storey_elevation_deviations']==int(changed)

def test_rescoring_does_not_mutate_old_evidence_or_erase_missing_components():
    from text2ifc_ifc2text.precision_compare_v10 import compare_observations
    from text2ifc_ifc2text.precision_compare_v11 import rescore
    old=compare_observations(facts(doors=[item('A'),item('MISSING',5000)]),facts(doors=[item('B',.5)]))
    before=copy.deepcopy(old);new=rescore(old)
    assert old==before and old['summary']['geometric_deviations']==1
    assert new['summary']['geometric_deviations']==0 and new['summary']['missing']==1
    assert new['status']['reconstruction_consistent'] is False

@pytest.mark.parametrize('shift,changed',[(.9996,False),(1.,False),(1.001,True)])
def test_current_campaign_uses_one_mm_on_real_ifc(tmp_path,shift,changed):
    from scripts.ifc2text.compact_campaign import compare_roundtrip
    from text2ifc_compiler import compile_document
    doc=json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    a=tmp_path/'a.ifc';b=tmp_path/'b.ifc';assert compile_document(doc,a).success
    target=next(e for e in doc['entities'] if e['id']=='wall-1')
    target['attributes']['ObjectPlacement']['origin'][0]+=shift
    assert compile_document(doc,b).success
    before=a.read_bytes();r=compare_roundtrip(a,b)
    assert r['schema_version']=='text2ifc/ifc2text-roundtrip-compare/1.1'
    assert (r['summary']['geometric_deviations']>0) is changed
    assert r['categories']['walls']['matched'][0]['wall_geometry']['pass'] is not changed
    assert before==a.read_bytes()
