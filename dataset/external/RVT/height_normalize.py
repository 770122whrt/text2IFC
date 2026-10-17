"""Correct only a zero railing height proven by two source parameters and geometry.

This separate policy never changes geometry or guesses a dimension. Every owner of
a shared property must supply the same positive value. Other errors stay blocked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

POLICY = "ddc-railing-height-evidence/1.0"


def prove_height_value(values: list[float], scale: float, span: float) -> float | None:
    if len(values) != 2 or not all(math.isfinite(v) and v > 0 for v in [*values, scale, span]):
        return None
    if values[0] != values[1] or not math.isclose(values[0] * scale, span, rel_tol=1e-8, abs_tol=1e-6):
        return None
    return values[0]


def normalize(source: Path, target: Path, geometry_report: Path) -> dict:
    import ifcopenshell
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    source, target = source.resolve(), target.resolve()
    if source == target or target.exists():
        raise ValueError("OVERWRITE_FORBIDDEN")
    original = source.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    validation = json.loads(geometry_report.read_text(encoding="utf-8"))
    if validation["sha256"] != digest or validation.get("geometry", {}).get("failed") != 0:
        raise ValueError("GEOMETRY_EVIDENCE_MISMATCH_OR_FAILURE")
    geometry = {r["id"]: r for r in validation["geometry"]["products"]}
    f = ifcopenshell.open(source)
    if f.schema != "IFC2X3" or len(f.by_type("IfcProject")) != 1:
        raise ValueError("UNSUPPORTED_SCHEMA_OR_PROJECT")
    project = f.by_type("IfcProject")[0]
    length_units = [u for u in project.UnitsInContext.Units if getattr(u, "UnitType", None) == "LENGTHUNIT"]
    if len(length_units) != 1:
        raise ValueError("LENGTH_UNIT_AMBIGUOUS")
    scale = ifcopenshell.util.unit.calculate_unit_scale(f)
    before = {e.id(): e.to_string() for e in f}
    changes, pending = [], []
    for prop in f.by_type("IfcPropertySingleValue"):
        value = prop.NominalValue
        if prop.Name != "Height" or value is None or not value.is_a("IfcPositiveLengthMeasure") or value.wrappedValue != 0:
            continue
        if prop.Unit is not None and prop.Unit != length_units[0]:
            pending.append({"property_id": prop.id(), "reason": "HEIGHT_UNIT_OVERRIDE"})
            continue
        psets = list(f.get_inverse(prop))
        if not psets or any(not ps.is_a("IfcPropertySet") or ps.Name != "Pset_RailingCommon" for ps in psets):
            pending.append({"property_id": prop.id(), "reason": "OTHER_PROPERTY_OWNERS"})
            continue
        owners = set()
        invalid = False
        for ps in psets:
            relations = list(f.get_inverse(ps))
            if not relations:
                invalid = True
            for rel in relations:
                if not rel.is_a("IfcRelDefinesByProperties"):
                    invalid = True
                else:
                    owners.update(rel.RelatedObjects)
        evidence = []
        for owner in sorted(owners, key=lambda e: e.id()):
            if not owner.is_a("IfcRailing") or owner.id() not in geometry or owner.ObjectPlacement is None:
                invalid = True
                continue
            matrix = ifcopenshell.util.placement.get_local_placement(owner.ObjectPlacement)
            if not all(math.isclose(float(matrix[i, 2]), desired, abs_tol=1e-9) for i, desired in enumerate((0., 0., 1.))):
                invalid = True
                continue
            sources = []
            for ps_name, prop_name in (("Construction(Type)", "Railing Height"), ("Top Rail(Type)", "Height")):
                matches = []
                for rel in owner.IsDefinedBy:
                    if not rel.is_a("IfcRelDefinesByProperties"):
                        continue
                    ps = rel.RelatingPropertyDefinition
                    if ps.is_a("IfcPropertySet") and ps.Name == ps_name:
                        matches.extend(p for p in ps.HasProperties if p.is_a("IfcPropertySingleValue") and p.Name == prop_name)
                if len(matches) != 1:
                    invalid = True
                    continue
                match = matches[0]
                if match.NominalValue is None or not match.NominalValue.is_a("IfcLengthMeasure") or (match.Unit is not None and match.Unit != length_units[0]):
                    invalid = True
                    continue
                sources.append({"pset": ps_name, "property_id": match.id(), "value": float(match.NominalValue.wrappedValue)})
            g = geometry[owner.id()]
            if not g.get("passed"):
                invalid = True
                continue
            span = g["bounds"][2][1] - g["bounds"][2][0]
            proved = prove_height_value([s["value"] for s in sources], scale, span)
            if proved is None:
                invalid = True
            evidence.append({"owner_id": owner.id(), "owner_guid": owner.GlobalId, "sources": sources,
                             "vertical_span_metres": span, "length_unit_scale": scale, "proven_height": proved})
        proposed = {e["proven_height"] for e in evidence}
        if invalid or not owners or len(evidence) != len(owners) or len(proposed) != 1 or None in proposed:
            pending.append({"property_id": prop.id(), "reason": "INSUFFICIENT_OR_CONFLICTING_EVIDENCE", "evidence": evidence})
            continue
        height = proposed.pop()
        prop.NominalValue = f.createIfcPositiveLengthMeasure(height)
        changes.append({"entity_id": prop.id(), "before": before[prop.id()], "after": prop.to_string(), "evidence": evidence})
    after = {e.id(): e.to_string() for e in f}
    changed_ids = {i for i in before if before[i] != after.get(i)}
    if set(before) != set(after) or changed_ids != {c["entity_id"] for c in changes}:
        raise ValueError("OUT_OF_SCOPE_ENTITY_CHANGE")
    serialized = f.to_string()
    if {e.id(): e.to_string() for e in ifcopenshell.file.from_string(serialized)} != after:
        raise ValueError("SERIALIZATION_DRIFT")
    if source.read_bytes() != original:
        raise ValueError("SOURCE_CHANGED")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(serialized.encode("utf-8"))
    return {"policy": POLICY, "source_sha256": digest, "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "changes": changes, "pending": pending, "technical_candidate": False,
            "preservation": {"source_unchanged": True, "product_guids_unchanged": True, "unchanged_entities_equal": True,
                             "geometry_unchanged": True, "entities_added_or_removed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--geometry-report", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("REPORT_ALREADY_EXISTS")
    result = normalize(args.source, args.target, args.geometry_report)
    with args.report.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(json.dumps({"changes": len(result["changes"]), "pending": result["pending"]}))
    return 0 if result["changes"] and not result["pending"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
