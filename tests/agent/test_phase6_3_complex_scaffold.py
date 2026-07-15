import collections
import json

from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_compiler.compiler import compile_document
from text2ifc_contract.validation_v2 import validate_v2_document

try:
    from text2ifc_agent.complex_scaffold import build_scaffold_candidate
except ModuleNotFoundError:  # pragma: no cover - RED path before implementation.
    build_scaffold_candidate = None


def test_complex_nested_design_brief_scaffold_compiles_and_passes_dynamic_gates(tmp_path):
    assert build_scaffold_candidate is not None
    design_brief = _complex_two_storey_nested_design_brief()
    expected = build_expected_facts(
        case_id="complex-two-storey-scaffold",
        design_brief=design_brief,
    )

    candidate = build_scaffold_candidate(
        case_id="complex-two-storey-scaffold",
        design_brief=design_brief,
        expected_facts=expected,
    )

    class_counts = collections.Counter(
        entity["ifc_class"] for entity in candidate["entities"]
    )
    assert class_counts["IfcBuildingStorey"] == 2
    assert class_counts["IfcSpace"] == 9
    assert class_counts["IfcDoor"] == 9
    assert class_counts["IfcWindow"] == 9
    assert class_counts["IfcSlab"] >= 2
    assert class_counts["IfcRoof"] == 1
    assert class_counts["IfcStair"] == 1

    assert [_validation_issue(issue) for issue in validate_v2_document(candidate)] == []
    gates = evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
    assert {gate["name"]: gate["status"] for gate in gates} == {
        "dynamic_entity_completeness": "passed",
        "dynamic_storey_containment": "passed",
        "dynamic_opening_fill": "passed",
        "dynamic_storey_name_consistency": "skipped",
    }

    output_ifc = tmp_path / "two-storey-scaffold.ifc"
    compilation = compile_document(candidate, output_ifc)
    assert compilation.success, json.dumps(
        {
            "input_issues": [
                _validation_issue(issue) for issue in compilation.input_issues
            ],
            "ifc_issues": [
                {
                    "code": issue.code,
                    "entity": issue.entity,
                    "attribute": issue.attribute,
                    "message": issue.message,
                }
                for issue in compilation.ifc_issues
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
    assert output_ifc.is_file()


def test_complex_scaffold_accepts_live_deepseek_design_brief_field_aliases(tmp_path):
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "number_of_storeys": 2,
                "length_x_mm": 10000,
                "width_y_mm": 8000,
            },
            "walls": {"thickness": 200},
            "storeys": [
                {"name": "首层", "elevation": 0, "net_height": 3000},
                {"name": "二层", "elevation": 3150, "net_height": 3000},
            ],
            "spaces": {
                "首层": [
                    {"name": "客厅", "rectangle": {"min_x": 0, "min_y": 0, "max_x": 6000, "max_y": 4500}},
                    {"name": "厨房", "rectangle": {"min_x": 6000, "min_y": 0, "max_x": 10000, "max_y": 3500}},
                ],
                "二层": [
                    {"name": "主卧", "rectangle": {"min_x": 0, "min_y": 0, "max_x": 5000, "max_y": 4000}},
                ],
            },
            "doors": [{"id": "door_1", "host": "客厅南墙", "width": 1200, "height": 2200}],
            "windows": [{"id": "window_1", "host": "主卧南墙", "quantity": 2, "width": 1500, "height": 1200, "sill_height": 900}],
            "slabs": {
                "ground_floor": {"elevation": 0, "thickness": 150},
                "first_floor": {"elevation": 3150, "thickness": 150},
            },
            "roof": {"bottom_elevation": 6150, "thickness": 150},
            "stair": {"start_elevation": 150, "end_elevation": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }
    expected = build_expected_facts(
        case_id="live-deepseek-scaffold-aliases",
        design_brief=design_brief,
    )

    candidate = build_scaffold_candidate(
        case_id="live-deepseek-scaffold-aliases",
        design_brief=design_brief,
        expected_facts=expected,
    )

    assert [_validation_issue(issue) for issue in validate_v2_document(candidate)] == []
    gates = evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
    assert all(gate["status"] == "passed" for gate in gates)
    compilation = compile_document(candidate, tmp_path / "alias-scaffold.ifc")
    assert compilation.success


def test_complex_scaffold_accepts_footprint_and_xy_min_max_aliases(tmp_path):
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "footprint": {"x_min": 0, "x_max": 10000, "y_min": 0, "y_max": 8000},
                "storeys": 2,
            },
            "wall_thickness": 200,
            "storeys": [
                {"name": "Ground", "wall_base": 0, "wall_top": 3000},
                {"name": "First", "slab_top": 3150, "wall_base": 3150, "wall_top": 6150},
            ],
            "spaces": {
                "ground": {
                    "living_room": {"x_min": 0, "x_max": 6000, "y_min": 0, "y_max": 4500},
                    "kitchen": {"x_min": 6000, "x_max": 10000, "y_min": 0, "y_max": 3500},
                },
                "first": {
                    "master_bedroom": {"x_min": 0, "x_max": 5000, "y_min": 0, "y_max": 4000},
                },
            },
            "doors": {
                "ground": [{"host": "living_room south exterior", "width": 1200, "height": 2200}],
                "first": [{"room": "master_bedroom", "width": 900, "height": 2100}],
            },
            "windows": {
                "ground": [{"wall": "living_room south exterior", "width": 1500, "height": 1200, "sill": 900}],
                "first": [{"wall": "master_bedroom south exterior", "width": 1500, "height": 1200, "sill": 900}],
            },
            "roof_slab": {"bottom_elevation": 6150, "thickness": 150},
            "stair": {"rise_from_z": 150, "rise_to_z": 3150, "width": 1000},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }
    expected = build_expected_facts(
        case_id="footprint-xy-aliases",
        design_brief=design_brief,
    )

    assert expected["spaces"][0]["dimensions_mm"] == [6000, 4500]
    assert expected["spaces"][0]["origin_mm"] == [0, 0, 0]
    assert expected["spaces"][1]["origin_mm"] == [6000, 0, 0]

    candidate = build_scaffold_candidate(
        case_id="footprint-xy-aliases",
        design_brief=design_brief,
        expected_facts=expected,
    )

    assert [_validation_issue(issue) for issue in validate_v2_document(candidate)] == []
    compilation = compile_document(candidate, tmp_path / "footprint-alias-scaffold.ifc")
    assert compilation.success


def test_complex_scaffold_uses_room_label_when_opening_host_wall_is_missing(tmp_path):
    design_brief = _complex_two_storey_nested_design_brief()
    expected = build_expected_facts(
        case_id="room-label-opening-host",
        design_brief=design_brief,
    )
    expected["doors"][0].pop("host_wall", None)
    expected["doors"][0]["room"] = "主卧"

    candidate = build_scaffold_candidate(
        case_id="room-label-opening-host",
        design_brief=design_brief,
        expected_facts=expected,
    )

    class_counts = collections.Counter(
        entity["ifc_class"] for entity in candidate["entities"]
    )
    assert class_counts["IfcDoor"] == expected["total_counts"]["IfcDoor"]
    compilation = compile_document(candidate, tmp_path / "room-label-opening-host.ifc")
    assert compilation.success


def _validation_issue(issue) -> dict:
    return {
        "code": issue.code,
        "path": issue.path,
        "message": issue.message,
    }


def _complex_two_storey_nested_design_brief() -> dict:
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "coordinate_origin": "southwest_corner",
                "number_of_storeys": 2,
                "width_x_mm": 10000,
                "depth_y_mm": 8000,
                "storey_height_mm": 3000,
                "wall_thickness_mm": 200,
                "slab_thickness_mm": 150,
            },
            "storeys": {
                "first_floor": {
                    "elevation_mm": 0,
                    "spaces": {
                        "living_room": {
                            "dimensions_mm": [6000, 4500],
                            "height_mm": 3000,
                            "location": "southwest",
                        },
                        "kitchen": {
                            "dimensions_mm": [4000, 3500],
                            "height_mm": 3000,
                            "location": "southeast",
                        },
                        "bathroom": {
                            "dimensions_mm": [2500, 2500],
                            "height_mm": 3000,
                            "location": "northeast",
                        },
                        "staircase": {
                            "dimensions_mm": [3500, 3500],
                            "height_mm": 3000,
                            "location": "northwest",
                        },
                    },
                    "doors": [
                        {
                            "host_wall": "living_room_south",
                            "position": "center",
                            "width_mm": 1200,
                            "height_mm": 2200,
                        },
                        {
                            "host_wall": "living_room_east",
                            "width_mm": 900,
                            "height_mm": 2100,
                        },
                        {
                            "host_wall": "kitchen_north",
                            "width_mm": 800,
                            "height_mm": 2100,
                        },
                        {
                            "host_wall": "bathroom_west",
                            "width_mm": 750,
                            "height_mm": 2100,
                        },
                        {
                            "host_wall": "staircase_east",
                            "width_mm": 900,
                            "height_mm": 2100,
                        },
                    ],
                    "windows": [
                        {
                            "count": 2,
                            "host_wall": "living_room_south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        },
                        {
                            "host_wall": "kitchen_east",
                            "width_mm": 1200,
                            "height_mm": 1000,
                            "sill_height_mm": 1000,
                        },
                        {
                            "host_wall": "bathroom_north",
                            "width_mm": 800,
                            "height_mm": 600,
                            "sill_height_mm": 1600,
                        },
                    ],
                    "stair": {
                        "location": "staircase",
                        "start_elevation_mm": 150,
                        "end_elevation_mm": 3150,
                    },
                },
                "second_floor": {
                    "elevation_mm": 3150,
                    "spaces": {
                        "master_bedroom": {
                            "dimensions_mm": [5000, 4000],
                            "height_mm": 3000,
                            "location": "southwest",
                        },
                        "second_bedroom": {
                            "dimensions_mm": [4000, 3500],
                            "height_mm": 3000,
                            "location": "southeast",
                        },
                        "study": {
                            "dimensions_mm": [3000, 2500],
                            "height_mm": 3000,
                            "location": "northeast",
                        },
                        "bathroom": {
                            "dimensions_mm": [2500, 2500],
                            "height_mm": 3000,
                            "location": "northwest",
                        },
                        "corridor": {
                            "width_mm": 1200,
                            "description": "connects staircase to all rooms",
                        },
                    },
                    "doors": [
                        {
                            "host_wall": "corridor_to_master_bedroom",
                            "width_mm": 900,
                            "height_mm": 2100,
                        },
                        {
                            "host_wall": "corridor_to_second_bedroom",
                            "width_mm": 900,
                            "height_mm": 2100,
                        },
                        {
                            "host_wall": "corridor_to_study",
                            "width_mm": 900,
                            "height_mm": 2100,
                        },
                        {
                            "host_wall": "corridor_to_bathroom",
                            "width_mm": 750,
                            "height_mm": 2100,
                        },
                    ],
                    "windows": [
                        {
                            "count": 2,
                            "host_wall": "master_bedroom_south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        },
                        {
                            "host_wall": "second_bedroom_east",
                            "width_mm": 1400,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        },
                        {
                            "host_wall": "study_north",
                            "width_mm": 1200,
                            "height_mm": 1000,
                            "sill_height_mm": 900,
                        },
                        {
                            "host_wall": "bathroom_west",
                            "width_mm": 800,
                            "height_mm": 600,
                            "sill_height_mm": 1600,
                        },
                    ],
                },
            },
            "slabs": {
                "ground_floor": {"coverage": "full_building", "elevation_mm": 0, "thickness_mm": 150},
                "first_floor": {"coverage": "full_building", "elevation_mm": 3150, "thickness_mm": 150},
                "roof": {"coverage": "full_building", "elevation_mm": 6150, "thickness_mm": 150},
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }
