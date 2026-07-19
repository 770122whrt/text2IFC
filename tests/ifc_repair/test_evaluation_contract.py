from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest


SCHEMA_VERSION = "text2ifc/ifc-repair-evaluation/0.2"
LEGACY_SCHEMA_VERSION = "text2ifc/ifc-repair-evaluation/0.1"
ALL_STATUSES = {
    "passed",
    "failed",
    "partial",
    "not_required",
    "not_evaluable",
}


def _api() -> Any:
    models = importlib.import_module("text2ifc_ifc_repair.evaluation_models")
    evaluation = importlib.import_module("text2ifc_ifc_repair.evaluation")
    return type(
        "EvaluationApi",
        (),
        {
            "models": models,
            "evaluation": evaluation,
        },
    )


def _evidence(api: Any, fact_id: str = "fact.window.geometry") -> Any:
    return api.models.EvidenceFact(
        fact_id=fact_id,
        source_kind="independent_measurement",
        source_ref="repaired.ifc#window",
        expected_state="available",
        actual_state="available",
        expected_value={"width_mm": 1800.0},
        actual_value={"width_mm": 1800.0},
        provenance=("sha256:damaged", "sha256:repaired"),
    )


def _check(
    api: Any,
    status: str,
    *,
    mandatory: bool = True,
    check_id: str = "l1.window.geometry",
) -> Any:
    return api.models.CheckResult(
        check_id=check_id,
        policy_id="ifc-repair.window/0.2",
        applicability="required" if mandatory else "informational",
        mandatory=mandatory,
        status=api.models.EvaluationStatus(status),
        reason=f"fixture result: {status}",
        evidence=(_evidence(api, f"fact.{check_id}"),),
    )


def _level(
    api: Any,
    level: str,
    status: str = "passed",
    *,
    mandatory: bool = True,
) -> Any:
    check = _check(
        api,
        status,
        mandatory=mandatory,
        check_id=f"{level.lower()}.window.fixture",
    )
    return api.evaluation.aggregate_level(
        level=level,
        checks=(check,),
        reason=f"{level} fixture aggregate",
        evidence=check.evidence,
    )


def _operation(
    api: Any,
    *,
    l1_status: str = "passed",
    l2_status: str = "passed",
    l3_observation_status: str = "passed",
) -> Any:
    l1 = _level(api, "L1", l1_status)
    l2 = _level(api, "L2", l2_status)
    l3_observation = _check(
        api,
        l3_observation_status,
        mandatory=False,
        check_id="l3.window.identity_observation",
    )
    l3 = api.evaluation.make_l3_not_required(
        checks=(l3_observation,),
        reason="L3 authoring identity is outside the v1.1 compatibility target",
        evidence=l3_observation.evidence,
    )
    return api.evaluation.aggregate_operation(
        operation_id="op-window-1",
        operation_type="replace_missing_window",
        mandatory=True,
        policy_id="ifc-repair.window",
        policy_version="0.2",
        levels=(l1, l2, l3),
        reason="operation fixture aggregate",
        evidence=(_evidence(api, "fact.operation"),),
    )


def _repair(
    api: Any,
    *,
    application_status: str = "passed",
    preservation_status: str = "passed",
    l1_status: str = "passed",
    l2_status: str = "passed",
    l3_observation_status: str = "passed",
) -> Any:
    application = _check(
        api,
        application_status,
        check_id="application.completed",
    )
    preservation = _check(
        api,
        preservation_status,
        check_id="preservation.unexpected_changes",
    )
    return api.evaluation.aggregate_repair(
        policy_version="ifc-repair-aggregation/0.2",
        application=application,
        preservation=preservation,
        operations=(
            _operation(
                api,
                l1_status=l1_status,
                l2_status=l2_status,
                l3_observation_status=l3_observation_status,
            ),
        ),
        reason="repair fixture aggregate",
        evidence=(_evidence(api, "fact.run"),),
        diagnostic_artifact_retained=True,
    )


def test_evaluation_status_is_closed_to_exactly_five_values() -> None:
    api = _api()

    assert {status.value for status in api.models.EvaluationStatus} == ALL_STATUSES
    with pytest.raises(ValueError):
        api.models.EvaluationStatus("unknown")


@pytest.mark.parametrize(
    "record_factory",
    [
        lambda api: _evidence(api),
        lambda api: _check(api, "passed"),
        lambda api: _level(api, "L1"),
        lambda api: _operation(api),
        lambda api: _repair(api),
    ],
)
def test_evaluation_domain_records_are_frozen(record_factory: Any) -> None:
    api = _api()
    record = record_factory(api)

    with pytest.raises(FrozenInstanceError):
        record.reason = "mutated"  # type: ignore[misc]


@pytest.mark.parametrize("record_kind", ["check", "level"])
def test_checks_and_levels_require_reason_and_evidence(record_kind: str) -> None:
    api = _api()

    with pytest.raises(api.models.EvaluationContractError) as error:
        if record_kind == "check":
            api.models.CheckResult(
                check_id="l1.window.geometry",
                policy_id="ifc-repair.window/0.2",
                applicability="required",
                mandatory=True,
                status=api.models.EvaluationStatus.PASSED,
                reason="",
                evidence=(),
            )
        else:
            api.models.LevelResult(
                level="L1",
                status=api.models.EvaluationStatus.PASSED,
                reason="",
                evidence=(),
                checks=(_check(api, "passed"),),
            )

    assert error.value.code in {"missing_reason", "missing_evidence"}


@pytest.mark.parametrize("level_name", ["L1", "L2"])
@pytest.mark.parametrize("status", ["failed", "partial", "not_evaluable"])
def test_every_non_passing_mandatory_l1_l2_result_blocks_success_and_publication(
    level_name: str,
    status: str,
) -> None:
    api = _api()
    statuses = {"l1_status": "passed", "l2_status": "passed"}
    statuses[f"{level_name.lower()}_status"] = status

    result = _repair(api, **statuses)

    assert result.complete_repair_success is False
    assert result.successful_artifact_publishable is False
    assert result.diagnostic_artifact_retained is True
    assert result.status is api.models.EvaluationStatus(status)


@pytest.mark.parametrize("status", ["failed", "partial", "not_evaluable"])
def test_application_and_preservation_are_mandatory_run_gates(status: str) -> None:
    api = _api()

    application_failure = _repair(api, application_status=status)
    preservation_failure = _repair(api, preservation_status=status)

    assert application_failure.complete_repair_success is False
    assert application_failure.successful_artifact_publishable is False
    assert preservation_failure.complete_repair_success is False
    assert preservation_failure.successful_artifact_publishable is False


def test_application_and_mandatory_l1_l2_pass_produces_publishable_success() -> None:
    api = _api()

    result = _repair(api)

    assert result.status is api.models.EvaluationStatus.PASSED
    assert result.complete_repair_success is True
    assert result.successful_artifact_publishable is True


def test_not_required_is_allowed_only_for_a_non_mandatory_policy_check() -> None:
    api = _api()
    optional = _check(api, "not_required", mandatory=False)

    level = api.evaluation.aggregate_level(
        level="L2",
        checks=(optional,),
        reason="optional fact has no activating source",
        evidence=optional.evidence,
    )

    assert level.status is api.models.EvaluationStatus.PASSED
    with pytest.raises(api.models.EvaluationContractError) as error:
        _check(api, "not_required", mandatory=True)
    assert error.value.code == "invalid_status_transition"


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (("passed", "passed"), "passed"),
        (("passed", "failed"), "failed"),
        (("partial", "not_evaluable"), "partial"),
        (("not_evaluable", "failed"), "failed"),
    ],
)
def test_status_precedence_is_total_and_deterministic(
    statuses: tuple[str, str],
    expected: str,
) -> None:
    api = _api()
    checks = tuple(_check(api, status) for status in statuses)

    assert api.evaluation.aggregate_status(checks) is api.models.EvaluationStatus(
        expected
    )
    assert api.evaluation.aggregate_status(reversed(checks)) is api.models.EvaluationStatus(
        expected
    )


@pytest.mark.parametrize("observation_status", sorted(ALL_STATUSES - {"not_required"}))
def test_l3_observations_never_change_success(observation_status: str) -> None:
    api = _api()

    result = _repair(api, l3_observation_status=observation_status)

    l3 = result.operations[0].level("L3")
    assert l3.status is api.models.EvaluationStatus.NOT_REQUIRED
    assert result.complete_repair_success is True
    assert result.successful_artifact_publishable is True


def test_report_has_deterministic_hierarchy_and_validates_exact_schema() -> None:
    api = _api()
    report = api.evaluation.evaluation_to_dict(_repair(api))

    api.evaluation.validate_evaluation_report(report)

    assert report["schema_version"] == SCHEMA_VERSION
    assert list(report) == [
        "schema_version",
        "policy_version",
        "status",
        "reason",
        "evidence",
        "application",
        "preservation",
        "operations",
        "complete_repair_success",
        "successful_artifact_publishable",
        "diagnostic_artifact_retained",
    ]
    assert [level["level"] for level in report["operations"][0]["levels"]] == [
        "L1",
        "L2",
        "L3",
    ]
    assert report["operations"][0]["levels"][0]["checks"][0]["evidence"]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda report: report.update(status="unknown"), "invalid_schema"),
        (lambda report: report.pop("operations"), "invalid_schema"),
        (lambda report: report["application"].update(reason=""), "invalid_schema"),
        (lambda report: report["application"].update(evidence=[]), "missing_evidence"),
    ],
)
def test_schema_rejects_invalid_status_and_broken_required_hierarchy(
    mutation: Any,
    expected_code: str,
) -> None:
    api = _api()
    report = api.evaluation.evaluation_to_dict(_repair(api))
    mutation(report)

    with pytest.raises(api.models.EvaluationContractError) as error:
        api.evaluation.validate_evaluation_report(report)

    assert error.value.code == expected_code


def test_canonical_serialization_round_trips_in_deterministic_order() -> None:
    api = _api()
    evaluation = _repair(api)

    first = api.evaluation.evaluation_to_json(evaluation)
    round_tripped = api.evaluation.evaluation_from_dict(json.loads(first))
    second = api.evaluation.evaluation_to_json(round_tripped)

    assert round_tripped == evaluation
    assert second == first
    assert first.index('"L1"') < first.index('"L2"') < first.index('"L3"')


def test_frozen_legacy_0_1_fixture_is_read_without_inferred_l2_assurance(
    tmp_path: Path,
) -> None:
    api = _api()
    legacy = {
        "schema_version": LEGACY_SCHEMA_VERSION,
        "complete_repair_success": True,
        "application_postconditions_valid": True,
        "tolerances": {"linear_mm": 0.1},
        "common": {"complete_preservation_success": True},
        "operations": [{"operation_id": "op-window-1", "valid": True}],
    }
    fixture_path = tmp_path / "evaluation-0.1.json"
    fixture_path.write_text(
        json.dumps(legacy, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    projection = api.evaluation.read_evaluation_report(fixture_path)

    assert projection.schema_version == LEGACY_SCHEMA_VERSION
    assert projection.original_report == legacy
    assert projection.l1_assurance is api.models.EvaluationStatus.NOT_EVALUABLE
    assert projection.l2_assurance is api.models.EvaluationStatus.NOT_EVALUABLE
    assert projection.complete_repair_success is False
    assert projection.successful_artifact_publishable is False
    assert projection.assurance_error_code == "legacy_assurance_unavailable"
