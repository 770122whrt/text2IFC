from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid

from text2ifc_ifc_repair.occurrence_fidelity import (
    CLASSIFICATIONS,
    OccurrenceFact,
    OccurrenceSnapshot,
    compare_occurrence_snapshots,
    snapshot_window_occurrence,
)


def _model(*, direct_rating: str | None = "Rw35", type_rating: str = "Rw30"):
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 10.5")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="fixture",
        ApplicationIdentifier="fixture",
    )
    owner = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=model.create_entity(
            "IfcPersonAndOrganization",
            ThePerson=model.create_entity("IfcPerson"),
            TheOrganization=organization,
        ),
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    window = model.create_entity(
        "IfcWindow",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="W-01",
        ObjectType="Fixed",
        Tag="W-01",
        OverallWidth=915.0,
        OverallHeight=1830.0,
    )
    opening = model.create_entity(
        "IfcOpeningElement",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="O-01",
        ObjectType="Opening",
        Tag="O-01",
    )
    wall = model.create_entity(
        "IfcWall",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="North wall",
    )
    model.create_entity(
        "IfcRelVoidsElement",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        RelatingBuildingElement=wall,
        RelatedOpeningElement=opening,
    )
    model.create_entity(
        "IfcRelFillsElement",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        RelatingOpeningElement=opening,
        RelatedBuildingElement=window,
    )

    type_pset = model.create_entity(
        "IfcPropertySet",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="Pset_WindowCommon",
        HasProperties=[
            model.create_entity(
                "IfcPropertySingleValue",
                Name="AcousticRating",
                NominalValue=model.create_entity("IfcLabel", type_rating),
            )
        ],
    )
    style = model.create_entity(
        "IfcWindowStyle",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="Type A",
        HasPropertySets=[type_pset],
        ConstructionType="NOTDEFINED",
        OperationType="NOTDEFINED",
        ParameterTakesPrecedence=False,
        Sizeable=False,
    )
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        RelatedObjects=[window],
        RelatingType=style,
    )
    if direct_rating is not None:
        direct_pset = model.create_entity(
            "IfcPropertySet",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner,
            Name="Pset_WindowCommon",
            HasProperties=[
                model.create_entity(
                    "IfcPropertySingleValue",
                    Name="AcousticRating",
                    NominalValue=model.create_entity(
                        "IfcLabel", direct_rating
                    ),
                )
            ],
        )
        model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner,
            RelatedObjects=[window],
            RelatingPropertyDefinition=direct_pset,
        )
    window_qto = model.create_entity(
        "IfcElementQuantity",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="BaseQuantities",
        Quantities=[
            model.create_entity(
                "IfcQuantityLength", Name="Width", LengthValue=915.0
            )
        ],
    )
    opening_qto = model.create_entity(
        "IfcElementQuantity",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="BaseQuantities",
        Quantities=[
            model.create_entity(
                "IfcQuantityArea", Name="Area", AreaValue=1_674_450.0
            )
        ],
    )
    for target, qto in ((window, window_qto), (opening, opening_qto)):
        model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner,
            RelatedObjects=[target],
            RelatingPropertyDefinition=qto,
        )
    return model, window, opening


def _snapshot_with(facts: dict[str, OccurrenceFact]) -> OccurrenceSnapshot:
    return OccurrenceSnapshot(
        window_global_id="W",
        window_name="W",
        opening_global_id="O",
        opening_name="O",
        facts=facts,
    )


def test_snapshot_uses_direct_over_type_and_separates_window_opening() -> None:
    model, window, _ = _model(direct_rating="Rw35", type_rating="Rw30")
    snapshot = snapshot_window_occurrence(model, str(window.GlobalId))

    rating = snapshot.facts[
        "window_occurrence:pset:Pset_WindowCommon.AcousticRating"
    ]
    assert rating.value == "Rw35"
    assert rating.ownership == "occurrence_direct"
    assert (
        snapshot.facts[
            "window_occurrence:quantity:BaseQuantities.Width"
        ].value
        == 915.0
    )
    assert (
        snapshot.facts[
            "opening_occurrence:quantity:BaseQuantities.Area"
        ].value
        == 1_674_450.0
    )


def test_matching_value_with_different_owner_is_ownership_only() -> None:
    key = "window_occurrence:pset:Pset_WindowCommon.IsExternal"
    expected = _snapshot_with(
        {
            key: OccurrenceFact(
                key, True, "IfcBoolean", None, "occurrence_direct", "guid:A"
            )
        }
    )
    actual = _snapshot_with(
        {
            key: OccurrenceFact(
                key, True, "IfcBoolean", None, "occurrence_direct", "guid:B"
            )
        }
    )

    report = compare_occurrence_snapshots(
        expected=expected,
        actual=actual,
        authorization_ledger=(key,),
        complete_replication=True,
    )

    assert report["details"][0]["classification"] == "ownership_only"
    assert report["occurrence_fidelity_success"] is True
    assert report["authoring_exactness"] is False


def test_type_value_cannot_hide_missing_occurrence_direct_value() -> None:
    key = "window_occurrence:pset:Pset_WindowCommon.AcousticRating"
    expected = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                "Rw35",
                "IfcLabel",
                None,
                "occurrence_direct",
                "guid:direct",
            )
        }
    )
    actual = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                "Rw35",
                "IfcLabel",
                None,
                "type_inherited",
                "guid:type",
            )
        }
    )

    report = compare_occurrence_snapshots(
        expected=expected,
        actual=actual,
        authorization_ledger=(key,),
    )

    assert report["details"][0]["classification"] == "unsupported_authoring"
    assert report["semantic_fidelity_success"] is False


def test_authorized_type_inheritance_makes_gold_direct_ownership_diagnostic() -> None:
    key = "window_occurrence:pset:Custom.Height"
    expected = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                1830.0,
                "IfcLengthMeasure",
                "mm",
                "occurrence_direct",
                "guid:gold-direct",
            )
        }
    )
    actual = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                1830.0,
                "IfcLengthMeasure",
                "mm",
                "type_inherited",
                "guid:approved-type",
            )
        }
    )

    report = compare_occurrence_snapshots(
        expected=expected,
        actual=actual,
        authorization_ledger=(key,),
        authorization_ownership={key: "type_inherited"},
        complete_replication=True,
    )

    assert report["details"][0]["classification"] == "ownership_only"
    assert report["occurrence_fidelity_success"] is True
    assert report["authoring_exactness"] is False


def test_units_are_canonical_and_wrong_values_are_blocking() -> None:
    key = "window_occurrence:quantity:BaseQuantities.Width"
    expected = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                915.0,
                "IfcQuantityLength",
                "millimetre",
                "occurrence_direct",
                "guid:A",
            )
        }
    )
    equivalent = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                915.0,
                "IfcQuantityLength",
                "mm",
                "occurrence_direct",
                "guid:A",
            )
        }
    )
    wrong = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                1200.0,
                "IfcQuantityLength",
                "mm",
                "occurrence_direct",
                "guid:A",
            )
        }
    )

    matched = compare_occurrence_snapshots(
        expected=expected, actual=equivalent, authorization_ledger=(key,)
    )
    failed = compare_occurrence_snapshots(
        expected=expected, actual=wrong, authorization_ledger=(key,)
    )

    assert matched["details"][0]["classification"] == "matched"
    assert failed["details"][0]["classification"] == "wrong_value"
    assert failed["occurrence_fidelity_success"] is False


def test_missing_authorized_unit_accepts_resolved_project_unit() -> None:
    key = "window_occurrence:pset:Dimensions.Width"
    expected = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                915.0,
                "IfcLengthMeasure",
                None,
                "type_inherited",
                "prototype:type-a",
            )
        }
    )
    actual = _snapshot_with(
        {
            key: OccurrenceFact(
                key,
                915.0,
                "IfcLengthMeasure",
                "mm",
                "type_inherited",
                "guid:type-pset",
            )
        }
    )

    report = compare_occurrence_snapshots(
        expected=expected,
        actual=actual,
        authorization_ledger=(key,),
    )

    assert report["details"][0]["classification"] == "ownership_only"
    assert report["occurrence_fidelity_success"] is True


def test_missing_unmentioned_and_extra_facts_classify_and_truncate() -> None:
    expected_facts = {
        f"window_occurrence:pset:Custom.P{index}": OccurrenceFact(
            f"window_occurrence:pset:Custom.P{index}",
            index,
            "IfcInteger",
            None,
            "occurrence_direct",
            f"guid:E{index}",
        )
        for index in range(5)
    }
    actual_facts = {
        "window_occurrence:pset:Custom.Extra": OccurrenceFact(
            "window_occurrence:pset:Custom.Extra",
            True,
            "IfcBoolean",
            None,
            "occurrence_direct",
            "guid:X",
        )
    }
    report = compare_occurrence_snapshots(
        expected=_snapshot_with(expected_facts),
        actual=_snapshot_with(actual_facts),
        authorization_ledger=("window_occurrence:pset:Custom.P0",),
        complete_replication=True,
        detail_limit=2,
    )

    assert report["counts"]["unsupported_authoring"] == 1
    assert report["counts"]["not_in_user_text"] == 5
    assert all(
        not item["required"]
        for item in report["details"]
        if item["classification"] == "not_in_user_text"
    )
    assert report["truncated"] is True
    assert report["detail_total"] == 6
    assert len(report["details"]) == 2


def test_report_schema_freezes_five_classifications_and_four_statuses() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = json.loads(
        (
            root
            / "schemas/agent/ifc-window-occurrence-comparison-0.1.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert tuple(
        schema["$defs"]["detail"]["properties"]["classification"]["enum"]
    ) == CLASSIFICATIONS
    for field in (
        "geometry_relationship_success",
        "semantic_fidelity_success",
        "occurrence_fidelity_success",
        "authoring_exactness",
    ):
        assert field in schema["required"]
