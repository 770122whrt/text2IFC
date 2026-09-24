"""Source selection must retain native geometry and inverse semantic relations."""
import copy
import hashlib

import ifcopenshell
import pytest

from tests.compiler.test_component_geometry_v26 import document
from text2ifc_compiler.compiler import compile_document


@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
def test_native_source_isolation_preserves_geometry_style_type_material_and_bytes(tmp_path,cls):
    from scripts.ifc2text.isolated_source import isolate_filling
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    doc=document(cls)
    other=copy.deepcopy(doc['entities'][-1]);other['id']='other'
    other['attributes']['ObjectPlacement']['origin'][0]=2000
    doc['entities'].append(other)
    source=tmp_path/'source.ifc';assert compile_document(doc,source).success
    model=ifcopenshell.open(str(source));selected=model.by_type(cls)[0]
    material=model.createIfcMaterial('Steel')
    model.createIfcRelAssociatesMaterial(ifcopenshell.guid.new(),selected.OwnerHistory,None,None,[selected],material)
    style=model.create_entity('IfcDoorStyle' if cls=='IfcDoor' else 'IfcWindowStyle',
        GlobalId=ifcopenshell.guid.new(),OwnerHistory=selected.OwnerHistory,Name='Native style',
        OperationType='NOTDEFINED',ConstructionType='NOTDEFINED',ParameterTakesPrecedence=False,Sizeable=False)
    model.createIfcRelDefinesByType(ifcopenshell.guid.new(),selected.OwnerHistory,None,None,[selected],style)
    model.write(str(source));before=source.read_bytes()
    out=tmp_path/'selected.ifc'
    report=isolate_filling(source,out,selected.GlobalId)
    reopened=ifcopenshell.open(str(out));target=reopened.by_type(cls)[0]
    assert len(reopened.by_type('IfcElement'))==1
    assert target.GlobalId==selected.GlobalId
    assert read_component_geometry(target)['representation']==read_component_geometry(selected)['representation']
    assert target.HasAssociations[0].RelatingMaterial.Name=='Steel'
    assert next(r for r in target.IsDefinedBy if r.is_a('IfcRelDefinesByType')).RelatingType.GlobalId==style.GlobalId
    assert report['geometry_comparison']['pass'] and report['source_bytes_unchanged']
    assert source.read_bytes()==before
    assert report['source_sha256']==hashlib.sha256(before).hexdigest()
    with pytest.raises(ValueError,match='OUTPUT_EXISTS'):
        isolate_filling(source,out,selected.GlobalId)
    with pytest.raises(ValueError,match='SOURCE_OUTPUT_SAME'):
        isolate_filling(source,source,selected.GlobalId)
