"""Native hosted selection preserves the entire host and every existing cut."""
import copy
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_compiler.compiler import compile_document


def source_document(cls):
    doc=json.loads((Path(__file__).parents[1]/'contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    doc['entities']=[e for e in doc['entities'] if e['id']!='window-1']
    door=next(e for e in doc['entities'] if e['id']=='door-1')
    door['ifc_class']=cls
    opening=copy.deepcopy(next(e for e in doc['entities'] if e['id']=='opening-1'))
    opening['id']='opening-other'
    opening['attributes']['ObjectPlacement']['origin']=[-1000,0,500]
    opening['attributes']['Representation']['profile']['x']=300
    opening['attributes']['Representation']['depth']=500
    doc['entities'].append(opening)
    relation=copy.deepcopy(doc['relationships'][0]);relation['id']='void-other'
    relation['attributes']['RelatedOpeningElement']='opening-other'
    doc['relationships'].append(relation)
    return doc


@pytest.mark.parametrize('cls',['IfcDoor','IfcWindow'])
def test_selection_keeps_filling_host_all_openings_and_native_geometry(tmp_path,cls):
    from scripts.ifc2text.hosted_source import isolate_hosted_filling
    source=tmp_path/'source.ifc';assert compile_document(source_document(cls),source).success
    model=ifcopenshell.open(str(source));target=model.by_type(cls)[0]
    wall=target.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
    before=source.read_bytes();output=tmp_path/'selected.ifc'
    report=isolate_hosted_filling(source,output,target.GlobalId)
    selected=ifcopenshell.open(str(output))
    assert source.read_bytes()==before
    assert len(selected.by_type('IfcElement'))==4  # filling + wall + two existing cuts
    assert len(selected.by_guid(wall.GlobalId).HasOpenings)==2
    assert selected.by_guid(target.GlobalId).FillsVoids[0].RelatingOpeningElement.GlobalId == target.FillsVoids[0].RelatingOpeningElement.GlobalId
    assert report['filling_comparison']['pass']
    assert report['host_mesh_unchanged'] and report['opening_meshes_unchanged']
    assert report['source_bytes_unchanged']
    with pytest.raises(ValueError,match='OUTPUT_EXISTS'):
        isolate_hosted_filling(source,output,target.GlobalId)
    with pytest.raises(ValueError,match='SOURCE_OUTPUT_SAME'):
        isolate_hosted_filling(source,source,target.GlobalId)


def test_standalone_cannot_be_passed_off_as_hosted(tmp_path):
    from scripts.ifc2text.hosted_source import isolate_hosted_filling
    from tests.compiler.test_component_geometry_v26 import document
    source=tmp_path/'source.ifc';assert compile_document(document(),source).success
    target=ifcopenshell.open(str(source)).by_type('IfcWindow')[0]
    with pytest.raises(ValueError,match='EXACTLY_ONE_OPENING_REQUIRED'):
        isolate_hosted_filling(source,tmp_path/'absent.ifc',target.GlobalId)
    assert not (tmp_path/'absent.ifc').exists()
