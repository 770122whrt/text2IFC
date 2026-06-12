from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell.util.element
import ifcopenshell.util.placement
import pytest

from text2ifc_compiler import compile_document, open_ifc
from text2ifc_contract.placement import world_transform_for


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _by_bim_id(model, bim_json_id: str):
    for entity in model.by_type("IfcProduct"):
        psets = ifcopenshell.util.element.get_psets(entity)
        if psets.get("Pset_text2IFCIdentity", {}).get("BimJsonId") == bim_json_id:
            return entity
    raise KeyError(bim_json_id)


def _solid(entity):
    return next(
        item
        for representation in entity.Representation.Representations
        for item in representation.Items
        if item.is_a("IfcExtrudedAreaSolid")
    )


def test_v2_round_trips_parent_relative_world_placement(tmp_path: Path) -> None:
    value = document()
    output = tmp_path / "placement-v2.ifc"
    assert compile_document(value, output).success
    model = open_ifc(output)
    opening = _by_bim_id(model, "opening-1")

    expected = world_transform_for(value, "opening-1")
    actual = ifcopenshell.util.placement.get_local_placement(
        opening.ObjectPlacement
    )
    assert actual[:3, 3] == pytest.approx(
        [row[3] for row in expected[:3]], abs=1.0
    )


def test_v2_round_trips_rectangle_polygon_and_solid_position(
    tmp_path: Path,
) -> None:
    value = document()
    wall_json = next(item for item in value["entities"] if item["id"] == "wall-1")
    wall_json["attributes"]["Representation"]["position"] = {
        "origin": [125.0, 250.0, 375.0],
        "axis": [0.0, 1.0, 0.0],
        "ref_direction": [1.0, 0.0, 0.0],
    }
    output = tmp_path / "geometry-v2.ifc"
    assert compile_document(value, output).success
    model = open_ifc(output)

    wall_solid = _solid(_by_bim_id(model, "wall-1"))
    wall_rep = wall_json["attributes"]["Representation"]
    assert wall_solid.SweptArea.is_a() == "IfcRectangleProfileDef"
    assert wall_solid.SweptArea.XDim == pytest.approx(wall_rep["profile"]["x"])
    assert wall_solid.SweptArea.YDim == pytest.approx(wall_rep["profile"]["y"])
    assert wall_solid.Depth == pytest.approx(wall_rep["depth"])
    assert list(wall_solid.Position.Location.Coordinates) == pytest.approx(
        [125.0, 250.0, 375.0]
    )

    slab_solid = _solid(_by_bim_id(model, "slab-1"))
    assert slab_solid.SweptArea.is_a() == "IfcArbitraryClosedProfileDef"
    source_points = next(
        item for item in value["entities"] if item["id"] == "slab-1"
    )["attributes"]["Representation"]["profile"]["points"]
    actual_points = [
        list(point.Coordinates) for point in slab_solid.SweptArea.OuterCurve.Points
    ]
    assert actual_points == pytest.approx(source_points)
