from __future__ import annotations

from dataclasses import replace

import pytest

from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.evaluation_policy import (
    EvidenceSourceKind,
    SemanticApplicability,
    extend_policy_with_explicit_facts,
)
from text2ifc_ifc_repair.operations.window import WINDOW_EVALUATION_POLICY
from text2ifc_ifc_repair.semantic_facts import (
    SemanticFact,
    evaluate_operation_semantics,
)


FACT_KEY = "pset:Custom_Asset.AssetCode"


def _fact(
    *,
    value: object = "W-007",
    value_type: str = "IfcLabel",
    unit: str | None = None,
    inherited: bool = False,
    source_kind: EvidenceSourceKind = EvidenceSourceKind.EXPLICIT_REQUEST,
) -> SemanticFact:
    return SemanticFact(
        fact_key=FACT_KEY,
        value=value,
        value_type=value_type,
        unit=unit,
        inherited=inherited,
        pset_path="Custom_Asset.AssetCode",
        entity_source="IfcWindow:fixture",
        source_kind=source_kind,
        source_ref="request:/properties/0",
        provenance=("property-hash:sha256:fixture",),
    )


def _policy():
    return extend_policy_with_explicit_facts(
        WINDOW_EVALUATION_POLICY,
        (FACT_KEY,),
        applicability=SemanticApplicability.REQUIRED,
    )


def test_requested_property_is_one_stable_mandatory_dynamic_l2_check() -> None:
    results = evaluate_operation_semantics(
        _policy(),
        expected_facts=(_fact(),),
        repaired_facts=(
            _fact(source_kind=EvidenceSourceKind.REPAIRED_OUTPUT),
        ),
    )
    requested = next(item for item in results if item.check_id == "explicit.pset-Custom_Asset.AssetCode")
    assert requested.status is EvaluationStatus.PASSED
    assert requested.mandatory is True
    assert requested.applicability == "required"


@pytest.mark.parametrize(
    "actual",
    [
        None,
        _fact(value="W-008", source_kind=EvidenceSourceKind.REPAIRED_OUTPUT),
        _fact(value_type="IfcIdentifier", source_kind=EvidenceSourceKind.REPAIRED_OUTPUT),
        _fact(unit="custom-unit", source_kind=EvidenceSourceKind.REPAIRED_OUTPUT),
        _fact(inherited=True, source_kind=EvidenceSourceKind.REPAIRED_OUTPUT),
    ],
)
def test_missing_value_type_unit_or_ownership_mismatch_fails(actual) -> None:
    repaired = () if actual is None else (actual,)
    results = evaluate_operation_semantics(
        _policy(),
        expected_facts=(_fact(),),
        repaired_facts=repaired,
    )
    requested = next(item for item in results if item.check_id == "explicit.pset-Custom_Asset.AssetCode")
    assert requested.status is EvaluationStatus.FAILED
    assert requested.mandatory is True
