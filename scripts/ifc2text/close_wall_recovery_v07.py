"""Read-only evaluation and explicit offline closure counterfactual; never a live pass."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.recover_wall_v07 import OUT,SOURCE
from scripts.ifc2text.attribute_roundtrip_v01 import dump,load
from scripts.ifc2text.probe_polygon_wall_backend_v01 import measured_geometry
from scripts.ifc2text.compact_campaign import budget_for
from text2ifc_ifc2text.observation import all_items
from text2ifc_ifc2text.wall_details_v08 import explicit_description,single_wall_description,closed_ring
from text2ifc_compiler import compile_document
import ifcopenshell
from shapely.geometry import Polygon


def main():
    output=OUT/'closeout-v08';output.mkdir(parents=True,exist_ok=False)
    original_bytes=SOURCE.read_bytes()
    facts=load(OUT/'host-normalized/source-facts.json')
    narration=load(OUT/'host-normalized/writing-v07/parsed-response.json')
    final_text=explicit_description(facts,narration)
    (output/'hxp-description.md').write_text(final_text,encoding='utf-8',newline='\n')
    wall=load(OUT/'single-wall-evaluator-only.json')
    (output/'single-wall-description-v08.txt').write_text(single_wall_description(wall),encoding='utf-8',newline='\n')
    model=ifcopenshell.open(str(SOURCE)); details=[]
    for category,item in all_items(facts):
        if category!='walls' or not item['solid_detail'].get('requires_explicit_outline'):continue
        detail=item['solid_detail'];entity=model.by_guid(item['source_global_id'])
        raw_bounds,raw_outline=measured_geometry(entity)
        text=closed_ring(detail['bottom_outline_xy_mm'])
        points=[[float(x) for x in re.findall(r'-?\d+\.\d+',p)] for p in text.split('→')]
        assert points[0]==points[-1]
        outline=Polygon(points)
        delta=raw_outline.boundary.hausdorff_distance(outline.boundary)
        details.append({'label':item['label'],'closed':True,'vertex_count_with_closure':len(points),
            'source_mesh_vs_text_outline_hausdorff_mm':delta,
            'z_bottom_delta_mm':abs(raw_bounds['z'][0]-detail['bottom_z_mm']),
            'height_delta_mm':abs(raw_bounds['z'][1]-raw_bounds['z'][0]-detail['height_mm'])})
    assert all(r['source_mesh_vs_text_outline_hausdorff_mm']<.1 for r in details)
    raw_path=OUT/'live-generator/generator/parsed-output.json'; raw_bytes=raw_path.read_bytes()
    raw=load(raw_path); graph=copy.deepcopy(raw)
    walls=[e for e in graph['entities'] if e['ifc_class']=='IfcWall']; assert len(walls)==1
    profile=walls[0]['attributes']['Representation']['profile']; assert profile['kind']=='polygon'
    assert profile['points'][0]!=profile['points'][-1]
    profile['points'].append(copy.deepcopy(profile['points'][0]))
    counter=output/'offline-closure-counterfactual'; counter.mkdir()
    dump(counter/'candidate.json',graph)
    compiled=compile_document(graph,counter/'compiled-offline-counterfactual.ifc')
    assert compiled.success
    candidate=ifcopenshell.open(str(counter/'compiled-offline-counterfactual.ifc'))
    target=candidate.by_type('IfcWall')[0]
    source=model.by_guid(wall['source_global_id'])
    a,pa=measured_geometry(source); b,pb=measured_geometry(target)
    comparison={'evidence_kind':'offline_counterfactual_on_copy_of_live_invalid_json',
        'only_edit':'append first point to polygon points; no source geometry added',
        'new_live_success':False,'compile_success':compiled.success,'opening_subtraction':False,
        'source_vs_counterfactual_max_bbox_coordinate_delta_mm':max(abs(x-y) for k in a for x,y in zip(a[k],b[k])),
        'source_vs_counterfactual_outline_hausdorff_mm':pa.boundary.hausdorff_distance(pb.boundary),
        'source_vs_counterfactual_symmetric_difference_mm2':pa.symmetric_difference(pb).area}
    dump(counter/'comparison.json',comparison)
    budget=budget_for(load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json'))
    budget.halt('REAL_GENERATOR_OPEN_POLYGON_PROFILE_REQUIRES_REVALIDATED_RETRY_AND_CALL_AUTHORIZATION')
    state=budget.snapshot(); dump(output/'budget.json',state)
    assert raw_path.read_bytes()==raw_bytes and SOURCE.read_bytes()==original_bytes
    summary={'schema_version':'text2ifc/wall-recovery-closeout/0.8',
        'wall_description':'implemented_with_explicit_closed_world_outline',
        'source_normalization':load(OUT/'source-normalization.json'),
        'text':{'path':'hxp-description.md','characters':len(final_text),'prompt':'ifc2text-compact-narrator.v0.7',
            'renderer':'wall-detail/0.8','reused_narration':'host-normalized/writing-v07/parsed-response.json',
            'note':'No new LLM writing call for v0.8; only explicit closure and common wording assembly changed.'},
        'wall_detail_checks':details,'forward_system_modified':False,
        'live_brief_status':'ready','live_generator_status':'invalid_OPEN_POLYGON_PROFILE',
        'live_polygon_choice':'polygon with correct displayed vertices but omitted final closure point',
        'v08_live_retry_done':False,'offline_counterfactual':comparison,
        'limitations':['Single-wall diagnostic excluded openings, materials and full-building acceptance.',
            'Host-storey normalization is an explicit modeling policy, not proof the archived source violates IFC.',
            'No raw LLM response was edited or promoted to accepted output.'],
        'budget':{'used_or_reserved':state['tokens_used_or_reserved'],'limit':state['limits']['tokens'],
            'calls':state['calls'],'call_limits':{'writing':26,'reconstruction':12}},
        'raw_provider_and_source_preserved':True}
    dump(output/'summary.json',summary)
    print(json.dumps({'characters':len(final_text),'detailed_walls':len(details),
        'max_text_outline_error_mm':max(r['source_mesh_vs_text_outline_hausdorff_mm'] for r in details),
        'offline_counterfactual':comparison,'budget':summary['budget']},ensure_ascii=True,indent=2))

if __name__=='__main__':main()
