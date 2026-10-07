"""Verify public identities and deterministically derive host-relative positions."""
from __future__ import annotations

from copy import deepcopy
import math

from .scene_context import PublicScene, SceneError, ORDER_AXES, class_matches


class GroundingError(ValueError):
    pass


def bind_spatial_intent(body: dict, bindings: list[dict], scene: PublicScene) -> tuple[dict, list[dict]]:
    document = deepcopy(body)
    by_operation = {b["operation_id"]: b for b in bindings}
    if len(by_operation) != len(bindings) or set(by_operation) != {o["operation_id"] for o in document["operations"]}:
        raise GroundingError("SCENE_OPERATION_BINDING_MISMATCH")
    evidence = []
    for op in document["operations"]:
        b = by_operation[op["operation_id"]]
        target = _offered(scene, b["target_id"])
        query = op["target_query"]
        if not any(class_matches(target["ifc_class"], c) for c in query["allowed_ifc_classes"]):
            raise GroundingError("SCENE_TARGET_CLASS_MISMATCH")
        if query.get("global_id") not in (None, target["id"]):
            raise GroundingError("SCENE_TARGET_ID_MISMATCH")
        # Natural-language labels have already been interpreted against the public
        # scene. Do not reapply them as exact Name/storey strings in the resolver.
        op["target_query"] = {k: v for k, v in query.items()
                              if k in {"schema_version", "allowed_ifc_classes", "max_candidates", "winner_margin"}}
        op["target_query"]["global_id"] = target["id"]
        item = {"operation_id": op["operation_id"], "target_id": target["id"],
                "source_role": "current_public_ifc", "derivation": "offered_identity"}
        if b.get("reference_id"):
            reference = _offered(scene, b["reference_id"])
            item["reference_occurrence_id"] = reference["id"]
            if b.get("reference_point_world_mm"):
                _validate_locator(reference, b["reference_point_world_mm"], scene)
            prototype = op.get("prototype_intent")
            if prototype and (prototype["reference_kind"] != "global_id" or
                              prototype["reference"] != reference.get("type_id")):
                raise GroundingError("SCENE_REFERENCE_TYPE_MISMATCH")
        if "target_point_world_mm" in b:
            _validate_locator(target, b["target_point_world_mm"], scene)
            item["target_point_world_mm"] = b["target_point_world_mm"]
        if b.get("position"):
            position = b["position"]
            if position["kind"] == "between_ranked":
                point, refs = _ranked_midpoint(target, position, scene)
                item.update(derivation="midpoint_of_public_occurrences", reference_ids=refs)
            elif position["kind"] == "world_point":
                point = position["point_world_mm"]
                item["derivation"] = "world_point_projected_to_public_wall_axis"
            else:
                raise GroundingError("SCENE_POSITION_UNSUPPORTED")
            offset = _wall_offset(target, point)
            params = op["parameters"].setdefault("position", {})
            # A numeric model guess is not authority for derived coordinates.
            if "center_offset_mm" in params and abs(params["center_offset_mm"]-offset) > 1:
                raise GroundingError("SCENE_POSITION_CONTRADICTS_MODEL_VALUE")
            params.update(reference="wall_local_start", center_offset_mm=offset)
            width = op["parameters"].get("opening", {}).get("width_mm", 0)
            length = target["wall_axis"]["length_mm"]
            if offset-width/2 < -1e-5 or offset+width/2 > length+1e-5:
                raise GroundingError("SCENE_OPENING_OUTSIDE_WALL")
            item.update(point_world_mm=point, center_offset_mm=offset)
        # Every identity reference must have been offered, including occurrence
        # reuse and the type identity attached to an offered occurrence.
        _verify_identity_references(op, scene)
        evidence.append(item)
    return document, evidence


def _offered(scene: PublicScene, identity: str) -> dict:
    try:
        return scene.offered_record(identity)
    except SceneError as e:
        raise GroundingError(str(e)) from e


def _ranked_midpoint(target: dict, position: dict, scene: PublicScene) -> tuple[list[float], list[str]]:
    q = {"ifc_classes": [position["ifc_class"]], "host_id": target["id"],
         "order_by": position["order_by"], "descending": position["descending"]}
    records = scene.complete_records(q)
    if records is None:
        raise GroundingError("SCENE_ORDER_INCOMPLETE")
    ranks = position["ranks"]
    if len(ranks) != 2 or any(type(r) is not int or r < 1 or r > len(records) for r in ranks) or ranks[1] != ranks[0]+1:
        raise GroundingError("SCENE_RANK_INVALID")
    axis = ORDER_AXES.get(position["order_by"])
    if axis is None:
        raise GroundingError("SCENE_ORDINAL_GEOMETRY_REQUIRED")
    coordinates = [r["center_world_mm"][axis] for r in records]
    if any(abs(a-b) < 1e-3 for a, b in zip(coordinates, coordinates[1:])):
        raise GroundingError("SCENE_ORDER_AMBIGUOUS")
    refs = [records[i-1] for i in ranks]
    if [r["id"] for r in refs] != position["reference_ids"]:
        raise GroundingError("SCENE_RANK_MISMATCH")
    for r in refs:
        _offered(scene, r["id"])
    return [(refs[0]["center_world_mm"][i]+refs[1]["center_world_mm"][i])/2 for i in range(3)], [r["id"] for r in refs]


def _wall_offset(wall: dict, point: list[float]) -> float:
    axis = wall.get("wall_axis")
    if not axis or len(point) != 3 or not all(type(p) in (float, int) and math.isfinite(p) for p in point):
        raise GroundingError("SCENE_WALL_AXIS_UNAVAILABLE")
    direction = axis["direction_world"]
    if abs(direction[2]) > 1e-6:
        raise GroundingError("SCENE_WALL_AXIS_UNSUPPORTED")
    delta = [point[i]-axis["start_world_mm"][i] for i in range(3)]
    offset = sum(delta[i]*direction[i] for i in range(3))
    normal_distance = abs(-delta[0]*direction[1]+delta[1]*direction[0])
    if normal_distance > axis["thickness_mm"]/2+10 or not -1e-5 <= offset <= axis["length_mm"]+1e-5:
        raise GroundingError("SCENE_POINT_OUTSIDE_HOST")
    return round(offset, 5)


def _validate_locator(target: dict, point: list[float], scene: PublicScene) -> None:
    if len(point) != 3 or not all(type(v) in (int, float) and math.isfinite(v) for v in point):
        raise GroundingError("SCENE_LOCATOR_INVALID")
    if not target.get("bounds_world_mm"):
        raise GroundingError("SCENE_GEOMETRY_UNAVAILABLE")
    if any(not target["bounds_world_mm"][a][0]-10 <= point[i] <= target["bounds_world_mm"][a][1]+10 for i,a in enumerate("xyz")):
        raise GroundingError("SCENE_LOCATOR_MISMATCH")
    matches = [r for r in scene.records if r["ifc_class"] == target["ifc_class"] and r.get("bounds_world_mm")
               and all(r["bounds_world_mm"][a][0]-10 <= point[i] <= r["bounds_world_mm"][a][1]+10 for i,a in enumerate("xyz"))]
    if len(matches) != 1:
        raise GroundingError("SCENE_LOCATOR_AMBIGUOUS")
    if any(r["ifc_class"] == target["ifc_class"] and not r.get("bounds_world_mm") for r in scene.records):
        raise GroundingError("SCENE_LOCATOR_GEOMETRY_INCOMPLETE")


def _verify_identity_references(value: object, scene: PublicScene) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "global_id" and isinstance(item, str):
                _offered(scene, item)
            if key == "reference" and value.get("reference_kind") == "global_id":
                known_types = {r.get("type_id") for r in scene.records if r["id"] in scene.offered_ids}
                if item not in scene.offered_ids and item not in known_types:
                    raise GroundingError("SCENE_REFERENCE_NOT_OFFERED")
            _verify_identity_references(item, scene)
    elif isinstance(value, list):
        for item in value:
            _verify_identity_references(item, scene)
