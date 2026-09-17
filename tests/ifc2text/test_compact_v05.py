"""Universal floor-ID contract and audited continuation without cost resets."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc2text.compact_pipeline import narration_schema
from text2ifc_ifc2text.campaign_budget import CampaignBudget
from text2ifc_ifc2text.goal_budget import GoalBudget, GoalStopped


def context():
    return {'storeys': [{'id': 'S01', 'name': 'Level 7'}, {'id': 'S02', 'name': 'Level 7'}]}


def test_dynamic_schema_pins_ids_not_names_without_translating_them():
    schema = narration_schema(context())
    good = {'overview': '按源标高记录组织。', 'storey_notes': [
        {'storey': 'S01', 'text': '构件按表定位。'}, {'storey': 'S02', 'text': '材料见索引。'}]}
    Draft202012Validator(schema).validate(good)
    for mutation in ('name', 'reorder', 'extra', 'missing'):
        bad = copy.deepcopy(good)
        if mutation == 'name': bad['storey_notes'][0]['storey'] = 'Level 7'
        if mutation == 'reorder': bad['storey_notes'].reverse()
        if mutation == 'extra': bad['storey_notes'].append(good['storey_notes'][0])
        if mutation == 'missing': bad['storey_notes'].pop()
        assert list(Draft202012Validator(schema).iter_errors(bad))


def test_prompt_names_and_version_do_not_include_revealed_scene():
    text = render_prompt(template_id='ifc2text-compact-narrator.v0.5',
        inputs={'FACT_SUMMARY': context(), 'OUTPUT_SCHEMA': narration_schema(context())})['text']
    assert 'id' in text and 'name' in text
    assert 'hxp' not in text and 'i5n' not in text


def test_reviewed_resume_preserves_attempts_totals_and_prior_halt(tmp_path):
    previous = GoalBudget(tmp_path/'old', historical_writing_calls=2, historical_tokens=100)
    token = previous.reserve('reconstruction', 100)
    previous.settle(token, usage={'prompt_tokens': 10, 'completion_tokens': 10})
    previous.halt('OLD_FAILURE')
    b = CampaignBudget(tmp_path/'current', predecessor=previous.path)
    t = b.reserve('writing', 100)
    b.settle(t, usage={'prompt_tokens': 20, 'completion_tokens': 30})
    b.halt('COMPACT_WRITING_FAILED')
    before = b.snapshot()
    with pytest.raises(GoalStopped): b.reserve('writing', 1)
    with pytest.raises(GoalStopped): b.resume_after_review(expected_reason='OTHER', code_commit='abc', note='offline review')
    b.resume_after_review(expected_reason='COMPACT_WRITING_FAILED', code_commit='abc', note='offline review')
    after = b.snapshot()
    assert not after['halted']
    assert after['attempts'] == before['attempts']
    assert after['calls'] == before['calls']
    assert after['tokens_used_or_reserved'] == before['tokens_used_or_reserved'] == 170
    assert after['continuations'][-1]['previous_halt'] == 'COMPACT_WRITING_FAILED'
    assert json.loads(previous.path.read_text())['halted'] is True
    with pytest.raises(GoalStopped): b.resume_after_review(expected_reason='COMPACT_WRITING_FAILED', code_commit='abc', note='duplicate')
