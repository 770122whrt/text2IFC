"""Preparation evidence, not an experiment scorer or a production admission."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
import ifcopenshell.validate

from text2ifc_ifc_repair.compare import normalized_model_diff


def native_validation(model: Any) -> dict[str, Any]:
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    diagnostics = []
    for entry in logger.statements:
        instance = entry.get("instance")
        diagnostics.append({
            "level": str(entry.get("level", "")),
            "attribute": str(entry.get("attribute", "")),
            "instance": str(instance),
            "message": str(entry.get("message", "")),
        })
    return {"validator": "ifcopenshell.validate", "version": ifcopenshell.version, "express_rules": True, "diagnostic_count": len(diagnostics), "passed": not diagnostics, "diagnostics": diagnostics}


def geometry_snapshot(entity: Any) -> dict[str, Any]:
    scale = ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000
    result = {"guid": entity.GlobalId, "class": entity.is_a(), "name": entity.Name, "project_unit_to_mm": scale}
    for name in ("OverallWidth", "OverallHeight"):
        value = getattr(entity, name, None)
        if value is not None:
            result[f"{name}_mm"] = float(value) * scale
    if not entity.Representation:
        result["geometry_status"] = "no_representation"
        return result
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        vertices = shape.geometry.verts
        if not vertices:
            raise ValueError("empty geometry")
        result["geometry_status"] = "available"
        result["bounds_world_m"] = [[min(vertices[axis::3]), max(vertices[axis::3])] for axis in range(3)]
    except (RuntimeError, ValueError) as error:
        result["geometry_status"] = "failed"
        result["geometry_error"] = str(error)
    return result


def relation_evidence(before: Any, after: Any, definition: dict[str, Any], opening_guid: str) -> list[dict[str, Any]]:
    """Count semantic membership edges, not shared relationship entities."""
    target_guid = definition["damage"]["target_guid"]
    attributes = {
        "IfcRelFillsElement": ("RelatedBuildingElement", "RelatingOpeningElement", target_guid),
        "IfcRelVoidsElement": ("RelatedOpeningElement", "RelatingBuildingElement", opening_guid),
        "IfcRelContainedInSpatialStructure": ("RelatedElements", "RelatingStructure", target_guid),
        "IfcRelDefinesByType": ("RelatedObjects", "RelatingType", target_guid),
    }
    evidence = []
    for requirement in definition["task"]["required_relations"]:
        kind = requirement["ifc_class"]
        if kind not in attributes:
            evidence.append({"id": requirement["id"], "verified": False, "reason": "unsupported relation obligation"})
            continue
        member_attribute, parent_attribute, guid = attributes[kind]

        def edges(model):
            result = []
            for relation in model.by_type(kind):
                members = getattr(relation, member_attribute)
                if not isinstance(members, tuple):
                    members = (members,)
                for member in members:
                    if member.GlobalId == guid:
                        result.append({"relation_guid": relation.GlobalId, "member_guid": guid, "parent_guid": getattr(relation, parent_attribute).GlobalId})
            return result

        original, damaged = edges(before), edges(after)
        evidence.append({"id": requirement["id"], "ifc_class": kind, "before": original, "after": damaged, "verified": len(original) == 1 and not damaged})
    return evidence


def inspect_damage(reference: Path, damaged: Path, definition: dict[str, Any]) -> dict[str, Any]:
    before = ifcopenshell.open(str(reference))
    after = ifcopenshell.open(str(damaged))
    target = before.by_guid(definition["damage"]["target_guid"])
    opening = target.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    expected_removed = {target.GlobalId}
    damage = definition["damage"]
    if damage["kind"] == "window" or not damage.get("preserve_opening", False):
        expected_removed.add(opening.GlobalId)
    before_products = {p.GlobalId: p for p in before.by_type("IfcProduct")}
    after_products = {p.GlobalId: p for p in after.by_type("IfcProduct")}
    changes = normalized_model_diff(before, after)
    modified_products = [row for row in changes["modified"] if row["global_id"] in before_products]
    # Deleting a void changes a relation, not the wall's intrinsic attributes.
    # Exempting the host here would also permit unrelated thickness/placement edits.
    unexpected_modified = modified_products
    references = [after.by_guid(guid) for guid in definition["task"].get("reference_guids", [])]
    source_validation = native_validation(before)
    damaged_validation = native_validation(after)
    def signatures(report):
        return Counter((row["level"], row["attribute"], row["instance"], row["message"]) for row in report["diagnostics"])
    new_diagnostics = sum((signatures(damaged_validation) - signatures(source_validation)).values())
    actual_removed = set(before_products) - set(after_products)
    actual_created = set(after_products) - set(before_products)
    after_openings = {p.GlobalId: p for p in after.by_type("IfcOpeningElement")}
    retained_opening_ok = True
    if damage["kind"] == "door" and damage["preserve_opening"]:
        kept = after_openings.get(opening.GlobalId)
        retained_opening_ok = kept is not None and len(kept.HasFillings) == 0 and len(kept.VoidsElements) == 1
    snapshots = {
        "target": geometry_snapshot(target), "opening": geometry_snapshot(opening),
        "host": geometry_snapshot(wall), "damaged_host": geometry_snapshot(after.by_guid(wall.GlobalId)),
    }
    if opening.GlobalId in after_openings:
        snapshots["retained_opening"] = geometry_snapshot(after_openings[opening.GlobalId])
    reference_snapshots = [geometry_snapshot(p) for p in references]
    geometry_available = all(row["geometry_status"] == "available" for row in [*snapshots.values(), *reference_snapshots])
    relation_rows = relation_evidence(before, after, definition, opening.GlobalId)
    checks = {
        "schema_preserved": before.schema == after.schema == "IFC2X3",
        "only_expected_products_removed": actual_removed == expected_removed,
        "no_products_created": not actual_created,
        "no_unexpected_modified_products": not unexpected_modified,
        "retained_opening_empty_and_hosted": retained_opening_ok,
        "no_new_native_diagnostics": new_diagnostics == 0,
        "source_native_validation_passed": source_validation["passed"],
        "damaged_native_validation_passed": damaged_validation["passed"],
        "required_geometry_available": geometry_available,
        "required_relation_edges_verified": all(row["verified"] for row in relation_rows),
    }
    return {
        "purpose": "development_preparation_only", "checks": checks,
        "counts_before": dict(sorted(Counter(p.is_a() for p in before_products.values()).items())),
        "counts_after": dict(sorted(Counter(p.is_a() for p in after_products.values()).items())),
        "removed_product_guids": sorted(actual_removed), "created_product_guids": sorted(actual_created),
        "root_diff": changes, "unexpected_modified_products": unexpected_modified,
        "source_validation": source_validation, "damaged_validation": damaged_validation,
        "new_native_diagnostic_count": new_diagnostics,
        **snapshots, "public_references": reference_snapshots, "required_relation_evidence": relation_rows,
        "unit_note": "Geometry bounds are metres; OverallWidth/Height are normalized to mm from actual IFC units. The legacy mutation opening dimensions_mm field is not used.",
    }
