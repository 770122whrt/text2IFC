"""Lossless rectangle notation adapter, never a bounding-box approximation."""
import copy
import pytest

def sample():
    return {'schema_version':'text2ifc/design-brief/2.7','known_facts':{
        'outline':{'x_min':-1200,'x_max':5300,'y_min':200,'y_max':8700},
        'plan_constraints':[{'kind':'wall_layout','outline_ref':'/known_facts/outline'}]}}

def test_exact_rectangle_conversion_and_original_immutability():
    from text2ifc_agent.brief_plan_normalization import normalize_layout_outlines
    b=sample();before=copy.deepcopy(b);fixed,changes=normalize_layout_outlines(b)
    assert b==before
    assert fixed['known_facts']['outline']==[[-1200,200],[5300,200],[5300,8700],[-1200,8700],[-1200,200]]
    assert changes[0]['before']==before['known_facts']['outline']
    assert changes[0]['after']==fixed['known_facts']['outline']
    assert normalize_layout_outlines(fixed)==(fixed,[])

@pytest.mark.parametrize('bad',[{'holes':[]}, {'x_max':-1200}, {'x_min':True}, {'y_max':float('inf')}, {'x_min':'-1200'}])
def test_ambiguous_or_invalid_notation_is_not_repaired(bad):
    from text2ifc_agent.brief_plan_normalization import normalize_layout_outlines
    b=sample();b['known_facts']['outline'].update(bad)
    fixed,changes=normalize_layout_outlines(b)
    assert fixed==b and not changes

@pytest.mark.parametrize('version,kind',[('text2ifc/design-brief/2.6','wall_layout'),('text2ifc/design-brief/2.7','inside_wall_envelope')])
def test_old_contracts_are_untouched(version,kind):
    from text2ifc_agent.brief_plan_normalization import normalize_layout_outlines
    b=sample();b['schema_version']=version;b['known_facts']['plan_constraints'][0]['kind']=kind
    assert normalize_layout_outlines(b)==(b,[])

def test_public_brief_records_adapter_without_an_extra_provider_call(tmp_path):
    import json
    from tests.agent.test_wall_layout_constraints import layout_fixture
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    case,b=layout_fixture()
    c=b['known_facts']['plan_constraints'][0]
    from text2ifc_agent.brief_plan_constraints import resolve
    points=resolve(b,c['outline_ref'])
    # Keep the existing rectangular fixture's exact vertices; no new scene.
    xs=[p[0] for p in points];ys=[p[1] for p in points]
    parent=b
    keys=c['outline_ref'].split('/')[1:]
    for k in keys[:-1]:parent=parent[int(k)] if isinstance(parent,list) else parent[k]
    parent[keys[-1]]={'x_min':min(xs),'x_max':max(xs),'y_min':min(ys),'y_max':max(ys)}
    provider=SequenceProvider([b])
    result=run_design_brief_stage(provider=provider,output_dir=tmp_path/'brief',case=case,design_brief_schema_version=b['schema_version'])
    assert result['valid'],result
    assert len(provider.calls)==1
    assert json.loads((tmp_path/'brief/parsed-output.json').read_text(encoding='utf-8'))==b
    assert (tmp_path/'brief/outline-normalization.json').is_file()
