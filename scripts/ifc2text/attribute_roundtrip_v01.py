"""Read-only stage attribution for a revealed roundtrip; never a production input."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from text2ifc_ifc2text.observation import extract_description_facts, all_items
from text2ifc_ifc2text.diagnostic_review import compare_observations
from text2ifc_agent.expected_facts import write_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def dump(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def walk(value, path=''):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + '/' + str(key))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from walk(child, path + '/' + str(key))


def representations(entity):
    rep = getattr(entity, 'Representation', None)
    return [{'identifier':r.RepresentationIdentifier,'type':r.RepresentationType,
             'items':[x.is_a() for x in r.Items]}
            for r in getattr(rep, 'Representations', ()) or ()]


def mesh_bounds(entity, *, no_openings=False):
    import ifcopenshell.geom
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    if no_openings:
        settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    verts = list(shape.geometry.verts)
    return {k:[min(verts[i::3])*1000,max(verts[i::3])*1000] for i,k in enumerate('xyz')}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--campaign',default='dataset/processed/experiments/ifc2text-phase1-20260917/compact-campaign-v06')
    parser.add_argument('--out',default='dataset/processed/experiments/ifc2text-attribution-20260921-v01')
    args=parser.parse_args()
    base=ROOT/args.campaign
    out=ROOT/args.out
    out.mkdir(parents=True,exist_ok=True)
    if (out/'attribution.json').exists():
        raise ValueError('ATTRIBUTION_ALREADY_EXISTS')
    recon=base/'hxp/reconstruction-128k'
    source=ROOT/'dataset/external/bimnet/hxp.ifc'
    gen=load(recon/'generation-result.json')
    candidate=Path(gen['ifc_path'])
    run=candidate.parent
    immutable={p:p.read_bytes() for p in [source,candidate,base/'hxp/design-description.md',run/'design-brief/design-brief.json',run/'generator/candidate.json']}
    sf=extract_description_facts(source)
    cf=extract_description_facts(candidate)
    comparison=compare_observations(sf,cf)
    text=(base/'hxp/design-description.md').read_text(encoding='utf-8')
    brief=load(run/'design-brief/design-brief.json')
    graph=load(run/'generator/candidate.json')
    expected=write_expected_facts(case_dir=out/'expectation-replay',case_id='attribution',design_brief=brief)
    if not isinstance(expected,dict): expected=load(expected)
    geometry=build_design_geometry_expectation(case_id='attribution',design_brief=brief,expected_facts=expected)
    dump(out/'geometry-expectation-replay.json',geometry)
    si={i['label']:i for _,i in all_items(sf)}
    ci={i['label']:i for _,i in all_items(cf)}
    import ifcopenshell
    sm,cm=ifcopenshell.open(str(source)),ifcopenshell.open(str(candidate))
    selected=('W011','W013','W015','D001','D003','D007','N001','O003')
    traces={}
    for label in selected:
        a,b=si[label],ci[label]
        se,ce=sm.by_guid(a['source_global_id']),cm.by_guid(b['source_global_id'])
        token=re.compile(r'(?<![A-Za-z0-9])'+label+r'(?![A-Za-z0-9])',re.I)
        brief_nodes=[{'path':p,'value':v} for p,v in walk(brief.get('known_facts',{}))
                     if isinstance(v.get('id'),str) and token.search(v['id'])]
        candidate_nodes=[v for v in graph.get('entities',[]) if token.search(str(v.get('id','')))]
        traces[label]={'source_observation':a,'candidate_observation':b,
            'source_representations':representations(se),'candidate_representations':representations(ce),
            'text_rows':[line for line in text.splitlines() if token.search(line)],
            'brief_nodes':brief_nodes,'generator_entities':candidate_nodes}
        if label.startswith('W'):
            traces[label]['mesh_without_openings']={'source':mesh_bounds(se,no_openings=True),'candidate':mesh_bounds(ce,no_openings=True)}
    known=brief.get('known_facts',{})
    spaces=[]
    for storey in known.get('storeys',[]):
        spaces.append({k:storey.get(k) for k in ['id','elevation_mm','net_height_mm','spaces']})
    semantic_materials=[{'path':p,'value':v} for p,v in walk(known.get('semantic_requirements',[])) if v.get('kind')=='material']
    unresolved_key=next((k for k in geometry if 'unresolved' in k),None)
    payload={'baseline_run':str(run.relative_to(ROOT)),'comparison_summary':comparison['summary'],
        'unassessed_record_count':len(comparison['unassessed']),
        'unassessed_field_count':sum(len(x['fields']) for x in comparison['unassessed']),
        'unassessed_reasons':dict(Counter(f for x in comparison['unassessed'] for f in x['fields'])),
        'brief_schema':brief.get('schema_version'),'graph_schema':graph.get('schema_version'),
        'brief_storeys_spaces':spaces,'brief_materials':semantic_materials,
        'geometry_expectation_keys':list(geometry),'geometry_unresolved':geometry.get(unresolved_key),
        'relation_differences':comparison['relation_differences'],'traces':traces}
    assert all(p.read_bytes()==content for p,content in immutable.items()),'BASELINE_MUTATED'
    payload['baseline_bytes_unchanged']=True
    dump(out/'attribution.json',payload)
    dump(out/'recomputed-comparison.json',comparison)
    print(json.dumps({k:v for k,v in payload.items() if k not in {'traces','brief_materials','brief_storeys_spaces'}},ensure_ascii=True,indent=2))
    print(json.dumps({'storeys':spaces},ensure_ascii=True,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
