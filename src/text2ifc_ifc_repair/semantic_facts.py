"""Deterministic typed semantic expectation resolution and comparison."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import math
from typing import Any, Iterable

from .evaluation_models import CheckResult, EvaluationStatus, EvidenceFact
from .evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SOURCE_PRECEDENCE,
    SemanticApplicability,
    SemanticFactSpec,
)
from .index_models import PropertyFact


class SemanticFactError(ValueError):
    """Stable machine-readable semantic fact failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class SemanticFact:
    fact_key: str
    value: Any
    value_type: str | None
    unit: str | None
    inherited: bool
    pset_path: str | None
    entity_source: str
    source_kind: EvidenceSourceKind
    source_ref: str
    provenance: tuple[str, ...]
    compatible: bool = True

    def __post_init__(self) -> None:
        if not self.fact_key or any(char.isspace() for char in self.fact_key):
            raise SemanticFactError("INVALID_SEMANTIC_FACT_KEY", self.fact_key)
        if not isinstance(self.source_kind, EvidenceSourceKind):
            raise SemanticFactError(
                "UNAUTHORIZED_EVIDENCE_SOURCE", str(self.source_kind)
            )
        if not self.entity_source or not self.source_ref:
            raise SemanticFactError("MISSING_SEMANTIC_SOURCE", self.fact_key)
        if not self.provenance or any(not item for item in self.provenance):
            raise SemanticFactError("MISSING_SEMANTIC_PROVENANCE", self.fact_key)


def semantic_fact_from_property_fact(
    fact: PropertyFact,
    *,
    source_kind: EvidenceSourceKind,
    source_ref: str,
    entity_source: str,
    provenance: tuple[str, ...],
    compatible: bool = True,
) -> SemanticFact:
    """Lift the Phase 7 typed property representation without losing provenance."""

    pset_path = f"{fact.set_name}.{fact.property_name}"
    return SemanticFact(
        fact_key=f"{fact.set_kind}:{pset_path}",
        value=fact.value,
        value_type=fact.value_type,
        unit=fact.unit,
        inherited=fact.inherited,
        pset_path=pset_path,
        entity_source=entity_source,
        source_kind=source_kind,
        source_ref=source_ref,
        provenance=(*provenance, fact.provenance),
        compatible=compatible,
    )


def resolve_expected_facts(
    spec: SemanticFactSpec,
    facts: Iterable[SemanticFact],
) -> tuple[tuple[SemanticFact, ...], tuple[str, ...]]:
    """Resolve every fact key through the one fixed authority ordering."""

    allowed = set(spec.allowed_sources)
    candidates: dict[str, list[SemanticFact]] = {}
    rejected: list[str] = []
    for fact in facts:
        if not fnmatchcase(fact.fact_key, spec.fact_pattern):
            continue
        if fact.source_kind not in allowed:
            rejected.append(f"{fact.source_kind.value}:not_allowed")
            continue
        if (
            fact.source_kind is EvidenceSourceKind.APPROVED_PROTOTYPE
            and not fact.compatible
        ):
            rejected.append("approved_prototype:incompatible")
            continue
        candidates.setdefault(fact.fact_key, []).append(fact)

    precedence = {source: rank for rank, source in enumerate(SOURCE_PRECEDENCE)}
    resolved = tuple(
        min(
            candidates[fact_key],
            key=lambda fact: (
                precedence[fact.source_kind],
                fact.source_ref,
                repr(fact.value),
            ),
        )
        for fact_key in sorted(candidates)
    )
    return resolved, tuple(sorted(set(rejected)))


def evaluate_operation_semantics(
    policy: OperationEvaluationPolicy,
    *,
    expected_facts: Iterable[SemanticFact],
    repaired_facts: Iterable[SemanticFact],
) -> tuple[CheckResult, ...]:
    """Evaluate any operation policy without operation-family field branches."""

    expected = tuple(expected_facts)
    repaired = tuple(repaired_facts)
    if any(fact.source_kind is not EvidenceSourceKind.REPAIRED_OUTPUT for fact in repaired):
        raise SemanticFactError(
            "INVALID_REPAIRED_FACT_SOURCE", "repaired facts must come from repaired_output"
        )

    results: list[CheckResult] = []
    claimed_fact_keys: set[str] = set()
    for spec in policy.semantic_facts:
        resolved, rejected = resolve_expected_facts(spec, expected)
        resolved = tuple(
            fact for fact in resolved if fact.fact_key not in claimed_fact_keys
        )
        claimed_fact_keys.update(fact.fact_key for fact in resolved)
        if resolved:
            for fact in resolved:
                results.append(
                    _compare_fact(policy=policy, spec=spec, expected=fact, repaired=repaired)
                )
            continue
        results.append(
            _result_without_expectation(
                policy=policy,
                spec=spec,
                repaired=repaired,
                rejected=rejected,
            )
        )
    return tuple(results)


def _compare_fact(
    *,
    policy: OperationEvaluationPolicy,
    spec: SemanticFactSpec,
    expected: SemanticFact,
    repaired: tuple[SemanticFact, ...],
) -> CheckResult:
    actual = next(
        (fact for fact in repaired if fact.fact_key == expected.fact_key), None
    )
    equivalent = actual is not None and _semantically_equivalent(spec, expected, actual)
    status = EvaluationStatus.PASSED if equivalent else EvaluationStatus.FAILED
    reason = (
        "Authorized semantic fact is present and equivalent in repaired output"
        if equivalent
        else (
            "Authorized semantic fact is missing from repaired output"
            if actual is None
            else "Authorized semantic fact differs from repaired output"
        )
    )
    evidence = EvidenceFact(
        fact_id=expected.fact_key,
        source_kind=expected.source_kind.value,
        source_ref=expected.source_ref,
        expected_state="available",
        actual_state="available" if actual is not None else "unavailable",
        expected_value=_fact_value(expected),
        actual_value=_fact_value(actual) if actual is not None else None,
        provenance=(
            *expected.provenance,
            *((f"repaired:{item}" for item in actual.provenance) if actual else ()),
        ),
    )
    return CheckResult(
        check_id=_result_check_id(spec, expected.fact_key),
        policy_id=policy.policy_id,
        applicability=spec.applicability.value,
        mandatory=spec.applicability is not SemanticApplicability.INFORMATIONAL,
        status=status,
        reason=reason,
        evidence=(evidence,),
    )


def _result_without_expectation(
    *,
    policy: OperationEvaluationPolicy,
    spec: SemanticFactSpec,
    repaired: tuple[SemanticFact, ...],
    rejected: tuple[str, ...],
) -> CheckResult:
    required = spec.applicability is SemanticApplicability.REQUIRED
    status = (
        EvaluationStatus.NOT_EVALUABLE if required else EvaluationStatus.NOT_REQUIRED
    )
    actual = next(
        (fact for fact in repaired if fnmatchcase(fact.fact_key, spec.fact_pattern)),
        None,
    )
    provenance = tuple(
        [*(f"searched:{source.value}" for source in spec.allowed_sources), *rejected]
    )
    evidence = EvidenceFact(
        fact_id=spec.check_id,
        source_kind="source_search",
        source_ref=f"{policy.policy_id}/{spec.check_id}",
        expected_state="unavailable",
        actual_state=(
            "available" if required and actual is not None else "not_applicable"
        ),
        expected_value=None,
        actual_value=_fact_value(actual) if required and actual is not None else None,
        provenance=provenance or ("searched:no_authorized_sources",),
    )
    return CheckResult(
        check_id=spec.check_id,
        policy_id=policy.policy_id,
        applicability=spec.applicability.value,
        mandatory=required,
        status=status,
        reason=(
            "Required semantic fact has no reliable expected evidence"
            if required
            else "No authorized source establishes this conditional semantic fact"
        ),
        evidence=(evidence,),
    )


def _semantically_equivalent(
    spec: SemanticFactSpec,
    expected: SemanticFact,
    actual: SemanticFact,
) -> bool:
    if spec.comparison is not ComparisonRule.TYPED_EQUIVALENCE:
        return False
    if expected.value_type != actual.value_type or expected.unit != actual.unit:
        return False
    if (
        isinstance(expected.value, (int, float))
        and not isinstance(expected.value, bool)
        and isinstance(actual.value, (int, float))
        and not isinstance(actual.value, bool)
    ):
        return math.isclose(
            float(expected.value),
            float(actual.value),
            rel_tol=0.0,
            abs_tol=spec.absolute_tolerance,
        )
    return expected.value == actual.value


def _fact_value(fact: SemanticFact | None) -> dict[str, Any] | None:
    if fact is None:
        return None
    return {
        "value": fact.value,
        "value_type": fact.value_type,
        "unit": fact.unit,
        "inherited": fact.inherited,
        "pset_path": fact.pset_path,
        "entity_source": fact.entity_source,
    }


def _result_check_id(spec: SemanticFactSpec, fact_key: str) -> str:
    return spec.check_id if "*" not in spec.fact_pattern else f"{spec.check_id}:{fact_key}"


__all__ = [
    "SemanticFact",
    "SemanticFactError",
    "evaluate_operation_semantics",
    "resolve_expected_facts",
    "semantic_fact_from_property_fact",
]
