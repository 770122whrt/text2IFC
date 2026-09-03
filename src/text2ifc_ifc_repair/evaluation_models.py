"""Immutable domain records for IFC repair evaluation 0.2."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import re
from types import MappingProxyType
from typing import Any, Mapping


EVALUATION_SCHEMA_VERSION = "text2ifc/ifc-repair-evaluation/0.2"
LEGACY_EVALUATION_SCHEMA_VERSION = "text2ifc/ifc-repair-evaluation/0.1"
_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")


class EvaluationStatus(str, Enum):
    """Closed outcome algebra used by every evaluation level and check."""

    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_REQUIRED = "not_required"
    NOT_EVALUABLE = "not_evaluable"


class EvaluationContractError(ValueError):
    """Stable machine-readable failure raised for invalid evaluation data."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _require_text(value: str, *, field_name: str) -> None:
    if not value or not value.strip():
        code = "missing_reason" if field_name == "reason" else "invalid_schema"
        raise EvaluationContractError(code, f"{field_name} must be non-empty")


def _require_stable_id(value: str, *, field_name: str) -> None:
    if not _STABLE_ID.fullmatch(value):
        raise EvaluationContractError(
            "invalid_schema", f"{field_name} is not a stable identifier"
        )


def _require_status(value: Any) -> None:
    if not isinstance(value, EvaluationStatus):
        raise EvaluationContractError(
            "invalid_schema", f"unknown evaluation status: {value!r}"
        )


def _require_evidence(evidence: tuple[EvidenceFact, ...]) -> None:
    if not evidence:
        raise EvaluationContractError(
            "missing_evidence", "evaluation results must retain evidence"
        )


def _deep_freeze_json(value: Any) -> Any:
    """Detach JSON evidence and make every nested container immutable."""

    def thaw(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(key): thaw(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [thaw(child) for child in item]
        return item

    detached = json.loads(
        json.dumps(
            thaw(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )

    def freeze(item: Any) -> Any:
        if isinstance(item, dict):
            return MappingProxyType({key: freeze(child) for key, child in item.items()})
        if isinstance(item, list):
            return tuple(freeze(child) for child in item)
        return item

    return freeze(detached)


@dataclass(frozen=True)
class EvidenceFact:
    fact_id: str
    source_kind: str
    source_ref: str
    expected_state: str
    actual_state: str
    expected_value: Any
    actual_value: Any
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_stable_id(self.fact_id, field_name="fact_id")
        _require_stable_id(self.source_kind, field_name="source_kind")
        _require_text(self.source_ref, field_name="source_ref")
        if self.expected_state not in {"available", "unavailable", "not_applicable"}:
            raise EvaluationContractError(
                "invalid_schema", f"invalid expected_state: {self.expected_state}"
            )
        if self.actual_state not in {"available", "unavailable", "not_applicable"}:
            raise EvaluationContractError(
                "invalid_schema", f"invalid actual_state: {self.actual_state}"
            )
        if not self.provenance or any(
            not isinstance(item, str) or not item.strip() for item in self.provenance
        ):
            raise EvaluationContractError(
                "missing_evidence", "evidence provenance must be non-empty"
            )
        try:
            object.__setattr__(self, "expected_value", _deep_freeze_json(self.expected_value))
            object.__setattr__(self, "actual_value", _deep_freeze_json(self.actual_value))
        except (TypeError, ValueError) as error:
            raise EvaluationContractError(
                "invalid_schema", "evidence values must be canonical JSON"
            ) from error


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    policy_id: str
    applicability: str
    mandatory: bool
    status: EvaluationStatus
    reason: str
    evidence: tuple[EvidenceFact, ...]

    def __post_init__(self) -> None:
        _require_stable_id(self.check_id, field_name="check_id")
        _require_stable_id(self.policy_id, field_name="policy_id")
        _require_status(self.status)
        _require_text(self.reason, field_name="reason")
        _require_evidence(self.evidence)
        if self.applicability not in {
            "required",
            "conditional",
            "informational",
        }:
            raise EvaluationContractError(
                "invalid_schema", f"invalid applicability: {self.applicability}"
            )
        invalid_mandatory = (
            (self.mandatory and self.status is EvaluationStatus.NOT_REQUIRED)
            or
            (self.applicability == "required" and not self.mandatory)
            or (self.applicability == "informational" and self.mandatory)
            or (
                self.applicability == "conditional"
                and self.mandatory != (self.status is not EvaluationStatus.NOT_REQUIRED)
            )
        )
        if invalid_mandatory:
            raise EvaluationContractError(
                "invalid_status_transition",
                "check mandatory state does not match applicability and status",
            )


@dataclass(frozen=True)
class LevelResult:
    level: str
    status: EvaluationStatus
    reason: str
    evidence: tuple[EvidenceFact, ...]
    checks: tuple[CheckResult, ...]

    def __post_init__(self) -> None:
        _require_status(self.status)
        if self.level not in {"L1", "L2", "L3"}:
            raise EvaluationContractError(
                "invalid_schema", f"invalid evaluation level: {self.level}"
            )
        _require_text(self.reason, field_name="reason")
        _require_evidence(self.evidence)
        if not self.checks:
            raise EvaluationContractError(
                "invalid_schema", "a level must contain at least one check"
            )


@dataclass(frozen=True)
class OperationEvaluation:
    operation_id: str
    operation_type: str
    mandatory: bool
    policy_id: str
    policy_version: str
    status: EvaluationStatus
    reason: str
    evidence: tuple[EvidenceFact, ...]
    levels: tuple[LevelResult, ...]

    def __post_init__(self) -> None:
        for name in (
            "operation_id",
            "operation_type",
            "policy_id",
            "policy_version",
        ):
            _require_stable_id(str(getattr(self, name)), field_name=name)
        _require_status(self.status)
        _require_text(self.reason, field_name="reason")
        _require_evidence(self.evidence)
        if tuple(level.level for level in self.levels) != ("L1", "L2", "L3"):
            raise EvaluationContractError(
                "invalid_schema", "operation levels must be ordered L1, L2, L3"
            )

    def level(self, name: str) -> LevelResult:
        for result in self.levels:
            if result.level == name:
                return result
        raise EvaluationContractError("invalid_schema", f"missing level: {name}")


@dataclass(frozen=True)
class RepairEvaluation:
    schema_version: str
    policy_version: str
    status: EvaluationStatus
    reason: str
    evidence: tuple[EvidenceFact, ...]
    application: CheckResult
    preservation: CheckResult
    operations: tuple[OperationEvaluation, ...]
    complete_repair_success: bool
    successful_artifact_publishable: bool
    diagnostic_artifact_retained: bool

    def __post_init__(self) -> None:
        _require_status(self.status)
        if self.schema_version != EVALUATION_SCHEMA_VERSION:
            raise EvaluationContractError(
                "invalid_schema", f"unsupported schema version: {self.schema_version}"
            )
        _require_stable_id(self.policy_version, field_name="policy_version")
        _require_text(self.reason, field_name="reason")
        _require_evidence(self.evidence)
        if not self.operations:
            raise EvaluationContractError(
                "invalid_schema", "a repair evaluation requires operations"
            )


@dataclass(frozen=True)
class LegacyEvaluationProjection:
    schema_version: str
    original_report: Mapping[str, Any]
    l1_assurance: EvaluationStatus
    l2_assurance: EvaluationStatus
    complete_repair_success: bool
    successful_artifact_publishable: bool
    assurance_error_code: str


__all__ = [
    "CheckResult",
    "EVALUATION_SCHEMA_VERSION",
    "EvaluationContractError",
    "EvaluationStatus",
    "EvidenceFact",
    "LEGACY_EVALUATION_SCHEMA_VERSION",
    "LegacyEvaluationProjection",
    "LevelResult",
    "OperationEvaluation",
    "RepairEvaluation",
]
