import inspect
import json
from pathlib import Path

import pytest

from text2ifc_ifc_repair.benchmark_evaluation import (
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    _application_role_mapping,
    evaluate_production,
    evaluate_mapped_role_semantics,
)
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind
from text2ifc_ifc_repair.operations.window import WINDOW_EVALUATION_POLICY
from text2ifc_ifc_repair.semantic_facts import SemanticFact
from text2ifc_ifc_repair.evaluation_projection import (
    PrivateCanaryLeakError,
    assert_public_bundle_has_no_canaries,
    project_public_evaluation,
)


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


@pytest.mark.parametrize("status", ["failed", "partial", "not_evaluable"])
def test_non_passing_publication_is_diagnostic_only(status: str) -> None:
    public = project_public_evaluation(_private_report(status=status))

    assert public["status"] == status
    assert public["complete_repair_success"] is False
    assert public["successful_artifact_publishable"] is False
    assert public["diagnostic_artifact_retained"] is True
    assert "successful_output_path" not in public
    assert public["operations"][0]["levels"][2]["status"] == "not_required"
