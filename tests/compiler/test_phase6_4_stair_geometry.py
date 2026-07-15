from pathlib import Path

from text2ifc_compiler import compile_document, open_ifc


def test_stair_profile_rise_maps_to_positive_global_z(tmp_path: Path):
    document = {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            *_base_entities(),
            {
                "id": "stair-1",
                "ifc_class": "IfcStair",
                "attributes": {
                    "Name": "Upward stair",
                    "ShapeType": "STRAIGHT_RUN_STAIR",
                    "ObjectPlacement": {
                        "relative_to": "storey-1",
                        "origin": [0, 4000, 150],
                        "axis": [0, 0, 1],
                        "ref_direction": [1, 0, 0],
                    },
                    "Representation": {
                        "kind": "extruded_profile",
                        "profile": {
                            "kind": "polygon",
                            "points": [
                                [0, 0],
                                [2000, 0],
                                [2000, 3000],
                                [0, 3000],
                                [0, 0],
                            ],
                        },
                        "depth": 1000,
                        "direction": [0, 1, 0],
                    },
                },
                "property_sets": {},
                "provenance": {"source": "test"},
            }
        ],
        "relationships": [],
        "provenance": {"source": "test"},
    }

    output = tmp_path / "upward-stair.ifc"
    result = compile_document(document, output)

    assert result.success
    model = open_ifc(output)
    solid = model.by_type("IfcExtrudedAreaSolid")[0]
    axis = tuple(float(item) for item in solid.Position.Axis.DirectionRatios)
    ref = tuple(float(item) for item in solid.Position.RefDirection.DirectionRatios)
    profile_rise_axis = (
        axis[1] * ref[2] - axis[2] * ref[1],
        axis[2] * ref[0] - axis[0] * ref[2],
        axis[0] * ref[1] - axis[1] * ref[0],
    )

    assert profile_rise_axis == (0.0, 0.0, 1.0)


def _base_entities() -> list[dict]:
    return [
        {
            "id": "project-1",
            "ifc_class": "IfcProject",
            "attributes": {"Name": "Project"},
            "property_sets": {},
            "provenance": {"source": "test"},
        },
        {
            "id": "site-1",
            "ifc_class": "IfcSite",
            "attributes": {
                "Name": "Site",
                "ObjectPlacement": {
                    "relative_to": "project-1",
                    "origin": [0, 0, 0],
                    "axis": [0, 0, 1],
                    "ref_direction": [1, 0, 0],
                },
            },
            "property_sets": {},
            "provenance": {"source": "test"},
        },
        {
            "id": "building-1",
            "ifc_class": "IfcBuilding",
            "attributes": {
                "Name": "Building",
                "ObjectPlacement": {
                    "relative_to": "site-1",
                    "origin": [0, 0, 0],
                    "axis": [0, 0, 1],
                    "ref_direction": [1, 0, 0],
                },
            },
            "property_sets": {},
            "provenance": {"source": "test"},
        },
        {
            "id": "storey-1",
            "ifc_class": "IfcBuildingStorey",
            "attributes": {
                "Name": "Storey 1",
                "Elevation": 0,
                "ObjectPlacement": {
                    "relative_to": "building-1",
                    "origin": [0, 0, 0],
                    "axis": [0, 0, 1],
                    "ref_direction": [1, 0, 0],
                },
            },
            "property_sets": {},
            "provenance": {"source": "test"},
        },
    ]
