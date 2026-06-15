from __future__ import annotations

from typing import Any


def extract_material_assignments(
    entity: Any,
    length_factor: float,
) -> tuple[list[dict[str, Any]], set[int]]:
    assignments: list[dict[str, Any]] = []
    represented_relations: set[int] = set()
    for relation in getattr(entity, "HasAssociations", ()) or ():
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        material = relation.RelatingMaterial
        if not material.is_a("IfcMaterialLayerSetUsage"):
            continue
        assignment = _layer_set_usage(material, length_factor)
        if assignment is None:
            continue
        assignments.append(assignment)
        represented_relations.add(relation.id())
    return assignments, represented_relations


def _layer_set_usage(
    usage: Any,
    length_factor: float,
) -> dict[str, Any] | None:
    layer_set = usage.ForLayerSet
    layers = []
    for layer in layer_set.MaterialLayers or ():
        material = layer.Material
        if material is None or not material.Name:
            return None
        thickness = layer.LayerThickness
        if thickness is None:
            return None
        layers.append(
            {
                "name": str(material.Name),
                "thickness": float(thickness) * length_factor,
            }
        )
    if not layers:
        return None
    return {
        "kind": "material_layer_set_usage",
        "layer_set_name": str(layer_set.LayerSetName or ""),
        "direction": usage.LayerSetDirection,
        "direction_sense": usage.DirectionSense,
        "offset_from_reference_line": float(usage.OffsetFromReferenceLine or 0.0)
        * length_factor,
        "layers": layers,
    }
