from __future__ import annotations

from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.semantic_authoring import apply_semantic_assignments
from text2ifc_knowledge.property_search import (
    PropertyKnowledgeQuery,
    PropertyKnowledgeResolver,
    VectorHit,
    create_historical_alias_baseline_resolver,
)


OPERATION_TYPE = "set_occurrence_properties"


def _model_and_element(ifc_class: str):
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Phase 12")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="text2ifc structural property test",
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
        Name="Structural target",
    )
    return model, element


def _assignment(
    ifc_class: str,
    *,
    set_name: str | None = None,
    value_type: str = "IfcBoolean",
    scope: str = "target_occurrence",
) -> dict:
    family = ifc_class.removeprefix("Ifc")
    canonical_set = set_name or f"Pset_{family}Common"
    fact_key = f"pset:{canonical_set}.LoadBearing"
    return {
        "operation_id": "structural-property-1",
        "scope": scope,
        "fact_key": fact_key,
        "source_fact_key": fact_key,
        "value": True,
        "value_type": value_type,
        "unit": None,
        "ownership": "occurrence_direct",
        "applicability": "required",
        "source_kind": "explicit_request",
        "source_ref": "request:/properties/0",
        "provenance": ["property-resolution:sha256:fixture"],
        "authoring_action": "set_occurrence_pset",
    }


def _operation(element, assignment: dict) -> dict:
    return {
        "operation_id": "structural-property-1",
        "operation_type": OPERATION_TYPE,
        "target": {"element_global_id": str(element.GlobalId)},
        "parameters": {},
        "semantic_assignments": [assignment],
    }


def test_generic_occurrence_property_scope_includes_both_structural_families() -> None:
    definition = create_default_registry().require(OPERATION_TYPE)

    assert definition.target_ifc_classes == (
        "IfcBeam",
        "IfcColumn",
        "IfcDoor",
        "IfcWall",
        "IfcWallStandardCase",
        "IfcWindow",
    )
    assert definition.editable_occurrence_ifc_classes == definition.target_ifc_classes


@pytest.mark.parametrize(
    ("ifc_class", "set_name"),
    (
        ("IfcBeam", "Pset_BeamCommon"),
        ("IfcColumn", "Pset_ColumnCommon"),
    ),
)
def test_structural_load_bearing_resolves_to_exact_applicable_typed_fact(
    ifc_class: str,
    set_name: str,
) -> None:
    decision = create_historical_alias_baseline_resolver().resolve(
        PropertyKnowledgeQuery(
            target_ifc_class=ifc_class,
            phrase=f"{set_name}.LoadBearing",
            raw_value=True,
            scope="occurrence_direct",
        )
    )

    assert decision.status == "standard_resolved"
    assert decision.reason_code == "CANONICAL_EXACT"
    assert decision.exact_intent is not None
    assert decision.exact_intent.set_name == set_name
    assert decision.exact_intent.property_name == "LoadBearing"
    assert decision.exact_intent.requested_value_type == "IfcBoolean"
    assert decision.exact_intent.value is True
    assert decision.exact_intent.scope == "occurrence_direct"


class _VectorOnly:
    def __init__(self, record_id: str) -> None:
        self.record_id = record_id

    def search(self, text: str, *, limit: int = 10) -> tuple[VectorHit, ...]:
        del text, limit
        return (VectorHit(self.record_id, 0.99),)


def test_vector_only_cross_class_and_noncanonical_structural_paths_have_no_authority() -> None:
    base = create_historical_alias_baseline_resolver()
    beam_record = next(
        record
        for record in base.records
        if record.canonical_path == "Pset_BeamCommon.LoadBearing"
    )
    vector_only = PropertyKnowledgeResolver(
        registry=base.registry,
        records=base.records,
        aliases=(),
        vector_index=_VectorOnly(beam_record.record_id),
    )

    vector_decision = vector_only.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcBeam",
            phrase="structural carrying intent",
            raw_value=True,
        )
    )
    cross_class = base.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcBeam",
            phrase="Pset_ColumnCommon.LoadBearing",
            raw_value=True,
        )
    )
    noncanonical = base.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcBeam",
            phrase="Pset_BeamCommon.load_bearing",
            raw_value=True,
        )
    )

    assert vector_decision.reason_code == "VECTOR_ONLY_NOT_AUTHORIZED"
    assert vector_decision.exact_intent is None
    assert cross_class.exact_intent is None
    assert noncanonical.exact_intent is None
    with pytest.raises(ValueError, match="PROPERTY_VALUE_TYPE_INCOMPATIBLE"):
        base.resolve(
            PropertyKnowledgeQuery(
                target_ifc_class="IfcBeam",
                phrase="Pset_BeamCommon.LoadBearing",
                raw_value="true",
            )
        )


@pytest.mark.parametrize(
    ("change", "expected_code"),
    (
        ({"set_name": "Pset_ColumnCommon"}, "PROPERTY_PSET_NOT_APPLICABLE"),
        ({"value_type": "IfcLabel"}, "PROPERTY_VALUE_TYPE_MISMATCH"),
        ({"scope": "window_occurrence"}, "PROPERTY_ASSIGNMENT_SCOPE_UNSUPPORTED"),
    ),
)
def test_structural_precondition_rejects_one_defect_authority(
    change: dict[str, str],
    expected_code: str,
) -> None:
    model, beam = _model_and_element("IfcBeam")
    assignment = _assignment("IfcBeam", **change)

    result = create_default_registry().dispatch(
        "precondition_checker",
        _operation(beam, assignment),
        model=model,
    )

    assert result["issues"][0]["code"] == expected_code


@pytest.mark.parametrize(
    ("ifc_class", "role", "scope", "set_name"),
    (
        ("IfcBeam", "beam", "beam_occurrence", "Pset_BeamCommon"),
        ("IfcColumn", "column", "column_occurrence", "Pset_ColumnCommon"),
    ),
)
def test_structural_semantic_role_authors_exact_property_and_reopens(
    tmp_path: Path,
    ifc_class: str,
    role: str,
    scope: str,
    set_name: str,
) -> None:
    model, element = _model_and_element(ifc_class)
    operation = _operation(
        element,
        _assignment(ifc_class, scope=scope),
    )

    result = apply_semantic_assignments(
        model=model,
        operation=operation,
        application={
            "created": [
                {
                    "role": role,
                    "ifc_class": ifc_class,
                    "global_id": str(element.GlobalId),
                }
            ]
        },
        target_role=role,
    )
    output = tmp_path / f"{role}.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output)).by_guid(str(element.GlobalId))

    pset = next(
        relation.RelatingPropertyDefinition
        for relation in reopened.IsDefinedBy
        if relation.is_a("IfcRelDefinesByProperties")
        and relation.RelatingPropertyDefinition.Name == set_name
    )
    prop = next(item for item in pset.HasProperties if item.Name == "LoadBearing")
    assert prop.NominalValue.is_a() == "IfcBoolean"
    assert prop.NominalValue.wrappedValue is True
    assert all(item["role"].startswith(f"semantic_{role}_") for item in result["created"])
    assert not reopened.HasAssociations
