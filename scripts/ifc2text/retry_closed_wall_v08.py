"""User-authorized 12->14 call continuation for one explicitly closed wall.

No changes to forward production code, prompts, schemas or evaluator thresholds.
The closed public text is the only building information sent to the Provider.
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from text2ifc_ifc2text.goal_budget import GoalBudget,GoalStopped
from scripts.ifc2text.compact_campaign import load,budget_for,runtime
from scripts.ifc2text.attribute_roundtrip_v01 import dump
from scripts.ifc2text.attribution_probe_v01 import run_public_brief
from scripts.ifc2text.recover_wall_v07 import generator_diagnostic

PREVIOUS=ROOT/'dataset/processed/experiments/ifc2text-wall-recovery-20260921-v07'
OUT=ROOT/'dataset/processed/experiments/ifc2text-closed-wall-retry-20260921-v08'
PUBLIC=PREVIOUS/'closeout-v08/single-wall-description-v08.txt'
CONFIG=ROOT/'scripts/ifc2text/compact-campaign-v0.6.json'
SCOPE=['src/text2ifc_ifc2text','src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract',
       'prompts/agent','schemas','scripts/ifc2text','tests/ifc2text/test_wall_retry_v08.py']
FORWARD=['src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract','prompts/agent','schemas']


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()


class ScopedRetryBudget(GoalBudget):
    """Link the entire prior snapshot; only the explicitly added two calls are usable."""
    def __init__(self,root,predecessor):
        if any(a['status']=='reserved' for a in predecessor['attempts']):
            raise GoalStopped('PREDECESSOR_UNSETTLED')
        if predecessor['calls']['reconstruction']!=12 or predecessor['limits']['tokens']!=2000000:
            raise GoalStopped('AUTHORIZATION_BASELINE_MISMATCH')
        self.inherited_reconstruction=predecessor['calls']['reconstruction']
        authority={'authorization':'2026-09-21 user: reconstruction 12 to 14, same 2000000 tokens; closed single-wall retry only',
                   'predecessor_snapshot':predecessor,'no_new_writing':True,
                   'new_limits':{'writing':26,'reconstruction':14,'tokens':2000000}}
        p=Path(root)/'authorization.json'
        if p.exists():
            if load(p)!=authority:raise GoalStopped('PREDECESSOR_OR_AUTHORIZATION_CHANGED')
        else:dump(p,authority)
        super().__init__(root,writing_calls=26,reconstruction_calls=14,tokens=2000000,
                         historical_writing_calls=predecessor['calls']['writing'],
                         historical_tokens=predecessor['tokens_used_or_reserved'])

    def snapshot(self):
        value=super().snapshot()
        value['calls']['reconstruction']+=self.inherited_reconstruction
        value['historical_reconstruction_calls']=self.inherited_reconstruction
        return value

    def check_capacity(self,stage,*,calls=1,tokens=0):
        if stage!='reconstruction':raise GoalStopped('AUTHORIZATION_SINGLE_WALL_RECONSTRUCTION_ONLY')
        return super().check_capacity(stage,calls=calls,tokens=tokens)


def contour_from_text(text):
    from shapely.geometry import Polygon
    m=re.search(r'底面闭合外轮廓（世界XY，mm）([^；]+)；底面Z=([-\d.]+)；\+Z拉伸 ([-\d.]+)',text)
    if not m:raise ValueError('EXPLICIT_CONTOUR_MISSING')
    points=[[float(x) for x in re.findall(r'-?\d+\.\d+',p)] for p in m[1].split('→')]
    if len(points)<4 or any(len(p)!=2 for p in points) or points[0]!=points[-1]:
        raise ValueError('EXPLICIT_CLOSURE_REQUIRED')
    z,h=float(m[2]),float(m[3]);polygon=Polygon(points)
    if not all(math.isfinite(x) for p in points for x in p) or not polygon.is_valid or polygon.area<=0 or not math.isfinite(z+h) or h<=0:
        raise ValueError('INVALID_CONTOUR_OR_HEIGHT')
    return points,z,h


def compare_planar(a,b):
    from shapely.geometry import Polygon
    from shapely import hausdorff_distance
    pa,pb=Polygon(a),Polygon(b)
    if not pa.is_valid or not pb.is_valid:raise ValueError('INVALID_COMPARISON_POLYGON')
    distance=float(hausdorff_distance(pa.boundary,pb.boundary,densify=.1))
    return {'hausdorff_densified_mm':distance,'symmetric_difference_mm2':pa.symmetric_difference(pb).area,
            'diagnostic_0_1mm_pass':distance<=.1,'legacy_20mm_planar_pass':distance<=20.,
            'metric_note':'discrete symmetric Hausdorff with segment densification; not arbitrary-surface proof'}


def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    cfg=load(CONFIG);parent=budget_for(cfg).snapshot()
    if parent['calls']['reconstruction']!=12 or not parent['halted']:
        raise GoalStopped('FROZEN_PARENT_REQUIRED')
    dump(OUT/'predecessor-budget.json',parent)
    shutil.copyfile(PUBLIC,OUT/'public-description.txt')
    text=(OUT/'public-description.txt').read_text(encoding='utf-8');points,z,h=contour_from_text(text)
    dump(OUT/'input-check.json',{'closed':True,'valid_simple_polygon':True,'point_count':len(points),
        'distinct_vertices':len(points)-1,'bottom_z_mm':z,'height_mm':h,
        'rounding_step_mm':.1,'per_axis_rounding_bound_mm':.05,
        'xy_rounding_bound_mm':math.sqrt(2)*.05,'supplementary_shape_tolerance_mm':.1,
        'unchanged_legacy_tolerance_mm':20.,'source_data_not_a_provider_input':True})
    ScopedRetryBudget(OUT/'budget',parent)
    print(json.dumps({'prepared':str(OUT),'inherited':parent['calls'],'tokens':parent['tokens_used_or_reserved']}))


def get_budget():
    saved=load(OUT/'predecessor-budget.json')
    if budget_for(load(CONFIG)).snapshot()!=saved:raise GoalStopped('PREDECESSOR_CHANGED')
    return ScopedRetryBudget(OUT/'budget',saved)


def admitted():
    record=load(OUT/'validation/admission.json')
    if record['status']!='admitted':raise GoalStopped('ADMISSION_REQUIRED')
    if git('diff',record['code_commit'],'--',*SCOPE):raise GoalStopped('ADMISSION_CHANGED')
    if git('status','--porcelain','--untracked-files=all','--',*SCOPE):raise GoalStopped('EXECUTION_SCOPE_DIRTY')
    if (OUT/'public-description.txt').read_bytes()!=PUBLIC.read_bytes():raise GoalStopped('PUBLIC_INPUT_CHANGED')
    return record


def validate():
    import compileall
    import pytest
    from scripts.ifc2text.validate_goal import OfflineRecorder
    ancestor=load(PREVIOUS/'validation/admission.json')
    if ancestor['status']!='admitted' or git('diff',ancestor['code_commit'],'--',*FORWARD):
        raise GoalStopped('FORWARD_CHAIN_CHANGED_REQUIRES_REVIEW')
    if git('status','--porcelain','--untracked-files=all','--',*SCOPE):raise GoalStopped('COMMIT_BEFORE_ADMISSION')
    out=OUT/'validation';out.mkdir(parents=True,exist_ok=False)
    command=['-o','addopts=','tests/ifc2text/test_wall_retry_v08.py','tests/ifc2text/test_wall_closure_v08.py',
             'tests/ifc2text/test_recover_wall_v07.py','tests/ifc2text/test_goal_budget_v03.py',
             '-q','--basetemp='+str(out/('tmp-'+uuid.uuid4().hex[:10])),'-p','no:cacheprovider']
    recorder=OfflineRecorder();log=io.StringIO();start=time.time()
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log),recorder.network_guard():
        code=pytest.main(command,plugins=[recorder])
    (out/'pytest.log').write_text(log.getvalue(),encoding='utf-8')
    compiled=compileall.compile_file(__file__,quiet=1)
    ok=code==0 and compiled and not recorder.network_attempts and not recorder.setup_errors and not recorder.counts['skipped']
    record={'status':'admitted' if ok else 'blocked','code_commit':git('rev-parse','HEAD'),
            'ancestor':str(PREVIOUS/'validation/admission.json'),'forward_chain_unchanged':True,
            'scope':SCOPE,'command':command,'exit_code':int(code),'counts':recorder.counts,
            'setup_errors':recorder.setup_errors,'network_attempts':recorder.network_attempts,
            'compileall':compiled,'elapsed_seconds':time.time()-start,'nodeids':recorder.nodeids,
            'live_scope':'two calls only: existing public Brief and existing Generator stage; single-wall diagnostic; no Audit',
            'full_preflight':False,'network_transport_attempted':False}
    dump(out/'admission.json',record)
    print(json.dumps({k:v for k,v in record.items() if k not in {'nodeids','command','scope'}},ensure_ascii=True))
    return 0 if ok else 1


def brief():
    admitted();budget=get_budget();budget.check_capacity('reconstruction')
    cfg=load(CONFIG);conf,client,_=runtime(cfg,budget,'reconstruction',65536)
    text=(OUT/'public-description.txt').read_text(encoding='utf-8')
    try:
        result=run_public_brief(text,OUT/'live-brief',conf,client,evidence_kind='live_closed_wall_retry')
        if result['controller_status']=='ready':
            call=Path(result['run_dir'])/'calls/01-design-brief';dest=OUT/'design-source';dest.mkdir(exist_ok=False)
            for name in ('design-brief.json','conversation.json','context-selection.json'):
                shutil.copyfile(call/name,dest/name)
            (dest/'input.txt').write_text(text,encoding='utf-8')
        else:budget.halt('RETRY_BRIEF_NOT_READY')
        print(json.dumps(result,ensure_ascii=True))
    except Exception:
        budget.halt('RETRY_BRIEF_FAILED');raise
    finally:client.client.close();dump(OUT/'budget-after-brief.json',budget.snapshot())


def generate():
    admitted();budget=get_budget();budget.check_capacity('reconstruction')
    if load(OUT/'live-brief/result.json')['controller_status']!='ready':raise GoalStopped('BRIEF_NOT_READY')
    cfg=load(CONFIG);conf,client,provider=runtime(cfg,budget,'reconstruction',65536)
    try:
        result=generator_diagnostic(OUT/'design-source',OUT/'live-generator',provider,evidence_kind='live_closed_wall_diagnostic_not_whole_building_acceptance')
        if not result.get('compile_success'):budget.halt('RETRY_GENERATOR_OR_COMPILATION_FAILED')
        print(json.dumps(result,ensure_ascii=True))
    except Exception:
        budget.halt('RETRY_GENERATOR_FAILED');raise
    finally:client.client.close();dump(OUT/'budget-after-generator.json',budget.snapshot())


def evaluate():
    import ifcopenshell
    from scripts.ifc2text.probe_polygon_wall_backend_v01 import measured_geometry
    text=(OUT/'public-description.txt').read_text(encoding='utf-8');points,z,height=contour_from_text(text)
    result=load(OUT/'live-generator/result.json');budget=get_budget().snapshot()
    summary={'original_provider_result':result,'budget':{'calls':budget['calls'],'limit_tokens':2000000,
             'used_or_reserved':budget['tokens_used_or_reserved'],'new_tokens':sum(a['charged_tokens'] for a in budget['attempts']),
             'remaining_tokens':2000000-budget['tokens_used_or_reserved']},
             'forward_system_modified':False,'raw_provider_edited':False,'full_audit_done':False,
             'opening_material_space_scope_tested':False,'source_role':'original archived hxp, unvoided W013 wall only'}
    if result.get('compile_success'):
        source=ROOT/'dataset/external/bimnet/hxp.ifc';candidate=Path(result['ifc_path'])
        immutable={p:p.read_bytes() for p in (source,candidate,OUT/'live-generator/generator/candidate.json')}
        raw=load(OUT/'live-generator/generator/parsed-output.json');graph=load(OUT/'live-generator/generator/candidate.json')
        if raw!=graph:raise ValueError('CANDIDATE_DIFFERS_FROM_RAW_PARSED_PROVIDER_OUTPUT')
        rawwalls=[e for e in raw['entities'] if e['ifc_class']=='IfcWall']
        if len(rawwalls)!=1:raise ValueError('EXPECTED_SINGLE_WALL')
        profile=rawwalls[0]['attributes']['Representation']['profile']
        if profile['kind']!='polygon' or profile['points'][0]!=profile['points'][-1]:raise ValueError('RAW_POLYGON_NOT_EXPLICITLY_CLOSED')
        src=ifcopenshell.open(str(source));dst=ifcopenshell.open(str(candidate))
        w=load(PREVIOUS/'single-wall-evaluator-only.json');se=src.by_guid(w['source_global_id'])
        walls=dst.by_type('IfcWall')
        if len(walls)!=1:raise ValueError('EXPECTED_ONE_COMPILED_WALL')
        sb,sp=measured_geometry(se);cb,cp=measured_geometry(walls[0])
        source_vs_text=compare_planar(list(sp.exterior.coords),points)
        source_vs_ifc=compare_planar(list(sp.exterior.coords),list(cp.exterior.coords))
        text_vs_ifc=compare_planar(points,list(cp.exterior.coords))
        bbox=max(abs(a-b) for k in sb for a,b in zip(sb[k],cb[k]))
        z_error=max(abs(cb['z'][0]-z),abs(cb['z'][1]-(z+height)))
        body=[i for r in walls[0].Representation.Representations for i in r.Items]
        summary.update(raw_polygon_explicitly_closed=True,raw_profile_points=profile['points'],
            source_vs_text=source_vs_text,source_vs_generated_ifc=source_vs_ifc,text_vs_generated_ifc=text_vs_ifc,
            max_bbox_coordinate_delta_mm=bbox,z_range_error_mm=z_error,generated_z_range_mm=cb['z'],
            source_area_mm2=sp.area,generated_area_mm2=cp.area,ifc_schema=dst.schema,
            reconstructed_profile_types=[i.SweptArea.is_a() for i in body if i.is_a('IfcExtrudedAreaSolid')],
            wall_count=1,opening_count=len(dst.by_type('IfcOpeningElement')),
            micro_geometry_pass=source_vs_ifc['diagnostic_0_1mm_pass'] and bbox<=.1 and z_error<=.1,
            whole_building_accepted=False)
        if not all(p.read_bytes()==b for p,b in immutable.items()):raise ValueError('SOURCE_OR_PROVIDER_OUTPUT_MUTATED')
        summary['source_and_candidate_unchanged']=True
    dump(OUT/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=True,indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','validate','brief','generate','evaluate']);a=p.parse_args()
    result={'prepare':prepare,'validate':validate,'brief':brief,'generate':generate,'evaluate':evaluate}[a.command]()
    return result if isinstance(result,int) else 0

if __name__=='__main__':raise SystemExit(main())
