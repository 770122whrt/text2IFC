from __future__ import annotations

import ifcopenshell
import pytest

from text2ifc_ifc_repair.semantic_authoring import (
    SemanticManifestError,
    apply_semantic_assignments,
)


def _model_and_window():
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 10.1")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="text2ifc test",
        ApplicationIdentifier="text2ifc",
    )
    person = model.create_entity("IfcPerson", FamilyName="Tester")
    user = model.create_entity(
        "IfcPersonAndOrganization",
        ThePerson=person,
        TheOrganization=organization,
    )
    history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId="0000000000000000000001",
        OwnerHistory=history,
        OverallWidth=915.0,
        OverallHeight=1830.0,
    )
    return model, history, window


def _assignment(value="EI30"):
    return {
        "operation_id": "window-1",
        "fact_key": "pset:Pset_WindowCommon.FireRating",
        "source_fact_key": "pset:Pset_WindowCommon.FireRating",
        "value": value,
        "value_type": "IfcLabel",
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required",
        "source_kind": "explicit_request",
        "source_ref": "request:/properties/0",
        "provenance": ["property-hash:sha256:fixture"],
        "authoring_action": "set_occurrence_pset",
    }


def _apply(model, window, *assignments):
    return apply_semantic_assignments(
        model=model,
        operation={
            "operation_id": "window-1",
            "semantic_assignments": list(assignments),
        },
        application={
            "created": [{"role": "window", "global_id": str(window.GlobalId)}]
        },
        target_role="window",
    )


def _direct_psets(window, name):
    return [
        rel.RelatingPropertyDefinition
        for rel in window.IsDefinedBy
        if rel.is_a("IfcRelDefinesByProperties")
        and rel.RelatingPropertyDefinition.is_a("IfcPropertySet")
        and rel.RelatingPropertyDefinition.Name == name
    ]


def test_create_append_and_update_reuse_one_direct_exact_pset(tmp_path) -> None:
    model, _, window = _model_and_window()
    created = _apply(model, window, _assignment("EI30"))
    pset = _direct_psets(window, "Pset_WindowCommon")[0]
    pset.HasProperties = [
        *pset.HasProperties,
        model.create_entity(
            "IfcPropertySingleValue",
            Name="Reference",
            NominalValue=model.create_entity("IfcIdentifier", "W-001"),
        ),
    ]
    updated = _apply(model, window, _assignment("EI60"))
    output = tmp_path / "properties.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output)).by_guid(str(window.GlobalId))
    sets = _direct_psets(reopened, "Pset_WindowCommon")

    assert len(sets) == 1
    values = {
        prop.Name: prop.NominalValue.wrappedValue
        for prop in sets[0].HasProperties
    }
    assert values == {"FireRating": "EI60", "Reference": "W-001"}
    assert {item["role"] for item in created["created"]} == {
        "semantic_pset",
        "semantic_pset_relationship",
    }
    assert updated["updated"][0]["role"] == "semantic_pset_property_updated"


def test_duplicate_direct_set_and_duplicate_property_fail_before_mutation() -> None:
    model, history, window = _model_and_window()
    for index in range(2):
        pset = model.create_entity(
            "IfcPropertySet",
            GlobalId=f"00000000000000000000{index + 2:02d}",
            OwnerHistory=history,
            Name="Pset_WindowCommon",
            HasProperties=[],
        )
        model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=f"00000000000000000000{index + 4:02d}",
            OwnerHistory=history,
            RelatedObjects=[window],
            RelatingPropertyDefinition=pset,
        )
    count = len(list(model))
    with pytest.raises(SemanticManifestError, match="DUPLICATE_DIRECT_PROPERTY_SET"):
        _apply(model, window, _assignment())
    assert len(list(model)) == count

    model, _, window = _model_and_window()
    _apply(model, window, _assignment())
    pset = _direct_psets(window, "Pset_WindowCommon")[0]
    pset.HasProperties = [*pset.HasProperties, pset.HasProperties[0]]
    count = len(list(model))
    with pytest.raises(SemanticManifestError, match="DUPLICATE_DIRECT_PROPERTY"):
        _apply(model, window, _assignment("EI60"))
    assert len(list(model)) == count


def test_exact_inherited_match_skips_direct_duplicate_but_mismatch_overrides() -> None:
    model, history, window = _model_and_window()
    inherited = model.create_entity(
        "IfcPropertySet",
        GlobalId="0000000000000000000010",
        OwnerHistory=history,
        Name="Pset_WindowCommon",
        HasProperties=[
            model.create_entity(
                "IfcPropertySingleValue",
                Name="FireRating",
                NominalValue=model.create_entity("IfcLabel", "EI30"),
            )
        ],
    )
    style = model.create_entity(
        "IfcWindowStyle",
        GlobalId="0000000000000000000011",
        OwnerHistory=history,
        Name="Existing style",
        HasPropertySets=[inherited],
        ConstructionType="NOTDEFINED",
        OperationType="NOTDEFINED",
        ParameterTakesPrecedence=False,
        Sizeable=False,
    )
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId="0000000000000000000012",
        OwnerHistory=history,
        RelatedObjects=[window],
        RelatingType=style,
    )

    same = _apply(model, window, _assignment("EI30"))
    assert not _direct_psets(window, "Pset_WindowCommon")
    assert same["skipped"] == ["pset:Pset_WindowCommon.FireRating"]

    _apply(model, window, _assignment("EI60"))
    direct = _direct_psets(window, "Pset_WindowCommon")
    assert len(direct) == 1
    assert direct[0].HasProperties[0].NominalValue.wrappedValue == "EI60"
    assert inherited.HasProperties[0].NominalValue.wrappedValue == "EI30"
