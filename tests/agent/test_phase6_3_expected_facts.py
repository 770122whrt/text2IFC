import json
from pathlib import Path

from text2ifc_agent.expected_facts import (
    build_expected_facts,
    write_expected_facts,
)


ROOT = Path(__file__).resolve().parents[2]
THREE_STOREY_FIXTURE = (
    ROOT
    / "dataset/processed/agent-demo/phase6.3-gate-audit/non-two-storey-three-level/design-brief.json"
)


def test_expected_facts_extracts_complex_multi_storey_obligations(tmp_path):
    design_brief = _two_storey_design_brief()

    expected = build_expected_facts(
        case_id="complex-two-storey",
        design_brief=design_brief,
    )

    assert expected["schema_version"] == "text2ifc/expected-facts/1.0"
    assert expected["storey_count"] == 2
    assert expected["space_counts_by_storey"] == {"storey-1": 4, "storey-2": 5}
    assert expected["door_counts_by_storey"] == {
        "storey-1": 5,
        "storey-2": 4,
    }
    assert expected["window_counts_by_storey"] == {
        "storey-1": 4,
        "storey-2": 5,
    }
    assert expected["total_counts"] == {
        "IfcBuildingStorey": 2,
        "IfcSpace": 9,
        "IfcDoor": 9,
        "IfcWindow": 9,
    }
    assert expected["slabs"] == [
        {"id": "ground-floor-slab", "storey": "storey-1"},
        {"id": "second-floor-slab", "storey": "storey-2"},
    ]
    assert expected["roof"] == {"id": "roof-slab", "z_mm": 6150}
    assert expected["stairs"][0]["connects_storeys"] == ["storey-1", "storey-2"]
    assert expected["required_relationships"]["opening_fill"]["doors"] == 9
    assert expected["required_relationships"]["opening_fill"]["windows"] == 9
    assert expected["doors"][0]["host_wall"] == "living-south-wall"
    assert expected["doors"][0]["relative_position"] == "center"
    assert expected["source_paths"]["/known_facts/doors/0"] == ["turn-user-001"]


def test_expected_facts_three_storey_fixture_is_data_driven_and_reusable():
    design_brief = json.loads(THREE_STOREY_FIXTURE.read_text(encoding="utf-8"))

    expected = build_expected_facts(
        case_id="three-storey-scalability",
        design_brief=design_brief,
    )

    assert expected["storey_count"] == 3
    assert expected["space_counts_by_storey"] == {
        "storey-1": 1,
        "storey-2": 1,
        "storey-3": 1,
    }
    assert expected["door_counts_by_storey"] == {
        "storey-1": 1,
        "storey-2": 1,
        "storey-3": 1,
    }
    assert expected["fixture_reuse"]["intended_for"] == [
        "dynamic_gates",
        "route_decisions",
    ]


def test_write_expected_facts_persists_sidecar_without_mutating_design_brief(tmp_path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    design_brief = _two_storey_design_brief()
    original = json.loads(json.dumps(design_brief, sort_keys=True))

    output = write_expected_facts(
        case_dir=case_dir,
        case_id="persisted-expected-facts",
        design_brief=design_brief,
    )

    assert design_brief == original
    assert output == case_dir / "expected-facts.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["case_id"] == "persisted-expected-facts"
    assert payload["total_counts"]["IfcDoor"] == 9


def _two_storey_design_brief() -> dict:
    spaces = [
        {"id": "living", "storey": "storey-1"},
        {"id": "kitchen", "storey": "storey-1"},
        {"id": "bathroom-1", "storey": "storey-1"},
        {"id": "stair-room", "storey": "storey-1"},
        {"id": "main-bedroom", "storey": "storey-2"},
        {"id": "secondary-bedroom", "storey": "storey-2"},
        {"id": "study", "storey": "storey-2"},
        {"id": "bathroom-2", "storey": "storey-2"},
        {"id": "corridor", "storey": "storey-2"},
    ]
    doors = [
        {
            "id": "living-exterior-door",
            "storey": "storey-1",
            "host_wall": "living-south-wall",
            "relative_position": "center",
        },
        {"id": "living-kitchen-door", "storey": "storey-1"},
        {"id": "kitchen-north-door", "storey": "storey-1"},
        {"id": "bathroom-west-door", "storey": "storey-1"},
        {"id": "stair-east-door", "storey": "storey-1"},
        {"id": "main-bedroom-door", "storey": "storey-2"},
        {"id": "secondary-bedroom-door", "storey": "storey-2"},
        {"id": "study-door", "storey": "storey-2"},
        {"id": "bathroom-2-door", "storey": "storey-2"},
    ]
    windows = [
        *[
            {"id": f"storey-1-window-{index}", "storey": "storey-1"}
            for index in range(1, 5)
        ],
        *[
            {"id": f"storey-2-window-{index}", "storey": "storey-2"}
            for index in range(1, 6)
        ],
    ]
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "original_request": "complex two-storey fixture",
        "known_facts": {
            "storeys": [
                {"id": "storey-1", "elevation_mm": 0},
                {"id": "storey-2", "elevation_mm": 3150},
            ],
            "spaces": spaces,
            "doors": doors,
            "windows": windows,
            "slabs": [
                {"id": "ground-floor-slab", "storey": "storey-1"},
                {"id": "second-floor-slab", "storey": "storey-2"},
            ],
            "roof": {"id": "roof-slab", "z_mm": 6150},
            "stairs": [
                {
                    "id": "main-stair",
                    "connects_storeys": ["storey-1", "storey-2"],
                }
            ],
        },
        "fact_sources": [
            {
                "path": "/known_facts/doors/0",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["user:original-request"],
            }
        ],
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {"source_turns": ["turn-user-001"]},
    }
