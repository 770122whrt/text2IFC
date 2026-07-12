import json
from pathlib import Path

from text2ifc_agent.design_brief import validate_design_brief


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
    assert "Optional or not-yet-decided items must not consume a clarification question slot" in text
    assert "If you ask about an ambiguity, that ambiguity MUST be marked blocking: true" in text
    assert "Prioritize blocking geometry facts before optional openings or style choices" in text
    assert "Initial user phrases like not decided or not thought through yet are not the same as an answered unknown" in text
    assert "draft_required and blocked MUST have an empty clarification_questions array" in text
    assert "original_request MUST exactly equal CONVERSATION[0].content" in text
    assert "including punctuation, typos, trailing symbols, and unusual characters" in text
    assert "Never normalize, clean, summarize, translate, or append later answers to original_request" in text
    assert "Bind short numeric answers to the immediately preceding assistant question" in text
    assert "source_turns MUST use exact turn_id values already present in CONVERSATION" in text
    assert "missing_facts and unsupported_requests items MUST include a non-empty `code`" in text
    assert "ambiguities items MUST NOT include `code`" in text


def test_design_brief_v21_defines_canonical_multistorey_structure():
    text = DESIGN_BRIEF_V21.read_text(encoding="utf-8")

    assert "Canonical multi-storey Design Brief structure" in text
    assert "Use `elevation_mm`; do not use `level` as a substitute" in text
    assert "Do not create top-level `storey_1`, `storey_2`, `spaces_ground`, `spaces_first`, or generic `openings`" in text
    assert "Put doors and windows inside the storey that owns their host wall" in text
    assert "Use `known_facts.floor_slabs`" in text
    assert "Use one `known_facts.roof_slab`" in text
    assert "Do not collapse explicit slab instances into thickness-only building metadata" in text
    assert "literal key `bounds`, not `plan_bounds`" in text


def test_design_brief_few_shots_include_valid_standard_two_storey_contract():
    payload = json.loads(DESIGN_BRIEF_FEW_SHOTS.read_text(encoding="utf-8"))
    shot = next(
        item
        for item in payload["few_shots"]
        if item["few_shot_id"] == "design-brief-v2.standard-two-storey-building"
    )

    output = shot["output"]
    known = output["known_facts"]
    assert "storey_1" not in known
    assert "storey_2" not in known
    assert "spaces_ground" not in known
    assert "spaces_first" not in known
    assert "openings" not in known
    assert [storey["id"] for storey in known["storeys"]] == ["storey-1", "storey-2"]
    assert [storey["elevation_mm"] for storey in known["storeys"]] == [0, 3150]
    assert known["storeys"][0]["doors"][0]["host_wall"] == "storey-1-wall-south"
    assert known["storeys"][1]["windows"][0]["host_wall"] == "storey-2-wall-south"
    assert known["floor_slabs"] == [
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
        },
    ]
    assert known["roof_slab"] == {
        "id": "roof-slab",
        "bottom_elevation_mm": 6150,
        "thickness_mm": 150,
    }

    evidence_catalog = [
        {"evidence_id": evidence_id}
        for evidence_id in output["provenance"]["selected_evidence_ids"]
    ]
    assert validate_design_brief(output, evidence_catalog=evidence_catalog) == []
 
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


def test_audit_v2_requires_component_level_geometry_quality_findings():
    text = AUDIT_V2.read_text(encoding="utf-8")

    assert "Opening and filling alignment" in text
    assert "OPENING_FILLING_ORIENTATION_MISMATCH" in text
    assert "host_wall" in text
    assert "opening" in text
    assert "filling" in text
    assert "Vertical closure" in text
    assert "VERTICAL_SLAB_WALL_GAP" in text
    assert "wall_top_z" in text
    assert "slab_bottom_z" in text
    assert "gap_mm" in text


def test_audit_v2_does_not_recompute_a_passed_deterministic_invariant():
    text = AUDIT_V2.read_text(encoding="utf-8")

    assert "Do not recompute or contradict that same invariant by mental arithmetic" in text
    assert "machine-readable contradictory evidence" in text
    assert "component_ids" in text


def test_bim_json_generator_v2_keeps_wall_rotation_out_of_representation_position():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")

    assert "Do not duplicate wall rotation into `Representation.position`" in text
    assert "wall orientation belongs in `ObjectPlacement.ref_direction`" in text


def test_bim_json_generator_v2_contains_multistorey_error_constraints():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")

    assert "{{ENTITY_ID_CONTRACT}}" in text
    assert "must use `entity_id` verbatim" in text
    assert "does not change the human-facing Name" in text
    assert "Multi-storey generation rules" in text
    assert "Each storey must declare its own exterior and interior walls" in text
    assert "A second-storey window must reference a second-storey wall" in text
    assert "Every ObjectPlacement.relative_to and relationship endpoint must reference an entity id already declared in entities" in text
    assert "Preserve every component that is not identified by a blocking feedback issue" in text


def test_design_brief_v2_normalizes_axis_aligned_wall_segments_without_bent_walls():
    text = Path("prompts/agent/design-brief-v2.1.md").read_text(encoding="utf-8")

    assert "start_mm" in text
    assert "end_mm" in text
    assert "two independent straight wall records" in text
    assert "single bent or polyline wall" in text


def test_bim_json_generator_v2_requires_medium_straight_stair_contract():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")

    assert "Medium straight-stair contract" in text
    assert "IfcStairFlight" in text
    assert "IfcRelAggregates" in text
    assert "Do not represent a supported straight stair as only one solid block" in text
    assert "`Representation.direction` is the actual stair-width extrusion direction" in text


def test_generator_two_storey_example_teaches_local_datums_and_stepped_stair():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")
    payload = json.loads(
        Path("prompts/agent/few-shots/bim-json-generator-v2-two-storey-standard.json").read_text(
            encoding="utf-8"
        )
    )

    assert "Convert a confirmed global target to parent-local coordinates exactly once" in text
    assert "top_elevation_mm - parent_storey_elevation_mm - thickness_mm" in text
    entities = {entity["id"]: entity for entity in payload["entities"]}
    assert entities["first-floor-slab"]["attributes"]["ObjectPlacement"]["origin"][2] == -150
    assert entities["roof-slab"]["attributes"]["ObjectPlacement"]["origin"][2] == 3000
    assert entities["stair-flight-1"]["attributes"]["Representation"]["profile"]["kind"] == "polygon"
    assert len(entities["stair-flight-1"]["attributes"]["Representation"]["profile"]["points"]) >= 7
    assert entities["stair-flight-1"]["attributes"]["Representation"]["direction"] == [1, 0, 0]
    assert entities["opening-first-floor-slab-stair"]["attributes"]["ObjectPlacement"]["origin"] == [-4000, 2000, 0]


def test_bim_json_generator_v2_repeats_schema_self_checks_for_live_errors():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")

    assert "Polygon profiles must be closed rings" in text
    assert "Do not place `PredefinedType` or `ShapeType` inside property_sets" in text
    assert "Put IFC enum attributes such as `ShapeType` on `attributes`" in text


def test_bim_json_generator_v2_requires_addressable_draft_paths():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")

    assert "Draft path rules" in text
    assert "must point into `partial_document`, `missing_facts`, `losses`, or `clarification_targets`" in text
    assert "Do not output pseudo paths such as `/entities/ifc_class/door/placement`" in text


def test_design_brief_v21_preserves_explicit_layout_facts_and_blocks_conflicts():
    text = DESIGN_BRIEF_V21.read_text(encoding="utf-8")

    assert "Do not replace explicit coordinates" in text
    assert "LAYOUT_SPACE_OVERLAP" in text
    assert "DOOR_HOST_NO_SHARED_SEGMENT" in text
    assert "STAIR_OPENING_SPACE_COLLISION" in text


def test_generator_v2_teaches_rotated_host_opening_and_filling_placement():
    text = Path("prompts/agent/bim-json-generator-v2.md").read_text(encoding="utf-8")
    payload = json.loads(
        Path("prompts/agent/few-shots/bim-json-generator-v2-two-storey-standard.json").read_text(
            encoding="utf-8"
        )
    )

    assert "An opening placed relative to its host wall" in text
    assert "A filling placed relative to its opening" in text
    entities = {entity["id"]: entity for entity in payload["entities"]}
    east_wall = entities["storey-2-wall-east"]
    opening = entities["opening-storey-2-window-east"]
    window = entities["window-storey-2-east"]
    assert east_wall["attributes"]["ObjectPlacement"]["ref_direction"] == [0, 1, 0]
    assert opening["attributes"]["ObjectPlacement"] == {
        "relative_to": "storey-2-wall-east",
        "origin": [900, 0, 900],
        "axis": [0, 0, 1],
        "ref_direction": [1, 0, 0],
    }
    assert window["attributes"]["ObjectPlacement"] == {
        "relative_to": "opening-storey-2-window-east",
        "origin": [0, 0, 0],
        "axis": [0, 0, 1],
        "ref_direction": [1, 0, 0],
    }


def test_design_brief_few_shot_preserves_controlled_layout_coordinates():
    payload = json.loads(DESIGN_BRIEF_FEW_SHOTS.read_text(encoding="utf-8"))
    shot = next(
        item
        for item in payload["few_shots"]
        if item["few_shot_id"] == "design-brief-v2.coordinate-controlled-two-storey"
    )

    known = shot["output"]["known_facts"]
    ground = known["storeys"][0]
    assert ground["spaces"][0]["bounding_box"] == "x=0..4000, y=0..4000"
    assert ground["doors"][0]["center_global_mm"] == [4000, 2000]
    assert known["stairs"][0]["opening_bounds"] == "x=0..2000, y=4000..8000"
