"""Read-only replay of the frozen failed extraction; no Provider or rewriting."""
import collections
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.design_brief import validate_design_brief
from text2ifc_agent.brief_semantic_repair import semantic_repair_eligible
from text2ifc_agent.semantic_requirements import project_semantic_requirements

def main():
    run=OUT/'live-run/runs/a06665c5f155025f'; source=run/'calls/01-design-brief'
    def read(name):return json.loads((source/name).read_text(encoding='utf8'))
    original=(source/'parsed-output.json').read_bytes()
    brief=read('parsed-output.json');known=brief['known_facts'];types={t['id'] for t in known['types']}
    issues=validate_design_brief(brief,evidence_catalog=read('context-selection.json')['evidence'],
        expected_schema_version='text2ifc/design-brief/2.4',conversation=read('conversation.json'))
    by_code=dict(collections.Counter(i.code for i in issues))
    assert by_code=={'SEMANTIC_AUTHORITY_NON_CANONICAL':60,'SEMANTIC_MATERIAL_INCOMPLETE':5},by_code
    assert not semantic_repair_eligible(brief,issues)
    assert (source/'parsed-output.json').read_bytes()==original
    requirements=known['semantic_requirements']
    def compact_chars(value):return len(json.dumps(value,ensure_ascii=False,separators=(',',':')))
    result={'status':'reproduced_without_mutation','network_transport_attempted':False,
        'run_id':run.name,'source_sha256':hashlib.sha256(original).hexdigest(),
        'issues_by_code':by_code,'issues':[asdict(i) for i in issues],
        'semantic_repair_eligible':False,
        'evidence':{'finish_reasons':[c.get('finish_reason') for c in read('response.raw.json')['choices']],
            'source_request_preserved':brief['original_request']==(OUT/'request.txt').read_text(encoding='utf8'),
            'replacement_characters':(source/'model-text.txt').read_text(encoding='utf8').count('\ufffd'),
            'input_characters':len((OUT/'request.txt').read_text(encoding='utf8')),
            'rendered_prompt_characters':len((source/'prompt-rendered.md').read_text(encoding='utf8')),
            'output_characters':len((source/'model-text.txt').read_text(encoding='utf8')),
            'canonical_requirement_rows':len(requirements),
            'known_facts_character_breakdown':{k:compact_chars(v) for k,v in known.items()}},
        'additional_static_defects_not_the_65_terminal_issues':{
            'type_self_binding_rows':[q for q in requirements if q['entity_id'] in types and q.get('type_id')==q['entity_id']],
            'instance_material_layer_set_rows':[q['entity_id'] for q in requirements if q.get('material',{}).get('kind')=='material_layer_set' and q['entity_id'] not in types],
            'roof_opening_under_roof_slab':known.get('roof_slab',{}).get('opening')},
        'ranked_hypotheses':[
            {'hypothesis':'response was truncated by output limit','finding':'rejected: finish_reason stop, parse succeeds, 49864 completion tokens below 65536'},
            {'hypothesis':'encoding corrupted Chinese request','finding':'rejected: original request matches exactly and output has no replacement characters'},
            {'hypothesis':'extraction did not conform to canonical semantic contract','finding':'reproduced: 60 out-of-location semantic records plus 5 string material declarations'},
            {'hypothesis':'bounded repair loop ignores eligible canonical-field errors','finding':'not supported: errors live outside the two authorized fields, so correction is deliberately ineligible'}],
        'allowed_claim':'One real attempt exposed extraction and recovery coverage gaps; no system-wide stability or token improvement claim.'}
    (OUT/'brief-diagnosis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'issues':by_code,'self_type_bindings':len(result['additional_static_defects_not_the_65_terminal_issues']['type_self_binding_rows']),
        'instance_layer_sets':len(result['additional_static_defects_not_the_65_terminal_issues']['instance_material_layer_set_rows'])},ensure_ascii=False))

if __name__=='__main__':main()
