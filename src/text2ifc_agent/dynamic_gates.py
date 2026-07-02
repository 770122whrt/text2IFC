"""Dynamic expected-fact gates for Phase 6.3."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping


DYNAMIC_GATES_SCHEMA_VERSION = "text2ifc/dynamic-gates/1.0"

_EXPECTED_COLLECTIONS = {
    "IfcBuildingStorey": "storeys",
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
            actual_storey = graph.storey_for_entity(entity_id)
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
                actual_host = graph.host_wall_for_opening_element(entity_id)
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
        source_paths=["expected-facts.json", "generator/candidate.json"],
    )


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
    for collection in ("spaces", "doors", "windows"):
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
    for collection in ("spaces", "doors", "windows"):
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
    source_paths: list[str],
) -> dict[str, Any]:
    issue_list = list(issues or [])
    return {
        "name": name,
        "applicability": applicability,
        "status": status,
        "basis": basis,
        "issue_count": len(issue_list),
        "issues": issue_list,
        "issue_codes": sorted({str(issue.get("code", "UNKNOWN")) for issue in issue_list}),
        "source_paths": source_paths,
    }
