"""Versioned part colour requests must survive reopening without geometry changes."""
import copy

import ifcopenshell
import ifcopenshell.util.element as util
import pytest

from text2ifc_compiler import compile_document
from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_presentation import item_appearance_signatures
from text2ifc_presentation.generation import THEMES, verify_appearance
from tests.compiler.test_basic_filling import public_document, representation, roles, TEMPLATES
from tests.compiler.test_coordinated_appearance import product, mesh


def document(template):
    value = public_document('door-left')
    target = 'door-1'
    record = next(e for e in value['entities'] if e['id'] == target)
    record['ifc_class'] = 'IfcWindow' if template.startswith('window') else 'IfcDoor'
    record['attributes']['Representation'] = representation(template, width=900., height=2100.)
    value['schema_version'] = 'bim-json/2.2'
    value['appearance'] = {'profile': 'warm-residential'}
    return value, record


@pytest.mark.parametrize('template', TEMPLATES)
def test_part_override_reopens_with_identical_mesh_and_materials(tmp_path, template):
    value, record = document(template)
    baseline = copy.deepcopy(value); baseline['schema_version'] = 'bim-json/2.1'
    record['part_appearance'] = {'frame': {'color': [.13, .24, .35]}}
    panel = 'panel' if template.startswith('door') else 'glazing'
    record['part_appearance'][panel] = {'color': [.61, .42, .23]} if panel == 'panel' else {'transparency': .7}
    before = copy.deepcopy(value)
    results = []
    for label, source in [('old', baseline), ('new', value)]:
        result = compile_document(source, tmp_path / (label + '.ifc'))
        assert result.success, result
        results.append(ifcopenshell.open(str(result.output_path)))
    old, new = results
    for original in value['entities']:
        matches = [e for e in old.by_type('IfcProduct') if util.get_psets(e).get('Pset_text2IFCIdentity', {}).get('BimJsonId') == original['id'] and e.Representation]
        if matches:
            assert mesh(matches[0]) == mesh(product(new, original['id']))
    a, b = product(old, record['id']), product(new, record['id'])
    assert util.get_material(a) is None and util.get_material(b) is None
    for role, items in roles(b).items():
        signature = 'frame' if role in {'Framing', 'Lining'} else 'panel' if role == 'Panel' else 'glazing'
        requested = record['part_appearance'][signature]
        color = requested.get('color', THEMES['warm-residential'][signature])
        transparency = requested.get('transparency', .45 if signature == 'glazing' else 0)
        for item in items:
            values = item_appearance_signatures(item)
            assert len(values) == 1
            assert [values[0][k] for k in ('red', 'green', 'blue', 'transparency')] == pytest.approx([*color, transparency])
    assert value == before
    assert not verify_appearance(new, value)


@pytest.mark.parametrize('part', [None, {}, {'frame': {}}, {'hinge': {'color': [0, 0, 0]}},
    {'glazing': {'color': [0, 0, 0]}}, {'frame': {'color': [True, 0, 0]}},
    {'frame': {'color': [-.1, 0, 0]}}, {'frame': {'color': [0, 0, 1.1]}},
    {'frame': {'transparency': None}}, {'frame': {'transparency': float('nan')}},
    {'frame': {'material': 'aluminium'}}])
def test_invalid_part_requests_fail_closed(part):
    value, record = document('door-left'); record['part_appearance'] = part
    issues = validate_v2_document(value)
    assert any(i.code == 'INVALID_PART_APPEARANCE' for i in issues), issues


@pytest.mark.parametrize('attack', ['whole', 'type', 'legacy_geometry'])
def test_incompatible_targets_or_whole_colour_cannot_silently_override_parts(attack):
    value, record = document('door-right'); record['part_appearance'] = {'frame': {'color': [0, 0, 0]}}
    if attack == 'whole': record['appearance'] = {'color': [1, 1, 1]}
    if attack == 'type': record['ifc_class'] = 'IfcDoorStyle'
    if attack == 'legacy_geometry': record['attributes'].pop('Representation')
    assert any(i.code == 'INVALID_PART_APPEARANCE' for i in validate_v2_document(value))


def test_old_registered_contract_still_rejects_part_field():
    value, record = document('door-left'); value['schema_version'] = 'bim-json/2.1'
    record['part_appearance'] = {'frame': {'color': [0, 0, 0]}}
    assert validate_v2_document(value)


def test_verifier_reads_real_parts_instead_of_provenance(tmp_path):
    value, record = document('window-double-vertical')
    record['part_appearance'] = {'frame': {'color': [.1, .2, .3]}, 'glazing': {'transparency': .7}}
    result = compile_document(value, tmp_path / 'parts.ifc'); assert result.success, result
    model = ifcopenshell.open(str(result.output_path)); filling = product(model, record['id'])
    glazing = roles(filling)['Glazing'][0]
    for binding in glazing.StyledByItem:
        for assignment in binding.Styles:
            for style in assignment.Styles:
                for surface in style.Styles:
                    if surface.is_a('IfcSurfaceStyleRendering'): surface.Transparency = .1
    assert verify_appearance(model, value)


@pytest.mark.parametrize('attack', ['wrong_request', 'inherited_whole', 'none'])
def test_independent_request_verification_and_atomic_publication(tmp_path, attack):
    from text2ifc_compiler.semantic_verification import verify_semantic_expectations
    value, record = document('door-left')
    record['materials'] = [{'kind': 'single_material', 'name': 'Requested timber'}]
    record['part_appearance'] = {'frame': {'color': [0, 1, 0]}, 'panel': {'transparency': 0}}
    value['entities'].append({'id': 'requested-style', 'ifc_class': 'IfcDoorStyle',
        'attributes': {'Name': 'Requested door style', 'OperationType': 'SINGLE_SWING_LEFT'}, 'property_sets': {},
        'provenance': copy.deepcopy(record['provenance'])})
    value['relationships'].append({'id': 'requested-type-link', 'ifc_class': 'IfcRelDefinesByType',
        'attributes': {'RelatingType': 'requested-style', 'RelatedObjects': [record['id']]},
        'provenance': copy.deepcopy(value['relationships'][0]['provenance'])})
    request = [{'entity_id': record['id'], 'kind': 'part_appearance', 'value': copy.deepcopy(record['part_appearance'])}]
    path = tmp_path/'atomic.ifc'; path.write_bytes(b'existing output remains intact')
    if attack == 'wrong_request': request[0]['value']['frame']['color'] = [1, 0, 0]
    if attack == 'inherited_whole': value['entities'][-1]['appearance'] = {'color': [.5, .5, .5]}
    result = compile_document(value, path, semantic_expectations=request)
    if attack != 'none':
        assert not result.success
        assert path.read_bytes() == b'existing output remains intact'
    else:
        assert result.success, result
        model = ifcopenshell.open(str(path)); filling = product(model, record['id'])
        assert util.get_material(filling).Name == 'Requested timber'
        assert util.get_type(filling).OperationType == 'SINGLE_SWING_LEFT'
        assert not verify_semantic_expectations(model, request)
        request[0]['value']['frame']['color'] = [1, 0, 0]
        assert verify_semantic_expectations(model, request)
