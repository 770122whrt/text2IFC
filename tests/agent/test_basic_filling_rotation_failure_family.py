"""Freeze the rotated-host double-rotation failure independently of live output."""
import copy
import pytest
from scripts.presentation.validate_semantic_appearance import candidate
from text2ifc_compiler import compile_document


@pytest.mark.parametrize('template',['window-single','window-double-vertical','door-left','door-right'])
@pytest.mark.parametrize('double_rotate',[False,True])
def test_rotated_host_requires_local_identity_axes(tmp_path,template,double_rotate):
    value=copy.deepcopy(candidate(template))
    records={r['id']:r for r in value['entities']}
    records['wall-1']['attributes']['ObjectPlacement']['ref_direction']=[0,1,0]
    for identity in ['opening-1','door-1']:
        records[identity]['attributes']['ObjectPlacement']['ref_direction']=[0,1,0] if double_rotate else [1,0,0]
    output=tmp_path/'output.ifc'
    result=compile_document(value,output)
    assert result.success is not double_rotate
    assert output.exists() is not double_rotate
    if double_rotate:
        assert any(issue.code=='BASIC_FILLING_CONSTRAINT_CONFLICT' for issue in result.input_issues)
