"""Frozen S0 family: public contract/compile boundary, not an audit helper."""
import copy
import json
from pathlib import Path

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_compiler import compile_document


def document():
    return json.loads((Path(__file__).parent / 'fixtures/complete.json').read_text(encoding='utf-8'))


def typed_document(target='wall-1'):
    value = document()
    value['entities'].append(dict(id='type-a', ifc_class='IfcWallType',
        attributes={'Name': 'Common', 'PredefinedType': 'STANDARD'},
        property_sets={}, provenance={'source': 'user'}))
    value['relationships'].append(dict(id='type-rel-a', ifc_class='IfcRelDefinesByType',
        attributes={'RelatingType': 'type-a', 'RelatedObjects': [target]},
        provenance={'source': 'user'}))
    return value


@pytest.mark.parametrize('target', ['beam-1', 'column-1', 'door-1', 'window-1', 'space-1'])
def test_wrong_type_family_is_rejected_before_compile(target, tmp_path):
    value = typed_document(target)
    assert 'TYPE_FAMILY_MISMATCH' in {i.code for i in validate_v2_document(value)}
    result = compile_document(value, tmp_path / 'wrong.ifc')
    assert not result.success
    assert not (tmp_path / 'wrong.ifc').exists()


@pytest.mark.parametrize('same_type', [True, False])
def test_duplicate_type_relationship_cannot_be_silently_reassigned(same_type):
    value = typed_document()
    other = copy.deepcopy(value['relationships'][-1])
    other['id'] = 'type-rel-b'
    if not same_type:
        new_type = copy.deepcopy(value['entities'][-1])
        new_type['id'] = 'type-b'
        value['entities'].append(new_type)
        other['attributes']['RelatingType'] = 'type-b'
    value['relationships'].append(other)
    assert 'MULTIPLE_TYPE_ASSIGNMENTS' in {i.code for i in validate_v2_document(value)}


def test_wall_and_standard_case_can_share_one_wall_type():
    value = typed_document()
    second = copy.deepcopy(next(e for e in value['entities'] if e['id'] == 'wall-1'))
    second['id'] = 'wall-2'
    second['ifc_class'] = 'IfcWallStandardCase'
    value['entities'].append(second)
    value['relationships'][-1]['attributes']['RelatedObjects'].append('wall-2')
    assert validate_v2_document(value) == []


def test_malformed_type_endpoint_reports_shape_instead_of_crashing():
    value = typed_document()
    value['relationships'][-1]['attributes']['RelatingType'] = ['type-a']
    assert 'RELATIONSHIP_ENDPOINT_SHAPE' in {i.code for i in validate_v2_document(value)}
