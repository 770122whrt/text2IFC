"""Offline integration of the real W013 polygon into the existing full-scene graph.

Uses two already generated BIM JSON artifacts and the unchanged compiler. The
source IFC is evaluator-only. This controlled assembly is NOT a fresh whole-scene
LLM run and is never published as an accepted generation artifact.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
from text2ifc_compiler import compile_document
from text2ifc_contract.placement import world_transform_for
from text2ifc_ifc2text.wall_compare_v09 import compare_wall_entities,compare_with_wall_policy,wall_mesh,volume_mm3
from text2ifc_ifc2text.observation import extract_description_facts,all_items

BASE=ROOT/'dataset/processed/experiments/ifc2text-phase1-20260917/compact-campaign-v06/hxp/reconstruction-128k/runs/de4932f1dad7a868/generator/candidate.json'
DONOR=ROOT/'dataset/processed/experiments/ifc2text-closed-wall-retry-20260921-v08/live-generator/generator/candidate.json'
SOURCE=ROOT/'dataset/processed/experiments/ifc2text-wall-recovery-20260921-v07/hxp-host-normalized.ifc'
DEFAULT_OUT='dataset/processed/experiments/ifc2text-wall-context-20260921-v09'


def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def entity_record(doc,identity):
    rows=[e for e in doc['entities'] if e['id']==identity]
    if len(rows)!=1 or rows[0]['ifc_class'] not in ('IfcWall','IfcWallStandardCase'):
        raise ValueError('SINGLE_WALL_TARGET_REQUIRED')
    return rows[0]


def matrix_for_position(pos):
    m=np.eye(4)
    x=np.array(pos['ref_direction'],dtype=float);z=np.array(pos['axis'],dtype=float)
    x/=np.linalg.norm(x);z/=np.linalg.norm(z)
    if not np.isfinite(x).all() or not np.isfinite(z).all() or abs(np.dot(x,z))>1e-9:
        raise ValueError('INVALID_SOLID_POSITION')
    m[:3,0]=x;m[:3,2]=z;m[:3,1]=np.cross(z,x);m[:3,3]=pos['origin']
    return m


def merge_wall_representation(base,target_id,donor,donor_id,*,rebase=True):
    """Change ONE Representation, preserving host frame, children and all relations."""
    target=entity_record(base,target_id);source=entity_record(donor,donor_id)
    rep=copy.deepcopy(source['attributes']['Representation'])
    if rep.get('kind')!='extruded_profile' or rep['profile'].get('kind')!='polygon':
        raise ValueError('POLYGON_EXTRUSION_REQUIRED')
    points=rep['profile']['points']
    if points[0]!=points[-1]:raise ValueError('EXPLICIT_CLOSURE_REQUIRED')
    if rebase:
        if 'position' in rep:solid=matrix_for_position(rep['position'])
        elif np.allclose(rep['direction'],[0,0,1]):solid=np.eye(4)
        else:raise ValueError('EXPLICIT_SOLID_POSITION_REQUIRED_FOR_NONZ_DIRECTION')
        old=np.array(world_transform_for(base,target_id),dtype=float)
        incoming=np.array(world_transform_for(donor,donor_id),dtype=float)
        local=np.linalg.inv(old)@incoming@solid
        rep['position']={'origin':local[:3,3].tolist(),'axis':local[:3,2].tolist(),'ref_direction':local[:3,0].tolist()}
    merged=copy.deepcopy(base)
    entity_record(merged,target_id)['attributes']['Representation']=rep
    return merged


def by_bim_id(model):
    return {ifcopenshell.util.element.get_psets(e).get('Pset_text2IFCIdentity',{}).get('BimJsonId'):e
            for e in model.by_type('IfcProduct') if ifcopenshell.util.element.get_psets(e).get('Pset_text2IFCIdentity',{}).get('BimJsonId')}


def system_refs(entity):
    ref=lambda e:ifcopenshell.util.element.get_psets(e).get('Pset_text2IFCIdentity',{}).get('BimJsonId',e.Name)
    data={'containment':[ref(r.RelatingStructure) for r in getattr(entity,'ContainedInStructure',())],
          'opening_refs':[ref(r.RelatedOpeningElement) for r in getattr(entity,'HasOpenings',())]}
    data['world_placement']=ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement).tolist()
    return data


def compile_case(graph,path):
    result=compile_document(graph,path)
    record={'success':result.success,'input_issues':[{'code':i.code,'path':i.path,'message':i.message} for i in result.input_issues],
            'ifc_issues':[str(i) for i in result.ifc_issues],'output_path':str(result.output_path) if result.output_path else None}
    save(path.with_suffix('.compilation.json'),record)
    return (ifcopenshell.open(str(path)) if result.success else None),record


def non_target_checks(before,after,target_id):
    aa,bb=by_bim_id(before),by_bim_id(after)
    if aa.keys()!=bb.keys():raise ValueError('PRODUCT_IDS_CHANGED')
    rows=[]
    for identity,a in aa.items():
        if identity==target_id:continue
        b=bb[identity]
        matrix_delta=float(np.max(np.abs(ifcopenshell.util.placement.get_local_placement(a.ObjectPlacement)-ifcopenshell.util.placement.get_local_placement(b.ObjectPlacement))))
        row={'id':identity,'class':a.is_a(),'placement_matrix_max_delta':matrix_delta,'pass':matrix_delta<=1e-8}
        if a.Representation and b.Representation:
            try:
                av,af=wall_mesh(a);bv,bf=wall_mesh(b)
                bbox=float(max(np.max(np.abs(av.min(axis=0)-bv.min(axis=0))),np.max(np.abs(av.max(axis=0)-bv.max(axis=0)))))
                row.update(bbox_coordinate_max_delta_mm=bbox,volume_delta_mm3=abs(volume_mm3(av,af)-volume_mm3(bv,bf)))
                row['pass']=row['pass'] and bbox<=1e-6 and row['volume_delta_mm3']<=.01
            except (RuntimeError,ValueError) as exc:
                row.update(geometry_unassessed=type(exc).__name__)
                row['pass']=False
        rows.append(row)
    return {'tested_products':len(rows),'all_pass':all(r['pass'] for r in rows),'rows':rows}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default=DEFAULT_OUT);args=p.parse_args()
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=False)
    originals={path:path.read_bytes() for path in (BASE,DONOR,SOURCE,ROOT/'dataset/external/bimnet/hxp.ifc')}
    base,donor=load(BASE),load(DONOR)
    targets=[e['id'] for e in base['entities'] if e.get('attributes',{}).get('Name')=='W013' and e['ifc_class']=='IfcWall']
    donors=[e['id'] for e in donor['entities'] if e['ifc_class']=='IfcWall']
    if len(targets)!=1 or len(donors)!=1:raise ValueError('AMBIGUOUS_REVEALED_CASE_SELECTION')
    target_id,donor_id=targets[0],donors[0]
    merged=merge_wall_representation(base,target_id,donor,donor_id)
    naive=merge_wall_representation(base,target_id,donor,donor_id,rebase=False)
    for name,doc in [('baseline',base),('naive-negative-control',naive),('rebased',merged)]:save(out/(name+'.json'),doc)
    bm,br=compile_case(base,out/'baseline-recompiled.ifc')
    nm,nr=compile_case(naive,out/'naive-negative-control.ifc')
    cm,cr=compile_case(merged,out/'integrated-offline.ifc')
    if bm is None:raise RuntimeError('BASELINE_MUST_COMPILE')
    # Preserve failures as outcomes; do not remove materials/windows to force success.
    def world_points(doc,identity):
        rep=entity_record(doc,identity)['attributes']['Representation']
        solid=matrix_for_position(rep['position']) if 'position' in rep else np.eye(4)
        total=np.asarray(world_transform_for(doc,identity))@solid
        return np.array([(total@np.array([*p,0.,1.]))[:3] for p in rep['profile']['points']])
    donor_points=world_points(donor,donor_id)
    rebased_points=world_points(merged,target_id)
    naive_points=world_points(naive,target_id)
    coordinate_check={'basis':'BIM JSON transform composition, not a compiled full-scene IFC',
        'naive_max_vertex_displacement_mm':float(np.max(np.linalg.norm(naive_points-donor_points,axis=1))),
        'rebased_max_vertex_displacement_mm':float(np.max(np.linalg.norm(rebased_points-donor_points,axis=1))),
        'rebased_world_vertices_mm':rebased_points.tolist()}
    placement_changes=[]
    for e in base['entities']:
        if 'ObjectPlacement' in e.get('attributes',{}):
            d=float(np.max(np.abs(np.array(world_transform_for(base,e['id']))-np.array(world_transform_for(merged,e['id'])))))
            placement_changes.append({'id':e['id'],'matrix_delta':d})
    sf=extract_description_facts(SOURCE);bf=extract_description_facts(out/'baseline-recompiled.ifc')
    baseline_compare=compare_with_wall_policy(sf,bf)
    save(out/'baseline-comparison-wall-0.1mm.json',baseline_compare)
    sm=ifcopenshell.open(str(SOURCE))
    srcwall=next(i for c,i in all_items(sf) if c=='walls' and i['label']=='W013')
    sw=sm.by_guid(srcwall['source_global_id']);bw=by_bim_id(bm)[target_id]
    wall_reports={'baseline':compare_wall_entities(sw,bw)}
    for name,model in [('naive_negative_control',nm),('integrated',cm)]:
        wall_reports[name]=compare_wall_entities(sw,by_bim_id(model)[target_id]) if model else {'status':'not_run_compilation_blocked','pass':False}
    preservation=non_target_checks(bm,cm,target_id) if cm else {'status':'not_run_compilation_blocked'}
    original_target=copy.deepcopy(entity_record(base,target_id));merged_target=copy.deepcopy(entity_record(merged,target_id))
    original_target['attributes'].pop('Representation');merged_target['attributes'].pop('Representation')
    unchanged_graph=original_target==merged_target and base['relationships']==merged['relationships'] and [e for e in base['entities'] if e['id']!=target_id]==[e for e in merged['entities'] if e['id']!=target_id]
    issues=[]
    for issue in cr['input_issues']:
        index=int(issue['path'].split('/')[2])
        issues.append({**issue,'entity_id':merged['entities'][index]['id'],'name':merged['entities'][index]['attributes'].get('Name')})
    assert all(path.read_bytes()==data for path,data in originals.items()),'ARCHIVED_INPUT_CHANGED'
    report={'schema_version':'text2ifc/wall-context-integration/0.9','provider_calls':0,
        'status':'compiled_offline' if cm else 'blocked_by_existing_forward_contract',
        'mode':'offline composition of two archived real-provider graphs; not a new whole-building generation',
        'source_reference':str(SOURCE.relative_to(ROOT)),'source_reference_is_normalized_copy':True,
        'baseline_graph':str(BASE.relative_to(ROOT)),'donor_graph':str(DONOR.relative_to(ROOT)),
        'forward_code_or_prompt_changed':False,'whole_building_accepted':False,
        'wall_compare_tolerance_mm':.1,'old_reports_overwritten':False,
        'only_target_representation_changed':unchanged_graph,
        'all_graph_placements_unchanged':all(x['matrix_delta']==0 for x in placement_changes),
        'graph_placement_checks':placement_changes,'source_and_archived_provider_artifacts_unchanged':True,
        'target_id':target_id,'donor_id':donor_id,'coordinate_check':coordinate_check,
        'target_world_matrix':world_transform_for(base,target_id),'donor_world_matrix':world_transform_for(donor,donor_id),
        'new_representation_position':entity_record(merged,target_id)['attributes']['Representation']['position'],
        'target_baseline_relations':system_refs(bw),'compilation':{'baseline':br,'naive':nr,'rebased':cr},
        'targeted_blockers':issues,'wall_results':wall_reports,'non_target_ifc_preservation':preservation,
        'baseline_wall_scalar_deviations':sum(r['geometry_outside_tolerance'] for r in baseline_compare['categories']['walls']['matched']),
        'baseline_counts':{c:len(bm.by_type(c)) for c in ['IfcWall','IfcOpeningElement','IfcDoor','IfcWindow','IfcSpace','IfcBuildingStorey']},
        'limitations':['Input transforms preserved is not proof of compiled whole-scene geometry when compilation is blocked.',
          'No production contract change, removed material, removed filling, or skipped gate to force output.',
          'Five section checks are sampled; no claim of full continuous surface equivalence.',
          'The normalized source is a new reference convention, not a retrofit improvement of old relation scores.']}
    if cm:
        integrated_compare=compare_with_wall_policy(sf,extract_description_facts(out/'integrated-offline.ifc'))
        save(out/'integrated-comparison-wall-0.1mm.json',integrated_compare)
    save(out/'summary.json',report)
    print(json.dumps({k:report[k] for k in ('status','baseline_counts','coordinate_check','targeted_blockers','only_target_representation_changed','all_graph_placements_unchanged','baseline_wall_scalar_deviations')},ensure_ascii=True,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
