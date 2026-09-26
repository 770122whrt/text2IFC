import copy
import json

import pytest

from tests.compiler.test_polygon_wall_hosts_v24 import document, record, positioned_profile


def open_document():
    value=document();value['schema_version']='bim-json/2.6'
    record(value,'wall-1')['attributes']['Representation']['profile']['points'].pop()
    return value


@pytest.mark.parametrize('reverse,rotate',[(False,False),(True,False),(False,True)])
def test_closure_preserves_every_vertex_and_material(tmp_path,reverse,rotate):
    from text2ifc_agent.polygon_closure import recover_polygon_closures
    value=open_document()
    if rotate:positioned_profile(value)
    points=record(value,'wall-1')['attributes']['Representation']['profile']['points']
    if reverse:points.reverse()
    before=copy.deepcopy(value)
    result=recover_polygon_closures(value)
    assert result['eligible']
    after=result['candidate']
    closed=record(after,'wall-1')['attributes']['Representation']['profile']['points']
    assert closed==points+[points[0]]
    assert value==before
    assert record(after,'wall-1')['materials']==record(before,'wall-1')['materials']
    assert len(result['appended_paths'])==1
    from text2ifc_compiler import compile_document
    import ifcopenshell
    compiled=compile_document(after,tmp_path/'closed.ifc')
    assert compiled.success
    assert len(ifcopenshell.open(str(compiled.output_path)).by_type('IfcWall'))==1


@pytest.mark.parametrize('fault',['old-version','self-cross','short','nan','boolean','duplicate','zero-area','wrong-material','missing-provenance'])
def test_ambiguous_or_other_invalid_content_is_not_recovered(fault):
    from text2ifc_agent.polygon_closure import recover_polygon_closures
    value=open_document();wall=record(value,'wall-1')
    points=wall['attributes']['Representation']['profile']['points']
    if fault=='old-version':value['schema_version']='bim-json/2.5'
    elif fault=='self-cross':points[:]=[[0,0],[2,2],[0,2],[2,0]]
    elif fault=='short':points[:]=[[0,0],[1,0]]
    elif fault=='nan':points[0][0]=float('nan')
    elif fault=='boolean':points[0][0]=True
    elif fault=='duplicate':points.insert(1,points[0][:])
    elif fault=='zero-area':points[:]=[[0,0],[1,0],[2,0]]
    elif fault=='wrong-material':wall['materials'][0]['layers'][0]['thickness']=10
    elif fault=='missing-provenance':value.pop('provenance')
    assert not recover_polygon_closures(value)['eligible']


def test_closed_input_is_not_rewritten():
    from text2ifc_agent.polygon_closure import recover_polygon_closures
    value=document();value['schema_version']='bim-json/2.6'
    assert not recover_polygon_closures(value)['eligible']


def test_open_polygon_only_repair_needs_no_provider(tmp_path):
    from tests.agent.test_generation_v24_route import prepare_source
    from tests.agent.test_component_requirements_v26 import component_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_generator_stage,run_repair_stage
    source=prepare_source(tmp_path,selected=False)
    (source/'design-brief.json').write_text(json.dumps(component_brief()),encoding='utf-8')
    run_generator_stage(provider=SequenceProvider([open_document()]),output_dir=tmp_path/'generator',design_source_dir=source,case_id='closure')
    result=run_repair_stage(provider_factory=lambda:pytest.fail('Syntax closure must not call Provider'),output_dir=tmp_path/'repair',generator_source_dir=tmp_path/'generator',case_id='closure')
    assert result['valid'] and result['provider_call_count']==0
    assert result['evidence_class']=='deterministic-derived-no-call'


@pytest.mark.parametrize('extra_change',[False,True])
def test_production_repair_can_close_rings_but_cannot_hide_unoffered_changes(tmp_path,extra_change):
    from tests.agent.test_generation_v24_route import prepare_source
    from tests.agent.test_component_requirements_v26 import component_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_generator_stage,run_repair_stage
    value=open_document();raw_repaired=copy.deepcopy(value);value.pop('provenance')
    if extra_change:record(raw_repaired,'wall-1')['attributes']['Name']='unoffered change'
    source=prepare_source(tmp_path,selected=False)
    (source/'design-brief.json').write_text(json.dumps(component_brief()),encoding='utf-8')
    result=run_generator_stage(provider=SequenceProvider([value]),output_dir=tmp_path/'generator',design_source_dir=source,case_id='closure')
    assert not result['valid']
    result=run_repair_stage(provider_factory=lambda:SequenceProvider([raw_repaired]),output_dir=tmp_path/'repair',generator_source_dir=tmp_path/'generator',case_id='closure')
    assert result['valid'] is (not extra_change)
    assert json.loads((tmp_path/'repair/parsed-output.json').read_text(encoding='utf-8'))==raw_repaired
    if not extra_change:
        assert (tmp_path/'repair/polygon-closure-recovery.json').is_file()
        normalized=json.loads((tmp_path/'repair/repaired-candidate.json').read_text(encoding='utf-8'))
        recovery=json.loads((tmp_path/'repair/polygon-closure-recovery.json').read_text(encoding='utf-8'))
        assert all(isinstance(refs,list) for refs in recovery['evidence_by_path'].values())
        pts=record(normalized,'wall-1')['attributes']['Representation']['profile']['points']
        assert pts==record(raw_repaired,'wall-1')['attributes']['Representation']['profile']['points']+[pts[0]]
