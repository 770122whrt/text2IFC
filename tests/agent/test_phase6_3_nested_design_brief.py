from text2ifc_agent.expected_facts import build_expected_facts


def test_expected_facts_normalizes_nested_storey_design_brief_without_fabricated_ids():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "number_of_storeys": 2,
                "width_x_mm": 10000,
                "depth_y_mm": 8000,
                "storey_height_mm": 3000,
                "wall_thickness_mm": 200,
            },
            "storeys": {
                "first_floor": {
                    "elevation_mm": 0,
                    "spaces": {
                        "living_room": {"dimensions_mm": [6000, 4500]},
                        "kitchen": {"dimensions_mm": [4000, 3500]},
                    },
                    "doors": [
                        {
                            "host_wall": "living_room_south",
                            "width_mm": 1200,
                            "height_mm": 2200,
                        }
                    ],
                    "windows": [
                        {
                            "count": 2,
                            "host_wall": "living_room_south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        }
                    ],
                },
                "second_floor": {
                    "elevation_mm": 3150,
                    "spaces": {
                        "bedroom": {"dimensions_mm": [5000, 4000]},
                    },
                    "doors": [
                        {
                            "host_wall": "corridor_to_bedroom",
                            "width_mm": 900,
                            "height_mm": 2100,
                        }
                    ],
                    "windows": [
                        {
                            "host_wall": "bedroom_south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        }
                    ],
                },
            },
            "slabs": {
                "ground_floor": {"thickness_mm": 150, "elevation_mm": 0},
                "first_floor": {"thickness_mm": 150, "elevation_mm": 3150},
                "roof": {"thickness_mm": 150, "elevation_mm": 6150},
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="nested-live-style",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "first_floor", "elevation_mm": 0},
        {"id": "storey-2", "source_key": "second_floor", "elevation_mm": 3150},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 1}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 2, "storey-2": 1}
    assert expected["total_counts"] == {
        "IfcBuildingStorey": 2,
        "IfcSpace": 3,
        "IfcDoor": 2,
        "IfcWindow": 3,
    }
    assert expected["required_relationships"]["opening_fill"] == {
        "doors": 2,
        "windows": 3,
    }
    assert expected["doors"][0] == {
        "storey": "storey-1",
        "source_key": "first_floor.door[1]",
        "host_wall": "living_room_south",
        "width_mm": 1200,
        "height_mm": 2200,
    }
    assert expected["windows"][0]["source_key"] == "first_floor.window[1]"
    assert expected["windows"][1]["source_key"] == "first_floor.window[2]"
    assert "id" not in expected["doors"][0]
    assert "id" not in expected["windows"][0]
    assert expected["slabs"] == [
        {
            "source_key": "ground_floor",
            "elevation_mm": 0,
            "thickness_mm": 150,
        },
        {
            "source_key": "first_floor",
            "elevation_mm": 3150,
            "thickness_mm": 150,
        },
    ]
    assert expected["roof"]["source_key"] == "roof"
    assert expected["roof"]["elevation_mm"] == 6150
    assert expected["roof"]["thickness_mm"] == 150


def test_expected_facts_normalizes_live_deepseek_flat_multistorey_dialect():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "number_of_storeys": 2,
                "overall_width_x": 10000,
                "overall_depth_y": 8000,
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
                    {"name": "过道"},
                ],
                "二层": [
                    {"name": "主卧", "rectangle": {"min_x": 0, "min_y": 0, "max_x": 5000, "max_y": 4000}},
                    {"name": "走廊", "width": 1200},
                ],
            },
            "doors": [
                {"id": "door_1", "host": "客厅南墙", "width": 1200, "height": 2200},
                {"id": "door_2", "host": "二层走廊连接主卧", "width": 900, "height": 2100},
            ],
            "windows": [
                {
                    "id": "window_1",
                    "host": "客厅南墙",
                    "quantity": 2,
                    "width": 1500,
                    "height": 1200,
                    "sill_height": 900,
                },
                {
                    "id": "window_2",
                    "host": "主卧南墙",
                    "quantity": 2,
                    "width": 1500,
                    "height": 1200,
                    "sill_height": 900,
                },
            ],
            "slabs": {
                "ground_floor": {"elevation": 0, "thickness": 150},
                "first_floor": {"elevation": 3150, "thickness": 150},
                "roof_slab": {"elevation_bottom": 6150, "thickness": 150},
            },
            "roof": {"bottom_elevation": 6150, "thickness": 150},
            "stair": {"start_elevation": 150, "end_elevation": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="live-deepseek-dialect",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "首层", "elevation_mm": 0, "name": "首层"},
        {"id": "storey-2", "source_key": "二层", "elevation_mm": 3150, "name": "二层"},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 3, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["total_counts"] == {
        "IfcBuildingStorey": 2,
        "IfcSpace": 5,
        "IfcDoor": 2,
        "IfcWindow": 4,
    }
    assert expected["doors"][0]["host_wall"] == "客厅南墙"
    assert expected["doors"][0]["width_mm"] == 1200
    assert expected["windows"][1]["source_key"] == "window_1[2]"
    assert expected["windows"][2]["storey"] == "storey-2"
    assert expected["roof"]["source_key"] == "roof"
    assert expected["roof"]["elevation_mm"] == 6150
    assert expected["roof"]["thickness_mm"] == 150


def test_expected_facts_normalizes_live_deepseek_floor_map_without_storey_list():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "width_mm": 10000,
                "depth_mm": 8000,
                "num_storeys": 2,
                "storey_height_mm": 3000,
                "slab_thickness_mm": 150,
                "wall_thickness_mm": 200,
            },
            "spaces": {
                "ground_floor": [
                    {"name": "living", "width_mm": 6000, "depth_mm": 4500},
                    {"name": "kitchen", "width_mm": 4000, "depth_mm": 3500},
                    {"name": "bathroom", "width_mm": 2500, "depth_mm": 2500},
                    {"name": "stair", "width_mm": 3500, "depth_mm": 3500},
                ],
                "first_floor": [
                    {"name": "master", "width_mm": 5000, "depth_mm": 4000},
                    {"name": "second", "width_mm": 4000, "depth_mm": 3500},
                    {"name": "study", "width_mm": 3000, "depth_mm": 2500},
                    {"name": "bathroom2", "width_mm": 2500, "depth_mm": 2500},
                    {"name": "corridor", "width_mm": 1200},
                ],
            },
            "doors": {
                "ground_floor": [
                    {"name": "entry", "host": "south_wall", "width_mm": 1200, "height_mm": 2200},
                    {"name": "kitchen door", "host": "east_wall_living", "width_mm": 900, "height_mm": 2100},
                ],
                "first_floor": [
                    {"name": "master door", "host": "wall_main_bedroom", "width_mm": 900, "height_mm": 2100},
                    {"name": "bath door", "host": "west_wall_bathroom_ff", "width_mm": 750, "height_mm": 2100},
                ],
            },
            "windows": {
                "ground_floor": [
                    {"name": "living south 1", "host": "south_wall", "width_mm": 1500, "height_mm": 1200, "sill_height_mm": 900},
                    {"name": "living south 2", "host": "south_wall", "width_mm": 1500, "height_mm": 1200, "sill_height_mm": 900},
                ],
                "first_floor": [
                    {"name": "master south 1", "host": "south_wall", "width_mm": 1500, "height_mm": 1200, "sill_height_mm": 900},
                    {"name": "bath west", "host": "west_wall", "width_mm": 800, "height_mm": 600, "sill_height_mm": 1600},
                ],
            },
            "roof": {"elevation_mm": 6150},
            "stairs": {"start_z_mm": 150, "end_z_mm": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="live-floor-map-dialect",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "ground_floor", "elevation_mm": 0},
        {"id": "storey-2", "source_key": "first_floor", "elevation_mm": 3150},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 4, "storey-2": 5}
    assert expected["door_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["window_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["total_counts"]["IfcBuildingStorey"] == 2
    assert expected["total_counts"]["IfcSpace"] == 9
    assert expected["spaces"][0]["storey"] == "storey-1"
    assert expected["spaces"][4]["storey"] == "storey-2"
    assert expected["doors"][2]["storey"] == "storey-2"
    assert expected["windows"][3]["sill_height_mm"] == 1600


def test_expected_facts_normalizes_live_deepseek_storey_list_with_inline_spaces():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "length_mm": 10000,
                "width_mm": 8000,
                "num_storeys": 2,
                "storey_height_mm": 3000,
                "slab_thickness_mm": 150,
                "wall_thickness_mm": 200,
            },
            "storeys": [
                {
                    "name": "首层",
                    "elevation_mm": 0,
                    "spaces": [
                        {"name": "客厅", "length_mm": 6000, "width_mm": 4500},
                        {"name": "厨房", "length_mm": 4000, "width_mm": 3500},
                    ],
                },
                {
                    "name": "二层",
                    "elevation_mm": 3150,
                    "spaces": [
                        {"name": "主卧", "length_mm": 5000, "width_mm": 4000},
                        {"name": "走廊", "width_mm": 1200},
                    ],
                },
            ],
            "doors": [
                {"floor": 1, "host": "首层客厅南墙", "width_mm": 1200, "height_mm": 2200},
                {"floor": 2, "host": "二层主卧", "width_mm": 900, "height_mm": 2100},
            ],
            "windows": [
                {"floor": 1, "host": "首层客厅南墙", "quantity": 2, "width_mm": 1500, "height_mm": 1200},
                {"floor": 2, "host": "二层主卧南墙", "quantity": 2, "width_mm": 1500, "height_mm": 1200},
            ],
            "roof_elevation_mm": 6150,
            "stair": {"from_elevation_mm": 150, "to_elevation_mm": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="live-storey-list-inline-spaces",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "首层", "elevation_mm": 0, "name": "首层"},
        {"id": "storey-2", "source_key": "二层", "elevation_mm": 3150, "name": "二层"},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["spaces"][0]["dimensions_mm"] == [6000, 4500]
    assert expected["spaces"][2]["storey"] == "storey-2"
    assert expected["doors"][1]["storey"] == "storey-2"
    assert expected["roof"]["elevation_mm"] == 6150
    assert expected["stairs"][0]["start_elevation_mm"] == 150
    assert expected["stairs"][0]["end_elevation_mm"] == 3150
