from pathlib import Path


PROMPT = Path("prompts/agent/mimo-bim-json-v1.md")
PROMPT_V2 = Path("prompts/agent/mimo-bim-json-v2.md")
PROMPT_V3 = Path("prompts/agent/mimo-bim-json-v3.md")
ITERATIONS = Path("prompts/agent/mimo-bim-json-iterations.md")
DESIGN_BRIEF_V21 = Path("prompts/agent/design-brief-v2.1.md")
DESIGN_BRIEF_FEW_SHOTS = Path("prompts/agent/few-shots/design-brief-v2.json")
AUDIT_V2 = Path("prompts/agent/audit-v2.md")


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


def test_mimo_bim_json_v2_prompt_blocks_false_draft_for_complete_input():
    text = PROMPT_V2.read_text(encoding="utf-8")

    assert "{{USER_REQUEST}}" in text
    assert "{{REFERENCE_JSON}}" in text
    assert "{{VALIDATION_FEEDBACK}}" in text
    assert "信息足够时不要输出 Draft 字段" in text
    assert "entities 不得为空" in text
    assert "南墙中间" in text
    assert "北墙中间" in text
    assert "missing_facts" in text
    assert "clarification_targets" in text


def test_mimo_prompt_iteration_log_records_v1_false_draft_failure():
    text = ITERATIONS.read_text(encoding="utf-8")

    assert "mimo-live-simple-room-v1" in text
    assert "entities 为空" in text
    assert "mimo-bim-json-v2.md" in text


def test_mimo_prompt_iteration_log_records_v2_live_success():
    text = ITERATIONS.read_text(encoding="utf-8")

    assert "mimo-live-simple-room-v2" in text
    assert "validation_issue_count: 0" in text
    assert "compile_success: true" in text
    assert "output.ifc" in text


def test_mimo_bim_json_v3_prompt_encodes_geometry_gate_contract():
    text = PROMPT_V3.read_text(encoding="utf-8")

    assert "{{USER_REQUEST}}" in text
    assert "{{REFERENCE_JSON}}" in text
    assert "{{VALIDATION_FEEDBACK}}" in text
    assert "BIM JSON 2.0" in text
    assert "rectangle profile center-origin" in text
    assert "south/north walls" in text
    assert "east/west walls" in text
    assert "geometry failure feedback" in text
    assert "Do not output raw IFC" in text
    assert "IfcCartesianPoint" in text
    assert "IfcDirection" in text
    assert "IfcOwnerHistory" in text


def test_mimo_prompt_iteration_log_records_v3_geometry_gate_contract():
    text = ITERATIONS.read_text(encoding="utf-8")

    assert "mimo-bim-json-v3.md" in text
    assert "geometry gate" in text
    assert "rectangle profile center-origin" in text


def test_design_brief_v21_routes_user_unknown_answer_to_terminal_draft():
    text = DESIGN_BRIEF_V21.read_text(encoding="utf-8")
    few_shots = DESIGN_BRIEF_FEW_SHOTS.read_text(encoding="utf-8")

    assert "用户已经回答不知道" in text
    assert "不得继续追问同一个事实" in text
    assert "status" in few_shots
    assert "draft_required" in few_shots
    assert "我不知道墙体厚度" in few_shots
    assert '"clarification_questions": []' in few_shots


def test_design_brief_v21_enforces_question_target_consistency():
    text = DESIGN_BRIEF_V21.read_text(encoding="utf-8")

    assert "needs_clarification MUST include 1-3 clarification_questions" in text
    assert "Every clarification question target MUST reference an existing blocking item id" in text
    assert "Bind short numeric answers to the immediately preceding assistant question" in text
    assert "source_turns MUST use exact turn_id values already present in CONVERSATION" in text
 
def test_audit_v2_understands_parent_relative_centered_openings():
    text = AUDIT_V2.read_text(encoding="utf-8")

    assert "parent-relative placement" in text
    assert "centered opening usually has local X offset `0`" in text
    assert "do not block solely because the opening origin is `[0, 0, sill_height]`" in text


def test_audit_v2_classifies_gate_failures_without_override():
    text = AUDIT_V2.read_text(encoding="utf-8")

    assert "gate_dispute" in text
    assert "audit_override_attempt" in text
    assert "must not override deterministic gates" in text
    assert "geometry feedback" in text


def test_bim_json_generator_v2_keeps_wall_rotation_out_of_representation_position():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")

    assert "Do not duplicate wall rotation into `Representation.position`" in text
    assert "wall orientation belongs in `ObjectPlacement.ref_direction`" in text
