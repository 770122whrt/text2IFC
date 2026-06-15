from __future__ import annotations

import json
import subprocess
import sys
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


def test_generated_ifc_gate_cli_emits_machine_readable_failure(
    tmp_path: Path,
) -> None:
    expectation_path = tmp_path / "expectation.json"
    expectation_path.write_text(
        json.dumps(SIMPLE_ROOM_EXPECTATION, sort_keys=True),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/ifc_quality/check_generated_ifc.py",
            "--ifc",
            str(BAD_SIMPLE_ROOM),
            "--expectation",
            str(expectation_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["success"] is False
    codes = {issue["code"] for issue in payload["issues"]}
    assert "WALL_ORIENTATION_MISMATCH" in codes
