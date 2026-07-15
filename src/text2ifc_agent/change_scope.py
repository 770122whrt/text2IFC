"""Derive bounded ChangeSet targets from stable evidence and IFC relations."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.revisions import validate_change_scope


_COMPONENT_REF = re.compile(
    r"^(?P<kind>entity|relationship):(?P<id>[A-Za-z][A-Za-z0-9._:-]*)#(?P<path>/.*)$"
)
_TRAVERSABLE_RELATIONSHIPS = {
    "IfcRelVoidsElement",
    "IfcRelFillsElement",
    "IfcRelAggregates",
    "IfcRelSpaceBoundary",
}
_CONTAINMENT = "IfcRelContainedInSpatialStructure"


def derive_change_scope(
    *,
    candidate: Mapping[str, Any],
    issues: Sequence[Mapping[str, Any] | Any],
    scope_id: str,
    base_revision_id: str,
    dependency_hints: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return one validated scope or explicit unresolved-target issues."""

    index = build_candidate_index(candidate)
    entities = index["entities"]
    relationships = index["relationships"]
    all_ids = set(entities) | set(relationships)
    allowed_entities: set[str] = set()
    allowed_relationships: set[str] = set()
    allowed_paths: dict[str, set[str]] = {}
    dependencies: list[dict[str, str]] = []
    diagnostics: list[dict[str, str]] = []
    source_issue_ids: list[str] = []

    for issue in issues:
        issue_id = str(_value(issue, "issue_id") or "")
        if issue_id:
            source_issue_ids.append(issue_id)
        reference = _value(issue, "actual_ref")
        match = _COMPONENT_REF.fullmatch(str(reference or ""))
        if match is None:
            diagnostics.append(
                _diagnostic(
                    "CHANGESET_TARGET_UNRESOLVED",
                    issue_id,
                    f"Issue reference {reference!r} does not identify a stable component.",
                )
            )
            continue
        component_id = match.group("id")
        kind = match.group("kind")
        collection = entities if kind == "entity" else relationships
        if component_id not in collection:
            diagnostics.append(
                _diagnostic(
                    "CHANGESET_TARGET_UNRESOLVED",
                    issue_id,
                    f"Issue references unknown {kind} {component_id!r}.",
                )
            )
            continue
        _allow(kind, component_id, allowed_entities, allowed_relationships)
        allowed_paths.setdefault(component_id, set()).add(match.group("path"))

    for hint in dependency_hints or []:
        target_id = str(hint.get("target_id", ""))
        dependency_id = str(hint.get("dependency_id", ""))
        if target_id not in all_ids or dependency_id not in all_ids:
            diagnostics.append(
                _diagnostic(
                    "CHANGESET_DEPENDENCY_UNRESOLVED",
                    target_id or dependency_id,
                    "Dependency hint endpoints must both identify existing components.",
                )
            )
            continue
        _allow_component_id(
            dependency_id,
            entities,
            allowed_entities,
            allowed_relationships,
        )
        for path in hint.get("allowed_paths", []):
            allowed_paths.setdefault(dependency_id, set()).add(str(path))
        dependencies.append(
            {
                "target_id": target_id,
                "dependency_id": dependency_id,
                "relationship_type": str(hint.get("relationship_type", "dependency")),
                "reason": str(hint.get("reason", "Explicit expected-fact dependency.")),
            }
        )

    if diagnostics:
        return {"scope": None, "issues": _sorted_diagnostics(diagnostics)}

    changed = True
    while changed:
        changed = False
        for relationship_id, relationship in sorted(relationships.items()):
            if relationship_id in allowed_relationships:
                continue
            ifc_class = str(relationship.get("ifc_class", ""))
            attributes = relationship.get("attributes", {})
            if not isinstance(attributes, Mapping):
                continue
            current_entities = set(allowed_entities)
            if ifc_class == _CONTAINMENT:
                related = _string_ids(attributes.get("RelatedElements"), entities)
                if not (related & current_entities):
                    continue
                referenced = _string_ids(attributes.get("RelatingStructure"), entities)
            elif ifc_class in _TRAVERSABLE_RELATIONSHIPS:
                referenced = _string_ids(attributes, entities)
                if not (referenced & current_entities):
                    continue
            else:
                continue

            allowed_relationships.add(relationship_id)
            allowed_paths.setdefault(relationship_id, set()).add("/attributes")
            anchor = sorted(referenced & current_entities)[0] if referenced & current_entities else sorted(current_entities)[0]
            dependencies.append(
                {
                    "target_id": anchor,
                    "dependency_id": relationship_id,
                    "relationship_type": ifc_class,
                    "reason": f"{ifc_class} references an allowed component.",
                }
            )
            changed = True
            for entity_id in sorted(referenced - allowed_entities):
                allowed_entities.add(entity_id)
                dependencies.append(
                    {
                        "target_id": relationship_id,
                        "dependency_id": entity_id,
                        "relationship_type": ifc_class,
                        "reason": f"{entity_id} is an endpoint of {relationship_id}.",
                    }
                )

    allowed = allowed_entities | allowed_relationships
    scope = {
        "schema_version": "text2ifc/change-scope/1.0",
        "scope_id": scope_id,
        "base_revision_id": base_revision_id,
        "source_issue_ids": sorted(set(source_issue_ids)),
        "entity_ids": sorted(allowed_entities),
        "relationship_ids": sorted(allowed_relationships),
        "allowed_paths": {
            component_id: sorted(paths)
            for component_id, paths in sorted(allowed_paths.items())
        },
        "dependencies": _unique_dependencies(dependencies),
        "forbidden_ids": sorted(all_ids - allowed),
    }
    contract_issues = validate_change_scope(scope)
    if contract_issues:
        return {
            "scope": None,
            "issues": [
                {"code": issue.code, "path": issue.path, "message": issue.message}
                for issue in contract_issues
            ],
        }
    return {"scope": scope, "issues": []}


def _allow(
    kind: str,
    component_id: str,
    entities: set[str],
    relationships: set[str],
) -> None:
    (entities if kind == "entity" else relationships).add(component_id)


def _allow_component_id(
    component_id: str,
    entities_by_id: Mapping[str, Any],
    entities: set[str],
    relationships: set[str],
) -> None:
    (entities if component_id in entities_by_id else relationships).add(component_id)


def _string_ids(value: Any, entities: Mapping[str, Any]) -> set[str]:
    if isinstance(value, str):
        return {value} if value in entities else set()
    if isinstance(value, Mapping):
        return {
            item
            for child in value.values()
            for item in _string_ids(child, entities)
        }
    if isinstance(value, list):
        return {item for child in value for item in _string_ids(child, entities)}
    return set()


def _value(issue: Mapping[str, Any] | Any, key: str) -> Any:
    return issue.get(key) if isinstance(issue, Mapping) else getattr(issue, key, None)


def _diagnostic(code: str, reference: str, message: str) -> dict[str, str]:
    return {"code": code, "path": reference or "/", "message": message}


def _sorted_diagnostics(values: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    return [dict(value) for value in sorted(values, key=lambda item: (item["code"], item["path"]))]


def _unique_dependencies(values: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    unique = {
        (
            value["target_id"],
            value["dependency_id"],
            value["relationship_type"],
            value["reason"],
        ): dict(value)
        for value in values
    }
    return [unique[key] for key in sorted(unique)]
