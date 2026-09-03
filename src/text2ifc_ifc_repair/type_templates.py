"""Versioned deterministic IFC Type templates used by bound ChangeSets."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .run_models import hash_json


WINDOW_STYLE_TEMPLATE_VERSION = "0.1"
DOOR_STYLE_TEMPLATE_VERSION = "0.1"


def ensure_bound_type(
    model: Any,
    assignment: Mapping[str, Any],
    *,
    owner_history: Any,
    operation_id: str,
    expected_ifc_class: str | None = None,
    generated_type_factory: Callable[..., Any] | None = None,
    factory_context: Mapping[str, Any] | None = None,
) -> tuple[Any, bool]:
    global_id = str(assignment["value"])
    try:
        existing = model.by_guid(global_id)
    except RuntimeError:
        existing = None
    if existing is not None:
        if not existing.is_a("IfcTypeObject"):
            raise ValueError("BOUND_TYPE_CLASS_MISMATCH")
        if expected_ifc_class is not None and not existing.is_a(
            expected_ifc_class
        ):
            raise ValueError("BOUND_TYPE_CLASS_MISMATCH")
        return existing, False
    if assignment.get("source_kind") not in {
        "deterministic_policy",
        "deterministic_derived",
    }:
        raise ValueError("BOUND_EXISTING_TYPE_NOT_FOUND")
    value_type = str(assignment.get("value_type"))
    if expected_ifc_class is not None and value_type != expected_ifc_class:
        raise ValueError("GENERATED_TYPE_TEMPLATE_UNSUPPORTED")
    if value_type not in {
        "IfcWindowStyle",
        "IfcDoorStyle",
        "IfcBeamType",
        "IfcColumnType",
    }:
        raise ValueError("GENERATED_TYPE_TEMPLATE_UNSUPPORTED")
    derivation = assignment.get("derivation")
    legacy_window_template = (
        value_type == "IfcWindowStyle"
        and assignment.get("source_kind") == "deterministic_policy"
        and not isinstance(derivation, Mapping)
    )
    if not legacy_window_template:
        if not isinstance(derivation, Mapping):
            raise ValueError("GENERATED_TYPE_DERIVATION_REQUIRED")
        _validate_generated_derivation(
            derivation, expected_ifc_class=value_type
        )
    if generated_type_factory is not None:
        return (
            generated_type_factory(
                model=model,
                global_id=global_id,
                owner_history=owner_history,
                operation_id=operation_id,
                derivation=derivation,
                context=dict(factory_context or {}),
            ),
            True,
        )
    if value_type != "IfcWindowStyle":
        raise ValueError("GENERATED_TYPE_FACTORY_REQUIRED")
    created = model.create_entity(
        "IfcWindowStyle",
        GlobalId=global_id,
        OwnerHistory=owner_history,
        Name=f"Text2IFC generated window type {operation_id}",
        Description=f"text2ifc deterministic template {WINDOW_STYLE_TEMPLATE_VERSION}",
        ConstructionType="NOTDEFINED",
        OperationType="NOTDEFINED",
        ParameterTakesPrecedence=False,
        Sizeable=False,
    )
    return created, True


def type_authority_fingerprint(type_object: Any) -> str:
    """Hash the Type-owned forward graph and associated material resources.

    `IfcRelDefinesByType.RelatedObjects` is intentionally excluded: binding a
    new occurrence may extend that inverse relationship, but it must not alter
    the selected Type, its maps, property sets or inherited materials.
    """

    if not type_object.is_a("IfcTypeObject"):
        raise ValueError("TYPE_AUTHORITY_FINGERPRINT_CLASS_INVALID")
    material_resources = [
        relation.RelatingMaterial
        for relation in getattr(type_object, "HasAssociations", ())
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    payload = {
        "type_forward_graph": _forward_entity_payload(type_object, seen=set()),
        "associated_materials": sorted(
            (
                _forward_entity_payload(resource, seen=set())
                for resource in material_resources
            ),
            key=lambda item: hash_json(item),
        ),
    }
    return hash_json(payload)


def _forward_entity_payload(value: Any, *, seen: set[int]) -> Any:
    if hasattr(value, "is_a") and hasattr(value, "get_info"):
        identifier = int(value.id())
        if identifier in seen:
            return {
                "ifc_class": value.is_a(),
                "global_id": str(getattr(value, "GlobalId", "")),
                "cycle": True,
            }
        nested_seen = {*seen, identifier}
        info = value.get_info(include_identifier=False, recursive=False)
        return {
            str(key): _forward_entity_payload(item, seen=nested_seen)
            for key, item in sorted(info.items())
            if key != "type"
        } | {"ifc_class": value.is_a()}
    if isinstance(value, Mapping):
        return {
            str(key): _forward_entity_payload(item, seen=seen)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_forward_entity_payload(item, seen=seen) for item in value]
    return value


def _validate_generated_derivation(
    derivation: Mapping[str, Any],
    *,
    expected_ifc_class: str,
) -> None:
    if derivation.get("ifc_class") != expected_ifc_class:
        raise ValueError("GENERATED_TYPE_DERIVATION_CLASS_MISMATCH")
    template_id = str(derivation.get("template_id", ""))
    template_version = str(derivation.get("template_version", ""))
    formal = derivation.get("formal_attributes")
    template = derivation.get("template")
    digest = str(derivation.get("template_digest", ""))
    if (
        not template_id
        or not template_version
        or not isinstance(formal, Mapping)
        or not isinstance(template, Mapping)
        or not digest.startswith("sha256:")
    ):
        raise ValueError("GENERATED_TYPE_DERIVATION_INVALID")
    expected = hash_json(
        {
            "template_id": template_id,
            "template_version": template_version,
            "ifc_class": expected_ifc_class,
            "formal_attributes": dict(formal),
            "template": dict(template),
        }
    )
    if digest != expected:
        raise ValueError("GENERATED_TYPE_TEMPLATE_DIGEST_MISMATCH")
    operation = formal.get("operation_type")
    if expected_ifc_class == "IfcDoorStyle" and operation not in {
        "SINGLE_SWING_LEFT",
        "SINGLE_SWING_RIGHT",
        "NOTDEFINED",
    }:
        raise ValueError("GENERATED_DOOR_OPERATION_UNSUPPORTED")


__all__ = [
    "DOOR_STYLE_TEMPLATE_VERSION",
    "WINDOW_STYLE_TEMPLATE_VERSION",
    "ensure_bound_type",
    "type_authority_fingerprint",
]
