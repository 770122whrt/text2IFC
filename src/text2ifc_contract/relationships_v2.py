"""Registry-backed semantic endpoint validation for explicit relationships."""

from __future__ import annotations

from typing import Any

from text2ifc_knowledge.registry import load_ifc2x3_registry

from .validation import ValidationIssue


SUPPORTED_RELATIONSHIPS = {
    "IfcRelVoidsElement": {
        "RelatingBuildingElement": "IfcElement",
        "RelatedOpeningElement": "IfcOpeningElement",
    },
    "IfcRelFillsElement": {
        "RelatingOpeningElement": "IfcOpeningElement",
        "RelatedBuildingElement": "IfcElement",
    },
}


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, message=message)


def _matches_class(ifc_class: str, expected: str, registry) -> bool:
    declaration = registry.declaration(ifc_class)
    return declaration is not None and (
        ifc_class == expected or expected in declaration["supertypes"]
    )


def validate_relationships(
    document: dict[str, Any],
) -> list[ValidationIssue]:
    registry = load_ifc2x3_registry()
    entities = {
        record["id"]: record
        for record in document.get("entities", [])
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    issues: list[ValidationIssue] = []

    for index, relation in enumerate(document.get("relationships", [])):
        ifc_class = relation["ifc_class"]
        base = f"/relationships/{index}"
        endpoint_types = SUPPORTED_RELATIONSHIPS.get(ifc_class)
        if endpoint_types is None:
            issues.append(
                _issue(
                    "UNSUPPORTED_RELATIONSHIP_CLASS",
                    f"{base}/ifc_class",
                    (
                        "Only IfcRelVoidsElement and IfcRelFillsElement are "
                        "explicit formal relationships."
                    ),
                )
            )
            continue
        attributes = relation["attributes"]
        for attribute, expected_class in endpoint_types.items():
            path = f"{base}/attributes/{attribute}"
            endpoint_id = attributes.get(attribute)
            if not isinstance(endpoint_id, str) or endpoint_id not in entities:
                issues.append(
                    _issue(
                        "UNRESOLVED_RELATIONSHIP_ENDPOINT",
                        path,
                        f"Relationship endpoint {endpoint_id!r} is not declared.",
                    )
                )
                continue
            actual_class = entities[endpoint_id]["ifc_class"]
            if not _matches_class(actual_class, expected_class, registry):
                issues.append(
                    _issue(
                        "RELATIONSHIP_ENDPOINT_TYPE_MISMATCH",
                        path,
                        (
                            f"{attribute} requires {expected_class}, "
                            f"but {endpoint_id!r} is {actual_class}."
                        ),
                    )
                )

    return issues
