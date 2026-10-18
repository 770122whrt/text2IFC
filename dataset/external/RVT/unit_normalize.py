"""Fill uniquely determined names on unprefixed SI area/volume units, including property units."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def normalize(source: Path, target: Path) -> dict:
    import ifcopenshell
    source, target = source.resolve(), target.resolve()
    if source == target or target.exists():
        raise ValueError("OVERWRITE_FORBIDDEN")
    original = source.read_bytes()
    f = ifcopenshell.open(source)
    if f.schema != "IFC2X3":
        raise ValueError("ONLY_IFC2X3_SUPPORTED")
    before = {e.id(): e.to_string() for e in f}
    changes = []
    names = {"AREAUNIT": "SQUARE_METRE", "VOLUMEUNIT": "CUBIC_METRE"}
    for unit in f.by_type("IfcSIUnit"):
        if unit.Name is None and unit.Prefix is None and unit.UnitType in names:
            unit.Name = names[unit.UnitType]
            changes.append({"entity_id": unit.id(), "before": before[unit.id()], "after": unit.to_string(),
                            "evidence": "Explicit unprefixed SI area/volume type determines its base SI unit name uniquely; no values rescaled."})
    after = {e.id(): e.to_string() for e in f}
    if set(before) != set(after) or {i for i in before if before[i] != after[i]} != {c["entity_id"] for c in changes}:
        raise ValueError("OUT_OF_SCOPE_ENTITY_CHANGE")
    serialized = f.to_string()
    if after != {e.id(): e.to_string() for e in ifcopenshell.file.from_string(serialized)} or source.read_bytes() != original:
        raise ValueError("PRESERVATION_FAILURE")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as f:
        f.write(serialized.encode("utf-8"))
    return {"policy": "explicit-si-area-volume-unit-name/1.0", "source_sha256": hashlib.sha256(original).hexdigest(),
            "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "changes": changes, "pending": [],
            "technical_candidate": False, "preservation": {"source_unchanged": True, "product_guids_unchanged": True,
            "unchanged_entities_equal": True, "geometry_unchanged": True, "numeric_values_unchanged": True}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("REPORT_ALREADY_EXISTS")
    result = normalize(args.source, args.target)
    with args.report.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(json.dumps({"changes": len(result["changes"])}))
