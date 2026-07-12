"""Dynamic expected-fact gates for Phase 6.3."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any, Mapping


DYNAMIC_GATES_SCHEMA_VERSION = "text2ifc/dynamic-gates/1.0"

_EXPECTED_COLLECTIONS = {
    "IfcBuildingStorey": "storeys",
    "IfcWall": "walls",
    "IfcSpace": "spaces",
    "IfcDoor": "doors",
    "IfcWindow": "windows",
}
_CLASS_BY_COLLECTION = {value: key for key, value in _EXPECTED_COLLECTIONS.items()}


def evaluate_dynamic_gates(
    *,
    candidate: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate dynamic completeness and relationship gates.

    These gates are orchestration evidence only. They do not extend or redefine
    BIM JSON 2.0; they compare the generated candidate with explicit Design
    Brief-derived expectations.
    """
    graph = _CandidateGraph(candidate)
    return [
        _entity_completeness_gate(graph, expected_facts),
        _storey_containment_gate(graph, expected_facts),
        _storey_name_consistency_gate(graph, expected_facts),
        _opening_fill_gate(graph, expected_facts),
    ]


def _entity_completeness_gate(
    graph: "_CandidateGraph",
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    expected_counts = _expected_total_counts(expected_facts)
    if not expected_counts:
        return _gate(
            "dynamic_entity_completeness",
            applicability="not_applicable",
            status="skipped",
            basis="expected facts contain no explicit entity counts",
            source_paths=["expected-facts.json", "generator/candidate.json"],
        )

    issues: list[dict[str, Any]] = []
    for ifc_class, expected_count in sorted(expected_counts.items()):
        if expected_count <= 0:
            continue
        actual_count = graph.count_by_class(ifc_class)
        if actual_count < expected_count:
            collection = _EXPECTED_COLLECTIONS.get(ifc_class, ifc_class)
            issues.append(
                {
                    "code": "EXPECTED_ENTITY_MISSING",
                    "path": f"/{collection}",
                    "ifc_class": ifc_class,
                    "expected": expected_count,
                    "actual": actual_count,
                }
            )

    return _gate(
        "dynamic_entity_completeness",
        applicability="applicable",
        status="failed" if issues else "passed",
        basis="expected-facts total_counts compared with candidate entities",
        issues=issues,
        source_paths=["expected-facts.json", "generator/candidate.json"],
    )


def _storey_containment_gate(
    graph: "_CandidateGraph",
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    expected_storey_counts = _expected_counts_by_storey(expected_facts)
    exact_expected = _exact_expected_records(expected_facts)
    if not expected_storey_counts and not exact_expected:
        return _gate(
            "dynamic_storey_containment",
            applicability="not_applicable",
            status="skipped",
            basis="expected facts contain no storey membership expectations",
            source_paths=["expected-facts.json", "generator/candidate.json"],
        )

    issues: list[dict[str, Any]] = []
    entity_matches: list[dict[str, Any]] = []
    for collection, counts in sorted(expected_storey_counts.items()):
        ifc_class = _CLASS_BY_COLLECTION[collection]
        actual_counts = graph.count_collection_by_storey(ifc_class)
        for storey_id, expected_count in sorted(counts.items()):
            actual_count = actual_counts.get(storey_id, 0)
            if actual_count < expected_count:
                issues.append(
                    {
                        "code": "STOREY_CONTAINMENT_MISMATCH",
                        "path": f"/{collection}/{storey_id}",
                        "ifc_class": ifc_class,
                        "expected_storey": storey_id,
                        "expected": expected_count,
                        "actual": actual_count,
                    }
                )

    for collection, records in sorted(exact_expected.items()):
        for record in records:
            entity_id = _string(record.get("id"))
            expected_storey = _string(record.get("storey"))
            if not entity_id or not expected_storey:
                continue
            match = _resolve_expected_entity(
                graph=graph,
                expected_facts=expected_facts,
                collection=collection,
                record=record,
            )
            candidate_id = match.get("candidate_id") if match else None
            if match:
                entity_matches.append(match)
            actual_storey = graph.storey_for_entity(candidate_id) if candidate_id else None
            if actual_storey is None:
                issues.append(
                    {
                        "code": "EXPECTED_ENTITY_MISSING",
                        "path": f"/{collection}/{entity_id}",
                        "expected_storey": expected_storey,
                        "actual_storey": None,
                    }
                )
                continue
            if actual_storey != expected_storey:
                issues.append(
                    {
                        "code": "STOREY_CONTAINMENT_MISMATCH",
                        "path": f"/{collection}/{entity_id}/storey",
                        "expected_storey": expected_storey,
                        "actual_storey": actual_storey,
                    }
                )

            expected_host = _string(record.get("host_wall"))
            if expected_host and collection in {"doors", "windows"}:
                actual_host = graph.host_wall_for_opening_element(candidate_id) if candidate_id else None
                if actual_host != expected_host:
                    issues.append(
                        {
                            "code": "HOST_WALL_MISMATCH",
                            "path": f"/{collection}/{entity_id}/host_wall",
                            "expected_host_wall": expected_host,
                            "actual_host_wall": actual_host,
                        }
                    )

    return _gate(
        "dynamic_storey_containment",
        applicability="applicable",
        status="failed" if issues else "passed",
        basis="expected storey and host-wall facts compared with candidate placement/void-fill graph",
        issues=issues,
        entity_matches=entity_matches,
        source_paths=["expected-facts.json", "generator/candidate.json"],
    )


def _storey_name_consistency_gate(
    graph: "_CandidateGraph",
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    storey_names = {
        storey_id: storey_name
        for record in _records(expected_facts.get("storeys"))
        if (storey_id := _string(record.get("id")))
        and (storey_name := _string(record.get("name")))
    }
    unique_labels = {
        name: storey_id
        for name, ids in _group_storey_names(storey_names).items()
        if len(ids) == 1
        for storey_id in ids
    }
    if len(unique_labels) < 2:
        return _gate(
            "dynamic_storey_name_consistency",
            applicability="not_applicable",
            status="skipped",
            basis="expected facts contain fewer than two unique explicit storey names",
            source_paths=["expected-facts.json", "generator/candidate.json"],
        )

    issues: list[dict[str, Any]] = []
    for entity_id, entity in sorted(graph.entities.items()):
        actual_storey = graph.storey_for_entity(entity_id)
        expected_storey_name = storey_names.get(actual_storey or "")
        attributes = entity.get("attributes", {})
        actual_name = _string(attributes.get("Name")) if isinstance(attributes, Mapping) else None
        if not actual_storey or not expected_storey_name or not actual_name:
            continue
        for conflicting_name, conflicting_storey in sorted(unique_labels.items()):
            if conflicting_storey == actual_storey or conflicting_name not in actual_name:
                continue
            issues.append(
                {
                    "code": "STOREY_NAME_CONFLICT",
                    "path": f"/entities/{entity_id}/attributes/Name",
                    "entity_id": entity_id,
                    "target_entity_ids": [entity_id],
                    "actual_name": actual_name,
                    "expected_storey": actual_storey,
                    "expected_storey_name": expected_storey_name,
                    "conflicting_storey": conflicting_storey,
                    "conflicting_storey_name": conflicting_name,
                }
            )

    return _gate(
        "dynamic_storey_name_consistency",
        applicability="applicable",
        status="failed" if issues else "passed",
        basis="explicit component storey labels compared with placement-derived ownership",
        issues=issues,
        source_paths=["expected-facts.json", "generator/candidate.json"],
    )


def _group_storey_names(storey_names: Mapping[str, str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for storey_id, name in storey_names.items():
        grouped[name].append(storey_id)
    return grouped


def _resolve_expected_entity(
    *,
    graph: "_CandidateGraph",
    expected_facts: Mapping[str, Any],
    collection: str,
    record: Mapping[str, Any],
) -> dict[str, str] | None:
    expected_id = _string(record.get("id"))
    expected_storey = _string(record.get("storey"))
    if not expected_id or not expected_storey:
        return None
    canonical_id = _canonical_entity_id(
        expected_facts=expected_facts,
        collection=collection,
        expected_id=expected_id,
        expected_storey=expected_storey,
    )
    if canonical_id and graph.entity(canonical_id) is not None:
        return {
            "collection": collection,
            "expected_id": expected_id,
            "candidate_id": canonical_id,
            "match_basis": "canonical_entity_id",
        }
    if graph.entity(expected_id) is not None:
        return {
            "collection": collection,
            "expected_id": expected_id,
            "candidate_id": expected_id,
            "match_basis": "exact_brief_id",
        }

    expected_tokens = set(_entity_id_tokens(expected_id))
    if not expected_tokens:
        return None
    ifc_class = _CLASS_BY_COLLECTION[collection]
    matching_ids = [
        candidate_id
        for candidate_id in graph.ids_by_class(ifc_class)
        if graph.storey_for_entity(candidate_id) == expected_storey
        and expected_tokens.issubset(set(_entity_id_tokens(candidate_id)))
    ]
    if len(matching_ids) != 1:
        return None
    return {
        "collection": collection,
        "expected_id": expected_id,
        "candidate_id": matching_ids[0],
        "match_basis": "unique_semantic_alias",
    }


def _canonical_entity_id(
    *,
    expected_facts: Mapping[str, Any],
    collection: str,
    expected_id: str,
    expected_storey: str,
) -> str | None:
    contract = expected_facts.get("entity_id_contract", {})
    records = contract.get(collection, []) if isinstance(contract, Mapping) else []
    for item in _records(records):
        if (
            _string(item.get("brief_id")) == expected_id
            and _string(item.get("storey")) == expected_storey
        ):
            return _string(item.get("entity_id"))
    return None


def _entity_id_tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def _opening_fill_gate(
    graph: "_CandidateGraph",
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    expected = _expected_opening_fill_counts(expected_facts)
    if not expected:
        return _gate(
            "dynamic_opening_fill",
            applicability="not_applicable",
            status="skipped",
            basis="expected facts contain no opening/fill obligations",
            source_paths=["expected-facts.json", "generator/candidate.json"],
        )

    issues: list[dict[str, Any]] = []
    for collection, expected_count in sorted(expected.items()):
        ifc_class = _CLASS_BY_COLLECTION[collection]
        if expected_count <= 0:
            continue
        expected_by_candidate: dict[str, Mapping[str, Any]] = {}
        for record in _records(expected_facts.get(collection)):
            match = _resolve_expected_entity(
                graph=graph,
                expected_facts=expected_facts,
                collection=collection,
                record=record,
            )
            if match is not None:
                expected_by_candidate[match["candidate_id"]] = record
        actual_elements = graph.ids_by_class(ifc_class)
        elements_with_fill = [
            entity_id
            for entity_id in actual_elements
            if graph.explicit_fill_opening_for(entity_id)
        ]
        elements_with_void = [
            entity_id
            for entity_id in actual_elements
            if graph.explicit_host_wall_for_opening_element(entity_id)
        ]
        for entity_id in elements_with_fill:
            opening_id = graph.explicit_fill_opening_for(entity_id)
            host_wall = (
                graph.explicit_host_wall_for_opening(opening_id)
                if opening_id
                else None
            )
            issues.extend(
                _opening_fill_geometry_issues(
                    graph,
                    element_id=entity_id,
                    opening_id=opening_id,
                    host_wall=host_wall,
                    expected_record=expected_by_candidate.get(entity_id),
                )
            )
        if len(elements_with_fill) < expected_count:
            issues.append(
                {
                    "code": "OPENING_FILL_RELATIONSHIP_MISSING",
                    "path": f"/{collection}/fills",
                    "ifc_class": ifc_class,
                    "expected": expected_count,
                    "actual": len(elements_with_fill),
                }
            )
        if len(elements_with_void) < expected_count:
            issues.append(
                {
                    "code": "VOID_RELATIONSHIP_MISSING",
                    "path": f"/{collection}/voids",
                    "ifc_class": ifc_class,
                    "expected": expected_count,
                    "actual": len(elements_with_void),
                }
            )

    return _gate(
        "dynamic_opening_fill",
        applicability="applicable",
        status="failed" if issues else "passed",
        basis="expected opening/fill obligations compared with IfcRelVoidsElement and IfcRelFillsElement",
        issues=issues,
        source_paths=["expected-facts.json", "generator/candidate.json"],
    )


def _opening_fill_geometry_issues(
    graph: "_CandidateGraph",
    *,
    element_id: str,
    opening_id: str | None,
    host_wall: str | None,
    expected_record: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not opening_id or not host_wall:
        return []
    issues: list[dict[str, Any]] = []
    opening = graph.entity(opening_id)
    host = graph.entity(host_wall)
    element = graph.entity(element_id)
    opening_placement = _placement(opening)
    host_profile = _rectangle_profile(host)
    opening_profile = _rectangle_profile(opening)
    opening_origin = _number_list(opening_placement.get("origin"), 3)
    if (
        isinstance(expected_record, Mapping)
        and expected_record.get("alignment") == "host_centerline"
        and opening_origin is not None
        and abs(float(opening_origin[0])) > 1e-6
    ):
        issues.append(
            {
                "code": "OPENING_HOST_ALIGNMENT_MISMATCH",
                "path": f"/entities/{opening_id}/attributes/ObjectPlacement/origin/0",
                "message": (
                    "Expected host_centerline alignment requires opening local X "
                    "origin 0 in the host wall coordinate system."
                ),
                "element_id": element_id,
                "opening_id": opening_id,
                "host_wall": host_wall,
                "target_entity_ids": [opening_id],
                "source_alignment": "host_centerline",
                "expected_local_x": 0.0,
                "actual_local_x": float(opening_origin[0]),
            }
        )
    host_bounds = _representation_bounds(host)
    opening_local_bounds = _representation_bounds(opening)
    opening_host_bounds = _placed_bounds(opening_local_bounds, opening_placement)
    opening_outside_host = (
        host_bounds is not None
        and opening_host_bounds is not None
        and not _bounds_contain(host_bounds, opening_host_bounds)
    )
    if opening_outside_host:
        zero_origin_placement = dict(opening_placement)
        zero_origin_placement["origin"] = [0, 0, 0]
        opening_zero_origin_bounds = _placed_bounds(
            opening_local_bounds, zero_origin_placement
        )
        shape_exceeds_host = all(
            bounds is not None for bounds in (opening_zero_origin_bounds, host_bounds)
        ) and any(
            float(opening_zero_origin_bounds["size"][index])
            > float(host_bounds["size"][index]) + 1e-6
            for index in range(3)
        )
        allowed_origin_ranges = (
            _allowed_origin_ranges(host_bounds, opening_zero_origin_bounds)
            if not shape_exceeds_host
            else None
        )
        issues.append(
            {
                "code": "OPENING_HOST_LOCAL_BOUNDS_MISMATCH",
                "path": (
                    f"/entities/{opening_id}/attributes/Representation"
                    if shape_exceeds_host
                    else f"/entities/{opening_id}/attributes/ObjectPlacement/origin"
                ),
                "message": (
                    "Opening transformed local bounds must remain inside the host "
                    "wall bounds. Check placement and representation axes."
                ),
                "element_id": element_id,
                "opening_id": opening_id,
                "host_wall": host_wall,
                "target_entity_ids": [opening_id],
                "opening_origin": opening_origin,
                "opening_profile": opening_profile,
                "host_profile": host_profile,
                "opening_bounds": opening_host_bounds,
                "host_bounds": host_bounds,
                **(
                    {"allowed_origin_ranges": allowed_origin_ranges}
                    if allowed_origin_ranges is not None
                    else {}
                ),
            }
        )
    elif host_profile and opening_profile and opening_origin:
        half_host_x = host_profile["x"] / 2
        half_opening_x = opening_profile["x"] / 2
        outside_along_length = abs(opening_origin[0]) + half_opening_x > half_host_x + 1e-6
        if outside_along_length:
            issues.append(
                {
                    "code": "OPENING_HOST_LOCAL_BOUNDS_MISMATCH",
                    "path": f"/entities/{opening_id}/attributes/ObjectPlacement/origin",
                    "message": (
                        "Opening placement origin and profile must remain inside the "
                        "host wall local length and thickness bounds."
                    ),
                    "element_id": element_id,
                    "opening_id": opening_id,
                    "host_wall": host_wall,
                    "opening_origin": opening_origin,
                    "host_profile": host_profile,
                    "opening_profile": opening_profile,
                    "outside_along_length": outside_along_length,
                    "outside_thickness": False,
                    "target_entity_ids": [opening_id],
                }
            )
    element_placement = _placement(element)
    element_relative_to = _string(element_placement.get("relative_to"))
    element_ref = _number_list(element_placement.get("ref_direction"), 3)
    if element_relative_to != opening_id:
        issues.append(
            {
                "code": "FILLING_PLACEMENT_CHAIN_MISMATCH",
                "path": f"/entities/{element_id}/attributes/ObjectPlacement/relative_to",
                "element_id": element_id,
                "opening_id": opening_id,
                "host_wall": host_wall,
                "actual_relative_to": element_relative_to,
                "expected_relative_to": opening_id,
            }
        )
    if element_relative_to == opening_id and element_ref and element_ref != [1, 0, 0]:
        issues.append(
            {
                "code": "FILLING_RELATIVE_ROTATION_MISMATCH",
                "path": f"/entities/{element_id}/attributes/ObjectPlacement/ref_direction",
                "element_id": element_id,
                "opening_id": opening_id,
                "host_wall": host_wall,
                "actual_ref_direction": element_ref,
                "expected_ref_direction": [1, 0, 0],
            }
        )
    element_profile = _rectangle_profile(element)
    element_origin = _number_list(element_placement.get("origin"), 3)
    element_local_bounds = _representation_bounds(element)
    element_opening_bounds = _placed_bounds(element_local_bounds, element_placement)
    if (
        element_relative_to == opening_id
        and element_profile
        and opening_profile
        and element_origin
        and opening_local_bounds is not None
        and element_opening_bounds is not None
        and not opening_outside_host
    ):
        if not _bounds_contain(opening_local_bounds, element_opening_bounds):
            issues.append(
                {
                    "code": "FILLING_OPENING_BOUNDS_MISMATCH",
                    "path": (
                        f"/entities/{element_id}/attributes/ObjectPlacement/origin"
                        if any(abs(float(value)) > 1e-6 for value in element_origin)
                        else f"/entities/{element_id}/attributes/Representation"
                    ),
                    "message": (
                        "Filling transformed local bounds must remain inside the "
                        "opening bounds. Check placement and representation axes."
                    ),
                    "element_id": element_id,
                    "opening_id": opening_id,
                    "host_wall": host_wall,
                    "target_entity_ids": [element_id],
                    "element_origin": element_origin,
                    "element_profile": element_profile,
                    "opening_profile": opening_profile,
                    "element_bounds": element_opening_bounds,
                    "opening_bounds": opening_local_bounds,
                }
            )
    return issues


class _CandidateGraph:
    def __init__(self, candidate: Mapping[str, Any]) -> None:
        entities = candidate.get("entities", [])
        relationships = candidate.get("relationships", [])
        self.entities: dict[str, Mapping[str, Any]] = {
            str(entity.get("id")): entity
            for entity in entities
            if isinstance(entity, Mapping) and entity.get("id") is not None
        }
        self.relationships = [
            relationship
            for relationship in relationships
            if isinstance(relationship, Mapping)
        ]
        self._containment = self._build_explicit_containment()
        self._fill_by_element = self._build_fill_by_element()
        self._host_by_opening = self._build_host_by_opening()

    def count_by_class(self, ifc_class: str) -> int:
        return len(self.ids_by_class(ifc_class))

    def ids_by_class(self, ifc_class: str) -> list[str]:
        return [
            entity_id
            for entity_id, entity in self.entities.items()
            if entity.get("ifc_class") == ifc_class
        ]

    def count_collection_by_storey(self, ifc_class: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entity_id in self.ids_by_class(ifc_class):
            storey_id = self.storey_for_entity(entity_id)
            if storey_id:
                counts[storey_id] = counts.get(storey_id, 0) + 1
        return counts

    def storey_for_entity(self, entity_id: str) -> str | None:
        if entity_id in self._containment:
            return self._containment[entity_id]
        current = entity_id
        seen: set[str] = set()
        while current and current not in seen:
            seen.add(current)
            entity = self.entities.get(current)
            if entity is None:
                return None
            if entity.get("ifc_class") == "IfcBuildingStorey":
                return current
            placement = entity.get("attributes", {}).get("ObjectPlacement", {})
            relative_to = placement.get("relative_to") if isinstance(placement, Mapping) else None
            current = relative_to if isinstance(relative_to, str) else ""
        return None

    def fill_opening_for(self, element_id: str) -> str | None:
        opening_id = self._fill_by_element.get(element_id)
        if opening_id:
            return opening_id
        entity = self.entities.get(element_id)
        if entity is None:
            return None
        placement = entity.get("attributes", {}).get("ObjectPlacement", {})
        relative_to = placement.get("relative_to") if isinstance(placement, Mapping) else None
        if isinstance(relative_to, str) and self._is_opening(relative_to):
            return relative_to
        return None

    def explicit_fill_opening_for(self, element_id: str) -> str | None:
        return self._fill_by_element.get(element_id)

    def host_wall_for_opening_element(self, element_id: str) -> str | None:
        opening_id = self.fill_opening_for(element_id)
        if not opening_id:
            return None
        host = self._host_by_opening.get(opening_id)
        if host:
            return host
        opening = self.entities.get(opening_id)
        if opening is None:
            return None
        placement = opening.get("attributes", {}).get("ObjectPlacement", {})
        relative_to = placement.get("relative_to") if isinstance(placement, Mapping) else None
        if isinstance(relative_to, str) and self._is_wall(relative_to):
            return relative_to
        return None

    def explicit_host_wall_for_opening_element(self, element_id: str) -> str | None:
        opening_id = self.explicit_fill_opening_for(element_id)
        if not opening_id:
            return None
        return self._host_by_opening.get(opening_id)

    def explicit_host_wall_for_opening(self, opening_id: str) -> str | None:
        return self._host_by_opening.get(opening_id)

    def entity(self, entity_id: str) -> Mapping[str, Any] | None:
        return self.entities.get(entity_id)

    def _build_explicit_containment(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for relationship in self.relationships:
            if relationship.get("ifc_class") != "IfcRelContainedInSpatialStructure":
                continue
            attributes = relationship.get("attributes", {})
            if not isinstance(attributes, Mapping):
                continue
            storey = _string(attributes.get("RelatingStructure"))
            related = attributes.get("RelatedElements", [])
            if not storey or not isinstance(related, list):
                continue
            for entity_id in related:
                if isinstance(entity_id, str):
                    result[entity_id] = storey
        return result

    def _build_fill_by_element(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for relationship in self.relationships:
            if relationship.get("ifc_class") != "IfcRelFillsElement":
                continue
            attributes = relationship.get("attributes", {})
            if not isinstance(attributes, Mapping):
                continue
            element = _string(attributes.get("RelatedBuildingElement"))
            opening = _string(attributes.get("RelatingOpeningElement"))
            if element and opening:
                result[element] = opening
        return result

    def _build_host_by_opening(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for relationship in self.relationships:
            if relationship.get("ifc_class") != "IfcRelVoidsElement":
                continue
            attributes = relationship.get("attributes", {})
            if not isinstance(attributes, Mapping):
                continue
            host = _string(attributes.get("RelatingBuildingElement"))
            opening = _string(attributes.get("RelatedOpeningElement"))
            if host and opening:
                result[opening] = host
        return result

    def _is_opening(self, entity_id: str) -> bool:
        entity = self.entities.get(entity_id)
        return entity is not None and entity.get("ifc_class") == "IfcOpeningElement"

    def _is_wall(self, entity_id: str) -> bool:
        entity = self.entities.get(entity_id)
        return entity is not None and str(entity.get("ifc_class", "")).startswith("IfcWall")


def _expected_total_counts(expected_facts: Mapping[str, Any]) -> dict[str, int]:
    raw_counts = expected_facts.get("total_counts", {})
    counts = {
        ifc_class: int(value)
        for ifc_class, value in raw_counts.items()
        if ifc_class in _EXPECTED_COLLECTIONS and _is_non_negative_int(value)
    } if isinstance(raw_counts, Mapping) else {}
    for ifc_class, collection in _EXPECTED_COLLECTIONS.items():
        if ifc_class not in counts:
            records = _records(expected_facts.get(collection))
            if records:
                counts[ifc_class] = len(records)
    return counts


def _expected_counts_by_storey(expected_facts: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for collection in ("walls", "spaces", "doors", "windows"):
        explicit_key = f"{collection[:-1]}_counts_by_storey"
        raw_counts = expected_facts.get(explicit_key, {})
        counts = _clean_storey_counts(raw_counts)
        if not counts:
            counts = _count_records_by_storey(_records(expected_facts.get(collection)))
        if counts:
            result[collection] = counts
    return result


def _expected_opening_fill_counts(expected_facts: Mapping[str, Any]) -> dict[str, int]:
    relationships = expected_facts.get("required_relationships", {})
    opening_fill = (
        relationships.get("opening_fill", {})
        if isinstance(relationships, Mapping)
        else {}
    )
    counts: dict[str, int] = {}
    if isinstance(opening_fill, Mapping):
        for collection in ("doors", "windows"):
            value = opening_fill.get(collection)
            if _is_non_negative_int(value):
                counts[collection] = int(value)
    for collection in ("doors", "windows"):
        if collection not in counts:
            records = _records(expected_facts.get(collection))
            if records:
                counts[collection] = len(records)
    return counts


def _exact_expected_records(expected_facts: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = {}
    for collection in ("walls", "spaces", "doors", "windows"):
        records = [
            record
            for record in _records(expected_facts.get(collection))
            if _string(record.get("id"))
        ]
        if records:
            result[collection] = records
    return result


def _records(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _placement(entity: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(entity, Mapping):
        return {}
    placement = entity.get("attributes", {}).get("ObjectPlacement", {})
    return placement if isinstance(placement, Mapping) else {}


def _rectangle_profile(entity: Mapping[str, Any] | None) -> dict[str, float] | None:
    if not isinstance(entity, Mapping):
        return None
    representation = entity.get("attributes", {}).get("Representation", {})
    if not isinstance(representation, Mapping):
        return None
    profile = representation.get("profile", {})
    if not isinstance(profile, Mapping) or profile.get("kind") != "rectangle":
        return None
    x = profile.get("x")
    y = profile.get("y")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None
    return {"x": float(x), "y": float(y)}


def _representation_bounds(entity: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(entity, Mapping):
        return None
    representation = entity.get("attributes", {}).get("Representation", {})
    if not isinstance(representation, Mapping):
        return None
    profile = _rectangle_profile(entity)
    depth = representation.get("depth")
    direction = _number_list(representation.get("direction"), 3)
    if profile is None or not isinstance(depth, (int, float)) or direction is None:
        return None
    axis = _normalized_vector(direction)
    if axis is None:
        return None
    candidate = [1.0, 0.0, 0.0]
    if abs(_dot(axis, candidate)) > 0.9:
        candidate = [0.0, 1.0, 0.0]
    projection = _dot(axis, candidate)
    ref_direction = _normalized_vector(
        [candidate[index] - projection * axis[index] for index in range(3)]
    )
    if ref_direction is None:
        return None
    local_y = _cross(axis, ref_direction)
    points = []
    for x in (-profile["x"] / 2, profile["x"] / 2):
        for y in (-profile["y"] / 2, profile["y"] / 2):
            for extrusion in (0.0, float(depth)):
                points.append(
                    [
                        ref_direction[index] * x
                        + local_y[index] * y
                        + axis[index] * extrusion
                        for index in range(3)
                    ]
                )
    return _bounds_from_points(points)


def _placed_bounds(
    bounds: Mapping[str, Any] | None,
    placement: Mapping[str, Any],
) -> dict[str, Any] | None:
    if bounds is None:
        return None
    origin = _number_list(placement.get("origin"), 3)
    axis = _normalized_vector(_number_list(placement.get("axis"), 3))
    ref_direction = _normalized_vector(_number_list(placement.get("ref_direction"), 3))
    if origin is None or axis is None or ref_direction is None:
        return None
    local_y = _cross(axis, ref_direction)
    points = []
    for x in (bounds["min"][0], bounds["max"][0]):
        for y in (bounds["min"][1], bounds["max"][1]):
            for z in (bounds["min"][2], bounds["max"][2]):
                points.append(
                    [
                        float(origin[index])
                        + ref_direction[index] * x
                        + local_y[index] * y
                        + axis[index] * z
                        for index in range(3)
                    ]
                )
    return _bounds_from_points(points)


def _bounds_from_points(points: list[list[float]]) -> dict[str, list[float]]:
    minimum = [min(point[index] for point in points) for index in range(3)]
    maximum = [max(point[index] for point in points) for index in range(3)]
    return {
        "min": minimum,
        "max": maximum,
        "size": [maximum[index] - minimum[index] for index in range(3)],
    }


def _bounds_contain(
    outer: Mapping[str, Any], inner: Mapping[str, Any], *, tolerance: float = 1e-6
) -> bool:
    return all(
        float(inner["min"][index]) >= float(outer["min"][index]) - tolerance
        and float(inner["max"][index]) <= float(outer["max"][index]) + tolerance
        for index in range(3)
    )


def _allowed_origin_ranges(
    outer: Mapping[str, Any], inner: Mapping[str, Any]
) -> dict[str, list[float]]:
    return {
        axis: [
            float(outer["min"][index]) - float(inner["min"][index]),
            float(outer["max"][index]) - float(inner["max"][index]),
        ]
        for index, axis in enumerate(("x", "y", "z"))
    }


def _normalized_vector(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    numbers = [float(item) for item in value[:3]]
    magnitude = sum(item * item for item in numbers) ** 0.5
    if magnitude <= 1e-12:
        return None
    return [item / magnitude for item in numbers]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _number_list(value: Any, length: int) -> list[int | float] | None:
    if (
        isinstance(value, list)
        and len(value) >= length
        and all(isinstance(item, (int, float)) for item in value[:length])
    ):
        return list(value[:length])
    return None


def _clean_storey_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(storey): int(count)
        for storey, count in value.items()
        if isinstance(storey, str) and storey and _is_non_negative_int(count)
    }


def _count_records_by_storey(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        storey = _string(record.get("storey"))
        if storey:
            counts[storey] += 1
    return dict(sorted(counts.items()))


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and value >= 0


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _gate(
    name: str,
    *,
    applicability: str,
    status: str,
    basis: str,
    issues: list[dict[str, Any]] | None = None,
    entity_matches: list[dict[str, Any]] | None = None,
    source_paths: list[str],
) -> dict[str, Any]:
    issue_list = list(issues or [])
    payload = {
        "name": name,
        "applicability": applicability,
        "status": status,
        "basis": basis,
        "issue_count": len(issue_list),
        "issues": issue_list,
        "issue_codes": sorted({str(issue.get("code", "UNKNOWN")) for issue in issue_list}),
        "source_paths": source_paths,
    }
    if entity_matches is not None:
        payload["entity_matches"] = entity_matches
    return payload
