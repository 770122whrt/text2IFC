"""Public synthetic regression family for effective units on existing properties.

Frozen before the fix: implicit mm/m, explicit override, absent/conflicting units,
new properties, mixed evidence, shared Psets, and an independent Beam sibling.
The real task and its failed output are not inputs to these offline tests.
"""

from dataclasses import replace
from types import SimpleNamespace

import ifcopenshell
import ifcopenshell.util.unit
import pytest

from tests.ifc_repair.test_existing_property_type_preservation import (
    SIBLING_ID,
    TARGET_ID,
    _api,
    _DraftProvider,
    _source,
)
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.index_models import IndexMetadata
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.property_intent import (
    ExactPropertyIntent,
    PropertyResolutionStatus,
    resolve_exact_property_intent,
)
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
from text2ifc_ifc_repair.semantic_authoring import SemanticManifestError, apply_semantic_assignments
from text2ifc_ifc_repair.semantic_facts import extract_property_facts
from text2ifc_knowledge.registry import load_ifc2x3_registry


SET_NAME = "Fabrication"
PROPERTY_NAME = "Edge Width"


def _property(model, target_id=TARGET_ID):
    target = model.by_guid(target_id)
    pset = next(
        rel.RelatingPropertyDefinition for rel in target.IsDefinedBy
        if rel.is_a("IfcRelDefinesByProperties")
        and rel.RelatingPropertyDefinition.Name == SET_NAME
    )
    return next(prop for prop in pset.HasProperties if prop.Name == PROPERTY_NAME)


def _unit(model, token, unit_type="LENGTHUNIT", name="METRE"):
    if token == "FOOT":
        return model.create_entity(
            "IfcConversionBasedUnit", UnitType="LENGTHUNIT", Name="FOOT",
            Dimensions=model.create_entity("IfcDimensionalExponents", 1, 0, 0, 0, 0, 0, 0),
            ConversionFactor=model.create_entity(
                "IfcMeasureWithUnit", ValueComponent=model.create_entity("IfcRatioMeasure", 0.3048),
                UnitComponent=_unit(model, "m"),
            ),
        )
    return model.create_entity(
        "IfcSIUnit", UnitType=unit_type, Prefix="MILLI" if token == "mm" else None,
        Name=name,
    )


def _model(path, *, project_units=("mm",), explicit=None, ifc_class="IfcDoor", value_type="IfcLengthMeasure", shared=False):
    _source(path, ifc_class, SET_NAME, PROPERTY_NAME, value_type, shared, value=25.0)
    model = ifcopenshell.open(str(path))
    if project_units is not None:
        model.create_entity(
            "IfcProject", GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=model.by_type("IfcOwnerHistory")[0], Name="Public unit fixture",
            UnitsInContext=model.create_entity(
                "IfcUnitAssignment", Units=[_unit(model, token) for token in project_units],
            ),
        )
    if explicit is not None:
        _property(model).Unit = _unit(model, explicit)
    return model


def _intent(*, unit=None, value_type=None, property_name=PROPERTY_NAME):
    return ExactPropertyIntent(
        set_name=SET_NAME, property_name=property_name, value=75,
        requested_value_type=value_type, requested_unit=unit, scope="occurrence_direct",
        source=PublicProvenance("user_request", "request:/text", "Change to 75; preserve the original type."),
        intent_kind="exact_property",
    )


def _resolve(facts, **kwargs):
    return resolve_exact_property_intent(
        _intent(**kwargs), target_ifc_class="IfcDoor", existing_facts=facts,
        registry=load_ifc2x3_registry(),
    )


@pytest.mark.parametrize("project_units,explicit,expected", [
    (("mm",), None, "mm"), (("m",), None, "m"),
    (("m",), "mm", "mm"), (("mm",), "m", "m"),
    (None, "mm", "mm"), (("mm", "m"), "mm", "mm"),
    (("FOOT",), None, "FOOT"), (("m",), "FOOT", "FOOT"),
])
def test_existing_measure_effective_unit_is_public_index_fact(tmp_path, project_units, explicit, expected):
    path = tmp_path / "source.ifc"
    model = _model(path, project_units=project_units, explicit=explicit)
    model.write(str(path))
    before = path.read_bytes()
    build_ifc_index(path, tmp_path / "index.sqlite")
    with SQLiteIndexRepository.open(tmp_path / "index.sqlite") as index:
        facts = index.get_by_global_id(TARGET_ID).properties
    fact = next(fact for fact in facts if fact.property_name == PROPERTY_NAME)
    assert fact.unit == expected
    assert fact.value_type == "IfcLengthMeasure"
    result = _resolve(facts)
    assert result.status is PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
    assert (result.value, result.value_type, result.unit) == (75, "IfcLengthMeasure", expected)
    assert path.read_bytes() == before


@pytest.mark.parametrize("project_units", [None, (), ("mm", "m")])
def test_missing_or_conflicting_project_units_cannot_be_inferred(tmp_path, project_units):
    model = _model(tmp_path / "source.ifc", project_units=project_units)
    facts = extract_property_facts(model.by_guid(TARGET_ID))
    assert facts[0].unit is None
    result = _resolve(facts)
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "CUSTOM_UNIT_REQUIRED"


def test_multiple_projects_do_not_supply_an_arbitrary_first_unit(tmp_path):
    model = _model(tmp_path / "source.ifc")
    model.create_entity(
        "IfcProject", GlobalId=ifcopenshell.guid.new(),
        UnitsInContext=model.create_entity("IfcUnitAssignment", Units=[_unit(model, "m")]),
    )
    assert extract_property_facts(model.by_guid(TARGET_ID))[0].unit is None


@pytest.mark.parametrize("value_type,unit_type,name,expected", [
    ("IfcPositiveLengthMeasure", "LENGTHUNIT", "METRE", "mm"),
    ("IfcAreaMeasure", "AREAUNIT", "SQUARE_METRE", "mm2"),
    ("IfcVolumeMeasure", "VOLUMEUNIT", "CUBIC_METRE", "mm3"),
])
def test_measure_type_selects_its_own_project_unit(tmp_path, value_type, unit_type, name, expected):
    model = _model(tmp_path / "source.ifc", project_units=("m",), value_type=value_type)
    model.by_type("IfcProject")[0].UnitsInContext.Units = [_unit(model, "mm", unit_type, name)]
    assert extract_property_facts(model.by_guid(TARGET_ID))[0].unit == expected


def test_absent_area_unit_cannot_be_guessed_from_project_length(tmp_path):
    model = _model(tmp_path / "source.ifc", value_type="IfcAreaMeasure")
    assert extract_property_facts(model.by_guid(TARGET_ID))[0].unit is None


def test_incompatible_explicit_unit_cannot_fall_back_to_project_default(tmp_path):
    model = _model(tmp_path / "source.ifc")
    _property(model).Unit = _unit(model, "mm", "AREAUNIT", "SQUARE_METRE")
    facts = extract_property_facts(model.by_guid(TARGET_ID))
    assert facts[0].unit is None
    result = _resolve(facts)
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "CUSTOM_UNIT_REQUIRED"


def test_non_measure_property_does_not_acquire_project_length_unit(tmp_path):
    model = _model(tmp_path / "source.ifc", value_type="IfcReal")
    assert extract_property_facts(model.by_guid(TARGET_ID))[0].unit is None


def _thermal_unit(model):
    units = [
        (model.create_entity("IfcSIUnit", UnitType="MASSUNIT", Prefix="KILO", Name="GRAM"), 1),
        (model.create_entity("IfcSIUnit", UnitType="TIMEUNIT", Name="SECOND"), -3),
        (model.create_entity("IfcSIUnit", UnitType="THERMODYNAMICTEMPERATUREUNIT", Name="KELVIN"), -1),
    ]
    return model.create_entity(
        "IfcDerivedUnit", UnitType="THERMALTRANSMITTANCEUNIT",
        Elements=[model.create_entity("IfcDerivedUnitElement", Unit=unit, Exponent=exponent) for unit, exponent in units],
    )


def test_implicit_thermal_unit_does_not_expand_source_property_copy_contract(tmp_path):
    model = _model(tmp_path / "source.ifc", value_type="IfcThermalTransmittanceMeasure")
    source_property = _property(model)
    source_property.Name = "ThermalTransmittance"
    project = model.by_type("IfcProject")[0]
    project.UnitsInContext.Units = [*project.UnitsInContext.Units, _thermal_unit(model)]
    fact = extract_property_facts(model.by_guid(TARGET_ID))[0]
    assert fact.unit is None
    assert fact.value_type == "IfcThermalTransmittanceMeasure"
    copied_window = model.create_entity(
        "IfcWindow", GlobalId=SIBLING_ID, OwnerHistory=model.by_type("IfcOwnerHistory")[0],
    )
    assignment = {
        "operation_id": "copy-window", "fact_key": "pset:Fabrication.ThermalTransmittance",
        "source_fact_key": "pset:Fabrication.ThermalTransmittance", "value": fact.value,
        "value_type": fact.value_type, "unit": fact.unit,
        "ownership": "occurrence_direct", "applicability": "required",
        "source_kind": "authorized_type_cohort", "source_ref": "cohort:public-fixture",
        "provenance": ["offline-public-source-property"], "authoring_action": "set_occurrence_pset",
    }
    apply_semantic_assignments(
        model=model, operation={"operation_id": "copy-window", "semantic_assignments": [assignment]},
        application={"created": [{"role": "window", "global_id": copied_window.GlobalId}]}, target_role="window",
    )
    copied = next(
        prop for rel in copied_window.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties")
        for prop in rel.RelatingPropertyDefinition.HasProperties if prop.Name == "ThermalTransmittance"
    )
    assert copied.Unit is None
    assert copied.NominalValue.is_a() == "IfcThermalTransmittanceMeasure"
    assert copied.NominalValue.wrappedValue == source_property.NominalValue.wrappedValue == 25.0


def test_indexer_08_facts_are_stale_even_with_unchanged_source_hash():
    source_hash = "sha256:" + "a" * 64
    repository = SimpleNamespace(metadata=IndexMetadata(
        source_ifc_sha256=source_hash, ifc_schema="IFC2X3",
        extractor_version="text2ifc/ifc-indexer/0.8", source_size_bytes=1,
        created_at="2026-10-11T00:00:00Z",
    ))
    result = resolve_repair_intent(
        SimpleNamespace(model_fingerprint=source_hash), repository,
        expected_source_sha256=source_hash,
    )
    assert result.status == "failed"
    assert result.reason_code == "stale_index"
    assert result.operations == ()


def test_explicit_derived_unit_keeps_prior_extraction_and_unsupported_authoring(tmp_path):
    model = _model(tmp_path / "source.ifc", value_type="IfcThermalTransmittanceMeasure")
    _property(model).Unit = _thermal_unit(model)
    fact = extract_property_facts(model.by_guid(TARGET_ID))[0]
    assert fact.unit == "IfcDerivedUnit"
    assignment = {
        "operation_id": "set-property", "fact_key": "pset:Fabrication.Edge-Width",
        "source_fact_key": f"pset:{SET_NAME}.{PROPERTY_NAME}", "value": 75,
        "value_type": fact.value_type, "unit": fact.unit,
        "ownership": "occurrence_direct", "applicability": "required",
        "source_kind": "explicit_request", "source_ref": "request:/text",
        "provenance": ["offline-test"], "authoring_action": "set_occurrence_pset",
    }
    with pytest.raises(SemanticManifestError, match="SEMANTIC_PROPERTY_UNIT_UNSUPPORTED"):
        apply_semantic_assignments(
            model=model, operation={"operation_id": "set-property", "semantic_assignments": [assignment]},
            application={"modified": [{"role": "target", "global_id": TARGET_ID}]}, target_role="target",
        )


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize("damage", ["factor", "dimension", "unit_type", "base_prefix", "base_type", "missing_factor"])
def test_foot_label_requires_valid_length_conversion_definition(tmp_path, explicit, damage):
    model = _model(
        tmp_path / "source.ifc", project_units=("m" if explicit else "FOOT",),
        explicit="FOOT" if explicit else None,
    )
    foot = model.by_type("IfcConversionBasedUnit")[0]
    if damage == "factor":
        foot.ConversionFactor.ValueComponent = model.create_entity("IfcReal", 0.3)
    elif damage == "dimension":
        foot.Dimensions.LengthExponent = 2
    elif damage == "unit_type":
        foot.UnitType = "AREAUNIT"
    elif damage == "base_prefix":
        foot.ConversionFactor.UnitComponent.Prefix = "MILLI"
    elif damage == "base_type":
        foot.ConversionFactor.UnitComponent.UnitType = "AREAUNIT"
    else:
        incomplete = model.create_entity(
            "IfcConversionBasedUnit", UnitType="LENGTHUNIT", Name="FOOT", Dimensions=foot.Dimensions,
        )
        if explicit:
            _property(model).Unit = incomplete
        else:
            model.by_type("IfcProject")[0].UnitsInContext.Units = [incomplete]
    facts = extract_property_facts(model.by_guid(TARGET_ID))
    assert facts[0].unit is None
    assert _resolve(facts).reason_code == "CUSTOM_UNIT_REQUIRED"


@pytest.mark.parametrize("units", [("mm", "m"), ("mm", None)])
def test_all_matching_existing_facts_must_agree_before_unit_inference(tmp_path, units):
    model = _model(tmp_path / "source.ifc", explicit="mm")
    fact = extract_property_facts(model.by_guid(TARGET_ID))[0]
    result = _resolve([replace(fact, unit=unit) for unit in units])
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "CUSTOM_UNIT_REQUIRED"


@pytest.mark.parametrize("inherited", [False, True])
def test_new_measure_property_never_borrows_another_propertys_unit(tmp_path, inherited):
    model = _model(tmp_path / "source.ifc", explicit="mm")
    fact = extract_property_facts(model.by_guid(TARGET_ID))[0]
    result = _resolve(
        [replace(fact, inherited=inherited)], value_type="IfcLengthMeasure",
        property_name=PROPERTY_NAME if inherited else "New Width",
    )
    assert result.status is PropertyResolutionStatus.CLARIFICATION_REQUIRED
    assert result.reason_code == "CUSTOM_UNIT_REQUIRED"


@pytest.mark.parametrize("project_units,explicit,assignment_unit", [
    (("mm",), None, "mm"), (("m",), None, "m"), (("m",), "mm", "mm"),
    (("FOOT",), None, "FOOT"), (("m",), "FOOT", "FOOT"),
    (("mm",), "unsupported", "furlong"),
])
def test_authoring_retains_existing_unit_representation(tmp_path, project_units, explicit, assignment_unit):
    model = _model(tmp_path / "source.ifc", project_units=project_units, explicit=None if explicit == "unsupported" else explicit)
    if explicit == "unsupported":
        _property(model).Unit = model.create_entity(
            "IfcContextDependentUnit",
            Dimensions=model.create_entity("IfcDimensionalExponents", 1, 0, 0, 0, 0, 0, 0),
            UnitType="LENGTHUNIT", Name="furlong",
        )
    existing_unit = _property(model).Unit
    assignment = {
        "operation_id": "set-property", "fact_key": "pset:Fabrication.Edge-Width",
        "source_fact_key": f"pset:{SET_NAME}.{PROPERTY_NAME}", "value": 75,
        "value_type": "IfcLengthMeasure", "unit": assignment_unit,
        "ownership": "occurrence_direct", "applicability": "required",
        "source_kind": "explicit_request", "source_ref": "request:/text",
        "provenance": ["offline-test"], "authoring_action": "set_occurrence_pset",
    }
    def apply():
        apply_semantic_assignments(
            model=model, operation={"operation_id": "set-property", "semantic_assignments": [assignment]},
            application={"modified": [{"role": "target", "global_id": TARGET_ID}]}, target_role="target",
        )

    if explicit == "unsupported":
        with pytest.raises(SemanticManifestError, match="SEMANTIC_PROPERTY_UNIT_UNSUPPORTED"):
            apply()
        assert _property(model).NominalValue.wrappedValue == 25.0
        return
    apply()
    assert _property(model).Unit == existing_unit
    assert _property(model).NominalValue.wrappedValue == 75.0


@pytest.mark.parametrize("new_property", [False, True])
def test_foot_cannot_be_created_or_reinterpreted_from_a_different_unit(tmp_path, new_property):
    model = _model(tmp_path / "source.ifc", project_units=("FOOT" if new_property else "m",))
    property_name = "New Width" if new_property else PROPERTY_NAME
    assignment = {
        "operation_id": "set-property", "fact_key": "pset:Fabrication." + property_name.replace(" ", "-"),
        "source_fact_key": f"pset:{SET_NAME}.{property_name}", "value": 75,
        "value_type": "IfcLengthMeasure", "unit": "FOOT",
        "ownership": "occurrence_direct", "applicability": "required",
        "source_kind": "explicit_request", "source_ref": "request:/text",
        "provenance": ["offline-test"], "authoring_action": "set_occurrence_pset",
    }
    with pytest.raises(SemanticManifestError, match="SEMANTIC_PROPERTY_UNIT_UNSUPPORTED"):
        apply_semantic_assignments(
            model=model, operation={"operation_id": "set-property", "semantic_assignments": [assignment]},
            application={"modified": [{"role": "target", "global_id": TARGET_ID}]}, target_role="target",
        )
    assert [prop.Name for prop in model.by_type("IfcPropertySingleValue")] == [PROPERTY_NAME]
    assert _property(model).NominalValue.wrappedValue == 25.0


@pytest.mark.parametrize("ifc_class,project_unit,explicit,expected", [
    ("IfcDoor", "mm", None, "mm"), ("IfcDoor", "m", None, "m"),
    ("IfcWindow", "m", "mm", "mm"), ("IfcBeam", "mm", "m", "m"),
    ("IfcDoor", "FOOT", None, "FOOT"), ("IfcBeam", "m", "FOOT", "FOOT"),
])
def test_public_api_existing_measure_preview_confirmation_and_publish(tmp_path, ifc_class, project_unit, explicit, expected):
    path = tmp_path / "source.ifc"
    model = _model(path, project_units=(project_unit,), explicit=explicit, ifc_class=ifc_class, shared=True)
    model.write(str(path))
    before = path.read_bytes()
    before_unit = _property(model).Unit
    provider = _DraftProvider()
    api = _api(tmp_path / "out", ifc_class, SET_NAME, PROPERTY_NAME, provider, value=75)
    result = api.start(path, f"Geometry uses mm. Change existing {SET_NAME}.{PROPERTY_NAME} to 75; retain its original property type.")
    assert result.status == "clarification_required", result.to_dict()
    assert result.reason_code == "property_confirmation", result.to_dict()
    preview = result.clarification.property_preview
    assert (preview["value"], preview["value_type"], preview["unit"]) == (75, "IfcLengthMeasure", expected)
    assert provider.calls == []
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="CLARIFICATION_ANSWER_INVALID"):
        api.continue_with_answer(
            result.run_id, {"kind": "confirm_property", "preview_hash": "sha256:" + "0" * 64},
            clarification_id=result.clarification.clarification_id, expected_state_version=result.state_version,
        )
    final = api.continue_with_answer(
        result.run_id, {"kind": "confirm_property", "preview_hash": preview["preview_hash"]},
        clarification_id=result.clarification.clarification_id, expected_state_version=result.state_version,
    )
    assert final.status == "succeeded", final.to_dict()
    assert final.successful_artifact_publishable
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / final.artifacts["successful_ifc"]))
    prop = _property(repaired)
    assert prop.NominalValue.is_a() == "IfcLengthMeasure"
    assert prop.NominalValue.wrappedValue == 75.0
    assert (prop.Unit is None) == (before_unit is None)
    if before_unit is not None:
        # Shared-Pset copy-on-write may clone the unit along with the property.
        assert (prop.Unit.UnitType, getattr(prop.Unit, "Prefix", None), prop.Unit.Name) == (
            before_unit.UnitType, getattr(before_unit, "Prefix", None), before_unit.Name,
        )
    effective = ifcopenshell.util.unit.get_property_unit(prop, repaired)
    if expected == "FOOT":
        assert effective.is_a("IfcConversionBasedUnit")
        assert effective.Name == "FOOT"
        assert effective.UnitType == "LENGTHUNIT"
        assert tuple(effective.Dimensions) == (1, 0, 0, 0, 0, 0, 0)
        assert effective.ConversionFactor.ValueComponent.wrappedValue == 0.3048
        assert effective.ConversionFactor.UnitComponent.Name == "METRE"
        assert effective.ConversionFactor.UnitComponent.Prefix is None
        assert prop.NominalValue.wrappedValue * 0.3048 == pytest.approx(22.86)
    else:
        assert effective.Name == "METRE"
        assert effective.Prefix == ("MILLI" if expected == "mm" else None)
        assert prop.NominalValue.wrappedValue * (0.001 if effective.Prefix == "MILLI" else 1.0) == pytest.approx(0.075 if expected == "mm" else 75.0)
    assert _property(repaired, SIBLING_ID).NominalValue.wrappedValue == 25.0
    assert path.read_bytes() == before


@pytest.mark.parametrize("project_units", [None, ("mm", "m")])
def test_public_api_unresolved_unit_stops_without_provider_or_publication(tmp_path, project_units):
    path = tmp_path / "source.ifc"
    model = _model(path, project_units=project_units)
    model.write(str(path))
    before = path.read_bytes()
    provider = _DraftProvider()
    api = _api(tmp_path / "out", "IfcDoor", SET_NAME, PROPERTY_NAME, provider, value=75)
    result = api.start(path, "Change the existing Edge Width to 75 and preserve its type.")
    assert result.status == "clarification_required", result.to_dict()
    assert result.reason_code != "property_confirmation"
    assert not result.successful_artifact_publishable
    assert provider.calls == []
    assert path.read_bytes() == before
