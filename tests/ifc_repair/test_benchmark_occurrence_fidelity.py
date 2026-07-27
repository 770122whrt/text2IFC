from __future__ import annotations

import ifcopenshell
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair.benchmark_evaluation import (
    _occurrence_fidelity_check,
)
from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind
from text2ifc_ifc_repair.semantic_facts import SemanticFact


def _window_model(*, width: float, rating: str = "Rw35"):
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="Fixture")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="1",
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
        OverallWidth=width,
        OverallHeight=1830.0,
    )
    pset = model.create_entity(
        "IfcPropertySet",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        Name="Pset_WindowCommon",
        HasProperties=[
            model.create_entity(
                "IfcPropertySingleValue",
                Name="AcousticRating",
                NominalValue=model.create_entity("IfcLabel", rating),
            )
        ],
    )
    model.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner,
        RelatedObjects=[window],
        RelatingPropertyDefinition=pset,
    )
    return model, str(window.GlobalId)


def _expected_width(value: float) -> SemanticFact:
    return SemanticFact(
        fact_key="attribute:OverallWidth",
        value=value,
        value_type="IfcPositiveLengthMeasure",
        unit=None,
        inherited=False,
        pset_path=None,
        entity_source="request",
        source_kind=EvidenceSourceKind.EXPLICIT_REQUEST,
        source_ref="request:/opening/width",
        provenance=("request:/opening/width",),
        occurrence_scope="window_occurrence",
        canonical_source_kind="explicit_value",
    )


def _expected_rating(value: str = "Rw35") -> SemanticFact:
    return SemanticFact(
        fact_key="pset:Pset_WindowCommon.AcousticRating",
        value=value,
        value_type="IfcLabel",
        unit=None,
        inherited=False,
        pset_path="Pset_WindowCommon.AcousticRating",
        entity_source="request",
        source_kind=EvidenceSourceKind.EXPLICIT_REQUEST,
        source_ref="request:/properties/acoustic-rating",
        provenance=("request:/properties/acoustic-rating",),
        occurrence_scope="window_occurrence",
        canonical_source_kind="explicit_value",
    )


def _expected_height(value: float = 1830.0) -> SemanticFact:
    fact = _expected_width(value)
    return SemanticFact(
        **{
            **fact.__dict__,
            "fact_key": "attribute:OverallHeight",
            "source_ref": "request:/opening/height",
            "provenance": ("request:/opening/height",),
        }
    )


def test_production_occurrence_check_passes_authorized_value() -> None:
    repaired, repaired_id = _window_model(width=915.0)

    result = _occurrence_fidelity_check(
        operation_id="window-1",
        repaired_model=repaired,
        repaired_id=repaired_id,
        public_expected=(
            _expected_width(915.0),
            _expected_height(),
            _expected_rating(),
        ),
        original_model=None,
        original_id=None,
        complete_replication=False,
        extraction_errors=(),
    )

    assert result.check_id == "l2.window-occurrence-fidelity"
    assert result.mandatory is True
    assert result.status is EvaluationStatus.PASSED


def test_production_occurrence_check_blocks_wrong_authorized_value() -> None:
    repaired, repaired_id = _window_model(width=1200.0)

    result = _occurrence_fidelity_check(
        operation_id="window-1",
        repaired_model=repaired,
        repaired_id=repaired_id,
        public_expected=(_expected_width(915.0),),
        original_model=None,
        original_id=None,
        complete_replication=False,
        extraction_errors=(),
    )

    assert result.status is EvaluationStatus.FAILED
    report = result.evidence[0].actual_value
    assert report["counts"]["wrong_value"] == 1


def test_private_complete_replication_passes_ownership_only() -> None:
    original, original_id = _window_model(width=915.0)
    repaired, repaired_id = _window_model(width=915.0)

    result = _occurrence_fidelity_check(
        operation_id="window-1",
        repaired_model=repaired,
        repaired_id=repaired_id,
        public_expected=(
            _expected_width(915.0),
            _expected_height(),
            _expected_rating(),
        ),
        original_model=original,
        original_id=original_id,
        complete_replication=True,
        extraction_errors=(),
    )

    assert result.status is EvaluationStatus.PASSED
    report = result.evidence[0].actual_value
    assert report["counts"]["ownership_only"] >= 1
    assert report["authoring_exactness"] is False


@pytest.mark.parametrize(
    "public_expected,actual_width,expected_classification",
    [
        ((), 915.0, "not_in_user_text"),
        ((_expected_width(915.0),), 1200.0, "wrong_value"),
    ],
)
def test_private_complete_replication_blocks_incomplete_or_wrong_text_authority(
    public_expected,
    actual_width: float,
    expected_classification: str,
) -> None:
    original, original_id = _window_model(width=915.0)
    repaired, repaired_id = _window_model(width=actual_width)

    result = _occurrence_fidelity_check(
        operation_id="window-1",
        repaired_model=repaired,
        repaired_id=repaired_id,
        public_expected=public_expected,
        original_model=original,
        original_id=original_id,
        complete_replication=True,
        extraction_errors=(),
    )

    assert result.status is EvaluationStatus.FAILED
    report = result.evidence[0].actual_value
    assert report["counts"][expected_classification] >= 1


def test_invalid_private_mapping_is_not_evaluable() -> None:
    repaired, repaired_id = _window_model(width=915.0)

    result = _occurrence_fidelity_check(
        operation_id="window-1",
        repaired_model=repaired,
        repaired_id=repaired_id,
        public_expected=(_expected_width(915.0),),
        original_model=None,
        original_id=None,
        complete_replication=True,
        extraction_errors=(),
    )

    assert result.status is EvaluationStatus.NOT_EVALUABLE
    assert "PRIVATE_WINDOW_MAPPING_REQUIRED" in str(
        result.evidence[0].actual_value
    )
