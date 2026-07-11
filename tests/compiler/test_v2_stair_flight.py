from pathlib import Path

from text2ifc_compiler import compile_document, open_ifc


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


def test_v2_compiles_stair_with_aggregated_stair_flight(tmp_path: Path):
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
                    "Name": "Main stair",
                    "ShapeType": "STRAIGHT_RUN_STAIR",
                    "ObjectPlacement": {
                        "relative_to": "storey-1",
                        "origin": [6000, 0, 150],
                        "axis": [0, 0, 1],
                        "ref_direction": [1, 0, 0],
                    },
                },
                "property_sets": {},
                "provenance": {"source": "test"},
            },
            {
                "id": "stair-flight-1",
                "ifc_class": "IfcStairFlight",
                "attributes": {
                    "Name": "Main stair flight",
                    "ObjectPlacement": {
                        "relative_to": "stair-1",
                        "origin": [0, 0, 0],
                        "axis": [0, 0, 1],
                        "ref_direction": [1, 0, 0],
                    },
                    "Representation": {
                        "kind": "extruded_profile",
                        "profile": {
                            "kind": "polygon",
                            "points": [
                                [0, 0],
                                [300, 0],
                                [300, 300],
                                [600, 300],
                                [600, 600],
                                [900, 600],
                                [900, 900],
                                [0, 900],
                                [0, 0],
                            ],
                        },
                        "depth": 1000,
                        "direction": [0, 0, 1],
                    },
                },
                "property_sets": {},
                "provenance": {"source": "test"},
            },
        ],
        "relationships": [
            {
                "id": "aggregate-stair-flight",
                "ifc_class": "IfcRelAggregates",
                "attributes": {
                    "RelatingObject": "stair-1",
                    "RelatedObjects": ["stair-flight-1"],
                },
                "provenance": {"source": "test"},
            }
        ],
        "provenance": {"source": "test"},
    }

    output = tmp_path / "stair-flight.ifc"
    result = compile_document(document, output)

    assert result.success
    model = open_ifc(output)
    assert len(model.by_type("IfcStair")) == 1
    assert len(model.by_type("IfcStairFlight")) == 1
    stair_aggregates = [
        relation
        for relation in model.by_type("IfcRelAggregates")
        if relation.RelatingObject.is_a("IfcStair")
    ]
    assert len(stair_aggregates) == 1
    assert [item.is_a() for item in stair_aggregates[0].RelatedObjects] == [
        "IfcStairFlight"
    ]
