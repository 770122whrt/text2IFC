"""Offline hosted-opening family for a wall Axis away from its Body centre.

All source geometry is public and synthetic. Expected normal ranges, along-
axis positions and removed volumes are independently authored below. These
tests are regression evidence, not model capability or formal-task results.
"""
from __future__ import annotations

import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import numpy as np
import pytest

from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.operations.hosted_opening import create_hosted_opening
from tests.ifc_repair.test_window_installation_anchor import PublicWindowProvider, scene


def offset_wall_scene(*, normal_range_mm=(0.,150.), millimetres=False,
                      wall_angle=0., axis_angle=0., axis_start_mm=(0.,0.)):
    """A rectangular wall whose physical normal range need not straddle Axis.

    The retained public window and its existing cutter move with the authored
    wall cross-section. Rotating Axis also rotates Body and retained opening
    locally; wall placement rotation is a separate transform.
    """
    lower,upper = normal_range_mm
    thickness = upper-lower
    center = (lower+upper)/2
    model,wall,retained_opening,reference,_,unit = scene(
        millimetres=millimetres,angle=wall_angle,normal=center-45.,
        cut_depth=thickness,cut_center=center,
    )
    cosine,sine = math.cos(math.radians(axis_angle)),math.sin(math.radians(axis_angle))
    start_x,start_y = axis_start_mm
    body = next(r for r in wall.Representation.Representations if r.RepresentationIdentifier=='Body')
    solid = body.Items[0]
    solid.SweptArea.YDim = thickness*unit
    solid.SweptArea.Position.Location.Coordinates = (3500*unit,center*unit)
    solid.Position.Location.Coordinates = (start_x*unit,start_y*unit,0.)
    solid.Position.RefDirection = model.createIfcDirection((cosine,sine,0.))
    axis = next(r for r in wall.Representation.Representations if r.RepresentationIdentifier=='Axis')
    axis.Items[0].Points[0].Coordinates = (start_x*unit,start_y*unit)
    axis.Items[0].Points[1].Coordinates = ((start_x+7000*cosine)*unit,(start_y+7000*sine)*unit)
    placement = retained_opening.ObjectPlacement.RelativePlacement
    placement.Location.Coordinates = ((start_x+5000*cosine)*unit,(start_y+5000*sine)*unit,700*unit)
    placement.RefDirection.DirectionRatios = (cosine,sine,0.)
    return model,wall,retained_opening,reference,unit


def _axis_frame_bounds(product,wall,*,unit,axis_angle=0.,axis_start_mm=(0.,0.)):
    """Project actual mesh vertices using the independently authored frame."""
    relative = np.linalg.inv(ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)) @ ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),product)
    vertices = shape.geometry.verts
    cosine,sine = math.cos(math.radians(axis_angle)),math.sin(math.radians(axis_angle))
    points = []
    for index in range(0,len(vertices),3):
        # Mesh vertices are SI metres; placement translations are project units.
        local = np.array([vertices[index]*1000*unit,vertices[index+1]*1000*unit,
                          vertices[index+2]*1000*unit,1.])
        placed = (relative @ local)[:3]/unit
        x,y = placed[0]-axis_start_mm[0],placed[1]-axis_start_mm[1]
        points.append((x*cosine+y*sine,-x*sine+y*cosine,placed[2]))
    return [
        [min(point[axis] for point in points),max(point[axis] for point in points)]
        for axis in range(3)
    ]


def _wall_volume(wall):
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),wall)
    return ifcopenshell.util.shape.get_volume(shape.geometry)


def _opening_operation(wall):
    return {
        'operation_id':'public-new-hosted-opening',
        'target':{'wall_global_id':wall.GlobalId},
        'parameters':{
            'position':{'center_offset_mm':1500.},
            'opening':{'width_mm':900.,'height_mm':1200.,'sill_height_mm':700.},
        },
    }


def _snapshot(model,roots):
    return {entity.id():entity.to_string()
            for root in roots for entity in model.traverse(root)}


@pytest.mark.parametrize('normal_range,millimetres,wall_angle,axis_angle,axis_start',[
    ((0.,150.),False,0.,0.,(0.,0.)),
    ((-160.,0.),True,90.,0.,(0.,0.)),
    ((-75.,75.),False,180.,0.,(0.,0.)),
    ((40.,220.),True,37.,0.,(0.,0.)),
    ((-220.,-40.),False,-37.,0.,(0.,0.)),
    ((0.,250.),True,180.,0.,(400.,80.)),
    ((-80.,80.),False,90.,90.,(120.,-80.)),
    ((0.,180.),False,37.,90.,(120.,-80.)),
    ((-180.,0.),True,180.,180.,(400.,80.)),
    ((30.,170.),True,37.,37.,(400.,-150.)),
    ((0.,90.),True,0.,-37.,(125.,-85.)),
    ((-75.,75.),True,45.,37.,(120.,80.)),
])
def test_new_hosted_opening_spans_physical_wall_not_axis(
    tmp_path,normal_range,millimetres,wall_angle,axis_angle,axis_start,
):
    source_model,source_wall,_,_,unit = offset_wall_scene(
        normal_range_mm=normal_range,millimetres=millimetres,
        wall_angle=wall_angle,axis_angle=axis_angle,axis_start_mm=axis_start,
    )
    source = tmp_path/'public.ifc'
    source_model.write(str(source))
    source_bytes = source.read_bytes()
    model = ifcopenshell.open(str(source))
    wall = model.by_guid(source_wall.GlobalId)
    # Work on a separately reopened public model, as production transactions do.
    originals = {entity.id():entity.to_string() for entity in model}
    before_volume = _wall_volume(wall)
    created = create_hosted_opening(model=model,operation=_opening_operation(wall),wall=wall)
    opening = created['opening']
    actual = _axis_frame_bounds(opening,wall,unit=unit,axis_angle=axis_angle,axis_start_mm=axis_start)
    assert actual[0]==pytest.approx([1050.,1950.],abs=1e-5)
    assert actual[2]==pytest.approx([700.,1900.],abs=1e-5)
    assert actual[1]==pytest.approx(normal_range,abs=1e-5)
    assert created['opening_depth_mm']==pytest.approx(normal_range[1]-normal_range[0],abs=1e-5)
    void = created['voids_relationship']
    assert void.RelatingBuildingElement==wall and void.RelatedOpeningElement==opening
    assert len(opening.VoidsElements)==1
    # Matching depth alone misses half-wall cuts; the complete intended void
    # must actually be removed from the wall at a nonoverlapping public site.
    expected_removed_m3 = 900.*1200.*(normal_range[1]-normal_range[0])/1e9
    assert before_volume-_wall_volume(wall)==pytest.approx(expected_removed_m3,abs=1e-7)
    assert {key:model.by_id(key).to_string() for key in originals}==originals
    output = tmp_path/'candidate.ifc'
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    reopened_bounds = _axis_frame_bounds(
        reopened.by_guid(opening.GlobalId),reopened.by_guid(wall.GlobalId),
        unit=unit,axis_angle=axis_angle,axis_start_mm=axis_start,
    )
    for expected,measured in zip(actual,reopened_bounds):
        assert measured==pytest.approx(expected,abs=1e-5)
    assert source.read_bytes()==source_bytes


@pytest.mark.parametrize('normal_range,millimetres,wall_angle,axis_start',[
    ((0.,150.),False,0.,(0.,0.)),
    ((-160.,0.),True,90.,(0.,0.)),
    ((-75.,75.),False,180.,(0.,0.)),
    ((40.,220.),True,37.,(300.,80.)),
])
def test_public_window_api_reopens_a_full_depth_hole_and_preserves_public_source(
    tmp_path,normal_range,millimetres,wall_angle,axis_start,
):
    model,wall,retained_opening,reference,unit = offset_wall_scene(
        normal_range_mm=normal_range,millimetres=millimetres,
        wall_angle=wall_angle,axis_start_mm=axis_start,
    )
    preserved = _snapshot(model,[wall.Representation,wall.ObjectPlacement,
                                 retained_opening,reference])
    before_volume = _wall_volume(wall)
    source = tmp_path/'public.ifc'
    model.write(str(source))
    source_bytes = source.read_bytes()
    provider = PublicWindowProvider()
    result = RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(
        source,'Add a 900 by 1200 mm window at 1500 mm along the public wall Axis, '
        'with a 700 mm sill. Create the matching through-wall opening. Use the '
        'retained public window type, complete frame, glazing and installation. '
        'Keep the existing wall Body, retained opening and reference unchanged.',
    )
    assert result.status=='succeeded',result.to_dict()
    run = tmp_path/'run'/result.run_directory
    output = ifcopenshell.open(str(run/result.artifacts['successful_ifc']))
    created = [window for window in output.by_type('IfcWindow') if window.GlobalId!=reference.GlobalId]
    assert len(created)==1
    window = created[0]
    assert window.OverallWidth/unit==pytest.approx(900.)
    assert window.OverallHeight/unit==pytest.approx(1200.)
    assert len(window.FillsVoids)==1
    opening = window.FillsVoids[0].RelatingOpeningElement
    output_wall = output.by_guid(wall.GlobalId)
    bounds = _axis_frame_bounds(opening,output_wall,unit=unit,axis_start_mm=axis_start)
    assert bounds[0]==pytest.approx([1050.,1950.],abs=1e-5)
    assert bounds[2]==pytest.approx([700.,1900.],abs=1e-5)
    assert bounds[1]==pytest.approx(normal_range,abs=1e-5)
    assert opening.VoidsElements[0].RelatingBuildingElement==output_wall
    assert before_volume-_wall_volume(output_wall)==pytest.approx(
        900.*1200.*(normal_range[1]-normal_range[0])/1e9,abs=1e-7,
    )
    assert {key:output.by_id(key).to_string() for key in preserved}==preserved
    assert source.read_bytes()==source_bytes
    assert all('Gold' not in str(call['state']) for call in provider.calls)


@pytest.mark.parametrize('fault',['missing_axis','polyline_with_three_points'])
def test_unsupported_axis_still_fails_before_creating_any_opening(fault):
    model,wall,*_ = offset_wall_scene()
    axis = next(r for r in wall.Representation.Representations if r.RepresentationIdentifier=='Axis')
    if fault=='missing_axis':
        wall.Representation.Representations = [r for r in wall.Representation.Representations if r!=axis]
    else:
        points = axis.Items[0].Points
        axis.Items[0].Points = [points[0],model.createIfcCartesianPoint((3.,1.)),points[1]]
    before = model.to_string()
    with pytest.raises(ValueError,match='UNSUPPORTED_WALL_GEOMETRY'):
        create_hosted_opening(model=model,operation=_opening_operation(wall),wall=wall)
    assert model.to_string()==before
