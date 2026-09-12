"""Actual continuation entry, original live source plus explicitly fake Audit."""
import importlib.util
import json
from pathlib import Path
import pytest


def runner():
    spec=importlib.util.spec_from_file_location('courtyard_attachment_continuation',Path(__file__).with_name('run_case.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_public_stage_continuation_preserves_live_source_and_budget(tmp_path):
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    m=runner()
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json','repair/route.json']}
    class Provider(SequenceProvider):
        def generate_live(self, **kwargs):
            self.prompt_characters = len(kwargs['prompt'])
            return super().generate_live(**kwargs)
    provider=Provider([audit])
    r=m.execute(output=tmp_path/'run',provider_factory=lambda:provider,evidence_class='offline_live_source_fake_audit')
    assert r['status']=='compiled' and r['source_unchanged']
    assert r['budget_before']['calls_used']==8 and r['budget_before']['tokens_used_or_reserved']==626258
    assert r['budget_after']['attempts'][:8]==r['budget_before']['attempts']
    assert len(provider.calls)==1 and provider.calls[0]['state']['stage']=='audit'
    assert r['new_generator_calls']==r['new_brief_calls']==0
    final=tmp_path/'run/final-acceptance/output.ifc'
    assert final.is_file()
    source=m.read(m.ORIGIN/'generator/parsed-output.json')
    actual=m.read(tmp_path/'run/generator/candidate.json')
    assert actual['entities']==source['entities']
    assert len(actual['relationships'])==len(source['relationships'])+110
    checks={}
    for name,function in [('check_ifc','check_ifc'),('check_part_colours','check')]:
        spec=importlib.util.spec_from_file_location(name,m.BASE/(name+'.py'))
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        report=getattr(checker,function)(final);assert report['status']=='passed',report
        checks[name]={k:report[k] for k in ['status','passed','total']}
    Path(__file__).with_name('offline-continuation-result.json').write_text(json.dumps({
        'evidence_class':'offline_live_source_fake_audit', 'checks':checks,
        'source_unchanged':r['source_unchanged'],'new_fake_calls':1,
        'audit_prompt_characters':provider.prompt_characters},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


@pytest.mark.parametrize('attack',['parsed','request','finish_reason'])
def test_changed_or_truncated_origin_cannot_reach_transport(tmp_path,attack):
    import shutil
    m=runner(); source=tmp_path/'origin';shutil.copytree(m.ORIGIN,source);m.ORIGIN=source
    if attack=='request': (source/'generator/input.txt').write_text('other request',encoding='utf-8')
    elif attack=='parsed':
        p=source/'generator/parsed-output.json';v=m.read(p);v['entities'][0]['attributes']['Name']='changed';m.write(p,v)
    else:
        p=source/'generator/response.raw.json';v=m.read(p);v['choices'][0]['finish_reason']='length';m.write(p,v)
    calls=[]
    def forbidden():
        calls.append(True)
        raise AssertionError('transport must remain unreachable')
    with pytest.raises(AssertionError):
        m.execute(output=tmp_path/'run',provider_factory=forbidden,evidence_class='offline_invalid')
    assert not (tmp_path/'run/output.ifc').exists()
    assert not calls
