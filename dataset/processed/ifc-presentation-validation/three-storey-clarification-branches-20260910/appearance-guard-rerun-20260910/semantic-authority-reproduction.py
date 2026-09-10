"""Offline red-capable missing-versus-empty semantic authority family.

This diagnostic does not call a Provider, compile IFC, or modify the live run.
Use --assert-fixed after implementing the new authority boundary.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'pyproject.toml').is_file())
from text2ifc_agent.semantic_requirements import project_semantic_requirements, unauthorized_candidate_semantics
from text2ifc_agent.semantic_correction import build_semantic_correction


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assert-fixed', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for identity in ['wall-1','beam-1','door-1','slab-1']:
        for mode in ['notes','policy','nested','declared_none','declared_requirement']:
            candidate = json.loads((ROOT/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
            candidate['schema_version'] = 'bim-json/2.1'
            for e in candidate['entities']:
                e['materials'], e['property_sets'] = [], {}
            target = next(e for e in candidate['entities'] if e['id']==identity)
            material = {'kind':'single_material','name':'Explicit requested material'}
            target['materials'] = [material]
            request = f'{identity} must use Explicit requested material; keep geometry.'
            if mode == 'declared_none':
                request = f'{identity} has no specified physical material; keep geometry.'
            known = ({'notes':[request]} if mode=='notes' else
                     {'policy':{'material_text':request}} if mode=='policy' else
                     {'design':{'constraints':[request]}} if mode=='nested' else
                     {'semantic_requirements':[]} if mode=='declared_none' else
                     {'semantic_requirements':[{'entity_id':identity,'material':material}]})
            brief = {'schema_version':'text2ifc/design-brief/2.1','original_request':request,'known_facts':known}
            projected = project_semantic_requirements(brief)
            expected = {'schema_version':'text2ifc/expected-facts/1.0','storeys':[],
                        'semantic_expectations':projected['expectations']}
            issues = unauthorized_candidate_semantics(candidate,projected['expectations'])
            plan = build_semantic_correction(candidate=candidate,design_brief=brief,expected_facts=expected,
                issues=[{'issue_id':f'issue-{i}','actual_ref':r['path']} for i,r in enumerate(issues)])
            clears = plan['edits'].get(identity,{}).get('changes',{}).get('/materials') == []
            wanted_clear = mode=='declared_none'
            rows.append({'family':target['ifc_class'],'mode':mode,'projection_valid':projected['valid'],
                         'expectation_count':len(projected['expectations']),
                         'material_clear_authorized':clears,'expected_clear':wanted_clear,
                         'passed':clears==wanted_clear})
    report = {'evidence_class':'offline deterministic diagnostic, no live transport',
              'baseline_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'tests':len(rows),'failed':sum(not r['passed'] for r in rows),'cases':rows,
              'limits':'Missing authority must be distinguished from explicit no-request; not a natural-language completeness proof or unseen capability benchmark.'}
    with args.output.open('x',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ['tests','failed']}))
    if args.assert_fixed:
        assert not report['failed'], 'Missing semantic authority still permits destructive cleanup'


if __name__ == '__main__':
    main()
