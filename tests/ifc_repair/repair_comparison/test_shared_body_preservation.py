"""Shared geometry must survive evaluator subtraction, and real drift must fail."""
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

from scripts.ifc_repair.repair_comparison.preservation_v2 import preservation
from tests.ifc_repair.repair_comparison.test_preparation import sample

PUBLIC = Path(__file__).resolve().parents[3] / (
    'dataset/processed/ifc-repair/repair-comparison/formal/formal-005/public/model.ifc')


def add_shared(model, template, count=1):
    source = next(rep for rep in template.Representation.Representations
                  if rep.RepresentationIdentifier == 'Body')
    made = []
    for index in range(count):
        shape = model.create_entity('IfcShapeRepresentation',
            ContextOfItems=source.ContextOfItems, RepresentationIdentifier='Body',
            RepresentationType=source.RepresentationType, Items=source.Items)
        origin = model.create_entity('IfcAxis2Placement3D',
            Location=model.create_entity('IfcCartesianPoint', Coordinates=(0., 0., 0.)))
        mapping = model.create_entity('IfcRepresentationMap', MappingOrigin=origin,
                                      MappedRepresentation=shape)
        target = model.create_entity('IfcCartesianTransformationOperator3D',
            LocalOrigin=model.create_entity('IfcCartesianPoint', Coordinates=(0., 0., 0.)), Scale=1.)
        mapped = model.create_entity('IfcMappedItem', MappingSource=mapping, MappingTarget=target)
        body = model.create_entity('IfcShapeRepresentation', ContextOfItems=source.ContextOfItems,
            RepresentationIdentifier='Body', RepresentationType='MappedRepresentation', Items=[mapped])
        product = model.create_entity(template.is_a(), GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=template.OwnerHistory, Name='synthetic-new',
            Representation=model.create_entity('IfcProductDefinitionShape', Representations=[body]),
            ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=origin))
        if template.is_a('IfcDoor') or template.is_a('IfcWindow'):
            product.OverallWidth, product.OverallHeight = template.OverallWidth, template.OverallHeight
        made.append(product.GlobalId)
    return made


@pytest.fixture
def graph(request, sample):
    if request.param == 'public_brep':
        damaged = ifcopenshell.open(str(PUBLIC))
        template = next(p for p in damaged.by_type('IfcDoor') if p.Name == 'Door-035')
    else:
        damaged = ifcopenshell.open(str(sample[1]))
        template = damaged.by_type('IfcDoor')[0]
    result = ifcopenshell.file.from_string(damaged.to_string())
    return damaged, result, result.by_guid(template.GlobalId)


@pytest.mark.parametrize('graph', ['public_brep', 'synthetic_swept'], indirect=True)
@pytest.mark.parametrize('count', [1, 2])
@pytest.mark.parametrize('order', ['forward', 'reverse'])
def test_shared_items_single_batch_and_order_preserve_source(graph, count, order):
    damaged, result, template = graph
    new = add_shared(result, template, count)
    if order == 'reverse':
        new.reverse()
    before = (damaged.to_string(), result.to_string())
    report = preservation(damaged, result, new)
    assert report['passed'], report
    assert before == (damaged.to_string(), result.to_string())


@pytest.mark.parametrize('graph', ['public_brep', 'synthetic_swept'], indirect=True)
@pytest.mark.parametrize('fault', ['name', 'placement', 'deleted', 'geometry', 'extra_relation', 'extra_property'])
def test_real_source_damage_still_fails(graph, fault):
    damaged, result, template = graph
    new = add_shared(result, template, 2)
    if fault == 'name':
        template.Name = 'unexpected'
    elif fault == 'placement':
        template.ObjectPlacement = result.create_entity('IfcLocalPlacement', RelativePlacement=
            result.create_entity('IfcAxis2Placement3D', Location=
                result.create_entity('IfcCartesianPoint', Coordinates=(20., 0., 0.))))
    elif fault == 'deleted':
        result.remove(template)
    elif fault == 'geometry':
        template.Representation = None
    elif fault == 'extra_relation':
        result.create_entity('IfcRelAssignsToGroup', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=template.OwnerHistory, RelatedObjects=[template],
            RelatingGroup=result.by_type('IfcBuilding')[0] if result.by_type('IfcBuilding') else result.by_type('IfcProject')[0])
    else:
        result.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=template.OwnerHistory, Name='unrelated', HasProperties=[
                result.create_entity('IfcPropertySingleValue', Name='test', NominalValue=result.create_entity('IfcBoolean', True))])
    assert not preservation(damaged, result, new)['passed']
