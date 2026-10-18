from copy import deepcopy
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import formal_workflow as formal
from scripts.ifc_repair.repair_comparison.contracts import write_json, read_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger


def cases(tmp_path, monkeypatch, count=2):
    base = tmp_path / 'cases'
    monkeypatch.setattr(formal, 'check_candidate', lambda p: {'valid': True, 'review_accepted': True})
    for i in range(1, count+1):
        case = base / f'formal-{i:03d}'
        (case / 'public').mkdir(parents=True)
        (case / 'private').mkdir()
        (case / 'public/model.ifc').write_text(f'damaged {i}', encoding='utf8')
        (case / 'public/request.txt').write_text('请修复窗。', encoding='utf8')
        (case / 'private/reference.ifc').write_text(f'reference {i}', encoding='utf8')
        (case / 'private/mutation').mkdir()
        (case / 'private/mutation/damaged.ifc').write_text(f'damaged {i}', encoding='utf8')
        write_json(case / 'private/checks.json', {'checks':{'prepared':True}})
        write_json(case / 'private/answer-card.json', {'required_user_facts': []})
        write_json(case / 'private/technical-review.json', {'passed': True})
        write_json(case / 'private/task.json', {
            'case_id':case.name, 'source_sha256':str(i), 'damage_profile':{'level':'S1'},
            'review':{'status':'accepted_by_delegation','kind':'delegated_technical',
                      'reviewer':'Codex','human_viewed':False,'technical_review_passed':True,
                      'authorization':{'user_quote':'审题托付给你先','at':'2026-10-08'}},
            'author_expectations':{'target-1':{
                'basis':'public_author_intent','ifc_class':'IfcWindow','width_mm':900,'height_mm':1200,
                'opening_center_xy_m':[0,0],'opening_bottom_world_m':0.9,'match_center_world_m':[0,0,1.5],
                'host_guid':'public-host','reference_guid':'public-reference',
                'target_center_offset_from_opening_m':[0,0,0]}},
            'required_product_count':1,'source':{'asset_id':f'asset{i}', 'scene_family':'shared-generator', 'license':'MIT'},
            'metrics':{'formal_scoring_frozen':False}})
    return base


def test_freeze_distinguishes_delegated_review_and_binds_inputs(tmp_path, monkeypatch):
    base = cases(tmp_path,monkeypatch)
    plan = formal.freeze(base,tmp_path/'plan.json',expected_count=2)
    assert len(plan['configuration']['order']) == 8
    assert all(r['review']['human_viewed'] is False for r in plan['cases'])
    assert formal.verify_plan(tmp_path/'plan.json')['configuration'] == plan['configuration']
    case=base/'formal-001'
    (case/'public/request.txt').write_text('改了题意',encoding='utf8')
    with pytest.raises(ValueError, match='FROZEN'):
        formal.verify_plan(tmp_path/'plan.json')


def test_pending_or_duplicate_source_cannot_freeze(tmp_path, monkeypatch):
    base=cases(tmp_path,monkeypatch)
    path=base/'formal-002/private/task.json'
    task=read_json(path)
    task['review']['status']='pending_human_review'
    write_json(path,task)
    with pytest.raises(ValueError,match='REVIEW'):
        formal.freeze(base,tmp_path/'plan.json',expected_count=2)
    task['review']['status']='accepted_by_delegation'
    task['source_sha256']='1'
    write_json(path,task)
    with pytest.raises(ValueError,match='DIFFERENT'):
        formal.freeze(base,tmp_path/'plan.json',expected_count=2)
    assert not (tmp_path/'plan.json').exists()


def test_frozen_evaluation_inputs_cannot_change_independently(tmp_path,monkeypatch):
    base=cases(tmp_path,monkeypatch,count=1)
    formal.freeze(base,tmp_path/'plan.json',expected_count=1)
    (base/'formal-001/private/mutation/damaged.ifc').write_text('changed D',encoding='utf8')
    with pytest.raises(ValueError,match='FROZEN_TASK_CHANGED'):
        formal.verify_plan(tmp_path/'plan.json')


def test_freeze_requires_complete_position_contract(tmp_path,monkeypatch):
    base=cases(tmp_path,monkeypatch)
    path=base/'formal-001/private/task.json'
    task=read_json(path)
    del task['author_expectations']['target-1']['target_center_offset_from_opening_m']
    write_json(path,task)
    with pytest.raises(ValueError,match='TARGET_CONTRACT'):
        formal.freeze(base,tmp_path/'plan.json',expected_count=2)


def test_scheduler_keeps_waiting_and_running_task_before_next_ready():
    states=[{'run_id':'first','status':'submitted'},{'run_id':'second','status':'awaiting_user'},
            {'run_id':'third','status':'ready'}]
    assert formal.next_task(states) == states[1]
    states[1]['status']='runtime_error'
    assert formal.next_task(states) == states[2]
    states[1]['status']='running'
    assert formal.next_task(states) == states[1]


def test_answer_only_requested_card_fact_and_never_entire_card():
    card={'status':'accepted_by_delegation','required_user_facts':[
        {'fact_id':'window_sill','question_keywords':['窗台','下沿','sill'], 'answer':'窗洞下沿距楼层850毫米。'},
        {'fact_id':'another_fact','question_keywords':['第二扇'], 'answer':'不应泄露的另一事实。'}]}
    question={'text':'窗台高度是多少？'}
    answer=formal.card_answer(question,card)
    assert answer['text']=='窗洞下沿距楼层850毫米。'
    assert answer['requested_fact_ids']==answer['answered_fact_ids']==['window_sill']
    assert answer['source']=='delegated_preapproved_card'
    assert formal.card_answer({'text':'给我原始文件和GUID'},card) is None


def test_summary_retains_failures_missing_usage_and_metric_denominators():
    rows=[{'arm':'A','status':'submitted','metric_status':'scored','success':True,
           'quantity':{'numerator':1,'denominator':1},'components':{'numerator':1,'denominator':1},
           'relations':{'numerator':3,'denominator':3},'known_tokens':10,'unknown_calls':0,'active_seconds':2},
          {'arm':'A','status':'runtime_error','metric_status':'scored','success':False,
           'quantity':{'numerator':0,'denominator':2},'components':{'numerator':0,'denominator':2},
           'relations':{'numerator':0,'denominator':6},'known_tokens':15,'unknown_calls':1,'active_seconds':3}]
    summary=formal.summarize(rows)['A']
    assert summary['task_success']=={'numerator':1,'denominator':2,'value':.5}
    assert summary['components']['denominator']==3
    assert summary['known_tokens']==25 and summary['total_tokens'] is None
    assert summary['unknown_calls']==1 and summary['active_seconds']==5


def test_d_card_answer_keeps_existing_warm_task_without_redispatch(tmp_path, monkeypatch):
    base=cases(tmp_path,monkeypatch,count=1)
    root=tmp_path/'run'
    ledger=Ledger(root/'control.sqlite')
    ledger.create('formal-001-D',case_id='formal-001',arm='D',budget=formal.BUDGETS['S1'])
    ledger.start('formal-001-D')
    ledger.ask('formal-001-D',question_id='sill',text='窗台高度是多少？')
    write_json(base/'formal-001/private/answer-card.json',{
        'status':'accepted_by_delegation', 'required_user_facts':['sill'],
        'facts':{'sill':{'keywords':['窗台'],'answer':'窗洞下沿距楼层850毫米。'}}})
    monkeypatch.setattr(formal,'experiment_plan',lambda root:{'configuration':{'cases_root':str(base)}})
    monkeypatch.setattr(formal.carrier,'status',lambda root:[ledger.snapshot('formal-001-D')])
    def answer(root,run_id,value):
        ledger.answer(run_id,question_id='sill',text=value['text'],event_id=value['event_id'])
    monkeypatch.setattr(formal.carrier,'answer',answer)
    monkeypatch.setattr(formal.carrier,'run',lambda *args:pytest.fail('warm D task was redispatched'))
    result=formal.run_next(root,answer_from_card=True)
    assert result['status']=='running'
    assert len([e for e in ledger.events('formal-001-D') if e['kind']=='answer'])==1


def test_initialize_cli_explicit_offline_mode_and_live_default(monkeypatch):
    seen=[]
    def initialize(root,plan,*,admission,mode):
        seen.append((mode,admission))
        if mode=='live' and admission is None:
            raise ValueError('CURRENT_STAGE_ADMISSION_REQUIRED')
        return {}
    monkeypatch.setattr(formal,'initialize',initialize)
    argv=['formal','initialize','--root','run','--plan','plan.json']
    monkeypatch.setattr(formal.sys,'argv',argv+['--mode','offline'])
    assert formal.main()==0
    assert seen==[('offline',None)]
    monkeypatch.setattr(formal.sys,'argv',argv)
    with pytest.raises(ValueError,match='ADMISSION'):
        formal.main()
    assert seen[-1]==('live',None)
