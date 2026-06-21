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
