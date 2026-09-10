"""Frozen, offline appearance authority and bounded cleanup family.

No live scene identities. The frozen request, not candidate provenance, owns
whole-product overrides; explicit user overrides retain their existing meaning.
"""
import copy
import json

import ifcopenshell
import pytest

from tests.compiler.test_basic_filling import public_document, representation, TEMPLATES
from tests.agent.test_semantic_scope_and_type_policy import _write
from tests.agent.test_generation_semantic_correction import PatchProvider
from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from text2ifc_agent.issue_normalizers import normalize_gate_sidecars
from text2ifc_agent.scoped_loop import run_scoped_changeset_round
from text2ifc_agent.semantic_requirements import unauthorized_candidate_semantics
from text2ifc_compiler import compile_document
from text2ifc_presentation import item_appearance_signatures


def fixture(template='door-left', explicit=False):
    candidate = public_document()
    for e in candidate['entities']:
        e['materials'], e['property_sets'] = [], {}
    filling = next(e for e in candidate['entities'] if e['id'] == 'door-1')
    filling['ifc_class'] = 'IfcWindow' if template.startswith('window') else 'IfcDoor'
    rep = representation(template, width=900, height=2100)
    filling['attributes'].update(Representation=rep, OverallWidth=900, OverallHeight=2100)
    candidate['appearance'] = {'profile': 'warm-residential'}
    filling['appearance'] = {'color': [.2, .2, .22], 'transparency': .7}
    brief = {'schema_version': 'text2ifc/design-brief/2.1', 'known_facts': {
        'appearance': candidate['appearance'], 'semantic_requirements': []}}
    if explicit:
        brief['known_facts']['semantic_requirements'].append(
            {'entity_id': filling['id'], 'appearance': copy.deepcopy(filling['appearance'])})
    expected = {'schema_version': 'text2ifc/expected-facts/1.0', 'storeys': []}
    return candidate, brief, expected, filling


@pytest.mark.parametrize('template', TEMPLATES)
@pytest.mark.parametrize('explicit', [False, True])
def test_public_gate_requires_request_authority(tmp_path, template, explicit):
    candidate, brief, expected, filling = fixture(template, explicit)
    _write(tmp_path/'generator/candidate.json', candidate)
    _write(tmp_path/'design-brief.json', brief)
    _write(tmp_path/'expected-facts.json', expected)
    gate = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='style-authority')
    assert gate['compile_reopen_success'] is explicit
    assert (tmp_path/'output.ifc').exists() is explicit
    if not explicit:
        assert 'UNREQUESTED_APPEARANCE' in json.dumps(gate)


@pytest.mark.parametrize('family', ['IfcWall', 'IfcBeam', 'IfcDoor', 'IfcWindow', 'IfcWindowStyle'])
@pytest.mark.parametrize('provenance', ['user', 'theme', 'template'])
def test_candidate_source_label_cannot_authorize_override(family, provenance):
    e = {'id': 'opaque-style-target', 'ifc_class': family,
         'appearance': {'color': [0, 0, 0], 'transparency': 1}, 'provenance': {'source': provenance}}
    issues = unauthorized_candidate_semantics({'schema_version': 'bim-json/2.1', 'entities': [e]}, [])
    assert any(i['code'] == 'UNREQUESTED_APPEARANCE' for i in issues)


class RemovalProvider(PatchProvider):
    def generate_live(self, **kwargs):
        from tests.agent.test_phase6_5_staged_generation import SequenceProvider
        # Reuse the exact bound control records and hashes from the existing
        # offline Provider seam, only changing the new contract version.
        original = SequenceProvider.generate_live
        def versioned(instance, **call):
            instance.payloads[0]['schema_version'] = 'text2ifc/bim-json-changeset/1.1'
            return original(instance, **call)
        from unittest.mock import patch
        with patch.object(SequenceProvider, 'generate_live', versioned):
            return super().generate_live(**kwargs)


@pytest.mark.parametrize('template', TEMPLATES)
def test_scoped_unset_restores_part_styles_without_geometry_change(tmp_path, template):
    candidate, brief, expected, filling = fixture(template)
    for name, value in [('generator/candidate', candidate), ('design-brief', brief), ('expected-facts', expected)]:
        _write(tmp_path/(name+'.json'), value)
    before = copy.deepcopy(candidate)
    gate = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='style-cleanup')
    assert not gate['compile_reopen_success']
    provider = RemovalProvider(tmp_path/'round', candidate, {filling['id']: {
        'op': 'update_entity', 'remove_paths': ['/appearance']}})
    result = run_scoped_changeset_round(provider=provider, output_dir=tmp_path/'round', case_id='style-cleanup',
        round_number=1, user_request='使用协调主题和默认部件分色。', conversation=[],
        design_brief=brief, expected_facts=expected, candidate=candidate,
        issues=normalize_gate_sidecars(tmp_path), max_attempts=1)
    assert result['valid'], result
    assert candidate == before
    after = copy.deepcopy(before)
    next(e for e in after['entities'] if e['id'] == filling['id']).pop('appearance')
    after['entities'].sort(key=lambda e: e['id'])
    after['relationships'].sort(key=lambda e: e['id'])
    assert result['candidate'] == after
    assert result['preservation']['unrelated_component_preservation_rate'] == 1
    # Both geometries are built by the unchanged compiler. Mesh coordinates
    # remain exact while only effective item styles differ.
    from tests.compiler.test_basic_filling import vertices
    paths = [tmp_path/'before.ifc', tmp_path/'after.ifc']
    for doc, path in zip([before, after], paths):
        assert compile_document(doc, path).success
    models = [ifcopenshell.open(str(p)) for p in paths]
    products = [m.by_type(filling['ifc_class'])[0] for m in models]
    assert (vertices(products[0]) == vertices(products[1])).all()
    by_role = {a.Name: [sig for r in a.ShapeRepresentations for i in r.Items
                       for sig in item_appearance_signatures(i)]
               for a in products[1].Representation.HasShapeAspects}
    frame = by_role.get('Framing', by_role.get('Lining'))
    assert all(s['transparency'] == 0 for s in frame)
    if template.startswith('window'):
        assert all(s['transparency'] == .45 for s in by_role['Glazing'])
    assert len({(s['red'], s['green'], s['blue']) for group in by_role.values() for s in group}) >= 2


@pytest.mark.parametrize('attack', ['geometry', 'identity', 'unknown_field', 'whole_entity', 'null', 'empty'])
def test_cleanup_cannot_expand_scope_or_encode_absence_as_a_value(tmp_path, attack):
    candidate, brief, expected, filling = fixture()
    for name, value in [('generator/candidate', candidate), ('design-brief', brief), ('expected-facts', expected)]:
        _write(tmp_path/(name+'.json'), value)
    run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='style-attack')
    edit = {'op': 'update_entity', 'remove_paths': ['/appearance']}
    if attack in ('geometry', 'identity', 'unknown_field'):
        edit['remove_paths'].append({'geometry': '/attributes/Representation', 'identity': '/id',
                                     'unknown_field': '/made_up'}[attack])
    elif attack == 'whole_entity':
        edit = {'op': 'remove_entity'}
    else:
        edit = {'op': 'update_entity', 'changes': {'/appearance': None if attack == 'null' else {}}}
    provider = RemovalProvider(tmp_path/'round', candidate, {filling['id']: edit})
    result = run_scoped_changeset_round(provider=provider, output_dir=tmp_path/'round', case_id='style-attack',
        round_number=1, user_request='主题默认值。', conversation=[], design_brief=brief,
        expected_facts=expected, candidate=candidate, issues=normalize_gate_sidecars(tmp_path), max_attempts=1)
    assert not result['valid']
    assert result['candidate'] is None
    assert not (tmp_path/'round/revisions').exists()


@pytest.mark.parametrize('version', ['1.0', '1.1'])
def test_field_removal_is_versioned_and_conflicting_writes_are_rejected(version):
    from text2ifc_agent.changesets import validate_changeset
    from tests.agent.test_phase6_5_changeset_contract import _valid_changeset
    value = _valid_changeset()
    value['schema_version'] = 'text2ifc/bim-json-changeset/' + version
    op = value['operations'][0]
    op.pop('changes'); op['remove_paths'] = ['/appearance']
    assert bool(validate_changeset(value)) is (version == '1.0')
    op['changes'] = {'/appearance/color': [0, 0, 0]}
    assert validate_changeset(value)


def test_optional_field_permission_alone_does_not_grant_removal():
    from text2ifc_agent.changeset_apply import apply_changeset
    from tests.agent.test_phase6_5_changeset_apply import _changeset, _revision, _scope
    candidate, brief, expected, filling = fixture(explicit=True)
    value = _changeset(candidate, expected)
    value['schema_version'] = 'text2ifc/bim-json-changeset/1.1'
    op = value['operations'][0]
    op.update(target_id=filling['id'], target_component_hash=_revision(candidate,expected)['component_hashes'][filling['id']],
              remove_paths=['/appearance'])
    op.pop('changes')
    scope = _scope(entity_ids=[filling['id']], paths={filling['id']: ['/appearance']})
    before = copy.deepcopy(candidate)
    result = apply_changeset(candidate=candidate, changeset=value, scope=scope,
                             base_revision=_revision(candidate,expected), expected_facts=expected)
    assert not result['valid']
    assert candidate == before


def test_explicit_type_appearance_is_preserved_while_unrequested_instance_override_is_removed(tmp_path):
    from tests.agent.test_generation_semantic_correction import fixture as type_fixture
    from text2ifc_agent.semantic_requirements import project_semantic_requirements
    data = type_fixture(shared=True)
    candidate, brief, expected, wall, other, type_row, link = data
    link['attributes']['RelatedObjects'] = [wall['id']]
    type_row['materials'], type_row['property_sets'] = [], {}
    appearance = {'color': [.1, .3, .6], 'transparency': 0}
    type_row['appearance'] = appearance
    wall['appearance'] = {'color': [.9, .1, .1]}
    brief['known_facts']['semantic_requirements'] = [
        {'entity_id': wall['id'], 'type_id': type_row['id']},
        {'entity_id': type_row['id'], 'appearance': appearance}]
    expected['semantic_expectations'] = project_semantic_requirements(brief)['expectations']
    for name, value in [('generator/candidate',candidate),('design-brief',brief),('expected-facts',expected)]:
        _write(tmp_path/(name+'.json'), value)
    run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='type-style')
    provider = RemovalProvider(tmp_path/'round', candidate, {wall['id']: {'op':'update_entity', 'remove_paths':['/appearance']}})
    result = run_scoped_changeset_round(provider=provider, output_dir=tmp_path/'round', case_id='type-style',
        round_number=1, user_request='保留指定类型颜色。', conversation=[], design_brief=brief,
        expected_facts=expected, candidate=candidate, issues=normalize_gate_sidecars(tmp_path), max_attempts=1)
    assert result['valid'], result
    assert next(e for e in result['candidate']['entities'] if e['id']==type_row['id']) == type_row
    assert result['preservation']['changed_ids'] == [wall['id']]
