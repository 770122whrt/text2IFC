"""Names describe proven connections, not only placement ownership."""
import copy
import pytest
from tests.agent.test_cross_storey_name_boundary import _case, _gate


@pytest.mark.parametrize('labels',[('首层','二层','三层'),('Ground','Upper','Roof'),('地下','夹层','屋顶')])
@pytest.mark.parametrize('kind',['IfcStair','IfcStairFlight'])
@pytest.mark.parametrize('wording',['synonym','destination_only'])
def test_proven_endpoint_does_not_require_literal_owner_name(labels,kind,wording):
    candidate,expected=_case(labels,kind)
    candidate['entities'][-1]['attributes']['Name']=(f'从起点到{labels[1]}的楼梯' if wording=='synonym' else f'{labels[1]}楼梯')
    before=copy.deepcopy(candidate)
    assert _gate(candidate,expected)['status']=='passed'
    assert candidate==before


def opening_case(labels=('下层','平台层','屋面层')):
    candidate,expected=_case(labels,'IfcStair')
    bounds={'x':[1250,2250],'y':[3500,6500]}
    expected['stairs'][0]['opening_bounds']=copy.deepcopy(bounds)
    expected['slabs']=[{'id':'deck-z','storey':'level-1','opening':{'id':'void-q','bounds':copy.deepcopy(bounds)}}]
    candidate['entities'].extend([
        {'id':'deck-z','ifc_class':'IfcSlab','attributes':{'Name':labels[1]+'楼板','ObjectPlacement':{'relative_to':'level-1'}}},
        {'id':'void-q','ifc_class':'IfcOpeningElement','attributes':{'Name':f'{labels[1]}楼板{labels[0]}至{labels[1]}楼梯洞口','ObjectPlacement':{'relative_to':'deck-z'}}}])
    candidate['relationships'].append({'id':'void-rel','ifc_class':'IfcRelVoidsElement','attributes':{'RelatingBuildingElement':'deck-z','RelatedOpeningElement':'void-q'}})
    return candidate,expected


@pytest.mark.parametrize('labels',[('下层','平台层','屋面层'),('Base','Mezzanine','Roof'),('Niveau A','Niveau B','Niveau C')])
def test_frozen_opening_service_context_is_not_wrong_ownership(labels):
    candidate,expected=opening_case(labels);before=copy.deepcopy(candidate)
    assert _gate(candidate,expected)['status']=='passed'
    assert candidate==before


@pytest.mark.parametrize('failure',['missing_stair','duplicate_stair','wrong_destination','wrong_bounds','missing_bounds',
    'missing_void','duplicate_void','wrong_host','wrong_host_storey','duplicate_opening','ordinary_wall','unrelated_level','candidate_only'])
def test_opening_context_requires_unique_frozen_relationship(failure):
    c,e=opening_case()
    if failure=='missing_stair':e['stairs']=[]
    elif failure=='duplicate_stair':e['stairs']*=2
    elif failure=='wrong_destination':e['stairs'][0]['to_storey']='level-2'
    elif failure=='wrong_bounds':e['stairs'][0]['opening_bounds']['x'][0]+=100
    elif failure=='missing_bounds':e['stairs'][0].pop('opening_bounds')
    elif failure=='missing_void':c['relationships']=[]
    elif failure=='duplicate_void':c['relationships']*=2
    elif failure=='wrong_host':c['relationships'][0]['attributes']['RelatingBuildingElement']='flight-a'
    elif failure=='wrong_host_storey':c['entities'][-2]['attributes']['ObjectPlacement']['relative_to']='level-2'
    elif failure=='duplicate_opening':e['slabs']*=2
    elif failure=='ordinary_wall':c['entities'][-1]['ifc_class']='IfcWall'
    elif failure=='unrelated_level':c['entities'][-1]['attributes']['Name']+='屋面层'
    else:
        e['stairs']=[]
        c['entities'][-1]['attributes']['stair_id']='flight-a'
    assert _gate(c,e)['status']=='failed'
