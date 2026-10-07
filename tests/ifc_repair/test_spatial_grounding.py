from copy import deepcopy

import pytest

from text2ifc_ifc_repair.spatial_grounding import bind_spatial_intent, GroundingError
from tests.ifc_repair.test_scene_context import fixture_scene, mixed_scene
from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent


def body():
    return fixture_intent("window", {"allowed_ifc_classes": ["IfcWall"]},
                          {"opening": {"width_mm": 900, "height_mm": 1800, "sill_height_mm": 300},
                           "window": {"fit_opening": True}})


def binding(**position):
    return {"operation_id": "offline-repair", "target_id": "wall", "position": position}


def offered_scene(limit=10):
    scene = fixture_scene()
    scene.query({"ids": ["wall"]})
    scene.query({"ifc_classes": ["IfcWindow"], "host_id": "wall", "order_by": "world_y", "descending": True, "limit": limit})
    return scene


def test_ranked_neighbors_derive_wall_offset_not_facade_axis_label():
    scene = offered_scene()
    raw = body()
    bound, evidence = bind_spatial_intent(raw, [binding(kind="between_ranked", ifc_class="IfcWindow",
                            order_by="world_y", descending=True, ranks=[2, 3],
                            reference_ids=["window-1", "window-2"])], scene)
    op = bound["operations"][0]
    assert op["target_query"]["global_id"] == "wall"
    assert op["parameters"]["position"]["center_offset_mm"] == 5000
    assert evidence[0]["derivation"] == "midpoint_of_public_occurrences"
    assert raw == body()  # model document untouched


@pytest.mark.parametrize("scale", [1, .001])
def test_world_point_projection_is_si_normalized_even_for_native_mm(scale):
    scene = offered_scene()
    scene.project_unit_scale = scale
    bound, _ = bind_spatial_intent(body(), [binding(kind="world_point", point_world_mm=[100, 2500, 0])], scene)
    assert bound["operations"][0]["parameters"]["position"]["center_offset_mm"] == 2500


def test_incomplete_ranked_list_cannot_authorize_ordinals():
    with pytest.raises(GroundingError, match="SCENE_ORDER_INCOMPLETE"):
        bind_spatial_intent(body(), [binding(kind="between_ranked", ifc_class="IfcWindow",
                           order_by="world_y", descending=True, ranks=[1, 2],
                           reference_ids=["window-0", "window-1"])], offered_scene(limit=2))


@pytest.mark.parametrize("target", ["private-deleted-id", "unseen-id"])
def test_unoffered_id_is_never_bound(target):
    with pytest.raises(GroundingError, match="SCENE_ID_NOT_OFFERED"):
        bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": target}], offered_scene())


@pytest.mark.parametrize("point", [[100, -20, 0], [900, 2500, 0], [100, 10200, 0]])
def test_world_point_outside_host_is_rejected(point):
    with pytest.raises(GroundingError):
        bind_spatial_intent(body(), [binding(kind="world_point", point_world_mm=point)], offered_scene())


def test_wrong_rank_and_cross_host_reference_fail_closed():
    scene = offered_scene()
    position = binding(kind="between_ranked", ifc_class="IfcWindow", order_by="world_y",
                       descending=True, ranks=[2, 3], reference_ids=["window-0", "window-2"])
    with pytest.raises(GroundingError, match="SCENE_RANK_MISMATCH"):
        bind_spatial_intent(body(), [position], scene)


def test_translated_rotated_wall_projection_and_boundary_opening():
    scene = offered_scene()
    scene._by_id['wall']['wall_axis'].update(start_world_mm=[4000, -1000, 2000], direction_world=[-1,0,0])
    bound, _ = bind_spatial_intent(body(), [binding(kind='world_point', point_world_mm=[1500,-1000,2000])], scene)
    assert bound['operations'][0]['parameters']['position']['center_offset_mm']==2500
    with pytest.raises(GroundingError, match='SCENE_OPENING_OUTSIDE_WALL'):
        bind_spatial_intent(body(), [binding(kind='world_point', point_world_mm=[4000,-1000,2000])], scene)


def test_reference_type_must_belong_to_observed_reference():
    scene = offered_scene()
    scene._by_id['window-1']['type_id']='existing-type'
    raw=body()
    raw['operations'][0]['prototype_intent']={'reference_kind':'global_id', 'reference':'different-type'}
    with pytest.raises(GroundingError, match='SCENE_REFERENCE_TYPE_MISMATCH'):
        bind_spatial_intent(raw, [{**binding(kind='world_point', point_world_mm=[100,5000,0]),
                                  'reference_id':'window-1'}], scene)


def test_coincident_neighbors_are_ambiguous_even_if_order_has_id_tiebreak():
    scene = fixture_scene()
    scene._by_id['window-2']['center_world_mm'][1]=7000
    scene.records=deepcopy(list(scene._by_id.values()))
    scene.query({'ids':['wall']})
    scene.query({'ifc_classes':['IfcWindow'], 'host_id':'wall', 'order_by':'world_y', 'descending':True})
    with pytest.raises(GroundingError, match='SCENE_ORDER_AMBIGUOUS'):
        bind_spatial_intent(body(), [binding(kind='between_ranked', ifc_class='IfcWindow', order_by='world_y',
                            descending=True, ranks=[2,3], reference_ids=['window-2','window-1'])], scene)


def test_ranked_binding_reuses_complete_mixed_query_without_another_tool_call():
    scene = mixed_scene()
    scene.query({'ids': ['wall']})
    scene.query({'ifc_classes': ['IfcWindow', 'IfcOpeningElement'], 'host_id': 'wall',
                 'storey_id': 'level', 'order_by': 'id'})
    before = deepcopy(scene.pages)
    bound, _ = bind_spatial_intent(body(), [binding(kind='between_ranked', ifc_class='IfcWindow',
        order_by='world_y', descending=True, ranks=[2,3], reference_ids=['window-1','window-2'])], scene)
    assert bound['operations'][0]['parameters']['position']['center_offset_mm'] == 5000
    assert scene.pages == before
