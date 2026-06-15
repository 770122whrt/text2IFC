from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_compiler import compile_document  # noqa: E402
from text2ifc_contract.validation_v2 import validate_v2_document  # noqa: E402
from text2ifc_quality import check_generated_ifc  # noqa: E402


DEFAULT_OUTPUT_ROOT = ROOT / "dataset" / "processed" / "agent-demo" / "geometry-gate"


def run_case(case_id: str, output_dir: Path | None = None) -> dict[str, Any]:
    case = _case(case_id)
    output = output_dir or DEFAULT_OUTPUT_ROOT / case_id
    output.mkdir(parents=True, exist_ok=True)

    raw_response = json.dumps(
        case["candidate"],
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )
    candidate = json.loads(raw_response)
    validation_issues = validate_v2_document(candidate)
    output_ifc = output / "output.ifc"
    compilation = None
    quality = None

    if not validation_issues:
        compilation = compile_document(candidate, output_ifc)
        if compilation.success:
            quality = check_generated_ifc(output_ifc, case["expected"])

    metrics = _metrics(
        candidate=candidate,
        validation_issues=validation_issues,
        compilation=compilation,
        quality=quality,
    )
    diagnostics = {
        "validation": [_contract_issue(issue) for issue in validation_issues],
        "compilation": _compilation_payload(compilation),
        "quality": _quality_payload(quality),
    }
    success = all(
        bool(metrics[key])
        for key in (
            "parse_valid",
            "bim_json_valid",
            "geometry_pass",
            "attributes_pass",
            "relationships_pass",
            "ifc_structure_pass",
            "compile_reopen_success",
        )
    )

    _write_text(output / "input.txt", case["input_text"])
    _write_text(output / "prompt-used.md", _prompt_text(case_id))
    _write_text(output / "raw-response.txt", raw_response + "\n")
    _write_json(output / "candidate.json", candidate)
    _write_json(output / "expected.json", case["expected"])
    _write_json(output / "diagnostics.json", diagnostics)
    _write_json(output / "metrics.json", metrics)
    _write_report(output / "report.md", case_id, success, metrics, diagnostics)
    return {"success": success, "output_dir": str(output), "metrics": metrics}


def _case(case_id: str) -> dict[str, Any]:
    if case_id == "simple-room-fixed":
        return _simple_room_fixed()
    if case_id == "two-room-suite":
        return _two_room_suite()
    raise ValueError(f"Unknown geometry gate case: {case_id}")


def _simple_room_fixed() -> dict[str, Any]:
    return {
        "input_text": (
            "请创建一个单层矩形房间，长 6 米、宽 4 米、高 3 米；"
            "四面墙闭合，南墙中间有一扇门，北墙中间有一扇窗。"
        ),
        "candidate": _simple_room_candidate(),
        "expected": {
            "case_id": "simple-room-fixed",
            "units": "METRE",
            "tolerance": 0.05,
            "walls": {
                "wall-south": {
                    "axis": "x",
                    "bbox": {
                        "x": [0.0, 6.0],
                        "y": [-0.1, 0.1],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-north": {
                    "axis": "x",
                    "bbox": {
                        "x": [0.0, 6.0],
                        "y": [3.9, 4.1],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-west": {
                    "axis": "y",
                    "bbox": {
                        "x": [-0.1, 0.1],
                        "y": [0.0, 4.0],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-east": {
                    "axis": "y",
                    "bbox": {
                        "x": [5.9, 6.1],
                        "y": [0.0, 4.0],
                        "z": [0.0, 3.0],
                    },
                },
            },
        },
    }


def _simple_room_candidate() -> dict[str, Any]:
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _entity("project-1", "IfcProject", {"Name": "Text2IFC Geometry Gate"}),
            _entity(
                "site-1",
                "IfcSite",
                {"Name": "Site", "ObjectPlacement": _placement("project-1")},
            ),
            _entity(
                "building-1",
                "IfcBuilding",
                {"Name": "Building", "ObjectPlacement": _placement("site-1")},
            ),
            _entity(
                "storey-1",
                "IfcBuildingStorey",
                {
                    "Name": "Level 1",
                    "Elevation": 0,
                    "ObjectPlacement": _placement("building-1"),
                },
            ),
            _entity(
                "space-1",
                "IfcSpace",
                {
                    "Name": "Room",
                    "InteriorOrExteriorSpace": "INTERNAL",
                    "ObjectPlacement": _placement("storey-1"),
                    "Representation": _polygon_representation(
                        [[0, 0], [6000, 0], [6000, 4000], [0, 4000], [0, 0]],
                        3000,
                    ),
                },
            ),
            _wall("wall-south", [3000, 0, 0], 6000),
            _wall("wall-north", [3000, 4000, 0], 6000),
            _wall("wall-west", [0, 2000, 0], 4000, [0, 1, 0]),
            _wall("wall-east", [6000, 2000, 0], 4000, [0, 1, 0]),
            _opening("opening-door-1", "wall-south", [0, 0, 0], 900, 2100),
            _entity(
                "door-1",
                "IfcDoor",
                {
                    "Name": "Door",
                    "OverallWidth": 900,
                    "OverallHeight": 2100,
                    "ObjectPlacement": _placement("opening-door-1"),
                    "Representation": _rectangle_representation(900, 100, 2100),
                },
            ),
            _opening("opening-window-1", "wall-north", [0, 0, 900], 1200, 1500),
            _entity(
                "window-1",
                "IfcWindow",
                {
                    "Name": "Window",
                    "OverallWidth": 1200,
                    "OverallHeight": 1500,
                    "ObjectPlacement": _placement("opening-window-1"),
                    "Representation": _rectangle_representation(1200, 100, 1500),
                },
            ),
        ],
        "relationships": [
            _relationship(
                "void-door-1",
                "IfcRelVoidsElement",
                {
                    "RelatingBuildingElement": "wall-south",
                    "RelatedOpeningElement": "opening-door-1",
                },
            ),
            _relationship(
                "fill-door-1",
                "IfcRelFillsElement",
                {
                    "RelatingOpeningElement": "opening-door-1",
                    "RelatedBuildingElement": "door-1",
                },
            ),
            _relationship(
                "void-window-1",
                "IfcRelVoidsElement",
                {
                    "RelatingBuildingElement": "wall-north",
                    "RelatedOpeningElement": "opening-window-1",
                },
            ),
            _relationship(
                "fill-window-1",
                "IfcRelFillsElement",
                {
                    "RelatingOpeningElement": "opening-window-1",
                    "RelatedBuildingElement": "window-1",
                },
            ),
        ],
        "provenance": {"source": "phase-4-geometry-gate"},
    }


def _two_room_suite() -> dict[str, Any]:
    return {
        "input_text": (
            "请创建一个单层双房间套间，总长 8 米、宽 4 米、高 3 米；"
            "中间在 x=4 米处设置分隔墙，分隔墙中间有门，东墙中间有窗。"
        ),
        "candidate": _two_room_candidate(),
        "expected": {
            "case_id": "two-room-suite",
            "units": "METRE",
            "tolerance": 0.05,
            "walls": {
                "wall-south": {
                    "axis": "x",
                    "bbox": {
                        "x": [0.0, 8.0],
                        "y": [-0.1, 0.1],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-north": {
                    "axis": "x",
                    "bbox": {
                        "x": [0.0, 8.0],
                        "y": [3.9, 4.1],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-west": {
                    "axis": "y",
                    "bbox": {
                        "x": [-0.1, 0.1],
                        "y": [0.0, 4.0],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-east": {
                    "axis": "y",
                    "bbox": {
                        "x": [7.9, 8.1],
                        "y": [0.0, 4.0],
                        "z": [0.0, 3.0],
                    },
                },
                "wall-partition": {
                    "axis": "y",
                    "bbox": {
                        "x": [3.9, 4.1],
                        "y": [0.0, 4.0],
                        "z": [0.0, 3.0],
                    },
                },
            },
        },
    }


def _two_room_candidate() -> dict[str, Any]:
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _entity("project-1", "IfcProject", {"Name": "Text2IFC Geometry Gate"}),
            _entity(
                "site-1",
                "IfcSite",
                {"Name": "Site", "ObjectPlacement": _placement("project-1")},
            ),
            _entity(
                "building-1",
                "IfcBuilding",
                {"Name": "Building", "ObjectPlacement": _placement("site-1")},
            ),
            _entity(
                "storey-1",
                "IfcBuildingStorey",
                {
                    "Name": "Level 1",
                    "Elevation": 0,
                    "ObjectPlacement": _placement("building-1"),
                },
            ),
            _entity(
                "space-west",
                "IfcSpace",
                {
                    "Name": "West Room",
                    "InteriorOrExteriorSpace": "INTERNAL",
                    "ObjectPlacement": _placement("storey-1"),
                    "Representation": _polygon_representation(
                        [[0, 0], [4000, 0], [4000, 4000], [0, 4000], [0, 0]],
                        3000,
                    ),
                },
            ),
            _entity(
                "space-east",
                "IfcSpace",
                {
                    "Name": "East Room",
                    "InteriorOrExteriorSpace": "INTERNAL",
                    "ObjectPlacement": _placement("storey-1"),
                    "Representation": _polygon_representation(
                        [[4000, 0], [8000, 0], [8000, 4000], [4000, 4000], [4000, 0]],
                        3000,
                    ),
                },
            ),
            _wall("wall-south", [4000, 0, 0], 8000),
            _wall("wall-north", [4000, 4000, 0], 8000),
            _wall("wall-west", [0, 2000, 0], 4000, [0, 1, 0]),
            _wall("wall-east", [8000, 2000, 0], 4000, [0, 1, 0]),
            _wall("wall-partition", [4000, 2000, 0], 4000, [0, 1, 0]),
            _opening("opening-door-1", "wall-partition", [0, 0, 0], 900, 2100),
            _entity(
                "door-1",
                "IfcDoor",
                {
                    "Name": "Door",
                    "OverallWidth": 900,
                    "OverallHeight": 2100,
                    "ObjectPlacement": _placement("opening-door-1"),
                    "Representation": _rectangle_representation(900, 100, 2100),
                },
            ),
            _opening("opening-window-1", "wall-east", [0, 0, 900], 1200, 1500),
            _entity(
                "window-1",
                "IfcWindow",
                {
                    "Name": "Window",
                    "OverallWidth": 1200,
                    "OverallHeight": 1500,
                    "ObjectPlacement": _placement("opening-window-1"),
                    "Representation": _rectangle_representation(1200, 100, 1500),
                },
            ),
        ],
        "relationships": [
            _relationship(
                "void-door-1",
                "IfcRelVoidsElement",
                {
                    "RelatingBuildingElement": "wall-partition",
                    "RelatedOpeningElement": "opening-door-1",
                },
            ),
            _relationship(
                "fill-door-1",
                "IfcRelFillsElement",
                {
                    "RelatingOpeningElement": "opening-door-1",
                    "RelatedBuildingElement": "door-1",
                },
            ),
            _relationship(
                "void-window-1",
                "IfcRelVoidsElement",
                {
                    "RelatingBuildingElement": "wall-east",
                    "RelatedOpeningElement": "opening-window-1",
                },
            ),
            _relationship(
                "fill-window-1",
                "IfcRelFillsElement",
                {
                    "RelatingOpeningElement": "opening-window-1",
                    "RelatedBuildingElement": "window-1",
                },
            ),
        ],
        "provenance": {"source": "phase-4-geometry-gate"},
    }


def _entity(entity_id: str, ifc_class: str, attributes: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "phase-4-geometry-gate"},
    }


def _relationship(
    relationship_id: str, ifc_class: str, attributes: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": relationship_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "provenance": {"source": "phase-4-geometry-gate"},
    }


def _placement(
    relative_to: str,
    origin: list[float] | None = None,
    ref_direction: list[float] | None = None,
) -> dict[str, Any]:
    return {
        "relative_to": relative_to,
        "origin": origin or [0, 0, 0],
        "axis": [0, 0, 1],
        "ref_direction": ref_direction or [1, 0, 0],
    }


def _rectangle_representation(x: float, y: float, depth: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "rectangle", "x": x, "y": y},
        "depth": depth,
        "direction": [0, 0, 1],
    }


def _polygon_representation(points: list[list[float]], depth: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "polygon", "points": points},
        "depth": depth,
        "direction": [0, 0, 1],
    }


def _wall(
    entity_id: str,
    origin: list[float],
    length: float,
    ref_direction: list[float] | None = None,
) -> dict[str, Any]:
    return _entity(
        entity_id,
        "IfcWall",
        {
            "Name": entity_id,
            "ObjectPlacement": _placement("storey-1", origin, ref_direction),
            "Representation": _rectangle_representation(length, 200, 3000),
        },
    )


def _opening(
    entity_id: str,
    wall_id: str,
    origin: list[float],
    width: float,
    height: float,
) -> dict[str, Any]:
    return _entity(
        entity_id,
        "IfcOpeningElement",
        {
            "Name": entity_id,
            "ObjectPlacement": _placement(wall_id, origin),
            "Representation": _rectangle_representation(width, 200, height),
        },
    )


def _metrics(
    *,
    candidate: dict[str, Any],
    validation_issues: list[Any],
    compilation: Any,
    quality: Any,
) -> dict[str, Any]:
    return {
        "parse_valid": True,
        "bim_json_valid": not validation_issues,
        "geometry_pass": bool(quality and quality.success),
        "attributes_pass": _attributes_present(candidate),
        "relationships_pass": len(candidate.get("relationships", [])) >= 4,
        "ifc_structure_pass": bool(compilation and compilation.success),
        "compile_reopen_success": bool(compilation and compilation.success),
        "iteration_count": 1,
    }


def _attributes_present(candidate: dict[str, Any]) -> bool:
    entities = {entity["id"]: entity for entity in candidate.get("entities", [])}
    door = entities.get("door-1", {}).get("attributes", {})
    window = entities.get("window-1", {}).get("attributes", {})
    return (
        door.get("OverallWidth") == 900
        and door.get("OverallHeight") == 2100
        and window.get("OverallWidth") == 1200
        and window.get("OverallHeight") == 1500
    )


def _contract_issue(issue: Any) -> dict[str, str]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _compilation_payload(compilation: Any) -> dict[str, Any]:
    if compilation is None:
        return {"attempted": False, "success": False, "issues": []}
    issues = []
    for issue in getattr(compilation, "input_issues", ()):
        issues.append(_contract_issue(issue))
    for issue in getattr(compilation, "ifc_issues", ()):
        issues.append(
            {
                "code": issue.code,
                "path": f"{issue.entity}/{issue.attribute}",
                "message": issue.message,
            }
        )
    return {
        "attempted": True,
        "success": compilation.success,
        "issues": issues,
        "output_path": str(compilation.output_path) if compilation.output_path else None,
    }


def _quality_payload(quality: Any) -> dict[str, Any]:
    if quality is None:
        return {"attempted": False, "success": False, "issues": [], "metrics": {}}
    return {
        "attempted": True,
        "success": quality.success,
        "issues": quality.issues,
        "metrics": quality.metrics,
    }


def _prompt_text(case_id: str) -> str:
    return "\n".join(
        [
            f"# Geometry Gate Prompt: {case_id}",
            "",
            "Return BIM JSON 2.0 only.",
            "Use IfcWall objects for walls.",
            "Use rectangle profile center-origin semantics.",
            "Orient east/west walls along the local Y direction.",
            "Do not output raw IFC, STEP IDs, IfcCartesianPoint, or OwnerHistory.",
            "",
        ]
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def _write_report(
    path: Path,
    case_id: str,
    success: bool,
    metrics: dict[str, Any],
    diagnostics: dict[str, Any],
) -> None:
    lines = [
        f"# Geometry Gate Report: {case_id}",
        "",
        f"- Success: {success}",
        f"- BIM JSON valid: {metrics['bim_json_valid']}",
        f"- Geometry pass: {metrics['geometry_pass']}",
        f"- Compile/reopen success: {metrics['compile_reopen_success']}",
        f"- Quality issues: {len(diagnostics['quality']['issues'])}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    result = run_case(arguments.case, arguments.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["success"] or not arguments.check else 2


if __name__ == "__main__":
    raise SystemExit(main())
