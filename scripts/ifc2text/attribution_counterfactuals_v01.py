"""Offline counterfactuals only: never update production artifacts or call a model."""
from __future__ import annotations
from collections import Counter
import copy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.attribute_roundtrip_v01 import load, dump, mesh_bounds
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def profile_info(entity):
    reps=getattr(getattr(entity,'Representation',None),'Representations',()) or ()
    result=[]
    for rep in reps:
        if rep.RepresentationIdentifier!='Body':continue
        for item in rep.Items:
            p=getattr(item,'SweptArea',None)
            row={'body_type':item.is_a(),'profile_type':p.is_a() if p else None}
            if p:
                if p.is_a('IfcArbitraryClosedProfileDef'):
                    curve=p.OuterCurve
                    row['curve_type']=curve.is_a()
                    row['profile_points']=[list(point.Coordinates) for point in getattr(curve,'Points',())]
                if p.is_a('IfcRectangleProfileDef'):
                    row.update(x_dim=p.XDim,y_dim=p.YDim)
            result.append(row)
    return result


def main():
    import ifcopenshell
    out=ROOT/'dataset/processed/experiments/ifc2text-attribution-20260921-v01'
    trace=load(out/'attribution.json')
    run=ROOT/trace['baseline_run']
    src=ROOT/'dataset/external/bimnet/hxp.ifc';dst=run/'output.ifc'
    originals={p:p.read_bytes() for p in [src,dst,run/'design-brief/design-brief.json',run/'generator/candidate.json']}
    sm,cm=ifcopenshell.open(str(src)),ifcopenshell.open(str(dst))
    walls={}
    for label in ('W011','W013','W015'):
        t=trace['traces'][label]
        a=sm.by_guid(t['source_observation']['source_global_id'])
        b=cm.by_guid(t['candidate_observation']['source_global_id'])
        ba,bb=mesh_bounds(a,no_openings=True),mesh_bounds(b,no_openings=True)
        walls[label]={'source':profile_info(a),'candidate':profile_info(b),
            'no_openings_bbox_size_delta_mm':{k:abs((ba[k][1]-ba[k][0])-(bb[k][1]-bb[k][0])) for k in 'xyz'},
            'source_axis_start':t['source_observation']['axis_start_mm'],
            'candidate_axis_start':t['candidate_observation']['axis_start_mm'],
            'source_axis_end':t['source_observation']['axis_end_mm'],
            'candidate_axis_end':t['candidate_observation']['axis_end_mm']}
    brief=load(run/'design-brief/design-brief.json')
    expected=load(out/'expectation-replay/expected-facts.json')
    changed=copy.deepcopy(expected)
    raw=[]
    for floor in brief['known_facts']['storeys']:
        raw.extend((floor,s) for s in floor.get('spaces',[]))
    additions=[]
    for record in changed['spaces']:
        matches=[(f,s) for f,s in raw if record['id'].lower().endswith('-'+s['id'].lower()) or record['id'].lower()==s['id'].lower()]
        if len(matches)!=1:raise ValueError('SPACE_MATCH_NOT_UNIQUE')
        floor,space=matches[0]
        points=space['polygon'];z=space['z_mm']
        assert z[0]==floor['elevation_mm'],'Counterfactual does not support an elevated base'
        record['bounds']={'x':[min(p[0] for p in points),max(p[0] for p in points)],'y':[min(p[1] for p in points),max(p[1] for p in points)]}
        record['height_mm']=z[1]-z[0]
        additions.append({'id':record['id'],'bounds':record['bounds'],'height_mm':record['height_mm'],
            'basis':'polygon and z_mm already present in the original public Brief; no source IFC facts'})
    before=build_design_geometry_expectation(case_id='offline-before',design_brief=brief,expected_facts=expected)
    after=build_design_geometry_expectation(case_id='offline-after',design_brief=brief,expected_facts=changed)
    results={'mode':'offline counterfactual, not production fix or new generated IFC',
        'walls':walls,'space_projection':{'before_unresolved':before['unresolved'],'after_unresolved':after['unresolved'],
            'before_space_count':len(before['spaces']),'after_space_count':len(after['spaces']),
            'projected_existing_brief_facts':additions,'room_semantics_proven':False,'polygon_shape_equivalence_proven':False},
        'skipped_reasons':trace['unassessed_reasons']}
    assert all(p.read_bytes()==v for p,v in originals.items())
    results['baseline_bytes_unchanged']=True
    dump(out/'counterfactuals.json',results)
    print(json.dumps(results,ensure_ascii=True,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
