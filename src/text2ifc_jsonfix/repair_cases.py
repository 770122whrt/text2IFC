"""Deterministic natural-language repair cases for jsonfix."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from text2ifc_contract.validation_v2 import validate_v2_document

from .composer import compose_patches
from .validation import validate_patch_document


REPAIR_CASE_SCHEMA_VERSION = "text2ifc/jsonfix-repair-case-v1"
DEFAULT_CASE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "dataset"
    / "processed"
    / "jsonfix"
)


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


def _rectangle(length: float, thickness: float, height: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {
            "kind": "rectangle",
            "x": length,
            "y": thickness,
        },
        "depth": height,
        "direction": [0, 0, 1],
    }


def _entity(
    entity_id: str,
    ifc_class: str,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "jsonfix-base-fixture"},
    }


def _wall(
    wall_id: str,
    origin: list[float],
    length: float,
    ref_direction: list[float] | None = None,
    *,
    ifc_class: str = "IfcWall",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wall = _entity(
        wall_id,
        ifc_class,
        {
            "Name": wall_id,
            "ObjectPlacement": _placement(
                "storey-1", origin, ref_direction
            ),
            "Representation": _rectangle(length, 200, 3000),
        },
    )
    if provenance is not None:
        wall["provenance"] = provenance
    return wall


def _base_document() -> dict[str, Any]:
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _entity(
                "project-1",
                "IfcProject",
                {"Name": "jsonfix Missing Piece Repair"},
            ),
            _entity(
                "site-1",
                "IfcSite",
                {
                    "Name": "Site",
                    "ObjectPlacement": _placement("project-1"),
                },
            ),
            _entity(
                "building-1",
                "IfcBuilding",
                {
                    "Name": "Building",
                    "ObjectPlacement": _placement("site-1"),
                },
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
                    "Representation": {
                        "kind": "extruded_profile",
                        "profile": {
                            "kind": "polygon",
                            "points": [
                                [0, 0],
                                [6000, 0],
                                [6000, 4000],
                                [0, 4000],
                                [0, 0],
                            ],
                        },
                        "depth": 3000,
                        "direction": [0, 0, 1],
                    },
                },
            ),
            _wall("wall-south", [3000, 0, 0], 6000),
            _wall("wall-north", [3000, 4000, 0], 6000),
            _wall(
                "wall-east",
                [6000, 2000, 0],
                4000,
                [0, 1, 0],
            ),
        ],
        "relationships": [],
        "provenance": {
            "source": "jsonfix-base-fixture",
            "document_id": "jsonfix-missing-piece-base",
        },
    }


def _west_wall() -> dict[str, Any]:
    return _wall(
        "wall-west",
        [0, 2000, 0],
        4000,
        [0, 1, 0],
        ifc_class="IfcWallStandardCase",
        provenance={
            "source": "user-patch",
            "layer_id": "user-add-west-wall",
        },
    )


def _patch() -> dict[str, Any]:
    return {
        "patch_version": "bim-json-patch/1.0",
        "target_schema_version": "bim-json/2.0",
        "target_ifc_schema": "IFC2X3",
        "target_document_id": "jsonfix-missing-piece-base",
        "layers": [
            {
                "id": "user-add-west-wall",
                "kind": "user",
                "provenance": {
                    "source": "user-natural-language",
                    "request_id": "missing-piece-repair",
                    "prompt_version": "semantic-patch-v1",
                },
                "operations": [
                    {
                        "op": "add_entity",
                        "target": {
                            "collection": "entities",
                            "id": "wall-west",
                        },
                        "value": _west_wall(),
                    }
                ],
            }
        ],
    }


def _quality_expectation() -> dict[str, Any]:
    return {
        "case_id": "missing-piece-repair",
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
    }


def repair_case(case_id: str) -> dict[str, Any]:
    if case_id != "missing-piece-repair":
        raise ValueError(f"Unknown jsonfix repair case: {case_id}")
    base = _base_document()
    patch = _patch()
    result = compose_patches(base, [patch])
    if validate_v2_document(base):
        raise ValueError("Repair case base document is not Formal BIM JSON 2.0.")
    if validate_patch_document(patch):
        raise ValueError("Repair case patch does not satisfy the patch contract.")
    if not result.valid:
        raise ValueError("Repair case patch does not compose to a Formal candidate.")
    return {
        "case_id": case_id,
        "input_text": (
            "现有一个长6000毫米、宽4000毫米、高3000毫米的单层房间，"
            "目前缺少西墙。请补上一面厚200毫米、长4000毫米、高3000毫米的"
            "西墙，沿Y方向，中心位于(0, 2000, 0)，归属storey-1，"
            "使四面墙闭合。不要修改其他构件。"
        ),
        "base": base,
        "patch": patch,
        "expected": result.document,
        "metadata": {
            "schema_version": REPAIR_CASE_SCHEMA_VERSION,
            "case_id": case_id,
            "target_ifc_schema": "IFC2X3",
            "expected_facts": {
                "added_entity_ids": ["wall-west"],
                "unchanged_entity_ids": [
                    item["id"] for item in base["entities"]
                ],
                "patch_operation_count": 1,
            },
            "quality": _quality_expectation(),
        },
    }


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(text)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _write_json_atomic(path: Path, value: Any) -> None:
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )
    _write_text_atomic(path, text + "\n")


def build_repair_case(
    case_id: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    case = repair_case(case_id)
    output = output_dir or DEFAULT_CASE_ROOT / case_id
    _write_text_atomic(output / "input.txt", case["input_text"] + "\n")
    _write_json_atomic(output / "base.json", case["base"])
    _write_json_atomic(output / "patch.json", case["patch"])
    _write_json_atomic(output / "expected.json", case["expected"])
    _write_json_atomic(output / "metadata.json", case["metadata"])
    return {
        "success": True,
        "case_id": case_id,
        "output_dir": str(output),
        "formal_valid": not validate_v2_document(case["expected"]),
        "patch_valid": not validate_patch_document(case["patch"]),
    }
