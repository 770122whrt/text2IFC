"""Public model inspection for the Composite Repair Milestone evidence task.

Reads ONLY public information from candidate IFC2X3 models using the
production index adapters themselves (``default_index_adapter_registry``), so
any geometry values frozen into case bindings are computed by the exact same
public measurement path the production retriever uses.  No private Gold,
mutation truth, deleted identities, or comparator data is touched.

Usage (repo root, repo venv)::

    python scripts/ifc_repair/composite_evidence/inspect_models.py \
        --model R1-DPX-ARC=dataset/external/ifc-bench/projects/duplex/arc.ifc
    python scripts/ifc_repair/composite_evidence/inspect_models.py --all-frozen
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import ifcopenshell  # noqa: E402

from text2ifc_ifc_repair.index_adapters import default_index_adapter_registry  # noqa: E402

FROZEN_R1_MODELS = (
    ("R1-DPX-ARC", "dataset/external/ifc-bench/projects/duplex/arc.ifc"),
    (
        "R1-WRH-ARC",
        "dataset/external/ifc-bench/projects/west_riverside_hospital/arc_ifc2x3.ifc",
    ),
    ("R1-S65-STR", "dataset/external/ifc-bench/projects/sixty5/str.ifc"),
    (
        "R1-BW-TALL",
        "dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc",
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unit_name(model) -> str:
    try:
        scale = ifcopenshell.util.unit.calculate_unit_scale(model)
        return f"length unit scale = {scale} m per project unit"
    except Exception:
        return "unknown"


def _storeys(model) -> list[dict]:
    rows = []
    for storey in sorted(
        model.by_type("IfcBuildingStorey"),
        key=lambda s: (s.Elevation or 0.0),
    ):
        contained = sum(
            len(relation.RelatedElements)
            for relation in storey.ContainsElements
        )
        rows.append(
            {
                "global_id": str(storey.GlobalId),
                "name": storey.Name,
                "elevation_project_units": (
                    None if storey.Elevation is None else float(storey.Elevation)
                ),
                "contained_elements": contained,
            }
        )
    return rows


def _counts(model) -> dict[str, int]:
    classes = (
        "IfcWall",
        "IfcWallStandardCase",
        "IfcBeam",
        "IfcColumn",
        "IfcDoor",
        "IfcWindow",
        "IfcOpeningElement",
        "IfcSlab",
        "IfcBeamType",
        "IfcColumnType",
        "IfcDoorStyle",
        "IfcWindowStyle",
        "IfcBuildingStorey",
    )
    return {cls: len(model.by_type(cls)) for cls in classes}


def _walls(model, adapter_registry, limit: int) -> list[dict]:
    adapter = adapter_registry.adapter_for(
        next(iter(model.by_type("IfcWall") or model.by_type("IfcWallStandardCase")))
    ) if (model.by_type("IfcWall") or model.by_type("IfcWallStandardCase")) else None
    del adapter
    rows: list[dict] = []
    walls = list(model.by_type("IfcWall")) + list(model.by_type("IfcWallStandardCase"))
    for wall in walls:
        adapter = adapter_registry.adapter_for(wall)
        if adapter is None:
            continue
        result = adapter.extract(wall)
        if result.geometry_capability != "straight_wall":
            continue
        dimensions = result.geometry_summary.get("dimensions_mm", {})
        rows.append(
            {
                "global_id": str(wall.GlobalId),
                "name": wall.Name,
                "length_mm": round(float(dimensions.get("length", 0.0)), 3),
                "height_mm": round(float(dimensions.get("height", 0.0)), 3),
                "thickness_mm": round(float(dimensions.get("thickness", 0.0)), 3),
                "orientation": result.geometry_summary.get("orientation"),
                "geometry_capability": result.geometry_capability,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _openings(model, adapter_registry, limit: int) -> list[dict]:
    rows: list[dict] = []
    for opening in model.by_type("IfcOpeningElement"):
        adapter = adapter_registry.adapter_for(opening)
        if adapter is None:
            continue
        result = adapter.extract(opening)
        if result.geometry_capability != "measured_hosted_opening":
            continue
        if result.facets.get("fill_state") != "empty":
            continue
        dimensions = result.geometry_summary.get("dimensions_mm", {})
        position = result.geometry_summary.get("wall_local_position_mm", {})
        rows.append(
            {
                "global_id": str(opening.GlobalId),
                "host_wall_global_id": (
                    result.facets.get("host_wall_global_ids") or [None]
                )[0],
                "width_mm": round(float(dimensions.get("width", 0.0)), 3),
                "height_mm": round(float(dimensions.get("height", 0.0)), 3),
                "depth_mm": round(float(dimensions.get("depth", 0.0)), 3),
                "center_offset_mm": round(
                    float(position.get("center_offset_mm", 0.0)), 3
                ),
                "sill_height_mm": round(
                    float(position.get("sill_height_mm", 0.0)), 3
                ),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def inspect(path: Path, model_id: str, *, wall_limit: int, opening_limit: int) -> dict:
    model = ifcopenshell.open(str(path))
    adapter_registry = default_index_adapter_registry()
    return {
        "model_id": model_id,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "schema": str(model.schema),
        "project_units": _unit_name(model),
        "storeys": _storeys(model),
        "counts": _counts(model),
        "straight_walls_sample": _walls(model, adapter_registry, wall_limit),
        "unfilled_openings_sample": _openings(model, adapter_registry, opening_limit),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="model spec 'id=relative/path.ifc' (repeatable)",
    )
    parser.add_argument("--all-frozen", action="store_true")
    parser.add_argument("--wall-limit", type=int, default=40)
    parser.add_argument("--opening-limit", type=int, default=40)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    specs: list[tuple[str, Path]] = []
    if args.all_frozen:
        specs.extend((mid, ROOT / rel) for mid, rel in FROZEN_R1_MODELS)
    for spec in args.model:
        model_id, _, rel = spec.partition("=")
        specs.append((model_id, ROOT / rel))

    if not specs:
        parser.error("provide --model or --all-frozen")

    report = {
        "task": "composite-repair-milestone model inspection",
        "public_information_only": True,
        "measurement_path": "text2ifc_ifc_repair.index_adapters.default_index_adapter_registry",
        "models": [
            inspect(
                path,
                model_id,
                wall_limit=args.wall_limit,
                opening_limit=args.opening_limit,
            )
            for model_id, path in specs
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {args.output}")
    print(text[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
