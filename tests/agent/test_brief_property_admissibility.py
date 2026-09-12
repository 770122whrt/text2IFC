"""Properties must be executable before they become frozen Generator authority."""
import copy
import pytest
from tests.agent.test_semantic_authority_completeness import valid_brief, review
from text2ifc_agent.semantic_requirements import project_semantic_requirements


def property_brief(cls='IfcSpace', pset='Pset_SpaceCommon', prop='IsExternal', value=True):
    case, b = valid_brief()
    b['schema_version'] = 'text2ifc/design-brief/2.7'
    b['known_facts'] = {'spaces': [{'id': 'target', 'ifc_class': cls, 'external': True}],
        'semantic_requirements': [{'entity_id': 'target', 'property_sets': {pset: {prop: value}}}],
        'semantic_review': review(property=True), 'plan_constraints': []}
    return case, b


@pytest.mark.parametrize('cls,pset,prop,value,valid', [
    ('IfcSpace', 'Pset_SpaceCommon', 'IsExternal', True, False),
    ('IfcWall', 'Pset_WallCommon', 'IsExternal', True, True),
    ('IfcWallType', 'Pset_WallCommon', 'IsExternal', False, True),
    ('IfcWall', 'Pset_WallCommon', 'IsExternal', 'true', False),
    ('IfcColumn', 'Pset_DoorCommon', 'FireRating', '60min', False),
    ('IfcWall', 'Pset_WallCommon', 'InventedRating', 'A', False),
    ('IfcWall', 'Pset_InventedCommon', 'Flag', True, False),
    ('IfcWall', 'custom:OwnerFacts', 'ReviewNote', 'requested', True),
])
def test_standard_identity_applicability_and_type_before_freezing(cls, pset, prop, value, valid):
    _, b = property_brief(cls, pset, prop, value)
    before = copy.deepcopy(b)
    result = project_semantic_requirements(b)
    assert result['valid'] == valid, result
    if not valid:
        assert any(i['code'] == 'SEMANTIC_PROPERTY_NOT_ADMISSIBLE' for i in result['issues'])
        assert not [e for e in result['expectations'] if e['kind'] == 'property']
    assert b == before


def test_public_brief_repairs_wrong_property_attachment_without_changing_space(tmp_path):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, bad = property_brief()
    bad['provenance'].update(selected_evidence_ids=[], few_shot_ids=[])
    bad['original_request'] = '这个空间按室外表达，不要求添加任何Pset。'
    case.update(user_request=bad['original_request'], conversation=[
        {'turn_id': 'turn-user-001', 'role': 'user', 'content': bad['original_request']}])
    good = copy.deepcopy(bad)
    good['known_facts']['semantic_requirements'] = []
    good['known_facts']['semantic_review'] = review()
    provider = SequenceProvider([bad, good])
    result = run_design_brief_stage(provider=provider, output_dir=tmp_path/'brief', case=case,
        design_brief_schema_version=bad['schema_version'])
    assert result['valid'], result
    assert len(provider.calls) == 2
    assert provider.calls[1]['state']['stage'] == 'design-brief-semantic-repair'
    import json
    final = json.loads((tmp_path/'brief/design-brief.json').read_text(encoding='utf-8'))
    assert final['known_facts']['spaces'] == bad['known_facts']['spaces']
    assert json.loads((tmp_path/'brief/parsed-output.json').read_text(encoding='utf-8')) == bad


@pytest.mark.parametrize('erase_valid', [False, True])
def test_semantic_correction_preserves_other_admissible_property_values(tmp_path, erase_valid):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, bad = property_brief()
    bad['known_facts']['semantic_requirements'][0]['property_sets']['custom:OwnerFacts'] = {'ReviewNote': 'retain this'}
    good = copy.deepcopy(bad)
    props = good['known_facts']['semantic_requirements'][0]['property_sets']
    props.pop('Pset_SpaceCommon')
    if erase_valid:
        good['known_facts']['semantic_requirements'] = []
        good['known_facts']['semantic_review'] = review()
    result = repair_semantic_brief(provider=SequenceProvider([good]), output_dir=tmp_path/'correction',
        brief=bad, case=case, evidence_catalog=[], session_id='offline-property')
    assert result['valid'] == (not erase_valid), result
