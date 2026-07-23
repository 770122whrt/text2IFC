"""Deterministic typed semantic expectation resolution and comparison."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fnmatch import fnmatchcase
import math
import re
from typing import Any, Iterable

import ifcopenshell.util.classification
import ifcopenshell.util.element

from .evaluation_models import CheckResult, EvaluationStatus, EvidenceFact
from .evaluation_policy import (
    ComparisonRule,
    EvidenceSourceKind,
    OperationEvaluationPolicy,
    SOURCE_PRECEDENCE,
    SemanticApplicability,
    SemanticFactSpec,
    normalize_policy_fact_key,
)
from .index_models import AssociationFact, ElementRecord, PropertyFact, TypeRecord


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
        fact_key=f"{_key_token(fact.set_kind)}:{_key_token(pset_path)}",
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


def semantic_facts_from_element_record(
    record: ElementRecord,
    *,
    source_kind: EvidenceSourceKind,
    source_ref: str,
    compatible: bool = True,
) -> tuple[SemanticFact, ...]:
    """Convert a Phase 7 record through the same typed semantic fact seam."""

    entity_source = f"{record.ifc_class}:{record.ifc_global_id or record.record_id}"
    provenance = (f"index:{record.record_id}",)
    facts = [
        semantic_fact_from_property_fact(
            fact,
            source_kind=source_kind,
            source_ref=source_ref,
            entity_source=entity_source,
            provenance=provenance,
            compatible=compatible,
        )
        for fact in record.properties
    ]
    facts.extend(
        _record_scalar_facts(
            record,
            source_kind=source_kind,
            source_ref=source_ref,
            entity_source=entity_source,
            provenance=provenance,
            compatible=compatible,
        )
    )
    for association in record.associations:
        facts.extend(
            _semantic_facts_from_association(
                association,
                source_kind=source_kind,
                authority_source_ref=source_ref,
                compatible=compatible,
            )
        )
    return tuple(sorted(facts, key=lambda fact: fact.fact_key))


def semantic_facts_from_type_record(
    record: TypeRecord,
    *,
    source_kind: EvidenceSourceKind,
    source_ref: str,
    compatible: bool = True,
) -> tuple[SemanticFact, ...]:
    """Convert direct IFC Type authority without occurrence-derived facts."""

    entity_source = f"{record.ifc_class}:{record.ifc_global_id or record.record_id}"
    provenance = (f"type-index:{record.record_id}",)
    facts = [
        semantic_fact_from_property_fact(
            fact,
            source_kind=source_kind,
            source_ref=source_ref,
            entity_source=entity_source,
            provenance=provenance,
            compatible=compatible,
        )
        for fact in record.properties
    ]
    scalar_values = (
        ("label:Name", record.name, "IfcLabel"),
        ("attribute:ApplicableOccurrence", record.applicable_occurrence, "IfcLabel"),
        ("attribute:PredefinedType", record.predefined_type, "IfcLabel"),
        ("attribute:ElementType", record.element_type, "IfcLabel"),
    )
    facts.extend(
        SemanticFact(
            fact_key=fact_key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source=entity_source,
            source_kind=source_kind,
            source_ref=source_ref,
            provenance=provenance,
            compatible=compatible,
        )
        for fact_key, value, value_type in scalar_values
        if value is not None
    )
    for association in record.associations:
        facts.extend(
            _semantic_facts_from_association(
                association,
                source_kind=source_kind,
                authority_source_ref=source_ref,
                compatible=compatible,
            )
        )
    return tuple(sorted(facts, key=lambda fact: (fact.fact_key, repr(fact.value))))


def extract_ifc_semantic_facts(
    element: Any,
    *,
    policy: OperationEvaluationPolicy,
    source_kind: EvidenceSourceKind,
    source_ref: str,
    provenance: tuple[str, ...],
    compatible: bool = True,
) -> tuple[SemanticFact, ...]:
    """Extract inheritance-aware semantic facts from an IFC occurrence."""

    entity_source = _entity_ref(element)
    facts: list[SemanticFact] = []
    for property_fact in extract_property_facts(element):
            semantic = semantic_fact_from_property_fact(
                property_fact,
                source_kind=source_kind,
                source_ref=source_ref,
                entity_source=entity_source,
                provenance=provenance,
                compatible=compatible,
            )
            semantic = _normalize_fact_for_policy(policy, semantic)
            if _policy_accepts_key(policy, semantic.fact_key):
                facts.append(semantic)

    facts.extend(
        _ifc_relationship_and_attribute_facts(
            element,
            policy=policy,
            source_kind=source_kind,
            source_ref=source_ref,
            entity_source=entity_source,
            provenance=provenance,
            compatible=compatible,
        )
    )
    if _policy_accepts_key(policy, "material:probe"):
        facts.extend(
            _ifc_material_facts(
                element,
                source_kind=source_kind,
                source_ref=source_ref,
                entity_source=entity_source,
                provenance=provenance,
                compatible=compatible,
            )
        )
    if _policy_accepts_key(policy, "classification:probe"):
        facts.extend(
            _ifc_classification_facts(
                element,
                source_kind=source_kind,
                source_ref=source_ref,
                entity_source=entity_source,
                provenance=provenance,
                compatible=compatible,
            )
        )
    unique = {(fact.fact_key, repr(fact.value)): fact for fact in facts}
    return tuple(unique[key] for key in sorted(unique))


def extract_property_facts(
    element: Any, *, should_inherit: bool = True
) -> tuple[PropertyFact, ...]:
    """Extract deterministic Pset/Qto facts and classify their actual origin."""

    merged_sets = _get_psets(element, should_inherit=should_inherit)
    direct_sets = (
        _get_psets(element, should_inherit=False) if should_inherit else merged_sets
    )
    facts: list[PropertyFact] = []
    for set_name, members in merged_sets.items():
        if not isinstance(members, dict):
            continue
        direct_members = direct_sets.get(set_name, {})
        for property_name, payload in members.items():
            if property_name == "id" or not isinstance(payload, dict) or "value" not in payload:
                continue
            property_class = str(payload.get("class") or "")
            inherited = should_inherit and not (
                isinstance(direct_members, dict) and property_name in direct_members
            )
            facts.append(
                PropertyFact(
                    set_kind=(
                        "quantity"
                        if property_class.startswith("IfcQuantity")
                        else "pset"
                    ),
                    set_name=str(set_name),
                    property_name=str(property_name),
                    value=payload.get("value"),
                    value_type=_optional_text(payload.get("value_type") or property_class),
                    unit=_optional_text(payload.get("unit")),
                    inherited=inherited,
                    provenance=(
                        "ifcopenshell.util.element.get_psets:inherited"
                        if inherited
                        else "ifcopenshell.util.element.get_psets:direct"
                    ),
                )
            )
    return tuple(
        sorted(
            facts,
            key=lambda fact: (
                fact.set_kind,
                fact.set_name,
                fact.property_name,
                repr(fact.value),
            ),
        )
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

    expected = tuple(_normalize_fact_for_policy(policy, fact) for fact in expected_facts)
    repaired = tuple(_normalize_fact_for_policy(policy, fact) for fact in repaired_facts)
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
    if (
        expected.value_type != actual.value_type
        or expected.unit != actual.unit
        or expected.inherited != actual.inherited
    ):
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


def _record_scalar_facts(
    record: ElementRecord,
    **source: Any,
) -> tuple[SemanticFact, ...]:
    values = (
        ("relationship:type", record.type_global_id, "IfcGloballyUniqueId"),
        ("relationship:storey", record.storey_global_id, "IfcGloballyUniqueId"),
        ("label:Name", record.name, "IfcLabel"),
        ("label:Tag", record.tag, "IfcIdentifier"),
    )
    return tuple(
        SemanticFact(
            fact_key=fact_key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=False,
            pset_path=None,
            **source,
        )
        for fact_key, value, value_type in values
        if value is not None
    )


def _ifc_relationship_and_attribute_facts(
    element: Any,
    *,
    policy: OperationEvaluationPolicy,
    **source: Any,
) -> tuple[SemanticFact, ...]:
    values: list[tuple[str, Any, str]] = []
    element_type = (
        ifcopenshell.util.element.get_type(element)
        if _policy_accepts_key(policy, "relationship:type")
        else None
    )
    if element_type is not None:
        values.append(
            ("relationship:type", _root_identity(element_type), element_type.is_a())
        )
    storey = (
        ifcopenshell.util.element.get_container(
            element, ifc_class="IfcBuildingStorey"
        )
        if _policy_accepts_key(policy, "relationship:storey")
        else None
    )
    if storey is not None:
        values.append(("relationship:storey", _root_identity(storey), storey.is_a()))
    host = (
        _filled_element_host(element)
        if _policy_accepts_key(policy, "relationship:host")
        else None
    )
    if host is not None:
        values.append(("relationship:host", _root_identity(host), host.is_a()))
    requested_attributes = sorted(
        spec.fact_pattern
        for spec in policy.semantic_facts
        if spec.fact_pattern.startswith(("attribute:", "label:"))
        and "*" not in spec.fact_pattern
    )
    for fact_key in requested_attributes:
        category, attribute = fact_key.split(":", 1)
        value = getattr(element, attribute, None)
        if value is not None:
            values.append((fact_key, value, _python_value_type(value, category, fact_key)))
    return tuple(
        SemanticFact(
            fact_key=fact_key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=False,
            pset_path=None,
            **source,
        )
        for fact_key, value, value_type in values
    )


def _ifc_material_facts(element: Any, **source: Any) -> tuple[SemanticFact, ...]:
    facts = []
    base_provenance = source.pop("provenance")
    for material in ifcopenshell.util.element.get_materials(
        element, should_inherit=True
    ):
        name = _optional_text(getattr(material, "Name", None)) or _root_identity(material)
        facts.append(
            SemanticFact(
                fact_key=f"material:{_key_token(name)}",
                value=name,
                value_type=material.is_a(),
                unit=None,
                inherited=False,
                pset_path=None,
                provenance=(
                    *base_provenance,
                    "ifcopenshell.util.element.get_materials",
                ),
                **source,
            )
        )
    return tuple(facts)


def _ifc_classification_facts(element: Any, **source: Any) -> tuple[SemanticFact, ...]:
    facts = []
    base_provenance = source.pop("provenance")
    references = ifcopenshell.util.classification.get_references(
        element, should_inherit=True
    )
    for reference in sorted(references, key=_root_identity):
        identification = _optional_text(
            getattr(reference, "Identification", None)
            or getattr(reference, "ItemReference", None)
        )
        name = _optional_text(getattr(reference, "Name", None))
        try:
            classification = ifcopenshell.util.classification.get_classification(reference)
        except Exception:
            classification = None
        system = _optional_text(getattr(classification, "Name", None)) or "unspecified"
        token = identification or name or _root_identity(reference)
        facts.append(
            SemanticFact(
                fact_key=f"classification:{_key_token(system)}:{_key_token(token)}",
                value={
                    "system": system,
                    "identification": identification,
                    "name": name,
                },
                value_type=reference.is_a(),
                unit=None,
                inherited=False,
                pset_path=None,
                provenance=(
                    *base_provenance,
                    "ifcopenshell.util.classification.get_references",
                ),
                **source,
            )
        )
    return tuple(facts)


def _get_psets(element: Any, *, should_inherit: bool) -> dict[str, Any]:
    try:
        return ifcopenshell.util.element.get_psets(
            element,
            psets_only=False,
            qtos_only=False,
            should_inherit=should_inherit,
            verbose=True,
        )
    except Exception as error:
        raise SemanticFactError(
            "IFC_PSET_EXTRACTION_FAILED",
            f"{_entity_ref(element)}:{type(error).__name__}:{error}",
        ) from error


def _filled_element_host(element: Any) -> Any | None:
    for fill in getattr(element, "FillsVoids", ()):
        opening = fill.RelatingOpeningElement
        for void in getattr(opening, "VoidsElements", ()):
            return void.RelatingBuildingElement
    return None


def _entity_ref(entity: Any) -> str:
    return f"{entity.is_a()}:{_root_identity(entity)}"


def _root_identity(entity: Any) -> str:
    return str(getattr(entity, "GlobalId", None) or f"#{entity.id()}")


def _key_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._/-]+", "-", value).strip("-") or "unnamed"


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _policy_accepts_key(policy: OperationEvaluationPolicy, fact_key: str) -> bool:
    return any(
        fnmatchcase(fact_key, spec.fact_pattern) for spec in policy.semantic_facts
    )


def _semantic_facts_from_association(
    association: AssociationFact,
    *,
    source_kind: EvidenceSourceKind,
    authority_source_ref: str,
    compatible: bool,
) -> tuple[SemanticFact, ...]:
    """Lift public IFC association facts while retaining reusable resource identity."""

    provenance = (
        *association.provenance,
        f"authority-source:{authority_source_ref}",
        f"relationship:{association.relationship_ref}",
        f"resource:{association.resource_ref}",
    )
    common = {
        "unit": None,
        "inherited": association.inherited,
        "pset_path": None,
        "entity_source": association.resource_ref,
        "source_kind": source_kind,
        "source_ref": f"resource:{association.resource_ref}",
        "provenance": provenance,
        "compatible": compatible,
    }
    if association.association_kind == "material":
        names = association.semantic_value.get("names", ())
        return tuple(
            SemanticFact(
                fact_key=f"material:{_key_token(str(name))}",
                value=str(name),
                value_type="IfcMaterial",
                **common,
            )
            for name in names
            if str(name).strip()
        )
    if association.association_kind == "classification":
        system = str(association.semantic_value.get("system") or "unspecified")
        identification = str(
            association.semantic_value.get("identification")
            or association.semantic_value.get("name")
            or association.resource_ref
        )
        return (
            SemanticFact(
                fact_key=(
                    f"classification:{_key_token(system)}:"
                    f"{_key_token(identification)}"
                ),
                value=dict(association.semantic_value),
                value_type=association.resource_ifc_class,
                **common,
            ),
        )
    return ()


def _normalize_fact_for_policy(
    policy: OperationEvaluationPolicy,
    fact: SemanticFact,
) -> SemanticFact:
    normalized = normalize_policy_fact_key(policy, fact.fact_key)
    if normalized.fact_key == fact.fact_key:
        return fact
    return replace(
        fact,
        fact_key=normalized.fact_key,
        provenance=(*fact.provenance, f"source_fact_key:{normalized.source_fact_key}"),
    )


def _python_value_type(value: Any, category: str, fact_key: str = "") -> str:
    if fact_key in {"attribute:OverallWidth", "attribute:OverallHeight"}:
        return "IfcPositiveLengthMeasure"
    if category == "label":
        return "IfcLabel"
    if isinstance(value, bool):
        return "IfcBoolean"
    if isinstance(value, (int, float)):
        return "IfcReal"
    return type(value).__name__


__all__ = [
    "SemanticFact",
    "SemanticFactError",
    "evaluate_operation_semantics",
    "extract_property_facts",
    "extract_ifc_semantic_facts",
    "resolve_expected_facts",
    "semantic_fact_from_property_fact",
    "semantic_facts_from_element_record",
    "semantic_facts_from_type_record",
]
