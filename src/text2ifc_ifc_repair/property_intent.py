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
from .run_models import hash_json

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


@dataclass(frozen=True)
class PropertyConfirmationPreview:
    operation_id: str
    target_global_id: str
    request_hash: str
    model_fingerprint: str
    set_name: str
    property_name: str
    value: Any
    value_type: str
    unit: str | None
    scope: str
    source: "PublicProvenance"
    preview_hash: str

    @classmethod
    def create(
        cls,
        resolution: PropertyResolution,
        *,
        operation_id: str,
        target_global_id: str,
        request_hash: str,
        model_fingerprint: str,
        source: "PublicProvenance",
    ) -> "PropertyConfirmationPreview":
        if (
            resolution.status is not PropertyResolutionStatus.CUSTOM_CONFIRMATION_REQUIRED
            or resolution.set_name is None
            or resolution.property_name is None
            or resolution.value_type is None
            or resolution.scope != "occurrence_direct"
        ):
            raise ValueError("PROPERTY_CONFIRMATION_PREVIEW_NOT_ALLOWED")
        payload = {
            "operation_id": operation_id,
            "target_global_id": target_global_id,
            "request_hash": request_hash,
            "model_fingerprint": model_fingerprint,
            "set_name": resolution.set_name,
            "property_name": resolution.property_name,
            "value": resolution.value,
            "value_type": resolution.value_type,
            "unit": resolution.unit,
            "scope": resolution.scope,
            "source": source.to_dict(),
        }
        return cls(
            operation_id=operation_id,
            target_global_id=target_global_id,
            request_hash=request_hash,
            model_fingerprint=model_fingerprint,
            set_name=resolution.set_name,
            property_name=resolution.property_name,
            value=resolution.value,
            value_type=resolution.value_type,
            unit=resolution.unit,
            scope=resolution.scope,
            source=source,
            preview_hash=hash_json(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "target_global_id": self.target_global_id,
            "request_hash": self.request_hash,
            "model_fingerprint": self.model_fingerprint,
            "set_name": self.set_name,
            "property_name": self.property_name,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "scope": self.scope,
            "source": self.source.to_dict(),
            "preview_hash": self.preview_hash,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PropertyConfirmationPreview":
        from .repair_intent import PublicProvenance

        preview = cls(
            operation_id=str(value["operation_id"]),
            target_global_id=str(value["target_global_id"]),
            request_hash=str(value["request_hash"]),
            model_fingerprint=str(value["model_fingerprint"]),
            set_name=str(value["set_name"]),
            property_name=str(value["property_name"]),
            value=value["value"],
            value_type=str(value["value_type"]),
            unit=None if value["unit"] is None else str(value["unit"]),
            scope=str(value["scope"]),
            source=PublicProvenance.from_dict(value["source"]),
            preview_hash=str(value["preview_hash"]),
        )
        expected = hash_json({key: item for key, item in preview.to_dict().items() if key != "preview_hash"})
        if preview.preview_hash != expected:
            raise ValueError("PROPERTY_CONFIRMATION_PREVIEW_HASH_MISMATCH")
        return preview


@dataclass(frozen=True)
class AuthorizedPropertyFact:
    operation_id: str
    target_global_id: str
    request_hash: str
    model_fingerprint: str
    set_name: str
    property_name: str
    value: Any
    value_type: str
    unit: str | None
    ownership: str
    source: "PublicProvenance"
    confirmation_ref: str | None
    confirmation_hash: str | None
    classification: str

    def __post_init__(self) -> None:
        if self.ownership != "occurrence_direct":
            raise ValueError("PROPERTY_OWNERSHIP_NOT_AUTHORIZED")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "kind": "authorized_property_fact",
            "operation_id": self.operation_id,
            "target_global_id": self.target_global_id,
            "request_hash": self.request_hash,
            "model_fingerprint": self.model_fingerprint,
            "set_name": self.set_name,
            "property_name": self.property_name,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "ownership": self.ownership,
            "source": self.source.to_dict(),
            "confirmation_ref": self.confirmation_ref,
            "confirmation_hash": self.confirmation_hash,
            "classification": self.classification,
        }
        payload["property_hash"] = hash_json(
            {key: value for key, value in payload.items() if key != "property_hash"}
        )
        return payload


def authorize_custom_property(
    preview: PropertyConfirmationPreview,
    *,
    answer_kind: str,
    preview_hash: str,
    confirmation_ref: str,
) -> AuthorizedPropertyFact:
    if preview_hash != preview.preview_hash:
        raise ValueError("PROPERTY_CONFIRMATION_HASH_MISMATCH")
    if answer_kind != "confirm_property":
        raise ValueError("PROPERTY_CONFIRMATION_REQUIRED")
    return AuthorizedPropertyFact(
        operation_id=preview.operation_id,
        target_global_id=preview.target_global_id,
        request_hash=preview.request_hash,
        model_fingerprint=preview.model_fingerprint,
        set_name=preview.set_name,
        property_name=preview.property_name,
        value=preview.value,
        value_type=preview.value_type,
        unit=preview.unit,
        ownership=preview.scope,
        source=preview.source,
        confirmation_ref=confirmation_ref,
        confirmation_hash=preview.preview_hash,
        classification="custom_confirmed",
    )


def authorize_standard_property(
    resolution: PropertyResolution,
    *,
    operation_id: str,
    target_global_id: str,
    request_hash: str,
    model_fingerprint: str,
    source: "PublicProvenance",
) -> AuthorizedPropertyFact:
    if (
        resolution.status is not PropertyResolutionStatus.STANDARD_RESOLVED
        or resolution.set_name is None
        or resolution.property_name is None
        or resolution.value_type is None
    ):
        raise ValueError("STANDARD_PROPERTY_NOT_RESOLVED")
    return AuthorizedPropertyFact(
        operation_id=operation_id,
        target_global_id=target_global_id,
        request_hash=request_hash,
        model_fingerprint=model_fingerprint,
        set_name=resolution.set_name,
        property_name=resolution.property_name,
        value=resolution.value,
        value_type=resolution.value_type,
        unit=resolution.unit,
        ownership=resolution.scope,
        source=source,
        confirmation_ref=None,
        confirmation_hash=None,
        classification="standard",
    )


def normalize_property_scope(scope: str | None) -> str:
    normalized = scope or "occurrence_direct"
    if normalized == "type_owned":
        raise ValueError("TYPE_PROPERTY_MUTATION_DEFERRED")
    if normalized != "occurrence_direct":
        raise ValueError("PROPERTY_SCOPE_UNSUPPORTED")
    return normalized


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
    "AuthorizedPropertyFact",
    "ExactPropertyIntent",
    "PropertyConfirmationPreview",
    "PropertyResolution",
    "PropertyResolutionStatus",
    "authorize_custom_property",
    "authorize_standard_property",
    "normalize_property_scope",
    "resolve_exact_property_intent",
]
