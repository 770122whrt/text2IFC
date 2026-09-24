import pytest
from scripts.ifc2text.rerun_v10 import fingerprint,RerunBudget
from text2ifc_ifc2text.goal_budget import GoalStopped

def test_snapshot_covers_dirty_untracked_and_ignores_only_bytecode(tmp_path):
    (tmp_path/'src').mkdir();p=tmp_path/'src/new.py';p.write_text('a=1',encoding='utf-8')
    before=fingerprint(tmp_path,['src']);p.write_text('a=2',encoding='utf-8')
    assert before!=fingerprint(tmp_path,['src'])

def test_one_rerun_preserves_usage_and_stops_at_three_new_reconstruction_calls(tmp_path):
    old={'limits':{'tokens':2000000},'historical':{'writing':21,'tokens':1400000},'attempts':[]}
    b=RerunBudget(tmp_path,old)
    assert b.snapshot()['calls']=={'writing':21,'reconstruction':14}
    for _ in range(3):
        n=b.reserve('reconstruction',100);b.settle(n,usage={'input_tokens':20,'output_tokens':30})
    assert b.snapshot()['tokens_used_or_reserved']==1400150
    with pytest.raises(GoalStopped): b.reserve('reconstruction',100)
    n=b.reserve('writing',100);b.settle(n,usage={'input_tokens':20,'output_tokens':30})
    with pytest.raises(GoalStopped): b.reserve('writing',100)
