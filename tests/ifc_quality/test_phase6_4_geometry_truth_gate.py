from pathlib import Path

import pytest

from text2ifc_compiler import compile_document
from text2ifc_quality.generated_ifc import (
    _stair_endpoint_diagnostics,
    _stair_footprint_diagnostics,
    check_generated_ifc,
)


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


def test_generated_ifc_gate_keeps_slab_gap_when_wall_also_fails(tmp_path: Path):
    output = tmp_path / "slab-gap-with-wall-error.ifc"
    result = compile_document(_slab_gap_document(), output)
    expectation = _slab_gap_expectation()
    expectation["walls"]["wall-1"]["bbox"]["x"] = [0.0, 6.0]

    assert result.success
    gate = check_generated_ifc(output, expectation)

    codes = {item["code"] for item in gate.issues}
    assert "WALL_BBOX_MISMATCH" in codes
    assert "VERTICAL_SLAB_WALL_GAP" in codes
    wall_issue = next(item for item in gate.issues if item["code"] == "WALL_BBOX_MISMATCH")
    assert wall_issue["entity_ids"] == ["wall-1"]
    assert wall_issue["expected"]["x"] == [0.0, 6.0]
    assert wall_issue["actual"]["x"] == [-3.0, 3.0]
    assert wall_issue["source_fact_refs"] == ["/known_facts/storeys/0/walls/interior/0"]


def test_generated_ifc_gate_fails_closed_for_incomplete_required_expectation(
    tmp_path: Path,
):
    output = tmp_path / "incomplete-expectation.ifc"
    result = compile_document(_slab_gap_document(), output)
    expectation = _slab_gap_expectation()
    expectation.update(
        {
            "complete": False,
            "unresolved": [
                {
                    "path": "/known_facts/storeys/0/spaces/0",
                    "reason": "space_geometry_missing",
                    "source_fact_refs": ["/known_facts/storeys/0/spaces/0"],
                }
            ],
        }
    )

    assert result.success
    gate = check_generated_ifc(output, expectation)

    assert gate.success is False
    issue = next(
        item
        for item in gate.issues
        if item["code"] == "GEOMETRY_EXPECTATION_INCOMPLETE"
    )
    assert issue["path"] == "/known_facts/storeys/0/spaces/0"
    assert issue["actual"] == {"reason": "space_geometry_missing"}
    assert issue["source_fact_refs"] == ["/known_facts/storeys/0/spaces/0"]


def test_generated_ifc_gate_rejects_wrong_roof_stair_and_opening_bounds(tmp_path: Path):
    output = tmp_path / "bad-stair-system.ifc"
    document = _slab_gap_document()
    document["entities"].extend(
        [
            _entity(
                "roof-slab",
                "IfcSlab",
                {
                    "Name": "Roof",
                    "ObjectPlacement": _placement("building-1", [0, 0, 9300]),
                    "Representation": _rectangle(6000, 4000, 150),
                },
            ),
            _entity(
                "stair-1",
                "IfcStair",
                    {
                        "Name": "Stair",
                        "ShapeType": "STRAIGHT_RUN_STAIR",
                        "ObjectPlacement": _placement("storey-1", [0, 0, 0]),
                        "Representation": _rectangle(1000, 3900, 3000),
                    },
                ),
            _entity(
                "stair-flight-1",
                "IfcStairFlight",
                {
                    "Name": "Ramp-like flight",
                    "ObjectPlacement": _placement("stair-1"),
                    "Representation": _rectangle(1000, 3900, 3000),
                },
            ),
            _entity(
                "stair-opening-1",
                "IfcOpeningElement",
                {
                    "Name": "Wrong stair opening",
                    "ObjectPlacement": _placement("building-1", [4000, 2000, 3150]),
                    "Representation": _rectangle(2000, 4000, 150),
                },
            ),
        ]
    )
    document["relationships"].append(
        {
            "id": "void-stair-opening",
            "ifc_class": "IfcRelVoidsElement",
            "attributes": {
                "RelatingBuildingElement": "slab-storey-2-floor",
                "RelatedOpeningElement": "stair-opening-1",
            },
            "provenance": {"source": "test"},
        }
    )
    result = compile_document(document, output)
    expectation = _slab_gap_expectation()
    expectation.update(
        {
            "roof": {
                "roof-slab": {
                    "bbox": {"x": [-3.0, 3.0], "y": [-2.0, 2.0], "z": [6.15, 6.3]}
                }
            },
            "stairs": {
                "stair-1": {
                    "flight_ids": ["stair-flight-1"],
                    "bbox": {"x": [0.5, 1.5], "y": [4.05, 7.95], "z": [0.15, 3.15]},
                    "require_steps": True,
                }
            },
            "floor_openings": {
                "stair-opening-1": {
                    "bbox": {"x": [0.0, 2.0], "y": [4.0, 8.0], "z": [3.0, 3.15]}
                }
            },
        }
    )

    assert result.success
    gate = check_generated_ifc(output, expectation)

    codes = {item["code"] for item in gate.issues}
    assert "ROOF_BBOX_MISMATCH" in codes
    assert "STAIR_FOOTPRINT_MISMATCH" in codes
    assert "STAIR_RISE_DIRECTION_MISMATCH" in codes
    assert "STAIR_STEP_PROFILE_MISSING" in codes
    assert "STAIR_OPENING_BBOX_MISMATCH" in codes
    stair_rise = next(
        item for item in gate.issues if item["code"] == "STAIR_RISE_DIRECTION_MISMATCH"
    )
    assert stair_rise["endpoint_deltas"] == {
        "lower": pytest.approx(0.15),
        "upper": pytest.approx(0.15),
    }
    assert stair_rise["translation_only_valid"] is True
    assert stair_rise["recommended_action"] == "translate_stair"


def test_stair_endpoint_diagnostics_require_profile_reshape_when_only_one_end_differs():
    diagnostics = _stair_endpoint_diagnostics(
        actual_z=[0.3, 3.15],
        expected_z=[0.15, 3.15],
        tolerance=0.05,
    )

    assert diagnostics["endpoint_deltas"] == {
        "lower": pytest.approx(-0.15),
        "upper": pytest.approx(0.0),
    }
    assert diagnostics["translation_only_valid"] is False
    assert diagnostics["recommended_action"] == "reshape_flight_profile_preserve_endpoints"
    assert diagnostics["correction_constraints"] == {
        "lower_endpoint": (
            "Create a non-zero-width horizontal tread edge at the expected "
            "lower world elevation."
        ),
        "upper_endpoint": "Preserve the expected upper world elevation.",
        "forbidden": (
            "Do not fix only parent or flight translation when endpoint deltas differ."
        ),
    }


def test_stair_footprint_diagnostics_identify_swapped_plan_axes():
    diagnostics = _stair_footprint_diagnostics(
        actual_bbox={"x": [0.6, 4.0], "y": [4.2, 5.2]},
        expected_bbox={"x": [4.0, 5.0], "y": [4.2, 7.6]},
        tolerance=0.05,
    )

    assert diagnostics == {
        "plan_axes_swapped": True,
        "recommended_action": "rotate_parent_stair_placement",
        "correction_constraints": {
            "change": "Adjust IfcStair ObjectPlacement.ref_direction in plan.",
            "preserve": (
                "Preserve the stepped flight profile and its horizontal width "
                "extrusion direction."
            ),
            "verify": "Recompile and compare the world-space X/Y footprint.",
        },
    }


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
                "source_fact_refs": ["/known_facts/storeys/0/walls/interior/0"],
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
