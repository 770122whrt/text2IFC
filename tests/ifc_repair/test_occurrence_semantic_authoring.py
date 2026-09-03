from __future__ import annotations

import hashlib
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair.semantic_authoring import (
    CanonicalSemanticSource,
    SemanticManifestError,
    apply_semantic_assignments,
    parse_semantic_manifest,
    semantic_manifest_to_dict,
)


def _model():
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 10.5")
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
    style_pset = model.create_entity(
        "IfcPropertySet",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history,
        Name="Pset_WindowCommon",
        HasProperties=[
            model.create_entity(
                "IfcPropertySingleValue",
                Name="Reference",
                NominalValue=model.create_entity("IfcIdentifier", "TYPE-A"),
            )
        ],
    )
    style = model.create_entity(
        "IfcWindowStyle",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history,
        Name="Type A",
        HasPropertySets=[style_pset],
        ConstructionType="NOTDEFINED",
        OperationType="NOTDEFINED",
        ParameterTakesPrecedence=False,
        Sizeable=False,
    )
    return model, history, style


def _assignment(
    operation_id: str,
    scope: str,
    fact_key: str,
    value,
    value_type: str,
    action: str,
) -> dict:
    return {
        "operation_id": operation_id,
        "scope": scope,
        "fact_key": fact_key,
        "source_fact_key": fact_key,
        "value": value,
        "value_type": value_type,
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required",
        "source_kind": "explicit_value",
        "source_ref": "request:/semantic-bundles/window-standard",
        "provenance": ["request:/semantic-bundles/window-standard"],
        "derivation": None,
        "authoring_action": action,
    }


def _direct_definitions(element, ifc_class: str, name: str):
    return [
        relation.RelatingPropertyDefinition
        for relation in element.IsDefinedBy
        if relation.is_a("IfcRelDefinesByProperties")
        and relation.RelatingPropertyDefinition.is_a(ifc_class)
        and relation.RelatingPropertyDefinition.Name == name
    ]


def _type_fingerprint(style) -> tuple:
    return (
        style.GlobalId,
        style.Name,
        tuple(
            (
                pset.GlobalId,
                pset.Name,
                tuple(
                    (prop.Name, prop.NominalValue.wrappedValue)
                    for prop in pset.HasProperties
                ),
            )
            for pset in style.HasPropertySets
        ),
    )


def test_five_bundle_consumers_author_isolated_window_and_opening_facts(
    tmp_path: Path,
) -> None:
    model, history, style = _model()
    style_before = _type_fingerprint(style)
    windows = []
    openings = []
    relation_ids: set[str] = set()
    operation_roles: dict[str, set[str]] = {}

    for index in range(5):
        operation_id = f"window-{index + 1}"
        window = model.create_entity(
            "IfcWindow",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=history,
            OverallWidth=915.0,
            OverallHeight=1830.0,
        )
        opening = model.create_entity(
            "IfcOpeningElement",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=history,
            Name=f"Opening {index + 1}",
        )
        model.create_entity(
            "IfcRelDefinesByType",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=history,
            RelatedObjects=[window],
            RelatingType=style,
        )
        assignments = [
            _assignment(
                operation_id,
                "window_occurrence",
                "pset:Pset_WindowCommon.IsExternal",
                True,
                "IfcBoolean",
                "set_occurrence_pset",
            ),
            _assignment(
                operation_id,
                "window_occurrence",
                "quantity:BaseQuantities.Width",
                915.0,
                "IfcQuantityLength",
                "set_quantity",
            ),
            _assignment(
                operation_id,
                "opening_occurrence",
                "quantity:BaseQuantities.Area",
                1_674_450.0,
                "IfcQuantityArea",
                "set_quantity",
            ),
        ]
        operation = {
            "operation_id": operation_id,
            "semantic_assignments": assignments,
        }
        application = {
            "created": [
                {"role": "window", "global_id": str(window.GlobalId)},
                {"role": "opening", "global_id": str(opening.GlobalId)},
            ]
        }
        for scope, role in (
            ("window_occurrence", "window"),
            ("opening_occurrence", "opening"),
        ):
            scoped = {
                **operation,
                "semantic_assignments": [
                    item for item in assignments if item["scope"] == scope
                ],
            }
            result = apply_semantic_assignments(
                model=model,
                operation=scoped,
                application=application,
                target_role=role,
            )
            relation_ids.update(
                item["global_id"]
                for item in result["created"]
                if item["ifc_class"] == "IfcRelDefinesByProperties"
            )
            operation_roles.setdefault(operation_id, set()).update(
                item["role"] for item in result["created"]
            )
        windows.append(window)
        openings.append(opening)

    assert len(relation_ids) == 15
    assert all(
        {
            "semantic_quantities",
            "semantic_quantity_relationship",
            "semantic_opening_quantities",
            "semantic_opening_quantity_relationship",
        }.issubset(roles)
        for roles in operation_roles.values()
    )
    assert _type_fingerprint(style) == style_before
    assert len(
        {
            _direct_definitions(item, "IfcPropertySet", "Pset_WindowCommon")[0].id()
            for item in windows
        }
    ) == 5

    output = tmp_path / "occurrence-semantics.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    for window, opening in zip(windows, openings, strict=True):
        reopened_window = reopened.by_guid(str(window.GlobalId))
        reopened_opening = reopened.by_guid(str(opening.GlobalId))
        assert (
            _direct_definitions(
                reopened_window, "IfcPropertySet", "Pset_WindowCommon"
            )[0]
            .HasProperties[0]
            .NominalValue.wrappedValue
            is True
        )
        assert (
            _direct_definitions(
                reopened_window, "IfcElementQuantity", "BaseQuantities"
            )[0]
            .Quantities[0]
            .LengthValue
            == 915.0
        )
        assert (
            _direct_definitions(
                reopened_opening, "IfcElementQuantity", "BaseQuantities"
            )[0]
            .Quantities[0]
            .AreaValue
            == 1_674_450.0
        )


def test_unsupported_quantity_measure_fails_closed() -> None:
    model, history, _ = _model()
    window = model.create_entity(
        "IfcWindow",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history,
    )
    assignment = _assignment(
        "window-invalid",
        "window_occurrence",
        "quantity:BaseQuantities.Count",
        2,
        "IfcQuantityCount",
        "set_quantity",
    )
    before = hashlib.sha256(model.to_string().encode("utf-8")).hexdigest()
    with pytest.raises(
        SemanticManifestError, match="SEMANTIC_QUANTITY_TYPE_UNSUPPORTED"
    ):
        apply_semantic_assignments(
            model=model,
            operation={
                "operation_id": "window-invalid",
                "semantic_assignments": [assignment],
            },
            application={
                "created": [{"role": "window", "global_id": str(window.GlobalId)}]
            },
            target_role="window",
        )
    # The outer apply transaction owns rollback; this unit proves the error is
    # raised before an unsupported quantity relation is attached.
    assert not _direct_definitions(window, "IfcElementQuantity", "BaseQuantities")
    assert hashlib.sha256(model.to_string().encode("utf-8")).hexdigest() == before


def test_quantity_units_are_converted_to_project_millimetres() -> None:
    model, history, _ = _model()
    length_unit = model.create_entity(
        "IfcSIUnit",
        UnitType="LENGTHUNIT",
        Prefix="MILLI",
        Name="METRE",
    )
    units = model.create_entity("IfcUnitAssignment", Units=[length_unit])
    model.create_entity(
        "IfcProject",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history,
        Name="Millimetre project",
        UnitsInContext=units,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history,
    )
    width = _assignment(
        "window-units",
        "window_occurrence",
        "quantity:BaseQuantities.Width",
        0.915,
        "IfcQuantityLength",
        "set_quantity",
    )
    width["unit"] = "m"
    area = _assignment(
        "window-units",
        "window_occurrence",
        "quantity:BaseQuantities.Area",
        1.67445,
        "IfcQuantityArea",
        "set_quantity",
    )
    area["unit"] = "m2"

    apply_semantic_assignments(
        model=model,
        operation={
            "operation_id": "window-units",
            "semantic_assignments": [width, area],
        },
        application={
            "created": [{"role": "window", "global_id": str(window.GlobalId)}]
        },
        target_role="window",
    )

    quantities = _direct_definitions(
        window, "IfcElementQuantity", "BaseQuantities"
    )[0].Quantities
    by_name = {str(item.Name): item for item in quantities}
    assert by_name["Width"].LengthValue == pytest.approx(915.0)
    assert by_name["Area"].AreaValue == pytest.approx(1_674_450.0)


def test_manifest_02_explicit_property_preserves_exact_ifc_spelling() -> None:
    model, history, _ = _model()
    window = model.create_entity(
        "IfcWindow",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=history,
    )
    assignment = _assignment(
        "window-exact-spelling",
        "window_occurrence",
        "pset:Identity-Data.Family-and-Type",
        "M_Fixed: 0915 x 1830mm",
        "IfcLabel",
        "set_occurrence_pset",
    )
    assignment["source_kind"] = "explicit_value"
    assignment["source_fact_key"] = (
        "pset:Identity Data.Family and Type"
    )

    apply_semantic_assignments(
        model=model,
        operation={
            "operation_id": "window-exact-spelling",
            "semantic_assignments": [assignment],
        },
        application={
            "created": [
                {"role": "window", "global_id": str(window.GlobalId)}
            ]
        },
        target_role="window",
    )

    pset = _direct_definitions(
        window,
        "IfcPropertySet",
        "Identity Data",
    )[0]
    assert [str(prop.Name) for prop in pset.HasProperties] == [
        "Family and Type"
    ]


def test_semantic_manifest_02_round_trips_scope_source_and_derivation() -> None:
    document = {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.2",
        "manifest_id": "manifest-window-1",
        "operation_id": "window-1",
        "operation_type": "add_window_with_opening_to_wall",
        "base_model_fingerprint": "sha256:" + "a" * 64,
        "policy": {
            "policy_id": "window.add-with-opening.l2",
            "policy_version": "0.2",
        },
        "assignments": [
            {
                **_assignment(
                    "window-1",
                    "opening_occurrence",
                    "quantity:BaseQuantities.Area",
                    1.67445,
                    "IfcQuantityArea",
                    "set_quantity",
                ),
                "source_fact_key": "parameters:/opening/width_mm+height_mm",
                "source_kind": "deterministic_derived",
                "source_ref": "operation:window-1:parameters/opening",
                "derivation": {
                    "formula": "width_mm * height_mm / 1000000",
                    "input_digest": "sha256:" + "b" * 64,
                },
            }
        ],
    }

    manifest = parse_semantic_manifest(document)

    assert semantic_manifest_to_dict(manifest) == document
    assert manifest.assignments[0].scope == "opening_occurrence"
    assert (
        manifest.assignments[0].source_kind
        is CanonicalSemanticSource.DETERMINISTIC_DERIVED
    )
