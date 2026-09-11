"""Read-only attribution of actual Audit message size and exact duplicates."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from text2ifc_agent.audit_context import ROOTS, MIN_SHARED_BYTES, render_audit_context
from text2ifc_agent.prompt_registry import render_prompt, _render_value


def diagnose(audit_dir):
    root=Path(audit_dir)
    inputs=json.loads((root/'prompt-render-input.json').read_text(encoding='utf-8'))
    metadata=json.loads((root/'response-metadata.json').read_text(encoding='utf-8'))
    request=json.loads((root/'request.redacted.json').read_text(encoding='utf-8'))
    review='DESIGN_REVIEW_CONTEXT' in inputs
    baseline=render_prompt(template_id='audit.v3' if review else 'audit.v2',inputs=inputs)
    actual=request.get('request',request)['messages'][0]['content']
    assert baseline['text']==actual, 'Baseline must reproduce the actual message'
    transmitted=baseline['inputs'];total=len(actual.encode('utf-8'))
    sections=[{'key':k,'bytes':len(_render_value(v).encode('utf-8')),
        'percent_of_message':100*len(_render_value(v).encode('utf-8'))/total,
        'eligible_in_current_algorithm':k in ROOTS} for k,v in transmitted.items()]
    occurrences=defaultdict(list)
    def visit(v,path):
        if isinstance(v,(dict,list)):
            key=json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
            occurrences[key].append(path)
            for k,w in (v.items() if isinstance(v,dict) else enumerate(v)):
                visit(w,path+'/'+str(k))
    for k,v in transmitted.items():visit(v,'/'+k)
    repeated=[]
    for value,paths in occurrences.items():
        size=len(value.encode('utf-8'))
        if len(paths)>1 and size>=32:
            eligible=[p for p in paths if p.split('/')[1] in ROOTS]
            repeated.append({'canonical_bytes':size,'occurrences':len(paths),
                'eligible_occurrences':len(eligible),'paths':paths,
                'sha256':hashlib.sha256(value.encode()).hexdigest()})
    counts={str(n):{'eligible_duplicates':sum(r['canonical_bytes']>=n and r['eligible_occurrences']>1 for r in repeated),
        'all_transmitted_duplicates':sum(r['canonical_bytes']>=n for r in repeated)} for n in [512,128,32]}
    _,comparison=render_audit_context(inputs=inputs,review_enabled=review,mode='deduplicated')
    return {'evidence_class':'offline_attribution_of_frozen_live_message','provider_calls':0,
        'actual_message_reproduced':True,'message_bytes':total,'sections':sections,
        'template_and_separators_bytes':total-sum(s['bytes'] for s in sections),
        'eligible_roots':list(ROOTS),'minimum_shared_bytes':MIN_SHARED_BYTES,
        'threshold_probes':counts,'largest_repeated_objects':sorted(repeated,key=lambda r:-r['canonical_bytes'])[:30],
        'comparison':comparison,'live_usage':metadata['usage'],'response_id':metadata['response_id'],
        'source_hashes':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
            ['prompt-render-input.json','request.redacted.json','response-metadata.json']},
        'limits':'Repeated objects may be nested; counts and sizes cannot be summed as compression savings. No broader projection or provider quality experiment was performed.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audit-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=diagnose(a.audit_dir)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'message_bytes':result['message_bytes'],'sections':result['sections'],'threshold_probes':result['threshold_probes']}))
