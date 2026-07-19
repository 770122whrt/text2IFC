"""Pure aggregation and canonical serialization for evaluation 0.2."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .evaluation_models import (
    CheckResult,
    EVALUATION_SCHEMA_VERSION,
    EvaluationContractError,
    EvaluationStatus,
    EvidenceFact,
    LEGACY_EVALUATION_SCHEMA_VERSION,
    LegacyEvaluationProjection,
    LevelResult,
    OperationEvaluation,
    RepairEvaluation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-evaluation-0.2.schema.json"
)
_STATUS_PRECEDENCE = {
    EvaluationStatus.PASSED: 0,
    EvaluationStatus.NOT_REQUIRED: 0,
    EvaluationStatus.NOT_EVALUABLE: 1,
    EvaluationStatus.PARTIAL: 2,
    EvaluationStatus.FAILED: 3,
}


def aggregate_status(
    results: Iterable[CheckResult | LevelResult | OperationEvaluation],
) -> EvaluationStatus:
    """Return the total, order-independent status of mandatory children."""

    statuses: list[EvaluationStatus] = []
    for result in results:
        if isinstance(result, CheckResult) and not result.mandatory:
            continue
        if isinstance(result, OperationEvaluation) and not result.mandatory:
            continue
        if result.status is EvaluationStatus.NOT_REQUIRED:
            continue
        statuses.append(result.status)
    if not statuses:
        return EvaluationStatus.PASSED
    return max(statuses, key=_STATUS_PRECEDENCE.__getitem__)


def aggregate_level(
    *,
    level: str,
    checks: Iterable[CheckResult],
    reason: str,
    evidence: Iterable[EvidenceFact],
) -> LevelResult:
    frozen_checks = tuple(checks)
    return LevelResult(
        level=level,
        status=aggregate_status(frozen_checks),
        reason=reason,
        evidence=tuple(evidence),
        checks=frozen_checks,
    )


def make_l3_not_required(
    *,
    checks: Iterable[CheckResult],
    reason: str,
    evidence: Iterable[EvidenceFact],
) -> LevelResult:
    """Construct the disclosed but non-gating v1.1 L3 boundary."""

    return LevelResult(
        level="L3",
        status=EvaluationStatus.NOT_REQUIRED,
        reason=reason,
        evidence=tuple(evidence),
        checks=tuple(checks),
    )


def aggregate_operation(
    *,
    operation_id: str,
    operation_type: str,
    mandatory: bool,
    policy_id: str,
    policy_version: str,
    levels: Iterable[LevelResult],
    reason: str,
    evidence: Iterable[EvidenceFact],
) -> OperationEvaluation:
    frozen_levels = tuple(levels)
    gating_levels = tuple(
        level for level in frozen_levels if level.level in {"L1", "L2"}
    )
    return OperationEvaluation(
        operation_id=operation_id,
        operation_type=operation_type,
        mandatory=mandatory,
        policy_id=policy_id,
        policy_version=policy_version,
        status=aggregate_status(gating_levels),
        reason=reason,
        evidence=tuple(evidence),
        levels=frozen_levels,
    )


def aggregate_repair(
    *,
    policy_version: str,
    application: CheckResult,
    preservation: CheckResult,
    operations: Iterable[OperationEvaluation],
    reason: str,
    evidence: Iterable[EvidenceFact],
    diagnostic_artifact_retained: bool,
) -> RepairEvaluation:
    frozen_operations = tuple(operations)
    status = aggregate_status((application, preservation, *frozen_operations))
    complete = status is EvaluationStatus.PASSED
    return RepairEvaluation(
        schema_version=EVALUATION_SCHEMA_VERSION,
        policy_version=policy_version,
        status=status,
        reason=reason,
        evidence=tuple(evidence),
        application=application,
        preservation=preservation,
        operations=frozen_operations,
        complete_repair_success=complete,
        successful_artifact_publishable=complete,
        diagnostic_artifact_retained=diagnostic_artifact_retained,
    )


def evaluation_to_dict(value: RepairEvaluation) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "policy_version": value.policy_version,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
        "application": _check_to_dict(value.application),
        "preservation": _check_to_dict(value.preservation),
        "operations": [_operation_to_dict(item) for item in value.operations],
        "complete_repair_success": value.complete_repair_success,
        "successful_artifact_publishable": value.successful_artifact_publishable,
        "diagnostic_artifact_retained": value.diagnostic_artifact_retained,
    }


def evaluation_to_json(value: RepairEvaluation) -> str:
    return json.dumps(
        evaluation_to_dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def evaluation_from_dict(value: Mapping[str, Any]) -> RepairEvaluation:
    payload = dict(value)
    validate_evaluation_report(payload, semantic=False)
    application = _check_from_dict(payload["application"])
    preservation = _check_from_dict(payload["preservation"])
    operations = tuple(_operation_from_dict(item) for item in payload["operations"])
    result = aggregate_repair(
        policy_version=str(payload["policy_version"]),
        application=application,
        preservation=preservation,
        operations=operations,
        reason=str(payload["reason"]),
        evidence=tuple(_evidence_from_dict(item) for item in payload["evidence"]),
        diagnostic_artifact_retained=bool(payload["diagnostic_artifact_retained"]),
    )
    if evaluation_to_dict(result) != payload:
        raise EvaluationContractError(
            "invalid_status_transition",
            "serialized aggregate fields do not match their mandatory children",
        )
    return result


def validate_evaluation_report(
    value: Mapping[str, Any], *, semantic: bool = True
) -> None:
    payload = dict(value)
    if _contains_empty_evidence(payload):
        raise EvaluationContractError(
            "missing_evidence", "report contains an empty evidence collection"
        )
    errors = sorted(
        _validator().iter_errors(payload),
        key=lambda error: [str(item) for item in error.absolute_path],
    )
    if errors:
        raise EvaluationContractError("invalid_schema", errors[0].message)
    if semantic:
        evaluation_from_dict(payload)


def read_evaluation_report(
    path: Path | str,
) -> RepairEvaluation | LegacyEvaluationProjection:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version == EVALUATION_SCHEMA_VERSION:
        return evaluation_from_dict(payload)
    if schema_version == LEGACY_EVALUATION_SCHEMA_VERSION:
        return LegacyEvaluationProjection(
            schema_version=LEGACY_EVALUATION_SCHEMA_VERSION,
            original_report=payload,
            l1_assurance=EvaluationStatus.NOT_EVALUABLE,
            l2_assurance=EvaluationStatus.NOT_EVALUABLE,
            complete_repair_success=False,
            successful_artifact_publishable=False,
            assurance_error_code="legacy_assurance_unavailable",
        )
    raise EvaluationContractError(
        "invalid_schema", f"unsupported evaluation schema: {schema_version!r}"
    )


def _validator() -> Draft202012Validator:
    schema = json.loads(EVALUATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _contains_empty_evidence(value: Any) -> bool:
    if isinstance(value, Mapping):
        if "evidence" in value and value["evidence"] == []:
            return True
        return any(_contains_empty_evidence(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_empty_evidence(child) for child in value)
    return False


def _evidence_to_dict(value: EvidenceFact) -> dict[str, Any]:
    return {
        "fact_id": value.fact_id,
        "source_kind": value.source_kind,
        "source_ref": value.source_ref,
        "expected_state": value.expected_state,
        "actual_state": value.actual_state,
        "expected_value": _json_safe_copy(value.expected_value),
        "actual_value": _json_safe_copy(value.actual_value),
        "provenance": list(value.provenance),
    }


def _check_to_dict(value: CheckResult) -> dict[str, Any]:
    return {
        "check_id": value.check_id,
        "policy_id": value.policy_id,
        "applicability": value.applicability,
        "mandatory": value.mandatory,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
    }


def _level_to_dict(value: LevelResult) -> dict[str, Any]:
    return {
        "level": value.level,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
        "checks": [_check_to_dict(item) for item in value.checks],
    }


def _operation_to_dict(value: OperationEvaluation) -> dict[str, Any]:
    return {
        "operation_id": value.operation_id,
        "operation_type": value.operation_type,
        "mandatory": value.mandatory,
        "policy_id": value.policy_id,
        "policy_version": value.policy_version,
        "status": value.status.value,
        "reason": value.reason,
        "evidence": [_evidence_to_dict(item) for item in value.evidence],
        "levels": [_level_to_dict(item) for item in value.levels],
    }


def _evidence_from_dict(value: Mapping[str, Any]) -> EvidenceFact:
    return EvidenceFact(
        fact_id=str(value["fact_id"]),
        source_kind=str(value["source_kind"]),
        source_ref=str(value["source_ref"]),
        expected_state=str(value["expected_state"]),
        actual_state=str(value["actual_state"]),
        expected_value=value["expected_value"],
        actual_value=value["actual_value"],
        provenance=tuple(str(item) for item in value["provenance"]),
    )


def _check_from_dict(value: Mapping[str, Any]) -> CheckResult:
    return CheckResult(
        check_id=str(value["check_id"]),
        policy_id=str(value["policy_id"]),
        applicability=str(value["applicability"]),
        mandatory=bool(value["mandatory"]),
        status=EvaluationStatus(str(value["status"])),
        reason=str(value["reason"]),
        evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
    )


def _level_from_dict(value: Mapping[str, Any]) -> LevelResult:
    checks = tuple(_check_from_dict(item) for item in value["checks"])
    if value["level"] == "L3":
        result = make_l3_not_required(
            checks=checks,
            reason=str(value["reason"]),
            evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
        )
    else:
        result = aggregate_level(
            level=str(value["level"]),
            checks=checks,
            reason=str(value["reason"]),
            evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
        )
    _require_aggregate_match(result.status, value["status"], scope="level")
    return result


def _operation_from_dict(value: Mapping[str, Any]) -> OperationEvaluation:
    result = aggregate_operation(
        operation_id=str(value["operation_id"]),
        operation_type=str(value["operation_type"]),
        mandatory=bool(value["mandatory"]),
        policy_id=str(value["policy_id"]),
        policy_version=str(value["policy_version"]),
        levels=tuple(_level_from_dict(item) for item in value["levels"]),
        reason=str(value["reason"]),
        evidence=tuple(_evidence_from_dict(item) for item in value["evidence"]),
    )
    _require_aggregate_match(result.status, value["status"], scope="operation")
    return result


def _require_aggregate_match(
    actual: EvaluationStatus, serialized: Any, *, scope: str
) -> None:
    if actual.value != serialized:
        raise EvaluationContractError(
            "invalid_status_transition",
            f"{scope} status does not match its mandatory children",
        )


def _json_safe_copy(value: Any) -> Any:
    """Detach arbitrary evidence values while retaining canonical JSON types."""

    return json.loads(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )


__all__ = [
    "aggregate_level",
    "aggregate_operation",
    "aggregate_repair",
    "aggregate_status",
    "evaluation_from_dict",
    "evaluation_to_dict",
    "evaluation_to_json",
    "make_l3_not_required",
    "read_evaluation_report",
    "validate_evaluation_report",
]
