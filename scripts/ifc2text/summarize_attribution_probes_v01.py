"""Post-run diagnostic summary; reads actual responses rather than model self-scores."""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.attribute_roundtrip_v01 import load,dump
from scripts.ifc2text.compact_campaign import budget_for

OUT=ROOT/'dataset/processed/experiments/ifc2text-attribution-20260921-v01'


def main():
    rows={}; controls={};selections={}
    for arm in ('original','explicit_containment'):
        case=OUT/('live-'+arm)
        state=load(case/'result.json')
        run=Path(state['run_dir'])
        stage=run/'calls/01-design-brief'
        brief=load(stage/'design-brief.json')
        metric=load(stage/'metrics.json')
        controls[arm]=load(case/'transport-controls.json')
        selections[arm]=load(stage/'context-selection.json')
        windows=[];spaces=[]
        for floor in brief['known_facts']['storeys']:
            for w in floor.get('windows',[]):
                windows.append({'id':w['id'],'actual_array_storey':floor['id'],
                    'recorded_storey':w.get('recorded_storey') or w.get('source_recorded_storey'),
                    'host_wall':w.get('host_wall'),'host_storey':w.get('host_storey'),
                    'dimensions':[w.get('width_mm'),w.get('height_mm')]})
            for s in floor.get('spaces',[]):
                spaces.append({'id':s['id'],'keys':list(s),
                    'vertical_fields':{k:v for k,v in s.items() if k!='polygon' and any(word in k for word in ['height','elevation','z_','bounds'])}})
        rows[arm]={'controller_status':state['controller_status'],'finish_reason':metric['finish_reason'],
            'provider_model':metric['model'],'response_id':metric['response_id'],
            'prompt_template_id':metric['prompt_template_id'],'prompt_template_hash':metric['prompt_template_hash'],
            'usage':metric['usage'],'windows':windows,'space_vertical_fields':spaces,
            'blocking_unsupported':[v for v in brief.get('unsupported_requests',[]) if v.get('blocking')],
            'blocking_missing':[v for v in brief.get('missing_facts',[]) if v.get('blocking')],
            'generator_invoked':False,'ifc_publication':False}
    def differences(a,b,path=''):
        if isinstance(a,dict) and isinstance(b,dict):
            return [v for k in a.keys()|b.keys() for v in differences(a.get(k),b.get(k),path+'/'+str(k))]
        if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
            return [v for i,(x,y) in enumerate(zip(a,b)) for v in differences(x,y,path+'/'+str(i))]
        return [] if a==b else [path]
    selection_diff=differences(selections['original'],selections['explicit_containment'])
    cfg=load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json')
    budget=budget_for(cfg).snapshot()
    new=sum(row['usage']['total_tokens'] for row in rows.values())
    unknown=sum(a['charged_tokens'] for a in budget['attempts'] if not a['usage_known'])
    summary={'evidence_kind':'two real public-Brief calls plus independent deterministic analysis',
        'arms':rows,'same_prompt':rows['original']['prompt_template_hash']==rows['explicit_containment']['prompt_template_hash'],
        'same_runtime_controls':controls['original']==controls['explicit_containment'],
        'same_context_selection':selections['original']==selections['explicit_containment'],
        'context_selection_changed_fields':selection_diff,
        'same_evidence_content':selections['original'].get('evidence')==selections['explicit_containment'].get('evidence'),
        'same_fewshot_content':selections['original'].get('few_shots')==selections['explicit_containment'].get('few_shots'),
        'new_provider_tokens':new,'cumulative':{'used_or_reserved':budget['tokens_used_or_reserved'],
            'unknown_usage_conservative_charge':unknown,'known_usage_including_history':budget['tokens_used_or_reserved']-unknown,
            'remaining_allowance':budget['limits']['tokens']-budget['tokens_used_or_reserved'],
            'calls':budget['calls'],'limits':budget['limits'],'halted':budget['halted']},
        'limitations':['One run per arm on a revealed building, not statistical causal proof or unseen-building evaluation.',
            'Only Brief is tested live; there is no newly generated IFC and no acceptance promotion.',
            'The model unsupported explanation is an observation, not proof of an IFC standard restriction.']}
    dump(OUT/'probe-summary.json',summary)
    dump(OUT/'budget-final.json',budget)
    print(json.dumps({k:v for k,v in summary.items() if k!='arms'},ensure_ascii=True,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
