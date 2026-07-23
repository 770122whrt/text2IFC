"""Versioned deterministic IFC Type templates used by bound ChangeSets."""

from __future__ import annotations

from typing import Any, Mapping


WINDOW_STYLE_TEMPLATE_VERSION = "0.1"


def ensure_bound_type(
    model: Any,
    assignment: Mapping[str, Any],
    *,
    owner_history: Any,
    operation_id: str,
) -> tuple[Any, bool]:
    global_id = str(assignment["value"])
    try:
        existing = model.by_guid(global_id)
    except RuntimeError:
        existing = None
    if existing is not None:
        if not existing.is_a("IfcTypeObject"):
            raise ValueError("BOUND_TYPE_CLASS_MISMATCH")
        return existing, False
    if assignment.get("source_kind") != "deterministic_policy":
        raise ValueError("BOUND_EXISTING_TYPE_NOT_FOUND")
    if assignment.get("value_type") != "IfcWindowStyle":
        raise ValueError("GENERATED_TYPE_TEMPLATE_UNSUPPORTED")
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


__all__ = ["WINDOW_STYLE_TEMPLATE_VERSION", "ensure_bound_type"]
