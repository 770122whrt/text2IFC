"""Published storeys are authority; unpublished products and identities are not."""
from copy import deepcopy

import pytest

from text2ifc_ifc_repair.scene_context import PublicScene, SceneError
from text2ifc_ifc_repair.spatial_grounding import GroundingError, bind_spatial_intent
from tests.ifc_repair.test_scene_context import fixture_scene


def operation(family='beam',storey='level'):
    return {'operations':[{'operation_id':'add','operation_type':'add_'+family,
        'target_query':{'schema_version':'text2ifc/ifc-target-query/0.1',
                        'allowed_ifc_classes':['IfcBuildingStorey'],'global_id':storey},
        'parameters':{},'prototype_intent':None}]}


@pytest.mark.parametrize('family',['beam','column'])
def test_published_storey_can_bind_without_a_redundant_product_query(family):
    scene=fixture_scene();scene.overview()
    result,evidence=bind_spatial_intent(operation(family),[{'operation_id':'add','target_id':'level'}],scene)
    assert result['operations'][0]['target_query']['global_id']=='level'
    assert evidence[0]['source_role']=='current_public_ifc'
    assert scene.pages==[]


def test_storey_authority_begins_only_when_overview_is_offered():
    scene=fixture_scene()
    with pytest.raises(SceneError,match='ID_NOT_OFFERED'):scene.offered_record('level')
    before=deepcopy(scene.records);summary=scene.overview()
    assert summary['storeys'][0]['id']=='level'
    assert scene.offered_record('level')['ifc_class']=='IfcBuildingStorey'
    assert scene.records==before


@pytest.mark.parametrize('identity',['wall','deleted-storey','other-scene-storey'])
def test_overview_does_not_offer_unqueried_products_or_missing_ids(identity):
    scene=fixture_scene();scene.overview()
    with pytest.raises(SceneError,match='ID_NOT_OFFERED'):scene.offered_record(identity)


def test_known_storey_cannot_be_bound_as_wall_or_given_invented_geometry():
    scene=fixture_scene();scene.overview();body=operation()
    body['operations'][0]['target_query']['allowed_ifc_classes']=['IfcWall']
    with pytest.raises(GroundingError,match='TARGET_CLASS_MISMATCH'):
        bind_spatial_intent(body,[{'operation_id':'add','target_id':'level'}],scene)
    with pytest.raises(GroundingError,match='GEOMETRY_UNAVAILABLE'):
        bind_spatial_intent(operation(),[{'operation_id':'add','target_id':'level',
                                        'target_point_world_mm':[0,0,0]}],scene)


def test_duplicate_storeys_and_product_storey_id_collision_fail_closed():
    scene=fixture_scene()
    with pytest.raises(SceneError,match='IDENTITY_AMBIGUOUS'):
        PublicScene(scene.records,scene.storeys*2,project_unit_scale=.001)
    with pytest.raises(SceneError,match='IDENTITY_AMBIGUOUS'):
        PublicScene(scene.records,[{**scene.storeys[0],'id':'wall'}],project_unit_scale=.001)


def test_independent_scene_storey_and_empty_overview_boundary():
    scene=PublicScene([], [{'id':'upper','name':'Level two','elevation_mm':3500}],project_unit_scale=1)
    scene.overview();bound,_=bind_spatial_intent(operation('column','upper'),
        [{'operation_id':'add','target_id':'upper'}],scene)
    assert bound['operations'][0]['target_query']['global_id']=='upper'
    empty=PublicScene([],[],project_unit_scale=1);empty.overview()
    with pytest.raises(SceneError,match='ID_NOT_OFFERED'):empty.offered_record('upper')
