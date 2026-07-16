"""Dynamic package manifests for staged multi-storey generation."""

from __future__ import annotations

from typing import Any, Mapping


MANIFEST_VERSION = "text2ifc/generation-package-manifest/1.0"


def build_generation_package_manifest(
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Partition explicit expected facts without inventing building facts."""

    issues: list[dict[str, str]] = []
    storeys = _records(expected_facts.get("storeys"))
    storey_ids: list[str] = []
    for index, storey in enumerate(storeys):
        storey_id = _non_empty(storey.get("id"))
        if storey_id is None:
            issues.append(
                _issue("PACKAGE_STOREY_ID_MISSING", f"/storeys/{index}/id", "Storey ID is required.")
            )
            continue
        if storey_id in storey_ids:
            issues.append(
                _issue("PACKAGE_STOREY_ID_DUPLICATE", f"/storeys/{index}/id", f"Storey ID {storey_id!r} is duplicated.")
            )
        storey_ids.append(storey_id)
        if not isinstance(storey.get("elevation_mm"), (int, float)):
            issues.append(
                _issue(
                    "PACKAGE_STOREY_ELEVATION_MISSING",
                    f"/storeys/{index}/elevation_mm",
                    f"Storey {storey_id!r} has no explicit elevation.",
                )
            )

    blocking_expectations = [
        item
        for item in _records(expected_facts.get("unresolved_expectations"))
        if item.get("blocking") is not False
    ]
    for index, item in enumerate(blocking_expectations):
        issues.append(
            _issue(
                "PACKAGE_EXPECTATION_UNRESOLVED",
                str(item.get("path") or f"/unresolved_expectations/{index}"),
                "A blocking expected fact remains unresolved.",
            )
        )

    local_components = {storey_id: [] for storey_id in storey_ids}
    local_relationships = {storey_id: [] for storey_id in storey_ids}
    local_refs = {storey_id: set() for storey_id in storey_ids}
    for collection in ("walls", "spaces", "doors", "windows"):
        for index, record in enumerate(_records(expected_facts.get(collection))):
            storey_id = _non_empty(record.get("storey"))
            if storey_id not in local_components:
                issues.append(
                    _issue(
                        "PACKAGE_COMPONENT_OWNER_UNRESOLVED",
                        f"/{collection}/{index}/storey",
                        f"{collection[:-1].title()} does not identify an existing storey.",
                    )
                )
                continue
            component_id = _component_id(record, f"{collection[:-1]}-{storey_id}-{index + 1}")
            local_components[storey_id].append(component_id)
            if collection in {"doors", "windows"}:
                host_wall = _non_empty(record.get("host_wall"))
                if host_wall is None:
                    issues.append(
                        _issue(
                            "PACKAGE_HOST_WALL_UNRESOLVED",
                            f"/{collection}/{index}/host_wall",
                            f"{component_id!r} has no explicit host wall.",
                        )
                    )
                else:
                    local_refs[storey_id].add(host_wall)
                    local_components[storey_id].extend(
                        [host_wall, f"opening-{component_id}"]
                    )
                    local_relationships[storey_id].extend(
                        [f"rel-voids-{component_id}", f"rel-fills-{component_id}"]
                    )

    for index, record in enumerate(_records(expected_facts.get("products"))):
        storey_id = _non_empty(record.get("storey"))
        if storey_id not in local_components:
            issues.append(
                _issue(
                    "PACKAGE_COMPONENT_OWNER_UNRESOLVED",
                    f"/products/{index}/storey",
                    "Product does not identify an existing storey.",
                )
            )
        else:
            local_components[storey_id].append(
                _component_id(record, f"product-{storey_id}-{index + 1}")
            )
        if not _valid_linear_product_geometry(record.get("geometry")):
            issues.append(
                _issue(
                    "PACKAGE_PRODUCT_GEOMETRY_INCOMPLETE",
                    f"/products/{index}/geometry",
                    "A linear product requires axis-aligned non-zero endpoints, height, and thickness.",
                )
            )

    cross_components: list[str] = []
    cross_relationships: list[str] = []
    cross_refs: set[str] = set()
    for collection in ("slabs", "stairs"):
        for index, record in enumerate(_records(expected_facts.get(collection))):
            component_id = _component_id(record, f"{collection[:-1]}-{index + 1}")
            cross_components.append(component_id)
            if collection == "slabs":
                openings = _slab_openings(record)
                for opening_index, opening in enumerate(openings):
                    if not isinstance(opening.get("bounds"), Mapping):
                        continue
                    opening_id = _component_id(
                        opening,
                        (
                            f"opening-{component_id}-stair"
                            if opening_index == 0
                            else f"opening-{component_id}-stair-{opening_index + 1}"
                        ),
                    )
                    cross_components.append(opening_id)
                    relationship_id = (
                        f"rel-voids-{component_id}"
                        if opening_index == 0
                        else f"rel-voids-{component_id}-{opening_index + 1}"
                    )
                    cross_relationships.append(relationship_id)
            if collection == "stairs":
                flight_ids = _stair_flight_ids(record, component_id)
                cross_components.extend(flight_ids)
                cross_relationships.append(f"aggregate-{component_id}-flight")
                for field in ("from_storey", "to_storey"):
                    endpoint = _non_empty(record.get(field))
                    if endpoint not in storey_ids:
                        issues.append(
                            _issue(
                                "PACKAGE_CROSS_STOREY_ENDPOINT_UNRESOLVED",
                                f"/{collection}/{index}/{field}",
                                f"Stair endpoint {endpoint!r} is not an explicit storey.",
                            )
                        )
                    else:
                        cross_refs.add(endpoint)
    roof = expected_facts.get("roof")
    if isinstance(roof, Mapping):
        cross_components.append(_component_id(roof, "roof-main"))

    if issues:
        return {
            "schema_version": MANIFEST_VERSION,
            "status": "draft_required",
            "storey_count": len(storeys),
            "packages": [],
            "issues": sorted(issues, key=lambda item: (item["path"], item["code"])),
        }

    packages = [
        {
            "package_id": "package-skeleton",
            "kind": "skeleton",
            "storey_id": None,
            "owned_component_ids": [
                "project-main",
                "site-main",
                "building-main",
                *storey_ids,
            ],
            "owned_relationship_ids": [
                "aggregate-project-site",
                "aggregate-site-building",
                "aggregate-building-storeys",
            ],
            "allowed_reference_ids": [],
        }
    ]
    packages.extend(
        {
            "package_id": f"package-{storey_id}",
            "kind": "storey_local",
            "storey_id": storey_id,
            "owned_component_ids": _ordered_unique(local_components[storey_id]),
            "owned_relationship_ids": _ordered_unique(local_relationships[storey_id]),
            "allowed_reference_ids": sorted({storey_id, *local_refs[storey_id]}),
        }
        for storey_id in storey_ids
    )
    if cross_components or cross_relationships:
        packages.append(
            {
                "package_id": "package-cross-storey",
                "kind": "cross_storey",
                "storey_id": None,
                "owned_component_ids": _ordered_unique(cross_components),
                "owned_relationship_ids": _ordered_unique(cross_relationships),
                "allowed_reference_ids": sorted({*storey_ids, *cross_refs}),
            }
        )
    return {
        "schema_version": MANIFEST_VERSION,
        "status": "ready",
        "storey_count": len(storeys),
        "packages": packages,
        "issues": [],
    }


def _records(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) else []


def _slab_openings(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    openings = _records(record.get("openings"))
    singular = record.get("opening")
    if isinstance(singular, Mapping):
        openings.insert(0, dict(singular))
    return openings


def _stair_flight_ids(record: Mapping[str, Any], stair_id: str) -> list[str]:
    explicit = record.get("flight_ids")
    if isinstance(explicit, list) and explicit:
        return _ordered_unique([str(item) for item in explicit if str(item)])
    return [stair_id.replace("stair-", "stair-flight-", 1)]


def _valid_linear_product_geometry(value: Any) -> bool:
    if not isinstance(value, Mapping) or value.get("kind") != "linear_segment":
        return False
    start = value.get("start_mm")
    end = value.get("end_mm")
    if not (_numeric_point(start) and _numeric_point(end)):
        return False
    if start[2] != end[2] or (start[0] != end[0] and start[1] != end[1]):
        return False
    if start == end:
        return False
    return _positive_number(value.get("height_mm")) and _positive_number(
        value.get("thickness_mm")
    )


def _numeric_point(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    )


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _component_id(record: Mapping[str, Any], fallback: str) -> str:
    return (
        _non_empty(record.get("technical_id"))
        or _non_empty(record.get("id"))
        or _non_empty(record.get("source_id"))
        or fallback
    )


def _non_empty(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}
