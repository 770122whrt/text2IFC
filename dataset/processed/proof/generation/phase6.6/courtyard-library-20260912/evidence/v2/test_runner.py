"""Offline wrapper check: fresh Brief, generator, review Audit, final publication."""
import importlib.util,json
from pathlib import Path
from tests.agent.test_phase6_2_fix_semantic_fidelity import _outside_boundary_design_brief,_outside_boundary_center_overlap_candidate
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.agent.test_semantic_authority_completeness import review
from text2ifc_agent.generation_budget import GenerationBudget


def test_fresh_runner_retains_budget_and_binds_concept_review(tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('open_court_fresh_runner',Path(__file__).with_name('run_case.py'))
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    source=tmp_path/'source';source.mkdir()
    b=_outside_boundary_design_brief();b['schema_version']='text2ifc/design-brief/2.6'
    b['known_facts'].update(semantic_requirements=[],semantic_review=review(),plan_constraints=[])
    b['provenance'].update(selected_evidence_ids=[],few_shot_ids=[])
    (source/'request.txt').write_text(b['original_request'],encoding='utf-8')
    quote='请按确认方案重新从头完成。'
    turns=[{'turn_id':'turn-user-001','role':'user','content':b['original_request']},
           {'turn_id':'turn-user-concept-revision','role':'user','content':quote}]
    (source/'conversation.json').write_text(json.dumps(turns),encoding='utf-8')
    reference={'concerns':[{'id':'layout','description':'核对新方案布局','location':'测试房间'}]}
    (source/'reference-design-review.json').write_text(json.dumps(reference),encoding='utf-8')
    ledger_root=tmp_path/'prior';budget=GenerationBudget(ledger_root)
    # Reserve+settle one genuine-to-this-offline-fixture attempt, never erase it.
    from text2ifc_agent.generation_budget import BudgetedProvider
    dummy=BudgetedProvider(SequenceProvider([{}]),budget)
    dummy.generate_live(session_id='prior-offline',prompt='fixture',schema={},state={'stage':'fixture'})
    prior=ledger_root/'generation-budget.json';before=prior.read_bytes()
    monkeypatch.setattr(runner,'SOURCE',source);monkeypatch.setattr(runner,'PRIOR_BUDGET',prior)
    candidate=_outside_boundary_center_overlap_candidate();candidate['schema_version']='bim-json/2.3'
    for row in candidate['entities']:row['property_sets']={};row.pop('materials',None)
    audit={'schema_version':'text2ifc/audit/3.0','recommendation':'accept','blocking':False,
           'deterministic_gate_status':'passed','findings':[],
           'evidence_paths':['generator/candidate.json','design-review-context.json'],
           'design_review':{'scope':'limited_review_not_code_compliance',
             'concerns':[{'id':'layout','status':'not_verified','description':'布局已请求修改，独立验证仍需报告。',
                          'evidence_paths':['design-review-context.json','generator/candidate.json']}],
             'limitations':['离线夹具，不能证明真实模型能力或工程合规。']}}
    provider=SequenceProvider([b,candidate,audit])
    result=runner.execute(output=tmp_path/'run',provider_factory=lambda:provider,evidence_class='offline_fake')
    assert result['status']=='compiled',result
    assert len(provider.calls)==3
    assert result['budget_after']['calls_used']==4
    assert result['budget_after']['attempts'][0]==result['budget_before']['attempts'][0]
    assert prior.read_bytes()==before and result['prior_budget_unchanged']
    assert Path(result['result']['ifc_path']).is_file()
    run_dir=Path(result['run_dir'])
    assert (run_dir/'design-review-context.json').is_file()
    assert json.loads((run_dir/'audit/audit-report.json').read_text(encoding='utf-8'))['schema_version']=='text2ifc/audit/3.0'
