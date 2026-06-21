from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "prompts" / "jsonfix" / "semantic-patch-v1.md"
FEW_SHOT = ROOT / "prompts" / "jsonfix" / "semantic-patch-fewshot.md"


def test_versioned_prompt_has_stable_inputs_and_patch_envelope() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    for placeholder in (
        "{{USER_REQUEST}}",
        "{{BASE_DOCUMENT_ID}}",
        "{{BASE_DOCUMENT_SUMMARY}}",
        "{{VALIDATION_FEEDBACK}}",
        "{{PATCH_SCHEMA}}",
        "{{FEW_SHOT_EXAMPLES}}",
    ):
        assert placeholder in text
    for field in (
        "patch_version",
        "target_schema_version",
        "target_ifc_schema",
        "target_document_id",
        "layers",
        "operations",
    ):
        assert field in text
    assert 'patch_version: "bim-json-patch/1.0"' in text
    assert 'target_schema_version: "bim-json/2.0"' in text
    assert 'target_ifc_schema: "IFC2X3"' in text


def test_prompt_uses_chinese_bounded_questions_and_no_defaults() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "中文" in text
    assert "1-3" in text
    assert "mark_missing" in text
    assert "questions" in text
    assert "不得猜测" in text
    assert "不得使用默认值" in text
    assert "信息不足" in text


def test_prompt_forbids_compiler_level_and_geometry_payloads() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    for forbidden in (
        "raw IFC",
        "STEP",
        "STEP ID",
        "IfcCartesianPoint",
        "IfcDirection",
        "IfcOwnerHistory",
        "mesh points",
        "face indices",
        "4x4 transform matrices",
    ):
        assert forbidden in text
    assert "只输出一个 JSON 对象" in text
    assert "不得输出完整 BIM JSON 2.0 文档" in text


def test_prompt_keeps_review_feedback_in_a_separate_layer() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "reviewer" in text
    assert "validator" in text
    assert "单独的 layer" in text
    assert "不得静默修改 base" in text
    assert "overwrite" in text
    assert "request_tombstone" in text


def test_few_shot_covers_required_semantic_repair_examples() -> None:
    text = FEW_SHOT.read_text(encoding="utf-8")

    assert "Example 1: Add a missing wall" in text
    assert '"op": "add_entity"' in text
    assert '"ifc_class": "IfcWallStandardCase"' in text
    assert "Example 2: Set a wall property" in text
    assert '"op": "set_property"' in text
    assert '"property": "FireRating"' in text
    assert "Example 3: Record unsupported source geometry" in text
    assert '"op": "mark_unsupported_loss"' in text
    assert '"substitution": "none"' in text


def test_few_shot_examples_do_not_cross_the_model_boundary() -> None:
    text = FEW_SHOT.read_text(encoding="utf-8")

    assert "ISO-10303-21" not in text
    assert "#42=IFC" not in text.upper()
    assert "IfcCartesianPoint" not in text
    assert "IfcDirection" not in text
    assert "IfcOwnerHistory" not in text
