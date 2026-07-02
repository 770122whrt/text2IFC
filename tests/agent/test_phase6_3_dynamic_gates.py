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
