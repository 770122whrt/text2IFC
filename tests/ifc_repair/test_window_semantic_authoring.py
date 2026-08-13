from __future__ import annotations

import ifcopenshell

from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind
from text2ifc_ifc_repair.operations.window import WINDOW_EVALUATION_POLICY
from text2ifc_ifc_repair.semantic_authoring import apply_semantic_assignments
from text2ifc_ifc_repair.semantic_facts import extract_ifc_semantic_facts


def _assignment(
    fact_key,
    value,
    value_type,
    action,
    *,
    source_ref="request:/fixture",
    source_kind="deterministic_policy",
):
    return {
        "operation_id": "operation-window-001",
        "fact_key": fact_key,
        "source_fact_key": fact_key,
        "value": value,
        "value_type": value_type,
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required" if fact_key.startswith(("attribute:", "quantity:", "pset:")) else "conditional",
        "source_kind": source_kind,
        "source_ref": source_ref,
        "provenance": ["test:fixture"],
        "authoring_action": action,
    }


def test_generic_semantic_dispatch_reopens_typed_window_facts(tmp_path) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 10")
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
    owner_history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId="0000000000000000000001",
        OwnerHistory=owner_history,
        OverallWidth=1.0,
        OverallHeight=1.0,
    )
    material = model.create_entity("IfcMaterial", Name="Glass")
    system = model.create_entity("IfcClassification", Name="Uniclass")
    classification = model.create_entity(
        "IfcClassificationReference",
        ItemReference="Ss_25_30_95",
        Name="Windows",
        ReferencedSource=system,
    )
    operation = {
        "operation_id": "operation-window-001",
        "semantic_assignments": [
            _assignment("attribute:OverallWidth", 915.0, "IfcPositiveLengthMeasure", "set_attribute"),
            _assignment("attribute:OverallHeight", 1830.0, "IfcPositiveLengthMeasure", "set_attribute"),
            _assignment("pset:Pset_WindowCommon.IsExternal", True, "IfcBoolean", "set_occurrence_pset"),
            _assignment("quantity:window-base.Width", 915.0, "IfcLengthMeasure", "set_quantity"),
            _assignment("quantity:window-base.Height", 1830.0, "IfcLengthMeasure", "set_quantity"),
            _assignment("quantity:window-base.Area", 1674450.0, "IfcAreaMeasure", "set_quantity"),
            _assignment("material:Glass", "Glass", "IfcMaterial", "reuse_material", source_ref=f"resource:step:{material.id()}"),
            _assignment(
                "classification:Uniclass:Ss_25_30_95",
                {"system": "Uniclass", "identification": "Ss_25_30_95", "name": "Windows"},
                "IfcClassificationReference",
                "reuse_classification",
                source_ref=f"resource:step:{classification.id()}",
            ),
        ],
    }
    result = apply_semantic_assignments(
        model=model,
        operation=operation,
        application={"created": [{"role": "window", "global_id": str(window.GlobalId)}]},
        target_role="window",
    )
    output = tmp_path / "semantic.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    repaired = reopened.by_guid(str(window.GlobalId))
    facts = extract_ifc_semantic_facts(
        repaired,
        policy=WINDOW_EVALUATION_POLICY,
        source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
        source_ref="fixture",
        provenance=("reopened",),
    )
    by_key = {fact.fact_key: fact for fact in facts}

    assert float(repaired.OverallWidth) == 915.0
    assert by_key["pset:Pset_WindowCommon.IsExternal"].value is True
    assert by_key["quantity:window-base.Area"].value == 1674450.0
    assert by_key["material:Glass"].value_type == "IfcMaterial"
    assert by_key["classification:Uniclass:Ss_25_30_95"].value["name"] == "Windows"
    assert {item["role"] for item in result["created"]} == {
        "semantic_pset", "semantic_pset_relationship", "semantic_quantities",
        "semantic_quantity_relationship", "semantic_material_relationship",
        "semantic_classification_relationship",
    }


def test_window_semantic_dispatch_preserves_multiple_authorized_materials() -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 12")
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
    owner_history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId="0000000000000000000002",
        OwnerHistory=owner_history,
    )
    glass = model.create_entity("IfcMaterial", Name="Glass")
    sash = model.create_entity("IfcMaterial", Name="Sash")

    result = apply_semantic_assignments(
        model=model,
        operation={
            "operation_id": "operation-window-001",
            "semantic_assignments": [
                _assignment(
                    "material:Glass",
                    "Glass",
                    "IfcMaterial",
                    "reuse_material",
                    source_ref=f"resource:step:{glass.id()}",
                ),
                _assignment(
                    "material:Sash",
                    "Sash",
                    "IfcMaterial",
                    "reuse_material",
                    source_ref=f"resource:step:{sash.id()}",
                ),
            ],
        },
        application={
            "created": [{"role": "window", "global_id": str(window.GlobalId)}]
        },
        target_role="window",
    )

    assert {
        str(relation.RelatingMaterial.Name)
        for relation in window.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    } == {"Glass", "Sash"}
    assert {
        item["role"] for item in result["created"]
    } == {
        "semantic_material_relationship",
        "semantic_material_relationship_2",
    }


def test_window_explicit_material_uses_the_exact_requested_label() -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 12")
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
    owner_history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId="0000000000000000000003",
        OwnerHistory=owner_history,
    )

    apply_semantic_assignments(
        model=model,
        operation={
            "operation_id": "operation-window-001",
            "semantic_assignments": [
                _assignment(
                    "material:Powder-coated-Aluminium",
                    "Powder-coated Aluminium",
                    "IfcMaterial",
                    "reuse_material",
                    source_ref="request:/materials/0",
                    source_kind="explicit_request",
                )
            ],
        },
        application={
            "created": [{"role": "window", "global_id": str(window.GlobalId)}]
        },
        target_role="window",
    )

    relations = [
        relation
        for relation in window.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    assert len(relations) == 1
    assert relations[0].RelatingMaterial.Name == "Powder-coated Aluminium"
