import io

from text2ifc_agent import interactive_cli_flow
from text2ifc_agent.repl_chat import _print_ifc_live_progress


def test_failed_candidate_gate_emits_one_structured_event_per_issue():
    events: list[tuple[str, dict]] = []
    candidate_gates = {
        "valid": False,
        "geometry_feedback": {
            "issues": [
                {
                    "code": "SPACE_BBOX_MISMATCH",
                    "entity_ids": ["space-a"],
                    "expected": {"x": [0.0, 3.0]},
                    "actual": {"x": [-1.5, 1.5]},
                },
                {
                    "code": "STAIR_BBOX_MISMATCH",
                    "entity_ids": ["stair-a", "flight-a"],
                    "expected": {"y": [4.0, 7.0]},
                    "actual": {"y": [1.0, 4.0]},
                },
            ]
        },
    }

    interactive_cli_flow._emit_candidate_gate_progress(
        lambda stage, payload: events.append((stage, payload)),
        candidate_gates,
    )

    assert events[0] == ("candidate_gates", {"status": "failed"})
    assert events[1] == (
        "issue",
        {
            "status": "open",
            "issue_index": 1,
            "issue_total": 2,
            "code": "SPACE_BBOX_MISMATCH",
            "component": "space-a",
            "expected": {"x": [0.0, 3.0]},
            "actual": {"x": [-1.5, 1.5]},
            "owner": "generator",
            "route": "regenerate_json",
        },
    )
    assert events[2][1]["component"] == "stair-a, flight-a"


def test_cli_prints_structured_issue_evidence():
    stdout = io.StringIO()

    _print_ifc_live_progress(
        stage="issue",
        payload={
            "status": "open",
            "issue_index": 3,
            "issue_total": 13,
            "code": "INTERIOR_WALL_SHARED_BOUNDARY_MISMATCH",
            "component": "wall-a-b",
            "expected": {"x": [2.9, 3.1], "y": [0.0, 4.0]},
            "actual": {"x": [1.0, 2.0], "y": [0.0, 4.0]},
            "owner": "generator",
            "route": "regenerate_json",
        },
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert "[Issue 03/13]" in output
    assert "code: INTERIOR_WALL_SHARED_BOUNDARY_MISMATCH" in output
    assert "component: wall-a-b" in output
    assert 'expected: {"x": [2.9, 3.1], "y": [0.0, 4.0]}' in output
    assert 'actual: {"x": [1.0, 2.0], "y": [0.0, 4.0]}' in output
    assert "owner: generator" in output
    assert "route: regenerate_json" in output
    assert "status: open" in output
