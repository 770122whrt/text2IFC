from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


IDENTITY_PSET = "Pset_text2IFCIdentity"
IDENTITY_PROPERTY = "BimJsonId"
AXES = ("x", "y", "z")


@dataclass(frozen=True)
class GeneratedIfcCheckResult:
    success: bool
    issues: list[dict[str, Any]]
    metrics: dict[str, Any]


def check_generated_ifc(
    ifc_path: str | Path,
    expectation: Mapping[str, Any],
) -> GeneratedIfcCheckResult:
    model = ifcopenshell.open(str(Path(ifc_path)))
    products_by_id = _products_by_bim_json_id(model)
    tolerance = float(expectation.get("tolerance", 0.01))
    issues: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {
        "case_id": expectation.get("case_id"),
        "walls": {},
    }

    wall_had_geometry_issue = False
    for wall_id, expected_wall in expectation.get("walls", {}).items():
        wall = products_by_id.get(wall_id)
        if wall is None:
            wall_had_geometry_issue = True
            issues.append(
                _issue(
                    "MISSING_WALL",
                    f"/walls/{wall_id}",
                    f"Expected wall {wall_id!r} was not found in the IFC.",
                )
            )
            continue

        actual_bbox = _bbox_for_product(wall)
        actual_axis = _dominant_plan_axis(actual_bbox)
        metrics["walls"][wall_id] = {
            "ifc_class": wall.is_a(),
            "axis": actual_axis,
            "bbox": actual_bbox,
        }

        expected_axis = expected_wall.get("axis")
        if expected_axis and actual_axis != expected_axis:
            wall_had_geometry_issue = True
            issues.append(
                _issue(
                    "WALL_ORIENTATION_MISMATCH",
                    f"/walls/{wall_id}/axis",
                    (
                        f"Wall {wall_id!r} has dominant plan axis {actual_axis!r}; "
                        f"expected {expected_axis!r}."
                    ),
                )
            )

        expected_bbox = expected_wall.get("bbox")
        if expected_bbox and not _bbox_matches(actual_bbox, expected_bbox, tolerance):
            wall_had_geometry_issue = True
            issues.append(
                _issue(
                    "WALL_BBOX_MISMATCH",
                    f"/walls/{wall_id}/bbox",
                    f"Wall {wall_id!r} world bounding box is outside tolerance.",
                )
            )

    if wall_had_geometry_issue and expectation.get("walls"):
        issues.append(
            _issue(
                "ROOM_ENCLOSURE_OPEN",
                "/walls",
                "Expected wall geometry does not form the required room enclosure.",
            )
        )

    return GeneratedIfcCheckResult(
        success=not issues,
        issues=issues,
        metrics=metrics,
    )


def _products_by_bim_json_id(model: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for product in model.by_type("IfcProduct"):
        psets = ifcopenshell.util.element.get_psets(product)
        bim_json_id = psets.get(IDENTITY_PSET, {}).get(IDENTITY_PROPERTY)
        if bim_json_id:
            result[str(bim_json_id)] = product
    return result


def _bbox_for_product(product: Any) -> dict[str, list[float]]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, product)
    vertices = shape.geometry.verts
    if not vertices:
        raise ValueError(f"Product {product.id()} has no shape vertices.")
    coordinates = {
        axis: list(vertices[index::3])
        for index, axis in enumerate(AXES)
    }
    return {
        axis: [float(min(values)), float(max(values))]
        for axis, values in coordinates.items()
    }


def _dominant_plan_axis(bbox: Mapping[str, list[float]]) -> str:
    x_extent = bbox["x"][1] - bbox["x"][0]
    y_extent = bbox["y"][1] - bbox["y"][0]
    return "x" if x_extent >= y_extent else "y"


def _bbox_matches(
    actual: Mapping[str, list[float]],
    expected: Mapping[str, list[float]],
    tolerance: float,
) -> bool:
    for axis in AXES:
        actual_range = actual[axis]
        expected_range = expected[axis]
        if abs(actual_range[0] - expected_range[0]) > tolerance:
            return False
        if abs(actual_range[1] - expected_range[1]) > tolerance:
            return False
    return True


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}
