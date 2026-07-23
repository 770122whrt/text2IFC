"""Operation-neutral exact IFC property intent contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Iterable, Mapping, TYPE_CHECKING

from text2ifc_knowledge.registry import (
    IfcKnowledgeRegistry,
    RegistryDriftError,
    check_registry_files,
)

if TYPE_CHECKING:
    from .index_models import PropertyFact
    from .repair_intent import PublicProvenance


class PropertyResolutionStatus(str, Enum):
    """Deterministic outcomes used by the exact-property resolver."""

    STANDARD_RESOLVED = "standard_resolved"
    CUSTOM_CONFIRMATION_REQUIRED = "custom_confirmation_required"
    CLARIFICATION_REQUIRED = "clarification_required"


@dataclass(frozen=True)
class ExactPropertyIntent:
    """A claim copied from public user text, never an authorization."""

    set_name: str | None
    property_name: str | None
    value: Any
    requested_value_type: str | None
    requested_unit: str | None
    scope: str | None
    source: "PublicProvenance"
    intent_kind: str = "pset_property"

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExactPropertyIntent":
        from .repair_intent import PublicProvenance

        return cls(
            set_name=_optional_text(value["set_name"]),
            property_name=_optional_text(value["property_name"]),
            value=value["value"],
            requested_value_type=_optional_text(value["requested_value_type"]),
            requested_unit=_optional_text(value["requested_unit"]),
            scope=_optional_text(value["scope"]),
            source=PublicProvenance.from_dict(value["source"]),
        )

    @property
    def missing_fields(self) -> tuple[str, ...]:
        missing: list[str] = []
        if self.set_name is None:
            missing.append("set_name")
        if self.property_name is None:
            missing.append("property_name")
        if self.value is None:
            missing.append("value")
        return tuple(missing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_kind": self.intent_kind,
            "set_name": self.set_name,
            "property_name": self.property_name,
            "value": self.value,
            "requested_value_type": self.requested_value_type,
            "requested_unit": self.requested_unit,
            "scope": self.scope,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class PropertyResolution:
    """Deterministic preview; custom candidates are never authorization."""

    status: PropertyResolutionStatus
    set_name: str | None
    property_name: str | None
    value: Any
    value_type: str | None
    unit: str | None
    scope: str
    classification: str | None
    applicable_classes: tuple[str, ...] = ()
    template_type: str | None = None
    unit_types: tuple[str, ...] = ()
    reason_code: str | None = None
    evidence: tuple[str, ...] = ()

    @property
    def requires_confirmation(self) -> bool:
        return self.status is not PropertyResolutionStatus.STANDARD_RESOLVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "set_name": self.set_name,
            "property_name": self.property_name,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "scope": self.scope,
            "classification": self.classification,
            "applicable_classes": list(self.applicable_classes),
            "template_type": self.template_type,
            "unit_types": list(self.unit_types),
            "reason_code": self.reason_code,
            "evidence": list(self.evidence),
        }


def resolve_exact_property_intent(
    intent: ExactPropertyIntent,
    *,
    target_ifc_class: str,
    existing_facts: Iterable["PropertyFact"],
    registry: IfcKnowledgeRegistry,
) -> PropertyResolution:
    """Resolve one scalar claim without aliases, fuzzy matching, RAG or I/O."""

    try:
        checked = check_registry_files()
    except RegistryDriftError as exc:
        return _clarification(intent, "REGISTRY_DRIFT", evidence=(str(exc),))

    evidence = tuple(f"registry:{name}:{digest}" for name, digest in checked.items())
    if intent.missing_fields:
        return _clarification(
            intent,
            "PROPERTY_FIELDS_REQUIRED",
            evidence=evidence + tuple(f"missing:{name}" for name in intent.missing_fields),
        )
    if not _is_valid_scalar(intent.value):
        return _clarification(intent, "PROPERTY_VALUE_INVALID", evidence=evidence)

    assert intent.set_name is not None
    assert intent.property_name is not None
    pset = registry.property_set(intent.set_name)
    if pset is None:
        return _resolve_custom(intent, registry, existing_facts, evidence)

    properties = pset.get("properties", {})
    property_definition = properties.get(intent.property_name)
    if property_definition is None:
        return _resolve_custom(intent, registry, existing_facts, evidence)

    applicable_classes = tuple(str(item) for item in pset.get("applicable_classes", ()))
    official_type = str(property_definition["data_type"])
    template_type = str(property_definition["template_type"])
    unit_types = tuple(str(item) for item in property_definition.get("unit_types", ()))
    base = {
        "set_name": intent.set_name,
        "property_name": intent.property_name,
        "value": intent.value,
        "value_type": official_type,
        "unit": intent.requested_unit,
        "scope": intent.scope or "occurrence_direct",
        "classification": "standard",
        "applicable_classes": applicable_classes,
        "template_type": template_type,
        "unit_types": unit_types,
        "evidence": evidence + (f"registry-property:{intent.set_name}.{intent.property_name}",),
    }
    if target_ifc_class not in applicable_classes:
        return PropertyResolution(
            status=PropertyResolutionStatus.CLARIFICATION_REQUIRED,
            reason_code="STANDARD_PROPERTY_INAPPLICABLE",
            **base,
        )
    if template_type != "TypePropertySingleValue":
        return PropertyResolution(
            status=PropertyResolutionStatus.CLARIFICATION_REQUIRED,
            reason_code="STANDARD_PROPERTY_TEMPLATE_UNSUPPORTED",
            **base,
        )
    if (
        intent.requested_value_type is not None
        and intent.requested_value_type != official_type
    ):
        return PropertyResolution(
            status=PropertyResolutionStatus.CLARIFICATION_REQUIRED,
            reason_code="REQUESTED_VALUE_TYPE_CONFLICT",
            **base,
        )
    if intent.requested_unit is not None and not unit_types:
        return PropertyResolution(
            status=PropertyResolutionStatus.CLARIFICATION_REQUIRED,
            reason_code="UNIT_NOT_APPLICABLE",
            **base,
        )
    if not _value_matches_ifc_type(intent.value, official_type):
        return PropertyResolution(
            status=PropertyResolutionStatus.CLARIFICATION_REQUIRED,
            reason_code="PROPERTY_VALUE_TYPE_INCOMPATIBLE",
            **base,
        )
    return PropertyResolution(
        status=PropertyResolutionStatus.STANDARD_RESOLVED,
        reason_code=None,
        **base,
    )


def _resolve_custom(
    intent: ExactPropertyIntent,
    registry: IfcKnowledgeRegistry,
    existing_facts: Iterable["PropertyFact"],
    evidence: tuple[str, ...],
) -> PropertyResolution:
    value_type = intent.requested_value_type or _safe_primitive_ifc_type(intent.value)
    matching_facts = tuple(
        fact
        for fact in existing_facts
        if fact.set_name == intent.set_name and fact.property_name == intent.property_name
    )
    fact_types = {fact.value_type for fact in matching_facts if fact.value_type}
    fact_units = {fact.unit for fact in matching_facts if fact.unit}
    if value_type is None and len(fact_types) == 1:
        value_type = next(iter(fact_types))
    unit = intent.requested_unit
    if unit is None and len(fact_units) == 1:
        unit = next(iter(fact_units))
    fact_evidence = tuple(
        f"existing-fact:{fact.provenance}" for fact in matching_facts
    )

    if value_type is None:
        return _clarification(
            intent,
            "CUSTOM_VALUE_TYPE_REQUIRED",
            classification="custom",
            evidence=evidence + fact_evidence,
        )
    declaration = registry.declaration(value_type)
    if declaration is None or declaration.get("kind") != "type":
        return _clarification(
            intent,
            "CUSTOM_VALUE_TYPE_UNKNOWN",
            classification="custom",
            value_type=value_type,
            evidence=evidence + fact_evidence,
        )
    if not _value_matches_ifc_type(intent.value, value_type):
        return _clarification(
            intent,
            "PROPERTY_VALUE_TYPE_INCOMPATIBLE",
            classification="custom",
            value_type=value_type,
            unit=unit,
            evidence=evidence + fact_evidence,
        )
    if _is_measure_type(value_type) and unit is None:
        return _clarification(
            intent,
            "CUSTOM_UNIT_REQUIRED",
            classification="custom",
            value_type=value_type,
            evidence=evidence + fact_evidence,
        )
    return PropertyResolution(
        status=PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED,
        set_name=intent.set_name,
        property_name=intent.property_name,
        value=intent.value,
        value_type=value_type,
        unit=unit,
        scope=intent.scope or "occurrence_direct",
        classification="custom",
        reason_code="UNKNOWN_EXACT_PROPERTY",
        evidence=evidence + fact_evidence,
    )


def _clarification(
    intent: ExactPropertyIntent,
    reason_code: str,
    *,
    classification: str | None = None,
    value_type: str | None = None,
    unit: str | None = None,
    evidence: tuple[str, ...] = (),
) -> PropertyResolution:
    return PropertyResolution(
        status=PropertyResolutionStatus.CLARIFICATION_REQUIRED,
        set_name=intent.set_name,
        property_name=intent.property_name,
        value=intent.value,
        value_type=value_type,
        unit=unit,
        scope=intent.scope or "occurrence_direct",
        classification=classification,
        reason_code=reason_code,
        evidence=evidence,
    )


def _is_valid_scalar(value: Any) -> bool:
    if value is None or isinstance(value, (list, tuple, dict, set)):
        return False
    return not isinstance(value, float) or math.isfinite(value)


def _safe_primitive_ifc_type(value: Any) -> str | None:
    if isinstance(value, bool):
        return "IfcBoolean"
    if isinstance(value, str):
        return "IfcLabel"
    if isinstance(value, int):
        return "IfcInteger"
    return None


def _is_measure_type(value_type: str) -> bool:
    return value_type.endswith("Measure")


def _value_matches_ifc_type(value: Any, value_type: str) -> bool:
    if not _is_valid_scalar(value):
        return False
    if value_type in {"IfcBoolean", "IfcLogical"}:
        return isinstance(value, bool)
    if value_type == "IfcInteger":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type in {
        "IfcLabel",
        "IfcText",
        "IfcIdentifier",
        "IfcGloballyUniqueId",
    }:
        return isinstance(value, str)
    if value_type == "IfcReal" or _is_measure_type(value_type):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, (str, bool, int, float))


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)


__all__ = [
    "ExactPropertyIntent",
    "PropertyResolution",
    "PropertyResolutionStatus",
    "resolve_exact_property_intent",
]
