"""Length facts are normalized in mm; IFC attributes use project units."""
import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.unit
import pytest

from text2ifc_ifc_repair.semantic_authoring import apply_semantic_assignments, SemanticManifestError


def fixture(ifc_class, prefix):
    model = ifcopenshell.file(schema='IFC2X3')
    unit = model.createIfcSIUnit(None, 'LENGTHUNIT', prefix, 'METRE')
    units = model.createIfcUnitAssignment([unit])
    model.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), UnitsInContext=units)
    target = model.create_entity(ifc_class, GlobalId=ifcopenshell.guid.new(), OverallWidth=12., OverallHeight=34.)
    return model, target


def assignment(attribute, value, unit=None):
    return {'fact_key': f'attribute:{attribute}', 'value': value, 'unit': unit,
            'ownership': 'occurrence_direct', 'authoring_action': 'set_attribute'}


def apply(model, target, assignments):
    return apply_semantic_assignments(model=model, operation={'semantic_assignments': assignments},
                                      application={'created': [{'role': 'target', 'global_id': target.GlobalId}]}, target_role='target')


@pytest.mark.parametrize('ifc_class', ['IfcDoor', 'IfcWindow'])
@pytest.mark.parametrize('prefix', [None, 'MILLI'])
@pytest.mark.parametrize('fact_unit', [None, 'mm'])
def test_normalized_dimension_roundtrip_in_both_project_units(tmp_path, ifc_class, prefix, fact_unit):
    model, target = fixture(ifc_class, prefix)
    apply(model, target, [assignment('OverallWidth', 864., fact_unit), assignment('OverallHeight', 2032., fact_unit)])
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    assert target.OverallWidth * scale == pytest.approx(.864)
    assert target.OverallHeight * scale == pytest.approx(2.032)
    path = tmp_path / 'units.ifc'
    model.write(str(path))
    reopened = ifcopenshell.open(str(path)).by_guid(target.GlobalId)
    assert reopened.OverallWidth * scale == pytest.approx(.864)
    assert reopened.OverallHeight * scale == pytest.approx(2.032)


@pytest.mark.parametrize('unit,value', [('m', .864), ('cm', 86.4)])
def test_explicit_supported_length_units(unit, value):
    model, target = fixture('IfcDoor', 'MILLI')
    apply(model, target, [assignment('OverallWidth', value, unit)])
    assert target.OverallWidth == pytest.approx(864.)


@pytest.mark.parametrize('unit', ['feet', '', 'm2'])
def test_unknown_or_non_length_unit_is_rejected_without_writing(unit):
    model, target = fixture('IfcDoor', None)
    with pytest.raises(SemanticManifestError, match='UNIT_UNSUPPORTED'):
        apply(model, target, [assignment('OverallWidth', 864., unit)])
    assert target.OverallWidth == 12.


def test_non_length_attribute_is_not_scaled():
    model, target = fixture('IfcWindow', None)
    apply(model, target, [assignment('Name', '窗864：保留原文')])
    assert target.Name == '窗864：保留原文'
    assert target.OverallWidth == 12.
