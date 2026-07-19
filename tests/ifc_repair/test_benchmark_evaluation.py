import inspect
import json
from pathlib import Path

import pytest

from text2ifc_ifc_repair.benchmark_evaluation import (
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    _application_role_mapping,
    _not_evaluable_semantic_checks,
    evaluate_benchmark,
    evaluate_production,
    evaluate_mapped_role_semantics,
)
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind
from text2ifc_ifc_repair.operations.window import WINDOW_EVALUATION_POLICY
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.semantic_facts import SemanticFact
from text2ifc_ifc_repair.evaluation_projection import (
    PrivateCanaryLeakError,
    assert_public_bundle_has_no_canaries,
    project_public_evaluation,
)
from text2ifc_ifc_repair.workflow import _private_semantic_canaries


PRIVATE_CANARIES = (
    "CANARY-GOLD-GUID-7d7f",
    "CANARY-GOLD-VALUE-velvet",
    "C:/private-gold/CANARY-original.ifc",
    "CANARY-MUTATION-ROLE-window",
)


def _fact(
    *,
    fact_key: str,
    value: object,
    source_kind: EvidenceSourceKind,
    source_ref: str,
) -> SemanticFact:
    return SemanticFact(
        fact_key=fact_key,
        value=value,
        value_type="IfcLabel",
        unit=None,
        inherited=False,
        pset_path=None,
        entity_source="IfcWindow:semantic-window-role",
        source_kind=source_kind,
        source_ref=source_ref,
        provenance=("benchmark-role-map",),
    )


def _private_report(*, status: str = "failed") -> dict[str, object]:
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation/0.2",
        "policy_version": "phase8.1",
        "status": status,
        "reason": "Mandatory L2 semantic facts differ.",
        "complete_repair_success": status == "passed",
        "successful_artifact_publishable": status == "passed",
        "diagnostic_artifact_retained": status != "passed",
        "private_original_path": PRIVATE_CANARIES[2],
        "private_role_mapping": {
            PRIVATE_CANARIES[3]: PRIVATE_CANARIES[0],
        },
        "application": {
            "check_id": "application.valid",
            "status": "passed",
            "reason": "Application completed.",
            "evidence": [{"actual_value": PRIVATE_CANARIES[1]}],
        },
        "preservation": {
            "check_id": "preservation.valid",
            "status": "passed",
            "reason": "Unrelated roots are preserved.",
            "evidence": [{"source_ref": PRIVATE_CANARIES[2]}],
        },
        "operations": [
            {
                "operation_id": "operation-public-001",
                "operation_type": "add_window_with_opening_to_wall",
                "policy_id": "window.add-with-opening.l2",
                "policy_version": "0.1",
                "status": status,
                "reason": "Window semantic fidelity is incomplete.",
                "levels": [
                    {
                        "level": "L1",
                        "status": "passed",
                        "reason": "Geometry and relationships pass.",
                        "checks": [],
                    },
                    {
                        "level": "L2",
                        "status": status,
                        "reason": "Material differs.",
                        "checks": [
                            {
                                "check_id": f"window.material:material:{PRIVATE_CANARIES[1]}",
                                "policy_id": "window.add-with-opening.l2",
                                "applicability": "conditional",
                                "mandatory": True,
                                "status": status,
                                "reason": "Authorized material is missing.",
                                "evidence": [
                                    {
                                        "source_kind": "private_original",
                                        "source_ref": PRIVATE_CANARIES[0],
                                        "expected_value": PRIVATE_CANARIES[1],
                                        "actual_value": None,
                                        "provenance": [PRIVATE_CANARIES[3]],
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "level": "L3",
                        "status": "not_required",
                        "reason": "Authoring identity is observational.",
                        "checks": [],
                    },
                ],
            }
        ],
    }


def test_production_inputs_cannot_accept_gold_original_or_mutation_mapping() -> None:
    parameters = inspect.signature(ProductionEvaluationInputs).parameters
    forbidden = {
        "original_ifc_path",
        "private_original_ifc_path",
        "mutation_mapping",
        "private_mutation_mapping",
        "gold",
    }
    assert forbidden.isdisjoint(parameters)
    assert "production" in inspect.signature(BenchmarkEvaluationInputs).parameters

    with pytest.raises(TypeError):
        ProductionEvaluationInputs(  # type: ignore[call-arg]
            original_ifc_path=Path(PRIVATE_CANARIES[2]),
        )


def test_production_inputs_reject_private_original_semantic_fact_immediately() -> None:
    private_fact = _fact(
        fact_key="material:CANARY",
        value=PRIVATE_CANARIES[1],
        source_kind=EvidenceSourceKind.PRIVATE_ORIGINAL,
        source_ref=PRIVATE_CANARIES[0],
    )

    with pytest.raises(ValueError, match="PRODUCTION_PRIVATE_ORIGINAL_FORBIDDEN"):
        ProductionEvaluationInputs(
            damaged_ifc_path="missing-damaged.ifc",
            repaired_ifc_path="missing-repaired.ifc",
            changeset={"operations": []},
            application_result={"operations": []},
            registry=None,
            expected_facts_by_operation={"operation-1": (private_fact,)},
        )


def test_production_evaluator_rechecks_fact_sources_before_opening_ifc() -> None:
    public_fact = _fact(
        fact_key="material:public",
        value="public",
        source_kind=EvidenceSourceKind.EXPLICIT_REQUEST,
        source_ref="request:/material",
    )
    inputs = ProductionEvaluationInputs(
        damaged_ifc_path="missing-damaged.ifc",
        repaired_ifc_path="missing-repaired.ifc",
        changeset={"operations": []},
        application_result={"operations": []},
        registry=None,
        expected_facts_by_operation={"operation-1": (public_fact,)},
    )
    private_fact = _fact(
        fact_key="material:CANARY",
        value=PRIVATE_CANARIES[1],
        source_kind=EvidenceSourceKind.PRIVATE_ORIGINAL,
        source_ref=PRIVATE_CANARIES[0],
    )
    object.__setattr__(
        inputs,
        "expected_facts_by_operation",
        {"operation-1": (private_fact,)},
    )

    with pytest.raises(ValueError, match="PRODUCTION_PRIVATE_ORIGINAL_FORBIDDEN"):
        evaluate_production(inputs)


def test_application_role_mapping_is_owned_by_operation_id() -> None:
    mapping = _application_role_mapping(
        {
            "operations": [
                {
                    "operation_id": "operation-2",
                    "changes": {
                        "created": [{"role": "window", "global_id": "window-2"}]
                    },
                },
                {
                    "operation_id": "operation-1",
                    "changes": {
                        "created": [{"role": "window", "global_id": "window-1"}]
                    },
                },
            ]
        }
    )

    assert mapping == {
        "operation-1": {"window": "window-1"},
        "operation-2": {"window": "window-2"},
    }


def _missing_ifc_inputs() -> ProductionEvaluationInputs:
    operation_id = "operation-missing-ifc"
    return ProductionEvaluationInputs(
        damaged_ifc_path="missing-damaged.ifc",
        repaired_ifc_path="missing-repaired.ifc",
        changeset={
            "base_model_fingerprint": "sha256:missing",
            "scope": {"target_ids": ["wall-missing"], "forbidden_ids": []},
            "operations": [
                {
                    "operation_id": operation_id,
                    "operation_type": "add_window_with_opening_to_wall",
                    "target": {"wall_global_id": "wall-missing"},
                    "parameters": {},
                }
            ],
        },
        application_result={
            "valid": True,
            "published": True,
            "operations": [
                {
                    "operation_id": operation_id,
                    "changes": {"created": [], "modified": [], "removed": []},
                }
            ],
        },
        registry=create_default_registry(),
    )


def test_missing_repaired_ifc_returns_non_evaluable_report_for_both_entrypoints() -> None:
    production = evaluate_production(_missing_ifc_inputs())
    benchmark = evaluate_benchmark(
        BenchmarkEvaluationInputs(
            production=_missing_ifc_inputs(),
            private_original_ifc_path="missing-original.ifc",
            private_mutation_mapping={"operation-missing-ifc": {"window": "missing"}},
        )
    ).evaluation

    for evaluation in (production, benchmark):
        assert evaluation.complete_repair_success is False
        assert evaluation.successful_artifact_publishable is False
        assert evaluation.operations[0].level("L1").status.value != "passed"
        assert evaluation.operations[0].level("L2").status.value == "not_evaluable"


def test_extraction_error_makes_conditional_pset_and_quantity_not_evaluable() -> None:
    checks = _not_evaluable_semantic_checks(
        WINDOW_EVALUATION_POLICY,
        errors=("IFC_PSET_EXTRACTION_FAILED:boom",),
    )
    affected = [
        check
        for check in checks
        if check.check_id in {"window.pset", "window.quantity"}
    ]

    assert len(affected) == 2
    assert all(check.status.value == "not_evaluable" for check in affected)
    assert all(check.mandatory is True for check in affected)


def test_private_role_mapping_compares_semantics_without_gold_guid_reuse() -> None:
    original_guid = PRIVATE_CANARIES[0]
    repaired_guid = "RECREATED-PUBLIC-GUID-42"
    original = _fact(
        fact_key="material:CANARY",
        value=PRIVATE_CANARIES[1],
        source_kind=EvidenceSourceKind.PRIVATE_ORIGINAL,
        source_ref=original_guid,
    )
    repaired = _fact(
        fact_key="material:CANARY",
        value=PRIVATE_CANARIES[1],
        source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
        source_ref=repaired_guid,
    )

    checks = evaluate_mapped_role_semantics(
        policy=WINDOW_EVALUATION_POLICY,
        semantic_role="window",
        private_original_role_mapping={"window": original_guid},
        application_role_mapping={"window": repaired_guid},
        private_original_facts=(original,),
        repaired_facts=(repaired,),
    )

    material = next(check for check in checks if check.check_id.startswith("window.material"))
    assert original_guid != repaired_guid
    assert material.status.value == "passed"
    assert material.evidence[0].source_ref == original_guid


def test_public_projection_is_useful_positive_allowlist_and_contains_no_gold() -> None:
    private = _private_report()

    public = project_public_evaluation(private)

    assert public["schema_version"] == "text2ifc/ifc-repair-evaluation-public/0.2"
    assert public["status"] == "failed"
    assert public["complete_repair_success"] is False
    assert public["successful_artifact_publishable"] is False
    assert public["diagnostic_artifact_retained"] is True
    l2_check = public["operations"][0]["levels"][1]["checks"][0]
    assert l2_check["check_id"] == "window.material"
    assert l2_check["status"] == "failed"
    assert l2_check["difference_category"] == "material"
    assert l2_check["remediation_required"] is True
    assert l2_check["provenance_source_kinds"] == ["private_original"]
    encoded = json.dumps(public, ensure_ascii=False, sort_keys=True)
    for canary in PRIVATE_CANARIES:
        assert canary not in encoded
    assert "evidence" not in encoded
    assert "private_original_path" not in public
    assert "private_role_mapping" not in public


def test_whole_provider_and_public_bundle_canary_scan_fails_closed(tmp_path: Path) -> None:
    public = project_public_evaluation(_private_report())
    public_path = tmp_path / "evaluation-public.json"
    public_path.write_text(json.dumps(public), encoding="utf-8")
    bundle = {
        "provider_input": {"repair_request": "add a window"},
        "public_context": {"candidate_targets": []},
        "target_query": {"selector": "public-wall"},
        "changeset": {"operations": []},
        "public_evaluation": public,
        "report": "L2 material remediation is required",
        "manifest": {"artifacts": ["evaluation-public.json"]},
        "successful_output_path": None,
        "public_files": (public_path,),
    }
    assert_public_bundle_has_no_canaries(bundle, PRIVATE_CANARIES)

    leaking = dict(bundle)
    leaking["target_query"] = {"selector": PRIVATE_CANARIES[3]}
    with pytest.raises(PrivateCanaryLeakError) as error:
        assert_public_bundle_has_no_canaries(leaking, PRIVATE_CANARIES)
    assert PRIVATE_CANARIES[3] not in str(error.value)


def test_private_semantic_values_are_included_in_whole_bundle_canaries(
    tmp_path: Path,
) -> None:
    private = _private_report()
    canaries = _private_semantic_canaries(private)
    public_path = tmp_path / "runtime-artifact.json"
    public_path.write_text(
        json.dumps({"material": PRIVATE_CANARIES[1]}),
        encoding="utf-8",
    )

    assert PRIVATE_CANARIES[1] in canaries
    with pytest.raises(PrivateCanaryLeakError):
        assert_public_bundle_has_no_canaries((public_path,), canaries)


@pytest.mark.parametrize("status", ["failed", "partial", "not_evaluable"])
def test_non_passing_publication_is_diagnostic_only(status: str) -> None:
    public = project_public_evaluation(_private_report(status=status))

    assert public["status"] == status
    assert public["complete_repair_success"] is False
    assert public["successful_artifact_publishable"] is False
    assert public["diagnostic_artifact_retained"] is True
    assert "successful_output_path" not in public
    assert public["operations"][0]["levels"][2]["status"] == "not_required"
