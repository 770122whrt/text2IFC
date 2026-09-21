"""Two-issue IFC2Text recovery, without modifying the forward text2IFC system.

prepare: audit original, create explicit host-policy COPY, write detailed texts.
write: reuse registered v0.6 Narrator unchanged, append measured v0.7 wall details.
brief/generate: two bounded live calls on one unvoided wall, not full-building acceptance.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from text2ifc_ifc2text.observation import extract_description_facts, all_items
from text2ifc_ifc2text.wall_details_v07 import enrich_wall_details, detailed_description, wall_detail_text
from text2ifc_ifc2text.source_containment_v07 import inspect_containment, normalize_copy, POLICY
from scripts.ifc2text.attribute_roundtrip_v01 import dump, load
from scripts.ifc2text.compact_campaign import budget_for, runtime
from scripts.ifc2text.attribution_probe_v01 import run_public_brief

OUT=ROOT/'dataset/processed/experiments/ifc2text-wall-recovery-20260921-v07'
SOURCE=ROOT/'dataset/external/bimnet/hxp.ifc'
WALL='W013'  # Explicit revealed-case selection; all algorithms are scene-independent.


def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    audit=inspect_containment(SOURCE); dump(OUT/'source-review.json',audit)
    # Explicit source-work-copy policy for the three reviewed mismatches. This is
    # not a claim that IFC requires host and recorded containers to be identical.
    selected=[r['global_id'] for r in audit['fillings'] if r['eligible_for_explicit_host_policy']]
    target=OUT/'hxp-host-normalized.ifc'
    normalization=normalize_copy(SOURCE,target,selected_global_ids=selected,policy=POLICY)
    dump(OUT/'source-normalization.json',normalization)
    records={}
    for role,path in [('original',SOURCE),('host-normalized',target)]:
        facts=enrich_wall_details(path,extract_description_facts(path))
        folder=OUT/role; dump(folder/'source-facts.json',facts)
        text=detailed_description(facts)
        (folder/'design-description-deterministic.md').write_text(text,encoding='utf-8',newline='\n')
        walls=[w for c,w in all_items(facts) if c=='walls']
        records[role]={'characters':len(text),'source':str(path),'details':[w['label'] for w in walls if w['solid_detail'].get('requires_explicit_outline')],
            'unsupported':[{'label':w['label'],**w['solid_detail']} for w in walls if w['solid_detail']['status']=='unsupported']}
    original_facts=load(OUT/'original/source-facts.json')
    wall=next(w for c,w in all_items(original_facts) if c=='walls' and w['label']==WALL)
    request=single_wall_text(wall)
    (OUT/'single-wall-description.txt').write_text(request,encoding='utf-8',newline='\n')
    dump(OUT/'single-wall-evaluator-only.json',wall)
    records['micro_scope']={'wall':WALL,'input':'single-wall-description.txt','excludes':['openings','fillings','materials','whole-building acceptance'],
        'evaluator_only_file_forbidden_in_provider_input':'single-wall-evaluator-only.json'}
    dump(OUT/'preparation.json',records)
    print(json.dumps(records,ensure_ascii=True,indent=2))


def single_wall_text(wall):
    from text2ifc_ifc2text.compact import mm1
    d=wall['solid_detail']
    return ('建立一个单墙几何诊断模型，不是整栋建筑。长度均为mm，XY坐标系与世界坐标系相同。'+
        '需要基本项目、场地、建筑与一个楼层层级；楼层S01参考标高为'+mm1(d['bottom_z_mm'])+'。'+
        '本诊断只创建一面墙，不生成空间、楼板、屋顶、门窗、洞口或楼梯。没有材料与外观要求。\n\n'+
        wall_detail_text(wall)+'\n\n'+
        '上面的轮廓是墙底面完整的顺序顶点，自动闭合，不是墙的中心线；应以多边形截面竖直拉伸，而不是改用外包矩形。'+
        '诊断不包含源墙开口，故本次不扣任何洞。不要增加其他墙体。模型不需要建筑功能、净房间用途或围合假设。\n')


def generator_diagnostic(design_dir, output, provider, *, evidence_kind):
    from text2ifc_agent.live_pipeline import run_generator_stage
    from text2ifc_agent.expected_facts import write_expected_facts
    from text2ifc_compiler import compile_document
    source=Path(design_dir); output=Path(output)
    if output.exists():raise ValueError('GENERATOR_ATTEMPT_EXISTS')
    output.mkdir(parents=True)
    brief=load(source/'design-brief.json')
    if brief.get('status')!='ready':raise ValueError('READY_BRIEF_REQUIRED')
    write_expected_facts(case_dir=source.parent,case_id='single-wall-detail-v07',design_brief=brief)
    result=run_generator_stage(provider=provider,output_dir=output/'generator',design_source_dir=source,
        case_id='single-wall-detail-v07',session_prefix='ifc2text-diagnostic',trace_level='debug')
    record={'evidence_kind':evidence_kind,'generator_result':result,'audit_invoked':False,'accepted_publication':False}
    candidate=output/'generator/candidate.json'
    if candidate.exists() and result.get('valid'):
        graph=load(candidate); target=output/'single-wall-generated-diagnostic.ifc'
        compiled=compile_document(graph,target)
        record['compile_success']=compiled.success
        if compiled.success:
            import ifcopenshell
            model=ifcopenshell.open(str(target)); walls=model.by_type('IfcWall')
            record['wall_count']=len(walls); record['ifc_schema']=model.schema;record['ifc_path']=str(target)
            record['profiles']=[item.SweptArea.is_a() for wall in walls for rep in wall.Representation.Representations
                for item in rep.Items if item.is_a('IfcExtrudedAreaSolid')]
    dump(output/'result.json',record)
    return record


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()


def require_admission():
    r=load(OUT/'validation/admission.json')
    if r['status']!='admitted':raise ValueError('ADMISSION_REQUIRED')
    if git('diff',r['code_commit'],'--',*r['scope']):raise ValueError('ADMISSION_CHANGED')
    if git('status','--porcelain','--untracked-files=all','--',*r['scope']):raise ValueError('EXECUTION_SCOPE_DIRTY')
    return r


def write():
    from text2ifc_ifc2text.compact_pipeline import write_compact
    require_admission();cfg=load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json');b=budget_for(cfg)
    conf,client,provider=runtime(cfg,b,'writing',8192)
    folder=OUT/'host-normalized'
    # Use the unmodified registered narrator: it organizes floors, not the solids.
    try:
        result=write_compact(output=folder,provider=provider,budget=b,template_id='ifc2text-compact-narrator.v0.6')
        narration=load(folder/'writing/narration/parsed-response.json')
        facts=load(folder/'source-facts.json'); text=detailed_description(facts,narration)
        (folder/'design-description-v07.md').write_text(text,encoding='utf-8',newline='\n')
        dump(folder/'detail-writing-result.json',{'narrator':result,'detail_version':'0.7','characters':len(text),
            'prompt_changed':False,'description_path':'design-description-v07.md'})
        print(json.dumps({'characters':len(text),'budget':b.snapshot()['calls']},ensure_ascii=True))
    finally:
        client.client.close();dump(OUT/'budget-after-writing.json',b.snapshot())


def brief():
    require_admission();cfg=load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json');b=budget_for(cfg)
    b.check_capacity('reconstruction')
    conf,client,_=runtime(cfg,b,'reconstruction',65536)
    text=(OUT/'single-wall-description.txt').read_text(encoding='utf-8')
    try:
        r=run_public_brief(text,OUT/'live-brief',conf,client,evidence_kind='live_single_wall_diagnostic')
        if r['controller_status']=='ready':
            run=Path(r['run_dir']); call=run/'calls/01-design-brief'; dest=OUT/'design-source';dest.mkdir(exist_ok=False)
            for name in ('design-brief.json','conversation.json','context-selection.json'):
                shutil.copyfile(call/name,dest/name)
            (dest/'input.txt').write_text(text,encoding='utf-8',newline='\n')
        print(json.dumps(r,ensure_ascii=True))
    except Exception:
        b.halt('SINGLE_WALL_BRIEF_FAILED');raise
    finally:client.client.close();dump(OUT/'budget-after-brief.json',b.snapshot())


def generate():
    require_admission();cfg=load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json');b=budget_for(cfg)
    b.check_capacity('reconstruction')
    conf,client,provider=runtime(cfg,b,'reconstruction',65536)
    try:
        r=generator_diagnostic(OUT/'design-source',OUT/'live-generator',provider,evidence_kind='live_generator_diagnostic_not_accepted')
        print(json.dumps(r,ensure_ascii=True))
    except Exception:
        b.halt('SINGLE_WALL_GENERATOR_FAILED');raise
    finally:client.client.close();dump(OUT/'budget-after-generator.json',b.snapshot())


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','write','brief','generate']);a=p.parse_args()
    {'prepare':prepare,'write':write,'brief':brief,'generate':generate}[a.command]()

if __name__=='__main__':main()
