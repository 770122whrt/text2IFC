"""Visible stair colour must target actual flight bodies, not the assembly."""
import copy
import pytest
from tests.agent.test_semantic_authority_completeness import valid_brief, review
from text2ifc_agent.semantic_requirements import project_semantic_requirements
from text2ifc_agent.brief_semantic_roles import recoverable_value_loss


def stair_brief(identity='access', flights=None):
    case, brief = valid_brief()
    brief['schema_version'] = 'text2ifc/design-brief/2.7'
    stair = {'id': identity}
    if flights: stair['flight_ids'] = flights
    brief['known_facts'] = {'stairs': [stair], 'semantic_review': review(appearance=True),
        'plan_constraints': [], 'semantic_requirements': [
            {'entity_id': identity, 'appearance': {'color': [.3, .4, .5]}, 'scope': 'direct'}]}
    return case, brief


@pytest.mark.parametrize('identity,flights', [('access', None), ('stair-east', ['rise-a', 'rise-b'])])
def test_assembly_style_is_rejected_and_actual_flight_targets_are_legal(identity, flights):
    from text2ifc_agent.cross_storey_identity import stair_flight_ids
    _, brief = stair_brief(identity, flights)
    before = copy.deepcopy(brief)
    bad = project_semantic_requirements(brief)
    assert 'SEMANTIC_APPEARANCE_TARGET_ROLE' in {x['code'] for x in bad['issues']}
    assert brief == before
    targets = stair_flight_ids(brief['known_facts']['stairs'][0], identity)
    fixed = copy.deepcopy(brief)
    fixed['known_facts']['semantic_requirements'] = [
        {**before['known_facts']['semantic_requirements'][0], 'entity_id': target} for target in targets]
    assert project_semantic_requirements(fixed)['valid']
    assert not recoverable_value_loss(before, fixed)


@pytest.mark.parametrize('attack', ['missing', 'other_target', 'changed_colour'])
def test_correcting_assembly_target_cannot_erase_or_redirect_colour(attack):
    _, before = stair_brief('access', ['first', 'second'])
    after = copy.deepcopy(before)
    rows = [{**before['known_facts']['semantic_requirements'][0], 'entity_id': t} for t in ['first', 'second']]
    if attack == 'missing': rows.pop()
    if attack == 'other_target': rows[0]['entity_id'] = 'unrelated'
    if attack == 'changed_colour': rows[0]['appearance'] = {'color': [0, 0, 0]}
    after['known_facts']['semantic_requirements'] = rows
    assert recoverable_value_loss(before, after)


def test_legacy_contract_keeps_prior_target_rules():
    _, brief = stair_brief()
    brief['schema_version'] = 'text2ifc/design-brief/2.6'
    assert project_semantic_requirements(brief)['valid']


def test_public_semantic_repair_retargets_only_appearance(tmp_path):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, before = stair_brief()
    after = copy.deepcopy(before)
    after['known_facts']['semantic_requirements'][0]['entity_id'] = 'access-flight'
    result = repair_semantic_brief(provider=SequenceProvider([after]), output_dir=tmp_path/'repair',
        brief=before, case=case, evidence_catalog=[], session_id='stair-target')
    assert result['valid'], result
