"""Real IFC -> compact text -> frozen public Generation -> real diagnostic Compare."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pytest
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc2text.compact_pipeline import prepare_compact,write_compact
from text2ifc_ifc2text.campaign_budget import CampaignBudget
from text2ifc_ifc2text.goal_budget import GoalBudget,GoalStopped
from text2ifc_ifc2text.roundtrip_compare import compare_roundtrip
from text2ifc_compiler import compile_document
ROOT=Path(__file__).resolve().parents[2]

class Narrator:
    def generate_candidate(self,**kwargs):
        text=kwargs['prompt']; context,_=json.JSONDecoder().raw_decode(text[text.index('{'):])
        output={'overview':'空间与构件按楼层展开，材料在各层末尾对应。',
          'storey_notes':[{'storey':s['id'],'text':'本层的空间和构件布置见下列明细。'} for s in context['storeys']]}
        return ProviderOutput(json.dumps(output,ensure_ascii=False),{'evidence_class':'offline_fake'})


def test_compact_description_public_bridge_and_compare(tmp_path):
    root=ROOT/'dataset/processed/agent-demo/phase6.1-mimo-live/complete-room'
    candidate=json.loads((root/'generator/candidate.json').read_text(encoding='utf-8'))
    source=tmp_path/'original.ifc'; assert compile_document(candidate,source).success
    before=source.read_bytes(); output=tmp_path/'compact'
    prepare_compact(source,output)
    result=write_compact(output=output,provider=Narrator())
    assert result['provider_calls']==1
    text=(output/'design-description.md').read_text(encoding='utf-8')
    spec=importlib.util.spec_from_file_location('frozen_bridge',ROOT/'tests/ifc2text/test_offline_public_bridge.py')
    fixture=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
    provider=fixture._SequenceLiveProvider([candidate,{'schema_version':'text2ifc/audit/2.0',
      'recommendation':'accept','blocking':False,'deterministic_gate_status':'passed','findings':[],
      'evidence_paths':['design-brief/design-brief.json','generator/candidate.json']}])
    with SessionStore.open(tmp_path/'generation/sessions.sqlite',artifact_root=tmp_path/'generation') as store:
        reconstructed=reconstruct_description_with_public_text2ifc(text,store=store,
             invoke_design_brief=fixture._design_brief_invoker(store),provider_factory=lambda:provider)
        assert reconstructed['status']=='compiled'
        assert store.get_session(reconstructed['session_id']).original_input==text
        report=compare_roundtrip(source,reconstructed['ifc_path'])
        assert report['summary']['missing_count']==0 and report['summary']['extra_count']==0
    assert source.read_bytes()==before
    with pytest.raises(ValueError,match='ATTEMPT_EXISTS'): write_compact(output=output,provider=Narrator())


def test_budget_amendment_keeps_all_prior_calls_and_tokens(tmp_path):
    prior=GoalBudget(tmp_path/'old',writing_calls=26,reconstruction_calls=12,tokens=1000,
                     historical_writing_calls=6,historical_tokens=100)
    t=prior.reserve('reconstruction',100); prior.settle(t,usage={'prompt_tokens':20,'completion_tokens':30})
    prior.halt('TRUNCATED'); frozen=prior.path.read_bytes()
    new=CampaignBudget(tmp_path/'new',predecessor=prior.path,tokens=2000)
    assert new.snapshot()['tokens_used_or_reserved']==150
    assert new.snapshot()['calls']=={'writing':6,'reconstruction':1}
    t=new.reserve('reconstruction',100); new.settle(t,usage={'prompt_tokens':10,'completion_tokens':10})
    reopened=CampaignBudget(tmp_path/'new',predecessor=prior.path,tokens=2000)
    assert reopened.snapshot()['tokens_used_or_reserved']==170
    assert reopened.snapshot()['calls']['reconstruction']==2
    assert prior.path.read_bytes()==frozen
    with pytest.raises(GoalStopped): CampaignBudget(tmp_path/'new',predecessor=prior.path,tokens=3000)


def test_invalid_short_prose_is_preserved_and_not_published(tmp_path):
    root=ROOT/'dataset/processed/agent-demo/phase6.1-mimo-live/complete-room'
    source=tmp_path/'source.ifc'
    assert compile_document(json.loads((root/'generator/candidate.json').read_text(encoding='utf-8')),source).success
    prepare_compact(source,tmp_path/'out')
    class Bad:
        def generate_candidate(self,**kwargs): return ProviderOutput('{not-json',{'evidence_class':'offline_fake'})
    with pytest.raises(Exception): write_compact(output=tmp_path/'out',provider=Bad())
    assert not (tmp_path/'out/design-description.md').exists()
    assert (tmp_path/'out/writing/narration/raw-response.txt').read_text()=='{not-json'
