"""Version and assignment boundaries for non-layered lists."""
import copy

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document
from tests.compiler.test_material_list_v25 import material_document, record


@pytest.mark.parametrize('version', ['2.0', '2.1', '2.2', '2.3', '2.4'])
def test_list_is_not_backported_into_frozen_contracts(version):
    value = material_document()
    value['schema_version'] = f'bim-json/{version}'
    assert validate_v2_document(value)


@pytest.mark.parametrize('invalid', [None, 3, True, {}, [], {'name': None}, {'name': 'Steel', 'part': 'frame'}])
def test_material_members_are_only_named_materials(invalid):
    value = material_document()
    record(value, 'door-1')['materials'][0]['materials'] = [invalid]
    assert validate_v2_document(value)


def test_standardcase_cannot_inherit_material_list():
    value = material_document()
    wall = record(value, 'wall-1')
    wall['ifc_class'] = 'IfcWallStandardCase'
    wall['attributes']['Representation']['profile'] = {'kind': 'rectangle', 'x': 5000, 'y': 200}
    wall.pop('materials')
    value['entities'].append({'id': 'wall-type', 'ifc_class': 'IfcWallType',
        'attributes': {'Name': 'Type', 'PredefinedType': 'STANDARD'}, 'property_sets': {},
        'materials': copy.deepcopy(record(value, 'door-1')['materials']), 'provenance': {'source': 'test'}})
    value['relationships'].append({'id': 'typing', 'ifc_class': 'IfcRelDefinesByType',
        'attributes': {'RelatingType': 'wall-type', 'RelatedObjects': ['wall-1']}, 'provenance': {'source': 'test'}})
    assert any(i.code == 'UNSUPPORTED_MATERIAL_ASSIGNMENT' for i in validate_v2_document(value))
