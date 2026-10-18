"""Synthetic writer siblings for unique paths inside same-name direct Psets."""

import ifcopenshell
import pytest

from tests.ifc_repair.test_property_authoring import (
    _apply_to_modified_target,
    _assignment,
    _direct_psets,
    _model_and_window,
)
from text2ifc_ifc_repair.semantic_authoring import SemanticManifestError


def _property(model, name, value="old", value_type="IfcLabel", unit=None):
    return model.create_entity(
        "IfcPropertySingleValue", Name=name,
        NominalValue=model.create_entity(value_type, value), Unit=unit,
    )


def _pset(model, history, targets, *properties, name="Other"):
    pset = model.create_entity(
        "IfcPropertySet", GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history, Name=name, HasProperties=properties,
    )
    relation = _relation(model, history, targets, pset)
    return pset, relation


def _relation(model, history, targets, pset):
    return model.create_entity(
        "IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history, RelatedObjects=targets,
        RelatingPropertyDefinition=pset,
    )


def _request(name, value="new", **overrides):
    return {
        **_assignment(value), "fact_key": f"pset:Other.{name}",
        "source_fact_key": f"pset:Other.{name}", **overrides,
    }


def _sibling(model, history):
    return model.create_entity(
        "IfcWindow", GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
    )


@pytest.mark.parametrize("selected_first", [False, True])
def test_unique_exact_path_preserves_other_same_name_pset_and_source(
    tmp_path, selected_first,
):
    model, history, target = _model_and_window()
    unit = model.create_entity(
        "IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE", Prefix="MILLI",
    )
    selected_prop = _property(model, "门扇侧边宽度", 70.0, "IfcLengthMeasure", unit)
    other_prop = _property(model, "Reference", "untouched")
    props = [selected_prop, other_prop] if selected_first else [other_prop, selected_prop]
    for prop in props:
        _pset(model, history, [target], prop)
    source = tmp_path / "source.ifc"
    model.write(str(source))
    source_bytes = source.read_bytes()
    original_ids = {pset.GlobalId for pset in _direct_psets(target, "Other")}
    model = ifcopenshell.open(str(source))
    target = model.by_guid(target.GlobalId)

    result = _apply_to_modified_target(
        model, target,
        _request("门扇侧边宽度", 75.0, value_type="IfcLengthMeasure", unit="mm"),
    )
    output = tmp_path / "repaired.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output)).by_guid(target.GlobalId)
    psets = _direct_psets(reopened, "Other")
    actual = {prop.Name: prop for pset in psets for prop in pset.HasProperties}
    assert {pset.GlobalId for pset in psets} == original_ids
    assert actual["门扇侧边宽度"].NominalValue.is_a() == "IfcLengthMeasure"
    assert actual["门扇侧边宽度"].NominalValue.wrappedValue == 75.0
    assert actual["门扇侧边宽度"].Unit.id() == unit.id()
    assert actual["Reference"].NominalValue.wrappedValue == "untouched"
    assert result["created"] == []
    assert source.read_bytes() == source_bytes


@pytest.mark.parametrize("ambiguous_name", ["Duplicate", "Missing"])
def test_ambiguous_path_fails_before_any_assignment_mutates(ambiguous_name):
    model, history, target = _model_and_window()
    _pset(model, history, [target], _property(model, "Unique"), _property(model, "Duplicate"))
    _pset(model, history, [target], _property(model, "Duplicate"))
    before = model.to_string()
    code = "DUPLICATE_DIRECT_PROPERTY" if ambiguous_name == "Duplicate" else "DUPLICATE_DIRECT_PROPERTY_SET"

    with pytest.raises(SemanticManifestError, match=f"{code}:"):
        _apply_to_modified_target(model, target, _request("Unique"), _request(ambiguous_name))

    assert model.to_string() == before


@pytest.mark.parametrize("sharing", ["relation", "separate_relation", "type"])
def test_selected_shared_pset_copies_only_target_and_preserves_other_owner(sharing):
    model, history, target = _model_and_window()
    sibling = _sibling(model, history)
    shared, relation = _pset(model, history, [target], _property(model, "Selected"))
    unrelated, _ = _pset(model, history, [target], _property(model, "Unrelated"))
    if sharing == "relation":
        relation.RelatedObjects = [target, sibling]
    elif sharing == "separate_relation":
        _relation(model, history, [sibling], shared)
    else:
        style = model.create_entity(
            "IfcWindowStyle", GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
            HasPropertySets=[shared], ConstructionType="NOTDEFINED",
            OperationType="NOTDEFINED", ParameterTakesPrecedence=False, Sizeable=False,
        )
        model.create_entity(
            "IfcRelDefinesByType", GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
            RelatedObjects=[sibling], RelatingType=style,
        )

    _apply_to_modified_target(model, target, _request("Selected"))

    selected = next(pset for pset in _direct_psets(target, "Other") if pset != unrelated)
    assert selected != shared
    assert selected.HasProperties[0].NominalValue.wrappedValue == "new"
    assert shared.HasProperties[0].NominalValue.wrappedValue == "old"
    assert unrelated in _direct_psets(target, "Other")
    if sharing == "type":
        assert tuple(style.HasPropertySets) == (shared,)
    else:
        assert _direct_psets(sibling, "Other") == [shared]
    if sharing == "relation":
        assert tuple(relation.RelatedObjects) == (sibling,)


def test_two_selected_shared_same_name_psets_receive_distinct_copy_identities():
    model, history, target = _model_and_window()
    sibling = _sibling(model, history)
    originals = [
        _pset(model, history, [target, sibling], _property(model, name))[0]
        for name in ["First", "Second"]
    ]

    _apply_to_modified_target(model, target, _request("First"), _request("Second"))

    selected = _direct_psets(target, "Other")
    assert len(selected) == 2
    assert len({root.GlobalId for root in model.by_type("IfcRoot")}) == len(model.by_type("IfcRoot"))
    assert {prop.Name: prop.NominalValue.wrappedValue for pset in selected for prop in pset.HasProperties} == {"First": "new", "Second": "new"}
    assert set(_direct_psets(sibling, "Other")) == set(originals)
    assert all(pset.HasProperties[0].NominalValue.wrappedValue == "old" for pset in originals)


def test_individual_shared_property_is_replaced_in_selected_pset_only():
    model, history, target = _model_and_window()
    sibling = _sibling(model, history)
    shared = _property(model, "Selected")
    selected, _ = _pset(model, history, [target], shared)
    _pset(model, history, [target], _property(model, "Unrelated"))
    other_owner, _ = _pset(model, history, [sibling], shared)

    _apply_to_modified_target(model, target, _request("Selected"))

    assert selected.HasProperties[0] != shared
    assert selected.HasProperties[0].NominalValue.wrappedValue == "new"
    assert other_owner.HasProperties[0] == shared
    assert shared.NominalValue.wrappedValue == "old"


def test_inherited_assignment_does_not_select_or_create_a_direct_pset():
    model, history, target = _model_and_window()
    for name in ["First", "Second"]:
        _pset(model, history, [target], _property(model, name))
    before = model.to_string()

    result = _apply_to_modified_target(
        model, target, _request("Inherited", ownership="type_inherited"),
    )

    assert result["skipped"] == ["pset:Other.Inherited"]
    assert model.to_string() == before


def test_public_api_unique_same_name_path_confirms_and_publishes(tmp_path):
    from tests.ifc_repair.test_existing_property_type_preservation import (
        SIBLING_ID, TARGET_ID, _DraftProvider, _api,
    )
    from tests.ifc_repair.test_existing_property_units import (
        PROPERTY_NAME, SET_NAME, _model,
    )

    source = tmp_path / "source.ifc"
    model = _model(source, shared=True)
    target = model.by_guid(TARGET_ID)
    unrelated, _ = _pset(
        model, target.OwnerHistory, [target], _property(model, "Reference"), name=SET_NAME,
    )
    unrelated_id = unrelated.GlobalId
    model.write(str(source))
    before = source.read_bytes()
    api = _api(tmp_path / "out", "IfcDoor", SET_NAME, PROPERTY_NAME, _DraftProvider(), value=75)

    result = api.start(source, f"Set existing {SET_NAME}.{PROPERTY_NAME} to 75; preserve its original type and unit.")
    assert result.reason_code == "property_confirmation", result.to_dict()
    preview = result.clarification.property_preview
    assert (preview["value"], preview["value_type"], preview["unit"]) == (75, "IfcLengthMeasure", "mm")
    final = api.continue_with_answer(
        result.run_id, {"kind": "confirm_property", "preview_hash": preview["preview_hash"]},
        clarification_id=result.clarification.clarification_id,
        expected_state_version=result.state_version,
    )

    assert final.status == "succeeded", final.to_dict()
    assert final.successful_artifact_publishable
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / final.artifacts["successful_ifc"]))
    for target_id, expected in [(TARGET_ID, 75.0), (SIBLING_ID, 25.0)]:
        prop = next(
            prop for pset in _direct_psets(repaired.by_guid(target_id), SET_NAME)
            for prop in pset.HasProperties if prop.Name == PROPERTY_NAME
        )
        assert prop.NominalValue.is_a() == "IfcLengthMeasure"
        assert prop.NominalValue.wrappedValue == expected
        assert prop.Unit is None
    assert repaired.by_guid(unrelated_id).HasProperties[0].NominalValue.wrappedValue == "old"
    assert source.read_bytes() == before
