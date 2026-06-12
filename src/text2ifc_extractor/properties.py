"""Native attribute and property-set extraction."""

from __future__ import annotations

from numbers import Number
from typing import Any

import ifcopenshell.util.element

from text2ifc_knowledge.registry import load_ifc2x3_registry


_SKIP_ATTRIBUTES = {
    "GlobalId",
    "OwnerHistory",
    "ObjectPlacement",
    "Representation",
}


def _primitive(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Number):
        return value
    if isinstance(value, tuple):
        converted = [_primitive(item) for item in value]
        if all(item is not None for item in converted):
            return converted
    return None


def native_attributes(entity) -> dict[str, Any]:
    registry = load_ifc2x3_registry()
    declaration = registry.declaration(entity.is_a())
    attributes: dict[str, Any] = {}
    if declaration is None:
        return attributes
    for record in declaration["attributes"]:
        name = record["name"]
        if name in _SKIP_ATTRIBUTES:
            continue
        value = _primitive(getattr(entity, name, None))
        if value is not None:
            attributes[name] = value
    return attributes


def property_sets(entity) -> tuple[dict[str, dict[str, Any]], int, int]:
    registry = load_ifc2x3_registry()
    raw = ifcopenshell.util.element.get_psets(entity, psets_only=True)
    output: dict[str, dict[str, Any]] = {}
    represented = 0
    reported = 0
    for source_name in sorted(raw):
        values = raw[source_name]
        target_name = (
            source_name
            if registry.property_set(source_name) is not None
            else f"custom:{source_name}"
        )
        clean: dict[str, Any] = {}
        for name in sorted(values):
            if name == "id":
                continue
            value = _primitive(values[name])
            if value is None:
                reported += 1
            else:
                clean[name] = value
                represented += 1
        if clean:
            output[target_name] = clean
    return output, represented, reported
