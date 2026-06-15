from pathlib import Path


PROMPT = Path("prompts/agent/mimo-bim-json-v1.md")
ITERATIONS = Path("prompts/agent/mimo-bim-json-iterations.md")


def test_mimo_bim_json_prompt_preserves_live_io_contract():
    text = PROMPT.read_text(encoding="utf-8")

    assert "{{USER_REQUEST}}" in text
    assert "{{REFERENCE_JSON}}" in text
    assert "{{VALIDATION_FEEDBACK}}" in text
    assert "只输出一个完整 JSON 对象" in text
    assert "schema_version" in text
    assert "entities" in text
    assert "relationships" in text
    assert "不要输出 IFC" in text
    assert "IfcCartesianPoint" in text
    assert "IfcOwnerHistory" in text


def test_mimo_prompt_iteration_log_records_failure_and_next_contract():
    text = ITERATIONS.read_text(encoding="utf-8")

    assert "mimo-live-simple-room-001" in text
    assert "validation failed" in text
    assert "普通尺寸 JSON" in text
    assert "mimo-bim-json-v1.md" in text
    assert "保留 prompt 版本" in text
