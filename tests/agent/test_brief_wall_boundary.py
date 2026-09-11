"""Prompt regression and deterministic boundary probes; not live-model scores."""
import json
from pathlib import Path
import pytest
from text2ifc_agent.design_brief import design_brief_template_id
from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.semantic_coverage import _wall_plan_bounds


@pytest.mark.parametrize('review',[False,True])
def test_active_brief_distinguishes_outline_from_wall_solid(review):
    template=design_brief_template_id('text2ifc/design-brief/2.3',design_review_enabled=review)
    text=render_prompt(template_id=template,inputs={'USER_REQUEST':'墙端连接不重叠。',
        'CONVERSATION':[],'DESIGN_BRIEF_SCHEMA':{},'EVIDENCE_CATALOG':[],'FEW_SHOTS':[]})['text']
    assert 'Outer outline is not a wall centerline' in text
    assert 'do not treat intersections of offset centerlines as solid endpoints' in text
    assert 'Preserve explicitly supplied centerline endpoints and wall bounds' in text
    assert 'Agent-derived coordinates must be corrected before ready' in text


@pytest.mark.parametrize('dx,dy',[(0,0),(-3000,1000),(2500,-6000)])
def test_existing_bounds_contract_supports_join_without_changing_extent(dx,dy):
    horizontal={'bounds':{'x':[dx,dx+6000],'y':[dy,dy+200]}}
    vertical={'bounds':{'x':[dx,dx+200],'y':[dy+200,dy+4000]}}
    a=_wall_plan_bounds(horizontal);b=_wall_plan_bounds(vertical)
    assert a==(dx,dx+6000,dy,dy+200) and b==(dx,dx+200,dy+200,dy+4000)
    assert a[3]==b[2] and a[0]==b[0]  # Touch, no area overlap, outer corner covered.
    explicit={'start_mm':[dx,dy],'end_mm':[dx+4000,dy],'thickness_mm':200}
    before=json.dumps(explicit)
    assert _wall_plan_bounds(explicit)==(dx,dx+4000,dy-100,dy+100)
    assert json.dumps(explicit)==before  # The original centerline meaning is unchanged.


def test_family_is_frozen_before_prompt_change():
    f=json.loads(Path('docs/validation/brief-wall-boundary/family.json').read_text(encoding='utf-8'))
    assert {c['slice'] for c in f['cases']}=={'positive','negative','boundary','cross_scene'}
    assert len(f['cases'])==8
