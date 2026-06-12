"""Explicit semantic relationship extraction."""

from __future__ import annotations

from typing import Any


_ENDPOINTS = {
    "IfcRelVoidsElement": (
        "RelatingBuildingElement",
        "RelatedOpeningElement",
    ),
    "IfcRelFillsElement": (
        "RelatingOpeningElement",
        "RelatedBuildingElement",
    ),
}

_COMPILER_DERIVED = {
    "IfcRelAggregates",
    "IfcRelContainedInSpatialStructure",
    "IfcRelDefinesByProperties",
}


def explicit_relationship(relation, entity_ids: dict[int, str]):
    names = _ENDPOINTS.get(relation.is_a())
    if names is None:
        return None
    attributes: dict[str, Any] = {}
    for name in names:
        endpoint = getattr(relation, name)
        endpoint_id = entity_ids.get(endpoint.id())
        if endpoint_id is None:
            return None
        attributes[name] = endpoint_id
    return attributes


def relationship_category(ifc_class: str) -> str:
    if ifc_class in _ENDPOINTS or ifc_class in _COMPILER_DERIVED:
        return "represented"
    return "reported"


def relationship_loss_kind(ifc_class: str) -> str:
    if ifc_class == "IfcRelAssociatesMaterial":
        return "MATERIAL_ASSOCIATION"
    if ifc_class == "IfcRelDefinesByType":
        return "TYPE_RELATIONSHIP"
    if ifc_class.startswith("IfcRelConnects"):
        return "CONNECTION_RELATIONSHIP"
    return "UNSUPPORTED_RELATIONSHIP"
