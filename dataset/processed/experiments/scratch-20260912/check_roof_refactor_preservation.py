import copy, hashlib, json, subprocess
from pathlib import Path
from text2ifc_agent.complex_scaffold import build_scaffold_candidate
from text2ifc_agent.expected_facts import build_expected_facts
root=Path(__file__).resolve().parents[1]
old=subprocess.check_output(['git','show','33ecbfc0:src/text2ifc_agent/complex_scaffold.py'],cwd=root).decode('utf-8')
namespace={'__name__':'text2ifc_agent.baseline_scaffold','__package__':'text2ifc_agent'}
exec(compile(old,'baseline_scaffold','exec'),namespace)
results=[]
for name in ['two-storey','three-storey']:
    brief=json.loads((root/f'dataset/processed/agent-demo/phase6.5-cases/{name}-case.json').read_text(encoding='utf-8'))['design_brief']
    expected=build_expected_facts(case_id='roof-preservation',design_brief=brief)
    kwargs={'case_id':'roof-preservation','design_brief':brief,'expected_facts':expected}
    before=namespace['build_scaffold_candidate'](**copy.deepcopy(kwargs))
    after=build_scaffold_candidate(**copy.deepcopy(kwargs))
    assert before['relationships']==after['relationships']
    changed=[]
    for old_record,new_record in zip(before['entities'],after['entities'],strict=True):
        if old_record!=new_record:
            assert old_record['ifc_class']=='IfcRoof'
            expected_record=copy.deepcopy(old_record)
            dims=brief['known_facts']['building']
            expected_record['attributes']['ObjectPlacement']['origin'][:2]=[dims['width_x_mm']/2,dims['depth_y_mm']/2]
            assert expected_record==new_record
            changed.append(old_record['id'])
    assert len(changed)==1
    results.append({'fixture':name,'changed_roof_ids':changed,'unrelated_entities_unchanged':True,'all_relationships_unchanged':True})
record={'baseline':'33ecbfc0','evidence':'offline deterministic comparison, not Provider','results':results}
(root/'.tmp/roof-refactor-preservation-20260909.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
