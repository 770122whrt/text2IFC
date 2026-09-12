"""Read-only production-boundary reproduction; no Provider, IFC edits or compile."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'pyproject.toml').is_file())
sys.path.insert(0, str(ROOT / 'src'))
from text2ifc_agent.semantic_requirements import request_contract_issues, request_semantics_for_case

OUT = Path(__file__).resolve().parent
RUN = OUT.parent / 'A-revise/runtime/runs/026823cac75af845'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    candidate = read(RUN / 'candidate.json')
    request = request_semantics_for_case(RUN)
    current = request_contract_issues(candidate, request)
    without_seed = copy.deepcopy(candidate)
    without_seed['appearance'].pop('seed', None)
    projected_only = copy.deepcopy(request)
    for appearance in projected_only['appearance_requests']:
        appearance.pop('style_notes', None)
    schema = read(ROOT / 'schemas/bim-json/2.1/schema.json')['properties']['appearance']
    assert 'style_notes' not in schema['properties'] and schema['additionalProperties'] is False
    family = []
    for profile in ['neutral-architectural', 'warm-residential']:
        for note in [None, '浅暖墙面与深框，不能推断物理材料。', 'Coordinated facade; narrative evidence only.']:
            for wrong_profile in [False, True]:
                wanted = {'profile': profile}
                if note is not None:
                    wanted['style_notes'] = note
                actual = {'profile': ('warm-residential' if profile == 'neutral-architectural' else 'neutral-architectural') if wrong_profile else profile}
                issues = request_contract_issues({'appearance': actual}, {'appearance_requests': [wanted]})
                family.append({'requested': wanted, 'candidate': actual, 'expected_pass': not wrong_profile,
                               'actual_pass': not issues, 'issue_codes': [i['code'] for i in issues]})
    for wanted, actual in [('frozen-seed', 'frozen-seed'), ('frozen-seed', 'different-seed')]:
        issues = request_contract_issues({'appearance': {'profile': 'warm-residential', 'seed': actual}},
            {'appearance_requests': [{'profile': 'warm-residential', 'seed': wanted}]})
        family.append({'requested_seed': wanted, 'candidate_seed': actual,
                       'expected_pass': wanted == actual, 'actual_pass': not issues,
                       'issue_codes': [i['code'] for i in issues]})
    result = {
        'evidence_class': 'offline diagnostic reproduction of current production request comparator; not a new live run',
        'candidate_sha256': hashlib.sha256((RUN / 'candidate.json').read_bytes()).hexdigest(),
        'source_sha256': hashlib.sha256((ROOT / 'src/text2ifc_agent/semantic_requirements.py').read_bytes()).hexdigest(),
        'actual_candidate_appearance': candidate['appearance'],
        'actual_frozen_appearance_requests': request['appearance_requests'],
        'actual_issues': current,
        'remove_candidate_seed_only_issues': request_contract_issues(without_seed, request),
        'exclude_narrative_from_machine_comparison_only_issues': request_contract_issues(candidate, projected_only),
        'schema_appearance': schema, 'family': family,
        'family_mismatches': sum(row['expected_pass'] != row['actual_pass'] for row in family),
        'limits': 'Counterfactuals are memory-only copies for localization. No frozen request/candidate or published schema was edited. Passing this comparator alone does not prove IFC conformance or visual quality.',
    }
    with (OUT / 'appearance-projection-reproduction.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({'actual_issues': len(current), 'seed_removal_still_fails': bool(result['remove_candidate_seed_only_issues']),
                      'narrative_projection_only_issues': len(result['exclude_narrative_from_machine_comparison_only_issues']),
                      'family_cases': len(family), 'red_cases': result['family_mismatches']}))
    return 1 if result['family_mismatches'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
