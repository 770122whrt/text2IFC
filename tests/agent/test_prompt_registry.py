import importlib
import importlib.util
import json

import pytest


def test_prompt_trace_requires_template_identity():
    module_name = "text2ifc_agent.prompt_registry"
    assert importlib.util.find_spec(module_name) is not None, (
        "prompt registry implementation is missing"
    )
    prompt_registry = importlib.import_module(module_name)

    with pytest.raises(
        prompt_registry.PromptRegistryError,
        match="template_id|template_hash|renderer_input_path",
    ):
        prompt_registry.validate_prompt_trace(
            {
                "rendered_prompt_path": "prompt-rendered.md",
                "raw_response_path": "raw-response.txt",
            }
        )


def test_registry_loads_and_renders_versioned_generator_prompt():
    module_name = "text2ifc_agent.prompt_registry"
    assert importlib.util.find_spec(module_name) is not None, (
        "prompt registry implementation is missing"
    )
    prompt_registry = importlib.import_module(module_name)

    registry = prompt_registry.load_prompt_registry()
    template = registry["bim-json-generator.v3"]
    rendered = prompt_registry.render_prompt(
        template_id="bim-json-generator.v3",
        inputs={
            "USER_REQUEST": "创建一个六米乘四米的房间。",
            "REFERENCE_JSON": {"schema_version": "bim-json/2.0"},
            "VALIDATION_FEEDBACK": [],
        },
    )

    assert template["sha256"].startswith("sha256:")
    assert rendered["metadata"]["template_id"] == "bim-json-generator.v3"
    assert rendered["metadata"]["template_hash"] == template["sha256"]
    assert "创建一个六米乘四米的房间。" in rendered["text"]
    assert "{{USER_REQUEST}}" not in rendered["text"]


def test_design_brief_v1_registry_hash_remains_historical():
    prompt_registry = importlib.import_module("text2ifc_agent.prompt_registry")
    registry = prompt_registry.load_prompt_registry()

    assert registry["design-brief.v1"]["sha256"] == (
        "sha256:b944c7a82d6eb5f9ae6a625dc208c1164f8179cf4d5346606979f07dac992411"
    )


def test_design_brief_v2_registry_hash_remains_live_attempt_history():
    prompt_registry = importlib.import_module("text2ifc_agent.prompt_registry")
    registry = prompt_registry.load_prompt_registry()

    assert registry["design-brief.v2"]["sha256"] == (
        "sha256:338baa65b301ebef566c8fc0761c44de836c7f42bc1adf951ba39ff4ff4dacdf"
    )


def test_registry_renders_evidence_grounded_design_brief_v2_prompt():
    prompt_registry = importlib.import_module("text2ifc_agent.prompt_registry")
    selector = importlib.import_module("text2ifc_agent.context_selection")
    registry = prompt_registry.load_prompt_registry()
    selection = selector.select_design_brief_context(
        user_request="创建一个6米乘4米、高3米的房间。",
        conversation=[],
    )
    schema = json.loads(
        (
            prompt_registry.PROJECT_ROOT
            / "schemas/agent/design-brief/2.0/schema.json"
        ).read_text(encoding="utf-8")
    )

    rendered = prompt_registry.render_prompt(
        template_id="design-brief.v2",
        inputs={
            "USER_REQUEST": "创建一个6米乘4米、高3米的房间。",
            "CONVERSATION": [],
            "DESIGN_BRIEF_SCHEMA": schema,
            "EVIDENCE_CATALOG": selection["evidence"],
            "FEW_SHOTS": selection["few_shots"],
        },
    )
    text = rendered["text"]

    assert registry["design-brief.v2"]["sha256"].startswith("sha256:")
    assert rendered["metadata"]["template_id"] == "design-brief.v2"
    assert "创建一个6米乘4米、高3米的房间。" in text
    assert "text2ifc/design-brief/2.0" in text
    assert "capability:IFC2X3:IfcSpace" in text
    assert "首个非空白字符必须是 `{`" in text
    assert "最后一个非空白字符必须是 `}`" in text
    assert "禁止使用 Markdown 代码围栏" in text
    assert "整个响应只能包含一个 JSON 对象" in text
    assert "required_facts" not in text
    assert '"not_required"' not in text
    for placeholder in (
        "USER_REQUEST",
        "CONVERSATION",
        "DESIGN_BRIEF_SCHEMA",
        "EVIDENCE_CATALOG",
        "FEW_SHOTS",
    ):
        assert "{{" + placeholder + "}}" not in text


def test_design_brief_v2_1_strengthens_live_bare_json_contract():
    prompt_registry = importlib.import_module("text2ifc_agent.prompt_registry")
    registry = prompt_registry.load_prompt_registry()

    rendered = prompt_registry.render_prompt(
        template_id="design-brief.v2.1",
        inputs={
            "USER_REQUEST": "创建一个房间。",
            "CONVERSATION": [],
            "DESIGN_BRIEF_SCHEMA": {"type": "object"},
            "EVIDENCE_CATALOG": [],
            "FEW_SHOTS": [],
        },
    )

    assert registry["design-brief.v2.1"]["sha256"].startswith("sha256:")
    assert "任何反引号字符" in rendered["text"]
    assert "响应将被判定为失败" in rendered["text"]
    assert "发送前自检" in rendered["text"]


def test_generator_v1_registry_hash_remains_historical():
    prompt_registry = importlib.import_module("text2ifc_agent.prompt_registry")
    registry = prompt_registry.load_prompt_registry()

    assert registry["bim-json-generator.v1"]["sha256"] == (
        "sha256:c99b445f1b536d74130446256a944f2bdb128e7762d779be2c9f4d196011dec0"
    )


def test_generator_v2_renders_both_exact_canonical_contracts():
    prompt_registry = importlib.import_module("text2ifc_agent.prompt_registry")
    registry = prompt_registry.load_prompt_registry()
    formal_schema = json.loads(
        (
            prompt_registry.PROJECT_ROOT
            / "schemas/bim-json/2.0/schema.json"
        ).read_text(encoding="utf-8")
    )
    draft_schema = json.loads(
        (
            prompt_registry.PROJECT_ROOT
            / "schemas/bim-json/draft/1.0/schema.json"
        ).read_text(encoding="utf-8")
    )

    rendered = prompt_registry.render_prompt(
        template_id="bim-json-generator.v2",
        inputs={
            "USER_REQUEST": "创建一个矩形房间。",
            "CONVERSATION": [],
            "DESIGN_BRIEF": {"status": "ready"},
            "FORMAL_SCHEMA": formal_schema,
            "DRAFT_SCHEMA": draft_schema,
            "CAPABILITY_PROFILE": [],
            "FEW_SHOTS": [],
        },
    )
    text = rendered["text"]

    assert registry["bim-json-generator.v2"]["sha256"].startswith("sha256:")
    assert formal_schema["$id"] in text
    assert draft_schema["$id"] in text
    assert '"schema_version": "bim-json/2.0"' in text
    assert '"draft_version": "bim-json-draft/1.0"' in text
    assert '"target_schema_version": "bim-json/2.0"' in text
    assert "任何反引号字符" in text
    assert "SCHEMA_SUMMARY" not in text
    assert "{{FORMAL_SCHEMA}}" not in text
    assert "{{DRAFT_SCHEMA}}" not in text
