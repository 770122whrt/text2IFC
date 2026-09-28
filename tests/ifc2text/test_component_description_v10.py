"""Public parametric description: source identities stay in extraction evidence."""
import copy
import json

import ifcopenshell
import pytest

from tests.compiler.test_component_geometry_v26 import document
from text2ifc_compiler.compiler import compile_document


@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
def test_prepared_description_contains_all_parts_and_explicit_frames(tmp_path,cls):
    from text2ifc_ifc2text.compact_pipeline import prepare_compact
    source=tmp_path/'private-source.ifc'
    assert compile_document(document(cls),source).success
    before=source.read_bytes()
    report=prepare_compact(source,tmp_path/'prepared',description_version='1.0',containment_policy='preserve_recorded')
    text=(tmp_path/'prepared/design-description-deterministic.md').read_text(encoding='utf-8')
    facts=json.loads((tmp_path/'prepared/source-facts.json').read_text(encoding='utf-8'))
    assert report['component_supported_count']==1 and report['component_unsupported_count']==0
    assert '部件几何' in text and '世界坐标' in text and '内环' in text
    assert all(f'blade-{i:03d}' in text for i in range(1,15))
    assert '0.2,0.3,0.4' in text and '透明度=0' in text
    assert '850' in text and '1100' in text and 'geometry-015' in text
    assert str(source) not in text
    assert ifcopenshell.open(str(source)).by_type(cls)[0].GlobalId not in text
    assert source.read_bytes()==before
    from text2ifc_ifc2text.compact_pipeline import render_prepared_description
    assert text==render_prepared_description(facts)


def test_one_unsupported_solid_refuses_whole_product_without_partial_geometry(tmp_path):
    from text2ifc_ifc2text.compact_pipeline import prepare_compact
    source=tmp_path/'private-source.ifc'
    assert compile_document(document(),source).success
    model=ifcopenshell.open(str(source)); window=model.by_type('IfcWindow')[0]
    body=window.Representation.Representations[0]
    body.Items=(*body.Items,model.createIfcBlock(model.createIfcAxis2Placement3D(
        model.createIfcCartesianPoint((0.,0.,0.)),None,None),10.,10.,10.))
    model.write(str(source))
    report=prepare_compact(source,tmp_path/'prepared',description_version='1.0',containment_policy='preserve_recorded')
    text=(tmp_path/'prepared/design-description-deterministic.md').read_text(encoding='utf-8')
    assert report['component_unsupported_count']==1
    assert 'IfcBlock' in text and '不支持' in text and '需要人工确认' in text
    assert 'geometry-001' not in text and 'blade-001' not in text
    assert report['status']=='prepared_requires_component_review'


def test_render_rejects_missing_component_details_instead_of_falling_back():
    from text2ifc_ifc2text.component_description_v10 import component_description
    from tests.ifc2text.test_offline_public_bridge import _room_facts
    facts=copy.deepcopy(_room_facts())
    with pytest.raises(ValueError,match='COMPONENT_DETAIL_REQUIRED'):
        component_description(facts)
