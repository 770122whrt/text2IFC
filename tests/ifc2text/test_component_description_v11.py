"""Failure family: storey names containing numbers are not elevation values."""
import copy
import json
import pytest

from tests.compiler.test_component_geometry_v26 import document
from text2ifc_compiler.compiler import compile_document
from text2ifc_ifc2text.compact_pipeline import prepare_compact,render_prepared_description


@pytest.fixture(scope='module')
def prepared(tmp_path_factory):
    root=tmp_path_factory.mktemp('floor-name-family');source=root/'source.ifc'
    assert compile_document(document(),source).success
    prepare_compact(source,root/'prepared',description_version='1.0',containment_policy='preserve_recorded')
    return json.loads((root/'prepared/source-facts.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('name,elevation',[('标高 3',40.),('Level 2',-1140.),('0.000',0.),('地板标高',None)])
def test_storey_name_is_quoted_and_never_substitutes_for_explicit_elevation(prepared,name,elevation):
    facts=copy.deepcopy(prepared);floor=facts['storeys'][0]
    floor.update(name=name,elevation_mm=elevation)
    previous=render_prepared_description(facts)
    facts['description_policy']['version']='1.1';before=copy.deepcopy(facts)
    current=render_prepared_description(facts)
    expected='未确认' if elevation is None else f'{elevation:.1f}'
    assert f'名称={json.dumps(name,ensure_ascii=False)}；楼层标高={expected} mm' in current
    assert '名称中的数字不作为标高' in current
    assert current.split('#### N001 部件几何')[1]==previous.split('#### N001 部件几何')[1]
    assert facts==before
    facts['description_policy']['version']='1.0'
    assert render_prepared_description(facts)==previous


def test_v11_preparation_retains_source_bytes_and_full_component_parameters(tmp_path):
    source=tmp_path/'source.ifc';assert compile_document(document('IfcDoor'),source).success
    before=source.read_bytes()
    report=prepare_compact(source,tmp_path/'prepared',description_version='1.1',containment_policy='preserve_recorded')
    facts=json.loads((tmp_path/'prepared/source-facts.json').read_text(encoding='utf-8'))
    text=(tmp_path/'prepared/design-description-deterministic.md').read_text(encoding='utf-8')
    assert report['component_supported_count']==1 and report['component_unsupported_count']==0
    assert '#### D001 部件几何' in text and 'blade-014' in text
    assert render_prepared_description(facts)==text
    assert source.read_bytes()==before
