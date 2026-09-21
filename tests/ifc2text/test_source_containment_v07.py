"""Containment normalization is an explicit derived-copy policy, never silent repair."""
import json
from pathlib import Path
import ifcopenshell
import pytest
from text2ifc_compiler import compile_document
from text2ifc_ifc2text.source_containment_v07 import inspect_containment, normalize_copy


def source_file(tmp_path):
    doc=json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    path=tmp_path/'source.ifc'
    assert compile_document(doc,path).success
    model=ifcopenshell.open(str(path)); door=model.by_type('IfcDoor')[0]
    host=model.by_type('IfcWall')[0]; old=door.ContainedInStructure[0]
    old.RelatedElements=tuple(x for x in old.RelatedElements if x!=door)
    base=host.ContainedInStructure[0].RelatingStructure
    datum=model.create_entity('IfcBuildingStorey',GlobalId=ifcopenshell.guid.new(),OwnerHistory=base.OwnerHistory,
        Name='reference record',ObjectPlacement=base.ObjectPlacement,CompositionType='ELEMENT',Elevation=3500.)
    model.create_entity('IfcRelContainedInSpatialStructure',GlobalId=ifcopenshell.guid.new(),OwnerHistory=base.OwnerHistory,
        RelatedElements=[door],RelatingStructure=datum)
    model.write(str(path))
    return path,door.GlobalId


def test_audit_does_not_claim_different_storeys_are_schema_errors(tmp_path):
    path,gid=source_file(tmp_path); before=path.read_bytes()
    report=inspect_containment(path)
    row=next(x for x in report['fillings'] if x['global_id']==gid)
    assert row['recorded_vs_host_different']
    assert row['difference_alone_proves_source_error'] is False
    assert report['normalization_applied'] is False
    assert path.read_bytes()==before


def test_policy_copy_changes_only_selected_containment(tmp_path):
    path,gid=source_file(tmp_path); before=path.read_bytes()
    out=tmp_path/'normalized.ifc'
    report=normalize_copy(path,out,selected_global_ids=[gid],policy='host_storey_for_selected_fillings')
    assert path.read_bytes()==before
    assert report['geometry_and_noncontainment_entities_unchanged']
    assert report['moved_count']==1
    model=ifcopenshell.open(str(out)); door=model.by_guid(gid)
    host=door.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
    assert door.ContainedInStructure[0].RelatingStructure==host.ContainedInStructure[0].RelatingStructure
    assert all(len(r.RelatedElements)>0 for r in model.by_type('IfcRelContainedInSpatialStructure'))


def test_no_implicit_policy_or_source_overwrite(tmp_path):
    path,gid=source_file(tmp_path)
    with pytest.raises(ValueError):normalize_copy(path,path,selected_global_ids=[gid],policy='host_storey_for_selected_fillings')
    with pytest.raises(ValueError):normalize_copy(path,tmp_path/'out.ifc',selected_global_ids=[gid],policy='automatic')
    with pytest.raises(ValueError):normalize_copy(path,tmp_path/'out.ifc',selected_global_ids=['not-an-entity'],policy='host_storey_for_selected_fillings')
    assert not (tmp_path/'out.ifc').exists()
