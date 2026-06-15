from __future__ import annotations

from pathlib import Path

from text2ifc_quality.generated_ifc import check_generated_ifc


ROOT = Path(__file__).resolve().parents[2]
BAD_SIMPLE_ROOM = (
    ROOT / "dataset" / "processed" / "agent-demo" / "mimo-live-simple-room-v2" / "output.ifc"
)


SIMPLE_ROOM_EXPECTATION = {
    "case_id": "simple-room-fixed",
    "units": "METRE",
    "tolerance": 0.05,
    "walls": {
        "wall-south": {
            "axis": "x",
            "bbox": {"x": [0.0, 6.0], "y": [-0.1, 0.1], "z": [0.0, 3.0]},
        },
        "wall-north": {
            "axis": "x",
            "bbox": {"x": [0.0, 6.0], "y": [3.9, 4.1], "z": [0.0, 3.0]},
        },
        "wall-west": {
            "axis": "y",
            "bbox": {"x": [-0.1, 0.1], "y": [0.0, 4.0], "z": [0.0, 3.0]},
        },
        "wall-east": {
            "axis": "y",
            "bbox": {"x": [5.9, 6.1], "y": [0.0, 4.0], "z": [0.0, 3.0]},
        },
    },
}


def test_generated_ifc_gate_rejects_known_disconnected_simple_room() -> None:
    assert BAD_SIMPLE_ROOM.exists()

    result = check_generated_ifc(BAD_SIMPLE_ROOM, SIMPLE_ROOM_EXPECTATION)

    assert result.success is False
    codes = {issue["code"] for issue in result.issues}
    assert "WALL_ORIENTATION_MISMATCH" in codes
    assert "ROOM_ENCLOSURE_OPEN" in codes
