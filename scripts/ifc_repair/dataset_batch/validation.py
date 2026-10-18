"""Pinned native validation and independent recorded-change checks."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.validate


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def program_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def native_validate(model_or_path: Any) -> dict:
    started = time.monotonic()
    logger = ifcopenshell.validate.json_logger()
    try:
        model = ifcopenshell.open(str(model_or_path)) if isinstance(model_or_path, (str, Path)) else model_or_path
        ifcopenshell.validate.validate(model, logger, express_rules=True)
        findings = [{"level": str(row.get("level", "error")), "attribute": str(row.get("attribute", "")), "message": str(row.get("message", "")), "instance": str(row.get("instance", ""))[:800]} for row in logger.statements]
        return {"passed": model.schema == "IFC2X3" and not findings, "schema": model.schema, "express_rules": True, "ifcopenshell_version": ifcopenshell.version, "finding_count": len(findings), "findings": findings, "elapsed_seconds": round(time.monotonic() - started, 3)}
    except Exception as exc:
        return {"passed": False, "express_rules": True, "ifcopenshell_version": ifcopenshell.version, "finding_count": 1, "findings": [{"message": f"{type(exc).__name__}: {exc}"}], "elapsed_seconds": round(time.monotonic() - started, 3)}


def _plain(value):
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items() if k != "id"}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    return value


def product_state(model) -> dict:
    """Forward graph hashes plus inverse semantic edges, independent of STEP ids."""
    cache = {}
    active = set()

    def digest(value):
        if isinstance(value, ifcopenshell.entity_instance):
            if not value.id():
                return [value.is_a(), digest(value.wrappedValue)]
            if value.id() in cache:
                return cache[value.id()]
            if value.id() in active:
                return ["cycle", value.is_a(), getattr(value, "GlobalId", None)]
            active.add(value.id())
            token = hashlib.sha256(json.dumps([value.is_a(), [digest(v) for v in value]], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            active.remove(value.id())
            cache[value.id()] = token
            return token
        if isinstance(value, (list, tuple)):
            return [digest(v) for v in value]
        return value

    states = {}
    for product in model.by_type("IfcProduct"):
        identity = str(product.GlobalId)
        edges = {}
        for name in ("ContainedInStructure", "FillsVoids", "VoidsElements", "HasOpenings"):
            rows = []
            for rel in getattr(product, name, ()) or ():
                for attr in ("RelatingStructure", "RelatingOpeningElement", "RelatingBuildingElement", "RelatedOpeningElement"):
                    other = getattr(rel, attr, None)
                    if other is not None and other != product:
                        rows.append((rel.is_a(), attr, str(other.GlobalId)))
            edges[name] = sorted(rows)
        edges["types"] = sorted((str(rel.RelatingType.GlobalId), digest(rel.RelatingType)) for rel in getattr(product, "IsDefinedBy", ()) if rel.is_a("IfcRelDefinesByType"))
        edges["materials"] = sorted(str(digest(rel.RelatingMaterial)) for rel in getattr(product, "HasAssociations", ()) if rel.is_a("IfcRelAssociatesMaterial"))
        typed = []
        for rel in getattr(product, "IsDefinedBy", ()):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            definition = rel.RelatingPropertyDefinition
            if not definition.is_a("IfcPropertySet"):
                typed.append({"class": definition.is_a(), "graph": digest(definition)})
                continue
            properties = []
            for prop in definition.HasProperties:
                if prop.is_a("IfcPropertySingleValue"):
                    value = prop.NominalValue
                    properties.append({"name": prop.Name, "class": prop.is_a(), "description": prop.Description, "value_type": value.is_a() if value else None, "value": value.wrappedValue if value else None, "unit": digest(prop.Unit)})
                else:
                    properties.append({"name": prop.Name, "class": prop.is_a(), "graph": digest(prop)})
            typed.append({"class": definition.is_a(), "name": definition.Name, "description": definition.Description, "properties": sorted(properties, key=lambda p: json.dumps(p, sort_keys=True, ensure_ascii=False))})
        states[identity] = {"graph": digest(product), "properties": _plain(ifcopenshell.util.element.get_psets(product, should_inherit=False)), "typed_properties": sorted(typed, key=lambda p: json.dumps(p, sort_keys=True, ensure_ascii=False)), "edges": edges}
    states["__project_context__"] = {"graph": sorted(digest(project) for project in model.by_type("IfcProject"))}
    return states


def verify_case(source, damaged, manifest: dict, *, baseline_state=None) -> dict:
    before_model = None
    if baseline_state is None:
        before_model = ifcopenshell.open(str(source)) if isinstance(source, (str, Path)) else source
        baseline_state = product_state(before_model)
    after_model = ifcopenshell.open(str(damaged)) if isinstance(damaged, (str, Path)) else damaged
    after = product_state(after_model)
    removed = {item["guid"] for item in manifest.get("deletions", [])}
    removed.update(item["opening_guid"] for item in manifest.get("deletions", []) if not item.get("preserve_opening", True) and item.get("opening_guid"))
    unexpected_missing = sorted(set(baseline_state) - set(after) - removed)
    not_removed = sorted(removed & set(after))
    additions = sorted(set(after) - set(baseline_state))
    changed_properties = {}
    for change in manifest.get("property_changes", []):
        changed_properties.setdefault(change["guid"], []).append(change)
    discrepancies = []
    property_failures = []
    for guid in sorted(set(baseline_state) & set(after)):
        expected = json.loads(json.dumps(baseline_state[guid]))
        if guid == "__project_context__":
            if expected != after[guid]:
                discrepancies.append(guid)
            continue
        for name in ("FillsVoids", "VoidsElements", "HasOpenings"):
            expected["edges"][name] = [row for row in expected["edges"][name] if row[2] not in removed]
        for change in changed_properties.get(guid, []):
            pset = expected["properties"].get(change["pset_name"], {})
            if pset.get(change["property_name"]) != change["before"]:
                property_failures.append({"guid": guid, "reason": "before_value_mismatch"})
            pset[change["property_name"]] = change["after"]
            matching = [prop for definition in expected["typed_properties"] if definition.get("name") == change["pset_name"] for prop in definition.get("properties", []) if prop["name"] == change["property_name"]]
            if len(matching) != 1 or matching[0].get("value_type") != change["value_type"] or matching[0].get("value") != change["before"]:
                property_failures.append({"guid": guid, "reason": "typed_property_binding_failed"})
            else:
                matching[0]["value"] = change["after"]
            for definition in expected["typed_properties"]:
                if "properties" in definition:
                    definition["properties"].sort(key=lambda p: json.dumps(p, sort_keys=True, ensure_ascii=False))
            expected["typed_properties"].sort(key=lambda p: json.dumps(p, sort_keys=True, ensure_ascii=False))
        # JSON normalization equates tuple and list containers, never numeric values.
        actual = json.loads(json.dumps(after[guid]))
        if expected != actual:
            discrepancies.append(guid)
    return {"passed": not (unexpected_missing or not_removed or additions or discrepancies or property_failures), "expected_removed_products": len(removed), "removed_targets_absent": not not_removed, "unexpected_missing_products": unexpected_missing, "unexpected_added_products": additions, "unrecorded_product_changes": discrepancies, "property_failures": property_failures, "checked_preserved_products": len(set(baseline_state) & set(after)) - 1, "scope": "all surviving product forward graphs, typed instance properties and units, project/context/unit graphs, type/material/containment/void/fill edges; sampled mesh checks are separate"}
