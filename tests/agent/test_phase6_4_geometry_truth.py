import json

from text2ifc_agent.live_pipeline import _semantic_geometry_expectation_from_case
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


def test_derives_explicit_straight_wall_segment_bounds_for_irregular_envelope():
    design_brief = _controlled_design_brief()
    expected_facts = _controlled_expected_facts()
    expected_facts["walls"] = [
        {
            "id": "storey-1-wall-l-south",
            "storey": "storey-1",
            "bounds": {
                "x_min": 0,
                "x_max": 8000,
                "y_min": 0,
                "y_max": 200,
            },
            "height_mm": 3000,
        }
    ]

    expectation = build_design_geometry_expectation(
        case_id="l-shaped-envelope",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    wall = expectation["walls"]["storey-1-wall-l-south"]
    assert wall["axis"] == "x"
    assert wall["bbox"] == {
        "x": [0.0, 8.0],
        "y": [0.0, 0.2],
        "z": [0.0, 3.0],
    }
    assert wall["bbox_issue_code"] == "WALL_SEGMENT_MISMATCH"


def test_derives_wall_bbox_from_axis_aligned_centerline_endpoints_and_thickness():
    design_brief = _controlled_design_brief()
    expected_facts = _controlled_expected_facts()
    expected_facts["walls"] = [
        {
            "id": "storey-1-wall-l-east",
            "storey": "storey-1",
            "start_mm": [8000, 0],
            "end_mm": [8000, 5000],
            "thickness_mm": 200,
            "height_mm": 3000,
        }
    ]

    expectation = build_design_geometry_expectation(
        case_id="l-shaped-endpoints",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["walls"]["storey-1-wall-l-east"]["bbox"] == {
        "x": [7.9, 8.1],
        "y": [0.0, 5.0],
        "z": [0.0, 3.0],
    }


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
    assert slab["must_touch_walls"] == ["storey-1-wall-utility-corridor"]
    assert slab["source_fact_refs"] == [
        "/known_facts/building/outer_bounds",
        "/known_facts/building/floor_slab_thickness_mm",
        "/known_facts/storeys/1/elevation_mm",
    ]


def test_derives_generic_linear_product_geometry_from_railing_facts():
    design_brief = _controlled_design_brief()
    expected_facts = _controlled_expected_facts()
    expected_facts["products"] = [
        {
            "id": "railing-atrium-north",
            "ifc_class": "IfcRailing",
            "storey": "storey-2",
            "geometry": {
                "kind": "linear_segment",
                "start_mm": [6000, 3000, 3300],
                "end_mm": [12000, 3000, 3300],
                "height_mm": 1100,
                "thickness_mm": 50,
            },
            "alignment_target": "void-atrium:north-edge",
        },
        {
            "id": "railing-atrium-west",
            "ifc_class": "IfcRailing",
            "storey": "storey-2",
            "geometry": {
                "kind": "linear_segment",
                "start_mm": [6000, 0, 3300],
                "end_mm": [6000, 3000, 3300],
                "height_mm": 1100,
                "thickness_mm": 50,
            },
            "alignment_target": "void-atrium:west-edge",
        },
    ]

    expectation = build_design_geometry_expectation(
        case_id="difficult-railing-geometry",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["products"] == {
        "railing-atrium-north": {
            "ifc_class": "IfcRailing",
            "geometry_kind": "linear_segment",
            "bbox": {
                "x": [6.0, 12.0],
                "y": [2.975, 3.025],
                "z": [3.3, 4.4],
            },
            "bbox_issue_code": "LINEAR_PRODUCT_BBOX_MISMATCH",
            "alignment_target": "void-atrium:north-edge",
            "source_fact_refs": ["/products/0/geometry"],
        },
        "railing-atrium-west": {
            "ifc_class": "IfcRailing",
            "geometry_kind": "linear_segment",
            "bbox": {
                "x": [5.975, 6.025],
                "y": [0.0, 3.0],
                "z": [3.3, 4.4],
            },
            "bbox_issue_code": "LINEAR_PRODUCT_BBOX_MISMATCH",
            "alignment_target": "void-atrium:west-edge",
            "source_fact_refs": ["/products/1/geometry"],
        },
    }


def test_candidate_gate_uses_design_derived_geometry_expectation(tmp_path):
    design_brief = _controlled_design_brief()
    expected_facts = _controlled_expected_facts()
    (tmp_path / "design-brief.json").write_text(
        json.dumps(design_brief), encoding="utf-8"
    )
    (tmp_path / "expected-facts.json").write_text(
        json.dumps(expected_facts), encoding="utf-8"
    )

    expectation = _semantic_geometry_expectation_from_case(
        case_root=tmp_path,
        case_id="two-storey-control",
        candidate={"entities": []},
    )

    assert expectation is not None
    assert expectation["source"] == "design_brief_expected_facts"
    assert expectation["walls"]["storey-2-wall-landing-corridor"]["bbox"]["y"] == [
        4.0,
        8.0,
    ]


def test_derives_canonical_slab_roof_stair_and_opening_expectations():
    design_brief = _controlled_design_brief()
    known = design_brief["known_facts"]
    known["building"].pop("outer_bounds")
    known["building"]["outline"] = {
        "x_min": 0,
        "x_max": 10000,
        "y_min": 0,
        "y_max": 8000,
    }
    known["floor_slabs"] = [
        {
            "id": "first-floor-slab",
            "storey": "storey-2",
            "top_elevation_mm": 3150,
            "thickness_mm": 150,
            "opening": {"id": "stair-opening-1", "bounds": "x=0..2000,y=4000..8000"},
        }
    ]
    known["roof_slab"] = {
        "id": "roof-slab",
        "bottom_elevation_mm": 6150,
        "thickness_mm": 150,
    }
    known["stairs"] = [
        {
            "id": "stair-1",
            "bounds": "x=500..1500,y=4050..7950",
            "opening_bounds": "x=0..2000,y=4000..8000",
            "start_elevation_mm": 150,
            "end_elevation_mm": 3150,
        }
    ]
    expected_facts = _controlled_expected_facts()
    expected_facts.update(
        {
            "slabs": known["floor_slabs"],
            "roof": known["roof_slab"],
            "stairs": known["stairs"],
        }
    )

    expectation = build_design_geometry_expectation(
        case_id="canonical-two-storey",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["slabs"]["first-floor-slab"]["bbox"]["z"] == [3.0, 3.15]
    assert expectation["roof"]["roof-slab"]["bbox"]["z"] == [6.15, 6.3]
    assert expectation["stairs"]["stair-1"]["bbox"] == {
        "x": [0.5, 1.5],
        "y": [4.05, 7.95],
        "z": [0.15, 3.15],
    }
    assert expectation["stairs"]["stair-1"]["require_steps"] is True
    assert expectation["stairs"]["stair-1"]["bbox_issue_code"] == (
        "STAIR_BBOX_MISMATCH"
    )
    assert expectation["floor_openings"]["stair-opening-1"]["bbox"] == {
        "x": [0.0, 2.0],
        "y": [4.0, 8.0],
        "z": [3.0, 3.15],
    }
    assert expectation["floor_openings"]["stair-opening-1"][
        "bbox_issue_code"
    ] == "FLOOR_OPENING_BBOX_MISMATCH"


def test_stair_opening_bounds_must_contain_the_stair_plan_bounds():
    design_brief = _controlled_design_brief()
    stair = {
        "id": "stair-1",
        "bounds": {"x": [4300, 5300], "y": [4300, 7500]},
        "opening_bounds": {"x": [4500, 5200], "y": [4400, 7400]},
        "start_elevation_mm": 0,
        "end_elevation_mm": 3150,
    }
    design_brief["known_facts"]["stairs"] = [stair]
    expected_facts = {**_controlled_expected_facts(), "stairs": [stair]}

    expectation = build_design_geometry_expectation(
        case_id="stair-opening-too-small",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["complete"] is False
    assert {
        "path": "/known_facts/stairs/0/opening_bounds",
        "reason": "stair_opening_does_not_contain_stair_bounds",
        "source_fact_refs": ["/known_facts/stairs/0"],
    } in expectation["unresolved"]


def test_legacy_slab_identity_uses_confirmed_storey_datum_and_building_thickness():
    expectation = build_design_geometry_expectation(
        case_id="legacy-slab-id",
        design_brief=_controlled_design_brief(),
        expected_facts={
            **_controlled_expected_facts(),
            "slabs": [{"id": "first-floor-slab", "storey": "storey-2"}],
        },
    )

    assert expectation["slabs"]["first-floor-slab"]["bbox"] == {
        "x": [0.0, 10.0],
        "y": [0.0, 8.0],
        "z": [3.0, 3.15],
    }


def test_plural_slab_openings_preserve_explicit_identity_in_geometry_expectation():
    design_brief = _controlled_design_brief()
    slab = {
        "id": "first-floor-slab",
        "storey": "storey-2",
        "top_elevation_mm": 3150,
        "thickness_mm": 150,
        "openings": [
            {
                "id": "stair-opening-storey-2",
                "bounds": {"x_min": 6000, "x_max": 8000, "y_min": 1000, "y_max": 6000},
            }
        ],
    }
    expected_facts = {**_controlled_expected_facts(), "slabs": [slab]}

    expectation = build_design_geometry_expectation(
        case_id="plural-opening",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["floor_openings"]["stair-opening-storey-2"]["host_slab_id"] == (
        "first-floor-slab"
    )


def test_live_design_brief_plan_bounds_alias_keeps_stair_gate_active():
    design_brief = _controlled_design_brief()
    stair = {
        "id": "stair-1",
        "plan_bounds": "x=500..1500,y=4050..7950",
        "start_elevation_mm": 150,
        "end_elevation_mm": 3150,
    }
    design_brief["known_facts"]["stairs"] = [stair]
    expected_facts = {**_controlled_expected_facts(), "stairs": [stair]}

    expectation = build_design_geometry_expectation(
        case_id="live-plan-bounds-alias",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["stairs"]["stair-1"]["bbox"] == {
        "x": [0.5, 1.5],
        "y": [4.05, 7.95],
        "z": [0.15, 3.15],
    }


def test_candidate_gate_keeps_design_expectation_for_stair_only_case(tmp_path):
    design_brief = {
        "known_facts": {
            "stairs": [
                {
                    "id": "stair-1",
                    "bounds": "x=0..1000,y=0..3000",
                    "start_elevation_mm": 0,
                    "end_elevation_mm": 3000,
                }
            ]
        }
    }
    expected_facts = {"stairs": design_brief["known_facts"]["stairs"]}
    (tmp_path / "design-brief.json").write_text(
        json.dumps(design_brief), encoding="utf-8"
    )
    (tmp_path / "expected-facts.json").write_text(
        json.dumps(expected_facts), encoding="utf-8"
    )

    expectation = _semantic_geometry_expectation_from_case(
        case_root=tmp_path,
        case_id="stair-only",
        candidate={"entities": []},
    )

    assert expectation is not None
    assert expectation["source"] == "design_brief_expected_facts"
    assert "stair-1" in expectation["stairs"]


def test_canonical_bounds_and_connects_derive_spaces_and_shared_walls():
    design_brief = {
        "known_facts": {
            "building": {"wall_thickness_mm": 200},
            "storeys": [
                {
                    "id": "level-a",
                    "elevation_mm": 0,
                    "net_height_mm": 3000,
                    "spaces": [
                        {
                            "id": "space-a",
                            "bounds": {"x": [0, 3000], "y": [0, 4000]},
                        },
                        {
                            "id": "space-b",
                            "bounds": {"x": [3000, 6000], "y": [0, 4000]},
                        },
                    ],
                    "walls": {
                        "interior": [
                            {
                                "id": "wall-a-b",
                                "connects": ["space-a", "space-b"],
                                "thickness_mm": 200,
                            }
                        ]
                    },
                }
            ],
        }
    }
    expected_facts = {
        "storeys": [{"id": "level-a", "elevation_mm": 0}],
        "spaces": [
            {
                "id": "space-a",
                "storey": "level-a",
                "bounds": {"x": [0, 3000], "y": [0, 4000]},
            },
            {
                "id": "space-b",
                "storey": "level-a",
                "bounds": {"x": [3000, 6000], "y": [0, 4000]},
            },
        ],
        "walls": [
            {
                "id": "wall-a-b",
                "storey": "level-a",
                "connects": ["space-a", "space-b"],
                "thickness_mm": 200,
                "height_mm": 3000,
            }
        ],
    }

    expectation = build_design_geometry_expectation(
        case_id="canonical-shared-boundary",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["spaces"]["space-a"]["bbox"] == {
        "x": [0.0, 3.0],
        "y": [0.0, 4.0],
        "z": [0.0, 3.0],
    }
    assert expectation["walls"]["wall-a-b"]["axis"] == "y"
    assert expectation["walls"]["wall-a-b"]["bbox_issue_code"] == (
        "INTERIOR_WALL_SHARED_BOUNDARY_MISMATCH"
    )
    assert expectation["walls"]["wall-a-b"]["bbox"] == {
        "x": [2.9, 3.1],
        "y": [0.0, 4.0],
        "z": [0.0, 3.0],
    }


def test_canonical_polygon_derives_slab_and_roof_plan_bounds():
    polygon = [[0, 0], [6000, 0], [6000, 3000], [4000, 3000], [4000, 5000], [0, 5000], [0, 0]]
    design_brief = {
        "known_facts": {
            "building": {"wall_thickness_mm": 200},
            "storeys": [
                {"id": "level-a", "elevation_mm": 0, "net_height_mm": 3000}
            ],
        }
    }
    expected_facts = {
        "storeys": [{"id": "level-a", "elevation_mm": 0}],
        "slabs": [
            {
                "id": "slab-a",
                "storey": "level-a",
                "polygon": polygon,
                "top_elevation_mm": 0,
                "thickness_mm": 150,
            }
        ],
        "roof": {
            "id": "roof-a",
            "polygon": polygon,
            "bottom_elevation_mm": 3000,
            "thickness_mm": 150,
        },
    }

    expectation = build_design_geometry_expectation(
        case_id="canonical-polygon",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["slabs"]["slab-a"]["bbox"] == {
        "x": [0.0, 6.0],
        "y": [0.0, 5.0],
        "z": [-0.15, 0.0],
    }
    assert expectation["roof"]["roof-a"]["bbox"] == {
        "x": [0.0, 6.0],
        "y": [0.0, 5.0],
        "z": [3.0, 3.15],
    }


def test_explicit_wall_inherits_confirmed_building_thickness_and_storey_height():
    design_brief = {
        "known_facts": {
            "building": {"wall_thickness_mm": 200},
            "storeys": [
                {
                    "id": "level-a",
                    "elevation_mm": 3150,
                    "net_height_mm": 3000,
                }
            ],
        }
    }
    expected_facts = {
        "storeys": [{"id": "level-a", "elevation_mm": 3150}],
        "walls": [
            {
                "id": "wall-a",
                "storey": "level-a",
                "start_mm": [0, 4000],
                "end_mm": [6000, 4000],
            }
        ],
    }

    expectation = build_design_geometry_expectation(
        case_id="canonical-wall-inheritance",
        design_brief=design_brief,
        expected_facts=expected_facts,
    )

    assert expectation["complete"] is True
    assert expectation["unresolved"] == []
    assert expectation["walls"]["wall-a"]["bbox"] == {
        "x": [0.0, 6.0],
        "y": [3.9, 4.1],
        "z": [3.15, 6.15],
    }


def test_three_storey_wall_bounds_use_each_storeys_confirmed_height():
    storeys = [
        {"id": "storey-1", "elevation_mm": 0, "net_height_mm": 3000},
        {"id": "storey-2", "elevation_mm": 3150, "net_height_mm": 3200},
        {"id": "storey-3", "elevation_mm": 6500, "net_height_mm": 3000},
    ]
    walls = [
        {
            "id": f"wall-{index}",
            "storey": storey["id"],
            "start_mm": [0, 0],
            "end_mm": [6000, 0],
        }
        for index, storey in enumerate(storeys, start=1)
    ]

    expectation = build_design_geometry_expectation(
        case_id="nonuniform-three-storey",
        design_brief={
            "known_facts": {
                "building": {"wall_thickness_mm": 200},
                "storeys": storeys,
            }
        },
        expected_facts={
            "storeys": [
                {"id": item["id"], "elevation_mm": item["elevation_mm"]}
                for item in storeys
            ],
            "walls": walls,
        },
    )

    assert expectation["walls"]["wall-1"]["bbox"]["z"] == [0.0, 3.0]
    assert expectation["walls"]["wall-2"]["bbox"]["z"] == [3.15, 6.35]
    assert expectation["walls"]["wall-3"]["bbox"]["z"] == [6.5, 9.5]


def test_required_geometry_with_unresolved_facts_is_marked_incomplete():
    expectation = build_design_geometry_expectation(
        case_id="incomplete-required-geometry",
        design_brief={
            "known_facts": {
                "building": {"wall_thickness_mm": 200},
                "storeys": [
                    {
                        "id": "level-a",
                        "elevation_mm": 0,
                        "net_height_mm": 3000,
                        "spaces": [
                            {
                                "id": "space-a",
                                "bounds": {"x": [0, 3000], "y": [0, 4000]},
                            }
                        ],
                        "walls": {
                            "interior": [
                                {
                                    "id": "wall-unresolved",
                                    "connects": ["space-a", "space-missing"],
                                }
                            ]
                        },
                    }
                ],
            }
        },
        expected_facts={
            "storeys": [{"id": "level-a", "elevation_mm": 0}],
            "spaces": [
                {
                    "id": "space-a",
                    "storey": "level-a",
                    "bounds": {"x": [0, 3000], "y": [0, 4000]},
                }
            ],
            "walls": [
                {
                    "id": "wall-unresolved",
                    "storey": "level-a",
                    "connects": ["space-a", "space-missing"],
                    "height_mm": 3000,
                    "thickness_mm": 200,
                }
            ],
        },
    )

    assert expectation["complete"] is False
    assert expectation["unresolved"] == [
        {
            "path": "/known_facts/storeys/0/walls/interior/0",
            "reason": "shared_boundary_not_unique_or_wall_thickness_missing",
            "source_fact_refs": [
                "/known_facts/storeys/0/spaces/0",
                "/known_facts/storeys/0/walls/interior/0",
            ],
        }
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
                    "spaces": [
                        {"id": "utility", "bounding_box": "x=2000..4000,y=4000..8000"},
                        {"id": "corridor", "bounding_box": "x=4000..6000,y=0..8000"},
                    ],
                    "walls": {
                        "interior": [
                            {
                                "id": "storey-1-wall-utility-corridor",
                                "from": "utility",
                                "to": "corridor",
                            }
                        ]
                    },
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
