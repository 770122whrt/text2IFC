import json
from pathlib import Path

from scripts.agent.run_clarification_demo import DEFAULT_REQUEST, run_demo
from text2ifc_contract.validation_v2 import validate_v2_document


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_scripted_demo_asks_chinese_questions_and_writes_ifc(tmp_path: Path):
    result = run_demo(output_dir=tmp_path, check=True)

    assert result["success"] is True
    assert "矩形房间" in DEFAULT_REQUEST

    transcript = _load(tmp_path / "transcript.json")
    agent_turns = [turn for turn in transcript["turns"] if turn["role"] == "agent"]
    assert agent_turns
    for turn in agent_turns:
        assert 1 <= len(turn["question_ids"]) <= 3
        assert any("\u4e00" <= char <= "\u9fff" for char in turn["content"])

    state = _load(tmp_path / "state.json")
    assert state["original_request"] == DEFAULT_REQUEST
    assert state["status"] == "formal_ready"
    assert state["accepted_facts"]

    candidate = _load(tmp_path / "candidate.json")
    assert candidate["schema_version"] == "bim-json/2.0"
    assert candidate["ifc_schema"] == "IFC2X3"
    assert validate_v2_document(candidate) == []
    classes = [entity["ifc_class"] for entity in candidate["entities"]]
    assert classes.count("IfcWall") == 4
    assert "IfcSpace" in classes
    assert "IfcDoor" in classes
    assert "IfcWindow" in classes

    diagnostics = _load(tmp_path / "diagnostics.json")
    assert diagnostics["compiled_ifc"]["success"] is True
    assert diagnostics["compiled_ifc"]["reopen_success"] is True

    metrics = _load(tmp_path / "metrics.json")
    assert metrics["turn_count"] >= 3
    assert metrics["asked_question_count"] >= 1
    assert metrics["final_status"] == "formal_ready"
    assert metrics["compile_success"] is True

    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "output.ifc").exists()


def test_invalid_demo_writes_diagnostics_without_overwriting_ifc(tmp_path: Path):
    existing = tmp_path / "output.ifc"
    existing.write_text("existing-ifc-placeholder", encoding="utf-8")

    result = run_demo(output_dir=tmp_path, check=True, force_invalid=True)

    assert result["success"] is False
    assert existing.read_text(encoding="utf-8") == "existing-ifc-placeholder"
    diagnostics = _load(tmp_path / "diagnostics.json")
    assert diagnostics["compiled_ifc"]["attempted"] is False
    assert diagnostics["validation"]["issues"]

