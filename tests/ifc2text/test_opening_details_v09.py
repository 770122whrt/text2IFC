"""Independent geometry family for the new exact opening-description path."""
import copy
import importlib
import importlib.util
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit
import numpy as np
import pytest
from shapely.geometry import Polygon, MultiPoint

from text2ifc_compiler import compile_document
from text2ifc_ifc2text.wall_compare_v09 import wall_mesh, volume_mm3


def api():
    assert importlib.util.find_spec('text2ifc_ifc2text.opening_details_v09') is not None, 'Exact opening profile extraction is missing'
    return importlib.import_module('text2ifc_ifc2text.opening_details_v09')


def model_with_opening(tmp_path, *, angle=0., horizontal=False, unit='MILLIMETER'):
    doc = json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    path = tmp_path/'source.ifc'
    assert compile_document(doc,path).success
    model=ifcopenshell.open(str(path))
    wall=model.by_type('IfcWall')[0]
    wall.ObjectPlacement.RelativePlacement.RefDirection=model.createIfcDirection((.6,.8,0.))
    opening=model.by_type('IfcOpeningElement')[0]
    solid=opening.Representation.Representations[0].Items[0]
    solid.Position.Location.Coordinates=(17.,-29.,37.)
    a=math.radians(angle)
    if horizontal:
        solid.Position.Axis=model.createIfcDirection((math.cos(a),math.sin(a),0.))
        solid.Position.RefDirection=model.createIfcDirection((0.,0.,1.))
        solid.SweptArea.XDim=2100.
        solid.SweptArea.YDim=900.
        solid.Depth=200.
    else:
        solid.Position.RefDirection=model.createIfcDirection((math.cos(a),math.sin(a),0.))
        solid.SweptArea.Position.Location.Coordinates=(13.,-7.)
        solid.SweptArea.Position.RefDirection=model.createIfcDirection((.8,.6))
    if unit=='METER':
        model=ifcopenshell.util.unit.convert_file_length_units(model,'METER')
    model.write(str(path))
    return path, model, model.by_type('IfcOpeningElement')[0]


@pytest.mark.parametrize('angle,horizontal,unit', [(a,h,u) for a in (0.,30.,89.9,90.) for h in (False,True) for u in ('MILLIMETER','METER')])
def test_exact_profile_matches_native_mesh_under_nested_transforms(tmp_path,angle,horizontal,unit):
    path,model,opening=model_with_opening(tmp_path,angle=angle,horizontal=horizontal,unit=unit)
    frozen=path.read_bytes()
    detail=api().read_opening_solid(opening,ifcopenshell.util.unit.calculate_unit_scale(model)*1000.)
    assert detail['status']=='supported_vertical_prism'
    polygon=Polygon(detail['bottom_outline_xy_mm'])
    verts,faces=wall_mesh(opening,subtract_openings=False)
    native=MultiPoint(verts[:,:2]).convex_hull
    assert polygon.boundary.hausdorff_distance(native.boundary)<1e-6
    assert polygon.area==pytest.approx(180000.,abs=1e-5)
    assert detail['bottom_z_mm']==pytest.approx(float(verts[:,2].min()),abs=1e-6)
    assert detail['height_mm']==pytest.approx(2100.,abs=1e-6)
    assert polygon.area*detail['height_mm']==pytest.approx(volume_mm3(verts,faces),rel=1e-9)
    assert detail['bottom_outline_xy_mm'][0]==detail['bottom_outline_xy_mm'][-1]
    assert path.read_bytes()==frozen


@pytest.mark.parametrize('change,reason', [('tilted','NOT_WORLD_VERTICAL_PRISM'),('circle','UNSUPPORTED_PROFILE'),('multiple','REQUIRES_SINGLE_EXTRUDED_SOLID'),('direction','INVALID_EXTRUSION_DIRECTION')])
def test_unsupported_shapes_never_become_bbox_profiles(tmp_path,change,reason):
    _,_,opening=model_with_opening(tmp_path)
    solid=opening.Representation.Representations[0].Items[0]
    model=opening.file
    if change=='tilted': solid.ExtrudedDirection.DirectionRatios=(.2,0.,1.)
    elif change=='circle': solid.SweptArea=model.createIfcCircleProfileDef('AREA',None,solid.SweptArea.Position,100.)
    elif change=='multiple': opening.Representation.Representations[0].Items=(solid,solid)
    elif change=='direction': solid.ExtrudedDirection.DirectionRatios=(0.,0.,0.)
    detail=api().read_opening_solid(opening,1.)
    assert detail['status']=='unsupported'
    assert detail['reason']==reason
    assert 'bottom_outline_xy_mm' not in detail


def test_v09_prepare_renders_true_opening_and_v08_stays_old(tmp_path):
    from text2ifc_ifc2text.compact_pipeline import prepare_compact,render_prepared_description
    from text2ifc_ifc2text.observation import extract_description_facts,all_items
    from text2ifc_ifc2text.wall_details_v07 import enrich_wall_details
    from text2ifc_ifc2text.wall_details_v08 import explicit_description
    path,_,_=model_with_opening(tmp_path,angle=30.,horizontal=True)
    api()
    before=path.read_bytes()
    old=prepare_compact(path,tmp_path/'old',description_version='0.8')
    old_bytes=(tmp_path/'old/design-description-deterministic.md').read_bytes()
    new=prepare_compact(path,tmp_path/'new',description_version='0.9')
    facts=json.loads((tmp_path/'new/source-facts.json').read_text(encoding='utf-8'))
    text=(tmp_path/'new/design-description-deterministic.md').read_text(encoding='utf-8')
    assert new['description_version']=='0.9' and old['description_version']=='0.8'
    assert '**开口 O001 的切割实体**' in text
    assert '不得把表格外包尺寸当成矩形截面' in text
    assert '末尾闭合点不可省略' in text
    assert render_prepared_description(facts)==text
    assert path.read_bytes()==before
    assert (tmp_path/'old/design-description-deterministic.md').read_bytes()==old_bytes
    source_facts=enrich_wall_details(path,extract_description_facts(path))
    assert explicit_description(source_facts)==old_bytes.decode('utf-8')
    original=copy.deepcopy(source_facts)
    enriched=api().enrich_opening_details(path,source_facts)
    assert source_facts==original
    assert next(item for category,item in all_items(enriched) if category=='openings')['opening_solid_detail']['status']=='supported_vertical_prism'


def test_negative_extrusion_and_concave_native_profile_are_not_convexified(tmp_path):
    _,model,opening=model_with_opening(tmp_path)
    solid=opening.Representation.Representations[0].Items[0]
    points=[(0.,0.),(900.,0.),(900.,200.),(500.,200.),(500.,100.),(400.,100.),(400.,200.),(0.,200.),(0.,0.)]
    curve=model.createIfcPolyline([model.createIfcCartesianPoint(point) for point in points])
    solid.SweptArea=model.createIfcArbitraryClosedProfileDef('AREA',None,curve)
    solid.ExtrudedDirection.DirectionRatios=(0.,0.,-1.)
    detail=api().read_opening_solid(opening,1.)
    assert detail['status']=='supported_vertical_prism'
    polygon=Polygon(detail['bottom_outline_xy_mm'])
    assert polygon.area==pytest.approx(170000.)
    vertices,faces=wall_mesh(opening,subtract_openings=False)
    assert detail['bottom_z_mm']==pytest.approx(vertices[:,2].min())
    assert polygon.area*detail['height_mm']==pytest.approx(volume_mm3(vertices,faces),rel=1e-9)


def test_narrator_v07_keeps_v09_geometry_in_deterministic_text(tmp_path):
    from text2ifc_ifc2text.compact_pipeline import prepare_compact,write_compact
    from text2ifc_agent.providers import ProviderOutput
    path,_,_=model_with_opening(tmp_path,angle=30.,horizontal=True)
    prepared=tmp_path/'prepared'
    prepare_compact(path,prepared,description_version='0.9')
    facts=json.loads((prepared/'source-facts.json').read_text(encoding='utf-8'))
    deterministic=(prepared/'design-description-deterministic.md').read_text(encoding='utf-8')
    class Narrator:
        def generate_candidate(self,**kwargs):
            return ProviderOutput(json.dumps({'overview':'建筑按标高组织。','storey_notes':[{'storey':s['label'],'text':'本层构件见明细。'} for s in facts['storeys']]},ensure_ascii=False),{'evidence_class':'offline_fake'})
    write_compact(output=prepared,provider=Narrator(),template_id='ifc2text-compact-narrator.v0.7')
    written=(prepared/'design-description.md').read_text(encoding='utf-8')
    expected=[line for line in deterministic.splitlines() if line.startswith('**开口 ')]
    assert expected and all(line in written for line in expected)


def test_brief28_and_generator25_transport_explicit_opening_polygon(tmp_path):
    """Fake outputs verify transport/contracts, never claimed as model capability."""
    from text2ifc_ifc2text.compact_pipeline import prepare_compact
    from text2ifc_agent.live_pipeline import run_design_brief_stage,run_generator_stage
    from tests.agent.test_semantic_authority_completeness import valid_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from tests.agent.test_generation_v24_route import fixture_candidate
    from text2ifc_ifc2text.observation import all_items
    path,_,_=model_with_opening(tmp_path,angle=30.,horizontal=True)
    prepared=tmp_path/'prepared'
    prepare_compact(path,prepared,description_version='0.9')
    text=(prepared/'design-description-deterministic.md').read_text(encoding='utf-8')
    facts=json.loads((prepared/'source-facts.json').read_text(encoding='utf-8'))
    item=next(item for category,item in all_items(facts) if category=='openings')
    detail=item['opening_solid_detail']
    opening={'id':'opening-1','host_wall':'wall-1','polygon':detail['bottom_outline_xy_mm'],
             'z_mm':[detail['bottom_z_mm'],detail['bottom_z_mm']+detail['height_mm']], 'coordinate_frame':'world'}
    case,brief=valid_brief()
    case['user_request']=text
    case['conversation']=[{'turn_id':'turn-user-001','role':'user','content':text}]
    brief['schema_version']='text2ifc/design-brief/2.8'
    brief['original_request']=text
    brief['known_facts']={'storeys':[{'id':'storey-1','elevation_mm':0.,'openings':[opening]}],
                          'semantic_requirements':[], 'semantic_review':brief['known_facts']['semantic_review'],
                          'plan_constraints':[]}
    source=tmp_path/'design-brief'
    result=run_design_brief_stage(provider=SequenceProvider([brief]),output_dir=source,case=case,design_brief_schema_version='text2ifc/design-brief/2.8')
    assert result['valid'],json.dumps(result,ensure_ascii=False)
    saved=json.loads((source/'design-brief.json').read_text(encoding='utf-8'))
    assert saved['known_facts']['storeys'][0]['openings'][0]==opening
    assert (source/'input.txt').read_text(encoding='utf-8')==text+'\n'
    (tmp_path/'generation-contract.json').write_text(json.dumps({'schema_version':'text2ifc/generation-contract-selection/1.0','bim_json_schema_version':'bim-json/2.5','generation_strategy':'legacy_full'}),encoding='utf-8')
    candidate=fixture_candidate()
    candidate['schema_version']='bim-json/2.5'
    generated=run_generator_stage(provider=SequenceProvider([candidate]),output_dir=tmp_path/'generator',design_source_dir=source,case_id='opening-transport')
    assert generated['valid'],generated
    inputs=json.loads((tmp_path/'generator/prompt-render-input.json').read_text(encoding='utf-8'))
    assert inputs['USER_REQUEST']==text.rstrip('\r\n')
    assert inputs['DESIGN_BRIEF']['known_facts']['storeys'][0]['openings'][0]==opening
