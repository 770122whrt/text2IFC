"""Reproduce offline integration after the 2026-09-22 fixes. No Provider calls.

Frozen real graphs are composed, not regenerated. Never edit their evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
from scripts.ifc2text.check_wall_context_v09 import (
    BASE, DONOR, load, save, merge_wall_representation, compile_case,
    by_bim_id, non_target_checks, system_refs,
)
from text2ifc_ifc2text.precision_compare_v10 import compare_roundtrip
from text2ifc_ifc2text.wall_compare_v09 import compare_wall_entities
from text2ifc_ifc2text.observation import all_items, extract_description_facts
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation
import ifcopenshell


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='dataset/processed/experiments/ifc2text-fixes-20260922/full-scene-integration')
    args = parser.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'dataset/external/bimnet/hxp.ifc'
    brief_path = BASE.parent.parent / 'design-brief/design-brief.json'
    inputs = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE, DONOR, source, brief_path)}
    brief = load(brief_path)
    expected = build_expected_facts(case_id='hxp-offline-replay', design_brief=brief)
    space_versions = {}
    for version in ('1.1', '1.2'):
        expectation = build_design_geometry_expectation(case_id='hxp-offline-replay', design_brief=brief,
            expected_facts=expected, schema_version='text2ifc/design-geometry-expectation/' + version)
        save(out / ('space-expectation-' + version + '.json'), expectation)
        space_versions[version] = {'spaces': len(expectation['spaces']), 'complete': expectation['complete'],
                                   'unresolved': expectation['unresolved']}
    assert space_versions['1.1']['spaces'] == 0
    assert space_versions['1.2']['spaces'] == 5 and space_versions['1.2']['complete']
    base, donor = load(BASE), load(DONOR)
    target = next(e['id'] for e in base['entities'] if e['ifc_class'] == 'IfcWall' and e['attributes'].get('Name') == 'W013')
    donor_id = next(e['id'] for e in donor['entities'] if e['ifc_class'] == 'IfcWall')
    old_composition = merge_wall_representation(base, target, donor, donor_id)
    new_composition = copy.deepcopy(old_composition)
    new_composition['schema_version'] = 'bim-json/2.4'
    models, compilation = {}, {}
    for name, graph in [('baseline', base), ('old-v23-composition', old_composition), ('new-v24-composition', new_composition)]:
        save(out / (name + '.json'), graph)
        models[name], compilation[name] = compile_case(graph, out / (name + '.ifc'))
    assert models['baseline'] is not None
    assert models['old-v23-composition'] is None, 'Frozen negative control must still reject unsupported polygon hosts'
    assert models['new-v24-composition'] is not None, compilation['new-v24-composition']
    facts = extract_description_facts(source)
    guid = next(i['source_global_id'] for category, i in all_items(facts) if category == 'walls' and i['label'] == 'W013')
    source_model = ifcopenshell.open(str(source))
    source_wall = source_model.by_guid(guid)
    walls, comparisons = {}, {}
    for name in ('baseline', 'new-v24-composition'):
        walls[name] = compare_wall_entities(source_wall, by_bim_id(models[name])[target])
        comparison = compare_roundtrip(source, out / (name + '.ifc'))
        save(out / (name + '-compare-0.1mm.json'), comparison)
        comparisons[name] = {'summary': comparison['summary'], 'status': comparison['status']}
    before, after = models['baseline'], models['new-v24-composition']
    preservation = non_target_checks(before, after, target)
    target_relations_unchanged = system_refs(by_bim_id(before)[target]) == system_refs(by_bim_id(after)[target])
    hashes_unchanged = all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in inputs.items())
    assert hashes_unchanged
    assert preservation['all_pass'], preservation
    assert target_relations_unchanged
    assert walls['new-v24-composition']['pass']
    summary = {
        'provider_calls': 0,
        'experiment': 'offline integration of two archived real-provider graphs',
        'fresh_whole_building_generation': False, 'whole_building_accepted': False,
        'source_and_archived_inputs_unchanged': hashes_unchanged,
        'input_sha256': {str(p.relative_to(ROOT)): h for p, h in inputs.items()},
        'target_id': target, 'compilation': compilation, 'wall_results': walls,
        'space_projection': space_versions,
        'non_target_preservation': preservation, 'target_relations_unchanged': target_relations_unchanged,
        'comparison': comparisons,
        'limits': ['Only W013 geometry replaced; other original errors remain.',
                   'Wall sections are sampled, not a proof of all surfaces.',
                   'This is an engineering regression experiment, not unseen capability evidence.'],
    }
    save(out / 'summary.json', summary)
    print({'old_v23_rejected': True, 'v24_compiled': True, 'non_target_preserved': preservation['tested_products'],
           'space_counts': {k: v['spaces'] for k, v in space_versions.items()},
           'wall_pass': walls['new-v24-composition']['pass'], 'comparison': comparisons})


if __name__ == '__main__':
    main()
