"""Versioned, immutable operation-owned semantic evaluation policies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Callable


_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+$")


class PolicyContractError(ValueError):
    """Stable machine-readable policy contract failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class SemanticApplicability(str, Enum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    INFORMATIONAL = "informational"


class EvidenceSourceKind(str, Enum):
    """Closed authority set; arbitrary neighbor/name/model guesses are absent."""

    EXPLICIT_REQUEST = "explicit_request"
    PRIVATE_ORIGINAL = "private_original"
    SURVIVING_TARGET = "surviving_target"
    SURVIVING_HOST = "surviving_host"
    SURVIVING_TYPE = "surviving_type"
    APPROVED_PROTOTYPE = "approved_prototype"
    DETERMINISTIC_POLICY = "deterministic_policy"
    REPAIRED_OUTPUT = "repaired_output"


class ComparisonRule(str, Enum):
    TYPED_EQUIVALENCE = "typed_equivalence"


@dataclass(frozen=True)
class FactKeyNormalization:
    fact_key: str
    source_fact_key: str


SOURCE_PRECEDENCE = (
    EvidenceSourceKind.EXPLICIT_REQUEST,
    EvidenceSourceKind.PRIVATE_ORIGINAL,
    EvidenceSourceKind.SURVIVING_TARGET,
    EvidenceSourceKind.SURVIVING_HOST,
    EvidenceSourceKind.SURVIVING_TYPE,
    EvidenceSourceKind.APPROVED_PROTOTYPE,
    EvidenceSourceKind.DETERMINISTIC_POLICY,
)


@dataclass(frozen=True)
class SemanticFactSpec:
    check_id: str
    version: str
    fact_pattern: str
    applicability: SemanticApplicability
    allowed_sources: tuple[EvidenceSourceKind, ...]
    comparison: ComparisonRule
    absolute_tolerance: float = 0.0

    def __post_init__(self) -> None:
        if not _STABLE_ID.fullmatch(self.check_id):
            raise PolicyContractError("INVALID_EVALUATION_CHECK_ID", self.check_id)
        if not _VERSION.fullmatch(self.version):
            raise PolicyContractError(
                "INVALID_EVALUATION_CHECK_VERSION", self.version
            )
        if not self.fact_pattern or any(char.isspace() for char in self.fact_pattern):
            raise PolicyContractError(
                "INVALID_SEMANTIC_FACT_PATTERN", self.fact_pattern
            )
        if not isinstance(self.applicability, SemanticApplicability):
            raise PolicyContractError(
                "INVALID_SEMANTIC_APPLICABILITY", repr(self.applicability)
            )
        if not self.allowed_sources or any(
            not isinstance(source, EvidenceSourceKind)
            or source is EvidenceSourceKind.REPAIRED_OUTPUT
            for source in self.allowed_sources
        ):
            raise PolicyContractError(
                "INVALID_EVIDENCE_SOURCE", self.check_id
            )
        if len(set(self.allowed_sources)) != len(self.allowed_sources):
            raise PolicyContractError("DUPLICATE_EVIDENCE_SOURCE", self.check_id)
        if not isinstance(self.comparison, ComparisonRule):
            raise PolicyContractError("INVALID_COMPARISON_RULE", self.check_id)
        if self.absolute_tolerance < 0:
            raise PolicyContractError("INVALID_COMPARISON_TOLERANCE", self.check_id)


@dataclass(frozen=True)
class OperationEvaluationPolicy:
    policy_id: str
    version: str
    operation_type: str
    semantic_facts: tuple[SemanticFactSpec, ...]
    semantic_role: str = "target"
    fact_key_normalizer: Callable[[str], FactKeyNormalization] | None = None

    def __post_init__(self) -> None:
        if not _STABLE_ID.fullmatch(self.policy_id):
            raise PolicyContractError("INVALID_EVALUATION_POLICY_ID", self.policy_id)
        if not _VERSION.fullmatch(self.version):
            raise PolicyContractError(
                "INVALID_EVALUATION_POLICY_VERSION", self.version
            )
        if not _STABLE_ID.fullmatch(self.operation_type):
            raise PolicyContractError(
                "INVALID_EVALUATION_OPERATION_TYPE", self.operation_type
            )
        if not _STABLE_ID.fullmatch(self.semantic_role):
            raise PolicyContractError(
                "INVALID_EVALUATION_SEMANTIC_ROLE", self.semantic_role
            )
        if not self.semantic_facts:
            raise PolicyContractError(
                "MISSING_EVALUATION_CHECKS", self.policy_id
            )
        check_ids = [spec.check_id for spec in self.semantic_facts]
        if len(set(check_ids)) != len(check_ids):
            duplicate = next(
                check_id for check_id in check_ids if check_ids.count(check_id) > 1
            )
            raise PolicyContractError("DUPLICATE_EVALUATION_CHECK_ID", duplicate)


def extend_policy_with_explicit_facts(
    policy: OperationEvaluationPolicy,
    fact_keys: tuple[str, ...],
) -> OperationEvaluationPolicy:
    """Return an exact explicit-request extension without global wildcards."""

    existing = {spec.fact_pattern for spec in policy.semantic_facts}
    additions: list[SemanticFactSpec] = []
    for fact_key in sorted(set(fact_keys)):
        if not fact_key or "*" in fact_key or any(char.isspace() for char in fact_key):
            raise PolicyContractError("INVALID_EXPLICIT_SEMANTIC_FACT", fact_key)
        if fact_key in existing:
            continue
        token = re.sub(r"[^A-Za-z0-9._/-]+", "-", fact_key).strip("-")
        additions.append(
            SemanticFactSpec(
                check_id=f"explicit.{token}",
                version=policy.version,
                fact_pattern=fact_key,
                applicability=SemanticApplicability.CONDITIONAL,
                allowed_sources=(EvidenceSourceKind.EXPLICIT_REQUEST,),
                comparison=ComparisonRule.TYPED_EQUIVALENCE,
            )
        )
    return OperationEvaluationPolicy(
        policy_id=policy.policy_id,
        version=policy.version,
        operation_type=policy.operation_type,
        semantic_facts=(*policy.semantic_facts, *additions),
        semantic_role=policy.semantic_role,
        fact_key_normalizer=policy.fact_key_normalizer,
    )


__all__ = [
    "ComparisonRule",
    "EvidenceSourceKind",
    "FactKeyNormalization",
    "OperationEvaluationPolicy",
    "PolicyContractError",
    "SOURCE_PRECEDENCE",
    "SemanticApplicability",
    "SemanticFactSpec",
    "extend_policy_with_explicit_facts",
]
