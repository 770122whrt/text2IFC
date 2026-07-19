"""Production-safe and benchmark-private post-application Evaluation 0.2."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any
import re

import ifcopenshell
import ifcopenshell.util.element

from .evaluation import (
    aggregate_level,
    aggregate_operation,
    aggregate_repair,
    aggregate_status,
    evaluate_independent_l1,
    evaluation_to_dict,
    make_l3_not_required,
)
from .evaluation_models import CheckResult, EvaluationStatus, EvidenceFact, RepairEvaluation
from .evaluation_policy import EvidenceSourceKind, OperationEvaluationPolicy
from .evaluation_projection import project_public_evaluation
from .semantic_facts import (
    SemanticFact,
    _ifc_classification_facts,
    _ifc_material_facts,
    _ifc_relationship_and_attribute_facts,
    evaluate_operation_semantics,
)


BENCHMARK_POLICY_VERSION = "phase8.1"


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

    def __post_init__(self) -> None:
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
    private_mutation_mapping: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "private_mutation_mapping",
            MappingProxyType(
                {str(role): str(global_id) for role, global_id in self.private_mutation_mapping.items()}
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
        "mutation_role_mapping": dict(inputs.private_mutation_mapping),
        "application_role_mapping": _application_role_mapping(
            inputs.production.application_result
        ),
    }
    public = project_public_evaluation(private)
    return BenchmarkEvaluationResult(
        evaluation=evaluation,
        private_report=private,
        public_report=public,
    )


def _evaluate(
    inputs: ProductionEvaluationInputs,
    *,
    private_original_path: Path | None,
    private_mapping: Mapping[str, str],
) -> RepairEvaluation:
    l1 = evaluate_independent_l1(
        damaged_ifc_path=inputs.damaged_ifc_path,
        repaired_ifc_path=inputs.repaired_ifc_path,
        changeset=inputs.changeset,
        application_result=inputs.application_result,
        registry=inputs.registry,
    )
    repaired_model = ifcopenshell.open(str(Path(inputs.repaired_ifc_path)))
    original_model = (
        ifcopenshell.open(str(private_original_path))
        if private_original_path is not None
        else None
    )
    applied_roles = _application_role_mapping(inputs.application_result)
    operations = []
    for operation in inputs.changeset.get("operations", ()):
        operation_id = str(operation["operation_id"])
        operation_type = str(operation["operation_type"])
        policy = inputs.registry.require_evaluation_policy(operation_type)
        expected = list(inputs.expected_facts_by_operation.get(operation_id, ()))
        repaired_facts: tuple[SemanticFact, ...] = ()
        repaired_id = applied_roles.get("window")
        if repaired_id:
            repaired = repaired_model.by_guid(repaired_id)
            repaired_facts = _extract_benchmark_semantic_facts(
                repaired,
                policy=policy,
                source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
                source_ref=repaired_id,
                provenance=(f"application-role:window:{operation_id}",),
            )
        original_id = private_mapping.get("window")
        if original_model is not None and original_id:
            original = original_model.by_guid(original_id)
            expected.extend(
                _extract_benchmark_semantic_facts(
                    original,
                    policy=policy,
                    source_kind=EvidenceSourceKind.PRIVATE_ORIGINAL,
                    source_ref=original_id,
                    provenance=(f"private-mutation-role:window:{operation_id}",),
                )
            )
        l2_checks = inputs.registry.evaluate_semantics(
            operation_type,
            expected_facts=tuple(expected),
            repaired_facts=repaired_facts,
        )
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
    inherited_sets = _get_psets(element, should_inherit=True)
    direct_sets = _get_psets(element, should_inherit=False)
    for set_name, members in inherited_sets.items():
        if not isinstance(members, dict):
            continue
        direct_members = direct_sets.get(set_name, {})
        for property_name, payload in members.items():
            if property_name == "id" or not isinstance(payload, dict) or "value" not in payload:
                continue
            property_class = str(payload.get("class") or "")
            category = "quantity" if property_class.startswith("IfcQuantity") else "pset"
            fact_key = (
                f"{category}:{_fact_key_token(str(set_name))}."
                f"{_fact_key_token(str(property_name))}"
            )
            if fact_key in known:
                continue
            facts.append(
                SemanticFact(
                    fact_key=fact_key,
                    value=payload.get("value"),
                    value_type=str(payload.get("value_type") or property_class or type(payload.get("value")).__name__),
                    unit=(None if payload.get("unit") is None else str(payload.get("unit"))),
                    inherited=not (
                        isinstance(direct_members, dict)
                        and property_name in direct_members
                    ),
                    pset_path=f"{set_name}.{property_name}",
                    entity_source=f"{element.is_a()}:{source_ref}",
                    source_kind=source_kind,
                    source_ref=source_ref,
                    provenance=(*provenance, "ifcopenshell.util.element.get_psets", "normalized-private-evaluator-key"),
                )
            )
            known.add(fact_key)
    return tuple(sorted(facts, key=lambda fact: (fact.fact_key, repr(fact.value))))


def _get_psets(element: Any, *, should_inherit: bool) -> Mapping[str, Any]:
    try:
        return ifcopenshell.util.element.get_psets(
            element,
            psets_only=False,
            qtos_only=False,
            should_inherit=should_inherit,
            verbose=True,
        )
    except Exception:
        return {}


def _fact_key_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._/-]+", "-", value).strip("-") or "unnamed"


def _application_role_mapping(application_result: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(item["role"]): str(item["global_id"])
        for operation in application_result.get("operations", ())
        for kind in ("created", "modified", "removed")
        for item in operation.get("changes", {}).get(kind, ())
        if item.get("role") and item.get("global_id")
    }


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
    "evaluate_benchmark",
    "evaluate_mapped_role_semantics",
    "evaluate_production",
]
