"""Frozen retry checks: two additional calls, inherited usage and explicit closure."""
from __future__ import annotations
import copy
import pytest
from scripts.ifc2text.retry_closed_wall_v08 import ScopedRetryBudget, contour_from_text, compare_planar
from text2ifc_ifc2text.goal_budget import GoalStopped


def history():
    return {'tokens_used_or_reserved':1342637,'calls':{'writing':21,'reconstruction':12},
            'limits':{'writing':26,'reconstruction':12,'tokens':2000000},
            'halted':True,'attempts':[]}


def test_two_calls_only_with_inherited_tokens_and_calls(tmp_path):
    before=history(); frozen=copy.deepcopy(before)
    b=ScopedRetryBudget(tmp_path,before)
    assert b.snapshot()['calls']=={'writing':21,'reconstruction':12}
    assert b.snapshot()['tokens_used_or_reserved']==1342637
    with pytest.raises(GoalStopped): b.reserve('writing',100)
    for _ in range(2):
        n=b.reserve('reconstruction',200)
        b.settle(n,usage={'prompt_tokens':40,'completion_tokens':60})
    reopened=ScopedRetryBudget(tmp_path,before)
    assert reopened.snapshot()['calls']['reconstruction']==14
    assert reopened.snapshot()['tokens_used_or_reserved']==1342837
    with pytest.raises(GoalStopped): reopened.reserve('reconstruction',200)
    assert before==frozen


def test_no_token_reset_or_unsettled_predecessor(tmp_path):
    p=history();p['tokens_used_or_reserved']=1999990
    b=ScopedRetryBudget(tmp_path/'token',p)
    with pytest.raises(GoalStopped): b.reserve('reconstruction',11)
    p=history();p['attempts']=[{'status':'reserved'}]
    with pytest.raises(GoalStopped):ScopedRetryBudget(tmp_path/'reserved',p)


def test_failure_halts_reopened_retry(tmp_path):
    b=ScopedRetryBudget(tmp_path,history());n=b.reserve('reconstruction',200)
    b.settle(n,failure='connection')
    with pytest.raises(GoalStopped):ScopedRetryBudget(tmp_path,history()).reserve('reconstruction',100)


def test_closed_contour_and_invalid_rejected():
    text='底面闭合外轮廓（世界XY，mm）(0.0,0.0)→(100.0,0.0)→(90.0,20.0)→(0.0,20.0)→(0.0,0.0)；底面Z=0.0；+Z拉伸 3000.0。'
    points,z,h=contour_from_text(text)
    assert points[0]==points[-1] and z==0. and h==3000.
    with pytest.raises(ValueError):contour_from_text(text.replace('→(0.0,0.0)；','；'))
    bow_tie=text.replace('(100.0,0.0)','(100.0,20.0)').replace('(90.0,20.0)','(100.0,0.0)')
    with pytest.raises(ValueError):contour_from_text(bow_tie)


def test_local_diagnostic_threshold_not_global_gate():
    a=[[0.,0.],[100.,0.],[100.,20.],[0.,20.],[0.,0.]]
    b=[[x+.049,y+.049] for x,y in a]
    row=compare_planar(a,b)
    assert .055<row['hausdorff_densified_mm']<.1
    assert row['diagnostic_0_1mm_pass']
    assert row['legacy_20mm_planar_pass']
    c=[[x+1.,y] for x,y in a]
    row=compare_planar(a,c)
    assert not row['diagnostic_0_1mm_pass'] and row['legacy_20mm_planar_pass']
