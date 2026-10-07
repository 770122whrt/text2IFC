"""Public-scene failure family; no private benchmark data or model calls."""
from copy import deepcopy

import pytest

from text2ifc_ifc_repair.scene_context import PublicScene, SceneError


def scene_records():
    wall = {"id": "wall", "ifc_class": "IfcWall", "storey_id": "level", "host_id": None,
            "bounds_world_mm": {"x": [0, 200], "y": [0, 10000], "z": [0, 3000]},
            "center_world_mm": [100, 5000, 1500], "geometry_status": "available",
            "wall_axis": {"start_world_mm": [100, 0, 0], "direction_world": [0, 1, 0],
                          "length_mm": 10000, "thickness_mm": 200}}
    records = [wall]
    for i, y in enumerate([9000, 7000, 3000, 1000]):
        records.append({"id": f"window-{i}", "ifc_class": "IfcWindow", "storey_id": "level",
                        "host_id": "wall", "geometry_status": "available", "center_world_mm": [100, y, 1500],
                        "bounds_world_mm": {"x": [0, 200], "y": [y-450, y+450], "z": [300, 2700]}})
    return records


def fixture_scene():
    return PublicScene(scene_records(), [{"id": "level", "name": "Ground East", "elevation_mm": 0}],
                       project_unit_scale=0.001)


def test_query_orders_complete_host_set_and_reports_truncation():
    scene = fixture_scene()
    q = {"ifc_classes": ["IfcWindow"], "host_id": "wall", "order_by": "world_y", "descending": True, "limit": 2}
    first = scene.query(q)
    assert [r["id"] for r in first["records"]] == ["window-0", "window-1"]
    assert first["total_matches"] == 4 and first["omitted_count"] == 2 and not first["complete"]
    second = scene.query({**q, "offset": 2})
    assert second["complete"] is False  # a page is not the entire matching set
    assert second["next_offset"] is None
    assert scene.complete_records(q) is not None  # both pages served


def test_query_is_read_only_and_world_filter_uses_mm_not_native_units():
    scene = fixture_scene()
    before = deepcopy(scene.records)
    page = scene.query({"ifc_classes": ["IfcWindow"], "world_bounds_mm": {"y": [6900, 7100]}})
    assert [r["id"] for r in page["records"]] == ["window-1"]
    page["records"][0]["id"] = "changed"
    assert scene.records == before
    assert scene.overview()["coordinates"]["length_unit"] == "mm"
    assert scene.overview()["storeys"][0]["name"] == "Ground East"


def test_unknown_geometry_is_disclosed_not_silently_excluded():
    records = scene_records()
    records[-1].update(geometry_status="unavailable", bounds_world_mm=None, center_world_mm=None)
    scene = PublicScene(records, [], project_unit_scale=1)
    page = scene.query({"ifc_classes": ["IfcWindow"], "world_bounds_mm": {"y": [0, 8000]}})
    assert page["geometry_unknown_ids"] == ["window-3"]
    assert not page["geometry_complete"]


@pytest.mark.parametrize("query", [{"path": "../private/G.ifc"}, {"limit": 100000},
                                   {"offset": -1}, {"order_by": "name"},
                                   {"world_bounds_mm": {"x": [2, 1]}}])
def test_query_rejects_unbounded_or_non_scene_access(query):
    with pytest.raises(SceneError):
        fixture_scene().query(query)


def mixed_scene(*, unknown_extra=False):
    records = scene_records()
    extra = {**deepcopy(records[1]), 'id': 'opening-extra', 'ifc_class': 'IfcOpeningElement'}
    if unknown_extra:
        extra.update(geometry_status='unavailable', bounds_world_mm=None, center_world_mm=None)
    return PublicScene(records + [extra], [], project_unit_scale=0.001)


def ranked_query():
    return {'ifc_classes': ['IfcWindow'], 'host_id': 'wall', 'order_by': 'world_y', 'descending': True}


@pytest.mark.parametrize('extra_filter', [{}, {'storey_id': 'level'},
    {'world_bounds_mm': {'z': [0, 3000]}}])
def test_complete_target_set_can_be_reused_from_mixed_query(extra_filter):
    scene = mixed_scene()
    page = scene.query({'ifc_classes': ['IfcOpeningElement', 'IfcWindow'], 'host_id': 'wall',
                        'order_by': 'id', **extra_filter})
    assert page['complete']
    before = deepcopy(scene.pages)
    result = scene.complete_records(ranked_query())
    assert result is not None
    assert [r['id'] for r in result] == [f'window-{i}' for i in range(4)]
    result[0]['center_world_mm'][1] = -1
    assert scene.pages == before and scene.records[1]['center_world_mm'][1] == 9000


def test_differently_filtered_pages_can_cover_the_same_target_set():
    scene = mixed_scene()
    scene.query({'ids': ['window-0', 'window-2']})
    assert scene.complete_records(ranked_query()) is None
    scene.query({'ifc_classes': ['IfcWindow', 'IfcOpeningElement'],
                 'world_bounds_mm': {'y': [0, 7100]}})
    assert [r['id'] for r in scene.complete_records(ranked_query())] == [f'window-{i}' for i in range(4)]


def test_mixed_pagination_requires_all_targets_not_query_signature():
    scene = mixed_scene()
    query = {'ifc_classes': ['IfcWindow', 'IfcOpeningElement'], 'host_id': 'wall', 'limit': 2}
    scene.query(query)
    assert scene.complete_records(ranked_query()) is None
    scene.query({**query, 'offset': 2})
    assert scene.complete_records(ranked_query()) is None
    scene.query({**query, 'offset': 4})
    assert len(scene.complete_records(ranked_query())) == 4


def test_complete_narrow_page_cannot_hide_an_unoffered_target():
    records = scene_records()
    records[-1]['storey_id'] = 'other-level'
    scene = PublicScene(records, [], project_unit_scale=1)
    assert scene.query({'ifc_classes': ['IfcWindow'], 'host_id': 'wall', 'storey_id': 'level'})['complete']
    assert scene.complete_records(ranked_query()) is None


def test_repeated_pages_cannot_count_missing_targets_twice():
    scene = mixed_scene()
    query = {'ifc_classes': ['IfcWindow', 'IfcOpeningElement'], 'host_id': 'wall', 'limit': 2}
    scene.query(query)
    scene.query(query)
    assert scene.complete_records(ranked_query()) is None


def test_irrelevant_geometry_gap_does_not_invalidate_known_target_set():
    scene = mixed_scene(unknown_extra=True)
    page = scene.query({'ifc_classes': ['IfcWindow', 'IfcOpeningElement'],
                        'host_id': 'wall', 'order_by': 'world_y'})
    assert not page['geometry_complete']
    assert len(scene.complete_records(ranked_query())) == 4


def test_relevant_geometry_gap_still_blocks_ordinal_evidence():
    records = scene_records()
    records[-1].update(geometry_status='unavailable', bounds_world_mm=None, center_world_mm=None)
    scene = PublicScene(records, [], project_unit_scale=1)
    scene.query({'ifc_classes': ['IfcWindow'], 'host_id': 'wall'})
    assert scene.complete_records(ranked_query()) is None


def test_partial_broad_query_is_sufficient_only_if_target_subset_is_complete():
    scene = mixed_scene()
    page = scene.query({'ifc_classes': ['IfcWindow', 'IfcOpeningElement'],
                        'host_id': 'wall', 'order_by': 'world_y', 'descending': True, 'limit': 4})
    assert not page['complete'] and scene.complete_records(ranked_query()) is None
    scene.query({'ids': ['window-3']})
    assert len(scene.complete_records(ranked_query())) == 4


def test_coverage_is_checked_against_selected_host_not_all_same_class_objects():
    records = scene_records()
    records.append({**deepcopy(records[1]), 'id': 'other-host-window', 'host_id': 'other-wall'})
    scene = PublicScene(records, [], project_unit_scale=1)
    scene.query({'ifc_classes': ['IfcWindow', 'IfcOpeningElement'], 'host_id': 'wall'})
    assert len(scene.complete_records(ranked_query())) == 4
    assert scene.complete_records({'ifc_classes': ['IfcWindow']}) is None
