"""BIM JSON 2.0 explicit and compiler-derived relationships."""

from __future__ import annotations

from typing import Any, Mapping

import ifcopenshell.api.owner
from ifcopenshell.api.type.assign_type import assign_type

from .identity import global_id_for


def add_v2_relationships(
    ifc_file: Any,
    relationships: list[Mapping[str, Any]],
    entities: Mapping[str, Any],
) -> None:
    for record in relationships:
        ifc_class = record["ifc_class"]
        if ifc_class == "IfcRelAggregates":
            attributes = record["attributes"]
            relating_object = entities[attributes["RelatingObject"]]
            related_objects = [
                entities[entity_id]
                for entity_id in attributes["RelatedObjects"]
            ]
            if _aggregate_already_assigned(relating_object, related_objects):
                continue
        if ifc_class == "IfcRelDefinesByType":
            attributes = record["attributes"]
            assign_type(
                ifc_file,
                related_objects=[
                    entities[entity_id]
                    for entity_id in attributes["RelatedObjects"]
                ],
                relating_type=entities[attributes["RelatingType"]],
                should_map_representations=False,
            )
            continue
        if ifc_class == "IfcRelConnectsPathElements":
            attributes = record["attributes"]
            ifc_file.create_entity(
                ifc_class,
                GlobalId=record.get("global_id")
                or global_id_for(
                    "bim-json/2.0", ifc_class, record["id"]
                ),
                OwnerHistory=ifcopenshell.api.owner.create_owner_history(ifc_file),
                Name=None,
                Description=None,
                ConnectionGeometry=None,
                RelatingElement=entities[attributes["RelatingElement"]],
                RelatedElement=entities[attributes["RelatedElement"]],
                RelatingPriorities=attributes["RelatingPriorities"],
                RelatedPriorities=attributes["RelatedPriorities"],
                RelatedConnectionType=attributes["RelatedConnectionType"],
                RelatingConnectionType=attributes["RelatingConnectionType"],
            )
            continue
        attributes = {
            name: (
                [entities[item_id] for item_id in entity_id]
                if isinstance(entity_id, list)
                else entities[entity_id]
            )
            for name, entity_id in record["attributes"].items()
        }
        ifc_file.create_entity(
            ifc_class,
            GlobalId=record.get("global_id")
            or global_id_for(
                "bim-json/2.0", ifc_class, record["id"]
            ),
            OwnerHistory=ifcopenshell.api.owner.create_owner_history(ifc_file),
            Name=None,
            Description=None,
            **attributes,
        )


def _aggregate_already_assigned(relating_object: Any, related_objects: list[Any]) -> bool:
    return all(
        any(
            relation.RelatingObject == relating_object
            for relation in getattr(related_object, "Decomposes", ())
        )
        for related_object in related_objects
    )
