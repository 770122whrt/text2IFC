from __future__ import annotations

from pathlib import Path

import ifcopenshell.geom
import ifcopenshell.util.element
import pytest

from text2ifc_compiler import compile_document, containment_map, open_ifc


def _spatial_entity(
    entity_id: str,
    ifc_class: str,
    parent_id: str | None,
    origin: list[int],
    *,
    elevation: int | None = None,
) -> dict:
    attributes = {"Name": entity_id}
    if parent_id is not None:
        attributes["ObjectPlacement"] = {
            "relative_to": parent_id,
            "origin": origin,
            "axis": [0, 0, 1],
            "ref_direction": [1, 0, 0],
        }
    if elevation is not None:
        attributes["Elevation"] = elevation
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "test"},
    }


def _railing(
    entity_id: str,
    origin: list[int],
    ref_direction: list[int],
    length: int,
) -> dict:
    return {
        "id": entity_id,
        "ifc_class": "IfcRailing",
        "attributes": {
            "Name": entity_id,
            "ObjectPlacement": {
                "relative_to": "storey-2",
                "origin": origin,
                "axis": [0, 0, 1],
                "ref_direction": ref_direction,
            },
            "Representation": {
                "kind": "extruded_profile",
                "profile": {"kind": "rectangle", "x": length, "y": 50},
                "depth": 1100,
                "direction": [0, 0, 1],
            },
        },
        "property_sets": {},
        "provenance": {"source": "test"},
    }


def _document() -> dict:
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _spatial_entity("project-1", "IfcProject", None, [0, 0, 0]),
            _spatial_entity("site-1", "IfcSite", "project-1", [0, 0, 0]),
            _spatial_entity("building-1", "IfcBuilding", "site-1", [0, 0, 0]),
            _spatial_entity(
                "storey-1", "IfcBuildingStorey", "building-1", [0, 0, 0], elevation=0
            ),
            _spatial_entity(
                "storey-2",
                "IfcBuildingStorey",
                "building-1",
                [0, 0, 3300],
                elevation=3300,
            ),
            _railing("railing-atrium-north", [9000, 3000, 0], [1, 0, 0], 6000),
            _railing("railing-atrium-west", [6000, 1500, 0], [0, 1, 0], 3000),
        ],
        "relationships": [],
        "provenance": {"source": "test"},
    }


def _bim_json_id(entity) -> str:
    return str(
        ifcopenshell.util.element.get_psets(entity)["Pset_text2IFCIdentity"][
            "BimJsonId"
        ]
    )


def _bbox(entity) -> dict[str, list[float]]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    vertices = shape.geometry.verts
    axes = (vertices[0::3], vertices[1::3], vertices[2::3])
    return {
        axis: [min(values), max(values)]
        for axis, values in zip(("x", "y", "z"), axes, strict=True)
    }


def test_v2_compiles_two_storey_local_railings_with_exact_world_geometry(
    tmp_path: Path,
) -> None:
    output = tmp_path / "two-linear-railings.ifc"
    result = compile_document(_document(), output)

    assert result.success
    model = open_ifc(output)
    railings = {_bim_json_id(item): item for item in model.by_type("IfcRailing")}
    assert set(railings) == {"railing-atrium-north", "railing-atrium-west"}
    assert all(item.Representation is not None for item in railings.values())
    containment = containment_map(model)
    assert containment["railing-atrium-north"] == "storey-2"
    assert containment["railing-atrium-west"] == "storey-2"
    expected_boxes = {
        "railing-atrium-north": {
            "x": [6.0, 12.0],
            "y": [2.975, 3.025],
            "z": [3.3, 4.4],
        },
        "railing-atrium-west": {
            "x": [5.975, 6.025],
            "y": [0.0, 3.0],
            "z": [3.3, 4.4],
        },
    }
    for entity_id, expected in expected_boxes.items():
        actual = _bbox(railings[entity_id])
        for axis in ("x", "y", "z"):
            assert actual[axis] == pytest.approx(expected[axis], abs=1e-6)
