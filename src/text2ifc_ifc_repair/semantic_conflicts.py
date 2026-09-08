"""Read-only exact-Type request compatibility for RepairIntent 0.10.

No Type or material mutation is authorized here. A null property scope retains
exact-Type values; an explicitly occurrence_direct property may override them.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import ifcopenshell
from text2ifc_presentation import type_surface_styles


def open_verified_source(path: Path | str | None, expected_sha: str) -> Any:
    if path is None:
        raise ValueError("EXACT_TYPE_SOURCE_REQUIRED")
    raw = Path(path).read_bytes()
    if "sha256:" + hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("EXACT_TYPE_SOURCE_CHANGED")
    return ifcopenshell.file.from_string(raw.decode("utf-8"))


def type_request_conflict(model: Any, type_id: str, operation: Any) -> str | None:
    type_object = model.by_guid(type_id)
    materials = [rel.RelatingMaterial for rel in type_object.HasAssociations
                 if rel.is_a("IfcRelAssociatesMaterial")]
    for claim in operation.attribute_intents:
        if claim.intent_kind != "material":
            continue
        matches = [item for item in model.by_type("IfcMaterial") if item.Name == claim.value]
        if len(matches) > 1:
            return "EXACT_TYPE_MATERIAL_IDENTITY_AMBIGUOUS"
        if materials and (len(materials) != 1 or not matches or materials[0] != matches[0]):
            return "EXACT_TYPE_MATERIAL_CONFLICT"
    if operation.appearance_intent is not None:
        expected = tuple(float(getattr(operation.appearance_intent, key)) for key in ("red", "green", "blue"))
        for style in type_surface_styles(type_object):
            colors = [item.SurfaceColour for item in style.Styles if item.is_a("IfcSurfaceStyleShading")]
            if not colors or any(any(abs(float(getattr(color, channel)) - value) > 1.e-6 for channel, value in zip(("Red", "Green", "Blue"), expected)) for color in colors):
                return "EXACT_TYPE_APPEARANCE_CONFLICT"
    return None


def type_property_conflict(model: Any, type_id: str, claim: Any, *, explicit_scope: str | None) -> str | None:
    if explicit_scope == "occurrence_direct":
        return None
    values = []
    for pset in tuple(model.by_guid(type_id).HasPropertySets or ()):
        if pset.is_a("IfcPropertySet") and pset.Name == claim.set_name:
            for prop in pset.HasProperties:
                if prop.Name == claim.property_name:
                    if not prop.is_a("IfcPropertySingleValue") or prop.NominalValue is None:
                        return "EXACT_TYPE_PROPERTY_CONFLICT"
                    values.append((prop.NominalValue.wrappedValue, prop.NominalValue.is_a()))
    if len(values) > 1 or (values and (values[0][0] != claim.value or (claim.requested_value_type and values[0][1] != claim.requested_value_type))):
        return "EXACT_TYPE_PROPERTY_CONFLICT"
    return None
