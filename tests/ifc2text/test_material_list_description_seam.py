"""Source material names survive IFC2Text; Compare detects a missing name."""
import copy
import json

from text2ifc_compiler import compile_document
from text2ifc_ifc2text.compact_pipeline import prepare_compact
from text2ifc_ifc2text.observation import all_items
from text2ifc_ifc2text.precision_compare_v11 import compare_roundtrip
from tests.compiler.test_material_list_v25 import material_document, record


def test_material_list_survives_description_and_compare_detects_one_missing_name(tmp_path):
    names = ['抛光不锈钢', '玻璃', '白油漆']
    document = material_document(names)
    source = tmp_path / 'source.ifc'
    assert compile_document(document, source).success
    original = source.read_bytes()
    out = tmp_path / 'description'
    prepare_compact(source, out)
    facts = json.loads((out / 'source-facts.json').read_text(encoding='utf-8'))
    door = next(item for category, item in all_items(facts) if category == 'doors')
    material = next(m for m in door['materials'] if m['kind'] == 'material_list')
    assert material['names'] == names
    text = (out / 'design-description-deterministic.md').read_text(encoding='utf-8')
    assert all(name in text for name in names)
    same = tmp_path / 'same.ifc'
    assert compile_document(document, same).success
    assert compare_roundtrip(source, same)['summary']['material_content_differences'] == 0
    changed = copy.deepcopy(document)
    record(changed, 'door-1')['materials'][0]['materials'].pop()
    incomplete = tmp_path / 'missing-name.ifc'
    assert compile_document(changed, incomplete).success
    assert compare_roundtrip(source, incomplete)['summary']['material_content_differences'] == 1
    assert source.read_bytes() == original
