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
    "IfcRelDefinesByType": {
        "RelatedObjects": "IfcObject",
        "RelatingType": "IfcTypeObject",
    },
    "IfcRelAggregates": {
        "RelatingObject": "IfcObjectDefinition",
        "RelatedObjects": "IfcObjectDefinition",
    },
    "IfcRelConnectsPathElements": {
        "RelatingElement": "IfcElement",
        "RelatedElement": "IfcElement",
    },
}
CONNECTION_TYPES = {"ATPATH", "ATSTART", "ATEND", "NOTDEFINED"}


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
                    "This IFC relationship is not explicit in the formal profile.",
                )
            )
            continue
        attributes = relation["attributes"]
        if ifc_class == "IfcRelConnectsPathElements":
            issues.extend(_validate_path_connection_attributes(base, attributes))
        for attribute, expected_class in endpoint_types.items():
            path = f"{base}/attributes/{attribute}"
            endpoint_id = attributes.get(attribute)
            if attribute == "RelatedObjects":
                if (
                    not isinstance(endpoint_id, list)
                    or not endpoint_id
                    or not all(isinstance(item, str) for item in endpoint_id)
                ):
                    issues.append(
                        _issue(
                            "RELATIONSHIP_ENDPOINT_SHAPE",
                            path,
                            "RelatedObjects must be a non-empty list of entity IDs.",
                        )
                    )
                    continue
                endpoint_ids = endpoint_id
            elif not isinstance(endpoint_id, str):
                issues.append(
                    _issue(
                        "RELATIONSHIP_ENDPOINT_SHAPE",
                        path,
                        f"{attribute} must be a single entity ID.",
                    )
                )
                continue
            else:
                endpoint_ids = [endpoint_id]
            for item_id in endpoint_ids:
                if not isinstance(item_id, str) or item_id not in entities:
                    issues.append(
                        _issue(
                            "UNRESOLVED_RELATIONSHIP_ENDPOINT",
                            path,
                            f"Relationship endpoint {item_id!r} is not declared.",
                        )
                    )
                    continue
                actual_class = entities[item_id]["ifc_class"]
                if not _matches_class(actual_class, expected_class, registry):
                    issues.append(
                        _issue(
                            "RELATIONSHIP_ENDPOINT_TYPE_MISMATCH",
                            path,
                            (
                                f"{attribute} requires {expected_class}, "
                                f"but {item_id!r} is {actual_class}."
                            ),
                        )
                    )

    return issues


def _validate_path_connection_attributes(
    base: str,
    attributes: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for name in ("RelatingPriorities", "RelatedPriorities"):
        value = attributes.get(name)
        if not isinstance(value, list) or not all(
            isinstance(item, int) and not isinstance(item, bool) for item in value
        ):
            issues.append(
                _issue(
                    "RELATIONSHIP_ATTRIBUTE_SHAPE",
                    f"{base}/attributes/{name}",
                    f"{name} must be a list of integer priorities.",
                )
            )
    for name in ("RelatingConnectionType", "RelatedConnectionType"):
        value = attributes.get(name)
        if value not in CONNECTION_TYPES:
            issues.append(
                _issue(
                    "RELATIONSHIP_ATTRIBUTE_VALUE",
                    f"{base}/attributes/{name}",
                    f"{name} must be an IfcConnectionTypeEnum value.",
                )
            )
    if attributes.get("ConnectionGeometry") is not None:
        issues.append(
            _issue(
                "UNSUPPORTED_RELATIONSHIP_ATTRIBUTE",
                f"{base}/attributes/ConnectionGeometry",
                "ConnectionGeometry is not supported in the formal profile.",
            )
        )
    return issues
