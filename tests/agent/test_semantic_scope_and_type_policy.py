"""Frozen failure family: semantic field scope and request-owned explicit Types.

Offline only. These checks do not claim live success or repair geometry.
"""
import copy
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_agent.change_scope import derive_change_scope
from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.issue_normalizers import normalize_gate_sidecars
from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from text2ifc_agent.revisions import hash_json_value
from text2ifc_agent.scoped_loop import resolve_issue_component_refs, run_scoped_changeset_round
from text2ifc_agent.semantic_requirements import unauthorized_candidate_semantics

ROOT = Path(__file__).resolve().parents[2]


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def _entity(identity, kind='IfcWallType'):
    return {'id': identity, 'ifc_class': kind, 'attributes': {}, 'materials': [],
            'property_sets': {}, 'provenance': {'source': 'synthetic test'}}


def _relation(identity, type_id, instances):
    row = _entity(identity, 'IfcRelDefinesByType')
    row.pop('materials')
    row.pop('property_sets')
    row['attributes'] = {'RelatingType': type_id, 'RelatedObjects': instances}
    return row


def _candidate(*entities, relationships=()):
    return {'schema_version': 'bim-json/2.1', 'entities': list(entities), 'relationships': list(relationships)}


def _type_request(instance, type_id):
    return {'entity_id': instance, 'kind': 'type', 'scope': 'effective', 'value': type_id}


def _normalize(tmp_path, path, *, targets=None, known=True):
    candidate = _candidate(_entity('type-a'), _entity('type-other')) if known else _candidate()
    detail = {'code': 'UNREQUESTED_MATERIAL', 'path': path}
    if targets is not None:
        detail['target_entity_ids'] = targets
    _write(tmp_path / 'candidate.json', candidate)
    _write(tmp_path / 'gate-summary.json', {'overall_status': 'failed', 'gates': [
        {'name': 'request_semantics', 'status': 'failed', 'issues': [detail]}]})
    issues = normalize_gate_sidecars(tmp_path)
    return candidate, issues, resolve_issue_component_refs(candidate=candidate, issues=issues)


@pytest.mark.parametrize('field', ['materials', 'property_sets/Pset_WallCommon/FireRating',
                                  'appearance/color', 'template/template_id'])
def test_semantic_field_reaches_scope_without_attributes_replacement(tmp_path, field):
    candidate, _, resolved = _normalize(tmp_path, f'/entities/type-a/{field}')
    assert not resolved['issues']
    assert resolved['resolved'][0]['actual_ref'] == f'entity:type-a#/{field}'
    result = derive_change_scope(candidate=candidate, issues=resolved['resolved'],
                                 scope_id='scope-fields', base_revision_id='revision-00')
    assert result['scope']['allowed_paths'] == {'type-a': [f'/{field}']}
    assert 'type-other' in result['scope']['forbidden_ids']


def test_semantic_property_pointer_escaping_is_preserved(tmp_path):
    _, _, resolved = _normalize(tmp_path, '/entities/type-a/property_sets/User~1Pset/Value~0Key')
    assert resolved['resolved'][0]['actual_ref'] == 'entity:type-a#/property_sets/User~1Pset/Value~0Key'


def test_unknown_semantic_target_stays_unresolved(tmp_path):
    _, _, resolved = _normalize(tmp_path, '/entities/missing/materials')
    assert resolved['issues'] and not resolved['resolved']


def test_semantic_target_disagreement_does_not_grant_other_entity(tmp_path):
    _, issues, resolved = _normalize(tmp_path, '/entities/type-a/materials', targets=['type-other'])
    assert not resolved['resolved']
    assert all(i.suggested_route == 'gate_issue' and not i.retryable for i in issues)


def test_geometry_dependency_scope_keeps_existing_contract(tmp_path):
    candidate = _candidate(_entity('type-a'))
    _write(tmp_path / 'candidate.json', candidate)
    _write(tmp_path / 'geometry-feedback.json', {'success': False, 'issues': [
        {'code': 'BBOX_MISMATCH', 'path': '/entities/type-a/attributes/Representation', 'entity_ids': ['type-a']} ]})
    assert normalize_gate_sidecars(tmp_path)[0].actual_ref == 'entity:type-a#/attributes'


@pytest.mark.parametrize('kind', ['IfcWallType', 'IfcSlabType', 'IfcDoorStyle', 'IfcWindowStyle', 'IfcBeamType'])
def test_no_requested_type_rejects_empty_or_claimed_compiler_type(kind):
    row = _entity('extra-type', kind)
    row['provenance'] = {'source': 'compiler', 'authorized': True}
    issues = unauthorized_candidate_semantics(_candidate(row), [])
    assert any(i['code'] == 'UNREQUESTED_TYPE' and i['path'] == '/entities/extra-type' for i in issues)


def test_requested_shared_type_allows_only_requested_members():
    a, b, other, type_row = [_entity(i, 'IfcWall' if i != 'requested-type' else 'IfcWallType')
                              for i in ['wall-a', 'wall-b', 'wall-other', 'requested-type']]
    requirements = [_type_request('wall-a', 'requested-type'), _type_request('wall-b', 'requested-type')]
    relation = _relation('type-link', 'requested-type', ['wall-a', 'wall-b'])
    candidate = _candidate(a, b, other, type_row, relationships=[relation])
    assert unauthorized_candidate_semantics(candidate, requirements) == []
    relation['attributes']['RelatedObjects'].append('wall-other')
    issues = unauthorized_candidate_semantics(candidate, requirements)
    assert any(i['code'] == 'UNREQUESTED_TYPE_ASSIGNMENT' and i['path'].startswith('/relationships/type-link/') for i in issues)


def test_requested_distinct_types_are_not_merged_or_rejected():
    candidate = _candidate(_entity('wall-a', 'IfcWall'), _entity('wall-b', 'IfcWall'),
                           _entity('type-a'), _entity('type-b'), relationships=[
                               _relation('link-a', 'type-a', ['wall-a']), _relation('link-b', 'type-b', ['wall-b'])])
    before = copy.deepcopy(candidate)
    assert unauthorized_candidate_semantics(candidate, [_type_request('wall-a', 'type-a'), _type_request('wall-b', 'type-b')]) == []
    assert candidate == before


def test_type_permission_does_not_authorize_material_or_performance():
    row = _entity('requested-type')
    row['materials'] = [{'kind': 'single_material', 'name': 'Guessed brick'}]
    row['property_sets'] = {'Pset_WallCommon': {'FireRating': '60'}}
    issues = unauthorized_candidate_semantics(_candidate(row), [_type_request('wall-a', 'requested-type')])
    assert {i['code'] for i in issues} == {'UNREQUESTED_MATERIAL', 'UNREQUESTED_PROPERTY'}


def test_legacy_generation_contract_keeps_old_type_behavior():
    candidate = _candidate(_entity('old-type'))
    candidate['schema_version'] = 'bim-json/2.0'
    assert unauthorized_candidate_semantics(candidate, []) == []


def test_public_gate_blocks_unrequested_type_before_compilation(tmp_path):
    candidate = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.1'
    for entity in candidate['entities']:
        entity['materials'], entity['property_sets'] = [], {}
    extra = _entity('unexpected-wall-type')
    extra['attributes'] = {'Name': 'Unexpected', 'PredefinedType': 'NOTDEFINED'}
    candidate['entities'].append(extra)
    _write(tmp_path / 'generator/candidate.json', candidate)
    _write(tmp_path / 'design-brief.json', {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': {'semantic_requirements': []}})
    original = (tmp_path / 'generator/candidate.json').read_bytes()
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='unrequested-type')
    assert not result['compile_reopen_success']
    assert any(i['code'] == 'UNREQUESTED_TYPE' for i in result['semantic_verification']['issues'])
    assert not (tmp_path / 'output.ifc').exists()
    assert (tmp_path / 'generator/candidate.json').read_bytes() == original


def test_public_gate_keeps_compiler_owned_minimal_door_style(tmp_path):
    from tests.compiler.test_basic_filling import public_document
    candidate = public_document('door-left')
    for entity in candidate['entities']:
        entity['materials'], entity['property_sets'] = [], {}
    _write(tmp_path / 'generator/candidate.json', candidate)
    _write(tmp_path / 'design-brief.json', {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': {'semantic_requirements': []}})
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='compiler-style')
    assert result['compile_reopen_success'], result['ifc_verification']
    model = ifcopenshell.open(str(tmp_path / 'output.ifc'))
    assert len(model.by_type('IfcDoorStyle')) == 1
    assert model.by_type('IfcDoorStyle')[0].OperationType == 'SINGLE_SWING_LEFT'


@pytest.mark.parametrize('violate_scope', [False, True])
def test_public_semantic_changeset_applies_or_rolls_back_without_changing_type(tmp_path, violate_scope):
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    import ifcopenshell.util.element as util

    candidate = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.1'
    for entity in candidate['entities']:
        entity['materials'], entity['property_sets'] = [], {}
    wall = next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcWall')
    wall['materials'] = [{'kind': 'single_material', 'name': 'Requested brick'}]
    type_row = _entity('requested-type')
    type_row['attributes'] = {'Name': 'Requested wall type', 'PredefinedType': 'STANDARD'}
    type_row['materials'] = [{'kind': 'single_material', 'name': 'Unrequested concrete'}]
    candidate['entities'].append(type_row)
    candidate['relationships'].append(_relation('requested-type-link', type_row['id'], [wall['id']]))
    brief = {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': {
        'semantic_requirements': [{'entity_id': wall['id'], 'type_id': type_row['id'],
                                   'material': wall['materials'][0]}]}}
    _write(tmp_path / 'generator/candidate.json', candidate)
    _write(tmp_path / 'design-brief.json', brief)
    gate = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='field-scope')
    assert [i['code'] for i in gate['semantic_verification']['issues']] == ['UNREQUESTED_MATERIAL']
    issues = [i.to_dict() for i in normalize_gate_sidecars(tmp_path)]
    expected = {'schema_version': 'text2ifc/expected-facts/1.0', 'storeys': []}
    index = build_candidate_index(candidate)
    before = copy.deepcopy(candidate)
    original_bytes = (tmp_path / 'generator/candidate.json').read_bytes()
    round_dir = tmp_path / 'round'

    class SemanticPatchProvider:
        """Offline response bound to the real round's scope and revision."""
        def generate_live(self, **kwargs):
            scope = json.loads((round_dir / 'change-scope.json').read_text(encoding='utf-8'))
            revision = json.loads((round_dir / 'base-revision.json').read_text(encoding='utf-8'))
            changes = {'/materials': []}
            if violate_scope:
                changes['/attributes/Name'] = 'Unrequested rename'
            payload = {
                'schema_version': 'text2ifc/bim-json-changeset/1.0',
                'changeset_id': 'changeset-semantic-field',
                'base_revision_id': revision['revision_id'],
                'base_candidate_hash': index['candidate_hash'],
                'expected_facts_hash': hash_json_value(expected),
                'source_issue_ids': scope['source_issue_ids'], 'scope_id': scope['scope_id'],
                'operations': [{'operation_id': 'remove-guessed-material', 'op': 'update_entity',
                    'target_id': type_row['id'], 'target_component_hash': index['component_hashes'][type_row['id']],
                    'changes': changes, 'evidence_refs': [i + ':/actual' for i in scope['source_issue_ids']]}]}
            return SequenceProvider([payload]).generate_live(**kwargs)

    result = run_scoped_changeset_round(provider=SemanticPatchProvider(), output_dir=round_dir,
        case_id='field-scope', round_number=1, user_request='墙使用指定砖材和指定类型。',
        conversation=[], design_brief=brief, expected_facts=expected, candidate=candidate,
        issues=issues, max_attempts=1)
    assert candidate == before
    assert (tmp_path / 'generator/candidate.json').read_bytes() == original_bytes
    assert result['scope']['allowed_paths'] == {type_row['id']: ['/materials']}
    if violate_scope:
        assert not result['valid'] and result['status'] == 'application_blocked'
        assert any(i['code'] == 'CHANGESET_SCOPE_VIOLATION' for i in result['issues'])
        assert not (round_dir / 'revisions').exists()
        assert not (tmp_path / 'output.ifc').exists()
        return
    assert result['valid'], result
    wanted = copy.deepcopy(before)
    wanted['entities'][-1]['materials'] = []
    assert build_candidate_index(result['candidate']) == build_candidate_index(wanted)
    assert result['preservation']['unrelated_component_preservation_rate'] == 1.0
    final = tmp_path / 'final'
    _write(final / 'generator/candidate.json', result['candidate'])
    _write(final / 'design-brief.json', brief)
    gates = run_candidate_gate_stage(case_dir=final, output_dir=final, case_id='field-scope-final')
    assert gates['compile_reopen_success'], gates['ifc_verification']
    model = ifcopenshell.open(str(final / 'output.ifc'))
    assert len(model.by_type('IfcWallType')) == 1
    reopened_wall = next(w for w in model.by_type('IfcWall') if util.get_type(w))
    assert util.get_type(reopened_wall).Name == 'Requested wall type'
    assert util.get_material(reopened_wall).Name == 'Requested brick'
    assert not any(m.Name == 'Unrequested concrete' for m in model.by_type('IfcMaterial'))


def test_whole_type_issue_never_grants_automatic_deletion(tmp_path):
    candidate = _candidate(_entity('extra-type'), relationships=[_relation('extra-link', 'extra-type', ['wall-a'])])
    diagnostics = unauthorized_candidate_semantics(candidate, [])
    _write(tmp_path / 'candidate.json', candidate)
    _write(tmp_path / 'gate-summary.json', {'overall_status': 'failed', 'gates': [
        {'name': 'request_semantics', 'status': 'failed', 'issues': diagnostics}]})
    resolved = resolve_issue_component_refs(candidate=candidate, issues=normalize_gate_sidecars(tmp_path))
    assert not resolved['issues']
    assert [i['actual_ref'] for i in resolved['context']] == ['/entities/extra-type']
    assert [i['actual_ref'] for i in resolved['resolved']] == ['relationship:extra-link#/attributes/RelatingType']
    scope = derive_change_scope(candidate=candidate, issues=resolved['resolved'],
                                scope_id='scope-types', base_revision_id='revision-00')['scope']
    assert scope['entity_ids'] == []
    assert scope['allowed_paths'] == {'extra-link': ['/attributes/RelatingType']}


@pytest.mark.parametrize('field', ['materials', 'property_sets', 'appearance', 'template'])
def test_semantic_field_scope_cannot_unlock_geometry_relationships(field):
    candidate = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    wall = next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcWall')
    issue = {'issue_id': 'issue-wall-semantic', 'actual_ref': f"entity:{wall['id']}#/{field}"}
    scope = derive_change_scope(candidate=candidate, issues=[issue],
                                scope_id='scope-field-only', base_revision_id='revision-00')['scope']
    assert scope['entity_ids'] == [wall['id']]
    assert scope['relationship_ids'] == []
    assert scope['allowed_paths'] == {wall['id']: [f'/{field}']}


def test_mixed_semantic_and_geometry_issues_keep_geometry_dependencies():
    candidate = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    wall = next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcWall')
    geometry = {'issue_id': 'issue-geometry', 'actual_ref': f"entity:{wall['id']}#/attributes"}
    semantic = {'issue_id': 'issue-material', 'actual_ref': f"entity:{wall['id']}#/materials"}
    args = {'candidate': candidate, 'scope_id': 'scope-mixed', 'base_revision_id': 'revision-00'}
    old = derive_change_scope(issues=[geometry], **args)['scope']
    mixed = derive_change_scope(issues=[semantic, geometry], **args)['scope']
    assert old['relationship_ids']
    for field in ['entity_ids', 'relationship_ids', 'dependencies', 'forbidden_ids']:
        assert mixed[field] == old[field]
    assert mixed['allowed_paths'] == {**old['allowed_paths'], wall['id']: ['/attributes', '/materials']}
