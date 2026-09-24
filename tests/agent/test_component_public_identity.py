"""Public catalog identity family: no prefix guessing or ambiguous union."""
import copy

import pytest

from tests.agent.test_component_requirements_v26 import component_brief
from text2ifc_agent.component_requirements import public_component_coverage
from text2ifc_agent.brief_semantic_repair import semantic_repair_eligible
from text2ifc_agent.design_brief import design_brief_template_id
from text2ifc_agent.prompt_registry import load_prompt_registry, PROJECT_ROOT


def catalog_brief(cls, label):
    brief = component_brief()
    collection = 'doors' if cls == 'IfcDoor' else 'windows'
    brief['known_facts'].pop('doors')
    brief['known_facts'][collection] = [{'id': 'generated-identity', 'ifc_class': cls}]
    brief['known_facts']['semantic_requirements'][0]['entity_id'] = 'generated-identity'
    brief['original_request'] = f'#### {label} 部件几何\n- frame：角色=frame；实体=frame-solid。\n'
    return brief, brief['known_facts'][collection]


@pytest.mark.parametrize('cls,label', [('IfcDoor','ENTRY-A'), ('IfcWindow','UPPER-07')])
def test_missing_public_identity_is_not_reported_as_missing_parts_or_semantically_retried(cls,label):
    brief, records = catalog_brief(cls,label)
    before = copy.deepcopy(brief)
    issues = public_component_coverage(brief)
    assert [i['code'] for i in issues] == ['PUBLIC_COMPONENT_IDENTITY_MISSING']
    assert not semantic_repair_eligible(brief, issues)
    assert brief == before


@pytest.mark.parametrize('key', ['id','label','name'])
@pytest.mark.parametrize('cls,label', [('IfcDoor','ENTRY-A'), ('IfcWindow','UPPER-07')])
def test_explicit_public_identity_maps_without_geometry_or_id_rewriting(key,cls,label):
    brief, records = catalog_brief(cls,label)
    records[0][key] = label
    if key == 'id':
        brief['known_facts']['semantic_requirements'][0]['entity_id'] = label
    before = copy.deepcopy(brief)
    assert public_component_coverage(brief) == []
    assert brief == before


def test_two_products_with_same_public_label_cannot_pool_parts():
    brief, records = catalog_brief('IfcDoor','ENTRY-A')
    records[0]['label'] = 'ENTRY-A'
    records.append({'id':'other-door','ifc_class':'IfcDoor','label':'ENTRY-A'})
    issues = public_component_coverage(brief)
    assert [i['code'] for i in issues] == ['PUBLIC_COMPONENT_IDENTITY_AMBIGUOUS']
    assert not semantic_repair_eligible(brief, issues)


@pytest.mark.parametrize('review,new,old', [(False,'2.30','2.28'), (True,'2.31','2.29')])
def test_new_brief_prompts_require_public_catalog_identity_and_keep_old_versions(review,new,old):
    assert design_brief_template_id('text2ifc/design-brief/2.9', design_review_enabled=review) == 'design-brief.v'+new
    registry = load_prompt_registry()
    text = (PROJECT_ROOT/registry['design-brief.v'+new]['path']).read_text(encoding='utf-8')
    previous = (PROJECT_ROOT/registry['design-brief.v'+old]['path']).read_text(encoding='utf-8')
    assert text.startswith(previous)
    assert 'Public component catalog identity' in text
    assert 'label' in text and 'semantic_requirements[].entity_id' in text
