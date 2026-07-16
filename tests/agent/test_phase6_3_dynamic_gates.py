import json
from pathlib import Path

from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.gate_audit_bundle import write_gate_summary


ROOT = Path(__file__).resolve().parents[2]
THREE_STOREY_FIXTURE = (
    ROOT
    / "dataset/processed/agent-demo/phase6.3-gate-audit/non-two-storey-three-level/design-brief.json"
)


def test_dynamic_gates_match_legacy_semantic_space_id_once_with_evidence():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[],
        windows=[],
    )
    expected["spaces"] = [
        {"id": "living_room", "storey": "storey-1"}
    ]
    expected["space_counts_by_storey"] = {"storey-1": 1}
    expected["total_counts"]["IfcSpace"] = 1
    expected["required_relationships"]["containment"]["spaces"] = 1
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[],
        doors=[],
        windows=[],
        include_opening_relationships=True,
    )
    candidate["entities"].append(
        _entity("space-storey-1-living-room", "IfcSpace", "storey-1")
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    storey_gate = gates["dynamic_storey_containment"]
    assert storey_gate["status"] == "passed"
    assert storey_gate["entity_matches"] == [
        {
            "collection": "spaces",
            "expected_id": "living_room",
            "candidate_id": "space-storey-1-living-room",
            "match_basis": "unique_semantic_alias",
        }
    ]


def test_dynamic_gates_fail_missing_requested_second_floor_doors():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2"],
        doors=[
            {"id": "door-1", "storey": "storey-1", "host_wall": "wall-1"},
            {"id": "door-2a", "storey": "storey-2", "host_wall": "wall-2a"},
            {"id": "door-2b", "storey": "storey-2", "host_wall": "wall-2b"},
            {"id": "door-2c", "storey": "storey-2", "host_wall": "wall-2c"},
            {"id": "door-2d", "storey": "storey-2", "host_wall": "wall-2d"},
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[("wall-1", "storey-1")],
        doors=[("door-1", "storey-1", "wall-1")],
        windows=[],
        include_opening_relationships=True,
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_entity_completeness"]["status"] == "failed"
    assert "EXPECTED_ENTITY_MISSING" in gates["dynamic_entity_completeness"][
        "issue_codes"
    ]
    assert gates["dynamic_storey_containment"]["status"] == "failed"
    assert any(
        issue["path"] == "/doors/storey-2"
        for issue in gates["dynamic_storey_containment"]["issues"]
    )


def test_dynamic_gates_reject_component_name_that_explicitly_names_another_storey():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2"], doors=[], windows=[]
    )
    expected["storeys"] = [
        {"id": "storey-1", "name": "首层"},
        {"id": "storey-2", "name": "二层"},
    ]
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[("storey-2-wall-east", "storey-2")],
        doors=[],
        windows=[],
        include_opening_relationships=True,
    )
    _entity_by_id(candidate, "storey-2-wall-east")["attributes"]["Name"] = "首层东外墙"

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    gate = gates["dynamic_storey_name_consistency"]
    assert gate["status"] == "failed"
    assert gate["issues"] == [
        {
            "code": "STOREY_NAME_CONFLICT",
            "path": "/entities/storey-2-wall-east/attributes/Name",
            "entity_id": "storey-2-wall-east",
            "target_entity_ids": ["storey-2-wall-east"],
            "actual_name": "首层东外墙",
            "expected_storey": "storey-2",
            "expected_storey_name": "二层",
            "conflicting_storey": "storey-1",
            "conflicting_storey_name": "首层",
        }
    ]


def test_dynamic_gates_allow_neutral_or_correct_storey_component_names():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2"], doors=[], windows=[]
    )
    expected["storeys"] = [
        {"id": "storey-1", "name": "首层"},
        {"id": "storey-2", "name": "二层"},
    ]
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[
            ("storey-2-wall-east", "storey-2"),
            ("storey-2-wall-west", "storey-2"),
        ],
        doors=[],
        windows=[],
        include_opening_relationships=True,
    )
    _entity_by_id(candidate, "storey-2-wall-east")["attributes"]["Name"] = "二层东外墙"
    _entity_by_id(candidate, "storey-2-wall-west")["attributes"]["Name"] = "西外墙"

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_storey_name_consistency"]["status"] == "passed"


def test_dynamic_gates_require_all_expected_walls_on_their_declared_storeys():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2"], doors=[], windows=[]
    )
    expected["walls"] = [
        {"id": "wall-1-a", "storey": "storey-1"},
        {"id": "wall-1-b", "storey": "storey-1"},
        {"id": "wall-2-a", "storey": "storey-2"},
    ]
    expected["total_counts"]["IfcWall"] = 3
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[("wall-1-a", "storey-1"), ("wall-2-a", "storey-1")],
        doors=[],
        windows=[],
        include_opening_relationships=True,
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_entity_completeness"]["status"] == "failed"
    assert any(
        issue["ifc_class"] == "IfcWall" and issue["expected"] == 3
        for issue in gates["dynamic_entity_completeness"]["issues"]
    )
    assert gates["dynamic_storey_containment"]["status"] == "failed"
    assert any(
        issue.get("path") == "/walls/wall-2-a/storey"
        and issue.get("expected_storey") == "storey-2"
        and issue.get("actual_storey") == "storey-1"
        for issue in gates["dynamic_storey_containment"]["issues"]
    )


def test_dynamic_gates_count_generic_railing_products():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2"], doors=[], windows=[]
    )
    expected["products"] = [
        {
            "id": "railing-atrium-north",
            "ifc_class": "IfcRailing",
            "storey": "storey-2",
        },
        {
            "id": "railing-atrium-west",
            "ifc_class": "IfcRailing",
            "storey": "storey-2",
        },
    ]
    expected["total_counts"]["IfcRailing"] = 2
    expected["required_relationships"]["containment"]["products"] = 2
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[],
        doors=[],
        windows=[],
        include_opening_relationships=True,
    )
    candidate["entities"].append(
        _entity("railing-atrium-north", "IfcRailing", "storey-2")
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    gate = gates["dynamic_entity_completeness"]
    assert gate["status"] == "failed"
    assert {
        "code": "EXPECTED_ENTITY_MISSING",
        "path": "/products",
        "ifc_class": "IfcRailing",
        "expected": 2,
        "actual": 1,
    } in gate["issues"]


def test_dynamic_gates_require_generic_product_on_declared_storey():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2"], doors=[], windows=[]
    )
    expected["products"] = [
        {
            "id": "railing-atrium-north",
            "ifc_class": "IfcRailing",
            "storey": "storey-2",
        }
    ]
    expected["total_counts"]["IfcRailing"] = 1
    expected["required_relationships"]["containment"]["products"] = 1
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[],
        doors=[],
        windows=[],
        include_opening_relationships=True,
    )
    candidate["entities"].append(
        _entity("railing-atrium-north", "IfcRailing", "storey-1")
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    gate = gates["dynamic_storey_containment"]
    assert gate["status"] == "failed"
    assert {
        "code": "STOREY_CONTAINMENT_MISMATCH",
        "path": "/products/railing-atrium-north/storey",
        "expected_storey": "storey-2",
        "actual_storey": "storey-1",
    } in gate["issues"]


def test_dynamic_gates_fail_windows_without_void_fill_relationships():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[],
        windows=[
            {"id": "window-1", "storey": "storey-1", "host_wall": "wall-north"},
            {"id": "window-2", "storey": "storey-1", "host_wall": "wall-north"},
        ],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-north", "storey-1")],
        doors=[],
        windows=[
            ("window-1", "storey-1", "wall-north"),
            ("window-2", "storey-1", "wall-north"),
        ],
        include_opening_relationships=False,
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_opening_fill"]["status"] == "failed"
    assert "VOID_RELATIONSHIP_MISSING" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]
    assert "OPENING_FILL_RELATIONSHIP_MISSING" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]


def test_dynamic_gates_fail_openings_outside_host_wall_local_bounds():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[],
        windows=[
            {
                "id": "window-north",
                "storey": "storey-1",
                "host_wall": "wall-north",
            }
        ],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-north", "storey-1")],
        doors=[],
        windows=[("window-north", "storey-1", "wall-north")],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "wall-north", x=10000, y=200)
    _set_rectangle(candidate, "opening-window-north", x=1200, y=200)
    _set_placement_origin(candidate, "opening-window-north", [8500, 0, 900])

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_opening_fill"]["status"] == "failed"
    assert "OPENING_HOST_LOCAL_BOUNDS_MISMATCH" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]
    issue = next(
        issue
        for issue in gates["dynamic_opening_fill"]["issues"]
        if issue["code"] == "OPENING_HOST_LOCAL_BOUNDS_MISMATCH"
    )
    assert issue["opening_id"] == "opening-window-north"
    assert issue["host_wall"] == "wall-north"
    assert issue["opening_origin"] == [8500, 0, 900]
    assert issue["recommended_action"] == "align_opening_frame_to_host"
    assert issue["coordinate_contract"] == {
        "local_x": "opening width along the host wall",
        "local_y": "opening thickness through the host wall",
        "local_z": "opening height",
    }
    assert issue["expected_object_placement_ref_direction"] == [1, 0, 0]
    assert issue["expected_representation_direction"] == [0, 0, 1]


def test_dynamic_gates_fail_filling_that_repeats_parent_wall_rotation():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[
            {
                "id": "door-internal",
                "storey": "storey-1",
                "host_wall": "wall-internal",
            }
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-internal", "storey-1")],
        doors=[("door-internal", "storey-1", "wall-internal")],
        windows=[],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "wall-internal", x=3500, y=200)
    _set_rectangle(candidate, "opening-door-internal", x=900, y=200)
    _set_placement_origin(candidate, "opening-door-internal", [0, 1750, 0])
    _set_ref_direction(candidate, "opening-door-internal", [0, 1, 0])
    _set_ref_direction(candidate, "door-internal", [0, 1, 0])

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_opening_fill"]["status"] == "failed"
    assert "FILLING_RELATIVE_ROTATION_MISMATCH" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]


def test_dynamic_gates_compare_transformed_opening_bounds_with_host_wall():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[],
        windows=[
            {"id": "window-north", "storey": "storey-1", "host_wall": "wall-north"}
        ],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-north", "storey-1")],
        doors=[],
        windows=[("window-north", "storey-1", "wall-north")],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "wall-north", x=10000, y=200)
    _set_rectangle(candidate, "opening-window-north", x=1200, y=400)
    _set_placement_origin(candidate, "opening-window-north", [0, 0, 900])

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert "OPENING_HOST_LOCAL_BOUNDS_MISMATCH" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]
    issue = next(
        issue
        for issue in gates["dynamic_opening_fill"]["issues"]
        if issue["code"] == "OPENING_HOST_LOCAL_BOUNDS_MISMATCH"
    )
    assert issue["path"].endswith("/attributes/Representation")
    assert issue["target_entity_ids"] == ["opening-window-north"]
    assert issue["opening_bounds"]["size"] == [1200.0, 400.0, 3000.0]
    assert issue["host_bounds"]["size"] == [10000.0, 200.0, 3000.0]


def test_dynamic_gates_fail_filling_with_wrong_placement_parent():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[
            {"id": "door-internal", "storey": "storey-1", "host_wall": "wall-internal"}
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-internal", "storey-1")],
        doors=[("door-internal", "storey-1", "wall-internal")],
        windows=[],
        include_opening_relationships=True,
    )
    _entity_by_id(candidate, "door-internal")["attributes"]["ObjectPlacement"][
        "relative_to"
    ] = "wall-internal"

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert "FILLING_PLACEMENT_CHAIN_MISMATCH" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]


def test_dynamic_gates_fail_filling_bounds_outside_opening():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[
            {"id": "door-internal", "storey": "storey-1", "host_wall": "wall-internal"}
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-internal", "storey-1")],
        doors=[("door-internal", "storey-1", "wall-internal")],
        windows=[],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "opening-door-internal", x=900, y=200)
    _set_rectangle(candidate, "door-internal", x=900, y=200)
    _set_placement_origin(candidate, "door-internal", [100, 0, 0])

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert "FILLING_OPENING_BOUNDS_MISMATCH" in gates["dynamic_opening_fill"][
        "issue_codes"
    ]
    issue = next(
        item
        for item in gates["dynamic_opening_fill"]["issues"]
        if item["code"] == "FILLING_OPENING_BOUNDS_MISMATCH"
    )
    assert issue["recommended_action"] == "align_filling_to_opening_frame"
    assert issue["correction_constraints"] == {
        "placement": "Use identity ref_direction [1,0,0] relative to the opening.",
        "profile": "Use profile.x=semantic width and profile.y=assembly thickness.",
        "extrusion": "Use depth=semantic height and direction=[0,0,1].",
        "forbidden": "Do not swap width, thickness, and height to chase one bounds check.",
    }


def test_dynamic_gates_enforce_expected_host_centerline_alignment():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[
            {
                "id": "door-south",
                "storey": "storey-1",
                "host_wall": "wall-south",
                "alignment": "host_centerline",
            }
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-south", "storey-1")],
        doors=[("door-south", "storey-1", "wall-south")],
        windows=[],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "wall-south", x=8000, y=200)
    _set_rectangle(candidate, "opening-door-south", x=900, y=200)
    _set_rectangle(candidate, "door-south", x=900, y=100)
    _set_placement_origin(candidate, "opening-door-south", [100, 0, 0])

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    issue = next(
        item
        for item in gates["dynamic_opening_fill"]["issues"]
        if item["code"] == "OPENING_HOST_ALIGNMENT_MISMATCH"
    )
    assert issue["path"] == "/entities/opening-door-south/attributes/ObjectPlacement/origin/0"
    assert issue["target_entity_ids"] == ["opening-door-south"]
    assert issue["expected_local_x"] == 0.0
    assert issue["actual_local_x"] == 100.0
    assert issue["source_alignment"] == "host_centerline"


def test_dynamic_gates_allow_equivalent_opening_and_filling_representation_dialects():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[
            {"id": "door-south", "storey": "storey-1", "host_wall": "wall-south"}
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-south", "storey-1")],
        doors=[("door-south", "storey-1", "wall-south")],
        windows=[],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "wall-south", x=8000, y=200)
    _set_rectangle(candidate, "opening-door-south", x=900, y=200)
    opening_representation = _entity_by_id(candidate, "opening-door-south")[
        "attributes"
    ]["Representation"]
    opening_representation["depth"] = 2100
    opening_representation["direction"] = [0, 0, 1]
    _set_rectangle(candidate, "door-south", x=900, y=2100)
    filling_representation = _entity_by_id(candidate, "door-south")["attributes"][
        "Representation"
    ]
    filling_representation["depth"] = 200
    filling_representation["direction"] = [0, 1, 0]
    _set_placement_origin(candidate, "door-south", [0, -100, 1050])

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_opening_fill"]["status"] == "passed"


def test_dynamic_gates_target_opening_when_wall_normal_dialect_lacks_origin_compensation():
    expected = _expected_facts(
        storeys=["storey-1"],
        doors=[
            {"id": "door-south", "storey": "storey-1", "host_wall": "wall-south"}
        ],
        windows=[],
    )
    candidate = _candidate(
        storeys=["storey-1"],
        walls=[("wall-south", "storey-1")],
        doors=[("door-south", "storey-1", "wall-south")],
        windows=[],
        include_opening_relationships=True,
    )
    _set_rectangle(candidate, "wall-south", x=8000, y=200)
    _set_rectangle(candidate, "opening-door-south", x=900, y=2100)
    opening_representation = _entity_by_id(candidate, "opening-door-south")[
        "attributes"
    ]["Representation"]
    opening_representation["depth"] = 200
    opening_representation["direction"] = [0, 1, 0]
    _set_rectangle(candidate, "door-south", x=900, y=2100)
    filling_representation = _entity_by_id(candidate, "door-south")["attributes"][
        "Representation"
    ]
    filling_representation["depth"] = 200
    filling_representation["direction"] = [0, 1, 0]

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    issues = gates["dynamic_opening_fill"]["issues"]
    issue = next(
        item for item in issues if item["code"] == "OPENING_HOST_LOCAL_BOUNDS_MISMATCH"
    )
    assert issue["path"] == "/entities/opening-door-south/attributes/ObjectPlacement/origin"
    assert issue["target_entity_ids"] == ["opening-door-south"]
    assert issue["opening_bounds"]["size"] == [900.0, 200.0, 2100.0]
    assert issue["host_bounds"]["size"] == [8000.0, 200.0, 3000.0]
    assert issue["allowed_origin_ranges"] == {
        "x": [-3550.0, 3550.0],
        "y": [-100.0, -100.0],
        "z": [1050.0, 1950.0],
    }
    assert not any(
        item["code"] == "FILLING_OPENING_BOUNDS_MISMATCH" for item in issues
    )


def test_dynamic_gates_fail_cross_storey_host_mismatch():
    expected = _expected_facts(
        storeys=["storey-1", "storey-2", "storey-3"],
        doors=[],
        windows=[
            {
                "id": "window-3",
                "storey": "storey-3",
                "host_wall": "wall-l3-north",
            }
        ],
    )
    candidate = _candidate(
        storeys=["storey-1", "storey-2", "storey-3"],
        walls=[
            ("wall-l1-north", "storey-1"),
            ("wall-l3-north", "storey-3"),
        ],
        doors=[],
        windows=[("window-3", "storey-1", "wall-l1-north")],
        include_opening_relationships=True,
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_storey_containment"]["status"] == "failed"
    assert "STOREY_CONTAINMENT_MISMATCH" in gates["dynamic_storey_containment"][
        "issue_codes"
    ]
    assert "HOST_WALL_MISMATCH" in gates["dynamic_storey_containment"][
        "issue_codes"
    ]


def test_non_two_storey_fixture_reaches_dynamic_gate_logic():
    design_brief = json.loads(THREE_STOREY_FIXTURE.read_text(encoding="utf-8"))
    expected = build_expected_facts(
        case_id="three-storey-dynamic-gate",
        design_brief=design_brief,
    )
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        walls=[
            ("level-1-south-wall", "storey-1"),
            ("level-2-south-wall", "storey-2"),
        ],
        doors=[
            ("level-1-door", "storey-1", "level-1-south-wall"),
            ("level-2-door", "storey-2", "level-2-south-wall"),
        ],
        windows=[],
        include_opening_relationships=True,
    )

    gates = _by_name(evaluate_dynamic_gates(candidate=candidate, expected_facts=expected))

    assert gates["dynamic_entity_completeness"]["status"] == "failed"
    assert any(
        issue.get("expected_storey") == "storey-3"
        for issue in gates["dynamic_storey_containment"]["issues"]
    )


def test_gate_summary_includes_dynamic_expected_fact_gates(tmp_path):
    case_dir = tmp_path / "case"
    (case_dir / "generator").mkdir(parents=True)
    _write_json(
        case_dir / "generator" / "candidate.json",
        _candidate(
            storeys=["storey-1"],
            walls=[("wall-north", "storey-1")],
            doors=[],
            windows=[("window-1", "storey-1", "wall-north")],
            include_opening_relationships=False,
        ),
    )
    _write_json(
        case_dir / "expected-facts.json",
        _expected_facts(
            storeys=["storey-1"],
            doors=[],
            windows=[
                {
                    "id": "window-1",
                    "storey": "storey-1",
                    "host_wall": "wall-north",
                }
            ],
        ),
    )
    _write_json(case_dir / "generator" / "validation.json", {"valid": True, "issues": []})

    summary = write_gate_summary(case_dir=case_dir, case_id="dynamic-summary")
    gates = _by_name(summary["gates"])

    assert gates["dynamic_entity_completeness"]["status"] == "passed"
    assert gates["dynamic_opening_fill"]["status"] == "failed"
    assert summary["overall_status"] == "failed"


def _expected_facts(*, storeys: list[str], doors: list[dict], windows: list[dict]) -> dict:
    return {
        "schema_version": "text2ifc/expected-facts/1.0",
        "case_id": "dynamic-gates-test",
        "storeys": [{"id": storey} for storey in storeys],
        "storey_count": len(storeys),
        "spaces": [],
        "doors": doors,
        "windows": windows,
        "slabs": [],
        "roof": None,
        "stairs": [],
        "space_counts_by_storey": {},
        "door_counts_by_storey": _counts_by_storey(doors),
        "window_counts_by_storey": _counts_by_storey(windows),
        "total_counts": {
            "IfcBuildingStorey": len(storeys),
            "IfcSpace": 0,
            "IfcDoor": len(doors),
            "IfcWindow": len(windows),
        },
        "required_relationships": {
            "containment": {
                "storeys": len(storeys),
                "spaces": 0,
                "doors": len(doors),
                "windows": len(windows),
            },
            "opening_fill": {
                "doors": len(doors),
                "windows": len(windows),
            },
        },
    }


def _candidate(
    *,
    storeys: list[str],
    walls: list[tuple[str, str]],
    doors: list[tuple[str, str, str]],
    windows: list[tuple[str, str, str]],
    include_opening_relationships: bool,
) -> dict:
    entities = [_entity(storey, "IfcBuildingStorey", "building-1") for storey in storeys]
    entities.extend(_entity(wall_id, "IfcWall", storey) for wall_id, storey in walls)
    relationships = []
    for door_id, _storey, host_wall in doors:
        opening_id = f"opening-{door_id}"
        entities.append(_entity(opening_id, "IfcOpeningElement", host_wall))
        entities.append(_entity(door_id, "IfcDoor", opening_id))
        if include_opening_relationships:
            relationships.extend(_opening_relationships(door_id, opening_id, host_wall))
    for window_id, _storey, host_wall in windows:
        opening_id = f"opening-{window_id}"
        entities.append(_entity(opening_id, "IfcOpeningElement", host_wall))
        entities.append(_entity(window_id, "IfcWindow", opening_id))
        if include_opening_relationships:
            relationships.extend(_opening_relationships(window_id, opening_id, host_wall))
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": entities,
        "relationships": relationships,
        "provenance": {"source": "test-fixture"},
    }


def _entity(entity_id: str, ifc_class: str, relative_to: str) -> dict:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": {
            "ObjectPlacement": {
                "relative_to": relative_to,
                "origin": [0, 0, 0],
                "axis": [0, 0, 1],
                "ref_direction": [1, 0, 0],
            }
        },
        "property_sets": {},
        "provenance": {"source": "test-fixture"},
    }


def _set_rectangle(candidate: dict, entity_id: str, *, x: int, y: int) -> None:
    entity = _entity_by_id(candidate, entity_id)
    entity["attributes"]["Representation"] = {
        "kind": "extruded_profile",
        "depth": 3000,
        "direction": [0, 0, 1],
        "profile": {"kind": "rectangle", "x": x, "y": y},
    }


def _set_placement_origin(candidate: dict, entity_id: str, origin: list[int]) -> None:
    _entity_by_id(candidate, entity_id)["attributes"]["ObjectPlacement"][
        "origin"
    ] = origin


def _set_ref_direction(candidate: dict, entity_id: str, ref_direction: list[int]) -> None:
    _entity_by_id(candidate, entity_id)["attributes"]["ObjectPlacement"][
        "ref_direction"
    ] = ref_direction


def _entity_by_id(candidate: dict, entity_id: str) -> dict:
    return next(entity for entity in candidate["entities"] if entity["id"] == entity_id)


def _opening_relationships(element_id: str, opening_id: str, host_wall: str) -> list[dict]:
    return [
        {
            "id": f"void-{opening_id}",
            "ifc_class": "IfcRelVoidsElement",
            "attributes": {
                "RelatingBuildingElement": host_wall,
                "RelatedOpeningElement": opening_id,
            },
            "provenance": {"source": "test-fixture"},
        },
        {
            "id": f"fill-{opening_id}",
            "ifc_class": "IfcRelFillsElement",
            "attributes": {
                "RelatingOpeningElement": opening_id,
                "RelatedBuildingElement": element_id,
            },
            "provenance": {"source": "test-fixture"},
        },
    ]


def _counts_by_storey(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record["storey"]] = counts.get(record["storey"], 0) + 1
    return counts


def _by_name(gates: list[dict]) -> dict[str, dict]:
    return {gate["name"]: gate for gate in gates}


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
