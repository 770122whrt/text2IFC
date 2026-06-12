"""BIM JSON 2.0 explicit and compiler-derived relationships."""

from __future__ import annotations

from typing import Any, Mapping

import ifcopenshell.api.owner

from .identity import global_id_for


def add_v2_relationships(
    ifc_file: Any,
    relationships: list[Mapping[str, Any]],
    entities: Mapping[str, Any],
) -> None:
    for record in relationships:
        ifc_class = record["ifc_class"]
        attributes = {
            name: entities[entity_id]
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
