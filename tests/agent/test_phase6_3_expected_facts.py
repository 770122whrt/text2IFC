import json
from pathlib import Path

import pytest

from text2ifc_agent.gate_audit_bundle import hash_json_file
from text2ifc_agent.expected_facts import (
    ExpectedFactsError,
    build_expected_facts,
    write_expected_facts,
)
from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore


ROOT = Path(__file__).resolve().parents[2]
THREE_STOREY_FIXTURE = (
    ROOT
    / "dataset/processed/agent-demo/phase6.3-gate-audit/non-two-storey-three-level/design-brief.json"
)
PHASE6_1_COMPLETE = (
    ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
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
        "IfcSlab": 2,
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


def test_expected_facts_reads_canonical_floor_slabs_and_vertical_datums():
    expected = build_expected_facts(
        case_id="canonical-datums",
        design_brief={
            "known_facts": {
                "storeys": [
                    {"id": "storey-1", "elevation_mm": 0},
                    {"id": "storey-2", "elevation_mm": 3150},
                ],
                "floor_slabs": [
                    {
                        "id": "ground-floor-slab",
                        "storey": "storey-1",
                        "top_elevation_mm": 0,
                        "thickness_mm": 150,
                    },
                    {
                        "id": "first-floor-slab",
                        "storey": "storey-2",
                        "top_elevation_mm": 3150,
                        "thickness_mm": 150,
                        "opening": {"bounds": "x=0..2000,y=4000..8000"},
                    },
                ],
                "roof_slab": {
                    "id": "roof-slab",
                    "bottom_elevation_mm": 6150,
                    "thickness_mm": 150,
                },
            }
        },
    )

    assert expected["slabs"] == [
        {
            "id": "ground-floor-slab",
            "storey": "storey-1",
            "top_elevation_mm": 0,
            "thickness_mm": 150,
        },
        {
            "id": "first-floor-slab",
            "storey": "storey-2",
            "top_elevation_mm": 3150,
            "thickness_mm": 150,
            "opening": {"bounds": "x=0..2000,y=4000..8000"},
        },
    ]
    assert expected["roof"]["bottom_elevation_mm"] == 6150


def test_expected_facts_projects_explicit_railings_as_linear_products():
    expected = build_expected_facts(
        case_id="difficult-railing-products",
        design_brief={
            "schema_version": "text2ifc/design-brief/2.0",
            "status": "ready",
            "known_facts": {
                "storeys": [
                    {"id": "storey-1", "elevation_mm": 0},
                    {"id": "storey-2", "elevation_mm": 3300},
                ],
                "railings": [
                    {
                        "id": "railing-atrium-north",
                        "ifc_class": "IfcRailing",
                        "storey": "storey-2",
                        "start_mm": [6000, 3000],
                        "end_mm": [12000, 3000],
                        "base_elevation_mm": 3300,
                        "height_mm": 1100,
                        "thickness_mm": 50,
                        "alignment_target": "void-atrium:north-edge",
                    },
                    {
                        "id": "railing-atrium-west",
                        "ifc_class": "IfcRailing",
                        "storey": "storey-2",
                        "start_mm": [6000, 0],
                        "end_mm": [6000, 3000],
                        "base_elevation_mm": 3300,
                        "height_mm": 1100,
                        "thickness_mm": 50,
                        "alignment_target": "void-atrium:west-edge",
                    },
                ],
            },
        },
    )

    assert expected["products"] == [
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
    assert expected["total_counts"]["IfcRailing"] == 2
    assert expected["required_relationships"]["containment"]["products"] == 2
    storey_package = next(
        package
        for package in expected["generation_package_manifest"]["packages"]
        if package["package_id"] == "package-storey-2"
    )
    assert {"railing-atrium-north", "railing-atrium-west"} <= set(
        storey_package["owned_component_ids"]
    )


def test_expected_facts_rejects_product_family_class_override():
    design_brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "known_facts": {
            "storeys": [{"id": "storey-2", "elevation_mm": 3300}],
            "railings": [
                {
                    "id": "railing-atrium-north",
                    "ifc_class": "IfcWall",
                    "storey": "storey-2",
                    "start_mm": [6000, 3000, 3300],
                    "end_mm": [12000, 3000, 3300],
                    "height_mm": 1100,
                    "thickness_mm": 50,
                }
            ],
        },
    }

    with pytest.raises(ExpectedFactsError, match="DESIGN_BRIEF_PRODUCT_CLASS_CONFLICT"):
        build_expected_facts(case_id="railing-class-conflict", design_brief=design_brief)


def test_incomplete_railing_product_blocks_package_generation():
    expected = build_expected_facts(
        case_id="incomplete-railing-product",
        design_brief={
            "schema_version": "text2ifc/design-brief/2.0",
            "status": "ready",
            "known_facts": {
                "storeys": [{"id": "storey-1", "elevation_mm": 0}],
                "railings": [
                    {
                        "id": "railing-incomplete",
                        "ifc_class": "IfcRailing",
                        "storey": "storey-missing",
                        "start_mm": [0, 0],
                        "height_mm": 1100,
                    }
                ],
            },
        },
    )

    manifest = expected["generation_package_manifest"]
    assert manifest["status"] == "draft_required"
    assert {
        (issue["code"], issue["path"])
        for issue in manifest["issues"]
    } >= {
        ("PACKAGE_COMPONENT_OWNER_UNRESOLVED", "/products/0/storey"),
        ("PACKAGE_PRODUCT_GEOMETRY_INCOMPLETE", "/products/0/geometry"),
    }


def test_expected_facts_projects_complete_single_storey_room_inventory():
    expected = build_expected_facts(
        case_id="easy-complete-room",
        design_brief={
            "schema_version": "text2ifc/design-brief/2.0",
            "status": "ready",
            "known_facts": {
                "storeys": [
                    {
                        "id": "storey-1",
                        "name": "一层",
                        "elevation_mm": 0,
                        "net_height_mm": 3000,
                        "spaces": [
                            {
                                "id": "space-room",
                                "name": "房间",
                                "bounds": {"x": [0, 6000], "y": [0, 4000]},
                            }
                        ],
                        "walls": {
                            "exterior": [
                                {"id": "wall-south", "side": "south", "thickness_mm": 300},
                                {"id": "wall-north", "side": "north", "thickness_mm": 300},
                                {"id": "wall-west", "side": "west", "thickness_mm": 300},
                                {"id": "wall-east", "side": "east", "thickness_mm": 300},
                            ],
                            "interior": [],
                        },
                        "doors": [
                            {"id": "door-south", "host_wall": "wall-south", "width_mm": 900}
                        ],
                        "windows": [
                            {"id": "window-north", "host_wall": "wall-north", "width_mm": 1200}
                        ],
                    }
                ]
            },
        },
    )

    assert expected["storey_count"] == 1
    assert expected["total_counts"] == {
        "IfcBuildingStorey": 1,
        "IfcSpace": 1,
        "IfcWall": 4,
        "IfcDoor": 1,
        "IfcWindow": 1,
    }
    local_package = next(
        package
        for package in expected["generation_package_manifest"]["packages"]
        if package["package_id"] == "package-storey-1"
    )
    assert set(local_package["owned_component_ids"]) >= {
        "wall-south",
        "wall-north",
        "wall-west",
        "wall-east",
        "space-room",
        "door-south",
        "window-north",
    }
    assert local_package["owned_relationship_ids"]


def test_ready_design_brief_cannot_silently_project_to_zero_storeys():
    with pytest.raises(ValueError, match="DESIGN_BRIEF_PROJECTION_EMPTY"):
        build_expected_facts(
            case_id="easy-singular-dialect-regression",
            design_brief={
                "schema_version": "text2ifc/design-brief/2.0",
                "status": "ready",
                "known_facts": {
                    "space": {"shape": "rectangle"},
                },
            },
        )


def test_expected_facts_migrates_complete_legacy_single_storey_room():
    design_brief = json.loads(
        (PHASE6_1_COMPLETE / "design-brief" / "design-brief.json").read_text(
            encoding="utf-8"
        )
    )

    expected = build_expected_facts(
        case_id="legacy-easy-complete-room",
        design_brief=design_brief,
    )

    assert expected["storey_count"] == 1
    assert expected["total_counts"] == {
        "IfcBuildingStorey": 1,
        "IfcSpace": 1,
        "IfcWall": 4,
        "IfcDoor": 1,
        "IfcWindow": 1,
    }
    assert expected["doors"][0]["host_wall"] == "wall-south"
    assert expected["windows"][0]["host_wall"] == "wall-north"


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


def test_ready_session_writes_expected_facts_before_gate_summary(tmp_path):
    root = tmp_path / "phase6.3-expected-flow"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="complex expected facts fixture")
    _write_ready_design_brief_call(session.run_dir, _two_storey_design_brief())
    store.mark_session_status(session.session_id, "ready")

    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "revise",
        "blocking": True,
        "deterministic_gate_status": "failed",
        "findings": [
            {
                "code": "EXPECTED_ENTITY_MISSING",
                "severity": "blocking",
                "message": "The single-room candidate does not satisfy two-storey expected facts.",
            }
        ],
        "evidence_paths": [
            "expected-facts.json",
            "gate-summary.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _SequenceLiveProvider(
        [candidate, audit, candidate, audit, candidate, audit]
    )

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "audit_blocked"
    expected_path = session.run_dir / "expected-facts.json"
    assert expected_path.is_file()
    gate_summary = json.loads(
        (session.run_dir / "gate-summary.json").read_text(encoding="utf-8")
    )
    prompt_inputs = json.loads(
        (session.run_dir / "audit" / "prompt-render-input.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate_summary["expected_facts_hash"] == hash_json_file(expected_path)
    assert prompt_inputs["EXPECTED_FACTS_HASH"] == hash_json_file(expected_path)


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


def _write_ready_design_brief_call(run_dir: Path, design_brief: dict) -> None:
    call_dir = run_dir / "calls" / "01-design-brief"
    design_dir = run_dir / "design-brief"
    call_dir.mkdir(parents=True)
    design_dir.mkdir(parents=True)
    for source in (PHASE6_1_COMPLETE / "design-brief").iterdir():
        if source.is_file():
            for target_dir in (call_dir, design_dir):
                (target_dir / source.name).write_text(
                    source.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
    text = json.dumps(design_brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    for target in (
        call_dir / "design-brief.json",
        design_dir / "design-brief.json",
        run_dir / "design-brief.json",
    ):
        target.write_text(text, encoding="utf-8")


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.call_count = 0

    def generate_live(self, *, session_id, prompt, schema, state):
        del prompt, schema, state
        self.call_count += 1
        payload = self.payloads.pop(0)
        text = json.dumps(payload, ensure_ascii=False)
        response = {
            "id": f"msg_phase63_expected_{self.call_count}",
            "type": "message",
            "role": "assistant",
            "model": "unit-test",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={
                "model": "unit-test",
                "max_tokens": 131072,
                "stream": True,
                "messages": [{"role": "user", "content": "<redacted-test-prompt>"}],
            },
            response=response,
            events=(),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "unit-test", "session_id": session_id},
            ),
        )
