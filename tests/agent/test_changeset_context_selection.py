"""T3 context selection cannot enlarge write permissions or lose frozen facts."""
import copy

from tests.agent.test_early_field_recovery import candidate


def select(**kwargs):
    from text2ifc_agent.changeset_context import select_changeset_context
    return select_changeset_context(**kwargs)


def test_field_context_omits_unrelated_examples_and_registry_classes():
    value = candidate()
    original = copy.deepcopy(value)
    context = select(candidate=value, scope={'entity_ids':['style-0'],'relationship_ids':[]},
                     field_recovery=True)
    assert context['few_shot_names'] == ['changeset-single-component.json']
    assert set(context['authoring_contract']['classes']) == {'IfcWindowStyle'}
    assert value == original


def test_shared_type_context_includes_users_from_separate_relationships():
    value = candidate()
    value['entities'].append({'id':'wall-other','ifc_class':'IfcWall','attributes':{}})
    for n, entity_id in enumerate(['wall-1','wall-other']):
        value['relationships'].append({'id':f'type-rel-{n}','ifc_class':'IfcRelDefinesByType',
            'attributes':{'RelatingType':'style-0','RelatedObjects':[entity_id]}})
    scope = {'entity_ids':['wall-1'],'relationship_ids':[]}
    original = copy.deepcopy(scope)
    context = select(candidate=value, scope=scope)
    assert {'style-0','wall-other','type-rel-0','type-rel-1'} <= set(context['read_only_components'])
    assert scope == original


def test_staged_context_uses_exact_package_references_without_granting_writes():
    value = candidate()
    package = {'kind':'storey_local','allowed_reference_ids':['wall-1'],
        'owned_component_ids':['new-wall'], 'owned_component_classes':{'new-wall':'IfcWall'}}
    scope = {'entity_ids':['new-wall'],'relationship_ids':[]}
    context = select(candidate=value, scope=scope, package=package)
    assert 'wall-1' in context['read_only_components']
    assert 'changeset-staged-package-add.json' in context['few_shot_names']
    assert 'changeset-staged-negative-y-stair.json' not in context['few_shot_names']
    assert len(context['few_shot_names']) < 8


def test_cross_storey_context_keeps_stair_coordinate_examples():
    context = select(candidate=candidate(), scope={'entity_ids':[],'relationship_ids':[]},
        package={'kind':'cross_storey','allowed_reference_ids':[], 'owned_component_ids':['flight']})
    assert {'changeset-staged-cross-storey.json','changeset-staged-negative-y-stair.json'} <= set(context['few_shot_names'])
