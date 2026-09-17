"""Text-only restatement contract; this is not automated semantic verification."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('text_restatement',ROOT/'scripts/ifc2text/clarify_public_description.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def payload():
    return {'origin':'agent_restatement_of_public_description','question_ids':['q1'],
            'source_quotes':['未知边界不补造。'],'answer':'重述已有说明：保留轮廓，不补造未知边界。'}


def test_original_quote_and_explicit_nonhuman_origin_accepted():
    p=payload()
    assert module.checked_restatement(p,'空间已给。未知边界不补造。',{'q1'})==p['answer']


@pytest.mark.parametrize('fault',['quote','question','origin','extra'])
def test_missing_provenance_or_nonpublic_quote_rejected(fault):
    p=payload()
    if fault=='quote': p['source_quotes']=['源IFC中另有砖墙。']
    if fault=='question': p['question_ids']=['q2']
    if fault=='origin': p['origin']='human_confirmed'
    if fault=='extra': p['private_source_fact']='brick'
    with pytest.raises(ValueError): module.checked_restatement(p,'未知边界不补造。',{'q1'})
