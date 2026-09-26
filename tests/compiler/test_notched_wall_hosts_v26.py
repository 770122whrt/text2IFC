"""Straight polygonal wall notches retain their actual shape and layer usage."""
import copy

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.shape
import pytest
from shapely.geometry import Polygon

from tests.compiler.test_polygon_wall_hosts_v24 import document,record,positioned_profile
from text2ifc_compiler import compile_document
from text2ifc_contract.validation_v2 import validate_v2_document


def notched_document():
    value=document();value['schema_version']='bim-json/2.6'
    record(value,'wall-1')['attributes']['Representation']['profile']['points']=[
        [-2480,-100],[2500,-100],[2500,100],[-2500,100],[-2500,0],[-2480,0],[-2480,-100]]
    return value


@pytest.mark.parametrize('rotate,reverse',[(False,False),(True,False),(False,True)])
def test_notched_wall_layers_opening_and_mesh_volume(tmp_path,rotate,reverse):
    value=notched_document()
    if rotate:positioned_profile(value)
    points=record(value,'wall-1')['attributes']['Representation']['profile']['points']
    if reverse:points.reverse()
    before=copy.deepcopy(value)
    assert not validate_v2_document(value)
    result=compile_document(value,tmp_path/'notched.ifc')
    assert result.success,(result.input_issues,result.ifc_issues)
    model=ifcopenshell.open(str(result.output_path));wall=model.by_type('IfcWall')[0]
    assert len(wall.HasOpenings)==1
    assert wall.HasOpenings[0].RelatedOpeningElement.HasFillings
    material=ifcopenshell.util.element.get_material(wall)
    assert material.ForLayerSet.MaterialLayers[0].LayerThickness==200
    settings=ifcopenshell.geom.settings();settings.set(settings.DISABLE_OPENING_SUBTRACTIONS,True)
    shape=ifcopenshell.geom.create_shape(settings,wall)
    assert ifcopenshell.util.shape.get_volume(shape.geometry)==pytest.approx(Polygon(points).area*3000/1e9,abs=1e-7)
    assert value==before


@pytest.mark.parametrize('fault',['old-version','crossing','wrong-layer','taper'])
def test_notched_support_preserves_other_rejections(fault):
    value=notched_document();wall=record(value,'wall-1')
    if fault=='old-version':value['schema_version']='bim-json/2.5'
    if fault=='crossing':wall['attributes']['Representation']['profile']['points']=[[-2500,-100],[2500,100],[-2500,100],[2500,-100],[-2500,-100]]
    if fault=='wrong-layer':wall['materials'][0]['layers'][0]['thickness']=199
    if fault=='taper':wall['attributes']['Representation']['profile']['points']=[[-2500,-100],[2500,-50],[2500,50],[-2500,100],[-2500,-100]]
    assert validate_v2_document(value)


def test_rectangle_in_notch_has_zero_wall_overlap():
    from text2ifc_contract.polygon_wall import _intersection_area
    points=[[-2,-1],[2,-1],[2,1],[1,1],[1,0],[-1,0],[-1,1],[-2,1]]
    assert _intersection_area(points,-.9,.9,.1,.9,allow_concave=True)==0
    assert _intersection_area(points,-2,2,.1,.9,allow_concave=True)==pytest.approx(1.6)


def test_notched_open_profile_can_use_exact_closure_recovery():
    from text2ifc_agent.polygon_closure import recover_polygon_closures
    value=notched_document();points=record(value,'wall-1')['attributes']['Representation']['profile']['points'];points.pop()
    recovered=recover_polygon_closures(value)
    assert recovered['eligible']
    assert record(recovered['candidate'],'wall-1')['attributes']['Representation']['profile']['points']==points+[points[0]]


def test_authoring_contract_adds_notches_without_rewriting_prior_contract():
    from text2ifc_agent.authoring_contract import build_authoring_contract
    old=build_authoring_contract(version='1.6')
    new=build_authoring_contract(version='1.7')
    assert 'concave' in old['geometry_encoding']['polygon_wall_host']['unsupported']
    assert 'notch' in new['geometry_encoding']['polygon_wall_host']['geometry']
    assert 'concave' not in new['geometry_encoding']['polygon_wall_host']['unsupported']
    assert new['geometry_encoding']['component_geometry']==old['geometry_encoding']['component_geometry']
