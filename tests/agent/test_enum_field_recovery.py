"""Closed-enum field recovery: related positives, ambiguity and preservation."""
import copy
import json

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document
from tests.agent.test_early_field_recovery import apply, group
from tests.agent.test_phase6_5_changeset_apply import COMPLETE, _candidate, _changeset, _expected_facts, _revision


def candidate(cls='IfcSpace', field='InteriorOrExternalSpace', value='INTERNAL'):
    doc = _candidate(COMPLETE)
    doc['schema_version'] = 'bim-json/2.1'
    wall = next(e for e in doc['entities'] if e['ifc_class'] == 'IfcSpace')
    wall['ifc_class'] = cls
    wall['attributes'].pop('InteriorOrExteriorSpace')
    wall['attributes'][field] = value
    stair = next(e for e in doc['entities'] if e['ifc_class'] == 'IfcStair')
    stair['attributes'].pop('Representation')
    doc['relationships'].append({'id': 'aggregate-flight', 'ifc_class': 'IfcRelAggregates',
        'attributes': {'RelatingObject': stair['id'], 'RelatedObjects': ['stair-flight-1']}, 'provenance': {'source': 'test'}})
    return doc, wall


def proposal(doc, g):
    cs = _changeset(doc, _expected_facts())
    cs['source_issue_ids'] = g['scope']['source_issue_ids']
    cs['operations'] = []
    for entity_id, required in g['required_field_values'].items():
        attrs = copy.deepcopy(next(e['attributes'] for e in doc['entities'] if e['id'] == entity_id))
        for path in g['scope']['allowed_paths'][entity_id]:
            attrs.pop(path.rsplit('/', 1)[-1], None)
        attrs.update({p.rsplit('/', 1)[-1]: v for p, v in required.items()})
        cs['operations'].append({'operation_id': f'fix-{entity_id}', 'op': 'update_entity',
            'target_id': entity_id, 'target_component_hash': _revision(doc, _expected_facts())['component_hashes'][entity_id],
            'changes': {'/attributes': attrs}, 'evidence_refs': [i + ':/actual' for i in cs['source_issue_ids']]})
    return cs


@pytest.mark.parametrize('cls,old,value,new', [
    ('IfcSpace', 'InteriorOrExternalSpace', 'INTERNAL', 'InteriorOrExteriorSpace'),
    ('IfcSpace', 'SpaceExposure', 'EXTERNAL', 'InteriorOrExteriorSpace'),
    ('IfcWindowStyle', 'PanelOperation', 'SINGLE_PANEL', 'OperationType'),
])
def test_unique_closed_enum_offers_only_rename_and_preserves_source(cls, old, value, new):
    if cls == 'IfcSpace':
        doc, entity = candidate(cls, old, value)
    else:
        doc = _candidate()
        doc['schema_version'] = 'bim-json/2.1'
        entity = {'id': 'style', 'ifc_class': cls, 'attributes': {old: value}, 'property_sets': {}, 'provenance': {'source': 'test'}}
        doc['entities'].append(entity)
    before = copy.deepcopy(doc)
    g = group(doc)
    assert g['eligible']
    assert set(g['scope']['allowed_paths'][entity['id']]) == {f'/attributes/{old}', f'/attributes/{new}'}
    result = apply(doc, g, proposal(doc, g))
    assert result['valid'], result['issues']
    assert doc == before
    assert {r['id']: r for r in result['candidate']['relationships']} == {r['id']: r for r in doc['relationships']}
    assert not validate_v2_document(result['candidate'])


@pytest.mark.parametrize('mode', ['ambiguous', 'existing', 'unknown', 'number', 'feedback', 'two_sources'])
def test_unproven_enum_identity_or_conflicting_sources_fail_closed(mode):
    doc, entity = candidate()
    if mode == 'ambiguous':
        doc['entities'].append({'id': 'style', 'ifc_class': 'IfcDoorStyle', 'attributes': {'UnknownKind': 'NOTDEFINED'}, 'property_sets': {}, 'provenance': {'source': 'test'}})
    elif mode == 'existing':
        entity['attributes']['InteriorOrExteriorSpace'] = 'INTERNAL'
    elif mode == 'unknown':
        entity['attributes']['InteriorOrExternalSpace'] = 'INSIDE'
    elif mode == 'number':
        entity['attributes']['InteriorOrExternalSpace'] = 1
    elif mode == 'two_sources':
        entity['attributes']['SpaceExposure'] = 'EXTERNAL'
    else:
        from text2ifc_agent.early_recovery import build_field_recovery_group
        assert not build_field_recovery_group(doc, [])['eligible']
        return
    assert not group(doc)['eligible']


@pytest.mark.parametrize('mode', ['value', 'unrelated', 'relationship'])
def test_out_of_scope_or_changed_value_rolls_back(mode):
    doc, _ = candidate()
    before = copy.deepcopy(doc)
    g = group(doc)
    assert g['eligible']
    cs = proposal(doc, g)
    if mode == 'value':
        cs['operations'][0]['changes']['/attributes']['InteriorOrExteriorSpace'] = 'EXTERNAL'
    elif mode == 'unrelated':
        cs['operations'][0]['changes']['/attributes']['Description'] = 'unrequested'
    else:
        relation = doc['relationships'][-1]
        cs['operations'].append({'operation_id': 'drop-relation', 'op': 'remove_relationship',
            'target_id': relation['id'], 'target_component_hash': _revision(doc, _expected_facts())['component_hashes'][relation['id']],
            'evidence_refs': cs['operations'][0]['evidence_refs']})
    result = apply(doc, g, cs)
    assert not result['valid'] and result['candidate'] is None
    assert doc == before


def test_public_formal_repair_uses_changeset_and_preserves_all_relationships(tmp_path):
    from text2ifc_agent.live_pipeline import run_repair_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    doc, _ = candidate()
    g = group(doc)
    assert g['eligible']
    source = tmp_path / 'generator'
    source.mkdir()
    (source / 'input.txt').write_text('建立一个内部空间，保留其所在楼层。', encoding='utf-8')
    expected = _expected_facts()
    records = {'conversation': [], 'design-brief': {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': expected},
        'parsed-output': doc, 'validation': {'valid': False, 'issues': [vars(i) for i in validate_v2_document(doc)]},
        'metrics': {'contract_valid': False, 'classification': 'formal'}}
    for name, data in records.items():
        (source / f'{name}.json').write_text(json.dumps(data), encoding='utf-8')
    (tmp_path / 'expected-facts.json').write_text(json.dumps(expected), encoding='utf-8')
    result = run_repair_stage(provider_factory=lambda: SequenceProvider([proposal(doc, g)]),
        output_dir=tmp_path / 'repair', generator_source_dir=source, case_id='enum-field-family')
    assert result['valid'] and result['provider_call_count'] == 1
    after = json.loads((tmp_path / 'repair/repaired-candidate.json').read_text(encoding='utf-8'))
    assert {r['id']: r for r in after['relationships']} == {r['id']: r for r in doc['relationships']}
    assert json.loads((source / 'parsed-output.json').read_text(encoding='utf-8')) == doc
    route = json.loads((tmp_path / 'repair/route.json').read_text(encoding='utf-8'))
    assert route['recovery_contract'] == 'text2ifc/early-field-recovery/1.1'
