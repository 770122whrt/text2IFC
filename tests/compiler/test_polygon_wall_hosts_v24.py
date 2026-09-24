"""Independent polygon-host failure family; deterministic, not Provider evidence."""
import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as util
import ifcopenshell.util.shape
import numpy as np
import pytest

from text2ifc_compiler import compile_document
from text2ifc_contract.validation_v2 import validate_v2_document


def record(document, entity_id):
    return next(e for e in document['entities'] if e['id'] == entity_id)


def document():
    value = json.loads((Path(__file__).parents[1] / 'contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    value['schema_version'] = 'bim-json/2.4'
    wall = record(value, 'wall-1')
    wall['attributes']['Representation']['profile'] = {
        'kind': 'polygon', 'points': [[-2500, -100], [2300, -100], [2500, 100], [-2500, 100], [-2500, -100]],
    }
    wall['materials'] = [{'kind': 'material_layer_set_usage', 'layer_set_name': 'assembly',
        'direction': 'AXIS2', 'direction_sense': 'POSITIVE', 'offset_from_reference_line': -100,
        'layers': [{'name': 'Concrete', 'thickness': 200}]}]
    record(value, 'door-1')['attributes']['Representation'] = {
        'kind': 'basic_filling', 'template_id': 'door-left',
        'template_version': 'text2ifc/basic-filling/1.0', 'width': 900, 'height': 2100,
        'depth': 200, 'parameters': {},
    }
    return value


def positioned_profile(value):
    """Same wall in a shifted/rotated representation frame, not object placement."""
    rep = record(value, 'wall-1')['attributes']['Representation']
    points = np.array(rep['profile']['points'])
    a = np.deg2rad(37)
    rotation = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    origin = np.array([137., -213.])
    rep['profile']['points'] = ((points - origin) @ rotation).tolist()
    rep['position'] = {'origin': [*origin, 0], 'axis': [0, 0, 1], 'ref_direction': [np.cos(a), np.sin(a), 0]}


@pytest.mark.parametrize('positioned,clockwise', [(False, False), (True, False), (True, True)])
def test_polygon_with_material_and_filling_compiles_without_mutation(tmp_path, positioned, clockwise):
    value = document()
    if positioned:
        positioned_profile(value)
    if clockwise:
        record(value, 'wall-1')['attributes']['Representation']['profile']['points'].reverse()
    before = copy.deepcopy(value)
    result = compile_document(value, tmp_path / 'polygon.ifc')
    assert result.success, (result.input_issues, result.ifc_issues)
    assert value == before
    model = ifcopenshell.open(str(result.output_path))
    wall = next(e for e in model.by_type('IfcWall') if util.get_psets(e).get('Pset_text2IFCIdentity', {}).get('BimJsonId') == 'wall-1')
    material = util.get_material(wall)
    assert material.ForLayerSet.MaterialLayers[0].LayerThickness == 200
    assert len(wall.HasOpenings) == 1
    assert wall.HasOpenings[0].RelatedOpeningElement.HasFillings[0].RelatedBuildingElement.is_a('IfcDoor')
    settings = ifcopenshell.geom.settings()
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    shape = ifcopenshell.geom.create_shape(settings, wall)
    verts = np.array(shape.geometry.verts).reshape(-1, 3)
    assert np.ptp(verts, axis=0) == pytest.approx([5., .2, 3.], abs=1e-8)


@pytest.mark.parametrize('mutation,expected', [
    ('disjoint-cut', 'BASIC_FILLING_CONSTRAINT_CONFLICT'),
    ('outside-height', 'BASIC_FILLING_CONSTRAINT_CONFLICT'),
    ('outside-thickness', 'BASIC_FILLING_CONSTRAINT_CONFLICT'),
    ('wrong-layer', 'MATERIAL_LAYER_THICKNESS_MISMATCH'),
    ('variable-thickness', 'UNSUPPORTED_LAYER_GEOMETRY'),
    ('concave', 'UNSUPPORTED_LAYER_GEOMETRY'),
    ('tilted', 'UNSUPPORTED_LAYER_GEOMETRY'),
])
def test_invalid_polygon_hosts_are_rejected(mutation, expected):
    value = document()
    wall = record(value, 'wall-1')
    rep = wall['attributes']['Representation']
    opening = record(value, 'opening-1')['attributes']
    if mutation == 'disjoint-cut':
        opening['ObjectPlacement']['origin'][0] = 3500
    elif mutation == 'outside-height':
        opening['ObjectPlacement']['origin'][2] = 4000
    elif mutation == 'outside-thickness':
        opening['ObjectPlacement']['origin'][1] = 300
    elif mutation == 'wrong-layer':
        wall['materials'][0]['layers'][0]['thickness'] = 190
    elif mutation == 'variable-thickness':
        rep['profile']['points'] = [[-2500, -100], [2500, -50], [2500, 50], [-2500, 100], [-2500, -100]]
    elif mutation == 'concave':
        rep['profile']['points'] = [[-2500, -100], [2300, -100], [2300, 0], [1000, 0], [1000, 100], [-2500, 100], [-2500, -100]]
    elif mutation == 'tilted':
        rep['position'] = {'origin': [0, 0, 0], 'axis': [0, 1, 1], 'ref_direction': [1, 0, 0]}
    assert expected in {i.code for i in validate_v2_document(value)}


def test_source_style_end_crossing_is_valid_but_tangent_cut_is_not():
    value = document()
    opening = record(value, 'opening-1')['attributes']['ObjectPlacement']
    opening['origin'][0] = 1950  # opening overlaps a bevel, as in the source IFC
    assert validate_v2_document(value) == []
    opening['origin'][0] = 2950  # touches only the extreme vertex; no cut volume
    assert any(i.code == 'BASIC_FILLING_CONSTRAINT_CONFLICT' for i in validate_v2_document(value))


def test_old_contract_still_rejects_polygon_host():
    value = document()
    value['schema_version'] = 'bim-json/2.3'
    codes = {i.code for i in validate_v2_document(value)}
    assert 'BASIC_FILLING_CONSTRAINT_CONFLICT' in codes
    assert 'MATERIAL_LAYER_THICKNESS_MISMATCH' in codes


def test_opening_representation_position_is_used_for_fit():
    value = document()
    record(value, 'opening-1')['attributes']['Representation']['position'] = {
        'origin': [100, 0, 0], 'axis': [0, 0, 1], 'ref_direction': [1, 0, 0],
    }
    assert any(i.code == 'BASIC_FILLING_CONSTRAINT_CONFLICT' for i in validate_v2_document(value))
    record(value, 'door-1')['attributes']['ObjectPlacement']['origin'][0] = 100
    assert validate_v2_document(value) == []


def test_rounding_at_collinear_face_vertex_does_not_create_a_false_notch():
    value = document()
    rep = record(value, 'wall-1')['attributes']['Representation']
    rep['profile']['points'] = [[-2500, -100], [2300, -100], [2500, 100],
        [-2300, 100], [-2400, 99.97], [-2500, 100], [-2500, -100]]
    assert validate_v2_document(value) == []


def test_crossing_opening_produces_the_measured_boolean_cut(tmp_path):
    value = document()
    record(value, 'opening-1')['attributes']['ObjectPlacement']['origin'][0] = 1950
    result = compile_document(value, tmp_path / 'cross-end.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    wall = next(e for e in model.by_type('IfcWall') if util.get_psets(e).get('Pset_text2IFCIdentity', {}).get('BimJsonId') == 'wall-1')
    settings = ifcopenshell.geom.settings()
    cut_shape = ifcopenshell.geom.create_shape(settings, wall)
    cut_volume = ifcopenshell.util.shape.get_volume(cut_shape.geometry)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    uncut_shape = ifcopenshell.geom.create_shape(settings, wall)
    uncut_volume = ifcopenshell.util.shape.get_volume(uncut_shape.geometry)
    # Analytic polygon/opening intersection is (900*200 - 100*100/2) mm2.
    assert uncut_volume == pytest.approx(2.94, abs=1e-8)
    assert uncut_volume - cut_volume == pytest.approx(.3675, abs=1e-8)
