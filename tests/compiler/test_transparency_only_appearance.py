"""A requested alpha channel must retain the unrequested palette colour."""
import copy
import ifcopenshell
import pytest
from text2ifc_compiler import compile_document
from text2ifc_presentation.generation import verify_appearance
from tests.compiler.test_part_appearance import document
from tests.compiler.test_basic_filling import TEMPLATES
from tests.compiler.test_coordinated_appearance import product, mesh, signatures


@pytest.mark.parametrize('template', TEMPLATES)
@pytest.mark.parametrize('version', ['2.1','2.2'])
def test_only_transparency_preserves_default_part_colours_and_mesh(tmp_path, template, version):
    value, record = document(template); value['schema_version'] = 'bim-json/'+version
    plain = compile_document(value, tmp_path/'plain.ifc'); assert plain.success
    model = ifcopenshell.open(str(plain.output_path))
    original = product(model, record['id']); baseline = signatures(original)
    record['appearance'] = {'transparency': .75}
    before = copy.deepcopy(value)
    expected = [{'entity_id':record['id'], 'kind':'appearance', 'value':record['appearance']}]
    result = compile_document(value, tmp_path/'alpha.ifc', semantic_expectations=expected)
    assert result.success, result
    changed_model = ifcopenshell.open(str(result.output_path)); changed = product(changed_model, record['id'])
    assert mesh(original) == mesh(changed)
    assert [(s['red'],s['green'],s['blue']) for s in signatures(changed)] == [(s['red'],s['green'],s['blue']) for s in baseline]
    assert all(s['transparency'] == .75 for s in signatures(changed))
    assert value == before
    assert not verify_appearance(changed_model, value)
    for rendering in changed_model.by_type('IfcSurfaceStyleRendering'): rendering.Transparency = .1
    assert verify_appearance(changed_model, value)
