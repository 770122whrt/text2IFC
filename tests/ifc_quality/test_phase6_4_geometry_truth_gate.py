from pathlib import Path

from text2ifc_compiler import compile_document
from text2ifc_quality.generated_ifc import check_generated_ifc


def test_generated_ifc_gate_reports_vertical_slab_wall_gap(tmp_path: Path):
    output = tmp_path / "slab-gap.ifc"
    result = compile_document(_slab_gap_document(), output)

    assert result.success
    gate = check_generated_ifc(output, _slab_gap_expectation())

    assert gate.success is False
    issue = next(item for item in gate.issues if item["code"] == "VERTICAL_SLAB_WALL_GAP")
    assert issue["entity_ids"] == ["wall-1", "slab-storey-2-floor"]
    assert issue["actual"]["gap_m"] == 0.15
    assert issue["source_fact_refs"] == [
        "/known_facts/building/floor_slab_thickness_mm",
        "/known_facts/storeys/1/elevation_mm",
    ]


def _slab_gap_expectation() -> dict:
    return {
        "case_id": "slab-gap",
        "tolerance": 0.05,
        "walls": {
            "wall-1": {
                "axis": "x",
                "bbox": {
                    "x": [-3.0, 3.0],
                    "y": [-0.1, 0.1],
                    "z": [0.0, 3.0],
                },
            }
        },
        "slabs": {
            "slab-storey-2-floor": {
                "bbox": {
                    "x": [0.0, 6.0],
                    "y": [0.0, 4.0],
                    "z": [3.0, 3.15],
                },
                "must_touch_walls": ["wall-1"],
                "source_fact_refs": [
                    "/known_facts/building/floor_slab_thickness_mm",
                    "/known_facts/storeys/1/elevation_mm",
                ],
            }
        },
    }


def _slab_gap_document() -> dict:
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _entity("project-1", "IfcProject", {"Name": "Project"}),
            _entity("site-1", "IfcSite", {"Name": "Site", "ObjectPlacement": _placement("project-1")}),
            _entity("building-1", "IfcBuilding", {"Name": "Building", "ObjectPlacement": _placement("site-1")}),
            _entity("storey-1", "IfcBuildingStorey", {"Name": "Storey 1", "Elevation": 0, "ObjectPlacement": _placement("building-1")}),
            _entity("storey-2", "IfcBuildingStorey", {"Name": "Storey 2", "Elevation": 3150, "ObjectPlacement": _placement("building-1", [0, 0, 3150])}),
            _entity(
                "wall-1",
                "IfcWall",
                {
                    "Name": "Wall 1",
                    "ObjectPlacement": _placement("storey-1"),
                    "Representation": _rectangle(6000, 200, 3000),
                },
            ),
            _entity(
                "slab-storey-2-floor",
                "IfcSlab",
                {
                    "Name": "Storey 2 floor",
                    "ObjectPlacement": _placement("building-1", [0, 0, 3150]),
                    "Representation": _rectangle(6000, 4000, 150),
                },
            ),
        ],
        "relationships": [],
        "provenance": {"source": "test"},
    }


def _entity(entity_id: str, ifc_class: str, attributes: dict) -> dict:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "test"},
    }


def _placement(relative_to: str, origin: list[int] | None = None) -> dict:
    return {
        "relative_to": relative_to,
        "origin": origin or [0, 0, 0],
        "axis": [0, 0, 1],
        "ref_direction": [1, 0, 0],
    }


def _rectangle(x: int, y: int, depth: int) -> dict:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "rectangle", "x": x, "y": y},
        "depth": depth,
        "direction": [0, 0, 1],
    }
