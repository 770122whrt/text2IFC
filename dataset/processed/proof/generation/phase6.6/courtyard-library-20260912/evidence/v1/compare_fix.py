"""Offline diagnosis of original bytes; never substitutes a repaired live Brief."""
import collections
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[3] / 'src'))
from text2ifc_agent.design_brief import validate_design_brief
from text2ifc_agent.brief_semantic_repair import semantic_repair_eligible
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation
from text2ifc_agent.generation_packages import build_generation_package_manifest

source = OUT / 'live-run/runs/a06665c5f155025f/calls/01-design-brief'
read = lambda name: json.loads((source / name).read_text(encoding='utf8'))
raw = (source / 'parsed-output.json').read_bytes()
brief = read('parsed-output.json')
issues = validate_design_brief(brief, evidence_catalog=read('context-selection.json')['evidence'],
    expected_schema_version=brief['schema_version'], conversation=read('conversation.json'))
facts = build_expected_facts(case_id='frozen-failed-attempt', design_brief=brief)
geometry = build_design_geometry_expectation(case_id='frozen-failed-attempt', design_brief=brief, expected_facts=facts)
packages = build_generation_package_manifest(facts)
roof = brief['known_facts']['roof_slab']
opening_id = roof['opening']['id']
result = {'evidence_class':'offline_diagnostic_of_original_failed_response', 'provider_calls':0,
    'source_sha256':hashlib.sha256(raw).hexdigest(), 'original_validation':read('validation.json'),
    'candidate_issues_by_code':dict(collections.Counter(i.code for i in issues)),
    'candidate_issues':[asdict(i) for i in issues],
    'semantic_repair_eligible':semantic_repair_eligible(brief, issues),
    'roof_opening':geometry['floor_openings'].get(opening_id),
    'roof_opening_identity':[r for r in facts['entity_id_contract']['floor_openings'] if r['brief_id']==opening_id],
    'roof_opening_owned':any(opening_id in p['owned_component_ids'] for p in packages['packages']),
    'scope':'Invalid Brief remains invalid. Eligibility and projection only; no corrected Provider output or whole building IFC.'}
assert (source / 'parsed-output.json').read_bytes() == raw
assert result['roof_opening'] and result['roof_opening_identity'] and result['roof_opening_owned']
(OUT / 'fix-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({k:result[k] for k in ('candidate_issues_by_code','semantic_repair_eligible','roof_opening_owned')}, ensure_ascii=False))
