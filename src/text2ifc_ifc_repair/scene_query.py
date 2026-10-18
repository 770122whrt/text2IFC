"""Pure, bounded constraint evaluation over public IFC records.

The caller owns basic filters, source extraction, pagination and offered-ID
coverage. Anchors contain only records already offered by that caller. This
module reads no files, resolves no identities and interprets no natural language.
Three-valued predicates preserve relevant gaps instead of proving absence.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from typing import Any
import unicodedata

from jsonschema import Draft202012Validator


EXTENSION_KEYS = frozenset({"names", "type_names", "predicates", "select"})
_BASE_KEYS = {"ifc_classes", "ids", "storey_id", "host_id", "world_bounds_mm",
              "order_by", "descending", "offset", "limit", "detail"}
_AXES = {"world_x": 0, "world_y": 1, "world_z": 2}
_TIE_TOLERANCE_MM = 1e-3
_MAX_NUMBER = 1e12


class SceneQueryError(ValueError):
    """An invalid query or insufficient public evidence; no private fallback."""

    def __init__(self, message: str, *, path: str | None = None):
        super().__init__(message)
        if path is not None:
            self.path = path


def query_properties() -> dict[str, Any]:
    """Fresh JSON Schema properties; runtime additionally checks finite ranges."""
    number = {"type": "number", "minimum": -_MAX_NUMBER, "maximum": _MAX_NUMBER}
    nonnegative = {**number, "minimum": 0}
    pair = {"type": "array", "items": number, "minItems": 2, "maxItems": 2}
    distance = {**pair, "items": nonnegative}
    point = {"type": "array", "items": number, "minItems": 3, "maxItems": 3}
    identity = {"type": "string", "minLength": 1, "maxLength": 128, "pattern": r"\S"}
    role = {"enum": ["placement_origin", "center"]}

    def variant(kind: str, properties: dict, required: list[str], **extra: Any) -> dict:
        return {"type": "object", "additionalProperties": False,
                "properties": {"kind": {"const": kind}, **properties},
                "required": ["kind", *required], **extra}

    predicates = [
        variant("point", {"point_mm": point, "role": {"enum": ["placement_origin", "center", "contains"]},
                          "tolerance_mm": nonnegative}, ["point_mm", "role", "tolerance_mm"]),
        variant("relative", {"reference_id": identity, "point_role": role, "distance_mm": distance,
                             "delta_mm": {"type": "object", "additionalProperties": False,
                                          "minProperties": 1, "properties": {a: pair for a in "xyz"}}},
                ["reference_id", "point_role"], anyOf=[{"required": ["delta_mm"]}, {"required": ["distance_mm"]}]),
        variant("host_local", {"host_id": identity, "point_role": role,
                               **{a: pair for a in ("along_mm", "normal_mm", "height_mm")}},
                ["host_id", "point_role"], anyOf=[{"required": [a]} for a in ("along_mm", "normal_mm", "height_mm")]),
        variant("relation", {"reference_id": identity, "relation": {"enum": ["host", "fills", "voids", "space_boundary"]}},
                ["reference_id", "relation"]),
        variant("empty_opening", {"value": {"type": "boolean"}}, ["value"]),
    ]
    select = {"type": "object", "additionalProperties": False,
              "properties": {"ranks": {"type": "array", "minItems": 1, "maxItems": 80, "uniqueItems": True,
                                       "items": {"type": "integer", "minimum": 1, "maximum": 20000}},
                             "order_by": {"enum": [*_AXES, "host_axis", "distance"]},
                             "descending": {"type": "boolean"}, "host_id": identity,
                             "reference_id": identity, "point_mm": point, "point_role": role},
              "required": ["ranks", "order_by", "descending"],
              "allOf": [
                  {"if": {"properties": {"order_by": {"const": "host_axis"}}},
                   "then": {"required": ["host_id"]}, "else": {"not": {"required": ["host_id"]}}},
                  {"if": {"properties": {"order_by": {"const": "distance"}}},
                   "then": {"required": ["point_role"],
                            "oneOf": [{"required": ["reference_id"], "not": {"required": ["point_mm"]}},
                                      {"required": ["point_mm"], "not": {"required": ["reference_id"]}}]},
                   "else": {"not": {"anyOf": [{"required": [key]} for key in ("reference_id", "point_mm", "point_role")]}}},
              ]}
    labels = {"type": "array", "minItems": 1, "maxItems": 80,
              "items": {"type": "string", "minLength": 1, "maxLength": 256, "pattern": r"\S"}}
    return deepcopy({"names": labels, "type_names": labels,
                     "predicates": {"type": "array", "minItems": 1, "maxItems": 16, "items": {"oneOf": predicates}},
                     "select": select})


_VALIDATOR = Draft202012Validator({"type": "object", "properties": query_properties(), "additionalProperties": False})


def validate_extensions(query: Mapping[str, Any]) -> None:
    """Validate the extension grammar without reinterpreting legacy filters."""
    if not isinstance(query, Mapping) or set(query) - EXTENSION_KEYS - _BASE_KEYS:
        raise SceneQueryError("SCENE_QUERY_INVALID")
    extensions = {key: value for key, value in query.items() if key in EXTENSION_KEYS}
    if next(_VALIDATOR.iter_errors(extensions), None) is not None:
        raise SceneQueryError("SCENE_QUERY_EXTENSION_INVALID")

    def finite_values(value: Any) -> bool:
        if isinstance(value, Mapping):
            return all(finite_values(v) for v in value.values())
        if isinstance(value, list):
            return all(finite_values(v) for v in value)
        return not isinstance(value, float) or math.isfinite(value)

    if not finite_values(extensions):
        raise SceneQueryError("SCENE_QUERY_NUMBER_INVALID")
    for predicate in query.get("predicates", []):
        ranges = list(predicate.get("delta_mm", {}).values())
        ranges.extend(predicate[key] for key in ("distance_mm", "along_mm", "normal_mm", "height_mm") if key in predicate)
        if any(pair[0] > pair[1] for pair in ranges):
            raise SceneQueryError("SCENE_QUERY_RANGE_INVALID")


def _anchor(anchors: Mapping[str, dict], identity: str) -> dict:
    record = anchors.get(identity)
    if not isinstance(record, Mapping) or record.get("id") != identity:
        raise SceneQueryError("SCENE_ID_NOT_OFFERED")
    return record


def _check_anchors(query: Mapping[str, Any], anchors: Mapping[str, dict]) -> None:
    for predicate in query.get("predicates", []):
        for key in ("reference_id", "host_id"):
            if key in predicate:
                _anchor(anchors, predicate[key])
    for key in ("reference_id", "host_id"):
        if key in query.get("select", {}):
            _anchor(anchors, query["select"][key])


def _label(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _number(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _vector(value: Any, size: int = 3) -> list[float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != size or not all(_number(v) for v in value):
        return None
    return list(value)


def _point(record: Mapping[str, Any], role: str) -> list[float] | None:
    if role == "center":
        return _vector(record.get("center_world_mm"))
    matrix = record.get("placement_world_mm")
    if not isinstance(matrix, (list, tuple)) or len(matrix) != 4 or any(_vector(row, 4) is None for row in matrix):
        return None
    if any(not math.isclose(matrix[3][i], value, abs_tol=1e-8, rel_tol=0) for i, value in enumerate((0, 0, 0, 1))):
        return None
    # Translation is not accepted from an invalid placement matrix.
    if any(not math.isclose(sum(matrix[k][i] * matrix[k][j] for k in range(3)),
                            float(i == j), abs_tol=1e-8, rel_tol=0) for i in range(3) for j in range(3)):
        return None
    determinant = sum(matrix[0][i] * (matrix[1][(i + 1) % 3] * matrix[2][(i + 2) % 3]
                      - matrix[1][(i + 2) % 3] * matrix[2][(i + 1) % 3]) for i in range(3))
    if not math.isclose(determinant, 1, abs_tol=1e-8, rel_tol=0):
        return None
    return [matrix[i][3] for i in range(3)]


def _within(value: float, limits: Sequence[float]) -> bool:
    return limits[0] <= value <= limits[1]


def _all(values: Sequence[bool | None]) -> bool | None:
    if False in values:
        return False
    return None if None in values else True


def _host_coordinates(point: list[float] | None, host: Mapping[str, Any]) -> list[float] | None:
    axis = host.get("wall_axis")
    if point is None or not isinstance(axis, Mapping):
        return None
    start, direction = _vector(axis.get("start_world_mm")), _vector(axis.get("direction_world"))
    if start is None or direction is None or not math.isclose(direction[2], 0, abs_tol=1e-8):
        return None
    length = math.hypot(direction[0], direction[1])
    if not math.isclose(length, 1, abs_tol=1e-8):
        return None
    dx, dy, dz = [point[i] - start[i] for i in range(3)]
    return [dx * direction[0] + dy * direction[1], -dx * direction[1] + dy * direction[0], dz]


def _edges(record: Mapping[str, Any]) -> list[dict] | None:
    edges = record.get("relationships")
    if not isinstance(edges, list) or any(not isinstance(edge, Mapping) or not isinstance(edge.get("kind"), str)
                                          or not isinstance(edge.get("id"), str) or not edge["id"] for edge in edges):
        return None
    return edges


def _relation(record: Mapping[str, Any], predicate: Mapping[str, Any]) -> bool | None:
    edges = _edges(record)
    if edges is None:
        return None
    relation = predicate["relation"]
    kinds = {"host": {"hosted_by_wall"}, "fills": {"fills_opening", "filled_by"},
             "voids": {"voids_opening"}, "space_boundary": {"bounds_space", "bounded_by_wall", "space_boundary"}}[relation]
    if relation == "voids" and record.get("ifc_class") == "IfcOpeningElement":
        kinds = {*kinds, "hosted_by_wall"}
    return any(edge["kind"] in kinds and edge["id"] == predicate["reference_id"] for edge in edges)


def _predicate(record: Mapping[str, Any], predicate: Mapping[str, Any], anchors: Mapping[str, dict]) -> bool | None:
    kind = predicate["kind"]
    if kind == "point":
        target, tolerance = predicate["point_mm"], predicate["tolerance_mm"]
        if predicate["role"] == "contains":
            # This is explicitly AABB containment, not a solid-interior test.
            bounds = record.get("bounds_world_mm")
            if not isinstance(bounds, Mapping):
                return None
            values = []
            for index, axis in enumerate("xyz"):
                limits = _vector(bounds.get(axis), 2)
                values.append(None if limits is None or limits[0] > limits[1] else
                              limits[0] - tolerance <= target[index] <= limits[1] + tolerance)
            return _all(values)
        coordinate = _point(record, predicate["role"])
        return None if coordinate is None else math.dist(coordinate, target) <= tolerance
    if kind == "relative":
        coordinate = _point(record, predicate["point_role"])
        reference = _point(_anchor(anchors, predicate["reference_id"]), predicate["point_role"])
        if coordinate is None or reference is None:
            return None
        delta = [coordinate[i] - reference[i] for i in range(3)]
        return all(_within(delta["xyz".index(axis)], limits) for axis, limits in predicate.get("delta_mm", {}).items()) and (
            "distance_mm" not in predicate or _within(math.dist(coordinate, reference), predicate["distance_mm"]))
    if kind == "host_local":
        host_id = predicate["host_id"]
        same_host = None if "host_id" not in record else record["host_id"] == host_id
        local = _host_coordinates(_point(record, predicate["point_role"]), _anchor(anchors, host_id))
        inside = None if local is None else all(_within(local[index], predicate[key])
            for index, key in enumerate(("along_mm", "normal_mm", "height_mm")) if key in predicate)
        return _all([same_host, inside])
    if kind == "relation":
        return _relation(record, predicate)
    if kind == "empty_opening":
        if record.get("ifc_class") != "IfcOpeningElement":
            return False
        fillings = record.get("filling_ids")
        edges = _edges(record)
        if isinstance(fillings, list) and all(isinstance(v, str) and v for v in fillings):
            # Contradictory explicit lists do not establish an empty opening.
            if edges is not None and set(fillings) != {e["id"] for e in edges if e["kind"] == "filled_by"}:
                return None
            empty = not fillings
        elif edges is not None:
            empty = not any(edge["kind"] == "filled_by" for edge in edges)
        else:
            return None
        return empty is predicate["value"]
    raise SceneQueryError("SCENE_QUERY_PREDICATE_INVALID")


def apply_constraints(records: Sequence[dict], query: Mapping[str, Any], anchors: Mapping[str, dict]) -> tuple[list[dict], list[str]]:
    """Apply AND constraints, retaining only potentially matching unknown IDs.

    Each names/type_names array is an exact normalized-label OR. Predicates are
    ANDed, and any definite false excludes a record regardless of missing facts
    in other predicates. Inputs remain unchanged; no record is discovered here.
    """
    validate_extensions(query)
    _check_anchors(query, anchors)
    labels = {key: {_label(value) for value in query[key]} for key in ("names", "type_names") if key in query}
    matches, unknown = [], []
    for record in records:
        results: list[bool | None] = []
        if "names" in labels:
            names = record.get("labels")
            names = names if isinstance(names, list) else []
            results.append(any(isinstance(name, str) and _label(name) in labels["names"]
                               for name in [record.get("name"), *names]))
        if "type_names" in labels:
            summary = record.get("type_summary")
            if isinstance(summary, Mapping):
                name = summary.get("name")
                results.append(isinstance(name, str) and _label(name) in labels["type_names"])
            else:
                results.append(None if record.get("type_id") else False)
        results.extend(_predicate(record, predicate, anchors) for predicate in query.get("predicates", []))
        result = _all(results)
        if result is True:
            matches.append(record)
        elif result is None:
            unknown.append(record["id"])
    return matches, unknown


def select_records(records: Sequence[dict], query: Mapping[str, Any], anchors: Mapping[str, dict], *,
                   unknown_ids: Sequence[str] = ()) -> tuple[list[dict], dict | None]:
    """Select explicit ordinals from the entire known cohort, never a page.

    A result proves its selected ordinals only. The caller must preserve the
    cohort size and separately describe page/identity coverage. Ties touching
    selected ranks and relevant unknown candidates fail closed; IDs never break
    a spatial tie. Ties solely among unselected ranks do not change the answer.
    """
    validate_extensions(query)
    _check_anchors(query, anchors)
    if "select" not in query:
        return list(records), None
    if unknown_ids:
        raise SceneQueryError("SCENE_SELECTION_INCOMPLETE")
    select = query["select"]
    order = select["order_by"]
    origin = None
    if order == "distance":
        origin = select.get("point_mm") if "point_mm" in select else _point(
            _anchor(anchors, select["reference_id"]), select["point_role"])
        if origin is None:
            raise SceneQueryError("SCENE_SELECTION_INCOMPLETE")
    keyed = []
    for record in records:
        if order == "host_axis":
            if "host_id" not in record:
                raise SceneQueryError("SCENE_SELECTION_INCOMPLETE")
            if record["host_id"] != select["host_id"]:
                raise SceneQueryError("SCENE_SELECTION_SCOPE_INVALID")
            local = _host_coordinates(_point(record, "center"), _anchor(anchors, select["host_id"]))
            key = None if local is None else local[0]
        else:
            coordinate = _point(record, select["point_role"] if order == "distance" else "center")
            key = None if coordinate is None else (math.dist(coordinate, origin) if order == "distance" else coordinate[_AXES[order]])
        if key is None or not _number(key):
            raise SceneQueryError("SCENE_SELECTION_INCOMPLETE")
        keyed.append((key, record))
    keyed.sort(key=lambda pair: pair[0], reverse=select["descending"])
    for index, rank in enumerate(select["ranks"]):
        if rank > len(keyed):
            raise SceneQueryError(
                f"SCENE_SELECTION_RANK_INVALID: The filtered public cohort has {len(keyed)} records; "
                "the requested rank exceeds this count. Verify unresolved filters against the request, "
                "or query without select to inspect the cohort. Do not substitute a different requested rank.",
                path=f"/select/ranks/{index}")
    indices = [int(rank) - 1 for rank in select["ranks"]]
    if any(abs(keyed[index][0] - keyed[neighbor][0]) < _TIE_TOLERANCE_MM
           for index in indices for neighbor in (index - 1, index + 1) if 0 <= neighbor < len(keyed)):
        raise SceneQueryError("SCENE_SELECTION_AMBIGUOUS")
    selected = [keyed[index][1] for index in indices]
    evidence = {"scope": "complete_filtered_set", "total_matches": len(records), **deepcopy(dict(select)),
                "selected_ids": [record["id"] for record in selected]}
    return selected, evidence
