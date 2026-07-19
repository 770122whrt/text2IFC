"""Pure aggregation and canonical serialization for evaluation 0.2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import ifcopenshell
from jsonschema import Draft202012Validator

from .compare import normalized_model_diff

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

_COMMON_L1_POLICY_ID = "l1.common"
_L1_EVIDENCE_VALUE_MAX_BYTES = 4096
COMMON_L1_CHECK_IDS = (
    "l1.output.readable",
    "l1.output.schema",
    "l1.source.immutable",
    "l1.scope.created-roots",
    "l1.scope.modified-roots",
    "l1.scope.removed-roots",
    "l1.scope.relations",
)
_SCOPE_L1_CHECK_IDS = COMMON_L1_CHECK_IDS[3:]


def evaluate_independent_l1(
    *,
    damaged_ifc_path: Path | str,
    repaired_ifc_path: Path | str,
    changeset: Mapping[str, Any],
    application_result: Mapping[str, Any],
    registry: Any,
) -> LevelResult:
    """Evaluate actual reopened IFC effects against policy and declared intent."""

    damaged_path = Path(damaged_ifc_path)
    repaired_path = Path(repaired_ifc_path)
    source_hash_before = _path_sha256(damaged_path)
    before_model, before_error = _open_ifc(damaged_path)
    after_model, after_error = _open_ifc(repaired_path)
    readable = before_model is not None and after_model is not None
    readability_status = (
        EvaluationStatus.PASSED if readable else EvaluationStatus.NOT_EVALUABLE
    )
    checks = [
        _l1_check(
            check_id="l1.output.readable",
            policy_id=_COMMON_L1_POLICY_ID,
            status=readability_status,
            reason="Both source and repaired IFC artifacts must reopen independently.",
            expected={"before_readable": True, "after_readable": True},
            actual={
                "before_readable": before_model is not None,
                "after_readable": after_model is not None,
                "before_error": before_error,
                "after_error": after_error,
            },
            source_kind="ifc_reopen",
            source_ref="repaired-ifc",
        )
    ]
    checks.append(_source_immutability_check(damaged_path, changeset, source_hash_before))
    if not readable:
        checks.append(
            _l1_check(
                check_id="l1.output.schema",
                policy_id=_COMMON_L1_POLICY_ID,
                status=EvaluationStatus.NOT_EVALUABLE,
                reason="Schema cannot be measured until both IFC artifacts reopen.",
                expected="matching IFC schema",
                actual="unavailable",
                source_kind="ifc_reopen",
                source_ref="repaired-ifc",
            )
        )
        return _l1_level(checks, readable=False)

    assert before_model is not None and after_model is not None
    schema_matches = before_model.schema == after_model.schema
    checks.append(
        _l1_check(
            check_id="l1.output.schema",
            policy_id=_COMMON_L1_POLICY_ID,
            status=(
                EvaluationStatus.PASSED
                if schema_matches
                else EvaluationStatus.FAILED
            ),
            reason="The repaired IFC schema must match the source IFC schema.",
            expected=before_model.schema,
            actual=after_model.schema,
            source_kind="ifc_schema",
            source_ref="repaired-ifc",
        )
    )
    if not schema_matches:
        return _l1_level(checks, readable=True)

    actual_changes = normalized_model_diff(before_model, after_model)
    operation_contexts = _operation_l1_contexts(
        before_model=before_model,
        after_model=after_model,
        changeset=changeset,
        application_result=application_result,
        registry=registry,
    )
    checks.extend(
        _scope_checks(
            actual_changes=actual_changes,
            changeset=changeset,
            operation_contexts=operation_contexts,
            before_model=before_model,
            after_model=after_model,
        )
    )
    for context in operation_contexts:
        checks.extend(_operation_measurement_checks(context))
    return _l1_level(checks, readable=True)


def _open_ifc(path: Path) -> tuple[Any | None, str | None]:
    try:
        return ifcopenshell.open(str(path)), None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def _path_sha256(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _source_immutability_check(
    damaged_path: Path,
    changeset: Mapping[str, Any],
    source_hash_before: str | None,
) -> CheckResult:
    source_hash_after = _path_sha256(damaged_path)
    expected = str(changeset.get("base_model_fingerprint", ""))
    passed = bool(expected) and source_hash_before == expected == source_hash_after
    return _l1_check(
        check_id="l1.source.immutable",
        policy_id=_COMMON_L1_POLICY_ID,
        status=EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED,
        reason="The source IFC must remain bound to the declared base fingerprint.",
        expected=expected,
        actual={"before": source_hash_before, "after": source_hash_after},
        source_kind="source_fingerprint",
        source_ref=str(damaged_path),
    )


def _operation_l1_contexts(
    *,
    before_model: Any,
    after_model: Any,
    changeset: Mapping[str, Any],
    application_result: Mapping[str, Any],
    registry: Any,
) -> list[dict[str, Any]]:
    applications = {
        str(item.get("operation_id")): item
        for item in application_result.get("operations", ())
    }
    contexts = []
    for operation in changeset.get("operations", ()):
        application = applications.get(str(operation.get("operation_id")), {})
        changes = application.get("changes", {})
        report = registry.dispatch(
            "comparison_adapter",
            operation,
            before_model=before_model,
            after_model=after_model,
            application=changes,
        )
        role_ids: dict[str, str] = {}
        id_roles: dict[str, list[str]] = {}
        for change_kind in ("created", "modified", "removed"):
            for item in changes.get(change_kind, ()):
                role = str(item.get("role", ""))
                global_id = str(item.get("global_id", ""))
                if role and global_id:
                    role_ids[role] = global_id
                    id_roles.setdefault(global_id, []).append(role)
        target_ids = {
            str(value)
            for key, value in operation.get("target", {}).items()
            if key.endswith("global_id") and value
        }
        contexts.append(
            {
                "operation": operation,
                "report": report,
                "authorization": report.get("authorization", {}),
                "role_ids": role_ids,
                "id_roles": id_roles,
                "target_ids": target_ids,
            }
        )
    return contexts


def _scope_checks(
    *,
    actual_changes: Mapping[str, list[dict[str, Any]]],
    changeset: Mapping[str, Any],
    operation_contexts: list[dict[str, Any]],
    before_model: Any,
    after_model: Any,
) -> list[CheckResult]:
    decisions: dict[tuple[str, str], tuple[bool, str]] = {}
    for change_kind in ("created", "modified", "removed"):
        for fact in actual_changes[change_kind]:
            decisions[(change_kind, fact["global_id"])] = _authorize_actual_change(
                fact=fact,
                changeset=changeset,
                operation_contexts=operation_contexts,
                before_model=before_model,
                after_model=after_model,
            )

    root_groups = {
        _SCOPE_L1_CHECK_IDS[0]: [
            item for item in actual_changes["created"] if not item["is_relationship"]
        ],
        _SCOPE_L1_CHECK_IDS[1]: [
            item for item in actual_changes["modified"] if not item["is_relationship"]
        ],
        _SCOPE_L1_CHECK_IDS[2]: [
            item for item in actual_changes["removed"] if not item["is_relationship"]
        ],
        _SCOPE_L1_CHECK_IDS[3]: [
            item
            for kind in ("created", "modified", "removed")
            for item in actual_changes[kind]
            if item["is_relationship"]
        ],
    }
    checks = []
    for check_id, facts in root_groups.items():
        evidence = _actual_change_evidence(check_id, facts, decisions)
        unauthorized = [
            fact
            for fact in facts
            if not decisions[(fact["change_kind"], fact["global_id"])][0]
        ]
        checks.append(
            _required_check(
                check_id=check_id,
                policy_id=_COMMON_L1_POLICY_ID,
                status=(
                    EvaluationStatus.FAILED
                    if unauthorized
                    else EvaluationStatus.PASSED
                ),
                reason="Every actual IFC effect must be authorized by policy and declared scope.",
                evidence=evidence,
            )
        )
    return checks


def _authorize_actual_change(
    *,
    fact: Mapping[str, Any],
    changeset: Mapping[str, Any],
    operation_contexts: list[dict[str, Any]],
    before_model: Any,
    after_model: Any,
) -> tuple[bool, str]:
    global_id = str(fact["global_id"])
    if global_id in {str(item) for item in changeset.get("scope", {}).get("forbidden_ids", ())}:
        return False, "actual effect touches a forbidden GlobalId"
    candidates = [
        context for context in operation_contexts if global_id in context["id_roles"]
    ]
    if len(candidates) != 1:
        return False, "actual effect has no unique Applicator role binding"
    context = candidates[0]
    declared_targets = {
        str(item) for item in changeset.get("scope", {}).get("target_ids", ())
    }
    if not context["target_ids"] or not context["target_ids"].issubset(declared_targets):
        return False, "operation target is outside the ChangeSet declared scope"
    roles = sorted(set(context["id_roles"][global_id]))
    if len(roles) != 1:
        return False, "Applicator assigned multiple roles to one actual effect"
    role = roles[0]
    allowed = context["authorization"].get(str(fact["change_kind"]), {})
    if allowed.get(role) != fact["ifc_class"]:
        return False, "Registry policy does not authorize this role/class/effect"
    if fact["is_relationship"]:
        return _authorize_relation(
            fact=fact,
            role=role,
            context=context,
            before_model=before_model,
            after_model=after_model,
        )
    return True, "authorized by Registry policy and ChangeSet operation scope"


def _authorize_relation(
    *,
    fact: Mapping[str, Any],
    role: str,
    context: Mapping[str, Any],
    before_model: Any,
    after_model: Any,
) -> tuple[bool, str]:
    specification = context["authorization"].get("relations", {}).get(role)
    if not specification or specification.get("ifc_class") != fact["ifc_class"]:
        return False, "Registry policy does not authorize the relationship role"
    model = before_model if fact["change_kind"] == "removed" else after_model
    try:
        relation = model.by_guid(str(fact["global_id"]))
    except RuntimeError:
        return False, "actual relationship cannot be reopened by GlobalId"
    for attribute, endpoint_role in specification.get("endpoints", {}).items():
        endpoint = getattr(relation, attribute, None)
        actual_id = str(getattr(endpoint, "GlobalId", ""))
        expected_id = (
            next(iter(context["target_ids"]), "")
            if endpoint_role == "target"
            else context["role_ids"].get(endpoint_role, "")
        )
        if not expected_id or actual_id != expected_id:
            return False, f"relationship endpoint {attribute} is outside declared roles"
    added_roles = tuple(specification.get("added_endpoint_roles", ()))
    if added_roles:
        expected_added = {context["role_ids"].get(role_name, "") for role_name in added_roles}
        expected_added.discard("")
        after_ids = _direct_root_ids(relation)
        if fact["change_kind"] == "modified":
            before_relation = before_model.by_guid(str(fact["global_id"]))
            actual_added = after_ids - _direct_root_ids(before_relation)
            if actual_added != expected_added:
                return False, "relationship endpoint delta exceeds declared generated roles"
        elif not expected_added.issubset(after_ids):
            return False, "created relationship omits a declared generated role"
    return True, "authorized relationship role and endpoints"


def _direct_root_ids(entity: Any) -> set[str]:
    identifiers: set[str] = set()
    for index in range(len(entity)):
        value = entity[index]
        children = value if isinstance(value, (tuple, list)) else (value,)
        for child in children:
            global_id = getattr(child, "GlobalId", None)
            if global_id:
                identifiers.add(str(global_id))
    return identifiers


def _actual_change_evidence(
    check_id: str,
    facts: list[dict[str, Any]],
    decisions: Mapping[tuple[str, str], tuple[bool, str]],
) -> tuple[EvidenceFact, ...]:
    if not facts:
        return (
            _evidence(
                fact_id=f"{check_id}.evidence",
                source_kind="ifc_actual_diff",
                source_ref="reopened-ifc",
                expected="no unexplained effects",
                actual={"changes": []},
            ),
        )
    return tuple(
        _evidence(
            fact_id=f"{check_id}.{index:04d}",
            source_kind="ifc_actual_diff",
            source_ref=f"ifc-guid:{fact['global_id']}",
            expected="policy-and-scope-authorized effect",
            actual={
                **_compact_actual_change(fact),
                "authorized": decisions[(fact["change_kind"], fact["global_id"])][0],
                "authorization_reason": decisions[(fact["change_kind"], fact["global_id"])][1],
            },
        )
        for index, fact in enumerate(facts)
    )


def _compact_actual_change(fact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "change_kind": fact["change_kind"],
        "global_id": fact["global_id"],
        "ifc_class": fact["ifc_class"],
        "is_relationship": fact["is_relationship"],
        "before": _compact_snapshot(fact.get("before")),
        "after": _compact_snapshot(fact.get("after")),
    }


def _compact_snapshot(snapshot: Any) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    canonical = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    attributes = snapshot.get("attributes", {})
    attribute_bytes = json.dumps(
        attributes,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "ifc_class": snapshot.get("ifc_class"),
        "name": snapshot.get("name"),
        "placement": snapshot.get("placement"),
        "containers": snapshot.get("containers"),
        "types": snapshot.get("types"),
        "geometry": snapshot.get("geometry"),
        "attribute_sha256": "sha256:" + hashlib.sha256(attribute_bytes).hexdigest(),
        "snapshot_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def _operation_measurement_checks(context: Mapping[str, Any]) -> list[CheckResult]:
    authorization = context["authorization"]
    policy_id = str(authorization.get("policy_id", "l1.operation"))
    operation_id = str(context["operation"].get("operation_id", "operation"))
    checks = []
    for check_id, measurement in sorted(context["report"].get("l1_checks", {}).items()):
        checks.append(
            _l1_check(
                check_id=str(check_id),
                policy_id=policy_id,
                status=EvaluationStatus(str(measurement["status"])),
                reason=str(measurement["reason"]),
                expected=measurement.get("expected"),
                actual=measurement.get("actual"),
                source_kind="operation_measurement",
                source_ref=f"operation:{operation_id}",
            )
        )
    return checks


def _l1_check(
    *,
    check_id: str,
    policy_id: str,
    status: EvaluationStatus,
    reason: str,
    expected: Any,
    actual: Any,
    source_kind: str,
    source_ref: str,
) -> CheckResult:
    return _required_check(
        check_id=check_id,
        policy_id=policy_id,
        status=status,
        reason=reason,
        evidence=(
            _evidence(
                fact_id=f"{check_id}.evidence",
                source_kind=source_kind,
                source_ref=source_ref,
                expected=expected,
                actual=actual,
            ),
        ),
    )


def _required_check(
    *,
    check_id: str,
    policy_id: str,
    status: EvaluationStatus,
    reason: str,
    evidence: tuple[EvidenceFact, ...],
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        policy_id=policy_id,
        applicability="required",
        mandatory=True,
        status=status,
        reason=reason,
        evidence=evidence,
    )


def _evidence(
    *,
    fact_id: str,
    source_kind: str,
    source_ref: str,
    expected: Any,
    actual: Any,
) -> EvidenceFact:
    evidence_size = len(
        json.dumps(
            {"expected": expected, "actual": actual},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )
    if evidence_size > _L1_EVIDENCE_VALUE_MAX_BYTES:
        raise EvaluationContractError(
            "invalid_schema",
            f"L1 evidence {fact_id} exceeds {_L1_EVIDENCE_VALUE_MAX_BYTES} bytes",
        )
    return EvidenceFact(
        fact_id=fact_id,
        source_kind=source_kind,
        source_ref=source_ref,
        expected_state="available",
        actual_state="available",
        expected_value=expected,
        actual_value=actual,
        provenance=(source_kind, source_ref),
    )


def _l1_level(checks: Iterable[CheckResult], *, readable: bool) -> LevelResult:
    ordered = tuple(sorted(checks, key=lambda item: item.check_id))
    if len({check.check_id for check in ordered}) != len(ordered):
        raise EvaluationContractError("invalid_schema", "duplicate L1 check identifier")
    return aggregate_level(
        level="L1",
        checks=ordered,
        reason="Independent reopened IFC L1 authorization and measurement.",
        evidence=(
            _evidence(
                fact_id="l1.summary",
                source_kind="ifc_actual_diff",
                source_ref="reopened-ifc",
                expected="readable policy-authorized physical repair",
                actual={"readable": readable, "check_count": len(ordered)},
            ),
        ),
    )


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
    for gate_name, gate in (("application", application), ("preservation", preservation)):
        if not gate.mandatory or gate.applicability != "required":
            raise EvaluationContractError(
                "invalid_status_transition",
                f"{gate_name} must be a mandatory required check",
            )
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
    _validate_mandatory_invariants(payload)
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


def _validate_mandatory_invariants(payload: Mapping[str, Any]) -> None:
    gates = (payload.get("application"), payload.get("preservation"))
    for gate in gates:
        if isinstance(gate, Mapping) and (
            gate.get("applicability") != "required" or gate.get("mandatory") is not True
        ):
            raise EvaluationContractError(
                "invalid_status_transition",
                "application and preservation must be mandatory required checks",
            )
    checks = [gate for gate in gates if isinstance(gate, Mapping)]
    for operation in payload.get("operations", ()):
        if not isinstance(operation, Mapping):
            continue
        for level in operation.get("levels", ()):
            if isinstance(level, Mapping):
                checks.extend(
                    check
                    for check in level.get("checks", ())
                    if isinstance(check, Mapping)
                )
    for check in checks:
        applicability = check.get("applicability")
        mandatory = check.get("mandatory")
        status = check.get("status")
        valid = (
            (applicability == "required" and mandatory is True)
            or (applicability == "informational" and mandatory is False)
            or (
                applicability == "conditional"
                and mandatory is (status != EvaluationStatus.NOT_REQUIRED.value)
            )
        )
        if not valid:
            raise EvaluationContractError(
                "invalid_status_transition",
                "check mandatory state does not match applicability and status",
            )


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

    if isinstance(value, Mapping):
        return {str(key): _json_safe_copy(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_safe_copy(child) for child in value]
    return value


__all__ = [
    "COMMON_L1_CHECK_IDS",
    "aggregate_level",
    "aggregate_operation",
    "aggregate_repair",
    "aggregate_status",
    "evaluation_from_dict",
    "evaluate_independent_l1",
    "evaluation_to_dict",
    "evaluation_to_json",
    "make_l3_not_required",
    "read_evaluation_report",
    "validate_evaluation_report",
]
