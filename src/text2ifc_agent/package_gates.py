"""Deterministic ownership and reference gates for generation packages."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


_LOCAL_CLASSES = {"IfcWall", "IfcWallStandardCase", "IfcSpace", "IfcDoor", "IfcWindow", "IfcOpeningElement"}
_CROSS_CLASSES = {
    "IfcSlab",
    "IfcStair",
    "IfcStairFlight",
    "IfcRamp",
    "IfcRampFlight",
    "IfcRoof",
    "IfcOpeningElement",
}
_CROSS_ONLY_CLASSES = _CROSS_CLASSES - {"IfcOpeningElement"}
_REPRESENTED_CLASSES = _LOCAL_CLASSES | (_CROSS_CLASSES - {"IfcStair"})
_REFERENCE_FIELDS = {
    "relative_to",
    "RelatingObject",
    "RelatedObjects",
    "RelatingStructure",
    "RelatedElements",
    "RelatingBuildingElement",
    "RelatingOpeningElement",
    "RelatedBuildingElement",
    "RelatedOpeningElement",
}


def validate_package_changeset(
    *,
    manifest: Mapping[str, Any],
    package_id: str,
    workspace: Mapping[str, Any],
    changeset: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one add-oriented package before composition."""

    issues: list[dict[str, Any]] = []
    package = _find_package(manifest, package_id)
    if package is None:
        return _result([_issue("PACKAGE_NOT_DECLARED", "/package_id", package_id)])
    if changeset.get("package_id") not in {None, package_id}:
        issues.append(_issue("PACKAGE_BINDING_MISMATCH", "/package_id", package_id))

    operations = _records(changeset.get("operations"))
    existing = _components(workspace)
    targets = [str(operation.get("target_id") or "") for operation in operations]
    owned = set(package.get("owned_component_ids", [])) | set(
        package.get("owned_relationship_ids", [])
    )
    allowed_refs = set(package.get("allowed_reference_ids", []))
    duplicate_targets = {target for target, count in Counter(targets).items() if target and count > 1}
    values: dict[str, dict[str, Any]] = {}

    for index, operation in enumerate(operations):
        target_id = targets[index]
        path = f"/operations/{index}"
        if operation.get("op") not in {"add_entity", "add_relationship"}:
            issues.append(_issue("PACKAGE_OPERATION_NOT_ADD", f"{path}/op", target_id))
        if target_id in existing or target_id in duplicate_targets:
            issues.append(_issue("PACKAGE_DUPLICATE_COMPONENT_ID", f"{path}/target_id", target_id))
        if target_id not in owned:
            issues.append(_issue("PACKAGE_COMPONENT_NOT_OWNED", f"{path}/target_id", target_id))
        value = operation.get("value")
        if not isinstance(value, Mapping) or value.get("id") != target_id:
            issues.append(_issue("PACKAGE_VALUE_ID_MISMATCH", f"{path}/value/id", target_id))
            continue
        values[target_id] = dict(value)
        issues.extend(_representation_issues(target_id, value))

    package_ids = set(values)
    visible_ids = set(existing) | package_ids | allowed_refs
    for component_id, value in values.items():
        for reference_path, reference_id in _component_references(value):
            if reference_id not in visible_ids:
                issues.append(
                    _issue(
                        "PACKAGE_REFERENCE_UNRESOLVED",
                        f"/{component_id}{reference_path}",
                        component_id,
                        reference_id,
                    )
                )

    for component_id in sorted(owned - set(existing) - set(values)):
        issues.append(
            _issue(
                "PACKAGE_OWNED_COMPONENT_MISSING",
                f"/{component_id}",
                component_id,
                message=(
                    f"Package {package_id!r} declares component {component_id!r}, "
                    "but the changeset did not generate it."
                ),
            )
        )

    issues.extend(_manifest_ownership_issues(manifest))
    kind = str(package.get("kind"))
    if kind == "storey_local":
        issues.extend(_local_package_issues(package, workspace, values))
    elif kind == "cross_storey":
        for component_id, value in values.items():
            if not str(value.get("ifc_class", "")).startswith("IfcRel") and value.get("ifc_class") not in _CROSS_CLASSES:
                issues.append(_issue("PACKAGE_CROSS_COMPONENT_INVALID", f"/{component_id}/ifc_class", component_id))
    return _result(issues)


def _local_package_issues(
    package: Mapping[str, Any],
    workspace: Mapping[str, Any],
    values: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    storey_id = str(package.get("storey_id") or "")
    combined = {**_components(workspace), **values}
    relationships = [
        value for value in combined.values() if str(value.get("ifc_class", "")).startswith("IfcRel")
    ]
    current_relationships = [
        value for value in values.values() if str(value.get("ifc_class", "")).startswith("IfcRel")
    ]
    containment = _containment_map(relationships)
    for component_id, value in values.items():
        ifc_class = str(value.get("ifc_class", ""))
        if ifc_class in _CROSS_ONLY_CLASSES:
            issues.append(_issue("PACKAGE_VERTICAL_COMPONENT_IN_LOCAL", f"/{component_id}/ifc_class", component_id))
        elif not ifc_class.startswith("IfcRel") and ifc_class not in _LOCAL_CLASSES:
            issues.append(_issue("PACKAGE_LOCAL_COMPONENT_INVALID", f"/{component_id}/ifc_class", component_id))

    voids = {
        str(rel.get("attributes", {}).get("RelatedOpeningElement")): str(
            rel.get("attributes", {}).get("RelatingBuildingElement")
        )
        for rel in current_relationships
        if rel.get("ifc_class") == "IfcRelVoidsElement"
    }
    fills = {
        str(rel.get("attributes", {}).get("RelatedBuildingElement")): str(
            rel.get("attributes", {}).get("RelatingOpeningElement")
        )
        for rel in current_relationships
        if rel.get("ifc_class") == "IfcRelFillsElement"
    }
    for opening_id, host_id in voids.items():
        host_storey = containment.get(host_id)
        if host_storey is not None and host_storey != storey_id:
            issues.append(
                _issue(
                    "PACKAGE_HOST_STOREY_MISMATCH",
                    f"/{opening_id}/host",
                    opening_id,
                    host_id,
                )
            )
    for filling_id, opening_id in fills.items():
        if opening_id not in combined:
            continue
        if opening_id not in voids:
            issues.append(
                _issue("PACKAGE_OPENING_ORPHANED", f"/{filling_id}/opening", filling_id, opening_id)
            )
        filling_storey = containment.get(filling_id)
        if filling_storey is not None and filling_storey != storey_id:
            issues.append(
                _issue("PACKAGE_FILLING_STOREY_MISMATCH", f"/{filling_id}/storey", filling_id, storey_id)
            )
    return issues


def _manifest_ownership_issues(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    owners: dict[str, list[str]] = {}
    for package in _records(manifest.get("packages")):
        for component_id in [
            *package.get("owned_component_ids", []),
            *package.get("owned_relationship_ids", []),
        ]:
            owners.setdefault(str(component_id), []).append(str(package.get("package_id")))
    return [
        _issue("PACKAGE_COMPONENT_MULTIPLE_OWNERS", "/packages", component_id)
        for component_id, package_ids in sorted(owners.items())
        if len(package_ids) > 1
    ]


def _representation_issues(
    component_id: str,
    value: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if str(value.get("ifc_class", "")) not in _REPRESENTED_CLASSES:
        return []
    attributes = value.get("attributes")
    representation = attributes.get("Representation") if isinstance(attributes, Mapping) else None
    if not isinstance(representation, Mapping):
        return [
            _issue(
                "PACKAGE_REPRESENTATION_MISSING",
                f"/{component_id}/attributes/Representation",
                component_id,
            )
        ]
    profile = representation.get("profile")
    if not isinstance(profile, Mapping) or profile.get("kind") != "polygon":
        return []
    issues: list[dict[str, Any]] = []
    if "holes" in profile:
        issues.append(
            _issue(
                "PACKAGE_PROFILE_HOLES_UNSUPPORTED",
                f"/{component_id}/attributes/Representation/profile/holes",
                component_id,
            )
        )
    points = profile.get("points")
    if isinstance(points, list) and points and points[0] != points[-1]:
        issues.append(
            _issue(
                "PACKAGE_POLYGON_PROFILE_OPEN",
                f"/{component_id}/attributes/Representation/profile/points",
                component_id,
            )
        )
    return issues


def _component_references(value: Mapping[str, Any]) -> list[tuple[str, str]]:
    attributes = value.get("attributes")
    if not isinstance(attributes, Mapping):
        return []
    refs: list[tuple[str, str]] = []
    for key, child in attributes.items():
        if key in _REFERENCE_FIELDS:
            refs.extend(_reference_values(child, f"/attributes/{key}"))
    return refs


def _reference_values(value: Any, path: str) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        return [item for index, child in enumerate(value) for item in _reference_values(child, f"{path}/{index}")]
    if isinstance(value, Mapping):
        return [item for key, child in value.items() for item in _reference_values(child, f"{path}/{key}")]
    return []


def _containment_map(relationships: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relationship in relationships:
        if relationship.get("ifc_class") != "IfcRelContainedInSpatialStructure":
            continue
        attributes = relationship.get("attributes", {})
        if not isinstance(attributes, Mapping):
            continue
        storey_id = attributes.get("RelatingStructure")
        related = attributes.get("RelatedElements", [])
        if isinstance(storey_id, str) and isinstance(related, list):
            for component_id in related:
                if isinstance(component_id, str):
                    result[component_id] = storey_id
    return result


def _find_package(manifest: Mapping[str, Any], package_id: str) -> dict[str, Any] | None:
    return next((package for package in _records(manifest.get("packages")) if package.get("package_id") == package_id), None)


def _components(workspace: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for collection in ("entities", "relationships"):
        for component in _records(workspace.get(collection)):
            component_id = component.get("id")
            if isinstance(component_id, str):
                result[component_id] = component
    return result


def _records(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _issue(
    code: str,
    path: str,
    component_id: str,
    related_component_id: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    payload = {"code": code, "path": path, "component_id": component_id}
    if related_component_id is not None:
        payload["related_component_id"] = related_component_id
    if message is not None:
        payload["message"] = message
    return payload


def _result(issues: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    unique = {
        (str(issue.get("code")), str(issue.get("path")), str(issue.get("component_id")), str(issue.get("related_component_id"))): dict(issue)
        for issue in issues
    }
    ordered = [unique[key] for key in sorted(unique)]
    return {"valid": not ordered, "issues": ordered}
