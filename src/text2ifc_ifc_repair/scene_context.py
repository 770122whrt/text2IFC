"""Bounded, read-only scene facts extracted exclusively from the caller's IFC.

Coordinates are SI millimetres in the IFC world frame (not map coordinates).
Names are labels, not instructions. Paging/geometry gaps are explicit so a
partial list cannot become authority for an ordinal or a unique spatial match.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
import math
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from .geometry import opening_position_in_wall_mm, straight_wall_axis, wall_dimensions_mm
from .index_store import SQLiteIndexRepository
from .scene_query import EXTENSION_KEYS, SceneQueryError, apply_constraints, select_records, validate_extensions


SCENE_VERSION = "text2ifc/ifc-public-scene/0.3"
MAX_PAGE_RECORDS = 80
MAX_SCENE_RECORDS = 20000
QUERY_KEYS = {"ifc_classes", "ids", "storey_id", "host_id", "world_bounds_mm",
              "order_by", "descending", "offset", "limit", "detail", *EXTENSION_KEYS}
ORDER_AXES = {"world_x": 0, "world_y": 1, "world_z": 2}
DETAIL_FIELDS = {"body_bounds_local_mm", "opening", "geometry_detail_status"}


class SceneError(ValueError):
    """A scene access/geometry limitation, never a missing user fact."""

    def __init__(self, message: str, *, path: str | None = None):
        super().__init__(message)
        if path is not None:
            self.path = path


def class_matches(actual: str, allowed: str) -> bool:
    return actual == allowed or (allowed == "IfcWall" and actual == "IfcWallStandardCase")


class PublicScene:
    def __init__(self, records: list[dict], storeys: list[dict], *, project_unit_scale: float,
                 true_north_world: list[float] | None = None):
        if len(records) > MAX_SCENE_RECORDS:
            raise SceneError("SCENE_RECORD_BUDGET_EXCEEDED")
        self.records = deepcopy(records)
        self.storeys = deepcopy(storeys)
        for storey in self.storeys:
            storey.setdefault("placement_world_mm", None)
        self.project_unit_scale = project_unit_scale
        self.true_north_world = deepcopy(true_north_world)
        self._by_id = {r["id"]: r for r in self.records}
        if len(self._by_id) != len(self.records):
            raise SceneError("SCENE_IDENTITY_AMBIGUOUS")
        self._storey_ids = {s["id"] for s in self.storeys}
        if len(self._storey_ids) != len(self.storeys) or self._storey_ids & self._by_id.keys():
            raise SceneError("SCENE_IDENTITY_AMBIGUOUS")
        self._by_id.update({s["id"]: {
            "id": s["id"], "ifc_class": "IfcBuildingStorey", "name": s.get("name"),
            "elevation_mm": s.get("elevation_mm"), "geometry_status": "unavailable",
            "bounds_world_mm": None, "center_world_mm": None, "type_id": None,
            "placement_world_mm": s["placement_world_mm"],
        } for s in self.storeys})
        self._geometry_model: Any | None = None
        self._geometry_details: dict[str, dict] = {}
        self._geometry_detail_failures: set[str] = set()
        self._body_bounds_local: dict[int, dict] = {}
        self._metadata_ids = {key: defaultdict(set) for key in ("ifc_class", "storey_id", "host_id")}
        self._record_ids = set()
        self._record_order = {}
        for ordinal, record in enumerate(self.records):
            self._record_ids.add(record["id"])
            self._record_order[record["id"]] = ordinal
            for key, index in self._metadata_ids.items():
                index[record.get(key)].add(record["id"])
        self._indexed_records = self.records
        self._indexed_count = len(self.records)
        self.pages: list[dict] = []
        self._query_results: dict[str, dict] = {}
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
        boundaries = _space_boundaries(model)
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
            fact["labels"] = list(dict.fromkeys(value for key in ("Name", "LongName", "Tag", "Description")
                                               if isinstance(value := getattr(product, key, None), str) and value))
            fact["relationships"].extend(boundaries.get(product.GlobalId, []))
            fact["relationships_status"] = "public_ifc_only_no_geometry_inference"
            try:
                placement = _placement_world_mm(product, scale)
                fact.update(placement_world_mm=placement,
                            placement_origin_world_mm=[placement[i][3] for i in range(3)])
            except (RuntimeError, ValueError, AttributeError, TypeError):
                fact.update(placement_world_mm=None, placement_origin_world_mm=None)
            geometry_product = _opening(product) or product
            fact["bounds_geometry_role"] = "retained_opening" if geometry_product != product else "product"
            fact["bounds_geometry_source_id"] = geometry_product.GlobalId
            type_record = types.get(record.type_global_id)
            if type_record:
                fact["type_name"] = type_record.name
                fact["type_summary"] = {"id": type_record.ifc_global_id, "ifc_class": type_record.ifc_class,
                                        "name": type_record.name, "formal_attributes": type_record.formal_attributes,
                                        "representation": type_record.representation_summary}
            else:
                fact["type_name"] = None
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
                fact["opening_state"] = "filled" if fact["filling_ids"] else "unfilled"
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
                            "elevation_mm": float(matrix[2, 3])*scale*1000,
                            "placement_world_mm": _placement_world_mm(storey, scale)
                                if storey.ObjectPlacement is not None else None})
        storeys.sort(key=lambda r: (r["elevation_mm"], r["id"]))
        scene = cls(records, storeys, project_unit_scale=scale, true_north_world=_true_north_world(model))
        # Keep the caller's one public model for targeted lazy detail reads.
        # No second model scan or tessellation of every Body is needed.
        scene._geometry_model = model
        return scene

    def overview(self) -> dict:
        # The model sees these verified public identities in the initial prompt.
        # Offering them does not offer products or invent storey geometry.
        self.offered_ids.update(self._storey_ids)
        bounds = [r["bounds_world_mm"] for r in self.records if r.get("bounds_world_mm")]
        return {"schema_version": SCENE_VERSION, "source_role": "current_public_ifc",
                "coordinates": {"frame": "IFC world XYZ axes; no geographic east/north assumption",
                                "length_unit": "mm", "native_length_unit_in_metres": self.project_unit_scale,
                                "true_north_world": deepcopy(self.true_north_world),
                                "true_north_status": "available" if self.true_north_world is not None else "unknown"},
                "storeys": deepcopy(self.storeys), "counts": dict(Counter(r["ifc_class"] for r in self.records)),
                "bounds_world_mm": {a: [min(b[a][0] for b in bounds), max(b[a][1] for b in bounds)] for a in "xyz"} if bounds else None,
                "geometry_unknown_count": sum(r["geometry_status"] != "available" for r in self.records),
                "query_limit": MAX_PAGE_RECORDS}

    def query(self, query: Mapping[str, Any]) -> dict:
        q = _validate_query(query)
        matches, unknown = self._matching_records(q)
        try:
            if "select" in q:
                selected, selection = select_records(matches, q, self._anchors(), unknown_ids=unknown)
            else:
                selected, selection = _ordered_records(matches, q), None
        except SceneQueryError as error:
            raise SceneError(str(error), path="/query" + getattr(error, "path", "")) from error
        offset, limit = q["offset"], q["limit"]
        page = selected[offset:offset+limit]
        total = len(matches)
        self.offered_ids.update(r["id"] for r in page)
        public_page = deepcopy(page)
        shared_types = {}
        for record in public_page:
            type_summary = record.pop("type_summary", None)
            if type_summary:
                shared_types[type_summary["id"]] = (type_summary if q["detail"] == "geometry" else {
                    key: type_summary[key] for key in ("id", "ifc_class", "name") if key in type_summary})
            if q["detail"] == "geometry":
                try:
                    record.update(self.geometry_detail(record["id"]), geometry_detail_status="available")
                except SceneError:
                    # A missing Body does not invalidate a separately read public placement.
                    record.update(body_bounds_local_mm=None, geometry_detail_status="unavailable")
            else:
                for key in DETAIL_FIELDS:
                    record.pop(key, None)
        query_id = f"q{len(self._query_results) + 1}"
        result = {"schema_version": SCENE_VERSION, "query_id": query_id, "query": q,
                  "records": public_page, "types": shared_types,
                  "total_matches": total, "omitted_count": total-len(page),
                  "complete": offset == 0 and len(page) == total,
                  "geometry_complete": not unknown, "geometry_unknown_ids": sorted(set(unknown)),
                  "next_offset": offset+len(page) if offset+len(page) < len(selected) else None}
        if selection is not None:
            result["selection"] = selection
            result["selection_complete"] = offset == 0 and len(page) == len(selected)
        self._query_results[query_id] = deepcopy(result)
        self.pages.append(deepcopy(result))
        return result

    def prompt_context(self) -> dict:
        """Deduplicate disclosed evidence without silently truncating identities.

        Pages remain raw audit snapshots. This projection includes only facts
        actually returned, never all indexed scene facts. Geometry already
        disclosed survives a later summary request for the same identity.
        """
        records, types, queries = {}, {}, {}
        for page in self._query_results.values():
            for record in page["records"]:
                records.setdefault(record["id"], {}).update(deepcopy(record))
            for identity, summary in page["types"].items():
                types.setdefault(identity, {}).update(deepcopy(summary))
            summary = {key: deepcopy(value) for key, value in page.items()
                       if key not in {"schema_version", "records", "types", "query_id"}}
            summary["record_ids"] = [record["id"] for record in page["records"]]
            key = json.dumps(summary, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            if key not in queries:
                queries[key] = {"query_id": page["query_id"], "query_ids": [], **summary}
            queries[key]["query_ids"].append(page["query_id"])
        return {"schema_version": SCENE_VERSION, "source_role": "current_public_ifc",
                "records": list(records.values()), "types": types, "queries": list(queries.values())}

    def verify_query_binding(self, query_id: str, identity: str) -> dict:
        """Verify membership and coverage; multiple matches do not imply uniqueness."""
        page = self._query_results.get(query_id)
        if page is None or identity not in self.offered_ids:
            raise SceneError("SCENE_QUERY_BINDING_INVALID: Cite a returned query and an already offered identity.")
        if not page["geometry_complete"]:
            raise SceneError("SCENE_QUERY_BINDING_INCOMPLETE: The cited query has candidates with unavailable geometry; "
                             "its spatial evidence is incomplete. Resolve the relevant public evidence before binding.")
        if not (page["complete"] or page.get("selection_complete")):
            raise SceneError("SCENE_QUERY_BINDING_INCOMPLETE: The cited query does not cover its complete cohort "
                             "or selected ranks. Obtain complete query evidence before binding.")
        if identity not in {r["id"] for r in page["records"]}:
            raise SceneError("SCENE_QUERY_BINDING_INCOMPLETE: The bound identity was not returned by the cited query. "
                             "Cite a returned query containing this already offered identity with complete coverage.")
        q = page["query"]
        records, unknown = self._matching_records(q)
        if unknown:
            raise SceneError("SCENE_QUERY_BINDING_INCOMPLETE: The cited query has candidates with unavailable geometry; "
                             "its spatial evidence is incomplete. Resolve the relevant public evidence before binding.")
        if page.get("selection"):
            try:
                selected, evidence = select_records(records, q, self._anchors(), unknown_ids=unknown)
            except SceneQueryError as error:
                raise SceneError(str(error)) from error
            if evidence != page["selection"] or identity not in {r["id"] for r in selected}:
                raise SceneError("SCENE_QUERY_BINDING_INVALID")
        elif {r["id"] for r in records} != {r["id"] for r in page["records"]}:
            raise SceneError("SCENE_QUERY_BINDING_INVALID")
        return {"query_id": query_id, "identity": identity, "total_matches": page["total_matches"],
                "record_ids": [r["id"] for r in page["records"]],
                "selection": deepcopy(page.get("selection")), "geometry_complete": True}

    def verified_query_records(self, query_id: str, identity: str) -> list[dict]:
        """Internal verification scope; this does not offer additional identities."""
        self.verify_query_binding(query_id, identity)
        records, unknown = self._matching_records(self._query_results[query_id]["query"])
        if unknown:
            raise SceneError("SCENE_QUERY_BINDING_INCOMPLETE")
        return deepcopy(records)

    def verified_selection(self, query: Mapping[str, Any], ranks: list[int],
                           reference_ids: list[str]) -> list[dict] | None:
        """Check a stored rank certificate against the same complete public cohort.

        Only selected identities are offered. This separate authority does not
        weaken complete_records' historical all-identities-offered requirement.
        """
        q = _validate_query(query)
        for page in self._query_results.values():
            selection = page.get("selection")
            if not selection or not page.get("selection_complete") or not page["geometry_complete"]:
                continue
            stored_q = page["query"]
            if (_cohort_signature(q) != _cohort_signature(stored_q)
                    or selection["ranks"] != ranks or selection["selected_ids"] != reference_ids):
                continue
            expected_order = q.get("select", q)
            if (selection["order_by"] != expected_order["order_by"]
                    or selection["descending"] != expected_order.get("descending", False)):
                continue
            if "select" in q and any(selection.get(key) != value for key, value in q["select"].items()
                                     if key != "ranks"):
                continue
            if any(identity not in self.offered_ids for identity in reference_ids):
                return None
            try:
                records, unknown = self._matching_records(stored_q)
                selected, evidence = select_records(records, stored_q, self._anchors(), unknown_ids=unknown)
            except (SceneQueryError, SceneError):
                return None
            if evidence == selection and [r["id"] for r in selected] == reference_ids:
                return deepcopy(selected)
        return None

    def _anchors(self) -> dict[str, dict]:
        return {identity: self._by_id[identity] for identity in self.offered_ids}

    def geometry_detail(self, identity: str) -> dict:
        """Return actual public placement and Body facts for an offered identity.

        Matrix translation and Body bounds use millimetres; the rotation block
        is dimensionless. Window/Door Opening facts describe the retained
        Opening in the occurrence's own frame. Referenced IDs do not become
        offered through this read. Missing facts are never inferred from an
        overview elevation or a world bounding box.
        """
        record = self.offered_record(identity)
        if identity in self._geometry_detail_failures:
            raise SceneError("SCENE_GEOMETRY_DETAIL_UNAVAILABLE")
        if identity not in self._geometry_details:
            try:
                if record["ifc_class"] == "IfcBuildingStorey":
                    detail = {"placement_world_mm": record.get("placement_world_mm"),
                              "body_bounds_local_mm": None}
                elif self._geometry_model is None:
                    detail = {key: record.get(key) for key in ("placement_world_mm", "body_bounds_local_mm")}
                    if record["ifc_class"] in {"IfcWindow", "IfcDoor"}:
                        detail["opening"] = record.get("opening")
                else:
                    detail = public_geometry_detail(self._geometry_model, identity,
                                                    body_bounds_cache=self._body_bounds_local)
                _validate_geometry_detail(detail, record["ifc_class"])
                self._geometry_details[identity] = deepcopy(detail)
            except (RuntimeError, ValueError, TypeError, AttributeError, KeyError) as error:
                self._geometry_detail_failures.add(identity)
                raise SceneError("SCENE_GEOMETRY_DETAIL_UNAVAILABLE") from error
        return deepcopy(self._geometry_details[identity])

    def body_vertices_mm(self, identity: str, *, opening: bool = False,
                         uncut: bool = False) -> list[list[float]]:
        """Internal geometry calculation only; never included in query payloads."""
        self.offered_record(identity)
        if self._geometry_model is None:
            raise SceneError('SCENE_GEOMETRY_DETAIL_UNAVAILABLE')
        product = self._geometry_model.by_guid(identity)
        if opening:
            product = _opening(product)
            if product is None:
                raise SceneError('SCENE_GEOMETRY_DETAIL_UNAVAILABLE')
        return public_body_vertices_mm(product, uncut=uncut)

    def _matching_records(self, q: Mapping[str, Any]) -> tuple[list[dict], list[str]]:
        """Select the actual public set, retaining relevant geometry gaps."""
        self._refresh_replaced_records()
        matches, unknown = [], []
        candidate_sets = []
        if q.get("ids") is not None:
            candidate_sets.append(set(q["ids"]) & self._record_ids)
        if q.get("ifc_classes"):
            classes = set(q["ifc_classes"])
            if "IfcWall" in classes:
                classes.add("IfcWallStandardCase")
            candidate_sets.append(set().union(*(self._metadata_ids["ifc_class"].get(c, set()) for c in classes)))
        for key in ("storey_id", "host_id"):
            if q.get(key) is not None:
                candidate_sets.append(self._metadata_ids[key].get(q[key], set()))
        identities = set.intersection(*candidate_sets) if candidate_sets else self._record_ids
        candidates = [self._by_id[identity] for identity in sorted(identities, key=self._record_order.__getitem__)]
        region = q.get("world_bounds_mm")
        if region:
            # A known disjoint bound proves false even when a later predicate's
            # placement/relationship fact is missing. Missing bounds remain
            # candidates until all other constraints have had a chance to fail.
            candidates = [record for record in candidates if not record.get("bounds_world_mm") or not any(
                record["bounds_world_mm"][a][1] < limits[0] or record["bounds_world_mm"][a][0] > limits[1]
                for a, limits in region.items())]
        # Cheap metadata filters run before any spatial geometry decisions.
        try:
            candidates, extra_unknown = apply_constraints(candidates, q, self._anchors())
            unknown.extend(extra_unknown)
        except SceneQueryError as error:
            raise SceneError(str(error)) from error
        for r in candidates:
            if region:
                if not r.get("bounds_world_mm"):
                    unknown.append(r["id"])
                    continue
            matches.append(r)
        axis = ORDER_AXES.get(q["order_by"]) if "select" not in q else None
        if axis is not None:
            sortable = [r for r in matches if r.get("center_world_mm")]
            unknown.extend(r["id"] for r in matches if not r.get("center_world_mm"))
            matches = sortable
        return matches, unknown

    def _refresh_replaced_records(self) -> None:
        """Reindex explicit fixture replacement; the production scene is read-only.

        Normal queries inspect only indexed candidates. A caller replacing the
        public fixture list (or changing its size) must not retain stale keys.
        In-place metadata mutation is outside this read-only scene contract.
        """
        if self.records is self._indexed_records and len(self.records) == self._indexed_count:
            return
        if self._query_results:
            raise SceneError("SCENE_RECORDS_REPLACED")
        if len(self.records) > MAX_SCENE_RECORDS:
            raise SceneError("SCENE_RECORD_BUDGET_EXCEEDED")
        by_id = {record["id"]: record for record in self.records}
        if len(by_id) != len(self.records):
            raise SceneError("SCENE_IDENTITY_AMBIGUOUS")
        self._by_id = {identity: record for identity, record in self._by_id.items() if identity in self._storey_ids}
        self._by_id.update(by_id)
        self._metadata_ids = {key: defaultdict(set) for key in ("ifc_class", "storey_id", "host_id")}
        self._record_ids = set(by_id)
        self._record_order = {}
        for ordinal, record in enumerate(self.records):
            self._record_order[record["id"]] = ordinal
            for key, index in self._metadata_ids.items():
                index[record.get(key)].add(record["id"])
        self._indexed_records, self._indexed_count = self.records, len(self.records)
        self._geometry_details.clear()
        self._geometry_detail_failures.clear()
        self.offered_ids.intersection_update(self._by_id)

    def offered_record(self, identity: str) -> dict:
        if identity not in self.offered_ids:
            raise SceneError("SCENE_ID_NOT_OFFERED")
        return deepcopy(self._by_id[identity])

    def complete_records(self, query: Mapping[str, Any]) -> list[dict] | None:
        """Verify coverage, not the wording/filter shape of previous queries.

        Any served pages may supply the target set, including mixed classes or
        different orderings. The known public scene verifies that *every*
        matching identity was offered; no unoffered fact becomes model input.
        Relevant unknown geometry and incomplete coverage still fail closed.
        """
        q = _validate_query(query)
        records, unknown = self._matching_records(q)
        if not self.pages or unknown or any(r["id"] not in self.offered_ids for r in records):
            return None
        return deepcopy(_ordered_records(records, q))


def public_geometry_detail(model: Any, identity: str, *, body_bounds_cache: dict[int, dict] | None = None) -> dict:
    """Read one bound identity from the caller's public IFC model only.

    This source-only primitive performs no index construction or product
    search. The scene wrapper verifies offered identities; an independent
    evaluator may instead pass its already-verified public operation bindings.
    Optional bounds caches belong to this one model instance. All translations
    and bounds are SI millimetres, regardless of native project length units.
    """
    cache = {} if body_bounds_cache is None else body_bounds_cache
    try:
        product = model.by_guid(identity)
        scale = ifcopenshell.util.unit.calculate_unit_scale(model)
        detail = {"placement_world_mm": _placement_world_mm(product, scale),
                  "body_bounds_local_mm": None if product.is_a("IfcBuildingStorey") else _local_body_bounds(product, cache)}
        if product.is_a("IfcWindow") or product.is_a("IfcDoor"):
            opening = _opening(product)
            host = _host(product)
            if opening is None or host is None or len(opening.HasFillings) != 1:
                raise ValueError("AMBIGUOUS_PUBLIC_OPENING_RELATION")
            relative = np.linalg.inv(np.asarray(detail["placement_world_mm"])) @ np.asarray(
                _placement_world_mm(opening, scale))
            detail["opening"] = {
                "id": opening.GlobalId, "host_id": host.GlobalId,
                "placement_in_product_mm": relative.tolist(),
                "body_bounds_local_mm": _local_body_bounds(opening, cache),
            }
        _validate_geometry_detail(detail, product.is_a())
        return deepcopy(detail)
    except (RuntimeError, ValueError, TypeError, AttributeError, KeyError) as error:
        raise SceneError("SCENE_GEOMETRY_DETAIL_UNAVAILABLE") from error


def public_body_vertices_mm(product: Any, *, uncut: bool = False) -> list[list[float]]:
    """Body vertices in occurrence-local millimetres for deterministic callers."""
    settings = ifcopenshell.geom.settings()
    settings.set('context-identifiers', ['Body'])
    if uncut:
        settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    shape = ifcopenshell.geom.create_shape(settings, product)
    vertices = shape.geometry.verts
    if not vertices:
        raise SceneError('SCENE_GEOMETRY_DETAIL_UNAVAILABLE')
    return [[float(v) * 1000. for v in vertices[i:i + 3]] for i in range(0, len(vertices), 3)]


def _local_body_bounds(product: Any, cache: dict[int, dict]) -> dict:
    key = product.id()
    if key not in cache:
        if product.Representation is None or not any(
            r.RepresentationIdentifier == "Body" and r.Items
            for r in product.Representation.Representations
        ):
            raise ValueError("PUBLIC_BODY_MISSING")
        settings = ifcopenshell.geom.settings()
        settings.set("context-identifiers", ["Body"])
        shape = ifcopenshell.geom.create_shape(settings, product)
        vertices = shape.geometry.verts
        if not vertices:
            raise ValueError("PUBLIC_BODY_EMPTY")
        cache[key] = {axis: [float(min(vertices[i::3])) * 1000, float(max(vertices[i::3])) * 1000]
                      for i, axis in enumerate("xyz")}
    return deepcopy(cache[key])


def _ordered_records(records: list[dict], query: Mapping[str, Any]) -> list[dict]:
    axis = ORDER_AXES.get(query["order_by"])
    return sorted(records,
                  key=lambda r: (r["center_world_mm"][axis], r["id"]) if axis is not None else (r["id"],),
                  reverse=query["descending"])


def _placement_world_mm(product: Any, project_unit_scale: float) -> list[list[float]]:
    if product.ObjectPlacement is None:
        raise ValueError("PUBLIC_PLACEMENT_MISSING")
    matrix = ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement).copy()
    matrix[:3, 3] *= project_unit_scale * 1000
    return matrix.tolist()


def _validate_geometry_detail(detail: Mapping[str, Any], ifc_class: str) -> None:
    def frame(value: Any) -> None:
        matrix = np.asarray(value, dtype=float)
        if (matrix.shape != (4, 4) or not np.isfinite(matrix).all()
                or not np.allclose(matrix[3], [0, 0, 0, 1], atol=1e-8, rtol=0)
                or not np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-8, rtol=0)
                or not math.isclose(float(np.linalg.det(matrix[:3, :3])), 1., abs_tol=1e-8)):
            raise ValueError("PUBLIC_PLACEMENT_INVALID")

    def bounds(value: Any) -> None:
        if not isinstance(value, Mapping) or set(value) != set("xyz"):
            raise ValueError("PUBLIC_BODY_BOUNDS_INVALID")
        for pair in value.values():
            if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                    or not all(type(v) in (int, float) and math.isfinite(v) for v in pair)
                    or pair[0] > pair[1]):
                raise ValueError("PUBLIC_BODY_BOUNDS_INVALID")

    frame(detail["placement_world_mm"])
    if ifc_class != "IfcBuildingStorey":
        bounds(detail["body_bounds_local_mm"])
    if ifc_class in {"IfcWindow", "IfcDoor"}:
        opening = detail["opening"]
        if not opening["id"] or not opening["host_id"]:
            raise ValueError("PUBLIC_OPENING_RELATION_MISSING")
        frame(opening["placement_in_product_mm"])
        bounds(opening["body_bounds_local_mm"])


def _validate_query(query: Mapping) -> dict:
    if not isinstance(query, Mapping) or set(query)-QUERY_KEYS:
        raise SceneError("SCENE_QUERY_INVALID")
    q = {"order_by": "id", "descending": False, "offset": 0, "limit": 40,
         "detail": "geometry", **deepcopy(dict(query))}
    if q["detail"] not in ("summary", "geometry"):
        raise SceneError("SCENE_QUERY_DETAIL_INVALID")
    if type(q["limit"]) is not int or not 1 <= q["limit"] <= MAX_PAGE_RECORDS:
        raise SceneError("SCENE_QUERY_LIMIT_INVALID")
    if type(q["offset"]) is not int or q["offset"] < 0:
        raise SceneError("SCENE_QUERY_OFFSET_INVALID")
    if (not isinstance(q["order_by"], str) or q["order_by"] not in {"id", *ORDER_AXES}
            or type(q["descending"]) is not bool):
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
    try:
        validate_extensions(q)
    except SceneQueryError as error:
        raise SceneError(str(error), path="/query" + getattr(error, "path", "")) from error
    return q


def _cohort_signature(query: Mapping[str, Any]) -> str:
    return json.dumps({key: value for key, value in query.items()
                       if key not in {"select", "detail", "offset", "limit", "order_by", "descending"}},
                      sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _space_boundaries(model: Any) -> dict[str, list[dict]]:
    """Only explicit public IFC boundaries, in both traversal directions."""
    result = defaultdict(list)
    for relation in model.by_type("IfcRelSpaceBoundary"):
        space = relation.RelatingSpace
        element = relation.RelatedBuildingElement
        if space is None or element is None:
            continue
        result[element.GlobalId].append({"kind": "space_boundary", "id": space.GlobalId})
        result[space.GlobalId].append({"kind": "space_boundary", "id": element.GlobalId})
    return {identity: [dict(pair) for pair in sorted({tuple(sorted(r.items())) for r in relations})]
            for identity, relations in result.items()}


def _true_north_world(model: Any) -> list[float] | None:
    """Use consistent explicit model-context TrueNorth; never infer geography."""
    vectors = []
    for context in model.by_type("IfcGeometricRepresentationContext"):
        if context.is_a("IfcGeometricRepresentationSubContext"):
            continue
        direction = getattr(context, "TrueNorth", None)
        if direction is None:
            continue
        ratios = direction.DirectionRatios
        if len(ratios) != 2 or not all(math.isfinite(v) for v in ratios):
            return None
        length = math.hypot(*ratios)
        if length == 0:
            return None
        vectors.append([ratios[0] / length, ratios[1] / length, 0.])
    if not vectors or any(not np.allclose(vectors[0], vector, atol=1e-8, rtol=0) for vector in vectors[1:]):
        return None
    return vectors[0]


def _opening(product: Any) -> Any | None:
    fillings = getattr(product, "FillsVoids", ())
    return fillings[0].RelatingOpeningElement if len(fillings) == 1 else None


def _host(product: Any) -> Any | None:
    opening = _opening(product) or product
    relations = getattr(opening, "VoidsElements", ())
    return relations[0].RelatingBuildingElement if len(relations) == 1 else None
