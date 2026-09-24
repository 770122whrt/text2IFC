"""Frozen Generation material scope matrix; identity is never inferred from names."""
import math

from .validation import ValidationIssue


SINGLE_OCCURRENCES = {"IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcRoof", "IfcPlate", "IfcCovering", "IfcBeam", "IfcColumn", "IfcDoor", "IfcWindow", "IfcMember", "IfcRailing", "IfcStair", "IfcStairFlight", "IfcCurtainWall"}
TYPE_OCCURRENCE = {"IfcWallType": "IfcWall", "IfcSlabType": "IfcSlab", "IfcPlateType": "IfcPlate", "IfcCoveringType": "IfcCovering", "IfcBeamType": "IfcBeam", "IfcColumnType": "IfcColumn", "IfcDoorStyle": "IfcDoor", "IfcWindowStyle": "IfcWindow", "IfcMemberType": "IfcMember", "IfcRailingType": "IfcRailing", "IfcStairFlightType": "IfcStairFlight", "IfcCurtainWallType": "IfcCurtainWall"}
LAYER_TYPES = {"IfcWallType", "IfcSlabType", "IfcPlateType", "IfcCoveringType"}
LAYER_OCCURRENCES = {"IfcWall": "AXIS2", "IfcWallStandardCase": "AXIS2", "IfcSlab": "AXIS3", "IfcRoof": "AXIS3", "IfcPlate": "AXIS3", "IfcCovering": "AXIS3"}


def validate_materials(document):
    issues = []
    records = {r["id"]: r for r in document.get("entities", [])}
    type_ids = {entity_id: r['attributes']['RelatingType']
                for r in document.get('relationships', [])
                if r.get('ifc_class') == 'IfcRelDefinesByType'
                and isinstance(r['attributes'].get('RelatingType'), str)
                and isinstance(r['attributes'].get('RelatedObjects'), list)
                for entity_id in r['attributes']['RelatedObjects'] if isinstance(entity_id, str)}
    for index, record in enumerate(document.get("entities", [])):
        assignments = record.get("materials", [])
        if not assignments and record["ifc_class"] in LAYER_OCCURRENCES:
            inherited = records.get(type_ids.get(record["id"]), {}).get("materials", [])
            if (document.get("schema_version") == "bim-json/2.5"
                    and record["ifc_class"] == "IfcWallStandardCase" and inherited
                    and inherited[0]["kind"] == "material_list"):
                issues.append(ValidationIssue("UNSUPPORTED_MATERIAL_ASSIGNMENT",
                    f"/entities/{index}/materials", "IfcWallStandardCase cannot inherit a non-layered material list."))
            if inherited and inherited[0]["kind"] == "material_layer_set":
                assignments = [{**inherited[0], "kind": "material_layer_set_usage", "direction": LAYER_OCCURRENCES[record["ifc_class"]]}]
        path = f"/entities/{index}/materials"
        if len(assignments) > 1:
            issues.append(ValidationIssue("MULTIPLE_MATERIAL_ASSIGNMENTS", path, "An object supports at most one material attachment."))
        for assignment in assignments:
            cls = record["ifc_class"]
            kind = assignment["kind"]
            supported = (kind == "single_material" and cls in SINGLE_OCCURRENCES | TYPE_OCCURRENCE.keys()) or (kind == "material_layer_set" and cls in LAYER_TYPES) or (kind == "material_layer_set_usage" and cls in LAYER_OCCURRENCES)
            supported = supported or (document.get("schema_version") == "bim-json/2.5"
                and kind == "material_list"
                and cls in (SINGLE_OCCURRENCES | TYPE_OCCURRENCE.keys()) - {"IfcWallStandardCase"})
            if not supported:
                issues.append(ValidationIssue("UNSUPPORTED_MATERIAL_ASSIGNMENT", path, f"{kind} is not supported on {cls}."))
                continue
            if kind != "material_layer_set_usage":
                continue
            rep = record["attributes"].get("Representation", {})
            expected_axis = LAYER_OCCURRENCES[cls]
            direction = rep.get("direction", [])
            if rep.get("kind") != "extruded_profile" or direction[:2] != [0, 0] or len(direction) != 3 or direction[2] <= 0:
                issues.append(ValidationIssue("UNSUPPORTED_LAYER_GEOMETRY", path, "Layers require positive local Z extrusion."))
                continue
            if expected_axis == "AXIS2":
                profile = rep.get("profile", {})
                thickness = profile.get("y") if profile.get("kind") == "rectangle" else None
                if document.get("schema_version") in {"bim-json/2.4", "bim-json/2.5"}:
                    from .polygon_wall import wall_section
                    try:
                        _, low, high, _, _ = wall_section(rep)
                        thickness = high - low
                    except (KeyError, TypeError, ValueError, IndexError) as exc:
                        issues.append(ValidationIssue("UNSUPPORTED_LAYER_GEOMETRY", path, str(exc)))
                        continue
            else:
                thickness = rep.get("depth")
            total = sum(layer["thickness"] for layer in assignment["layers"])
            tolerance = 0.1 if document.get("schema_version") in {"bim-json/2.4", "bim-json/2.5"} else 1e-6
            if thickness is None or not math.isclose(total, thickness, abs_tol=tolerance, rel_tol=0):
                issues.append(ValidationIssue("MATERIAL_LAYER_THICKNESS_MISMATCH", path, "Layer thickness sum must equal the declared wall thickness or slab extrusion depth."))
            if assignment["direction"] != expected_axis:
                issues.append(ValidationIssue("MATERIAL_LAYER_DIRECTION_MISMATCH", path, f"{cls} requires {expected_axis}."))
    return issues
