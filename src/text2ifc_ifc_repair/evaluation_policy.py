"""Versioned, immutable operation-owned semantic evaluation policies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import re
from typing import Any, Callable, Mapping


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
    AUTHORIZED_TYPE_COHORT = "authorized_type_cohort"
    APPROVED_PROTOTYPE = "approved_prototype"
    DETERMINISTIC_POLICY = "deterministic_policy"
    REPAIRED_OUTPUT = "repaired_output"


class ComparisonRule(str, Enum):
    TYPED_EQUIVALENCE = "typed_equivalence"


@dataclass(frozen=True)
class StructuralL1Thresholds:
    """Frozen Phase 12 structural precision grade in public millimetres."""

    axis_point_mm: float = 5.0
    direction_degrees: float = 0.1
    member_dimension_mm: float = 1.0
    section_dimension_mm: float = 1.0

    def __post_init__(self) -> None:
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0.0
            for value in (
                self.axis_point_mm,
                self.direction_degrees,
                self.member_dimension_mm,
                self.section_dimension_mm,
            )
        ):
            raise PolicyContractError(
                "INVALID_STRUCTURAL_L1_THRESHOLD",
                repr(self),
            )


STRUCTURAL_L1_THRESHOLDS = StructuralL1Thresholds()
STRUCTURAL_GEOMETRY_L1_CHECK_IDS = (
    "l1.structural.axis-points",
    "l1.structural.axis-direction",
    "l1.structural.member-dimension",
    "l1.structural.section-dimensions",
    "l1.structural.profile-orientation",
)
STRUCTURAL_L1_CHECK_IDS = (
    *STRUCTURAL_GEOMETRY_L1_CHECK_IDS,
    "l1.structural.product",
    "l1.structural.relationships",
)


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
    EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
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
    cohort_fact_patterns: tuple[str, ...] = ()
    target_authority_mode: str = "edited_entity"

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
        if any(
            not pattern or any(char.isspace() for char in pattern)
            for pattern in self.cohort_fact_patterns
        ):
            raise PolicyContractError("INVALID_COHORT_FACT_PATTERN", self.policy_id)
        if self.target_authority_mode not in {
            "edited_entity",
            "host_for_created_entity",
        }:
            raise PolicyContractError("INVALID_TARGET_AUTHORITY_MODE", self.policy_id)


def extend_policy_with_explicit_facts(
    policy: OperationEvaluationPolicy,
    fact_keys: tuple[str, ...],
    *,
    applicability: SemanticApplicability = SemanticApplicability.CONDITIONAL,
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
                applicability=applicability,
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
        cohort_fact_patterns=policy.cohort_fact_patterns,
        target_authority_mode=policy.target_authority_mode,
    )


def normalize_policy_fact_key(
    policy: OperationEvaluationPolicy,
    fact_key: str,
) -> FactKeyNormalization:
    """Apply an operation-owned canonicalizer through one common seam."""

    normalized = (
        FactKeyNormalization(fact_key, fact_key)
        if policy.fact_key_normalizer is None
        else policy.fact_key_normalizer(fact_key)
    )
    if not isinstance(normalized, FactKeyNormalization):
        raise PolicyContractError("INVALID_FACT_KEY_NORMALIZATION", fact_key)
    if not normalized.fact_key or not normalized.source_fact_key:
        raise PolicyContractError("INVALID_FACT_KEY_NORMALIZATION", fact_key)
    return normalized


def compare_structural_l1_measurement(
    *,
    family: str,
    expected: Mapping[str, Any],
    measured: Mapping[str, Any],
    thresholds: StructuralL1Thresholds = STRUCTURAL_L1_THRESHOLDS,
) -> dict[str, Any]:
    """Compare reopened member measurements without geometry proxies."""

    dimension_keys = {
        "beam": ("width_mm", "height_mm"),
        "column": ("width_mm", "depth_mm"),
    }.get(family)
    if dimension_keys is None:
        raise PolicyContractError("STRUCTURAL_FAMILY_UNSUPPORTED", family)

    expected_start = _structural_point(expected.get("axis_start_mm"))
    expected_end = _structural_point(expected.get("axis_end_mm"))
    actual_start = _structural_point(measured.get("axis_start_mm"))
    actual_end = _structural_point(measured.get("axis_end_mm"))
    expected_direction = _structural_direction(
        expected.get("axis_direction")
    )
    actual_direction = _structural_direction(
        measured.get("axis_direction")
    )
    expected_extent = _structural_positive_number(
        expected.get("axis_extent_mm")
    )
    actual_extent = _structural_positive_number(
        measured.get("axis_extent_mm")
    )
    expected_section = expected.get("section")
    actual_section = measured.get("section")
    if not isinstance(expected_section, Mapping) or not isinstance(
        actual_section, Mapping
    ):
        raise PolicyContractError(
            "STRUCTURAL_L1_MEASUREMENT_INVALID", "section"
        )
    if (
        expected_section.get("shape") != "rectangle"
        or actual_section.get("shape") != "rectangle"
    ):
        raise PolicyContractError(
            "STRUCTURAL_L1_MEASUREMENT_INVALID", "section.shape"
        )

    point_errors = {
        "start_mm": math.dist(expected_start, actual_start),
        "end_mm": math.dist(expected_end, actual_end),
    }
    direction_error = _direction_error_degrees(
        expected_direction, actual_direction
    )
    member_error = abs(expected_extent - actual_extent)
    section_errors = {
        key: abs(
            _structural_positive_number(expected_section.get(key))
            - _structural_positive_number(actual_section.get(key))
        )
        for key in dimension_keys
    }
    profile_error: float | None
    if family == "column":
        orientation_declared = "orientation" in expected_section
        actual_orientation = measured.get("orientation")
        if not orientation_declared:
            profile_error = None if actual_orientation is None else math.inf
        elif actual_orientation is None:
            profile_error = math.inf
        else:
            profile_error = _direction_error_degrees(
                _structural_direction(expected.get("profile_x_direction")),
                _structural_direction(actual_orientation),
            )
    else:
        profile_error = None

    metrics = {
        "axis_point_errors_mm": point_errors,
        "max_axis_point_error_mm": max(point_errors.values()),
        "direction_error_degrees": direction_error,
        "member_dimension_error_mm": member_error,
        "section_dimension_errors_mm": section_errors,
        "max_section_dimension_error_mm": max(section_errors.values()),
        "profile_orientation_error_degrees": profile_error,
        "representation_type": measured.get("representation_type"),
    }
    epsilon = 1e-9

    def check(
        passed: bool,
        reason: str,
        expected_value: Any,
        actual_value: Any,
    ) -> dict[str, Any]:
        return {
            "status": "passed" if passed else "failed",
            "reason": reason,
            "expected": expected_value,
            "actual": actual_value,
        }

    return {
        "metrics": metrics,
        "l1_checks": {
            "l1.structural.axis-points": check(
                metrics["max_axis_point_error_mm"]
                <= thresholds.axis_point_mm + epsilon,
                "Each reopened structural axis endpoint must match the bound center axis.",
                {"maximum_error_mm": thresholds.axis_point_mm},
                point_errors,
            ),
            "l1.structural.axis-direction": check(
                direction_error <= thresholds.direction_degrees + epsilon,
                "Reopened member direction and horizontal/vertical tilt must match.",
                {"maximum_error_degrees": thresholds.direction_degrees},
                {"error_degrees": direction_error},
            ),
            "l1.structural.member-dimension": check(
                member_error <= thresholds.member_dimension_mm + epsilon,
                "Reopened member axis extent must match the bound length or height.",
                {"maximum_error_mm": thresholds.member_dimension_mm},
                {"error_mm": member_error},
            ),
            "l1.structural.section-dimensions": check(
                metrics["max_section_dimension_error_mm"]
                <= thresholds.section_dimension_mm + epsilon,
                "Every reopened rectangular section dimension must match.",
                {"maximum_error_mm": thresholds.section_dimension_mm},
                section_errors,
            ),
            "l1.structural.profile-orientation": check(
                profile_error is None
                or profile_error <= thresholds.direction_degrees + epsilon,
                "Column profile orientation must match when declared and stay omitted for a square section.",
                {
                    "maximum_error_degrees": thresholds.direction_degrees,
                    "square_orientation": "omitted",
                },
                {"error_degrees": profile_error},
            ),
        },
    }


def structural_l1_authorization(family: str) -> dict[str, Any]:
    """Return exact Registry-driven effect authorization for one family."""

    occurrence_class = {
        "beam": "IfcBeam",
        "column": "IfcColumn",
    }.get(family)
    type_class = {
        "beam": "IfcBeamType",
        "column": "IfcColumnType",
    }.get(family)
    if occurrence_class is None or type_class is None:
        raise PolicyContractError("STRUCTURAL_FAMILY_UNSUPPORTED", family)
    semantic_prefix = f"semantic_{family}_"
    created = {
        family: occurrence_class,
        "structural_type": type_class,
        "structural_type_relationship": "IfcRelDefinesByType",
        "spatial_containment": "IfcRelContainedInSpatialStructure",
        f"{semantic_prefix}pset": "IfcPropertySet",
        f"{semantic_prefix}pset_relationship": "IfcRelDefinesByProperties",
        f"{semantic_prefix}quantities": "IfcElementQuantity",
        f"{semantic_prefix}quantity_relationship": "IfcRelDefinesByProperties",
        f"{semantic_prefix}material_relationship": "IfcRelAssociatesMaterial",
        f"{semantic_prefix}classification_relationship": "IfcRelAssociatesClassification",
    }
    relations: dict[str, Any] = {
        "structural_type_relationship": {
            "ifc_class": "IfcRelDefinesByType",
            "added_endpoint_roles": (family,),
        },
        "spatial_containment": {
            "ifc_class": "IfcRelContainedInSpatialStructure",
            "added_endpoint_roles": (family,),
        },
        f"{semantic_prefix}pset_relationship": {
            "ifc_class": "IfcRelDefinesByProperties",
            "added_endpoint_roles": (family,),
        },
        f"{semantic_prefix}quantity_relationship": {
            "ifc_class": "IfcRelDefinesByProperties",
            "added_endpoint_roles": (family,),
        },
        f"{semantic_prefix}material_relationship": {
            "ifc_class": "IfcRelAssociatesMaterial",
            "added_endpoint_roles": (family,),
        },
        f"{semantic_prefix}classification_relationship": {
            "ifc_class": "IfcRelAssociatesClassification",
            "added_endpoint_roles": (family,),
        },
    }
    for index in range(2, 65):
        pset_role = f"{semantic_prefix}pset_{index}"
        pset_relation_role = f"{semantic_prefix}pset_relationship_{index}"
        material_role = f"{semantic_prefix}material_relationship_{index}"
        classification_role = (
            f"{semantic_prefix}classification_relationship_{index}"
        )
        created[pset_role] = "IfcPropertySet"
        created[pset_relation_role] = "IfcRelDefinesByProperties"
        created[material_role] = "IfcRelAssociatesMaterial"
        created[classification_role] = "IfcRelAssociatesClassification"
        relations[pset_relation_role] = {
            "ifc_class": "IfcRelDefinesByProperties",
            "added_endpoint_roles": (family,),
        }
        relations[material_role] = {
            "ifc_class": "IfcRelAssociatesMaterial",
            "added_endpoint_roles": (family,),
        }
        relations[classification_role] = {
            "ifc_class": "IfcRelAssociatesClassification",
            "added_endpoint_roles": (family,),
        }
    return {
        "policy_id": f"{family}.add.l1",
        "policy_version": "0.1",
        "created": created,
        "modified": {
            # Exact existing-Type reuse extends the existing relation instead
            # of creating one; the generated-Type path stays in "created".
            "structural_type_relationship": "IfcRelDefinesByType",
            "spatial_containment": "IfcRelContainedInSpatialStructure",
            "structural_type_relationship": "IfcRelDefinesByType",
        },
        "removed": {},
        "required_roles": {
            "created": (family,),
            # Generated Types create the relation; exact existing-Type reuse
            # extends the existing one. Exactly one binding must exist either
            # way.
            "created_or_modified": ("structural_type_relationship",),
        },
        "relations": relations,
    }


def _structural_point(value: Any) -> tuple[float, float, float]:
    if (
        isinstance(value, (str, bytes, Mapping))
        or not isinstance(value, (tuple, list))
        or len(value) != 3
    ):
        raise PolicyContractError("STRUCTURAL_L1_MEASUREMENT_INVALID", "point")
    return tuple(_structural_number(item) for item in value)  # type: ignore[return-value]


def _structural_direction(value: Any) -> tuple[float, float, float]:
    direction = _structural_point(value)
    magnitude = math.sqrt(sum(item * item for item in direction))
    if magnitude <= 0.0:
        raise PolicyContractError(
            "STRUCTURAL_L1_MEASUREMENT_INVALID", "direction"
        )
    return tuple(item / magnitude for item in direction)


def _structural_number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyContractError("STRUCTURAL_L1_MEASUREMENT_INVALID", "number")
    number = float(value)
    if not math.isfinite(number):
        raise PolicyContractError("STRUCTURAL_L1_MEASUREMENT_INVALID", "number")
    return number


def _structural_positive_number(value: Any) -> float:
    number = _structural_number(value)
    if number <= 0.0:
        raise PolicyContractError(
            "STRUCTURAL_L1_MEASUREMENT_INVALID", "positive_number"
        )
    return number


def _direction_error_degrees(
    expected: tuple[float, float, float],
    actual: tuple[float, float, float],
) -> float:
    cosine = max(
        -1.0,
        min(1.0, sum(left * right for left, right in zip(expected, actual))),
    )
    return math.degrees(math.acos(cosine))


__all__ = [
    "ComparisonRule",
    "EvidenceSourceKind",
    "FactKeyNormalization",
    "OperationEvaluationPolicy",
    "PolicyContractError",
    "SOURCE_PRECEDENCE",
    "STRUCTURAL_GEOMETRY_L1_CHECK_IDS",
    "STRUCTURAL_L1_CHECK_IDS",
    "STRUCTURAL_L1_THRESHOLDS",
    "SemanticApplicability",
    "SemanticFactSpec",
    "StructuralL1Thresholds",
    "compare_structural_l1_measurement",
    "extend_policy_with_explicit_facts",
    "normalize_policy_fact_key",
    "structural_l1_authorization",
]
