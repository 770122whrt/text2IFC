from __future__ import annotations

import hashlib

import ifcopenshell
import pytest

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.semantic_authoring import apply_semantic_assignments


OPERATION_TYPE = "set_occurrence_properties"


def _model_and_element(ifc_class: str):
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 10.2")
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
    element = model.create_entity(
        ifc_class,
        GlobalId="0000000000000000000001",
        OwnerHistory=history,
        Name="Target occurrence",
    )
    return model, element


def _operation(element, *, value=True):
    return {
        "operation_id": "property-operation-1",
        "operation_type": OPERATION_TYPE,
        "target": {"element_global_id": str(element.GlobalId)},
        "parameters": {},
        "semantic_assignments": [
            {
                "operation_id": "property-operation-1",
                "fact_key": "pset:Pset_WindowCommon.IsExternal",
                "source_fact_key": "pset:Pset_WindowCommon.IsExternal",
                "value": value,
                "value_type": "IfcBoolean",
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_request",
                "source_ref": "property-resolution:/claim-001/decision.json",
                "provenance": ["property-resolution:sha256:fixture"],
                "authoring_action": "set_occurrence_pset",
            }
        ],
    }


def test_default_registry_exposes_generic_occurrence_property_operation() -> None:
    definition = create_default_registry().require(OPERATION_TYPE)

    assert definition.target_ifc_classes == (
        "IfcDoor",
        "IfcWall",
        "IfcWallStandardCase",
        "IfcWindow",
    )
    assert definition.editable_occurrence_ifc_classes == definition.target_ifc_classes
    assert definition.parameter_schema["maxProperties"] == 0
    assert definition.evaluation_policy.semantic_role == "target"
    assert (
        definition.capability_constraints["semantic_authoring_scope"]
        == "explicit_request_only"
    )


@pytest.mark.parametrize(
    "ifc_class",
    ["IfcWall", "IfcWallStandardCase", "IfcDoor", "IfcWindow"],
)
def test_generic_operation_modifies_only_selected_supported_occurrence(
    ifc_class: str,
) -> None:
    model, element = _model_and_element(ifc_class)
    registry = create_default_registry()
    operation = _operation(element)

    precondition = registry.dispatch(
        "precondition_checker",
        operation,
        model=model,
    )
    application = registry.dispatch("applicator", operation, model=model)
    semantic = apply_semantic_assignments(
        model=model,
        operation=operation,
        application=application,
        target_role="target",
    )
    application["created"].extend(semantic["created"])
    application["modified"].extend(semantic["modified"])
    postcondition = registry.dispatch(
        "postcondition_checker",
        operation,
        model=model,
        application=application,
    )

    assert precondition["issues"] == []
    assert application["modified"][0] == {
        "role": "target",
        "ifc_class": ifc_class,
        "global_id": str(element.GlobalId),
    }
    assert postcondition["valid"] is True
    assert element.ObjectPlacement is None
    assert element.Representation is None


def test_generic_operation_rejects_unsupported_target_class() -> None:
    model, column = _model_and_element("IfcColumn")
    registry = create_default_registry()

    result = registry.dispatch(
        "precondition_checker",
        _operation(column),
        model=model,
    )

    assert result["issues"][0]["code"] == "PROPERTY_TARGET_CLASS_UNSUPPORTED"


def test_bound_generic_operation_reopens_with_requested_property(tmp_path) -> None:
    model, window = _model_and_element("IfcWindow")
    source = tmp_path / "source.ifc"
    output = tmp_path / "repaired.ifc"
    model.write(str(source))
    request = "把目标窗户标记为外窗"
    operation = {
        **_operation(window),
        "evidence_refs": ["property-resolution:/claim-001/decision.json"],
        "semantic_manifest": {
            "manifest_id": "manifest-property-operation-1",
            "policy_id": "occurrence.property.l2",
            "policy_version": "0.1",
        },
    }
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.2",
        "changeset_id": "changeset-property-operation-1",
        "binding_status": "bound",
        "base_model_fingerprint": "sha256:"
        + hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_request_hash": "sha256:"
        + hashlib.sha256(request.encode("utf-8")).hexdigest(),
        "scope": {
            "target_ids": [str(window.GlobalId)],
            "forbidden_ids": [],
        },
        "evidence_refs": ["property-resolution:/claim-001/decision.json"],
        "preconditions": ["target_exists"],
        "postconditions": ["requested_properties_match"],
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "operations": [operation],
    }

    result = apply_changeset(
        damaged_ifc_path=source,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] and result["published"]
    repaired = ifcopenshell.open(str(output)).by_guid(str(window.GlobalId))
    pset = next(
        relation.RelatingPropertyDefinition
        for relation in repaired.IsDefinedBy
        if relation.is_a("IfcRelDefinesByProperties")
    )
    prop = next(item for item in pset.HasProperties if item.Name == "IsExternal")
    assert prop.NominalValue.is_a() == "IfcBoolean"
    assert prop.NominalValue.wrappedValue is True
