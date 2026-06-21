import importlib
import importlib.util

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
