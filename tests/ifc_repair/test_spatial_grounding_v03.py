"""Point roles and public-query authority at the intent binding seam."""
from copy import deepcopy

import pytest

from text2ifc_ifc_repair.scene_context import PublicScene
from text2ifc_ifc_repair.spatial_grounding import bind_spatial_intent, GroundingError
from tests.ifc_repair.test_scene_context import fixture_scene
from tests.ifc_repair.test_spatial_grounding import body


def positioned_scene():
    scene = fixture_scene()
    scene._by_id["wall"]["placement_origin_world_mm"] = [500, -100, 0]
    scene._by_id["wall"]["placement_world_mm"] = [
        [1, 0, 0, 500], [0, 1, 0, -100], [0, 0, 1, 0], [0, 0, 0, 1]]
    scene.query({"ids": ["wall"]})
    return scene


def test_placement_origin_is_not_required_to_be_inside_the_body():
    scene = positioned_scene()
    bound, evidence = bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": "wall",
        "target_locator": {"point_mm": [500, -100, 0], "role": "placement_origin", "tolerance_mm": 1},
        "position": {"kind": "world_point", "point_world_mm": [100, 5000, 0]}}], scene)
    assert bound["operations"][0]["target_query"]["global_id"] == "wall"
    assert evidence[0]["target_locator"]["role"] == "placement_origin"


@pytest.mark.parametrize("role,point", [("center", [500, -100, 0]), ("placement_origin", [100, 5000, 1500])])
def test_wrong_coordinate_role_cannot_bind_the_target(role, point):
    with pytest.raises(GroundingError, match="SCENE_LOCATOR"):
        bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": "wall",
            "target_locator": {"point_mm": point, "role": role, "tolerance_mm": 1}}], positioned_scene())


def test_query_binding_cannot_reuse_a_different_querys_identity():
    scene = positioned_scene()
    second = scene.query({"ids": ["window-0"]})
    with pytest.raises(GroundingError):
        bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": "wall",
            "target_query_id": second["query_id"]}], scene)


def test_binding_retains_query_provenance():
    scene = positioned_scene()
    query = scene.query({"ids": ["wall"]})
    _, evidence = bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": "wall",
        "target_query_id": query["query_id"]}], scene)
    assert evidence[0]["target_query_id"] == query["query_id"]


def test_unknown_geometry_cannot_establish_unique_point_binding():
    first = positioned_scene().records[0]
    other = deepcopy(first)
    other.update(id="unmeasurable-wall", placement_origin_world_mm=None, placement_world_mm=None)
    scene = PublicScene([first, other], [], project_unit_scale=.001)
    scene.query({"ids": ["wall"]})
    with pytest.raises(GroundingError, match="SCENE_LOCATOR_GEOMETRY_INCOMPLETE"):
        bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": "wall",
            "target_locator": {"point_mm": [500, -100, 0], "role": "placement_origin", "tolerance_mm": 1}}], scene)


def test_verified_floor_scope_excludes_irrelevant_unmeasurable_wall():
    first = positioned_scene().records[0]
    other = deepcopy(first)
    other.update(id="other-floor-wall", storey_id="other-floor", placement_world_mm=None)
    scene = PublicScene([first, other], [], project_unit_scale=.001)
    query = scene.query({"ifc_classes": ["IfcWall"], "storey_id": "level", "detail": "summary"})
    _, evidence = bind_spatial_intent(body(), [{"operation_id": "offline-repair", "target_id": "wall",
        "target_query_id": query["query_id"],
        "target_locator": {"point_mm": [500, -100, 0], "role": "placement_origin", "tolerance_mm": 1}}], scene)
    assert evidence[0]["target_query_id"] == query["query_id"]


@pytest.mark.parametrize('compressed', [False, True])
@pytest.mark.parametrize('gap,valid', [(0.0005, False), (0.001, True)])
def test_rank_tolerance_same_for_full_and_compressed_evidence(compressed, gap, valid):
    scene = fixture_scene()
    scene._by_id['window-1']['center_world_mm'][1] = 0.0
    scene._by_id['window-2']['center_world_mm'][1] = -gap
    scene._by_id['window-3']['center_world_mm'][1] = -100
    scene.query({'ids': ['wall']})
    q = {'ifc_classes': ['IfcWindow'], 'host_id': 'wall', 'detail': 'summary'}
    order = {'order_by': 'world_y', 'descending': True}
    if not valid and compressed:
        from text2ifc_ifc_repair.scene_context import SceneError
        with pytest.raises(SceneError, match='SCENE_SELECTION_AMBIGUOUS'):
            scene.query({**q, 'select': {**order, 'ranks': [2, 3]}})
        return
    scene.query({**q, **({'select': {**order, 'ranks': [2, 3]}} if compressed else order)})
    # Midpoint is outside this wall; check ordinal evidence before projection.
    from text2ifc_ifc_repair.spatial_grounding import _ranked_midpoint
    position = {'ifc_class': 'IfcWindow', **order, 'ranks': [2, 3],
                'reference_ids': ['window-1', 'window-2']}
    if not valid:
        with pytest.raises(GroundingError, match='SCENE_ORDER_AMBIGUOUS'):
            _ranked_midpoint(scene.offered_record('wall'), position, scene)
    else:
        assert _ranked_midpoint(scene.offered_record('wall'), position, scene)[1] == position['reference_ids']
