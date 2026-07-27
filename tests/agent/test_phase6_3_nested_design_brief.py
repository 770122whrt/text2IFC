from text2ifc_agent.expected_facts import build_expected_facts


def test_expected_facts_derives_a_unique_canonical_entity_id_contract():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": {
                "ground": {
                    "id": "storey-1",
                    "elevation_mm": 0,
                    "spaces": {
                        "living_room": {"id": "living_room"},
                        "corridor": {"id": "corridor"},
                    },
                },
                "upper": {
                    "id": "storey-2",
                    "elevation_mm": 3150,
                    "spaces": {
                        "corridor": {"id": "corridor"},
                    },
                },
            }
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="canonical-entity-contract",
        design_brief=design_brief,
    )

    assert expected["spaces"] == [
        {
            "id": "living_room",
            "storey": "storey-1",
            "source_key": "ground.spaces.living_room",
        },
        {
            "id": "corridor",
            "storey": "storey-1",
            "source_key": "ground.spaces.corridor",
        },
        {
            "id": "corridor",
            "storey": "storey-2",
            "source_key": "upper.spaces.corridor",
        },
    ]
    assert expected["entity_id_contract"]["spaces"] == [
        {
            "brief_id": "living_room",
            "entity_id": "space-storey-1-living-room",
            "storey": "storey-1",
        },
        {
            "brief_id": "corridor",
            "entity_id": "space-storey-1-corridor",
            "storey": "storey-1",
        },
        {
            "brief_id": "corridor",
            "entity_id": "space-storey-2-corridor",
            "storey": "storey-2",
        },
    ]


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
        "IfcSlab": 2,
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


def test_expected_facts_sorts_nested_storey_map_by_elevation_alias():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": {
                "first_floor": {
                    "elevation": 3150,
                    "spaces": {"bedroom": {"dimensions_mm": [4000, 3000]}},
                },
                "ground_floor": {
                    "elevation": 0,
                    "spaces": {"living": {"dimensions_mm": [6000, 4000]}},
                },
            },
            "doors": {
                "first_floor": [
                    {"host_wall": "bedroom_south", "width_mm": 900, "height_mm": 2100}
                ],
                "ground_floor": [
                    {"host_wall": "living_south", "width_mm": 1200, "height_mm": 2200}
                ],
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="nested-elevation-alias",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "ground_floor", "elevation_mm": 0},
        {"id": "storey-2", "source_key": "first_floor", "elevation_mm": 3150},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["spaces"][0]["source_key"] == "ground_floor.spaces.living"
    assert expected["spaces"][1]["source_key"] == "first_floor.spaces.bedroom"


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
        "IfcSlab": 3,
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


def test_expected_facts_reads_inline_storey_list_doors_and_windows():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {
                    "id": "storey-1",
                    "name": "棣栧眰",
                    "elevation_mm": 0,
                    "doors": [
                        {
                            "id": "door-entry",
                            "host_wall": "storey-1-wall-south",
                            "width_mm": 1200,
                            "height_mm": 2200,
                        }
                    ],
                    "windows": [
                        {
                            "id": "window-living-south-1",
                            "host_wall": "storey-1-wall-south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        }
                    ],
                },
                {
                    "id": "storey-2",
                    "name": "浜屽眰",
                    "elevation_mm": 3150,
                    "doors": [
                        {
                            "id": "door-master",
                            "host_wall": "storey-2-wall-master-corridor",
                            "width_mm": 900,
                            "height_mm": 2100,
                        }
                    ],
                    "windows": [
                        {
                            "id": "window-master-south-1",
                            "host_wall": "storey-2-wall-south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        },
                        {
                            "id": "window-master-south-2",
                            "host_wall": "storey-2-wall-south",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        },
                    ],
                },
            ],
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="inline-storey-list-openings",
        design_brief=design_brief,
    )

    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 1, "storey-2": 2}
    assert expected["total_counts"]["IfcDoor"] == 2
    assert expected["total_counts"]["IfcWindow"] == 3
    assert expected["required_relationships"]["opening_fill"] == {
        "doors": 2,
        "windows": 3,
    }
    assert expected["doors"][0]["id"] == "door-entry"
    assert expected["doors"][1]["storey"] == "storey-2"
    assert expected["windows"][2]["id"] == "window-master-south-2"


def test_expected_facts_normalizes_explicit_host_wall_id_without_guessing():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {
                    "id": "storey-1",
                    "elevation_mm": 0,
                    "doors": [
                        {
                            "id": "door-entry",
                            "host_wall_id": "storey-1-wall-south",
                            "width_mm": 1200,
                            "height_mm": 2200,
                        }
                    ],
                    "windows": [
                        {
                            "id": "window-west",
                            "host_wall_id": "storey-1-wall-west",
                            "width_mm": 1500,
                            "height_mm": 1200,
                            "sill_height_mm": 900,
                        }
                    ],
                }
            ]
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="explicit-host-wall-id",
        design_brief=design_brief,
    )

    assert expected["doors"][0]["host_wall"] == "storey-1-wall-south"
    assert expected["windows"][0]["host_wall"] == "storey-1-wall-west"
    assert "host_wall_id" not in expected["doors"][0]
    assert "host_wall_id" not in expected["windows"][0]


def test_expected_facts_infers_flat_opening_storey_from_chinese_location():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {
                    "name": "首层",
                    "elevation": 0,
                    "spaces": [{"name": "客厅", "internal_dimensions": {"x": 5000, "y": 6000}}],
                },
                {
                    "name": "二层",
                    "elevation": 3150,
                    "spaces": [{"name": "卧室", "internal_dimensions": {"x": 5000, "y": 6000}}],
                },
            ],
            "windows": [
                {
                    "location": "二层卧室南墙中央",
                    "width": 1500,
                    "height": 1200,
                    "sill_height": 900,
                }
            ],
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="flat-location-storey-inference",
        design_brief=design_brief,
    )

    assert expected["window_counts_by_storey"] == {"storey-2": 1}
    assert expected["windows"][0]["storey"] == "storey-2"


def test_expected_facts_reads_numbered_storey_sections_from_live_design_brief():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {"level": 1, "elevation_mm": 0, "net_height_mm": 3000},
                {"level": 2, "elevation_mm": 3150, "net_height_mm": 3000},
            ],
            "storey_1": {
                "spaces": [
                    {"name": "living_room", "axis_size_mm": [5000, 6000]},
                    {"name": "staircase_hall", "axis_size_mm": [3000, 6000]},
                ],
                "south_wall_door": {
                    "width_mm": 900,
                    "height_mm": 2100,
                    "location": "center_of_living_room_south_wall",
                },
                "internal_wall_door": {
                    "width_mm": 900,
                    "height_mm": 2100,
                    "location": "center_of_internal_wall",
                },
            },
            "storey_2": {
                "spaces": [
                    {"name": "bedroom", "axis_size_mm": [5000, 6000]},
                    {"name": "stair_landing", "axis_size_mm": [3000, 6000]},
                ],
                "south_wall_window": {
                    "width_mm": 1500,
                    "height_mm": 1200,
                    "sill_height_mm": 900,
                    "location": "center_of_bedroom_south_wall",
                },
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="numbered-storey-sections",
        design_brief=design_brief,
    )

    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 2}
    assert expected["window_counts_by_storey"] == {"storey-2": 1}
    assert expected["windows"][0]["source_key"] == "storey_2.window.south_wall_window"
    assert expected["windows"][0]["storey"] == "storey-2"


def test_expected_facts_reads_ground_first_suffix_maps_and_openings_list():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {"level": 0, "height": 3150, "net_height": 3000},
                {"level": 3150, "height": 3150, "net_height": 3000},
            ],
            "spaces_ground": {
                "living_room": {"axis_size": [5000, 6000], "zone": "west"},
                "staircase": {"axis_size": [3000, 6000], "zone": "east"},
            },
            "spaces_first": {
                "bedroom": {"axis_size": [5000, 6000], "zone": "west"},
                "landing": {"axis_size": [3000, 6000], "zone": "east"},
            },
            "openings": [
                {
                    "type": "door",
                    "host": "ground_floor_south_wall_living_room",
                    "width": 900,
                    "height": 2100,
                },
                {
                    "type": "window",
                    "host": "first_floor_south_wall_bedroom",
                    "width": 1500,
                    "height": 1200,
                    "sill_height": 900,
                },
            ],
            "stair": {
                "type": "straight",
                "start_z": 150,
                "end_z": 3150,
                "width": 1000,
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="ground-first-suffix-openings",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "storey-1", "elevation_mm": 0},
        {"id": "storey-2", "source_key": "storey-2", "elevation_mm": 3150},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1}
    assert expected["window_counts_by_storey"] == {"storey-2": 1}
    assert expected["spaces"][0]["dimensions_mm"] == [5000, 6000]
    assert expected["windows"][0]["host_wall"] == "first_floor_south_wall_bedroom"
    assert expected["stairs"][0]["storey"] == "storey-1"


def test_expected_facts_normalizes_nested_storey_map_with_space_lists_and_floor_labels():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "outer_dimensions_mm": {"x": 10000, "y": 8000},
                "number_of_storeys": 2,
                "storey_height_mm": 3000,
                "slab_thickness_mm": 150,
                "wall_thickness_mm": 200,
            },
            "storeys": {
                "ground": {
                    "elevation_mm": 0,
                    "spaces": [
                        {"name": "living", "dimensions_mm": [6000, 4500]},
                        {"name": "kitchen", "dimensions_mm": [4000, 3500]},
                    ],
                },
                "first": {
                    "elevation_mm": 3150,
                    "spaces": [
                        {"name": "master", "dimensions_mm": [5000, 4000]},
                        {"name": "corridor", "width_mm": 1200},
                    ],
                },
            },
            "doors": [
                {"storey": "ground", "host_wall": "south_wall", "width_mm": 1200, "height_mm": 2200},
                {"storey": "first", "host_wall": "master_wall", "width_mm": 900, "height_mm": 2100},
            ],
            "windows": [
                {"floor": "ground", "host_wall": "south_wall", "width_mm": 1500, "height_mm": 1200},
                {"floor": "first", "host_wall": "master_wall", "width_mm": 1500, "height_mm": 1200},
            ],
            "slabs": {
                "ground_floor": {"elevation_mm": 0, "thickness_mm": 150},
                "first_floor": {"elevation_mm": 3150, "thickness_mm": 150},
                "roof": {"elevation_mm": 6150, "thickness_mm": 150},
            },
            "stairs": {"start_elevation_mm": 150, "end_elevation_mm": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="nested-map-space-list-floor-labels",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "ground", "elevation_mm": 0},
        {"id": "storey-2", "source_key": "first", "elevation_mm": 3150},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["spaces"][2]["storey"] == "storey-2"
    assert expected["doors"][0]["storey"] == "storey-1"
    assert expected["doors"][1]["storey"] == "storey-2"


def test_expected_facts_normalizes_live_deepseek_suffix_floor_collections():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "width_x_mm": 10000,
                "depth_y_mm": 8000,
                "height_mm": 6150,
            },
            "wall_thickness_mm": 200,
            "slab_thickness_mm": 150,
            "roof_slab_thickness_mm": 150,
            "storeys": [
                {"name": "首层", "elevation_mm": 0, "height_mm": 3000},
                {"name": "二层", "elevation_mm": 3150, "height_mm": 3000},
            ],
            "spaces_ground": [
                {"name": "living", "dimensions_mm": [6000, 4500]},
                {"name": "kitchen", "dimensions_mm": [4000, 3500]},
            ],
            "spaces_first": [
                {"name": "master", "dimensions_mm": [5000, 4000]},
                {"name": "corridor", "width_mm": 1200},
            ],
            "doors_ground": [
                {"host_wall": "south_wall", "width_mm": 1200, "height_mm": 2200},
            ],
            "doors_first": [
                {"host_wall": "master_wall", "width_mm": 900, "height_mm": 2100},
            ],
            "windows_ground": [
                {"host_wall": "south_wall", "count": 2, "width_mm": 1500, "height_mm": 1200},
            ],
            "windows_first": [
                {"host_wall": "master_wall", "width_mm": 1500, "height_mm": 1200},
            ],
            "stair": {"start_elevation_mm": 150, "end_elevation_mm": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="suffix-floor-collections",
        design_brief=design_brief,
    )

    assert expected["storey_count"] == 2
    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 2, "storey-2": 1}
    assert expected["roof"]["thickness_mm"] == 150
    assert expected["slabs"][0]["thickness_mm"] == 150


def test_expected_facts_normalizes_storey_mapping_records_not_zero_counts():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "building": {
                "width_mm": 10000,
                "depth_mm": 8000,
                "storeys": 2,
                "clear_height_per_storey_mm": 3000,
                "wall_thickness_mm": 200,
                "slab_thickness_mm": 150,
                "roof_elevation_mm": 6150,
            },
            "storeys": [
                {"name": "首层", "elevation_mm": 0, "height_mm": 3000},
                {"name": "二层", "elevation_mm": 3150, "height_mm": 3000},
            ],
            "spaces": {
                "首层": {
                    "客厅": {"width_mm": 6000, "depth_mm": 4500},
                    "厨房": {"width_mm": 4000, "depth_mm": 3500},
                },
                "二层": {
                    "主卧": {"width_mm": 5000, "depth_mm": 4000},
                    "走廊": {"width_mm": 1200},
                },
            },
            "doors": {
                "首层": {
                    "客厅外门": {"host": "客厅南墙", "width_mm": 1200, "height_mm": 2200},
                },
                "二层": {
                    "主卧门": {"host": "走廊至主卧", "width_mm": 900, "height_mm": 2100},
                },
            },
            "windows": {
                "首层": {
                    "客厅南窗1": {"host": "客厅南墙", "width_mm": 1500, "height_mm": 1200},
                },
                "二层": {
                    "主卧南窗1": {"host": "主卧南墙", "width_mm": 1500, "height_mm": 1200},
                },
            },
            "stairs": {"start_elevation_mm": 150, "end_elevation_mm": 3150},
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="storey-mapping-records",
        design_brief=design_brief,
    )

    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["total_counts"]["IfcSpace"] == 4
    assert expected["total_counts"]["IfcDoor"] == 2
    assert expected["total_counts"]["IfcWindow"] == 2
    assert expected["spaces"][0]["name"] == "客厅"
    assert expected["doors"][0]["host_wall"] == "客厅南墙"


def test_expected_facts_reads_top_level_storey_maps_when_storeys_only_define_levels():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": {
                "first": {"elevation": 3150, "height": 3000},
                "ground": {"elevation": 0, "height": 3000},
            },
            "spaces": {
                "ground": [
                    {"name": "living", "bounds": [0, 6000, 0, 4500]},
                    {"name": "kitchen", "bounds": [6000, 10000, 0, 3500]},
                ],
                "first": [
                    {"name": "master", "bounds": [0, 5000, 0, 4000]},
                    {"name": "corridor", "bounds": [2500, 7000, 3500, 5500]},
                ],
            },
            "doors": {
                "ground": [
                    {"host": "living_south", "width": 1200, "height": 2200},
                ],
                "first": [
                    {"host": "master_to_corridor", "width": 900, "height": 2100},
                ],
            },
            "windows": {
                "ground": [
                    {"host": "living_south", "width": 1500, "height": 1200, "sill_height": 900},
                ],
                "first": [
                    {"host": "master_south", "width": 1500, "height": 1200, "sill_height": 900},
                ],
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="top-level-storey-maps",
        design_brief=design_brief,
    )

    assert expected["storeys"] == [
        {"id": "storey-1", "source_key": "ground", "elevation_mm": 0},
        {"id": "storey-2", "source_key": "first", "elevation_mm": 3150},
    ]
    assert expected["space_counts_by_storey"] == {"storey-1": 2, "storey-2": 2}
    assert expected["door_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["window_counts_by_storey"] == {"storey-1": 1, "storey-2": 1}
    assert expected["total_counts"] == {
        "IfcBuildingStorey": 2,
        "IfcSpace": 4,
        "IfcDoor": 2,
        "IfcWindow": 2,
    }
    assert expected["spaces"][0]["dimensions_mm"] == [6000, 4500]
    assert expected["spaces"][0]["origin_mm"] == [0, 0, 0]
    assert expected["spaces"][1]["dimensions_mm"] == [4000, 3500]
    assert expected["spaces"][1]["origin_mm"] == [6000, 0, 0]
    assert expected["spaces"][2]["storey"] == "storey-2"
    assert expected["doors"][1]["host_wall"] == "master_to_corridor"
    assert expected["windows"][1]["sill_height_mm"] == 900


def test_floor_map_does_not_invent_storey_height_or_slab_thickness():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "en",
        "known_facts": {
            "building": {},
            "spaces": {
                "storey_1": [{"name": "ground-room"}],
                "storey_2": [{"name": "upper-room"}],
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="no-invented-storey-dimensions",
        design_brief=design_brief,
    )

    assert all("elevation_mm" not in storey for storey in expected["storeys"])
    unresolved_paths = {
        item["path"] for item in expected["unresolved_expectations"]
    }
    assert "/known_facts/building/storey_height_mm" in unresolved_paths
    assert "/known_facts/building/slab_thickness_mm" in unresolved_paths


def test_floor_map_orders_arbitrary_numeric_storeys_without_two_storey_rules():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "en",
        "known_facts": {
            "building": {
                "storey_height_mm": 3000,
                "slab_thickness_mm": 150,
            },
            "spaces": {
                "storey_10": [{"name": "room-10"}],
                "storey_5": [{"name": "room-5"}],
                "storey_3": [{"name": "room-3"}],
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
    }

    expected = build_expected_facts(
        case_id="arbitrary-numeric-storeys",
        design_brief=design_brief,
    )

    assert [storey["source_key"] for storey in expected["storeys"]] == [
        "storey_3",
        "storey_5",
        "storey_10",
    ]
