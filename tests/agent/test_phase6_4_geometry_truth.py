from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def test_derives_shared_wall_segment_from_confirmed_space_bounds():
    expectation = build_design_geometry_expectation(
        case_id="two-storey-control",
        design_brief=_controlled_design_brief(),
        expected_facts=_controlled_expected_facts(),
    )

    wall = expectation["walls"]["storey-2-wall-landing-corridor"]

    assert wall["axis"] == "y"
    assert wall["bbox"] == {
        "x": [3.9, 4.1],
        "y": [4.0, 8.0],
        "z": [3.15, 6.15],
    }
    assert wall["source_fact_refs"] == [
        "/known_facts/storeys/1/spaces/2",
        "/known_facts/storeys/1/spaces/3",
        "/known_facts/storeys/1/walls/interior/0",
    ]


def test_derives_structural_slab_below_storey_top_elevation():
    expectation = build_design_geometry_expectation(
        case_id="two-storey-control",
        design_brief=_controlled_design_brief(),
        expected_facts=_controlled_expected_facts(),
    )

    slab = expectation["slabs"]["slab-storey-2-floor"]

    assert slab["bbox"] == {
        "x": [0.0, 10.0],
        "y": [0.0, 8.0],
        "z": [3.0, 3.15],
    }
    assert slab["datum"] == "storey_slab_top"
    assert slab["source_fact_refs"] == [
        "/known_facts/building/outer_bounds",
        "/known_facts/building/floor_slab_thickness_mm",
        "/known_facts/storeys/1/elevation_mm",
    ]


def _controlled_design_brief() -> dict:
    return {
        "known_facts": {
            "building": {
                "outer_bounds": "x=0..10000,y=0..8000",
                "wall_thickness_mm": 200,
                "floor_slab_thickness_mm": 150,
            },
            "storeys": [
                {
                    "id": "storey-1",
                    "elevation_mm": 0,
                    "net_height_mm": 3000,
                    "spaces": [],
                    "walls": {"interior": []},
                },
                {
                    "id": "storey-2",
                    "elevation_mm": 3150,
                    "net_height_mm": 3000,
                    "spaces": [
                        {"id": "master_bedroom", "bounding_box": "x=0..4000,y=0..4000"},
                        {"id": "bedroom_2", "bounding_box": "x=6000..10000,y=0..4000"},
                        {"id": "stair_landing", "bounding_box": "x=2000..4000,y=4000..8000"},
                        {"id": "corridor", "bounding_box": "x=4000..6000,y=0..8000"},
                    ],
                    "walls": {
                        "interior": [
                            {
                                "id": "storey-2-wall-landing-corridor",
                                "from": "stair_landing",
                                "to": "corridor",
                            }
                        ]
                    },
                },
            ],
        }
    }


def _controlled_expected_facts() -> dict:
    return {
        "storeys": [
            {"id": "storey-1", "elevation_mm": 0},
            {"id": "storey-2", "elevation_mm": 3150},
        ],
        "spaces": [
            {
                "id": "stair_landing",
                "storey": "storey-2",
                "bounding_box": "x=2000..4000,y=4000..8000",
            },
            {
                "id": "corridor",
                "storey": "storey-2",
                "bounding_box": "x=4000..6000,y=0..8000",
            },
        ],
    }
