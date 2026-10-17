"""Required structural facts remain questions, never entity selections."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from text2ifc_ifc_repair.api import _clarification
from text2ifc_ifc_repair.structural_resolution import resolve_structural_parameters


def parameters(family):
    keys=('base','top') if family=='column' else ('start','end')
    return {'axis':{keys[0]:{'x_mm':0,'y_mm':0,'z_mm':0},
                    keys[1]:{'x_mm':0 if family=='column' else 3000,'y_mm':0,'z_mm':3000}},
            'section':{'shape':'rectangle','width_mm':200,
                       'depth_mm' if family=='column' else 'height_mm':450}}


def clarification(decision):
    return _clarification('repair-public-scene',4,SimpleNamespace(
        operation_id='structural-1',reason_code=decision['reason_code'],
        candidates=decision['candidates'],property_preview=None))


@pytest.mark.parametrize(('family','missing'),[
    ('column','orientation'),('column','top'),('column','base'),
    ('beam','end'),('beam','start'),('beam','section'),('column','axis'),
])
def test_structural_hook_missing_facts_use_public_parameter_question(family,missing):
    values=parameters(family)
    if missing in ('axis','section'):values.pop(missing)
    elif missing!='orientation':values['axis'].pop(missing)
    result=resolve_structural_parameters(operation={'parameters':values},
        target_record=SimpleNamespace(ifc_class='IfcBuildingStorey'),repository=None,context={},family=family)
    assert result['status']=='clarification_required'
    expected={item['path'] for item in result['candidates']}
    question=clarification(result)
    assert question.reason_code=='missing_required_parameter'
    assert question.answer_modes==('add_detail','cancel') and question.candidates==()
    assert all(slot in question.question for slot in expected)
    assert question.run_id=='repair-public-scene' and question.state_version==4


@pytest.mark.parametrize('with_orientation',[False,True])
def test_square_or_explicitly_oriented_column_does_not_need_question(with_orientation):
    values=parameters('column')
    if with_orientation:values['section']['orientation']={'x':0,'y':1}
    else:values['section']['depth_mm']=200
    decision=resolve_structural_parameters(operation={'parameters':values},
        target_record=SimpleNamespace(ifc_class='IfcBuildingStorey'),repository=None,context={},family='column')
    assert decision['status']=='resolved'


def candidate():
    return {'token':'candidate-column','public_id':'public-column','ifc_class':'IfcColumn'}


def test_entity_candidate_with_extra_metadata_keeps_entity_selection():
    entity={**candidate(),'path':'/parameters/section/orientation','fact':'required'}
    question=clarification({'reason_code':'ambiguous','candidates':(entity,)})
    assert question.reason_code=='ambiguous_target'
    assert question.candidates[0].token==entity['token']
    assert 'select_candidate' in question.answer_modes


@pytest.mark.parametrize('invalid',[
    {'path':'/parameters/section/orientation'},
    {'path':'/private/reference','fact':'required'},
    {'path':'/parameters/section/orientation','fact':'required','public_id':'malformed-entity'},
])
def test_parameter_adapter_does_not_relax_malformed_entity_identity(invalid):
    with pytest.raises(KeyError):
        clarification({'reason_code':'missing_evidence','candidates':(deepcopy(invalid),)})
