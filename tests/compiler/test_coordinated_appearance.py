import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as util
import pytest

from text2ifc_compiler import compile_document
from text2ifc_presentation import item_appearance_signatures


def document():
    value = json.loads((Path(__file__).parents[1] / 'contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    value['schema_version'] = 'bim-json/2.1'
    return value


def product(model, name='wall-1'):
    return next(e for e in model.by_type('IfcProduct') if util.get_psets(e, should_inherit=False).get('Pset_text2IFCIdentity', {}).get('BimJsonId') == name)


def signatures(entity):
    return [s for r in entity.Representation.Representations for i in r.Items for s in item_appearance_signatures(i)]


def mesh(entity):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    return tuple(ifcopenshell.geom.create_shape(settings, entity).geometry.verts)


def test_default_is_coordinated_without_new_material_or_properties(tmp_path):
    value = document()
    value['entities'][4]['property_sets'] = {}
    assert compile_document(value, tmp_path / 'out.ifc').success
    model = ifcopenshell.open(str(tmp_path / 'out.ifc'))
    wall = product(model)
    assert signatures(wall)
    assert not util.get_material(wall)
    assert set(util.get_psets(wall)) <= {'Pset_text2IFCIdentity', 'Pset_text2IFCAppearance'}


def test_theme_only_changes_styles_and_explicit_color_wins(tmp_path):
    value = document()
    wall = next(e for e in value['entities'] if e['id'] == 'wall-1')
    wall['appearance'] = {'color': [0.2, 0.4, 0.6], 'transparency': 0.0}
    models = []
    for theme in ['neutral-architectural', 'warm-residential']:
        value['appearance'] = {'profile': theme, 'seed': 'frozen'}
        out = tmp_path / (theme + '.ifc')
        result = compile_document(value, out)
        assert result.success, result
        models.append(ifcopenshell.open(str(out)))
    assert mesh(product(models[0])) == mesh(product(models[1]))
    for model in models:
        actual = signatures(product(model))
        assert actual and all((s['red'], s['green'], s['blue']) == (0.2, 0.4, 0.6) for s in actual)
    assert signatures(product(models[0], 'beam-1')) != signatures(product(models[1], 'beam-1'))


def test_same_role_is_not_randomized_by_instance_identity(tmp_path):
    value = document()
    other = copy.deepcopy(next(e for e in value['entities'] if e['id'] == 'beam-1'))
    other['id'] = 'beam-other'
    value['entities'].append(other)
    assert compile_document(value, tmp_path / 'out.ifc').success
    model = ifcopenshell.open(str(tmp_path / 'out.ifc'))
    assert signatures(product(model, 'beam-1')) == signatures(product(model, 'beam-other'))
    assert signatures(product(model, 'beam-1'))


@pytest.mark.parametrize('profile', ['unknown', ''])
def test_invalid_theme_never_publishes(tmp_path, profile):
    value = document()
    value['appearance'] = {'profile': profile}
    assert not compile_document(value, tmp_path / 'out.ifc').success
    assert not (tmp_path / 'out.ifc').exists()


def test_requested_color_is_verified_from_reopened_items(tmp_path):
    from text2ifc_compiler.semantic_verification import verify_semantic_expectations
    value = document()
    wall = next(e for e in value['entities'] if e['id'] == 'wall-1')
    wall['appearance'] = {'color': [0.1234567, 0.4, 0.6]}
    expected = [{'entity_id':'wall-1','kind':'appearance','value':wall['appearance']}]
    result = compile_document(value, tmp_path/'out.ifc', semantic_expectations=expected)
    assert result.success, result
    model = ifcopenshell.open(str(tmp_path/'out.ifc'))
    assert not verify_semantic_expectations(model, expected)
    for color in model.by_type('IfcColourRgb'):
        color.Red = .9
    assert verify_semantic_expectations(model, expected)


def test_default_palette_wrong_effective_value_is_rejected(tmp_path):
    from text2ifc_presentation.generation import verify_appearance
    value = document()
    assert compile_document(value,tmp_path/'out.ifc').success
    model = ifcopenshell.open(str(tmp_path/'out.ifc'))
    for color in model.by_type('IfcColourRgb'):
        color.Red = .99
    assert verify_appearance(model, value)
