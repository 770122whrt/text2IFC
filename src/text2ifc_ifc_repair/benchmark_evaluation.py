"""Production-safe and benchmark-private post-application Evaluation 0.2."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any
import re

import ifcopenshell
import ifcopenshell.util.element

from .evaluation import (
    _open_ifc_pair,
    aggregate_level,
    aggregate_operation,
    aggregate_repair,
    aggregate_status,
    EvaluationExecutionPolicy,
    evaluate_independent_l1,
    evaluation_to_dict,
    make_l3_not_required,
)
from .evaluation_models import CheckResult, EvaluationStatus, EvidenceFact, RepairEvaluation
from .evaluation_policy import (
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SemanticApplicability,
    extend_policy_with_explicit_facts,
)
from .evaluation_projection import project_public_evaluation
from .semantic_facts import (
    SemanticFact,
    _ifc_classification_facts,
    _ifc_material_facts,
    _ifc_relationship_and_attribute_facts,
    evaluate_operation_semantics,
    extract_property_facts,
    semantic_fact_from_property_fact,
)
from .occurrence_fidelity import (
    compare_occurrence_snapshots,
    snapshot_from_semantic_facts,
    snapshot_window_occurrence,
)


BENCHMARK_POLICY_VERSION = "phase8.1"
PRODUCTION_EXPECTED_SOURCE_KINDS = frozenset(
    {
        EvidenceSourceKind.EXPLICIT_REQUEST,
        EvidenceSourceKind.SURVIVING_TARGET,
        EvidenceSourceKind.SURVIVING_HOST,
        EvidenceSourceKind.SURVIVING_TYPE,
        EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
        EvidenceSourceKind.APPROVED_PROTOTYPE,
        EvidenceSourceKind.DETERMINISTIC_POLICY,
    }
)


@dataclass(frozen=True)
class ProductionEvaluationInputs:
    """Public post-application inputs; Ground Truth is structurally impossible."""

    damaged_ifc_path: Path | str
    repaired_ifc_path: Path | str
    changeset: Mapping[str, Any]
    application_result: Mapping[str, Any]
    registry: Any
    expected_facts_by_operation: Mapping[str, tuple[SemanticFact, ...]] = field(
        default_factory=dict
    )
    execution_policy: EvaluationExecutionPolicy = field(
        default_factory=EvaluationExecutionPolicy
    )
    validation_cache_dir: Path | str | None = None

    def __post_init__(self) -> None:
        _validate_production_expected_facts(self.expected_facts_by_operation)
        object.__setattr__(
            self,
            "expected_facts_by_operation",
            MappingProxyType(
                {
                    str(key): tuple(value)
                    for key, value in self.expected_facts_by_operation.items()
                }
            ),
        )


@dataclass(frozen=True)
class BenchmarkEvaluationInputs:
    """Evaluator-only Gold added to an already-completed production application."""

    production: ProductionEvaluationInputs
    private_original_ifc_path: Path | str
    private_mutation_mapping: Mapping[str, Mapping[str, str]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "private_mutation_mapping",
            MappingProxyType(
                {
                    str(operation_id): MappingProxyType(
                        {
                            str(role): str(global_id)
                            for role, global_id in role_mapping.items()
                        }
                    )
                    for operation_id, role_mapping in self.private_mutation_mapping.items()
                }
            ),
        )


@dataclass(frozen=True)
class BenchmarkEvaluationResult:
    evaluation: RepairEvaluation
    private_report: Mapping[str, Any]
    public_report: Mapping[str, Any]


def evaluate_mapped_role_semantics(
    *,
    policy: OperationEvaluationPolicy,
    semantic_role: str,
    private_original_role_mapping: Mapping[str, str],
    application_role_mapping: Mapping[str, str],
    private_original_facts: tuple[SemanticFact, ...],
    repaired_facts: tuple[SemanticFact, ...],
) -> tuple[CheckResult, ...]:
    """Compare facts bound to equal roles, deliberately ignoring GUID equality."""

    original_id = str(private_original_role_mapping.get(semantic_role, ""))
    repaired_id = str(application_role_mapping.get(semantic_role, ""))
    if not original_id or not repaired_id:
        raise ValueError(f"BENCHMARK_ROLE_UNRESOLVED:{semantic_role}")
    if any(
        fact.source_kind is not EvidenceSourceKind.PRIVATE_ORIGINAL
        or fact.source_ref != original_id
        for fact in private_original_facts
    ):
        raise ValueError(f"BENCHMARK_ORIGINAL_ROLE_MISMATCH:{semantic_role}")
    if any(
        fact.source_kind is not EvidenceSourceKind.REPAIRED_OUTPUT
        or fact.source_ref != repaired_id
        for fact in repaired_facts
    ):
        raise ValueError(f"BENCHMARK_REPAIRED_ROLE_MISMATCH:{semantic_role}")
    return evaluate_operation_semantics(
        policy,
        expected_facts=private_original_facts,
        repaired_facts=repaired_facts,
    )


def evaluate_production(inputs: ProductionEvaluationInputs) -> RepairEvaluation:
    """Evaluate only public/authorized expectations after application."""

    _validate_production_expected_facts(inputs.expected_facts_by_operation)
    return _evaluate(inputs, private_original_path=None, private_mapping={})


def evaluate_benchmark(inputs: BenchmarkEvaluationInputs) -> BenchmarkEvaluationResult:
    """Consume original/mutation truth only at the private evaluator boundary."""

    evaluation = _evaluate(
        inputs.production,
        private_original_path=Path(inputs.private_original_ifc_path),
        private_mapping=inputs.private_mutation_mapping,
    )
    private = evaluation_to_dict(evaluation)
    private["benchmark_private"] = {
        "original_ifc_path": Path(inputs.private_original_ifc_path).as_posix(),
        "mutation_role_mapping": {
            operation_id: dict(role_mapping)
            for operation_id, role_mapping in inputs.private_mutation_mapping.items()
        },
        "application_role_mapping": _application_role_mapping(
            inputs.production.application_result
        ),
        "occurrence_fidelity": _benchmark_occurrence_reports(inputs),
    }
    public = project_public_evaluation(private)
    return BenchmarkEvaluationResult(
        evaluation=evaluation,
        private_report=private,
        public_report=public,
    )


def _occurrence_fidelity_check(
    *,
    operation_id: str,
    repaired_model: Any,
    repaired_id: str | None,
    public_expected: tuple[SemanticFact, ...],
    original_model: Any | None,
    original_id: str | None,
    complete_replication: bool,
    extraction_errors: tuple[str, ...],
) -> CheckResult:
    if extraction_errors or repaired_model is None or not repaired_id:
        return CheckResult(
            check_id="l2.window-occurrence-fidelity",
            policy_id="window-occurrence-fidelity.v0.1",
            applicability="required",
            mandatory=True,
            status=EvaluationStatus.NOT_EVALUABLE,
            reason="Occurrence fidelity could not read the mapped repaired Window.",
            evidence=(
                _evidence(
                    "l2.window-occurrence-fidelity",
                    "occurrence_fidelity_error",
                    f"operation:{operation_id}",
                    "readable mapped Window",
                    list(extraction_errors) or "missing repaired Window mapping",
                ),
            ),
        )
    try:
        actual = snapshot_window_occurrence(repaired_model, repaired_id)
        ledger = snapshot_from_semantic_facts(
            public_expected, window_global_id=repaired_id
        )
        authorized = tuple(ledger.facts)
        if complete_replication:
            if original_model is None or not original_id:
                raise ValueError("PRIVATE_WINDOW_MAPPING_REQUIRED")
            expected = snapshot_window_occurrence(original_model, original_id)
            required = _complete_replication_required_fact_keys(expected)
        else:
            expected = ledger
            required = authorized
        report = compare_occurrence_snapshots(
            expected=expected,
            actual=actual,
            authorization_ledger=authorized,
            authorization_ownership={
                key: fact.ownership
                for key, fact in ledger.facts.items()
            },
            required_fact_keys=required,
            complete_replication=complete_replication,
        )
    except Exception as error:
        return CheckResult(
            check_id="l2.window-occurrence-fidelity",
            policy_id="window-occurrence-fidelity.v0.1",
            applicability="required",
            mandatory=True,
            status=EvaluationStatus.NOT_EVALUABLE,
            reason="Occurrence fidelity input or mapping is invalid.",
            evidence=(
                _evidence(
                    "l2.window-occurrence-fidelity",
                    "occurrence_fidelity_error",
                    f"operation:{operation_id}",
                    "valid occurrence comparison",
                    f"{type(error).__name__}:{error}",
                ),
            ),
        )
    passed = bool(report["occurrence_fidelity_success"])
    return CheckResult(
        check_id="l2.window-occurrence-fidelity",
        policy_id="window-occurrence-fidelity.v0.1",
        applicability="required",
        mandatory=True,
        status=EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED,
        reason=(
            "Authorized Window/Opening occurrence facts match."
            if passed
            else "Required Window/Opening occurrence facts are incomplete or wrong."
        ),
        evidence=(
            _evidence(
                "l2.window-occurrence-fidelity",
                "occurrence_fidelity_report",
                f"operation:{operation_id}",
                {
                    "occurrence_fidelity_success": True,
                    "blocking_counts": {
                        "unsupported_authoring": 0,
                        "wrong_value": 0,
                        "not_in_user_text": 0 if complete_replication else "informational",
                    },
                },
                report,
            ),
        ),
    )


def _benchmark_occurrence_reports(
    inputs: BenchmarkEvaluationInputs,
) -> dict[str, Any]:
    if (
        inputs.production.changeset.get("schema_version")
        != "text2ifc/ifc-repair-changeset/0.3"
    ):
        return {}
    original = ifcopenshell.open(str(inputs.private_original_ifc_path))
    repaired = ifcopenshell.open(str(inputs.production.repaired_ifc_path))
    application = _application_role_mapping(
        inputs.production.application_result
    )
    reports: dict[str, Any] = {}
    seen_original: set[str] = set()
    seen_repaired: set[str] = set()
    for operation in inputs.production.changeset.get("operations", ()):
        operation_id = str(operation["operation_id"])
        if operation.get("operation_type") != "add_window_with_opening_to_wall":
            continue
        original_id = str(
            inputs.private_mutation_mapping.get(operation_id, {}).get("window", "")
        )
        repaired_id = str(application.get(operation_id, {}).get("window", ""))
        if not original_id or not repaired_id:
            raise ValueError(f"BENCHMARK_WINDOW_MAPPING_MISSING:{operation_id}")
        if original_id in seen_original or repaired_id in seen_repaired:
            raise ValueError(f"BENCHMARK_WINDOW_MAPPING_DUPLICATE:{operation_id}")
        seen_original.add(original_id)
        seen_repaired.add(repaired_id)
        ledger_snapshot = snapshot_from_semantic_facts(
            inputs.production.expected_facts_by_operation.get(operation_id, ()),
            window_global_id=repaired_id,
        )
        expected = snapshot_window_occurrence(original, original_id)
        reports[operation_id] = compare_occurrence_snapshots(
            expected=expected,
            actual=snapshot_window_occurrence(repaired, repaired_id),
            authorization_ledger=tuple(ledger_snapshot.facts),
            authorization_ownership={
                key: fact.ownership
                for key, fact in ledger_snapshot.facts.items()
            },
            required_fact_keys=_complete_replication_required_fact_keys(expected),
            complete_replication=True,
        )
    return reports


def _complete_replication_required_fact_keys(
    expected: Any,
) -> tuple[str, ...]:
    """Return the Phase 10.5 authorable semantic Ground Truth boundary."""

    required = []
    for key in expected.facts:
        if key.startswith("window_occurrence:pset:"):
            required.append(key)
        elif key.startswith(
            (
                "window_occurrence:quantity:",
                "opening_occurrence:quantity:",
            )
        ):
            required.append(key)
        elif key.endswith(
            (
                ":attribute:OverallWidth",
                ":attribute:OverallHeight",
            )
        ):
            required.append(key)
    return tuple(sorted(required))


def _evaluate(
    inputs: ProductionEvaluationInputs,
    *,
    private_original_path: Path | None,
    private_mapping: Mapping[str, Mapping[str, str]],
) -> RepairEvaluation:
    reopened_models = _open_ifc_pair(
        Path(inputs.damaged_ifc_path),
        Path(inputs.repaired_ifc_path),
        accelerated=inputs.execution_policy.mode == "accelerated",
    )
    l1 = evaluate_independent_l1(
        damaged_ifc_path=inputs.damaged_ifc_path,
        repaired_ifc_path=inputs.repaired_ifc_path,
        changeset=inputs.changeset,
        application_result=inputs.application_result,
        registry=inputs.registry,
        execution_policy=inputs.execution_policy,
        validation_cache_dir=inputs.validation_cache_dir,
        reopened_models=reopened_models,
    )
    repaired_model, repaired_open_error = reopened_models[1]
    original_model, original_open_error = (
        _open_evaluation_model(private_original_path, label="private-original")
        if private_original_path is not None
        else (None, None)
    )
    applied_roles_by_operation = _application_role_mapping(inputs.application_result)
    operations = []
    for operation in inputs.changeset.get("operations", ()):
        operation_id = str(operation["operation_id"])
        operation_type = str(operation["operation_type"])
        definition = inputs.registry.require(operation_type)
        policy = inputs.registry.require_evaluation_policy(operation_type)
        semantic_role = policy.semantic_role
        primary_scope = str(
            definition.semantic_scope_roles.get(
                semantic_role, "window_occurrence"
            )
        )
        public_expected = tuple(
            inputs.expected_facts_by_operation.get(operation_id, ())
        )
        expected = [
            fact
            for fact in public_expected
            if str(
                getattr(fact, "occurrence_scope", "window_occurrence")
            )
            == primary_scope
        ]
        policy = extend_policy_with_explicit_facts(
            policy,
            tuple(
                fact.fact_key
                for fact in expected
                if fact.source_kind is EvidenceSourceKind.EXPLICIT_REQUEST
            ),
            applicability=SemanticApplicability.REQUIRED,
        )
        repaired_facts: tuple[SemanticFact, ...] = ()
        extraction_errors: list[str] = []
        applied_roles = applied_roles_by_operation.get(operation_id, {})
        repaired_id = applied_roles.get(semantic_role)
        if repaired_open_error:
            extraction_errors.append(repaired_open_error)
        elif not repaired_id:
            extraction_errors.append(
                f"APPLICATION_SEMANTIC_ROLE_UNRESOLVED:{operation_id}:{semantic_role}"
            )
        else:
            try:
                repaired = _require_role_entity(
                    repaired_model,
                    repaired_id,
                    operation_id=operation_id,
                    semantic_role=semantic_role,
                    label="repaired",
                )
                repaired_facts = _extract_benchmark_semantic_facts(
                    repaired,
                    policy=policy,
                    occurrence_scope=primary_scope,
                    source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
                    source_ref=repaired_id,
                    provenance=(f"application-role:{semantic_role}:{operation_id}",),
                )
            except Exception as error:
                extraction_errors.append(_evaluator_input_error(error))
        private_roles = private_mapping.get(operation_id, {})
        original_id = private_roles.get(semantic_role)
        if private_original_path is not None:
            if original_open_error:
                extraction_errors.append(original_open_error)
            elif not original_id:
                extraction_errors.append(
                    f"PRIVATE_SEMANTIC_ROLE_UNRESOLVED:{operation_id}:{semantic_role}"
                )
            else:
                try:
                    original = _require_role_entity(
                        original_model,
                        original_id,
                        operation_id=operation_id,
                        semantic_role=semantic_role,
                        label="private-original",
                    )
                    expected.extend(
                        _extract_benchmark_semantic_facts(
                            original,
                            policy=policy,
                            occurrence_scope=primary_scope,
                            source_kind=EvidenceSourceKind.PRIVATE_ORIGINAL,
                            source_ref=original_id,
                            provenance=(
                                f"private-mutation-role:{semantic_role}:{operation_id}",
                            ),
                        )
                    )
                except Exception as error:
                    extraction_errors.append(_evaluator_input_error(error))
        l2_checks = list(
            _not_evaluable_semantic_checks(policy, errors=tuple(extraction_errors))
            if extraction_errors
            else inputs.registry.evaluate_semantics(
                operation_type,
                expected_facts=tuple(expected),
                repaired_facts=repaired_facts,
            )
        )
        if (
            operation_type == "add_window_with_opening_to_wall"
            and inputs.changeset.get("schema_version")
            == "text2ifc/ifc-repair-changeset/0.3"
        ):
            occurrence_check = _occurrence_fidelity_check(
                operation_id=operation_id,
                repaired_model=repaired_model,
                repaired_id=repaired_id,
                public_expected=public_expected,
                original_model=original_model,
                original_id=original_id,
                complete_replication=private_original_path is not None,
                extraction_errors=tuple(extraction_errors),
            )
            l2_checks.append(occurrence_check)
        l2_checks = tuple(l2_checks)
        l2 = aggregate_level(
            level="L2",
            checks=l2_checks,
            reason="Policy-owned semantic facts are compared through authorized evidence.",
            evidence=(
                _evidence(
                    "l2.summary",
                    "semantic_policy",
                    policy.policy_id,
                    "all mandatory L2 checks passed",
                    {"check_count": len(l2_checks)},
                ),
            ),
        )
        same_identity = bool(original_id and repaired_id and original_id == repaired_id)
        l3_check = CheckResult(
            check_id="l3.authoring-identity",
            policy_id="l3.v1.1-observation",
            applicability="informational",
            mandatory=False,
            status=(EvaluationStatus.PASSED if same_identity else EvaluationStatus.FAILED),
            reason="Original identity is observational and never gates v1.1 repair success.",
            evidence=(
                _evidence(
                    "l3.authoring-identity",
                    "identity_observation",
                    f"operation:{operation_id}",
                    original_id,
                    repaired_id,
                ),
            ),
        )
        l3 = make_l3_not_required(
            checks=(l3_check,),
            reason="L3 authoring and identity exactness is not required in v1.1.",
            evidence=(
                _evidence(
                    "l3.summary",
                    "policy_boundary",
                    "v1.1",
                    "not required",
                    "observed",
                ),
            ),
        )
        operations.append(
            aggregate_operation(
                operation_id=operation_id,
                operation_type=operation_type,
                mandatory=True,
                policy_id=policy.policy_id,
                policy_version=policy.version,
                levels=(l1, l2, l3),
                reason="Mandatory L1 and L2 jointly determine operation success.",
                evidence=(
                    _evidence(
                        f"operation.{operation_id}",
                        "operation_policy",
                        policy.policy_id,
                        "L1 and L2 passed",
                        {"l1": l1.status.value, "l2": l2.status.value},
                    ),
                ),
            )
        )
    application_ok = bool(inputs.application_result.get("valid")) and bool(
        inputs.application_result.get("published")
    )
    application = _required_check(
        "application.valid",
        EvaluationStatus.PASSED if application_ok else EvaluationStatus.FAILED,
        "The deterministic application must complete and publish its candidate.",
        {"valid": inputs.application_result.get("valid"), "published": inputs.application_result.get("published")},
    )
    preservation = _required_check(
        "preservation.valid",
        l1.status,
        "Independent L1 evidence must authorize preservation and scope effects.",
        {"l1_status": l1.status.value},
    )
    aggregate = aggregate_status((application, preservation, *operations))
    return aggregate_repair(
        policy_version=BENCHMARK_POLICY_VERSION,
        application=application,
        preservation=preservation,
        operations=operations,
        reason="Application, preservation, and mandatory L1/L2 are strict gates.",
        evidence=(
            _evidence(
                "run.summary",
                "evaluation_policy",
                BENCHMARK_POLICY_VERSION,
                "all mandatory gates passed",
                aggregate.value,
            ),
        ),
        diagnostic_artifact_retained=(
            aggregate is not EvaluationStatus.PASSED
            and Path(inputs.repaired_ifc_path).is_file()
        ),
    )


def _extract_benchmark_semantic_facts(
    element: Any,
    *,
    policy: OperationEvaluationPolicy,
    occurrence_scope: str = "window_occurrence",
    source_kind: EvidenceSourceKind,
    source_ref: str,
    provenance: tuple[str, ...],
) -> tuple[SemanticFact, ...]:
    """Normalize free-form IFC Pset labels at the evaluator boundary."""

    source = {
        "source_kind": source_kind,
        "source_ref": source_ref,
        "entity_source": f"{element.is_a()}:{source_ref}",
        "provenance": provenance,
        "compatible": True,
    }
    facts = list(
        _ifc_relationship_and_attribute_facts(
            element,
            policy=policy,
            **source,
        )
    )
    if any(spec.fact_pattern.startswith("material:") for spec in policy.semantic_facts):
        facts.extend(_ifc_material_facts(element, **source))
    if any(spec.fact_pattern.startswith("classification:") for spec in policy.semantic_facts):
        facts.extend(_ifc_classification_facts(element, **source))
    known = {fact.fact_key for fact in facts}
    for property_fact in extract_property_facts(
        element,
        should_inherit=True,
    ):
        fact = semantic_fact_from_property_fact(
            property_fact,
            source_kind=source_kind,
            source_ref=source_ref,
            entity_source=f"{element.is_a()}:{source_ref}",
            provenance=(
                *provenance,
                "ifcopenshell.util.element.get_psets",
                "normalized-private-evaluator-key",
            ),
        )
        if fact.fact_key in known:
            continue
        facts.append(fact)
        known.add(fact.fact_key)
    scoped = (
        replace(fact, occurrence_scope=occurrence_scope)
        for fact in facts
    )
    return tuple(
        sorted(scoped, key=lambda fact: (fact.fact_key, repr(fact.value)))
    )


def _get_psets(element: Any, *, should_inherit: bool) -> Mapping[str, Any]:
    try:
        return ifcopenshell.util.element.get_psets(
            element,
            psets_only=False,
            qtos_only=False,
            should_inherit=should_inherit,
            verbose=True,
        )
    except Exception as error:
        raise RuntimeError(
            f"IFC_PSET_EXTRACTION_FAILED:{type(error).__name__}:{error}"
        ) from error


def _open_evaluation_model(path: Path, *, label: str) -> tuple[Any | None, str | None]:
    try:
        return ifcopenshell.open(str(path)), None
    except Exception as error:
        return None, f"IFC_MODEL_OPEN_FAILED:{label}:{type(error).__name__}:{error}"


def _require_role_entity(
    model: Any,
    global_id: str,
    *,
    operation_id: str,
    semantic_role: str,
    label: str,
) -> Any:
    try:
        entity = model.by_guid(global_id)
    except Exception as error:
        raise RuntimeError(
            f"IFC_ROLE_ENTITY_UNRESOLVED:{label}:{operation_id}:"
            f"{semantic_role}:{global_id}"
        ) from error
    if entity is None:
        raise RuntimeError(
            f"IFC_ROLE_ENTITY_UNRESOLVED:{label}:{operation_id}:"
            f"{semantic_role}:{global_id}"
        )
    return entity


def _evaluator_input_error(error: Exception) -> str:
    return f"{type(error).__name__}:{error}"


def _not_evaluable_semantic_checks(
    policy: OperationEvaluationPolicy,
    *,
    errors: tuple[str, ...],
) -> tuple[CheckResult, ...]:
    evidence_errors = tuple(sorted(set(errors)))
    return tuple(
        CheckResult(
            check_id=spec.check_id,
            policy_id=policy.policy_id,
            applicability=spec.applicability.value,
            mandatory=spec.applicability is not SemanticApplicability.INFORMATIONAL,
            status=EvaluationStatus.NOT_EVALUABLE,
            reason="Semantic evaluator inputs were unavailable or extraction failed.",
            evidence=(
                EvidenceFact(
                    fact_id=spec.check_id,
                    source_kind="evaluator_input_error",
                    source_ref=f"{policy.policy_id}/{spec.check_id}",
                    expected_state="unavailable",
                    actual_state="unavailable",
                    expected_value="measurable authorized semantic evidence",
                    actual_value={"errors": evidence_errors},
                    provenance=("evaluator-input-validation",),
                ),
            ),
        )
        for spec in policy.semantic_facts
    )


def _fact_key_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._/-]+", "-", value).strip("-") or "unnamed"


def _application_role_mapping(
    application_result: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    mappings: dict[str, dict[str, str]] = {}
    for operation in application_result.get("operations", ()):
        operation_id = str(operation.get("operation_id", ""))
        if not operation_id or operation_id in mappings:
            raise ValueError(f"APPLICATION_OPERATION_ROLE_MAPPING_INVALID:{operation_id}")
        roles: dict[str, str] = {}
        for kind in ("created", "modified", "removed"):
            for item in operation.get("changes", {}).get(kind, ()):
                role = str(item.get("role", ""))
                global_id = str(item.get("global_id", ""))
                if not role or not global_id:
                    continue
                if role in roles:
                    raise ValueError(
                        f"APPLICATION_ROLE_CARDINALITY_INVALID:{operation_id}:{role}"
                    )
                roles[role] = global_id
        mappings[operation_id] = roles
    return {operation_id: mappings[operation_id] for operation_id in sorted(mappings)}


def _validate_production_expected_facts(
    expected_facts_by_operation: Mapping[str, tuple[SemanticFact, ...]],
) -> None:
    for operation_id, facts in expected_facts_by_operation.items():
        for fact in facts:
            if fact.source_kind is EvidenceSourceKind.PRIVATE_ORIGINAL:
                raise ValueError(
                    f"PRODUCTION_PRIVATE_ORIGINAL_FORBIDDEN:{operation_id}:{fact.fact_key}"
                )
            if fact.source_kind not in PRODUCTION_EXPECTED_SOURCE_KINDS:
                raise ValueError(
                    f"PRODUCTION_EVIDENCE_SOURCE_FORBIDDEN:{operation_id}:"
                    f"{fact.source_kind.value}"
                )


def _required_check(
    check_id: str,
    status: EvaluationStatus,
    reason: str,
    actual: Any,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        policy_id="evaluation.phase8",
        applicability="required",
        mandatory=True,
        status=status,
        reason=reason,
        evidence=(
            _evidence(
                f"{check_id}.evidence",
                "application_result",
                check_id,
                "passed",
                actual,
            ),
        ),
    )


def _evidence(
    fact_id: str,
    source_kind: str,
    source_ref: str,
    expected: Any,
    actual: Any,
) -> EvidenceFact:
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


__all__ = [
    "BENCHMARK_POLICY_VERSION",
    "BenchmarkEvaluationInputs",
    "BenchmarkEvaluationResult",
    "ProductionEvaluationInputs",
    "PRODUCTION_EXPECTED_SOURCE_KINDS",
    "evaluate_benchmark",
    "evaluate_mapped_role_semantics",
    "evaluate_production",
]
