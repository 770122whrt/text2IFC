from pathlib import Path
import hashlib
import json
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation
from text2ifc_agent.semantic_requirements import bind_geometry_targets
from text2ifc_quality.generated_ifc import check_generated_ifc

root=Path('dataset/processed/ifc-presentation-validation')
case=root/'two-storey-human-review-20260909/geometry-continuation/runs/5cd2006f0891913f'
out=root/'pipeline-opening-binding-20260909'
out.mkdir(exist_ok=True)
names=['candidate.json','design-brief.json','expected-facts.json','semantic-geometry-expectation.json',
       'output.ifc','geometry-feedback.json','audit/audit-report.json','generation-budget.json']
def hashes():
    return {name:hashlib.sha256((case/name).read_bytes()).hexdigest() for name in names}
before=hashes()
def read(name): return json.loads((case/name).read_text(encoding='utf-8'))
brief=read('design-brief.json'); facts=read('expected-facts.json'); candidate=read('candidate.json')
frozen=read('semantic-geometry-expectation.json')
results={}
for version in ['1.0','1.1']:
    expectation=build_design_geometry_expectation(case_id=frozen['case_id'], design_brief=brief,
        expected_facts=facts,schema_version=f'text2ifc/design-geometry-expectation/{version}')
    expectation=bind_geometry_targets(candidate,facts,expectation)
    if version=='1.0': assert expectation==frozen, 'Legacy projection changed'
    result=check_generated_ifc(case/'output.ifc',expectation)
    results[version]={'success':result.success,'issues':result.issues,'metrics':result.metrics}
    (out/f'expectation-{version}.json').write_text(json.dumps(expectation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert hashes()==before
record={'evidence_mode':'offline deterministic replay of disclosed live case','new_provider_calls':0,
        'legacy_projection_equals_frozen':True,'source':str(case),'unchanged_source_hashes':before,'results':results}
(out/'frozen-case-replay.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({version:[i['code'] for i in value['issues']] for version,value in results.items()}))
