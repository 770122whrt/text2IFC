"""Explicit wall extent survives fact projection independently of room adjacency."""
from copy import deepcopy
import json

import pytest

from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation
from text2ifc_agent.prompt_registry import load_prompt_registry, render_prompt


@pytest.mark.parametrize('axis',['x','y'])
@pytest.mark.parametrize('partial_room',[False,True])
def test_explicit_wall_bounds_are_not_shortened_to_net_room_overlap(axis,partial_room):
    bounds={'x':[3800,4000],'y':[0,9000]}
    room_a={'x':[0,3800],'y':[0,9000]}
    room_b={'x':[4000,6500],'y':[0,2200 if partial_room else 9000]}
    if axis=='x':
        bounds={a:bounds[b] for a,b in [('x','y'),('y','x')]}
        room_a={a:room_a[b] for a,b in [('x','y'),('y','x')]}
        room_b={a:room_b[b] for a,b in [('x','y'),('y','x')]}
    wall={'id':'divider','bounds':bounds,'connects':['reading','landing'],'thickness_mm':200}
    brief={'schema_version':'text2ifc/design-brief/2.1','known_facts':{'storeys':[
        {'id':'upper','elevation_mm':3600,'net_height_mm':3000,
         'spaces':[{'id':'reading','bounds':room_a},{'id':'landing','bounds':room_b}],
         'walls':{'interior':[wall],'exterior':[]}}]}}
    facts=build_expected_facts(case_id='wall-facts',design_brief=brief)
    result=build_design_geometry_expectation(case_id='wall-facts',design_brief=brief,expected_facts=facts)
    assert result['complete'],result['unresolved']
    assert result['walls']['divider']['bbox']=={
        'x':[v/1000 for v in bounds['x']], 'y':[v/1000 for v in bounds['y']], 'z':[3.6,6.6]}
    missing=deepcopy(brief)
    missing['known_facts']['storeys'][0]['walls']['interior'][0].pop('bounds')
    missing_facts=build_expected_facts(case_id='wall-facts',design_brief=missing)
    assert not build_design_geometry_expectation(case_id='wall-facts',design_brief=missing,
                                                 expected_facts=missing_facts)['complete']


def test_current_brief_entrypoints_select_versioned_explicit_fact_contract():
    from text2ifc_agent import live_pipeline, interactive_cli_flow
    assert live_pipeline.DESIGN_BRIEF_TEMPLATE_ID==interactive_cli_flow.DESIGN_BRIEF_TEMPLATE_ID=='design-brief.v2.3'
    registry=load_prompt_registry()
    for old,new in [('design-brief.v2.2','design-brief.v2.3'),
                    ('bim-json-changeset.v1.4','bim-json-changeset.v1.5')]:
        assert registry[old]['sha256']!=registry[new]['sha256']
        assert registry[old]['required_inputs']==registry[new]['required_inputs']
        rendered=render_prompt(template_id=new,inputs={k:{} for k in registry[new]['required_inputs']})
        assert rendered['text']


@pytest.mark.parametrize('version,template',[('2.0','bim-json-changeset.v1'),('2.1','bim-json-changeset.v1.5')])
def test_changeset_transport_keeps_explicit_facts_and_version_binding(tmp_path,version,template):
    from tests.agent.test_phase6_5_changeset_stage import (
        RecordingProvider, _candidate, _changeset, _expected, _issues, _revision, _scope)
    from text2ifc_agent.changeset_stage import run_changeset_stage
    candidate=_candidate(); candidate['schema_version']=f'bim-json/{version}'
    expected=_expected()
    expected['walls'][0].update(bounds={'x':[1200,1400],'y':[0,7800]},connects=['a','b'])
    frozen=deepcopy(expected)
    provider=RecordingProvider(_changeset(candidate,expected))
    result=run_changeset_stage(provider=provider,output_dir=tmp_path,case_id='wall-facts',call_index=1,
        user_request='保留整面隔墙，只修正名字。',conversation=[],design_brief={'known_facts':{}},
        expected_facts=expected,candidate=candidate,base_revision=_revision(candidate,expected),
        scope=_scope(),issues=_issues())
    assert result['valid'],result
    assert expected==frozen
    sent=json.loads((tmp_path/'prompt-render-input.json').read_text(encoding='utf-8'))
    assert sent['EXPECTED_FACTS']==frozen
    trace=json.loads((tmp_path/'trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['template_id']==template
