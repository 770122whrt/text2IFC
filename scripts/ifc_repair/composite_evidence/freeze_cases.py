"""Freeze the Composite Repair Milestone acceptance cases (spec Section 7).

Generates, deterministically and hash-bound:

* ``composite-acceptance-freeze.json`` — machine-readable frozen cases;
* ``composite-bound-testcases.md``     — human-readable bound test cases.

Every case carries: exact request text, request SHA-256, model binding,
operation composition with per-operation ``operation_id``, frozen public
bindings, expected terminal class, atomicity requirement, expected entity
delta, Type policy, operation-bound artifact predicates (Section 8), property
involvement, provider stages, reopen and preservation requirements.

The freeze is written ONCE.  Re-running the script against an existing freeze
fails closed.  Case meaning must not change after genuine execution begins.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC_DIR = ROOT / "docs" / "validation" / "repair-composite-milestone"
FREEZE_PATH = DOC_DIR / "composite-acceptance-freeze.json"
MARKDOWN_PATH = DOC_DIR / "composite-bound-testcases.md"

SCHEMA_VERSION = "text2ifc/composite-repair-acceptance-freeze/0.1"
PROVENANCE_NAMESPACE = "repair-composite-milestone"

MODELS = {
    "CM-VVO": {
        "path": "dataset/ifc/train/vvo.ifc",
        "schema": "IFC2X3",
        "sha256": "b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc",
        "size_bytes": 2409268,
        "source": "BIMNet (dataset/manifests/bimnet-ifc2x3.jsonl, scene vvo, split test)",
    },
    "CM-S65": {
        "path": "dataset/external/ifc-bench/projects/sixty5/str.ifc",
        "schema": "IFC2X3",
        "sha256": "79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22",
        "size_bytes": 7422441,
        "source": "IFC-Bench sixty5 str (CC BY 4.0), R1 model R1-S65-STR",
    },
    "CM-TALL": {
        "path": "dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc",
        "schema": "IFC2X3",
        "sha256": "9f180a7148bb7bcf43dd80800068553f1c8b189ebe0dc84b6c498061832960d1",
        "size_bytes": 616509,
        "source": "BIM Whale TallBuilding (MIT retained corpus), R1 model R1-BW-TALL",
    },
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _wall_query(
    *,
    length_mm: float,
    height_mm: float,
    thickness_mm: float,
    direction: str,
    storey_elevation_mm: float | None = None,
    tolerance_mm: float = 1.0,
) -> dict:
    constraints = [
        {"field": "wall_length_mm", "value": length_mm, "tolerance_mm": tolerance_mm},
        {"field": "wall_height_mm", "value": height_mm, "tolerance_mm": tolerance_mm},
        {"field": "wall_thickness_mm", "value": thickness_mm, "tolerance_mm": tolerance_mm},
    ]
    if storey_elevation_mm is not None:
        constraints.append(
            {
                "field": "storey_elevation_mm",
                "value": storey_elevation_mm,
                "tolerance_mm": tolerance_mm,
            }
        )
    return {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
        "direction": direction,
        "geometry_capabilities": ["straight_wall"],
        "geometry_constraints": constraints,
        "max_candidates": 5,
        "winner_margin": 10,
    }


def _opening_query(
    *,
    width_mm: float,
    height_mm: float,
    depth_mm: float,
    center_offset_mm: float,
    sill_height_mm: float,
    tolerance_mm: float = 1.0,
) -> dict:
    return {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcOpeningElement"],
        "geometry_capabilities": ["measured_hosted_opening"],
        "geometry_constraints": [
            {"field": "opening_width_mm", "value": width_mm, "tolerance_mm": tolerance_mm},
            {"field": "opening_height_mm", "value": height_mm, "tolerance_mm": tolerance_mm},
            {"field": "opening_depth_mm", "value": depth_mm, "tolerance_mm": tolerance_mm},
            {"field": "opening_center_offset_mm", "value": center_offset_mm, "tolerance_mm": tolerance_mm},
            {"field": "opening_sill_height_mm", "value": sill_height_mm, "tolerance_mm": tolerance_mm},
        ],
        "max_candidates": 5,
        "winner_margin": 10,
    }


def _storey_query(global_id: str) -> dict:
    return {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcBuildingStorey"],
        "global_id": global_id,
    }


def _beam_op(operation_id: str, start: tuple, end: tuple, width: int, height: int) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_beam",
        "expected_target": {"storey_query": "frozen_per_case"},
        "parameters": {
            "axis": {
                "start": {"x_mm": start[0], "y_mm": start[1], "z_mm": start[2]},
                "end": {"x_mm": end[0], "y_mm": end[1], "z_mm": end[2]},
            },
            "section": {"shape": "rectangle", "width_mm": width, "height_mm": height},
        },
        "type_policy": "generated",
    }


def _column_op(operation_id: str, base: tuple, top: tuple, width: int, depth: int) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_column",
        "expected_target": {"storey_query": "frozen_per_case"},
        "parameters": {
            "axis": {
                "base": {"x_mm": base[0], "y_mm": base[1], "z_mm": base[2]},
                "top": {"x_mm": top[0], "y_mm": top[1], "z_mm": top[2]},
            },
            "section": {
                "shape": "rectangle",
                "width_mm": width,
                "depth_mm": depth,
                "orientation": {"x": 0, "y": 1},
            },
        },
        "type_policy": "generated",
    }


def _fill_door_op(operation_id: str, opening: dict, style: str) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "fill_existing_opening_with_door",
        "expected_target": {"opening_query": opening},
        "parameters": {
            "fit_existing_opening": True,
            "door": {"formal_enum_explicit": True, "operation_type": style},
        },
        "type_policy": "generated",
    }


def _add_door_op(
    operation_id: str, wall: dict, width: int, height: int, sill: int, offset: int, style: str
) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_door_with_opening_to_wall",
        "expected_target": {"wall_query": wall},
        "parameters": {
            "position": {"reference": "wall_local_start", "center_offset_mm": offset},
            "opening": {
                "width_mm": width,
                "height_mm": height,
                "sill_height_mm": sill,
                "dimension_meaning": "overall_opening",
            },
            "door": {
                "overall_width_mm": width,
                "overall_height_mm": height,
                "formal_enum_explicit": True,
                "operation_type": style,
            },
        },
        "type_policy": "generated",
    }


def _add_window_op(operation_id: str, wall: dict, width: int, height: int, sill: int, offset: int) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_window_with_opening_to_wall",
        "expected_target": {"wall_query": wall},
        "parameters": {
            "position": {"reference": "wall_local_start", "center_offset_mm": offset},
            "opening": {"width_mm": width, "height_mm": height, "sill_height_mm": sill},
            "window": {"fit_opening": True},
        },
        "type_policy": "generated",
    }


def _unsupported_op(operation_id: str) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "structural_analysis_node",
        "note": (
            "Verified absent from create_default_registry() "
            "(src/text2ifc_ifc_repair/operations/__init__.py:18-27). "
            "Intent capability checker classifies structural_analysis_* as "
            "STRUCTURAL_ANALYSIS_UNSUPPORTED "
            "(src/text2ifc_ifc_repair/request_stage.py:455-458)."
        ),
    }


# ---------------------------------------------------------------------------
# Frozen request texts (natural language, ONE coherent request per case)
# ---------------------------------------------------------------------------

C1_REQUEST = (
    "Renovate Level 5 of this building with a small structural addition in one "
    "atomic ChangeSet: add one horizontal straight rectangular Beam with center "
    "axis from (3500, -5500, 3500) mm to (5500, -5500, 3500) mm and a "
    "rectangular section 300 mm wide and 500 mm high, and add one vertical "
    "straight rectangular Column with center-axis base (3500, -5500, 0) mm and "
    "top (3500, -5500, 3500) mm, a section 400 mm wide and 600 mm deep, with "
    "local width direction (0, 1). Create both on the IFC Building Storey "
    "named \"Level 5\", generate a dedicated structural Type for each, and "
    "publish both modifications as one atomic transaction."
)

C2_REQUEST = (
    "On the ground floor storey \"00 begane grond\" of this building, complete "
    "a structural and envelope repair in one atomic ChangeSet: add two vertical "
    "straight rectangular Columns with center-axis base (36000, 12000, 0) mm "
    "and top (36000, 12000, 3600) mm, and base (40000, 16000, 0) mm and top "
    "(40000, 16000, 3600) mm respectively, each with a section 400 mm wide "
    "and 600 mm deep and local width direction (0, 1), generating a dedicated "
    "structural Type for each; and fill the currently empty wall opening that "
    "is 1170.000 mm wide, 2490.000 mm high, 3048.000 mm deep, with wall-local "
    "center offset 3795.000 mm and sill height 0.000 mm, by installing a "
    "SINGLE_SWING_LEFT door that fits that existing opening exactly, "
    "generating its door Type. All three modifications are mandatory and must "
    "be published as one atomic transaction."
)

C3_REQUEST = (
    "Renovate Level 5 of this building in one atomic ChangeSet: add two "
    "horizontal straight rectangular Beams with center axes from (3500, -5500, "
    "3500) mm to (5500, -5500, 3500) mm and from (3500, -3500, 3500) mm to "
    "(5500, -3500, 3500) mm, each with a rectangular section 300 mm wide and "
    "500 mm high; add two vertical straight rectangular Columns with "
    "center-axis bases (3500, -5500, 0) mm and (5500, -3500, 0) mm and tops "
    "(3500, -5500, 3500) mm and (5500, -3500, 3500) mm respectively, each with "
    "a section 400 mm wide and 600 mm deep and local width direction (0, 1); "
    "and add one new Window with its opening on the straight wall on this "
    "storey that runs south, is 8000 mm long, 4000 mm high and 200 mm thick "
    "(storey elevation 12000 mm), placing the window opening 1200 mm wide and "
    "1500 mm high with a 900 mm sill, centered 3000 mm from the wall start. "
    "Generate dedicated Types for every new element. All five modifications "
    "are mandatory and must be published as one atomic transaction."
)

C4_REQUEST = (
    "On the ground floor storey \"00 begane grond\" of this building, build one "
    "local structural and envelope modification in a single atomic ChangeSet: "
    "add four vertical straight rectangular Columns with center-axis "
    "base/top pairs (36000, 12000, 0)-(36000, 12000, 3600) mm, (40000, 12000, "
    "0)-(40000, 12000, 3600) mm, (36000, 18000, 0)-(36000, 18000, 3600) mm "
    "and (40000, 18000, 0)-(40000, 18000, 3600) mm, each with a section 400 "
    "mm wide and 600 mm deep and local width direction (0, 1); add one "
    "horizontal straight rectangular Beam with center axis from (36000, 15000, "
    "3600) mm to (40000, 15000, 3600) mm and a rectangular section 300 mm "
    "wide and 500 mm high; on the straight wall on this storey that runs "
    "south, is 10990.0 mm long, 4100.0 mm high and 300.0 mm thick (storey "
    "elevation 0 mm), add one new door with its opening, placing the door "
    "opening 900 mm wide and 2100 mm high with a 0 mm sill, centered 4000 mm "
    "from the wall start, using a SINGLE_SWING_RIGHT door; and add one new "
    "Window with its opening on the straight wall on this storey that runs "
    "east, is 21880.0 mm long, 4500.0 mm high and 250.0 mm thick (storey "
    "elevation 0 mm), placing the window opening 1500 mm wide and 1800 mm "
    "high with a 900 mm sill, centered 5000 mm from the wall start. Generate "
    "dedicated Types for every new element. All seven modifications are "
    "mandatory and must be published as one atomic transaction."
)

C5_REQUEST = (
    "Renovate one defined region of the storey named \"\u6807\u9ad82\" of this building "
    "as a single atomic ChangeSet. Structural part: add four vertical straight "
    "rectangular Columns with center-axis base/top pairs (20000, -20000, "
    "0)-(20000, -20000, 3600) mm, (26000, -20000, 0)-(26000, -20000, 3600) "
    "mm, (20000, -14000, 0)-(20000, -14000, 3600) mm and (26000, -14000, "
    "0)-(26000, -14000, 3600) mm, each with a section 400 mm wide and 600 mm "
    "deep and local width direction (0, 1); and add two horizontal straight "
    "rectangular Beams with center axes from (20000, -17000, 3600) mm to "
    "(26000, -17000, 3600) mm and from (20000, -14000, 3600) mm to (26000, "
    "-14000, 3600) mm, each with a rectangular section 300 mm wide and 500 mm "
    "high. Envelope part: on the straight wall on this storey that runs east, "
    "is 2644.0 mm long, 3581.7 mm high and 180.0 mm thick (storey elevation "
    "-2213.701 mm), add one new door with its opening, placing the door "
    "opening 900 mm wide and 2100 mm high with a 0 mm sill, centered 1300 mm "
    "from the wall start, using a SINGLE_SWING_LEFT door, and set that new "
    "door's fire rating to EI60; and add one new Window with its opening on "
    "the straight wall on this storey that runs east, is 4609.0 mm long, "
    "3581.7 mm high and 260.0 mm thick (storey elevation -2213.701 mm), "
    "placing the window opening 1200 mm wide and 1500 mm high with a 900 mm "
    "sill, centered 2000 mm from the wall start, and mark that new window as "
    "an external window. Generate dedicated Types for every new element. All "
    "these modifications are mandatory and must be published together as one "
    "atomic transaction."
)

C5N_REQUEST = (
    "Renovate one defined region of the storey named \"\u6807\u9ad82\" of this building "
    "as a single atomic ChangeSet. Structural part: add four vertical straight "
    "rectangular Columns with center-axis base/top pairs (20000, -20000, "
    "0)-(20000, -20000, 3600) mm, (26000, -20000, 0)-(26000, -20000, 3600) "
    "mm, (20000, -14000, 0)-(20000, -14000, 3600) mm and (26000, -14000, "
    "0)-(26000, -14000, 3600) mm, each with a section 400 mm wide and 600 mm "
    "deep and local width direction (0, 1); and add two horizontal straight "
    "rectangular Beams with center axes from (20000, -17000, 3600) mm to "
    "(26000, -17000, 3600) mm and from (20000, -14000, 3600) mm to (26000, "
    "-14000, 3600) mm, each with a rectangular section 300 mm wide and 500 mm "
    "high. Envelope part: on the straight wall on this storey that runs east, "
    "is 2644.0 mm long, 3581.7 mm high and 180.0 mm thick (storey elevation "
    "-2213.701 mm), add one new door with its opening, placing the door "
    "opening 900 mm wide and 2100 mm high with a 0 mm sill, centered 1300 mm "
    "from the wall start, using a SINGLE_SWING_LEFT door, and set that new "
    "door's fire rating to EI60; and add one new Window with its opening on "
    "the straight wall on this storey that runs east, is 4609.0 mm long, "
    "3581.7 mm high and 260.0 mm thick (storey elevation -2213.701 mm), "
    "placing the window opening 1200 mm wide and 1500 mm high with a 900 mm "
    "sill, centered 2000 mm from the wall start, and mark that new window as "
    "an external window. Additionally, create a structural analysis node for "
    "this renovation. All these modifications are mandatory and must be "
    "published together as one atomic transaction."
)


# ---------------------------------------------------------------------------
# Case assembly
# ---------------------------------------------------------------------------

VVO_STOREY = "1vTeahUkP60PdWqwCTjSGJ"
S65_GROUND = "02GkOQJZz4x9WAhoZkM67S"
TALL_L5 = "2nxdYR2RHCDBiKJuiQqMQj"

VVO_DOOR_WALL = _wall_query(
    length_mm=2644.0,
    height_mm=3581.7,
    thickness_mm=180.0,
    direction="east",
    storey_elevation_mm=-2213.701,
)
VVO_WINDOW_WALL = _wall_query(
    length_mm=4609.0,
    height_mm=3581.7,
    thickness_mm=260.0,
    direction="east",
    storey_elevation_mm=-2213.701,
)
S65_DOOR_OPENING = _opening_query(
    width_mm=1170.000,
    height_mm=2490.000,
    depth_mm=3048.000,
    center_offset_mm=3795.000,
    sill_height_mm=0.000,
)
S65_DOOR_ADD_WALL = _wall_query(
    length_mm=10990.0,
    height_mm=4100.0,
    thickness_mm=300.0,
    direction="south",
    storey_elevation_mm=0.0,
    tolerance_mm=0.05,
)
S65_WINDOW_WALL = _wall_query(
    length_mm=21880.0,
    height_mm=4500.0,
    thickness_mm=250.0,
    direction="east",
    storey_elevation_mm=0.0,
    tolerance_mm=0.05,
)
TALL_WINDOW_WALL = _wall_query(
    length_mm=8000.0,
    height_mm=4000.0,
    thickness_mm=200.0,
    direction="south",
    storey_elevation_mm=12000.0,
)


def _structural_predicates(operations: list[dict], case_id: str) -> list[dict]:
    predicates = []
    for op in operations:
        if op["operation_type"] == "add_beam":
            axis = op["parameters"]["axis"]
            section = op["parameters"]["section"]
            predicates.append(
                {
                    "predicate_id": f"{case_id}-{op['operation_id']}",
                    "operation_id": op["operation_id"],
                    "operation_type": "add_beam",
                    "kind": "structural_add",
                    "storey_global_id": None,
                    "axis_start_mm": [
                        axis["start"]["x_mm"],
                        axis["start"]["y_mm"],
                        axis["start"]["z_mm"],
                    ],
                    "axis_end_mm": [
                        axis["end"]["x_mm"],
                        axis["end"]["y_mm"],
                        axis["end"]["z_mm"],
                    ],
                    "section_width_mm": section["width_mm"],
                    "section_height_mm": section["height_mm"],
                    "type_policy": "generated",
                }
            )
        elif op["operation_type"] == "add_column":
            axis = op["parameters"]["axis"]
            section = op["parameters"]["section"]
            predicates.append(
                {
                    "predicate_id": f"{case_id}-{op['operation_id']}",
                    "operation_id": op["operation_id"],
                    "operation_type": "add_column",
                    "kind": "structural_add",
                    "storey_global_id": None,
                    "axis_start_mm": [
                        axis["base"]["x_mm"],
                        axis["base"]["y_mm"],
                        axis["base"]["z_mm"],
                    ],
                    "axis_end_mm": [
                        axis["top"]["x_mm"],
                        axis["top"]["y_mm"],
                        axis["top"]["z_mm"],
                    ],
                    "section_width_mm": section["width_mm"],
                    "section_height_mm": section["depth_mm"],
                    "orientation_xy": [0, 1],
                    "type_policy": "generated",
                }
            )
    return predicates


def _hosted_predicates(operations: list[dict], case_id: str) -> list[dict]:
    predicates = []
    for op in operations:
        if op["operation_type"] == "fill_existing_opening_with_door":
            predicates.append(
                {
                    "predicate_id": f"{case_id}-{op['operation_id']}",
                    "operation_id": op["operation_id"],
                    "operation_type": "fill_existing_opening_with_door",
                    "kind": "door_fill",
                    "target_query": op["expected_target"]["opening_query"],
                    "door_style": op["parameters"]["door"]["operation_type"],
                }
            )
        elif op["operation_type"] == "add_door_with_opening_to_wall":
            predicates.append(
                {
                    "predicate_id": f"{case_id}-{op['operation_id']}",
                    "operation_id": op["operation_id"],
                    "operation_type": "add_door_with_opening_to_wall",
                    "kind": "door_add",
                    "target_query": op["expected_target"]["wall_query"],
                    "opening_width_mm": op["parameters"]["opening"]["width_mm"],
                    "opening_height_mm": op["parameters"]["opening"]["height_mm"],
                    "sill_height_mm": op["parameters"]["opening"]["sill_height_mm"],
                    "center_offset_mm": op["parameters"]["position"]["center_offset_mm"],
                    "door_style": op["parameters"]["door"]["operation_type"],
                }
            )
        elif op["operation_type"] == "add_window_with_opening_to_wall":
            predicates.append(
                {
                    "predicate_id": f"{case_id}-{op['operation_id']}",
                    "operation_id": op["operation_id"],
                    "operation_type": "add_window_with_opening_to_wall",
                    "kind": "window_add",
                    "target_query": op["expected_target"]["wall_query"],
                    "opening_width_mm": op["parameters"]["opening"]["width_mm"],
                    "opening_height_mm": op["parameters"]["opening"]["height_mm"],
                    "sill_height_mm": op["parameters"]["opening"]["sill_height_mm"],
                    "center_offset_mm": op["parameters"]["position"]["center_offset_mm"],
                }
            )
    return predicates


def _atomic_predicate(case_id: str, operations: list[dict]) -> dict:
    return {
        "predicate_id": f"{case_id}-atomic",
        "kind": "atomic_operation_set",
        "operation_ids": [op["operation_id"] for op in operations],
    }


def _entity_delta(operations: list[dict]) -> dict:
    beams = sum(1 for op in operations if op["operation_type"] == "add_beam")
    columns = sum(1 for op in operations if op["operation_type"] == "add_column")
    doors = sum(
        1
        for op in operations
        if op["operation_type"]
        in ("fill_existing_opening_with_door", "add_door_with_opening_to_wall")
    )
    door_openings = sum(
        1
        for op in operations
        if op["operation_type"] == "add_door_with_opening_to_wall"
    )
    windows = sum(
        1
        for op in operations
        if op["operation_type"] == "add_window_with_opening_to_wall"
    )
    return {
        "IfcBeam": beams,
        "IfcColumn": columns,
        "IfcDoor": doors,
        "IfcWindow": windows,
        "IfcBeamType": beams,
        "IfcColumnType": columns,
        "IfcDoorStyle": doors,
        "IfcWindowStyle": windows,
        "IfcOpeningElement": windows + door_openings,
    }


def _case(
    *,
    case_id: str,
    difficulty: str,
    model_id: str,
    request: str,
    operations: list[dict],
    storey_global_id: str,
    storey_name: str,
    property_intents: list[dict] | None = None,
    expected_terminal_class: str = "SUCCESS",
    negative: bool = False,
    unsupported_operations: list[dict] | None = None,
) -> dict:
    property_intents = property_intents or []
    predicates = []
    if not negative:
        predicates.extend(_structural_predicates(operations, case_id))
        predicates.extend(_hosted_predicates(operations, case_id))
        for intent in property_intents:
            predicates.append(
                {
                    "predicate_id": f"{case_id}-{intent['scope_operation_id']}-property",
                    "operation_id": intent["scope_operation_id"],
                    "operation_type": intent["scope_operation_type"],
                    "kind": "generated_occurrence_property",
                    "property": {
                        "set_name": intent["set_name"],
                        "property_name": intent["property_name"],
                        "value_type": intent["value_type"],
                        "value": intent["value"],
                        "scope": "occurrence_direct",
                    },
                }
            )
        predicates.append(_atomic_predicate(case_id, operations))
    return {
        "case_id": case_id,
        "difficulty": difficulty,
        "model_id": model_id,
        "request": request,
        "request_sha256": _sha256_text(request),
        "scale": {
            "operation_count": len(operations),
            "entity_operation_count": len(operations),
            "property_intent_count": len(property_intents),
            "families": sorted(
                {
                    {
                        "add_beam": "beam",
                        "add_column": "column",
                        "fill_existing_opening_with_door": "door",
                        "add_door_with_opening_to_wall": "door",
                        "add_window_with_opening_to_wall": "window",
                        "structural_analysis_node": "structural_analysis",
                    }[op["operation_type"]]
                    for op in operations
                }
            ),
        },
        "storey": {"global_id": storey_global_id, "name": storey_name},
        "operations": operations,
        "unsupported_operations": unsupported_operations or [],
        "property_intents": property_intents,
        "expected_terminal_class": expected_terminal_class,
        "required_atomicity": "all_or_nothing",
        "expected_entity_delta": _entity_delta(operations),
        "type_policy": "generated",
        "artifact_predicates": predicates,
        "property_resolution_involved": bool(property_intents),
        "provider_stages_expected": (
            ["stage1"]
            if negative
            else (["stage1", "property_resolution", "stage2"] if property_intents else ["stage1", "stage2"])
        ),
        "reopen_requirement": "IFC2X3 reopen + L0/L1/L2 recompute" if not negative else "zero model mutation (no publication)",
        "preservation_requirement": (
            "whole-model exact authorized delta only"
            if not negative
            else "byte-identical source; no candidate output"
        ),
    }


def build_cases() -> list[dict]:
    cases = []

    # ---- C1: small composite (TALL Level 5): beam x1 + column x1 ----------
    c1_ops = [
        _beam_op("C1-beam-01", (3500, -5500, 3500), (5500, -5500, 3500), 300, 500),
        _column_op("C1-column-01", (3500, -5500, 0), (3500, -5500, 3500), 400, 600),
    ]
    cases.append(
        _case(
            case_id="C1",
            difficulty="small",
            model_id="CM-TALL",
            request=C1_REQUEST,
            operations=c1_ops,
            storey_global_id=TALL_L5,
            storey_name="Level 5",
        )
    )

    # ---- C2: medium composite (S65 ground): column x2 + door fill x1 -----
    c2_ops = [
        _column_op("C2-column-01", (36000, 12000, 0), (36000, 12000, 3600), 400, 600),
        _column_op("C2-column-02", (40000, 16000, 0), (40000, 16000, 3600), 400, 600),
        _fill_door_op("C2-door-01", S65_DOOR_OPENING, "SINGLE_SWING_LEFT"),
    ]
    cases.append(
        _case(
            case_id="C2",
            difficulty="medium",
            model_id="CM-S65",
            request=C2_REQUEST,
            operations=c2_ops,
            storey_global_id=S65_GROUND,
            storey_name="00 begane grond",
        )
    )

    # ---- C3: multi-family composite (TALL Level 5): beam x2 + column x2 + window x1
    c3_ops = [
        _beam_op("C3-beam-01", (3500, -5500, 3500), (5500, -5500, 3500), 300, 500),
        _beam_op("C3-beam-02", (3500, -3500, 3500), (5500, -3500, 3500), 300, 500),
        _column_op("C3-column-01", (3500, -5500, 0), (3500, -5500, 3500), 400, 600),
        _column_op("C3-column-02", (5500, -3500, 0), (5500, -3500, 3500), 400, 600),
        _add_window_op("C3-window-01", TALL_WINDOW_WALL, 1200, 1500, 900, 3000),
    ]
    cases.append(
        _case(
            case_id="C3",
            difficulty="multi-family",
            model_id="CM-TALL",
            request=C3_REQUEST,
            operations=c3_ops,
            storey_global_id=TALL_L5,
            storey_name="Level 5",
        )
    )

    # ---- C4: large composite (S65 ground): column x4 + beam x1 + door add x1 + window x1
    c4_ops = [
        _column_op("C4-column-01", (36000, 12000, 0), (36000, 12000, 3600), 400, 600),
        _column_op("C4-column-02", (40000, 12000, 0), (40000, 12000, 3600), 400, 600),
        _column_op("C4-column-03", (36000, 18000, 0), (36000, 18000, 3600), 400, 600),
        _column_op("C4-column-04", (40000, 18000, 0), (40000, 18000, 3600), 400, 600),
        _beam_op("C4-beam-01", (36000, 15000, 3600), (40000, 15000, 3600), 300, 500),
        _add_door_op("C4-door-01", S65_DOOR_ADD_WALL, 900, 2100, 0, 4000, "SINGLE_SWING_RIGHT"),
        _add_window_op("C4-window-01", S65_WINDOW_WALL, 1500, 1800, 900, 16000),
    ]
    cases.append(
        _case(
            case_id="C4",
            difficulty="large",
            model_id="CM-S65",
            request=C4_REQUEST,
            operations=c4_ops,
            storey_global_id=S65_GROUND,
            storey_name="00 begane grond",
        )
    )

    # ---- C5 HERO (vvo 标高2): column x4 + beam x2 + door add x1 + window x1 + 2 property intents
    c5_ops = [
        _column_op("C5-column-01", (20000, -20000, 0), (20000, -20000, 3600), 400, 600),
        _column_op("C5-column-02", (26000, -20000, 0), (26000, -20000, 3600), 400, 600),
        _column_op("C5-column-03", (20000, -14000, 0), (20000, -14000, 3600), 400, 600),
        _column_op("C5-column-04", (26000, -14000, 0), (26000, -14000, 3600), 400, 600),
        _beam_op("C5-beam-01", (20000, -17000, 3600), (26000, -17000, 3600), 300, 500),
        _beam_op("C5-beam-02", (20000, -14000, 3600), (26000, -14000, 3600), 300, 500),
        _add_door_op("C5-door-01", VVO_DOOR_WALL, 900, 2100, 0, 1300, "SINGLE_SWING_LEFT"),
        _add_window_op("C5-window-01", VVO_WINDOW_WALL, 1200, 1500, 900, 2000),
    ]
    c5_properties = [
        {
            "scope_operation_id": "C5-door-01",
            "scope_operation_type": "add_door_with_opening_to_wall",
            "set_name": "Pset_DoorCommon",
            "property_name": "FireRating",
            "value_type": "IfcLabel",
            "value": "EI60",
            "natural_language": "set that new door's fire rating to EI60",
        },
        {
            "scope_operation_id": "C5-window-01",
            "scope_operation_type": "add_window_with_opening_to_wall",
            "set_name": "Pset_WindowCommon",
            "property_name": "IsExternal",
            "value_type": "IfcBoolean",
            "value": True,
            "natural_language": "mark that new window as an external window",
        },
    ]
    cases.append(
        _case(
            case_id="C5",
            difficulty="hero",
            model_id="CM-VVO",
            request=C5_REQUEST,
            operations=c5_ops,
            storey_global_id=VVO_STOREY,
            storey_name="标高2",
            property_intents=c5_properties,
        )
    )

    # ---- C5-N: negative twin (same structure + unsupported op) ------------
    c5n_ops = list(c5_ops)
    cases.append(
        _case(
            case_id="C5-N",
            difficulty="hero-negative",
            model_id="CM-VVO",
            request=C5N_REQUEST,
            operations=c5n_ops,
            storey_global_id=VVO_STOREY,
            storey_name="标高2",
            property_intents=c5_properties,
            expected_terminal_class="UNSUPPORTED_ATOMIC_GUARD",
            negative=True,
            unsupported_operations=[_unsupported_op("C5N-analysis-node-01")],
        )
    )
    return cases


def _render_markdown(freeze: dict) -> str:
    lines = []
    lines.append("# Composite Bound Test Cases — Text2IFC Composite Repair Milestone")
    lines.append("")
    lines.append(
        f"**Status:** frozen at base revision `{freeze['base_revision']}` "
        f"(branch `{freeze['branch']}`)."
    )
    lines.append("")
    lines.append(
        "Machine-readable twin: `composite-acceptance-freeze.json` "
        f"(sha256 `{freeze['freeze_sha256']}`). Case meaning does not change "
        "after genuine execution begins."
    )
    lines.append("")
    lines.append("## Execution order")
    lines.append("")
    lines.append("`C1 → C2 → C3 → C4 → C5 → C5-N`")
    lines.append("")
    for case in freeze["cases"]:
        lines.append(f"## {case['case_id']} — {case['difficulty']} composite ({case['model_id']})")
        lines.append("")
        lines.append(f"**Storey:** `{case['storey']['global_id']}` ({case['storey']['name']})")
        lines.append("")
        lines.append(f"**Target operation count:** {case['scale']['operation_count']} "
                     f"(families: {', '.join(case['scale']['families'])}; "
                     f"property intents: {case['scale']['property_intent_count']})")
        lines.append("")
        lines.append("**Exact frozen request:**")
        lines.append("")
        lines.append("> " + case["request"].replace("\n", "\n> "))
        lines.append("")
        lines.append(f"**Request SHA-256:** `{case['request_sha256']}`")
        lines.append("")
        lines.append("**Frozen operation bindings:**")
        lines.append("")
        lines.append("| operation_id | operation_type | frozen binding |")
        lines.append("| --- | --- | --- |")
        for op in case["operations"]:
            binding = json.dumps(op.get("parameters"), ensure_ascii=False)
            lines.append(
                f"| `{op['operation_id']}` | `{op['operation_type']}` | "
                f"`{binding[:160]}{'…' if len(binding) > 160 else ''}` |"
            )
        for op in case.get("unsupported_operations", []):
            lines.append(
                f"| `{op['operation_id']}` | `{op['operation_type']}` | "
                "UNSUPPORTED (verified absent from registry) |"
            )
        lines.append("")
        lines.append(f"**Expected terminal class:** `{case['expected_terminal_class']}`")
        lines.append("")
        lines.append(f"**Atomicity:** {case['required_atomicity']}")
        lines.append("")
        lines.append(
            "**Expected entity delta:** "
            + ", ".join(
                f"`{cls}` +{count}"
                for cls, count in case["expected_entity_delta"].items()
                if count
            )
        )
        lines.append("")
        lines.append(f"**Type policy:** {case['type_policy']}")
        lines.append("")
        lines.append(
            f"**Property resolution involved:** {case['property_resolution_involved']}"
        )
        lines.append("")
        lines.append(
            f"**Provider stages expected:** {', '.join(case['provider_stages_expected'])}"
        )
        lines.append("")
        lines.append(f"**Reopen:** {case['reopen_requirement']}")
        lines.append("")
        lines.append(f"**Preservation:** {case['preservation_requirement']}")
        lines.append("")
        lines.append("**Operation-bound artifact predicates:**")
        lines.append("")
        lines.append("| predicate_id | operation_id | operation_type | kind |")
        lines.append("| --- | --- | --- | --- |")
        for pred in case["artifact_predicates"]:
            lines.append(
                f"| `{pred['predicate_id']}` | `{pred.get('operation_id', '—')}` | "
                f"`{pred.get('operation_type', '—')}` | `{pred['kind']}` |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    if FREEZE_PATH.exists():
        print(f"ERROR: freeze already exists: {FREEZE_PATH}", file=sys.stderr)
        return 2
    cases = build_cases()
    import subprocess

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    freeze = {
        "schema_version": SCHEMA_VERSION,
        "provenance_namespace": PROVENANCE_NAMESPACE,
        "base_revision": head,
        "branch": branch,
        "created_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "models": MODELS,
        "execution_order": [case["case_id"] for case in cases],
        "cases": cases,
        "production_private_boundary": {
            "forbid_pristine_comparator_gold": True,
            "forbid_mutation_truth": True,
            "forbid_deleted_identities": True,
            "forbid_existing_proof_reuse": True,
            "forbid_synthetic_cached_fallback": True,
            "public_bindings_only": True,
        },
        "stop_rules": {
            "stop_on_deterministic_defect": True,
            "stop_on_infrastructure_defect": True,
            "preserve_every_genuine_provider_attempt": True,
            "never_replace_failed_case": True,
            "geometry_frozen_before_provider_execution": True,
        },
    }
    payload = json.dumps(freeze, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    freeze["freeze_sha256"] = _sha256_text(payload)
    # Recompute payload with the hash included (self-referential freeze hash is
    # stored alongside, computed over the hash-less payload).
    final_payload = json.dumps(freeze, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FREEZE_PATH.write_text(final_payload, encoding="utf-8", newline="\n")
    MARKDOWN_PATH.write_text(_render_markdown(freeze), encoding="utf-8", newline="\n")
    print(f"froze {len(cases)} cases -> {FREEZE_PATH}")
    print(f"freeze_sha256 (over hash-less payload) = {freeze['freeze_sha256']}")
    for case in cases:
        print(
            f"  {case['case_id']}: {case['scale']['operation_count']} ops, "
            f"families={case['scale']['families']}, "
            f"terminal={case['expected_terminal_class']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
