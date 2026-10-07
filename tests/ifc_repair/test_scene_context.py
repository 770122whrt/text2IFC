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
