import json
from copy import deepcopy
from pathlib import Path

from text2ifc_agent.failure_routing import assess_repair_eligibility
from text2ifc_agent.generator import validate_generation_document
from text2ifc_agent.live_pipeline import run_repair_stage
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = (
    ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
)


def test_repair_stage_blocks_invalid_formal_recovery_that_changes_unreported_facts(tmp_path):
    invalid_candidate = _invalid_formal_candidate()
    repaired_candidate = _valid_complete_room_candidate()
    source_dir = _write_invalid_formal_generator_source(
        tmp_path / "generator",
        invalid_candidate=invalid_candidate,
    )
    provider = _RecordingLiveProvider(repaired_candidate)
    created = []

    def provider_factory():
        created.append("created")
        return provider

    output_dir = tmp_path / "repair"
    result = run_repair_stage(
        provider_factory=provider_factory,
        output_dir=output_dir,
        generator_source_dir=source_dir,
        case_id="invalid-formal-recovery",
    )

    assert created == ["created"]
    assert result["route"] == "blocked_failure"
    assert result["provider_call_count"] == 1
    assert result["valid"] is False
    assert (output_dir / "invalid-candidate.json").is_file()
    assert not (source_dir / "candidate.json").exists()
    route = json.loads((output_dir / "route.json").read_text(encoding="utf-8"))
    assert route["source_document_kind"] == "invalid_formal"
    assert route["source_document_path"] == "parsed-output.json"
    assert route["repair_attempts"][0]["result_status"] == "improved"
    assert route["blocking_reason"] == "repair fact-delta gate failed"
    assert {
        issue["code"] for issue in route["fact_delta_issues"]
    } == {"UNPERMITTED_FACT_DELTA"}
    assert "failure feedback has no previous candidate" not in json.dumps(route)
    assert json.loads(
        (output_dir / "repaired-candidate.json").read_text(encoding="utf-8")
    ) == repaired_candidate


def test_invalid_formal_contract_errors_are_repair_eligible_when_facts_are_known():
    result = assess_repair_eligibility(
        issues=[
            {
                "code": "MISSING_REPRESENTATION",
                "path": "/entities/11/attributes/Representation",
            },
            {
                "code": "UNSUPPORTED_RELATIONSHIP_CLASS",
                "path": "/relationships/4/ifc_class",
            },
            {
                "code": "UNSUPPORTED_RELATIONSHIP_CLASS",
                "path": "/relationships/5/ifc_class",
            },
        ],
        known_facts={
            "space": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
            "walls": {"thickness_mm": 200, "height_mm": 3000},
            "door": {"width_mm": 900, "height_mm": 2100, "host_wall": "south"},
        },
    )

    assert result["route"] == "repair_attempted"
    assert result["eligible"] is True
    assert result["issue_codes"] == [
        "MISSING_REPRESENTATION",
        "UNSUPPORTED_RELATIONSHIP_CLASS",
    ]


def test_open_polygon_profile_routes_to_repair_agent_with_machine_feedback(tmp_path):
    invalid_candidate = _open_polygon_candidate()
    repaired_candidate = deepcopy(invalid_candidate)
    wall = next(entity for entity in repaired_candidate["entities"] if entity["ifc_class"] == "IfcWall")
    points = wall["attributes"]["Representation"]["profile"]["points"]
    points.append(deepcopy(points[0]))
    source_dir = _write_invalid_formal_generator_source(
        tmp_path / "generator",
        invalid_candidate=invalid_candidate,
    )
    provider = _RecordingLiveProvider(repaired_candidate)
    created = []

    def provider_factory():
        created.append("created")
        return provider

    output_dir = tmp_path / "repair"
    result = run_repair_stage(
        provider_factory=provider_factory,
        output_dir=output_dir,
        generator_source_dir=source_dir,
        case_id="open-polygon-agent-repair",
    )

    assert created == ["created"]
    assert result["route"] == "repair_attempted"
    assert result["provider_call_count"] == 1
    assert result["valid"] is True
    assert "OPEN_POLYGON_PROFILE" in provider.prompt
    assert "/attributes/Representation/profile/points" in provider.prompt
    assert "closed ring" in provider.prompt
    repaired = json.loads(
        (output_dir / "repaired-candidate.json").read_text(encoding="utf-8")
    )
    wall = next(entity for entity in repaired["entities"] if entity["ifc_class"] == "IfcWall")
    points = wall["attributes"]["Representation"]["profile"]["points"]
    assert points == [[0, 0], [6000, 0], [6000, 4000], [0, 4000], [0, 0]]
    route = json.loads((output_dir / "route.json").read_text(encoding="utf-8"))
    assert route["repair_attempts"][0]["result_status"] == "improved"


def test_open_polygon_profile_is_repair_eligible_when_facts_are_known():
    result = assess_repair_eligibility(
        issues=[
            {
                "code": "OPEN_POLYGON_PROFILE",
                "path": "/entities/1/attributes/Representation/profile/points",
            }
        ],
        known_facts={"space": {"length_mm": 6000, "width_mm": 4000}},
    )

    assert result["route"] == "repair_attempted"
    assert result["eligible"] is True
    assert result["issue_codes"] == ["OPEN_POLYGON_PROFILE"]


def test_stair_schema_contract_errors_are_repair_eligible_when_facts_are_known():
    result = assess_repair_eligibility(
        issues=[
            {
                "code": "MISSING_OBJECT_PLACEMENT",
                "path": "/entities/35/attributes/ObjectPlacement",
            },
            {
                "code": "INVALID_IFC_ATTRIBUTE",
                "path": "/entities/36/attributes/NumberOfRisers",
            },
        ],
        known_facts={
            "stair": {
                "width_mm": 1000,
                "from_storey": "storey-1",
                "to_storey": "storey-2",
            },
            "storeys": [
                {"id": "storey-1", "elevation_mm": 0},
                {"id": "storey-2", "elevation_mm": 3150},
            ],
        },
    )

    assert result["route"] == "repair_attempted"
    assert result["eligible"] is True
    assert result["issue_codes"] == [
        "INVALID_IFC_ATTRIBUTE",
        "MISSING_OBJECT_PLACEMENT",
    ]


def _write_invalid_formal_generator_source(
    target: Path,
    *,
    invalid_candidate: dict,
) -> Path:
    target.mkdir(parents=True)
    design_dir = PHASE6_1_COMPLETE / "design-brief"
    for name in (
        "input.txt",
        "conversation.json",
        "design-brief.json",
        "context-selection.json",
    ):
        (target / name).write_text(
            (design_dir / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    validation = validate_generation_document(invalid_candidate)
    assert validation["status"] == "invalid"
    assert validation["classification"] == "formal"
    (target / "parsed-output.json").write_text(
        json.dumps(invalid_candidate, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (target / "validation.json").write_text(
        json.dumps(
            {
                "valid": False,
                "issue_count": len(validation["diagnostics"]),
                "issues": validation["diagnostics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (target / "metrics.json").write_text(
        json.dumps(
            {
                "case_id": "invalid-formal-recovery",
                "stage": "generator",
                "status": "invalid",
                "classification": "formal",
                "contract_valid": False,
                "evidence_class": "unit_test_fixture",
                "response_id": "msg_invalid_formal",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (target / "generator-context.json").write_text(
        json.dumps(
            {
                "schema_version": "text2ifc/generator-context/1.0",
                "capability_profile": {},
                "few_shots": [],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def _invalid_formal_candidate() -> dict:
    candidate = deepcopy(_valid_complete_room_candidate())
    door = next(entity for entity in candidate["entities"] if entity["ifc_class"] == "IfcDoor")
    door["attributes"].pop("Representation")
    candidate["relationships"].append(
        {
            "id": "agg-1",
            "ifc_class": "IfcRelAggregates",
            "attributes": {
                "RelatingObject": "building-1",
                "RelatedObjects": ["storey-1"],
            },
            "provenance": {"source": "text2ifc-generator"},
        }
    )
    candidate["relationships"].append(
        {
            "id": "contain-1",
            "ifc_class": "IfcRelContainedInSpatialStructure",
            "attributes": {
                "RelatingStructure": "storey-1",
                "RelatedElements": ["wall-south", "wall-north"],
            },
            "provenance": {"source": "text2ifc-generator"},
        }
    )
    return candidate


def _open_polygon_candidate() -> dict:
    candidate = deepcopy(_valid_complete_room_candidate())
    wall = next(entity for entity in candidate["entities"] if entity["ifc_class"] == "IfcWall")
    wall["attributes"]["Representation"]["profile"] = {
        "kind": "polygon",
        "points": [[0, 0], [6000, 0], [6000, 4000], [0, 4000]],
    }
    wall["attributes"]["Representation"]["depth"] = 3000
    return candidate


def _valid_complete_room_candidate() -> dict:
    return json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )


class _RecordingLiveProvider:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompt = ""

    def generate_live(self, *, session_id, prompt, schema, state):
        del schema, state
        self.prompt = prompt
        text = json.dumps(self.payload, ensure_ascii=False)
        response = {
            "id": "msg_repaired_formal",
            "type": "message",
            "role": "assistant",
            "model": "mimo-v2.5-pro",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={
                "model": "mimo-v2.5-pro",
                "max_tokens": 131072,
                "stream": True,
                "messages": [{"role": "user", "content": "<redacted-test-prompt>"}],
            },
            response=response,
            events=(
                {
                    "sequence": 0,
                    "event": "message_start",
                    "data": {"type": "message_start", "message": response},
                },
                {
                    "sequence": 1,
                    "event": "message_stop",
                    "data": {"type": "message_stop"},
                },
            ),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "mimo", "session_id": session_id},
            ),
        )
