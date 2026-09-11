"""The active Brief prompt must request the supplied contract at its final check."""
import re

import pytest

from text2ifc_agent.design_brief import design_brief_template_id
from text2ifc_agent.prompt_registry import render_prompt


@pytest.mark.parametrize('design_review_enabled', [False, True])
def test_current_brief_final_instruction_matches_its_schema(design_review_enabled):
    version = 'text2ifc/design-brief/2.3'
    template = design_brief_template_id(version, design_review_enabled=design_review_enabled)
    result = render_prompt(template_id=template, inputs={
        'USER_REQUEST': '创建一间教室。', 'CONVERSATION': [],
        'DESIGN_BRIEF_SCHEMA': {'properties': {'schema_version': {'const': version}}},
        'EVIDENCE_CATALOG': [], 'FEW_SHOTS': []})
    instructions = re.findall(r'现在只返回一个满足 (\S+) Schema', result['text'])
    assert instructions == [version]
