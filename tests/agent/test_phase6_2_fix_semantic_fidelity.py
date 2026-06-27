import json
from copy import deepcopy
from pathlib import Path

from text2ifc_agent.live_pipeline import run_candidate_gate_stage


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
