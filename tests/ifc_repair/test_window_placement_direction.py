"""Public same-Type direction family, independent of benchmark identities."""
from types import SimpleNamespace

import numpy as np
import pytest

from text2ifc_ifc_repair.window_geometry import select_window_placement_in_opening


class Product:
    def __init__(self, number, kind, matrix):
        self.number,self.kind,self.ObjectPlacement=number,kind,matrix
    def id(self):
        return self.number
    def is_a(self, name):
        return name==self.kind


def turn(sign,translation=(0,0,0)):
    matrix=np.eye(4)
    matrix[0,0]=matrix[1,1]=sign
    matrix[:3,3]=translation
    return matrix


@pytest.mark.parametrize('opening_sign,window_sign,world_turn',[(1,1,1),(-1,1,1),(-1,-1,1),(-1,1,-1)])
@pytest.mark.parametrize('scale',[1,.001])
def test_direction_uses_wall_axis_not_imported_opening_axis(monkeypatch,opening_sign,window_sign,world_turn,scale):
    import text2ifc_ifc_repair.window_geometry as geometry
    wall=Product(1,'IfcWall',turn(world_turn,(3000/scale,4000/scale,1000/scale)))
    imported=Product(2,'IfcOpeningElement',wall.ObjectPlacement@turn(opening_sign))
    imported.VoidsElements=[SimpleNamespace(RelatingBuildingElement=wall)]
    peer=Product(3,'IfcWindow',wall.ObjectPlacement@turn(window_sign))
    peer.FillsVoids=[SimpleNamespace(RelatingOpeningElement=imported,is_a=lambda n:n=='IfcRelFillsElement')]
    new=Product(4,'IfcWindow',np.eye(4))
    generated=Product(5,'IfcOpeningElement',wall.ObjectPlacement.copy())
    prototype=SimpleNamespace(ObjectTypeOf=[SimpleNamespace(RelatedObjects=[peer])])
    monkeypatch.setattr(geometry.ifcopenshell.util.placement,'get_local_placement',lambda p:p)
    monkeypatch.setattr(geometry.ifcopenshell.util.unit,'calculate_unit_scale',lambda _:scale)
    generated.file=object()
    monkeypatch.setattr(geometry,'product_local_geometry_bounds_mm',lambda _: {'x':[0,900],'y':[0,100],'z':[0,1800]})
    monkeypatch.setattr(geometry,'product_geometry_bounds_in_host_mm',lambda *_:{'x':[0,900],'y':[0,200],'z':[0,1800]})
    monkeypatch.setattr(geometry,'straight_wall_axis',lambda _:([0,0,0],[10000,0,0]))
    result=select_window_placement_in_opening(new,generated,prototype,host_wall=wall)
    assert result['ref_direction']==(float(window_sign),0.,0.)
    assert result['orientation_source']=='surviving_same_type_wall_axis'


def test_conflicting_same_host_directions_are_not_silently_chosen(monkeypatch):
    import text2ifc_ifc_repair.window_geometry as geometry
    wall=Product(1,'IfcWall',np.eye(4));opening=Product(2,'IfcOpeningElement',np.eye(4))
    opening.VoidsElements=[SimpleNamespace(RelatingBuildingElement=wall)]
    peers=[]
    for i,sign in enumerate([1,-1]):
        peer=Product(i+3,'IfcWindow',turn(sign))
        peer.FillsVoids=[SimpleNamespace(RelatingOpeningElement=opening,is_a=lambda _:True)]
        peers.append(peer)
    prototype=SimpleNamespace(ObjectTypeOf=[SimpleNamespace(RelatedObjects=peers)])
    monkeypatch.setattr(geometry.ifcopenshell.util.placement,'get_local_placement',lambda p:p)
    monkeypatch.setattr(geometry,'straight_wall_axis',lambda _:([0,0,0],[10000,0,0]))
    monkeypatch.setattr(geometry,'product_local_geometry_bounds_mm',lambda _: {'x':[0,900],'y':[0,100],'z':[0,1800]})
    monkeypatch.setattr(geometry,'product_geometry_bounds_in_host_mm',lambda *_:{'x':[0,900],'y':[0,200],'z':[0,1800]})
    with pytest.raises(ValueError,match='ORIENTATION_AMBIGUOUS'):
        select_window_placement_in_opening(Product(10,'IfcWindow',np.eye(4)),opening,prototype,host_wall=wall)
