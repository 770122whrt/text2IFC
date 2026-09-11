"""Prompt scope regression; fixture checks are not live LLM quality evidence."""
import json
from pathlib import Path

import pytest

from text2ifc_agent.design_brief import design_brief_template_id
from text2ifc_agent.prompt_registry import render_prompt


@pytest.mark.parametrize('review', [False, True])
def test_active_prompt_distinguishes_functional_volume_from_solid_collision(review):
    template = design_brief_template_id('text2ifc/design-brief/2.3', design_review_enabled=review)
    rendered = render_prompt(template_id=template, inputs={
        'USER_REQUEST': '楼梯位于交通空间内。', 'CONVERSATION': [],
        'DESIGN_BRIEF_SCHEMA': {}, 'EVIDENCE_CATALOG': [], 'FEW_SHOTS': []})
    text = rendered['text']
    assert 'IfcSpace is a functional area/volume, not a solid floor slab' in text
    assert 'Explicit inclusion in a stair/circulation space is not by itself a conflict' in text
    assert 'If the purpose or usable-floor requirement is genuinely unclear' in text
    assert 'Do not merge storeys, split spaces, resize openings' in text
    assert 'A prompt-side inference is not an executed deterministic geometry check' in text
    assert 'If it does,\n   record `STAIR_OPENING_SPACE_COLLISION`' not in text
    # Actual solid collisions and contradictory host geometry stay blocking.
    assert 'Missing or contradictory host facts remain blocking' in text
    assert 'A conflicting layout must never be reported as `ready`' in text


def test_historical_prompt_keeps_original_rule_for_reproduction():
    text = Path('prompts/agent/design-brief-v2.9.md').read_text(encoding='utf-8')
    assert 'positively overlap an explicitly declared same-storey IfcSpace. If it does,' in text


def test_prechange_family_contains_positive_negative_boundary_and_cross_scene():
    family = json.loads(Path('docs/validation/brief-space-opening/family.json').read_text(encoding='utf-8'))
    assert {c['slice'] for c in family['cases']} >= {'positive', 'negative', 'boundary', 'cross_scene'}
    assert {c['expected'] for c in family['cases']} >= {'no_overlap_only_blocker', 'needs_clarification'}
