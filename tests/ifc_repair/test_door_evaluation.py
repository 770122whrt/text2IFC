from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind
from text2ifc_ifc_repair.operations.door import (
    ADD_DOOR_EVALUATION_POLICY,
    FILL_DOOR_EVALUATION_POLICY,
)
from text2ifc_ifc_repair.semantic_facts import (
    SemanticFact,
    evaluate_operation_semantics,
)


def _fact(
    key: str,
    value: object,
    value_type: str,
    *,
    repaired: bool = False,
) -> SemanticFact:
    return SemanticFact(
        fact_key=key,
        value=value,
        value_type=value_type,
        unit=None,
        inherited=key == "relationship:type",
        pset_path=None,
        entity_source="IfcDoor:test",
        source_kind=(
            EvidenceSourceKind.REPAIRED_OUTPUT
            if repaired
            else EvidenceSourceKind.DETERMINISTIC_POLICY
        ),
        source_ref="test:door",
        provenance=("test:door-policy",),
        occurrence_scope="door_occurrence",
        canonical_source_kind=(
            "repaired_output" if repaired else "deterministic_derived"
        ),
    )


def _required_facts(*, repaired: bool = False) -> tuple[SemanticFact, ...]:
    return (
        _fact(
            "relationship:type",
            "2cXV28XOjE6f6irhu0COgZ",
            "IfcDoorStyle",
            repaired=repaired,
        ),
        _fact(
            "relationship:host",
            "2cXV28XOjE6f6irgi0COfF",
            "IfcWall",
            repaired=repaired,
        ),
        _fact(
            "relationship:storey",
            "2nxdYR2RHCDBiKJuiQr1XP",
            "IfcBuildingStorey",
            repaired=repaired,
        ),
        _fact(
            "attribute:OverallWidth",
            915.0,
            "IfcPositiveLengthMeasure",
            repaired=repaired,
        ),
        _fact(
            "attribute:OverallHeight",
            2134.0,
            "IfcPositiveLengthMeasure",
            repaired=repaired,
        ),
    )


def test_both_door_policies_pass_the_same_required_semantic_core() -> None:
    for policy in (
        ADD_DOOR_EVALUATION_POLICY,
        FILL_DOOR_EVALUATION_POLICY,
    ):
        checks = evaluate_operation_semantics(
            policy,
            expected_facts=_required_facts(),
            repaired_facts=_required_facts(repaired=True),
        )
        mandatory = tuple(item for item in checks if item.mandatory)
        assert mandatory
        assert all(item.status is EvaluationStatus.PASSED for item in mandatory)


def test_wrong_door_overall_width_fails_only_the_width_semantic_gate() -> None:
    repaired = list(_required_facts(repaired=True))
    repaired[-2] = _fact(
        "attribute:OverallWidth",
        900.0,
        "IfcPositiveLengthMeasure",
        repaired=True,
    )

    checks = evaluate_operation_semantics(
        ADD_DOOR_EVALUATION_POLICY,
        expected_facts=_required_facts(),
        repaired_facts=tuple(repaired),
    )
    failed = [item.check_id for item in checks if item.status is EvaluationStatus.FAILED]

    assert failed == ["door.width"]
