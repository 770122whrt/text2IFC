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
    if relation.is_a() == "IfcRelDefinesByType":
        type_id = entity_ids.get(relation.RelatingType.id())
        related_ids = [
            entity_ids.get(item.id()) for item in relation.RelatedObjects
        ]
        if type_id is None or any(item is None for item in related_ids):
            return None
        return {
            "RelatedObjects": sorted(related_ids),
            "RelatingType": type_id,
        }
    if relation.is_a() == "IfcRelConnectsPathElements":
        relating_id = entity_ids.get(relation.RelatingElement.id())
        related_id = entity_ids.get(relation.RelatedElement.id())
        if relating_id is None or related_id is None:
            return None
        if relation.ConnectionGeometry is not None:
            return None
        return {
            "RelatingElement": relating_id,
            "RelatedElement": related_id,
            "RelatingPriorities": list(relation.RelatingPriorities or ()),
            "RelatedPriorities": list(relation.RelatedPriorities or ()),
            "RelatingConnectionType": relation.RelatingConnectionType,
            "RelatedConnectionType": relation.RelatedConnectionType,
        }
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
    if (
        ifc_class in _ENDPOINTS
        or ifc_class == "IfcRelDefinesByType"
        or ifc_class == "IfcRelConnectsPathElements"
        or ifc_class in _COMPILER_DERIVED
    ):
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
