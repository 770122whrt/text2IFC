"""Conservative DDC IFC2X3 normalization, with explicit entity-level preservation.

No solid geometry edits, property renaming, value coercion, blanket GUID regeneration,
source rewrite, entity deletion or dataset admission. Ambiguous cases stay pending.
Policy is independently implemented from IFC schema constraints; historical handoff
repair scripts were consulted as evidence, not executed or treated as authority.
Exactly planar grid axis curves may be cloned to IFC2X3-required 2D coordinates.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import uuid

import ifcopenshell

POLICY = "ddc-ifc2x3-conservative-normalization/1.1"
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, POLICY)


def typed_value(value):
    if isinstance(value, (tuple, list)):
        return [typed_value(v) for v in value]
    if isinstance(value, ifcopenshell.entity_instance):
        return {"ref": value.id(), "type": value.is_a()} if value.id() else {"type": value.is_a(), "values": [typed_value(v) for v in value]}
    return value


def property_payload(entity):
    return json.dumps({"class": entity.is_a(), "attributes": [typed_value(v) for v in entity]}, sort_keys=True, allow_nan=False)


def normalize(source: Path, target: Path, *, converter_label: str) -> dict:
    source, target = source.resolve(), target.resolve()
    if source == target or target.exists():
        raise ValueError("OVERWRITE_FORBIDDEN")
    if not converter_label.strip():
        raise ValueError("CONVERTER_PROVENANCE_REQUIRED")
    original = source.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    f = ifcopenshell.open(source)
    if f.schema != "IFC2X3":
        raise ValueError("ONLY_IFC2X3_SUPPORTED")
    before = {e.id(): e.to_string() for e in f}
    product_guids = {e.id(): e.GlobalId for e in f.by_type("IfcProduct")}
    changes, pending = [], []
    allowed_changed = set()
    used = {e.GlobalId for e in f.by_type("IfcRoot")}

    def new_guid(label):
        for salt in range(1000):
            guid = ifcopenshell.guid.compress(uuid.uuid5(NAMESPACE, f"{digest}|{label}|{salt}").hex)
            if guid not in used:
                used.add(guid)
                return guid
        raise ValueError("GUID_COLLISION_BUDGET")

    def record(rule, entity, **details):
        allowed_changed.add(entity.id())
        changes.append({"rule": rule, "entity_id": entity.id(), **details})

    if f.header.file_name.originating_system is None:
        f.header.file_name.originating_system = converter_label
        changes.append({"rule": "missing_originating_system", "value": converter_label})
    # Name=CUBIC_METRE is uniquely determined for an unprefixed SI volume unit.
    # Prefix belongs to this volume unit, independently of the LENGTHUNIT prefix.
    # Restrict to units explicitly present in a unit assignment; no numeric scaling.
    for assignment in f.by_type("IfcUnitAssignment"):
        for unit in assignment.Units:
            if unit.is_a("IfcSIUnit") and unit.UnitType == "VOLUMEUNIT" and unit.Name is None and unit.Prefix is None:
                unit.Name = "CUBIC_METRE"
                record("unprefixed_si_volume_name", unit, numeric_values_rescaled=False)
    # Empty optional aggregate means absence, not a reason to discard the grid.
    for grid in f.by_type("IfcGrid"):
        if grid.WAxes == ():
            grid.WAxes = None
            record("empty_optional_grid_waxes", grid)
    for axis in f.by_type("IfcGridAxis"):
        curve = axis.AxisCurve
        if curve.Dim != 3:
            continue
        # IFC2X3 requires a 2D curve in the grid's local XY plane. Clone only
        # line segments already exactly in that plane. Keep the original 3D
        # representation and all source geometric records intact.
        if not (curve.is_a("IfcTrimmedCurve") and curve.BasisCurve.is_a("IfcLine")):
            pending.append({"code": "GRID_CURVE_OUTSIDE_POLICY", "axis_id": axis.id()})
            continue
        line = curve.BasisCurve
        trims = list(curve.Trim1) + list(curve.Trim2)
        points = [line.Pnt] + [p for p in trims if p.is_a("IfcCartesianPoint")]
        direction = line.Dir.Orientation.DirectionRatios
        if (any(not (p.is_a("IfcCartesianPoint") or p.is_a("IfcParameterValue")) for p in trims) or
                len(direction) != 3 or direction[2] != 0 or not any(direction[:2]) or
                any(len(p.Coordinates) != 3 or p.Coordinates[2] != 0 for p in points)):
            pending.append({"code": "GRID_NOT_EXACT_LOCAL_XY", "axis_id": axis.id()})
            continue
        def point2d(p):
            return f.createIfcCartesianPoint(p.Coordinates[:2])
        def trim2d(p):
            return point2d(p) if p.is_a("IfcCartesianPoint") else p
        line2d = f.createIfcLine(point2d(line.Pnt), f.createIfcVector(f.createIfcDirection(direction[:2]), line.Dir.Magnitude))
        clone = f.createIfcTrimmedCurve(line2d, [trim2d(p) for p in curve.Trim1], [trim2d(p) for p in curve.Trim2], curve.SenseAgreement, curve.MasterRepresentation)
        axis.AxisCurve = clone
        record("grid_axis_exact_xy_curve_clone", axis, original_curve_id=curve.id(), new_curve_id=clone.id(),
               equality="all original z and direction-z are exactly zero; x/y, vector magnitude, trims and sense preserved")
    groups = defaultdict(list)
    for entity in f.by_type("IfcRoot"):
        groups[entity.GlobalId].append(entity)
    for guid, entities in groups.items():
        if len(entities) < 2:
            continue
        non_psets = [e for e in entities if not e.is_a("IfcPropertySet")]
        if len(non_psets) > 1:
            pending.append({"code": "NON_PSET_GUID_COLLISION", "guid": guid, "ids": [e.id() for e in entities]})
            continue
        keeper = non_psets[0] if non_psets else min(entities, key=lambda e: e.id())
        for entity in entities:
            if entity == keeper:
                continue
            entity.GlobalId = new_guid(f"duplicate-pset:{entity.id()}")
            record("duplicate_pset_guid", entity, old_guid=guid, new_guid=entity.GlobalId)
    for pset in f.by_type("IfcPropertySet"):
        groups = defaultdict(list)
        for prop in pset.HasProperties:
            groups[prop.Name].append(prop)
        detach = set()
        for name, properties in groups.items():
            if len(properties) < 2:
                continue
            if not all(p.is_a("IfcPropertySingleValue") for p in properties) or len({property_payload(p) for p in properties}) != 1:
                pending.append({"code": "PROPERTY_NAME_PAYLOAD_CONFLICT", "pset_id": pset.id(), "name": name, "ids": [p.id() for p in properties]})
                continue
            keep = min(properties, key=lambda p: p.id())
            detach.update(p.id() for p in properties if p != keep)
        retained, seen = [], set()
        for prop in pset.HasProperties:
            if prop.id() not in detach and prop.id() not in seen:
                retained.append(prop)
                seen.add(prop.id())
        if tuple(retained) != pset.HasProperties:
            old_ids = [p.id() for p in pset.HasProperties]
            pset.HasProperties = retained
            record("identical_typed_membership_dedup", pset, before_ids=old_ids, after_ids=[p.id() for p in retained], property_entities_deleted=False)
    for pset in list(f.by_type("IfcPropertySet")):
        owners = sorted(pset.DefinesType, key=lambda e: e.id())
        if len(owners) <= 1:
            continue
        if any(not (e.is_a("IfcTypeObject") or e.is_a("IfcRelDefinesByProperties")) for e in f.get_inverse(pset)):
            pending.append({"code": "SHARED_PSET_HAS_OTHER_ASSOCIATIONS", "pset_id": pset.id()})
            continue
        for owner in owners[1:]:
            clone = f.create_entity("IfcPropertySet", GlobalId=new_guid(f"pset-owner:{pset.id()}:{owner.id()}"),
                                    OwnerHistory=pset.OwnerHistory, Name=pset.Name, Description=pset.Description,
                                    HasProperties=pset.HasProperties)
            owner.HasPropertySets = tuple(clone if x == pset else x for x in owner.HasPropertySets)
            record("one_pset_container_per_type", owner, original_pset=pset.id(), clone_id=clone.id(), property_ids=[p.id() for p in clone.HasProperties])
    after = {e.id(): e.to_string() for e in f}
    removed = sorted(set(before) - set(after))
    changed = sorted(i for i in before if before[i] != after.get(i))
    if removed or set(changed) - allowed_changed:
        raise ValueError("OUT_OF_SCOPE_ENTITY_CHANGE")
    if product_guids != {e.id(): e.GlobalId for e in f.by_type("IfcProduct")}:
        raise ValueError("PRODUCT_IDENTITY_CHANGED")
    # Verify serialization does not alter any entity beyond the explicit edit set.
    serialized = f.to_string()
    reopened = ifcopenshell.file.from_string(serialized)
    if after != {e.id(): e.to_string() for e in reopened}:
        raise ValueError("SERIALIZATION_DRIFT")
    if source.read_bytes() != original:
        raise ValueError("SOURCE_CHANGED")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(serialized.encode("utf-8"))
    return {"policy": POLICY, "source_sha256": digest, "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "status": "candidate_requires_validation", "accepted": False, "changes": changes,
            "changes_by_rule": dict(Counter(c["rule"] for c in changes)), "pending": pending,
            "preservation": {"source_unchanged": source.read_bytes() == original, "product_guids_unchanged": True,
                             "unchanged_entities_equal": True, "existing_geometric_representation_records_edited": False,
                             "grid_axis_curve_references_changed": any(c["rule"] == "grid_axis_exact_xy_curve_clone" for c in changes),
                             "removed_ids": removed, "added_ids": sorted(set(after) - set(before)),
                             "changed_entities": [{"id": i, "before": before[i], "after": after[i]} for i in changed]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--converter-label", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("REPORT_OVERWRITE_FORBIDDEN")
    result = normalize(args.source, args.target, converter_label=args.converter_label)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"changes": result["changes_by_rule"], "pending": result["pending"]}, ensure_ascii=False))
    return 0 if not result["pending"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
