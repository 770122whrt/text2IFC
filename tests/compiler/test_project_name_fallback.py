import copy
import ifcopenshell
import pytest
from text2ifc_compiler import compile_document
from tests.compiler.test_material_list_v25 import material_document, record

@pytest.mark.parametrize('project_id', ['project-1', 'project-other'])
def test_unnamed_project_uses_existing_technical_id_not_invented_building_name(tmp_path, project_id):
    document = material_document()
    project = record(document, 'project-1')
    project['attributes'].pop('Name', None)
    if project_id != 'project-1':
        # Replace references too; this is a different valid input, not an alias hint.
        import json
        document = json.loads(json.dumps(document).replace('project-1', project_id))
    before = copy.deepcopy(document)
    result = compile_document(document, tmp_path / 'unnamed.ifc')
    assert result.success, result
    assert document == before
    model = ifcopenshell.open(str(result.output_path))
    assert model.by_type('IfcProject')[0].Name == project_id

def test_explicit_project_name_is_preserved(tmp_path):
    document = material_document()
    record(document, 'project-1')['attributes']['Name'] = '既有项目名'
    result = compile_document(document, tmp_path / 'named.ifc')
    assert result.success, result
    assert ifcopenshell.open(str(result.output_path)).by_type('IfcProject')[0].Name == '既有项目名'
