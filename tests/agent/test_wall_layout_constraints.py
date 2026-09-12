"""Frozen development family: open layouts retain selected geometric checks."""
import copy

import pytest

from tests.agent.test_brief_plan_constraints import fixture, LAYOUTS
from text2ifc_agent.design_brief import validate_design_brief, design_brief_template_id
from text2ifc_agent.brief_plan_repair import plan_repair_eligible, repair_plan_brief


def layout_fixture(shape='rectangle', transform=0):
    case, brief = fixture(shape, transform)
    brief['schema_version'] = 'text2ifc/design-brief/2.7'
    walls = brief['known_facts']['storeys'][0]['walls']['exterior']
    walls.pop(0)  # Explicitly omitted edge: no closure demand.
    constraint = brief['known_facts']['plan_constraints'][0]
    constraint.update(kind='wall_layout', checks=['inside_outline', 'non_overlapping'],
                      derived_wall_ids=[w['id'] for w in walls])
    constraint.pop('thickness_mm')
    return case, brief


@pytest.mark.parametrize('shape', LAYOUTS)
@pytest.mark.parametrize('transform', [0, 1, 2])
def test_open_layout_is_valid_without_dropping_containment_or_overlap_checks(shape, transform):
    case, brief = layout_fixture(shape, transform)
    before = copy.deepcopy(brief)
    assert not validate_design_brief(brief, conversation=case['conversation'])
    assert brief == before


@pytest.mark.parametrize('failure', ['outside', 'overlap'])
def test_open_layout_still_blocks_real_geometry_defects(failure):
    case, brief = layout_fixture()
    walls = brief['known_facts']['storeys'][0]['walls']['exterior']
    if failure == 'outside':
        walls[0]['bounds']['x'] = [7900, 8100]
    else:
        walls[0]['bounds']['y'][1] = 6000
    issues = validate_design_brief(brief, conversation=case['conversation'])
    assert any(i.code == 'BRIEF_PLAN_GEOMETRY' and failure in i.message for i in issues), issues


def test_only_requested_check_applies_even_for_overlap_outside_outline():
    case, brief = layout_fixture()
    walls = brief['known_facts']['storeys'][0]['walls']['exterior']
    walls[:] = [dict(id='a', bounds=dict(x=[9000, 9200], y=[0, 1000])),
                dict(id='b', bounds=dict(x=[9100, 9300], y=[0, 1000]))]
    c = brief['known_facts']['plan_constraints'][0]
    c.update(checks=['non_overlapping'], derived_wall_ids=[])
    issues = validate_design_brief(brief, conversation=case['conversation'])
    assert len(issues) == 1 and 'overlap' in issues[0].message, issues
    walls[1]['bounds']['x'] = [9200, 9400]
    assert not validate_design_brief(brief, conversation=case['conversation'])


@pytest.mark.parametrize('version', ['2.4', '2.5', '2.6', '2.7'])
def test_full_envelope_retains_missing_wall_failure(version):
    case, brief = fixture()
    brief['schema_version'] = 'text2ifc/design-brief/' + version
    brief['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['x'][0] = 100
    issues = validate_design_brief(brief, conversation=case['conversation'])
    assert any(i.code == 'BRIEF_PLAN_GEOMETRY' and 'gap' in i.message for i in issues), issues


@pytest.mark.parametrize('attack', ['old_version', 'unknown_check', 'empty_checks', 'bad_source'])
def test_new_checks_do_not_weaken_version_or_source_contract(attack):
    case, brief = layout_fixture()
    c = brief['known_facts']['plan_constraints'][0]
    if attack == 'old_version': brief['schema_version'] = 'text2ifc/design-brief/2.6'
    elif attack == 'unknown_check': c['checks'] = ['skip_geometry']
    elif attack == 'empty_checks': c['checks'] = []
    else: c['source_turns'] = ['invented-turn']
    assert validate_design_brief(brief, conversation=case['conversation'])


@pytest.mark.parametrize('attack', ['none', 'remove_check', 'move_fixed'])
def test_selected_layout_repair_is_atomic_and_cannot_remove_authority(tmp_path, attack):
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, good = layout_fixture()
    good['known_facts']['storeys'][0]['walls']['interior'] = [
        dict(id='fixed', bounds=dict(x=[3000, 3200], y=[1000, 2000]))]
    bad = copy.deepcopy(good)
    bad['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['x'] = [7900, 8100]
    response = copy.deepcopy(good)
    if attack == 'remove_check': response['known_facts']['plan_constraints'][0]['checks'] = ['non_overlapping']
    elif attack == 'move_fixed': response['known_facts']['storeys'][0]['walls']['interior'][0]['bounds']['x'] = [4000, 4200]
    before = copy.deepcopy(bad)
    issues = validate_design_brief(bad, conversation=case['conversation'])
    assert plan_repair_eligible(bad, issues)
    result = repair_plan_brief(provider=SequenceProvider([response]), output_dir=tmp_path/'repair',
        brief=bad, case=case, evidence_catalog=[], session_id='offline-layout')
    assert result['valid'] == (attack == 'none'), result
    assert bad == before


def test_prompt_and_generation_contract_selection_are_explicit():
    from text2ifc_agent.semantic_requirements import generation_schema_version
    assert design_brief_template_id('text2ifc/design-brief/2.7', design_review_enabled=False) == 'design-brief.v2.22'
    assert design_brief_template_id('text2ifc/design-brief/2.7', design_review_enabled=True) == 'design-brief.v2.23'
    assert generation_schema_version({'schema_version': 'text2ifc/design-brief/2.7'}) == 'bim-json/2.3'
