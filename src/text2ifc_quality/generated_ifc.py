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
    selected_result: GeneratedIfcCheckResult | None = None
    for convention, walls in _wall_expectation_sets(expectation):
        result = _check_wall_set(
            products_by_id=products_by_id,
            tolerance=tolerance,
            case_id=expectation.get("case_id"),
            convention=convention,
            walls=walls,
        )
        if result.success:
            selected_result = result
            break
        if selected_result is None:
            selected_result = result
    if selected_result is None:
        selected_result = GeneratedIfcCheckResult(
            success=False,
            issues=[
                _issue(
                    "GEOMETRY_EXPECTATION_UNAVAILABLE",
                    "/geometry-expectation",
                    "No wall expectation set was available for hard geometry verification.",
                )
            ],
            metrics={"case_id": expectation.get("case_id"), "walls": {}},
        )
    slab_result = _check_slabs(
        products_by_id=products_by_id,
        tolerance=tolerance,
        expectation=expectation,
        wall_result=selected_result,
    )
    result = _check_roof_stairs_and_openings(
        products_by_id=products_by_id,
        tolerance=tolerance,
        expectation=expectation,
        prior_result=slab_result,
    )
    if expectation.get("complete") is not False:
        return result

    issues = list(result.issues)
    unresolved = expectation.get("unresolved")
    unresolved_records = (
        [item for item in unresolved if isinstance(item, Mapping)]
        if isinstance(unresolved, list)
        else []
    )
    if not unresolved_records:
        unresolved_records = [
            {
                "path": "/geometry-expectation",
                "reason": "required_geometry_expectation_incomplete",
                "source_fact_refs": [],
            }
        ]
    for record in unresolved_records:
        reason = str(record.get("reason", "required_geometry_expectation_incomplete"))
        issues.append(
            _issue(
                "GEOMETRY_EXPECTATION_INCOMPLETE",
                str(record.get("path", "/geometry-expectation")),
                "Required geometry could not be derived from confirmed facts.",
                actual={"reason": reason},
                source_fact_refs=record.get("source_fact_refs"),
            )
        )
    metrics = dict(result.metrics)
    metrics["expectation_complete"] = False
    metrics["unresolved_expectation_count"] = len(unresolved_records)
    return GeneratedIfcCheckResult(success=False, issues=issues, metrics=metrics)


def _check_roof_stairs_and_openings(
    *,
    products_by_id: Mapping[str, Any],
    tolerance: float,
    expectation: Mapping[str, Any],
    prior_result: GeneratedIfcCheckResult,
) -> GeneratedIfcCheckResult:
    issues = list(prior_result.issues)
    metrics = dict(prior_result.metrics)
    metrics["roof"] = _check_component_bboxes(
        products_by_id=products_by_id,
        expected_components=expectation.get("roof"),
        tolerance=tolerance,
        missing_code="MISSING_ROOF",
        mismatch_code="ROOF_BBOX_MISMATCH",
        path_prefix="roof",
        issues=issues,
    )
    metrics["floor_openings"] = _check_component_bboxes(
        products_by_id=products_by_id,
        expected_components=expectation.get("floor_openings"),
        tolerance=tolerance,
        missing_code="MISSING_STAIR_OPENING",
        mismatch_code="STAIR_OPENING_BBOX_MISMATCH",
        path_prefix="floor_openings",
        issues=issues,
    )
    stair_metrics: dict[str, Any] = {}
    expected_stairs = expectation.get("stairs")
    if isinstance(expected_stairs, Mapping):
        for stair_id, expected_stair in expected_stairs.items():
            if not isinstance(expected_stair, Mapping):
                continue
            flight_ids = expected_stair.get("flight_ids", [])
            if not isinstance(flight_ids, list):
                flight_ids = []
            flights = [
                products_by_id.get(str(flight_id)) for flight_id in flight_ids
            ]
            flights = [flight for flight in flights if flight is not None]
            if not flights:
                issues.append(
                    _issue(
                        "MISSING_STAIR_FLIGHT",
                        f"/stairs/{stair_id}",
                        f"Expected stair {stair_id!r} has no checkable IfcStairFlight.",
                        entity_ids=[str(stair_id), *[str(item) for item in flight_ids]],
                        source_fact_refs=expected_stair.get("source_fact_refs"),
                    )
                )
                continue
            actual_bbox = _combined_bbox([_bbox_for_product(flight) for flight in flights])
            stair_metrics[str(stair_id)] = {
                "flight_ids": [str(item) for item in flight_ids],
                "bbox": actual_bbox,
                "has_stepped_profile": all(_has_stepped_profile(flight) for flight in flights),
            }
            expected_bbox = expected_stair.get("bbox")
            if isinstance(expected_bbox, Mapping):
                if not _axes_match(actual_bbox, expected_bbox, ("x", "y"), tolerance):
                    stair_issue = _issue(
                            "STAIR_FOOTPRINT_MISMATCH",
                            f"/stairs/{stair_id}/bbox",
                            f"Stair {stair_id!r} plan footprint is outside tolerance.",
                            entity_ids=[str(stair_id), *[str(item) for item in flight_ids]],
                            expected={axis: expected_bbox[axis] for axis in ("x", "y")},
                            actual={axis: actual_bbox[axis] for axis in ("x", "y")},
                            source_fact_refs=expected_stair.get("source_fact_refs"),
                        )
                    stair_issue.update(
                        _stair_footprint_diagnostics(
                            actual_bbox=actual_bbox,
                            expected_bbox=expected_bbox,
                            tolerance=tolerance,
                        )
                    )
                    issues.append(stair_issue)
                if not _axes_match(actual_bbox, expected_bbox, ("z",), tolerance):
                    endpoint_diagnostics = _stair_endpoint_diagnostics(
                        actual_z=actual_bbox["z"],
                        expected_z=expected_bbox["z"],
                        tolerance=tolerance,
                    )
                    stair_issue = _issue(
                            "STAIR_RISE_DIRECTION_MISMATCH",
                            f"/stairs/{stair_id}/bbox/z",
                            f"Stair {stair_id!r} does not rise through the confirmed elevations.",
                            entity_ids=[str(stair_id), *[str(item) for item in flight_ids]],
                            expected={"z": expected_bbox["z"]},
                            actual={"z": actual_bbox["z"]},
                            source_fact_refs=expected_stair.get("source_fact_refs"),
                        )
                    stair_issue.update(endpoint_diagnostics)
                    issues.append(stair_issue)
            if expected_stair.get("require_steps") is True and not all(
                _has_stepped_profile(flight) for flight in flights
            ):
                issues.append(
                    _issue(
                        "STAIR_STEP_PROFILE_MISSING",
                        f"/stairs/{stair_id}/flight_profile",
                        f"Stair {stair_id!r} is a ramp-like solid, not a stepped flight.",
                        entity_ids=[str(stair_id), *[str(item) for item in flight_ids]],
                        expected={"stepped_profile": True},
                        actual={"stepped_profile": False},
                        source_fact_refs=expected_stair.get("source_fact_refs"),
                    )
                )
    metrics["stairs"] = stair_metrics
    return GeneratedIfcCheckResult(success=not issues, issues=issues, metrics=metrics)


def _stair_endpoint_diagnostics(
    *, actual_z: list[float], expected_z: list[float], tolerance: float
) -> dict[str, Any]:
    lower_delta = float(expected_z[0]) - float(actual_z[0])
    upper_delta = float(expected_z[1]) - float(actual_z[1])
    translation_only_valid = abs(lower_delta - upper_delta) <= tolerance
    diagnostics = {
        "endpoint_deltas": {"lower": lower_delta, "upper": upper_delta},
        "translation_only_valid": translation_only_valid,
        "recommended_action": (
            "translate_stair"
            if translation_only_valid
            else "reshape_flight_profile_preserve_endpoints"
        ),
    }
    if not translation_only_valid:
        diagnostics["correction_constraints"] = {
            "lower_endpoint": (
                "Create a non-zero-width horizontal tread edge at the expected "
                "lower world elevation."
            ),
            "upper_endpoint": "Preserve the expected upper world elevation.",
            "forbidden": (
                "Do not fix only parent or flight translation when endpoint deltas differ."
            ),
        }
    return diagnostics


def _stair_footprint_diagnostics(
    *,
    actual_bbox: Mapping[str, list[float]],
    expected_bbox: Mapping[str, list[float]],
    tolerance: float,
) -> dict[str, Any]:
    actual_x_span = float(actual_bbox["x"][1]) - float(actual_bbox["x"][0])
    actual_y_span = float(actual_bbox["y"][1]) - float(actual_bbox["y"][0])
    expected_x_span = float(expected_bbox["x"][1]) - float(expected_bbox["x"][0])
    expected_y_span = float(expected_bbox["y"][1]) - float(expected_bbox["y"][0])
    axes_swapped = (
        abs(actual_x_span - expected_y_span) <= tolerance
        and abs(actual_y_span - expected_x_span) <= tolerance
    )
    if not axes_swapped:
        return {"plan_axes_swapped": False}
    return {
        "plan_axes_swapped": True,
        "recommended_action": "rotate_parent_stair_placement",
        "correction_constraints": {
            "change": "Adjust IfcStair ObjectPlacement.ref_direction in plan.",
            "preserve": (
                "Preserve the stepped flight profile and its horizontal width "
                "extrusion direction."
            ),
            "verify": "Recompile and compare the world-space X/Y footprint.",
        },
    }


def _check_component_bboxes(
    *,
    products_by_id: Mapping[str, Any],
    expected_components: Any,
    tolerance: float,
    missing_code: str,
    mismatch_code: str,
    path_prefix: str,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if not isinstance(expected_components, Mapping):
        return metrics
    for component_id, expected_component in expected_components.items():
        if not isinstance(expected_component, Mapping):
            continue
        product = products_by_id.get(str(component_id))
        if product is None:
            issues.append(
                _issue(
                    missing_code,
                    f"/{path_prefix}/{component_id}",
                    f"Expected component {component_id!r} was not found in the IFC.",
                    entity_ids=[str(component_id)],
                    source_fact_refs=expected_component.get("source_fact_refs"),
                )
            )
            continue
        actual_bbox = _bbox_for_product(product)
        metrics[str(component_id)] = {"ifc_class": product.is_a(), "bbox": actual_bbox}
        expected_bbox = expected_component.get("bbox")
        if isinstance(expected_bbox, Mapping) and not _bbox_matches(
            actual_bbox, expected_bbox, tolerance
        ):
            issues.append(
                _issue(
                    mismatch_code,
                    f"/{path_prefix}/{component_id}/bbox",
                    f"Component {component_id!r} world bounding box is outside tolerance.",
                    entity_ids=[str(component_id)],
                    expected=expected_bbox,
                    actual=actual_bbox,
                    source_fact_refs=expected_component.get("source_fact_refs"),
                )
            )
    return metrics


def _combined_bbox(boxes: list[Mapping[str, list[float]]]) -> dict[str, list[float]]:
    return {
        axis: [
            min(box[axis][0] for box in boxes),
            max(box[axis][1] for box in boxes),
        ]
        for axis in AXES
    }


def _axes_match(
    actual: Mapping[str, list[float]],
    expected: Mapping[str, list[float]],
    axes: tuple[str, ...],
    tolerance: float,
) -> bool:
    return all(
        abs(actual[axis][index] - expected[axis][index]) <= tolerance
        for axis in axes
        for index in (0, 1)
    )


def _has_stepped_profile(product: Any) -> bool:
    representation = getattr(product, "Representation", None)
    for shape in getattr(representation, "Representations", ()) or ():
        for item in getattr(shape, "Items", ()) or ():
            profile = getattr(item, "SweptArea", None)
            curve = getattr(profile, "OuterCurve", None)
            points = getattr(curve, "Points", ()) or ()
            coordinates = [tuple(point.Coordinates) for point in points]
            if len(coordinates) >= 7:
                unique_x = {round(float(point[0]), 6) for point in coordinates}
                unique_y = {round(float(point[1]), 6) for point in coordinates}
                if len(unique_x) >= 3 and len(unique_y) >= 3:
                    return True
    return False


def _check_slabs(
    *,
    products_by_id: Mapping[str, Any],
    tolerance: float,
    expectation: Mapping[str, Any],
    wall_result: GeneratedIfcCheckResult,
) -> GeneratedIfcCheckResult:
    issues = list(wall_result.issues)
    metrics = dict(wall_result.metrics)
    slab_metrics: dict[str, Any] = {}
    slabs = expectation.get("slabs", {})
    if not isinstance(slabs, Mapping):
        metrics["slabs"] = slab_metrics
        return GeneratedIfcCheckResult(success=not issues, issues=issues, metrics=metrics)

    for slab_id, expected_slab in slabs.items():
        if not isinstance(expected_slab, Mapping):
            continue
        slab = products_by_id.get(str(slab_id))
        if slab is None:
            issues.append(
                _issue(
                    "MISSING_SLAB",
                    f"/slabs/{slab_id}",
                    f"Expected slab {slab_id!r} was not found in the IFC.",
                    entity_ids=[str(slab_id)],
                    source_fact_refs=expected_slab.get("source_fact_refs"),
                )
            )
            continue
        actual_bbox = _bbox_for_product(slab)
        slab_metrics[str(slab_id)] = {"ifc_class": slab.is_a(), "bbox": actual_bbox}
        expected_bbox = expected_slab.get("bbox")
        if isinstance(expected_bbox, Mapping) and not _bbox_matches(
            actual_bbox, expected_bbox, tolerance
        ):
            issues.append(
                _issue(
                    "SLAB_BBOX_MISMATCH",
                    f"/slabs/{slab_id}/bbox",
                    f"Slab {slab_id!r} world bounding box is outside tolerance.",
                    entity_ids=[str(slab_id)],
                    expected=expected_bbox,
                    actual=actual_bbox,
                    source_fact_refs=expected_slab.get("source_fact_refs"),
                )
            )
        required_walls = expected_slab.get("must_touch_walls", [])
        if not isinstance(required_walls, list):
            continue
        for wall_id in required_walls:
            wall = products_by_id.get(str(wall_id))
            if wall is None:
                continue
            wall_bbox = _bbox_for_product(wall)
            gap = actual_bbox["z"][0] - wall_bbox["z"][1]
            if abs(gap) > tolerance:
                issues.append(
                    _issue(
                        "VERTICAL_SLAB_WALL_GAP",
                        f"/slabs/{slab_id}/must_touch_walls/{wall_id}",
                        (
                            f"Slab {slab_id!r} bottom is {gap:.6f} m from wall "
                            f"{wall_id!r} top."
                        ),
                        entity_ids=[str(wall_id), str(slab_id)],
                        expected={"gap_m": 0.0},
                        actual={"gap_m": round(gap, 6)},
                        source_fact_refs=expected_slab.get("source_fact_refs"),
                    )
                )
    metrics["slabs"] = slab_metrics
    return GeneratedIfcCheckResult(success=not issues, issues=issues, metrics=metrics)


def _check_wall_set(
    *,
    products_by_id: Mapping[str, Any],
    tolerance: float,
    case_id: Any,
    convention: str,
    walls: Mapping[str, Any],
) -> GeneratedIfcCheckResult:
    issues: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {
        "case_id": case_id,
        "wall_set_convention": convention,
        "walls": {},
    }

    wall_had_geometry_issue = False
    for wall_id, expected_wall in walls.items():
        wall = products_by_id.get(wall_id)
        if wall is None:
            wall_had_geometry_issue = True
            issues.append(
                _issue(
                    "MISSING_WALL",
                    f"/walls/{wall_id}",
                    f"Expected wall {wall_id!r} was not found in the IFC.",
                    entity_ids=[wall_id],
                    source_fact_refs=expected_wall.get("source_fact_refs"),
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
                    entity_ids=[wall_id],
                    expected={"axis": expected_axis},
                    actual={"axis": actual_axis},
                    source_fact_refs=expected_wall.get("source_fact_refs"),
                )
            )

        expected_bbox = expected_wall.get("bbox")
        if expected_bbox and not _bbox_matches(actual_bbox, expected_bbox, tolerance):
            wall_had_geometry_issue = True
            bbox_issue_code = str(expected_wall.get("bbox_issue_code", "WALL_BBOX_MISMATCH"))
            bbox_issue_path = str(
                expected_wall.get("bbox_issue_path", f"/walls/{wall_id}/bbox")
            )
            issues.append(
                _issue(
                    bbox_issue_code,
                    bbox_issue_path,
                    f"Wall {wall_id!r} world bounding box is outside tolerance.",
                    entity_ids=[wall_id],
                    expected=expected_bbox,
                    actual=actual_bbox,
                    source_fact_refs=expected_wall.get("source_fact_refs"),
                )
            )

    if wall_had_geometry_issue and walls:
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


def _wall_expectation_sets(
    expectation: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    primary_walls = expectation.get("walls", {})
    sets: list[tuple[str, Mapping[str, Any]]] = []
    if isinstance(primary_walls, Mapping):
        sets.append(("primary", primary_walls))
    accepted_sets = expectation.get("accepted_wall_sets", [])
    if isinstance(accepted_sets, list):
        for item in accepted_sets:
            if not isinstance(item, Mapping):
                continue
            walls = item.get("walls")
            if not isinstance(walls, Mapping):
                continue
            convention = str(item.get("convention", "accepted"))
            if walls is primary_walls:
                sets[0] = (convention, primary_walls)
            else:
                sets.append((convention, walls))
    return sets


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


def _issue(
    code: str,
    path: str,
    message: str,
    *,
    entity_ids: list[str] | None = None,
    expected: Any | None = None,
    actual: Any | None = None,
    source_fact_refs: Any = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "path": path, "message": message}
    if entity_ids is not None:
        payload["entity_ids"] = entity_ids
    if expected is not None:
        payload["expected"] = expected
    if actual is not None:
        payload["actual"] = actual
    if isinstance(source_fact_refs, list):
        payload["source_fact_refs"] = source_fact_refs
    return payload
