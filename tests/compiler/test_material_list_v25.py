"""Material-list names are an explicit sequence, never a layer or part map."""
import copy

import ifcopenshell
import ifcopenshell.util.element as util
import pytest

from text2ifc_compiler import compile_document
from text2ifc_compiler.semantic_verification import verify_document_semantics
from text2ifc_contract.validation_v2 import validate_v2_document
from tests.compiler.test_polygon_wall_hosts_v24 import document, record


def material_document(names=("Steel", "Wood")):
    value = document()
    value['schema_version'] = 'bim-json/2.5'
    record(value, 'door-1')['materials'] = [{'kind': 'material_list',
        'materials': [{'name': name} for name in names]}]
    return value


def door(model):
    return next(e for e in model.by_type('IfcDoor')
        if util.get_psets(e).get('Pset_text2IFCIdentity', {}).get('BimJsonId') == 'door-1')


@pytest.mark.parametrize('names', [('Steel', 'Wood'), ('Glass', 'Aluminium', 'Seal'), ('Steel', 'Wood', 'Steel'), ('Wood',)])
def test_list_roundtrip_preserves_names_order_multiplicity_without_layers(tmp_path, names):
    value = material_document(names)
    before = copy.deepcopy(value)
    result = compile_document(value, tmp_path / 'list.ifc')
    assert result.success, (result.input_issues, result.ifc_issues)
    assert value == before
    model = ifcopenshell.open(str(result.output_path))
    attached = [a for a in door(model).HasAssociations if a.is_a('IfcRelAssociatesMaterial')]
    assert len(attached) == 1
    material = attached[0].RelatingMaterial
    assert material.is_a() == 'IfcMaterialList'
    assert [m.Name for m in material.Materials] == list(names)
    assert len({m.id() for m in material.Materials}) == len(names)
    assert not verify_document_semantics(model, value)


@pytest.mark.parametrize('mutation', ['empty', 'unknown', 'thickness', 'blank', 'layers', 'duplicate-assignment', 'mixed-assignment'])
def test_invalid_list_is_rejected(mutation):
    value = material_document()
    assignments = record(value, 'door-1')['materials']
    item = assignments[0]
    if mutation == 'empty': item['materials'] = []
    elif mutation == 'unknown': item['unknown'] = True
    elif mutation == 'thickness': item['materials'][0]['thickness'] = 10
    elif mutation == 'blank': item['materials'][0]['name'] = ''
    elif mutation == 'layers': item['layers'] = [{'name': 'Wood', 'thickness': 10}]
    elif mutation == 'duplicate-assignment': assignments.append(copy.deepcopy(item))
    elif mutation == 'mixed-assignment': assignments.append({'kind': 'single_material', 'name': 'Wood'})
    assert validate_v2_document(value)


def test_old_24_still_rejects_list():
    value = material_document()
    value['schema_version'] = 'bim-json/2.4'
    assert validate_v2_document(value)


@pytest.mark.parametrize('mutation', ['rename', 'drop', 'reverse', 'duplicate-association'])
def test_reopen_verifier_detects_changed_material_content(tmp_path, mutation):
    value = material_document()
    result = compile_document(value, tmp_path / 'list.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    entity = door(model)
    material = util.get_material(entity)
    if mutation == 'rename': material.Materials[0].Name = 'Wrong'
    elif mutation == 'drop': material.Materials = material.Materials[:1]
    elif mutation == 'reverse': material.Materials = tuple(reversed(material.Materials))
    else:
        association = next(a for a in entity.HasAssociations if a.is_a('IfcRelAssociatesMaterial'))
        model.create_entity('IfcRelAssociatesMaterial', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=association.OwnerHistory, RelatedObjects=[entity], RelatingMaterial=material)
    assert verify_document_semantics(model, value)


def test_standard_case_cannot_silently_turn_list_into_layers():
    value = material_document()
    wall = record(value, 'wall-1')
    wall['ifc_class'] = 'IfcWallStandardCase'
    wall['attributes']['Representation']['profile'] = {'kind': 'rectangle', 'x': 5000, 'y': 200}
    wall['materials'] = copy.deepcopy(record(value, 'door-1')['materials'])
    assert any(i.code == 'UNSUPPORTED_MATERIAL_ASSIGNMENT' for i in validate_v2_document(value))


def test_list_inheritance_and_occurrence_override_stay_separate(tmp_path):
    from tests.compiler.test_v21_semantics import with_type, by_id
    value = with_type(material_document())
    record(value, 'beam-type')['materials'] = copy.deepcopy(record(value, 'door-1')['materials'])
    record(value, 'column-1')['materials'] = copy.deepcopy(record(value, 'door-1')['materials'])
    result = compile_document(value, tmp_path / 'inherited.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert util.get_material(by_id(model, 'beam-1')).is_a('IfcMaterialList')
    assert util.get_material(by_id(model, 'beam-1'), should_inherit=False) is None
    assert util.get_material(door(model)).id() != util.get_material(by_id(model, 'column-1')).id()
    record(value, 'beam-1')['materials'] = [{'kind': 'single_material', 'name': 'Override'}]
    result = compile_document(value, tmp_path / 'override.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert util.get_material(by_id(model, 'beam-1')).Name == 'Override'
    assert [m.Name for m in util.get_material(by_id(model, 'beam-type')).Materials] == ['Steel', 'Wood']


def test_25_preserves_railing_geometry_and_semantic_validation(tmp_path):
    from tests.compiler.test_basic_railing import document as railing_document
    value = railing_document(rise=1800, yaw=90, elevation=4200)
    value['schema_version'] = 'bim-json/2.5'
    result = compile_document(value, tmp_path / 'railing.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert len(model.by_type('IfcRailing')[0].Representation.Representations[0].Items) == 42


def test_draft_15_validates_but_cannot_compile(tmp_path):
    from text2ifc_contract.draft import validate_draft
    draft = {'draft_version': 'bim-json-draft/1.5', 'target_schema_version': 'bim-json/2.5',
        'partial_document': {}, 'missing_facts': [{'entity_id': 'door-1', 'path': '/materials',
        'code': 'MISSING', 'message': 'Material names are missing.'}], 'losses': [],
        'clarification_targets': [], 'provenance': {'source': 'test'}}
    assert validate_draft(draft) == []
    result = compile_document(draft, tmp_path / 'draft.ifc')
    assert [i.code for i in result.input_issues] == ['DRAFT_NOT_COMPILABLE']
    assert not (tmp_path / 'draft.ifc').exists()
