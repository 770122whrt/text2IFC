"""T2 frozen family: real validator -> bounded group -> atomic application."""
import copy
import json

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document
from tests.agent.test_phase6_5_changeset_apply import _candidate, _changeset, _expected_facts, _revision


def candidate():
    value = _candidate()
    value['schema_version'] = 'bim-json/2.1'
    for n, cls in enumerate(['IfcWindowStyle', 'IfcDoorStyle']):
        value['entities'].append({'id': f'style-{n}', 'ifc_class': cls,
            'attributes': {'ConstructionType': 'INVALID'}, 'property_sets': {},
            'provenance': {'source': 'test'}})
    return value


def group(value):
    from text2ifc_agent.early_recovery import build_field_recovery_group
    issues = [vars(i) for i in validate_v2_document(value)]
    return build_field_recovery_group(value, issues)


def patch(value, scope, *, omit_last=False, drift=False):
    cs = _changeset(value, _expected_facts())
    cs['source_issue_ids'] = scope['source_issue_ids']
    cs['operations'] = []
    ids = scope['entity_ids'][:-1] if omit_last else scope['entity_ids']
    idx = _revision(value, _expected_facts())['component_hashes']
    for n, entity_id in enumerate(ids):
        attrs = copy.deepcopy(next(e['attributes'] for e in value['entities'] if e['id'] == entity_id))
        if 'ConstructionType' in attrs:
            attrs['ConstructionType'] = 'NOTDEFINED'
        if 'Names' in attrs:
            attrs['Name'] = attrs.pop('Names')
        if drift:
            attrs['Description'] = 'unrequested'
        cs['operations'].append({'operation_id': f'fix-{n}', 'op': 'update_entity',
            'target_id': entity_id, 'target_component_hash': idx[entity_id],
            'changes': {'/attributes': attrs}, 'evidence_refs': scope['source_issue_ids']})
    return cs


def apply(value, g, cs):
    from text2ifc_agent.changeset_apply import apply_changeset
    return apply_changeset(candidate=value, changeset=cs, scope=g['scope'],
        base_revision=_revision(value, _expected_facts()), expected_facts=_expected_facts(),
        allow_field_containers=True)


def test_multiple_enum_errors_are_one_stable_atomic_group():
    value = candidate()
    original = copy.deepcopy(value)
    g = group(value)
    assert g['eligible']
    assert g['scope']['entity_ids'] == ['style-0', 'style-1']
    assert all(p == ['/attributes/ConstructionType'] for p in g['scope']['allowed_paths'].values())
    result = apply(value, g, patch(value, g['scope']))
    assert result['valid'], result['issues']
    assert value == original
    assert not validate_v2_document(result['candidate'])


@pytest.mark.parametrize('mode', ['partial', 'unrelated', 'stale'])
def test_group_never_promotes_partial_or_out_of_scope_result(mode):
    value = candidate()
    original = copy.deepcopy(value)
    g = group(value)
    cs = patch(value, g['scope'], omit_last=mode == 'partial', drift=mode == 'unrelated')
    if mode == 'stale':
        cs['base_candidate_hash'] = 'sha256:' + '0' * 64
    result = apply(value, g, cs)
    assert not result['valid'] and result['candidate'] is None
    assert value == original


def test_registry_derived_unique_field_rename_preserves_value_and_other_attributes():
    value = _candidate()
    value['schema_version'] = 'bim-json/2.1'
    wall = next(e for e in value['entities'] if e['ifc_class'] == 'IfcWall')
    wall['attributes']['Names'] = wall['attributes'].pop('Name', 'Wall')
    g = group(value)
    assert g['eligible']
    assert g['scope']['allowed_paths'][wall['id']] == ['/attributes/Name', '/attributes/Names']
    result = apply(value, g, patch(value, g['scope']))
    assert result['valid'], result['issues']
    after = next(e for e in result['candidate']['entities'] if e['id'] == wall['id'])
    assert after['attributes']['Name'] == wall['attributes']['Names']


@pytest.mark.parametrize('change', ['unknown', 'collision', 'wrong_value', 'duplicate_id', 'conflict'])
def test_unproven_routes_fail_closed(change):
    value = candidate()
    wall = next(e for e in value['entities'] if e['ifc_class'] == 'IfcWall')
    if change == 'unknown':
        wall['attributes']['UnrelatedTypo'] = 1
    elif change == 'collision':
        wall['attributes'].update(Name='retained', Names='different')
    elif change == 'wrong_value':
        wall['attributes']['Names'] = 10
    elif change == 'duplicate_id':
        value['entities'].append(copy.deepcopy(wall))
    else:
        from text2ifc_agent.early_recovery import build_field_recovery_group
        assert not build_field_recovery_group(value, [{'code':'BASIC_FILLING_CONSTRAINT_CONFLICT',
            'path':'/entities/1/attributes/Representation'}])['eligible']
        return
    assert not group(value)['eligible']


def test_semantic_dependencies_are_read_only_including_other_type_users():
    from text2ifc_agent.early_recovery import semantic_dependency_context
    value = candidate()
    value['entities'].append({'id':'wall-other', 'ifc_class':'IfcWall', 'attributes':{}})
    value['relationships'].append({'id':'shared-type', 'ifc_class':'IfcRelDefinesByType',
        'attributes':{'RelatingType':'style-0','RelatedObjects':['wall-1','wall-other']}})
    context = semantic_dependency_context(value, ['wall-1'])
    assert {'shared-type','style-0','wall-other'} <= set(context)
    assert 'style-1' not in context


def test_public_repair_stage_uses_bounded_changeset_for_invalid_formal(tmp_path):
    from text2ifc_agent.live_pipeline import run_repair_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    value = candidate()
    g = group(value)
    expected = _expected_facts()
    source = tmp_path/'generator'
    source.mkdir()
    (source/'input.txt').write_text('生成房间。', encoding='utf-8')
    records = {'conversation':[], 'design-brief':{'schema_version':'text2ifc/design-brief/2.1',
        'known_facts':expected}, 'parsed-output':value,
        'validation':{'valid':False, 'issues':[vars(i) for i in validate_v2_document(value)]},
        'metrics':{'contract_valid':False}}
    for name, record in records.items():
        (source/f'{name}.json').write_text(json.dumps(record), encoding='utf-8')
    provider = SequenceProvider([patch(value, g['scope'])])
    result = run_repair_stage(provider_factory=lambda:provider, output_dir=tmp_path/'repair',
        generator_source_dir=source, case_id='field-family')
    assert result['valid'] and result['provider_call_count'] == 1
    assert (tmp_path/'repair/repaired-candidate.json').is_file()
    assert (tmp_path/'repair/scoped/changeset.json').is_file()
    assert json.loads((source/'parsed-output.json').read_text()) == value
