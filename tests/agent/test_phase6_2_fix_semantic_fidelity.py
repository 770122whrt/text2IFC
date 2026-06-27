import json
from copy import deepcopy
from pathlib import Path

from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = (
    ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
)


def test_candidate_gate_derives_wall_expectations_from_design_brief(tmp_path):
    case_dir = tmp_path / "semantic-gap"
    generator_dir = case_dir / "generator"
    generator_dir.mkdir(parents=True)
    candidate = _outside_boundary_gap_candidate()
    (generator_dir / "candidate.json").write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (case_dir / "design-brief.json").write_text(
        json.dumps(_outside_boundary_design_brief(), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    result = run_candidate_gate_stage(
        case_dir=case_dir,
        output_dir=case_dir,
        case_id="semantic-gap",
    )

    semantic_expectation = case_dir / "semantic-geometry-expectation.json"
    assert semantic_expectation.is_file()
    assert result["geometry_success"] is False
    feedback = json.loads((case_dir / "geometry-feedback.json").read_text(encoding="utf-8"))
    assert any(
        issue["code"] == "WALL_OUTSIDE_BOUNDARY_GAP"
        and issue["path"] == "/walls/wall-west"
        for issue in feedback["issues"]
    )


def test_unwaived_unsupported_door_opening_direction_blocks_formal_ifc(tmp_path):
    root = tmp_path / "phase6.2-fix-repl"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建房间，门向房间内部开启。")
    _write_ready_design_brief_with_opening_direction(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _SequenceLiveProvider([candidate, audit])

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )

    assert result.status == "draft_or_blocked"
    coverage = json.loads(
        (session.run_dir / "semantic-coverage.json").read_text(encoding="utf-8")
    )
    assert coverage["valid"] is False
    assert any(
        fact["path"] == "/known_facts/door/opening_direction"
        and fact["coverage_state"] == "unsupported_draft"
        for fact in coverage["facts"]
    )
    assert not (session.run_dir / "output.ifc").exists()


def _outside_boundary_design_brief() -> dict:
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "original_request": (
            "创建内部净尺寸为6米乘4米的矩形房间，墙体厚度0.2米，"
            "墙体位于房间边界外侧。"
        ),
        "known_facts": {
            "space": {
                "shape": "rectangle",
                "length_mm": 6000,
                "width_mm": 4000,
                "height_mm": 3000,
            },
            "walls": {
                "count": 4,
                "enclosure": "closed",
                "height_mm": 3000,
                "placement": "outside_boundary",
                "thickness_mm": 200,
            },
        },
        "missing_facts": [],
        "unsupported_requests": [],
        "ambiguities": [],
        "clarification_questions": [],
        "fact_sources": [],
        "provenance": {"source_turns": ["turn-user-001"]},
        "user_corrections": [],
    }


def _write_ready_design_brief_with_opening_direction(run_dir: Path) -> None:
    call_dir = run_dir / "calls" / "01-design-brief"
    call_dir.mkdir(parents=True)
    design_brief = json.loads(
        (PHASE6_1_COMPLETE / "design-brief" / "design-brief.json").read_text(
            encoding="utf-8"
        )
    )
    design_brief["known_facts"].setdefault("door", {})[
        "opening_direction"
    ] = "into_space"
    design_brief["fact_sources"].append(
        {
            "path": "/known_facts/door/opening_direction",
            "source_turns": ["turn-user-001"],
            "evidence_refs": ["capability:IFC2X3:IfcDoor"],
        }
    )
    for source in (PHASE6_1_COMPLETE / "design-brief").iterdir():
        if source.is_file():
            (call_dir / source.name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    (call_dir / "design-brief.json").write_text(
        json.dumps(design_brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "design-brief.json").write_text(
        json.dumps(design_brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.session_ids: list[str] = []

    def generate_live(self, *, session_id, prompt, schema, state):
        del prompt, schema, state
        index = len(self.session_ids)
        self.session_ids.append(session_id)
        payload = self.payloads[index]
        text = json.dumps(payload, ensure_ascii=False)
        response = {
            "id": f"msg_semantic_{index + 1}",
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


def _outside_boundary_gap_candidate() -> dict:
    candidate = deepcopy(
        json.loads(
            (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
                encoding="utf-8"
            )
        )
    )
    entity_by_id = {entity["id"]: entity for entity in candidate["entities"]}

    space = entity_by_id["space-1"]
    space["attributes"]["ObjectPlacement"]["origin"] = [3000, 2000, 0]
    space["attributes"]["Representation"]["profile"] = {
        "kind": "rectangle",
        "x": 6000,
        "y": 4000,
    }

    _set_wall(entity_by_id["wall-south"], origin=[3000, -200, 0], ref=[1, 0, 0], x=6400, y=200)
    _set_wall(entity_by_id["wall-north"], origin=[3000, 4200, 0], ref=[1, 0, 0], x=6400, y=200)
    _set_wall(entity_by_id["wall-west"], origin=[-200, 2000, 0], ref=[0, 1, 0], x=4000, y=200)
    _set_wall(entity_by_id["wall-east"], origin=[6200, 2000, 0], ref=[0, 1, 0], x=4000, y=200)
    return candidate


def _set_wall(
    wall: dict,
    *,
    origin: list[int],
    ref: list[int],
    x: int,
    y: int,
) -> None:
    wall["attributes"]["ObjectPlacement"]["origin"] = origin
    wall["attributes"]["ObjectPlacement"]["ref_direction"] = ref
    wall["attributes"]["Representation"]["profile"]["x"] = x
    wall["attributes"]["Representation"]["profile"]["y"] = y
