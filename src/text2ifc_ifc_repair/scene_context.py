"""Bounded, read-only scene facts extracted exclusively from the caller's IFC.

Coordinates are SI millimetres in the IFC world frame (not map coordinates).
Names are labels, not instructions. Paging/geometry gaps are explicit so a
partial list cannot become authority for an ordinal or a unique spatial match.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .geometry import opening_position_in_wall_mm, straight_wall_axis, wall_dimensions_mm
from .index_store import SQLiteIndexRepository


SCENE_VERSION = "text2ifc/ifc-public-scene/0.1"
MAX_PAGE_RECORDS = 80
MAX_SCENE_RECORDS = 20000
QUERY_KEYS = {"ifc_classes", "ids", "storey_id", "host_id", "world_bounds_mm",
              "order_by", "descending", "offset", "limit"}
ORDER_AXES = {"world_x": 0, "world_y": 1, "world_z": 2}


class SceneError(ValueError):
    """A scene access/geometry limitation, never a missing user fact."""


def class_matches(actual: str, allowed: str) -> bool:
    return actual == allowed or (allowed == "IfcWall" and actual == "IfcWallStandardCase")


class PublicScene:
    def __init__(self, records: list[dict], storeys: list[dict], *, project_unit_scale: float):
        if len(records) > MAX_SCENE_RECORDS:
            raise SceneError("SCENE_RECORD_BUDGET_EXCEEDED")
        self.records = deepcopy(records)
        self.storeys = deepcopy(storeys)
        self.project_unit_scale = project_unit_scale
        self._by_id = {r["id"]: r for r in self.records}
        if len(self._by_id) != len(self.records):
            raise SceneError("SCENE_IDENTITY_AMBIGUOUS")
        self.pages: list[dict] = []
        self.offered_ids: set[str] = set()

    @classmethod
    def from_ifc(cls, source_path: Path | str, index_path: Path | str,
                 *, source_sha256: str) -> "PublicScene":
        """Use the verified public index and its one source; no directory search."""
        model = ifcopenshell.open(str(source_path))
        scale = ifcopenshell.util.unit.calculate_unit_scale(model)
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        with SQLiteIndexRepository.open(index_path, expected_source_ifc_sha256=source_sha256) as repository:
            indexed = list(repository.iter_records())
            types = {r.ifc_global_id: r for r in repository.iter_type_records() if r.identity_reliable}
        if len(indexed) > MAX_SCENE_RECORDS:
            raise SceneError("SCENE_RECORD_BUDGET_EXCEEDED")
        records = []
        for record in indexed:
            if not record.identity_reliable or not record.ifc_global_id:
                continue
            product = model.by_guid(record.ifc_global_id)
            if not product.is_a("IfcElement") and not product.is_a("IfcSpace"):
                continue
            host = _host(product)
            fact = {"id": product.GlobalId, "ifc_class": product.is_a(), "name": record.name,
                    "storey_id": record.storey_global_id, "storey_name": record.storey_name,
                    "host_id": getattr(host, "GlobalId", None), "type_id": record.type_global_id,
                    "geometry_status": "unavailable", "bounds_world_mm": None, "center_world_mm": None,
                    "relationships": [{"kind": r.kind, "id": r.target_global_id} for r in record.relationships]}
            geometry_product = _opening(product) or product
            type_record = types.get(record.type_global_id)
            if type_record:
                fact["type_summary"] = {"id": type_record.ifc_global_id, "ifc_class": type_record.ifc_class,
                                        "name": type_record.name, "formal_attributes": type_record.formal_attributes,
                                        "representation": type_record.representation_summary}
            try:
                # Keep the owning shape alive while reading the native geometry;
                # accessing .geometry on a temporary can yield an empty buffer.
                shape = ifcopenshell.geom.create_shape(settings, geometry_product)
                vertices = shape.geometry.verts
                if not vertices:
                    raise ValueError("empty")
                bounds = {axis: [round(min(vertices[i::3])*1000, 5), round(max(vertices[i::3])*1000, 5)]
                          for i, axis in enumerate("xyz")}
                fact.update(geometry_status="available", bounds_world_mm=bounds,
                            center_world_mm=[sum(bounds[a])/2 for a in "xyz"])
            except (RuntimeError, ValueError):
                pass
            if product.is_a("IfcWall"):
                try:
                    start, end = straight_wall_axis(product)
                    matrix = ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)
                    a = matrix @ [*start, 1.0]
                    b = matrix @ [*end, 1.0]
                    length = math.dist(a[:3], b[:3])
                    dims = wall_dimensions_mm(product)
                    fact["wall_axis"] = {"start_world_mm": [float(v)*scale*1000 for v in a[:3]],
                                         "direction_world": [float(b[i]-a[i])/length for i in range(3)],
                                         "length_mm": dims["length"], "thickness_mm": dims["thickness"]}
                except (RuntimeError, ValueError, AttributeError):
                    fact["wall_axis"] = None
            if product.is_a("IfcOpeningElement"):
                fact["filling_ids"] = [r.RelatedBuildingElement.GlobalId for r in product.HasFillings]
                if host is not None and host.is_a("IfcWall"):
                    try:
                        fact["opening_position"] = opening_position_in_wall_mm(product, host)
                    except (RuntimeError, ValueError, AttributeError):
                        fact["opening_position"] = None
            records.append(fact)
        storeys = []
        for storey in model.by_type("IfcBuildingStorey"):
            matrix = ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement)
            storeys.append({"id": storey.GlobalId, "name": storey.Name,
                            "elevation_mm": float(matrix[2, 3])*scale*1000})
        storeys.sort(key=lambda r: (r["elevation_mm"], r["id"]))
        return cls(records, storeys, project_unit_scale=scale)

    def overview(self) -> dict:
        bounds = [r["bounds_world_mm"] for r in self.records if r.get("bounds_world_mm")]
        return {"schema_version": SCENE_VERSION, "source_role": "current_public_ifc",
                "coordinates": {"frame": "IFC world XYZ; X east, Y north, Z up unless user states otherwise",
                                "length_unit": "mm", "native_length_unit_in_metres": self.project_unit_scale},
                "storeys": deepcopy(self.storeys), "counts": dict(Counter(r["ifc_class"] for r in self.records)),
                "bounds_world_mm": {a: [min(b[a][0] for b in bounds), max(b[a][1] for b in bounds)] for a in "xyz"} if bounds else None,
                "geometry_unknown_count": sum(r["geometry_status"] != "available" for r in self.records),
                "query_limit": MAX_PAGE_RECORDS}

    def query(self, query: Mapping[str, Any]) -> dict:
        q = _validate_query(query)
        matches, unknown = [], []
        for r in self.records:
            if q.get("ids") is not None and r["id"] not in q["ids"]:
                continue
            if q.get("ifc_classes") and not any(class_matches(r["ifc_class"], c) for c in q["ifc_classes"]):
                continue
            if any(q.get(k) is not None and r.get(k) != q[k] for k in ("storey_id", "host_id")):
                continue
            region = q.get("world_bounds_mm")
            if region:
                if not r.get("bounds_world_mm"):
                    unknown.append(r["id"])
                    continue
                # Regions intersect geometry bounds; they are not centroid selectors.
                if any(r["bounds_world_mm"][a][1] < limits[0] or r["bounds_world_mm"][a][0] > limits[1]
                       for a, limits in region.items()):
                    continue
            matches.append(r)
        order = q["order_by"]
        axis = ORDER_AXES.get(order)
        if axis is not None:
            sortable = [r for r in matches if r.get("center_world_mm")]
            unknown.extend(r["id"] for r in matches if not r.get("center_world_mm"))
            matches = sortable
        matches.sort(key=lambda r: (r["center_world_mm"][axis], r["id"]) if axis is not None else (r["id"],),
                     reverse=q["descending"])
        offset, limit = q["offset"], q["limit"]
        page = matches[offset:offset+limit]
        total = len(matches)
        result = {"schema_version": SCENE_VERSION, "query": q, "records": deepcopy(page),
                  "total_matches": total, "omitted_count": total-len(page),
                  "complete": offset == 0 and len(page) == total,
                  "geometry_complete": not unknown, "geometry_unknown_ids": sorted(set(unknown)),
                  "next_offset": offset+len(page) if offset+len(page) < total else None}
        self.offered_ids.update(r["id"] for r in page)
        self.pages.append(deepcopy(result))
        return result

    def offered_record(self, identity: str) -> dict:
        if identity not in self.offered_ids:
            raise SceneError("SCENE_ID_NOT_OFFERED")
        return deepcopy(self._by_id[identity])

    def complete_records(self, query: Mapping[str, Any]) -> list[dict] | None:
        signature = _signature(_validate_query(query))
        pages = [p for p in self.pages if _signature(p["query"]) == signature]
        if not pages or any(not p["geometry_complete"] for p in pages):
            return None
        records = {r["id"]: r for p in pages for r in p["records"]}
        if len(records) != pages[0]["total_matches"]:
            return None
        q = pages[0]["query"]
        axis = ORDER_AXES.get(q["order_by"])
        return sorted(deepcopy(list(records.values())),
                      key=lambda r: (r["center_world_mm"][axis], r["id"]) if axis is not None else (r["id"],),
                      reverse=q["descending"])


def _signature(query: Mapping) -> dict:
    return {k: v for k, v in query.items() if k not in {"offset", "limit"}}


def _validate_query(query: Mapping) -> dict:
    if not isinstance(query, Mapping) or set(query)-QUERY_KEYS:
        raise SceneError("SCENE_QUERY_INVALID")
    q = {"order_by": "id", "descending": False, "offset": 0, "limit": 40, **deepcopy(dict(query))}
    if type(q["limit"]) is not int or not 1 <= q["limit"] <= MAX_PAGE_RECORDS:
        raise SceneError("SCENE_QUERY_LIMIT_INVALID")
    if type(q["offset"]) is not int or q["offset"] < 0:
        raise SceneError("SCENE_QUERY_OFFSET_INVALID")
    if q["order_by"] not in {"id", *ORDER_AXES} or type(q["descending"]) is not bool:
        raise SceneError("SCENE_QUERY_ORDER_INVALID")
    for key in ("ifc_classes", "ids"):
        if key in q and (not isinstance(q[key], list) or not 1 <= len(q[key]) <= MAX_PAGE_RECORDS
                         or not all(isinstance(v, str) and 0 < len(v) <= 128 for v in q[key])):
            raise SceneError("SCENE_QUERY_FILTER_INVALID")
    for key in ("host_id", "storey_id"):
        if key in q and (not isinstance(q[key], str) or not 0 < len(q[key]) <= 128):
            raise SceneError("SCENE_QUERY_FILTER_INVALID")
    if "world_bounds_mm" in q:
        region = q["world_bounds_mm"]
        if not isinstance(region, dict) or not region or set(region)-set("xyz"):
            raise SceneError("SCENE_QUERY_BOUNDS_INVALID")
        for pair in region.values():
            if not isinstance(pair, list) or len(pair) != 2 or not all(type(v) in (int, float) and math.isfinite(v) for v in pair) or pair[0] > pair[1]:
                raise SceneError("SCENE_QUERY_BOUNDS_INVALID")
    return q


def _opening(product: Any) -> Any | None:
    fillings = getattr(product, "FillsVoids", ())
    return fillings[0].RelatingOpeningElement if len(fillings) == 1 else None


def _host(product: Any) -> Any | None:
    opening = _opening(product) or product
    relations = getattr(opening, "VoidsElements", ())
    return relations[0].RelatingBuildingElement if len(relations) == 1 else None
