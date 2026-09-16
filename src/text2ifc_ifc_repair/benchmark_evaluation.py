"""Private benchmark comparison layered on the public production gate.

Legacy production imports are re-exported here for compatibility. New public
callers import production_evaluation directly; private Gold is evaluator-only
and cannot promote a failed production result.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any

import ifcopenshell

from .evaluation import evaluation_to_dict
from .evaluation_models import CheckResult, RepairEvaluation
from .evaluation_policy import EvidenceSourceKind, OperationEvaluationPolicy
from .evaluation_projection import project_public_evaluation
from .occurrence_fidelity import (
    compare_occurrence_snapshots,
    snapshot_from_semantic_facts,
    snapshot_window_occurrence,
)
from .semantic_facts import SemanticFact, evaluate_operation_semantics
from .production_evaluation import (
    EVALUATION_POLICY_VERSION,
    PRODUCTION_EXPECTED_SOURCE_KINDS,
    ProductionEvaluationInputs,
    evaluate_production,
    _occurrence_fidelity_check,
    _complete_replication_required_fact_keys,
    _evaluate,
    _extract_benchmark_semantic_facts,
    _get_psets,
    _open_evaluation_model,
    _require_role_entity,
    _evaluator_input_error,
    _not_evaluable_semantic_checks,
    _fact_key_token,
    _application_role_mapping,
    _validate_production_expected_facts,
    _required_check,
    _evidence,
)

BENCHMARK_POLICY_VERSION = EVALUATION_POLICY_VERSION


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


def assert_benchmark_cannot_promote_failed_production(
    production_evaluation: Any,
    benchmark_evaluation: Any,
) -> None:
    """Prevent evaluator-only Gold from changing a failed production outcome.

    Benchmark-only comparison is useful as a stricter diagnostic, but it must
    never make an unsuccessful public production result publishable.
    """

    production_passed = (
        getattr(production_evaluation, "complete_repair_success", None) is True
        and getattr(
            production_evaluation,
            "successful_artifact_publishable",
            None,
        )
        is True
    )
    benchmark_promotes = (
        getattr(benchmark_evaluation, "complete_repair_success", None) is True
        or getattr(
            benchmark_evaluation,
            "successful_artifact_publishable",
            None,
        )
        is True
    )
    if not production_passed and benchmark_promotes:
        raise ValueError("BENCHMARK_CANNOT_PROMOTE_FAILED_PRODUCTION")


def evaluate_benchmark(inputs: BenchmarkEvaluationInputs) -> BenchmarkEvaluationResult:
    """Consume original/mutation truth only at the private evaluator boundary."""

    production_evaluation = evaluate_production(inputs.production)
    evaluation = _evaluate(
        inputs.production,
        private_original_path=Path(inputs.private_original_ifc_path),
        private_mapping=inputs.private_mutation_mapping,
    )
    assert_benchmark_cannot_promote_failed_production(
        production_evaluation,
        evaluation,
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
