"""Synthetic cutter/host intersection controls; never repair-model evidence."""
import importlib
import math

import ifcopenshell
from ifcopenshell.util.element import copy as copy_entity, copy_deep
import pytest

from tests.ifc_repair.repair_comparison.test_preparation import sample


def api():
    return importlib.import_module('scripts.ifc_repair.repair_comparison.damage_geometry')


@pytest.fixture
def openings(sample):
    _,source,_=sample
    def build(count=1,angle=0.,positions=None):
        model=ifcopenshell.open(str(source))
        wall=model.by_type('IfcWall')[0]
        original=model.by_type('IfcOpeningElement')[0]
        wall.Representation.Representations[0].Items[0].SweptArea.YDim=.15
        original.Representation.Representations[0].Items[0].SweptArea.YDim=1.
        radians=math.radians(angle)
        # Rotate actual wall and cutters together; no axis-aligned assumption.
        for entity in (wall,original):
            placement=copy_deep(model,entity.ObjectPlacement)
            placement.RelativePlacement.Axis=model.createIfcDirection((0.,0.,1.))
            placement.RelativePlacement.RefDirection=model.createIfcDirection((math.cos(radians),math.sin(radians),0.))
            entity.ObjectPlacement=placement
        guids=[]
        xs=positions if positions is not None else [-1.+index for index in range(count)]
        for index,x in enumerate(xs):
            opening=original if index==0 else copy_entity(model,original)
            if index:
                opening.Representation=copy_deep(model,original.Representation,exclude=('IfcGeometricRepresentationContext',))
                opening.ObjectPlacement=copy_deep(model,original.ObjectPlacement)
                model.create_entity('IfcRelVoidsElement',GlobalId=ifcopenshell.guid.new(),OwnerHistory=wall.OwnerHistory,
                    RelatingBuildingElement=wall,RelatedOpeningElement=opening)
            opening.ObjectPlacement.RelativePlacement.Location.Coordinates=(float(x*math.cos(radians)),float(x*math.sin(radians)),0.)
            guids.append(opening.GlobalId)
        model.write(str(source))
        return model,source,guids,wall.GlobalId
    return build


@pytest.mark.parametrize('count',[1,2,3])
@pytest.mark.parametrize('angle',[0.,37.,90.])
def test_overshooting_cutters_measure_only_wall_intersection(openings,count,angle):
    model,source,guids,wall_guid=openings(count,angle)
    serialized=model.to_string();source_bytes=source.read_bytes()
    before_products={p.GlobalId for p in model.by_type('IfcProduct')}
    result=api().effective_opening_volumes(model,guids)
    expected=.9*.15*2.1
    assert len(result['openings'])==count
    for row in result['openings']:
        assert row['wall_guid']==wall_guid
        assert row['effective_volume_m3']==pytest.approx(expected,abs=1e-7)
        assert row['raw_cutter_volume_m3']==pytest.approx(.9*1.*2.1,abs=1e-7)
    grouped=result['walls'][wall_guid]
    assert grouped['group_delta_m3']==pytest.approx(count*expected,abs=1e-7)
    assert grouped['non_overlapping'] is True
    assert model.to_string()==serialized and source.read_bytes()==source_bytes
    assert {p.GlobalId for p in model.by_type('IfcProduct')}==before_products
    assert all(len(model.by_guid(guid).VoidsElements)==1 for guid in guids)


def test_cutter_entirely_outside_wall_is_not_damage(openings):
    model,_,guids,_=openings(positions=[10.])
    with pytest.raises(ValueError,match='NONPOSITIVE_EFFECTIVE_OPENING_VOLUME'):
        api().effective_opening_volume(model,guids[0])


def test_nonunique_host_fails_without_changing_input(openings):
    model,_,guids,_=openings()
    relation=model.by_guid(guids[0]).VoidsElements[0]
    copy_entity(model,relation)
    before=model.to_string()
    with pytest.raises(ValueError,match='OPENING_REQUIRES_UNIQUE_WALL'):
        api().effective_opening_volume(model,guids[0])
    assert model.to_string()==before


def test_overlapping_cutters_are_diagnosed_instead_of_summing_marginals(openings):
    model,source,guids,_=openings(count=2,positions=[-.2,.2])
    before=source.read_bytes();serialized=model.to_string()
    # Each single opening has a positive unique contribution. That does not make
    # the sum equal to closing both cuts, which also fills the overlap region.
    assert all(api().effective_opening_volume(model,g)['effective_volume_m3']>0 for g in guids)
    with pytest.raises(api().DamageGeometryError,match='OVERLAPPING_OPENINGS_UNSUPPORTED') as caught:
        api().effective_opening_volumes(model,guids)
    evidence=caught.value.evidence
    assert evidence['group_delta_m3']>evidence['effective_sum_m3']
    assert evidence['non_overlapping'] is False
    assert model.to_string()==serialized and source.read_bytes()==before


def test_duplicate_selection_and_more_than_three_are_rejected(openings):
    model,_,guids,_=openings()
    with pytest.raises(ValueError,match='DUPLICATE_OPENINGS'):
        api().effective_opening_volumes(model,[guids[0],guids[0]])
    with pytest.raises(ValueError,match='ONE_TO_THREE_OPENINGS_REQUIRED'):
        api().effective_opening_volumes(model,['a','b','c','d'])


def test_negative_counterfactual_delta_is_not_accepted(openings,monkeypatch):
    model,_,guids,wall_guid=openings()
    value=api()._volume_m3(model.by_guid(wall_guid))
    monkeypatch.setattr(api(),'_unvoided_volume',lambda *args:value-.1)
    with pytest.raises(api().DamageGeometryError,match='NONPOSITIVE_EFFECTIVE_OPENING_VOLUME') as caught:
        api().effective_opening_volume(model,guids[0])
    assert caught.value.evidence['effective_volume_m3']<0


def test_nonfinite_engine_measurement_is_a_diagnostic(openings,monkeypatch):
    model,_,guids,_=openings()
    monkeypatch.setattr(api().ifcopenshell.util.shape,'get_volume',lambda _:float('nan'))
    with pytest.raises(api().DamageGeometryError,match='NONPOSITIVE_OR_NONFINITE_GEOMETRY_VOLUME') as caught:
        api().effective_opening_volume(model,guids[0])
    assert caught.value.evidence['volume_m3'] is None
