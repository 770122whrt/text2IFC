"""Frozen offline family for request-owned semantic graph correction.

The public Gate -> scope -> Provider ChangeSet -> apply -> reopened IFC boundary
is exercised without replacing downstream validation. No A/B case identities.
"""
import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as element
import pytest

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.issue_normalizers import normalize_gate_sidecars
from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from text2ifc_agent.scoped_loop import run_scoped_changeset_round
from text2ifc_agent.semantic_requirements import project_semantic_requirements
from tests.agent.test_semantic_scope_and_type_policy import _entity, _relation, _write
from tests.agent.test_phase6_5_staged_generation import SequenceProvider


def fixture(*, shared=False, inherited=False, prefix='sample'):
    candidate = json.loads((Path(__file__).parents[1] / 'contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.1'
    for row in candidate['entities']:
        row['materials'], row['property_sets'] = [], {}
    wall = next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcWall')
    other = copy.deepcopy(wall)
    other['id'] = prefix + '-other'
    other['attributes']['Name'] = '另一面墙'
    candidate['entities'].append(other)
    type_row = _entity(prefix + '-definition')
    type_row['attributes'] = {'Name': 'Unrequested definition', 'PredefinedType': 'STANDARD'}
    type_row['materials'] = [{'kind': 'single_material', 'name': 'Model guessed concrete'}]
    type_row['property_sets'] = {'Pset_WallCommon': {'FireRating': '120'}}
    candidate['entities'].append(type_row)
    link = _relation(prefix + '-membership', type_row['id'], [wall['id'], other['id']])
    candidate['relationships'].append(link)
    requested = {'entity_id': wall['id'], 'scope': 'inherited' if inherited else 'effective',
                 'material': {'kind': 'single_material', 'name': 'Requested brick'},
                 'property_sets': {'Pset_WallCommon': {'FireRating': '60'}}}
    if shared:
        requested['type_id'] = type_row['id']
        requested['scope'] = 'direct'
    brief = {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': {'semantic_requirements': [requested]}}
    expected = {'schema_version': 'text2ifc/expected-facts/1.0', 'storeys': [],
                'semantic_expectations': project_semantic_requirements(brief)['expectations']}
    return candidate, brief, expected, wall, other, type_row, link


def edits_for(data, *, shared=False):
    _, brief, _, wall, _, type_row, link = data
    req = brief['known_facts']['semantic_requirements'][0]
    updates = {wall['id']: {'op': 'update_entity', 'changes': {
        '/materials': [req['material']], '/property_sets': req['property_sets']}}}
    if shared:
        updates[type_row['id']] = {'op': 'update_entity', 'changes': {'/materials': [], '/property_sets': {}}}
        updates[link['id']] = {'op': 'update_relationship', 'changes': {'/attributes/RelatedObjects': [wall['id']]}}
    else:
        updates[type_row['id']] = {'op': 'remove_entity'}
        updates[link['id']] = {'op': 'remove_relationship'}
    return updates


class PatchProvider:
    def __init__(self, root, candidate, edits):
        self.root, self.candidate, self.edits = root, candidate, edits
        self.calls = []

    def generate_live(self, **kwargs):
        self.calls.append(kwargs)
        scope = json.loads((self.root/'change-scope.json').read_text(encoding='utf-8'))
        revision = json.loads((self.root/'base-revision.json').read_text(encoding='utf-8'))
        hashes = build_candidate_index(self.candidate)['component_hashes']
        payload = {'schema_version': 'text2ifc/bim-json-changeset/1.0', 'changeset_id': 'clean-semantics',
                   'base_revision_id': revision['revision_id'], 'base_candidate_hash': revision['candidate_hash'],
                   'expected_facts_hash': revision['expected_facts_hash'], 'scope_id': scope['scope_id'],
                   'source_issue_ids': scope['source_issue_ids'], 'operations': [
                       {'operation_id': f'edit-{i}', 'target_id': identity,
                        'target_component_hash': hashes[identity],
                        'evidence_refs': [issue + ':/actual' for issue in scope['source_issue_ids']], **edit}
                       for i, (identity, edit) in enumerate(self.edits.items())]}
        return SequenceProvider([payload]).generate_live(**kwargs)


def run_round(tmp_path, data, edits):
    candidate, brief, expected, *_ = data
    _write(tmp_path/'generator/candidate.json', candidate)
    _write(tmp_path/'design-brief.json', brief)
    _write(tmp_path/'expected-facts.json', expected)
    gate = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='semantic-family')
    assert not gate['semantic_verification']['valid']
    before = copy.deepcopy(candidate)
    provider = PatchProvider(tmp_path/'round', candidate, edits)
    result = run_scoped_changeset_round(provider=provider, output_dir=tmp_path/'round', case_id='semantic-family',
        round_number=1, user_request='这面墙使用指定砖材，耐火要求60分钟。其它内容保持。', conversation=[],
        design_brief=brief, expected_facts=expected, candidate=candidate,
        issues=normalize_gate_sidecars(tmp_path), max_attempts=1)
    assert candidate == before
    return result, provider


@pytest.mark.parametrize('prefix', ['alpha', 'opaque-71', 'building-z'])
def test_public_cleanup_restores_only_request_values_and_reopens(tmp_path, prefix):
    data = fixture(prefix=prefix)
    result, provider = run_round(tmp_path, data, edits_for(data))
    assert result['valid'], result
    assert len(provider.calls) == 1
    assert result['preservation']['unrelated_component_preservation_rate'] == 1.0
    assert result['preservation']['changed_ids'] == sorted([data[3]['id'], data[5]['id'], data[6]['id']])
    assert result['scope']['relationship_ids'] == [data[6]['id']]
    _write(tmp_path/'final/generator/candidate.json', result['candidate'])
    _write(tmp_path/'final/design-brief.json', data[1])
    gate = run_candidate_gate_stage(case_dir=tmp_path/'final', output_dir=tmp_path/'final', case_id='corrected')
    assert gate['compile_reopen_success'], gate
    assert gate['semantic_verification']['valid']
    model = ifcopenshell.open(str(tmp_path/'final/output.ifc'))
    assert model.schema == 'IFC2X3'
    assert not model.by_type('IfcWallType')
    wall = next(w for w in model.by_type('IfcWall') if element.get_material(w))
    assert element.get_material(wall).Name == 'Requested brick'
    assert element.get_psets(wall)['Pset_WallCommon']['FireRating'] == '60'
    assert not any(m.Name == 'Model guessed concrete' for m in model.by_type('IfcMaterial'))
    render = json.loads((tmp_path/'round/prompt-render-input.json').read_text(encoding='utf-8'))
    assert render['SEMANTIC_CORRECTION']['source_issue_ids']
    assert 'Requested brick' in json.dumps(render['SEMANTIC_CORRECTION'])


def test_mixed_type_members_keep_legal_group_and_direct_values(tmp_path):
    data = fixture(shared=True)
    # Already correct direct values must not be changed while trimming membership.
    req = data[1]['known_facts']['semantic_requirements'][0]
    data[3]['materials'], data[3]['property_sets'] = [req['material']], copy.deepcopy(req['property_sets'])
    edits = edits_for(data, shared=True)
    edits.pop(data[3]['id'])
    result, _ = run_round(tmp_path, data, edits)
    assert result['valid'], result
    after = build_candidate_index(result['candidate'])
    assert after['entities'][data[3]['id']] == data[3]
    assert after['entities'][data[4]['id']] == data[4]
    assert after['relationships'][data[6]['id']]['attributes']['RelatedObjects'] == [data[3]['id']]
    assert data[5]['id'] in after['entities']


@pytest.mark.parametrize('attack', ['partial', 'geometry', 'wrong_material', 'erase_requested', 'other_member'])
def test_bad_cleanup_is_atomic_and_never_published(tmp_path, attack):
    data = fixture()
    edits = edits_for(data)
    if attack == 'partial':
        edits.pop(data[6]['id'])
    elif attack == 'geometry':
        edits[data[3]['id']]['changes']['/attributes/Name'] = 'Unrequested rename'
    elif attack == 'wrong_material':
        edits[data[3]['id']]['changes']['/materials'] = data[5]['materials']
    elif attack == 'erase_requested':
        edits[data[3]['id']] = {'op': 'remove_entity'}
    else:
        edits[data[4]['id']] = {'op': 'remove_entity'}
    result, _ = run_round(tmp_path, data, edits)
    assert not result['valid']
    assert result['candidate'] is None
    assert not (tmp_path/'round/revisions').exists()
    assert not (tmp_path/'output.ifc').exists()


@pytest.mark.parametrize('conflict', ['inherited', 'unknown_reference', 'conflicting_frozen_value', 'requested_type_semantics'])
def test_unproven_cleanup_stops_before_transport(tmp_path, conflict):
    data = fixture(inherited=conflict == 'inherited')
    if conflict == 'unknown_reference':
        # A declared non-Type relation is not an authorized implicit cascade.
        relation = _relation('unknown-reference', data[5]['id'], [data[3]['id']])
        relation['ifc_class'] = 'IfcRelAssociatesClassification'
        relation['attributes'] = {'RelatingClassification': data[5]['id'], 'RelatedObjects': [data[3]['id']]}
        data[0]['relationships'].append(relation)
    elif conflict == 'conflicting_frozen_value':
        data[2]['semantic_expectations'][0]['value'] = {'kind': 'single_material', 'name': 'Different frozen material'}
    elif conflict == 'requested_type_semantics':
        data[1]['known_facts']['semantic_requirements'].append({'entity_id': data[5]['id'], 'material': data[5]['materials'][0]})
    result, provider = run_round(tmp_path, data, edits_for(data))
    assert not result['valid']
    assert not provider.calls
    assert any(i['code'].startswith('SEMANTIC_CORRECTION_') for i in result['issues'])


def test_field_permission_does_not_authorize_deleting_a_requested_type(tmp_path):
    data = fixture(shared=True)
    result, _ = run_round(tmp_path, data, {data[5]['id']: {'op': 'remove_entity'},
        data[6]['id']: {'op': 'remove_relationship'}})
    assert not result['valid']


def test_unrequested_property_removal_preserves_requested_siblings(tmp_path):
    data = fixture(shared=True)
    data[6]['attributes']['RelatedObjects'] = [data[3]['id']]
    data[5]['materials'], data[5]['property_sets'] = [], {}
    req = data[1]['known_facts']['semantic_requirements'][0]
    data[3]['materials'], data[3]['property_sets'] = [req['material']], copy.deepcopy(req['property_sets'])
    data[3]['property_sets']['Pset_WallCommon']['ThermalTransmittance'] = 0
    result, _ = run_round(tmp_path, data, {data[3]['id']: {'op': 'update_entity', 'changes': {'/property_sets': req['property_sets']}}})
    assert result['valid'], result
    assert build_candidate_index(result['candidate'])['entities'][data[3]['id']]['property_sets'] == req['property_sets']


def test_property_cleanup_escapes_user_pset_keys(tmp_path):
    data = fixture(shared=True)
    data[6]['attributes']['RelatedObjects'] = [data[3]['id']]
    data[5]['materials'], data[5]['property_sets'] = [], {}
    data[3]['property_sets'] = {'User/Pset': {'value~key': 'guessed'}}
    result, _ = run_round(tmp_path, data, {data[3]['id']: {'op': 'update_entity', 'changes': {'/property_sets': {}}}})
    assert result['valid'], result


@pytest.mark.parametrize('kind', ['IfcBeamType', 'IfcSlabType', 'IfcDoorStyle', 'IfcWindowStyle'])
def test_orphan_type_families_do_not_need_a_relationship_issue(tmp_path, kind):
    data = fixture()
    data[0]['relationships'].remove(data[6])
    data[5]['ifc_class'] = kind
    data[5]['materials'], data[5]['property_sets'] = [], {}
    data[5]['attributes'] = ({'Name': 'Unrequested style', 'ConstructionType': 'NOTDEFINED',
        'OperationType': 'NOTDEFINED', 'ParameterTakesPrecedence': False, 'Sizeable': False}
        if kind.endswith('Style') else {'Name': 'Unrequested type', 'PredefinedType': 'NOTDEFINED'})
    data[1]['known_facts']['semantic_requirements'] = []
    data[2]['semantic_expectations'] = []
    result, _ = run_round(tmp_path, data, {data[5]['id']: {'op': 'remove_entity'}})
    assert result['valid'], result
    assert result['preservation']['changed_ids'] == [data[5]['id']]


def test_staged_output_semantic_cleanup_uses_same_public_round(tmp_path):
    from text2ifc_agent.staged_generation import run_staged_generation
    from tests.agent.test_phase6_5_staged_generation import _fixture, _changesets
    skeleton, manifest, expected, values = _fixture(1)
    skeleton['schema_version'] = 'bim-json/2.1'
    for group in values:
        for row in group:
            if row['ifc_class'] == 'IfcSpace':
                row['attributes']['InteriorOrExteriorSpace'] = 'INTERNAL'
    wall = next(row for row in values[0] if row['id'] == 'wall-1')
    wall['attributes']['Representation']['profile']['x'] = 4000
    wall['property_sets'] = {'Pset_WallCommon': {'FireRating': 'guessed'}}
    brief = {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': {}}
    stage = run_staged_generation(provider=SequenceProvider(_changesets(skeleton, manifest, expected, values)),
        output_dir=tmp_path/'staged', case_id='staged-cleanup', user_request='按已确认尺寸生成。',
        conversation=[], design_brief=brief, expected_facts=expected, skeleton=skeleton, manifest=manifest)
    assert stage['valid'], stage
    result, _ = run_round(tmp_path/'review', (stage['candidate'], brief, expected),
        {'wall-1': {'op': 'update_entity', 'changes': {'/property_sets': {}}}})
    assert result['valid'], result
    final = tmp_path/'final'
    _write(final/'generator/candidate.json', result['candidate'])
    _write(final/'design-brief.json', brief)
    gate = run_candidate_gate_stage(case_dir=final, output_dir=final, case_id='staged-corrected')
    assert gate['compile_reopen_success'], gate
    assert gate['semantic_verification']['valid']


def test_ready_session_semantic_loop_publishes_and_resume_does_not_recall(tmp_path):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_phase6_2_fix_semantic_fidelity import _outside_boundary_design_brief, _outside_boundary_center_overlap_candidate
    brief = _outside_boundary_design_brief()
    brief['schema_version'] = 'text2ifc/design-brief/2.1'
    brief['provenance'].update(selected_evidence_ids=[], few_shot_ids=[])
    candidate = _outside_boundary_center_overlap_candidate()
    candidate['schema_version'] = 'bim-json/2.1'
    for row in candidate['entities']:
        row['property_sets'], row['materials'] = {}, []
    extra = _entity('unwanted-shared-type')
    extra['attributes'] = {'Name': 'Unrequested wall type', 'PredefinedType': 'STANDARD'}
    candidate['entities'].append(extra)
    candidate['relationships'].append(_relation('unwanted-membership', extra['id'], ['wall-south', 'wall-north']))
    store = SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path)
    session = store.create_session(original_input=brief['original_request'])
    result = run_design_brief_stage(provider=SequenceProvider([brief]),
        case={'case_id':session.session_hash, 'user_request':brief['original_request'], 'conversation':[]},
        output_dir=session.run_dir/'design-brief')
    assert result['valid'], result
    _write(session.run_dir/'design-brief.json', brief)
    store.mark_session_status(session.session_id, 'ready')
    audit = {'schema_version':'text2ifc/audit/2.0', 'recommendation':'accept', 'blocking':False,
        'deterministic_gate_status':'passed', 'findings':[],
        'evidence_paths':['generator/candidate.json','ifc-verification.json','semantic-verification.json']}

    class PublicProvider:
        def __init__(self):
            self.calls = []

        def generate_live(self, **kwargs):
            self.calls.append(kwargs['state']['stage'])
            if kwargs['state']['stage'] == 'changeset':
                return PatchProvider(session.run_dir/'changeset-round-01', candidate,
                    {extra['id']: {'op':'remove_entity'}, 'unwanted-membership': {'op':'remove_relationship'}}).generate_live(**kwargs)
            payload = candidate if len(self.calls) == 1 else audit
            return SequenceProvider([payload]).generate_live(**kwargs)

    provider = PublicProvider()
    result = run_ready_session_to_ifc(store=store, session=session.session_hash, provider_factory=lambda:provider)
    assert result.status == 'compiled', result
    assert provider.calls.count('changeset') == 1
    model = ifcopenshell.open(str(result.ifc_path))
    assert not model.by_type('IfcWallType')
    count = len(provider.calls)
    before = Path(result.ifc_path).read_bytes()
    # The ready-only API rejects a completed session before transport. The CLI
    # reads the existing artifacts instead; neither path regenerates this run.
    with pytest.raises(ValueError, match='requires a ready session'):
        run_ready_session_to_ifc(store=store, session=session.session_hash, provider_factory=lambda:provider)
    assert len(provider.calls) == count
    assert Path(result.ifc_path).read_bytes() == before
