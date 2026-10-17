"""Frozen public-scene compaction family; synthetic public inputs, no Provider."""
from copy import deepcopy
import json

import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.scene_context import PublicScene, SceneError
from tests.ifc_repair.test_scene_context import scene_records
from tests.ifc_repair.test_window_installation_anchor import scene as window_scene


def typed_scene():
    rows = scene_records()
    for row in rows:
        row.update(type_id="shared-type", type_name="Public shared type",
                   type_summary={"id": "shared-type", "name": "Public shared type",
                                 "representation": {"public": "geometry " * 200}})
    rows[0].update(placement_world_mm=[[1., 0., 0., 0.], [0., 1., 0., 0.],
                                      [0., 0., 1., 0.], [0., 0., 0., 1.]],
                   placement_origin_world_mm=[0., 0., 0.],
                   body_bounds_local_mm={"x": [0., 200.], "y": [0., 10000.], "z": [0., 3000.]})
    return PublicScene(rows, [], project_unit_scale=.001)


def test_summary_avoids_body_reads_preserves_cheap_geometry_and_shares_types(monkeypatch):
    scene = typed_scene()
    def forbidden(identity):
        raise AssertionError("summary must not read Body geometry")
    monkeypatch.setattr(scene, "geometry_detail", forbidden)
    page = scene.query({"detail": "summary"})
    wall = next(row for row in page["records"] if row["id"] == "wall")
    assert page["schema_version"] == "text2ifc/ifc-public-scene/0.3"
    assert wall["placement_origin_world_mm"] == [0., 0., 0.]
    assert wall["wall_axis"]["length_mm"] == 10000
    assert "body_bounds_local_mm" not in wall and "type_summary" not in wall
    assert set(page["types"]) == {"shared-type"}
    assert "representation" not in page["types"]["shared-type"]
    assert len(scene.offered_ids) == 5 and "shared-type" not in scene.offered_ids


def test_compact_context_deduplicates_records_types_and_queries_without_truncation():
    scene = typed_scene()
    for _ in range(6):
        scene.query({"detail": "geometry"})
    pages_before = deepcopy(scene.pages)
    compact = scene.prompt_context()
    assert len(scene.pages) == 6 and len(compact["queries"]) == 1
    assert len(compact["records"]) == 5 and len(compact["types"]) == 1
    assert {row["id"] for row in compact["records"]} == scene.offered_ids
    assert compact["queries"][0]["total_matches"] == 5
    assert compact["queries"][0]["complete"] is True
    assert len(json.dumps(compact)) < len(json.dumps(scene.pages)) / 3
    compact["records"][0]["id"] = "tampered"
    compact["types"]["shared-type"]["name"] = "tampered"
    assert scene.pages == pages_before
    assert "tampered" not in json.dumps(scene.prompt_context())


def test_compaction_retains_prior_geometry_after_a_later_summary_and_unknown_coverage():
    scene = typed_scene()
    scene.query({"ids": ["wall"], "detail": "geometry"})
    scene.query({"detail": "summary", "limit": 1})
    compact = scene.prompt_context()
    wall = next(row for row in compact["records"] if row["id"] == "wall")
    assert wall["body_bounds_local_mm"]["y"] == [0., 10000.]
    assert "representation" in compact["types"]["shared-type"]
    assert compact["queries"][-1]["omitted_count"] == 4
    assert scene.complete_records({"ifc_classes": ["IfcWindow"]}) is None
    records = scene_records()
    records[-1].update(bounds_world_mm=None, center_world_mm=None, geometry_status="unavailable")
    missing = PublicScene(records, [], project_unit_scale=1.)
    missing.query({"world_bounds_mm": {"y": [0, 10000]}, "detail": "summary"})
    evidence = missing.prompt_context()["queries"][0]
    assert evidence["geometry_unknown_ids"] == ["window-3"]
    assert evidence["geometry_complete"] is False


def test_legacy_queries_keep_geometry_detail_and_invalid_detail_is_rejected():
    scene = typed_scene()
    assert scene.query({"ids": ["wall"]})["records"][0]["geometry_detail_status"] == "available"
    for bad in ("full", None, 1, []):
        with pytest.raises(SceneError):
            scene.query({"detail": bad})


def build_public_scene(tmp_path, *, with_boundary=True, with_north=True):
    model, wall, opening, window, _, _ = window_scene()
    window.Tag = "W-public-01"
    window.Description = "A public source label"
    context = model.by_type("IfcGeometricRepresentationContext")[0]
    if with_north:
        context.TrueNorth = model.createIfcDirection((1., 0.))
    if with_boundary:
        space = model.createIfcSpace(GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory,
                                     Name="Public office", LongName="Workspace 101", CompositionType="ELEMENT",
                                     InteriorOrExteriorSpace="INTERNAL", ObjectPlacement=wall.ObjectPlacement)
        model.createIfcRelSpaceBoundary(GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory,
                                       RelatingSpace=space, RelatedBuildingElement=wall,
                                       PhysicalOrVirtualBoundary="PHYSICAL", InternalOrExternalBoundary="INTERNAL")
    source = tmp_path / "public.ifc"
    model.write(str(source))
    before = source.read_bytes()
    index = tmp_path / "public.sqlite"
    metadata = build_ifc_index(source, index)
    result = PublicScene.from_ifc(source, index, source_sha256=metadata.source_ifc_sha256)
    return result, source, before, wall.GlobalId, opening.GlobalId, window.GlobalId


@pytest.mark.parametrize("with_boundary,with_north", [(True, True), (False, False)])
def test_real_ifc_extraction_is_source_only_and_orientation_is_explicit(tmp_path, with_boundary, with_north):
    scene, source, before, wall_id, opening_id, window_id = build_public_scene(
        tmp_path, with_boundary=with_boundary, with_north=with_north)
    rows = {r["id"]: r for r in scene.query({"detail": "summary"})["records"]}
    assert rows[window_id]["type_name"] == "Public mapped window"
    assert "W-public-01" in rows[window_id]["labels"]
    assert "A public source label" in rows[window_id]["labels"]
    assert rows[window_id]["placement_origin_world_mm"] == pytest.approx([6000., 1955., 700.])
    assert rows[opening_id]["opening_state"] == "filled"
    assert rows[opening_id]["filling_ids"] == [window_id]
    boundary = [r for r in rows[wall_id]["relationships"] if r["kind"] == "space_boundary"]
    assert bool(boundary) is with_boundary
    coordinates = scene.overview()["coordinates"]
    assert "X east" not in coordinates["frame"]
    assert coordinates["true_north_world"] == ([1., 0., 0.] if with_north else None)
    assert coordinates["true_north_status"] == ("available" if with_north else "unknown")
    assert source.read_bytes() == before


def test_unfilled_opening_is_derived_from_public_hasfillings(tmp_path):
    model, _, opening, window, _, _ = window_scene()
    model.remove(model.by_type("IfcRelFillsElement")[0])
    source = tmp_path / "public.ifc"
    model.write(str(source))
    metadata = build_ifc_index(source, tmp_path / "public.sqlite")
    scene = PublicScene.from_ifc(source, tmp_path / "public.sqlite", source_sha256=metadata.source_ifc_sha256)
    row = scene.query({"ids": [opening.GlobalId], "detail": "summary"})["records"][0]
    assert row["opening_state"] == "unfilled" and row["filling_ids"] == []
    assert window.GlobalId not in scene.offered_ids


def test_selection_offers_only_chosen_rank_and_rechecks_matching_cohort():
    scene = typed_scene()
    cohort = {"ifc_classes": ["IfcWindow"], "host_id": "wall",
              "order_by": "world_y", "descending": True}
    page = scene.query({**cohort, "detail": "summary",
                        "select": {"ranks": [2], "order_by": "world_y", "descending": True}})
    assert [row["id"] for row in page["records"]] == ["window-1"]
    assert scene.offered_ids == {"window-1"}
    assert page["total_matches"] == 4 and page["selection"]["scope"] == "complete_filtered_set"
    assert scene.complete_records(cohort) is None
    assert [row["id"] for row in scene.verified_selection(cohort, [2], ["window-1"])] == ["window-1"]
    assert scene.verified_selection(cohort, [1], ["window-1"]) is None
    assert scene.verified_selection({**cohort, "descending": False}, [2], ["window-1"]) is None
    assert scene.verified_selection(cohort, [2], ["window-0"]) is None
    verified = scene.verify_query_binding(page["query_id"], "window-1")
    assert verified["total_matches"] == 4
    with pytest.raises(SceneError):
        scene.verify_query_binding(page["query_id"], "window-0")


def test_query_binding_rejects_partial_coverage_and_unknown_queries():
    scene = typed_scene()
    page = scene.query({"detail": "summary", "limit": 1})
    with pytest.raises(SceneError):
        scene.verify_query_binding(page["query_id"], "wall")
    with pytest.raises(SceneError):
        scene.verify_query_binding("q-private", "wall")
    complete = scene.query({"ids": ["wall"], "detail": "summary"})
    assert scene.verify_query_binding(complete["query_id"], "wall")["total_matches"] == 1
    again = scene.query({"ids": ["wall"], "detail": "summary"})
    summary = scene.prompt_context()["queries"][-1]
    assert summary["query_ids"] == [complete["query_id"], again["query_id"]]


def test_definite_bounds_rejection_precedes_unrelated_missing_placement():
    scene = typed_scene()
    page = scene.query({"ids": ["window-0"], "detail": "summary",
                        "world_bounds_mm": {"y": [-100, 0]},
                        "predicates": [{"kind": "point", "role": "placement_origin",
                                        "point_mm": [0, 0, 0], "tolerance_mm": 5}]})
    assert page["records"] == [] and page["geometry_unknown_ids"] == []
    assert page["geometry_complete"] is True
    missing = scene.query({"ids": ["window-0"], "detail": "summary",
                           "world_bounds_mm": {"y": [8000, 10000]},
                           "predicates": [{"kind": "point", "role": "placement_origin",
                                           "point_mm": [0, 0, 0], "tolerance_mm": 5}]})
    assert missing["geometry_unknown_ids"] == ["window-0"]


def test_record_list_replacement_rebuilds_metadata_prefilters():
    scene = typed_scene()
    replacement = deepcopy(scene.records)
    replacement[1]["storey_id"] = "changed-public-storey"
    scene.records = replacement
    page = scene.query({"storey_id": "changed-public-storey", "detail": "summary"})
    assert [r["id"] for r in page["records"]] == ["window-0"]
    assert scene.offered_record("window-0")["storey_id"] == "changed-public-storey"


def test_door_window_bounds_disclose_retained_opening_role(tmp_path):
    scene, _, _, _, opening_id, window_id = build_public_scene(tmp_path)
    row = scene.query({"ids": [window_id], "detail": "summary"})["records"][0]
    assert row["bounds_geometry_role"] == "retained_opening"
    assert row["bounds_geometry_source_id"] == opening_id


def test_record_replacement_after_disclosure_cannot_reuse_old_certificates():
    scene = typed_scene()
    page = scene.query({"ids": ["wall"], "detail": "summary"})
    scene.records = deepcopy(scene.records)
    scene.records[0]["bounds_world_mm"]["x"] = [1000, 2000]
    with pytest.raises(SceneError, match="SCENE_RECORDS_REPLACED"):
        scene.verify_query_binding(page["query_id"], "wall")
