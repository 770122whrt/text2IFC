"""Registry-backed BIM JSON 2.0 structural and semantic validation."""

from __future__ import annotations

import re
from numbers import Number
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_knowledge.registry import load_ifc2x3_registry

from .capabilities import load_capabilities
from .geometry_v2 import validate_geometry
from .placement import validate_placement_graph
from .relationships_v2 import validate_relationships
from .schema import load_schema_v2
from .validation import (
    ValidationIssue,
    _non_finite_number_issues,
    _normalize_error,
    _sort_issues,
)


_GLOBAL_ID = re.compile(r"^[0-9A-Za-z_$]{22}$")
_CAPABILITY_CODES = {
    "extract-only": "CLASS_NOT_GENERATABLE",
    "compiler-only": "COMPILER_ONLY_CLASS",
    "unsupported": "UNSUPPORTED_IFC_CLASS",
}


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, message=message)


def _property_type_matches(value: Any, record) -> bool:
    if record.get("enum_items"):
        return isinstance(value, str) and value in record["enum_items"]
    data_type = record.get("data_type") or record.get("reference_type")
    if data_type == "IfcBoolean":
        return isinstance(value, bool)
    if data_type in {"IfcLabel", "IfcIdentifier", "IfcText", "IfcURIReference"}:
        return isinstance(value, str)
    if data_type and ("Integer" in data_type or "Count" in data_type):
        return isinstance(value, int) and not isinstance(value, bool)
    if data_type and (
        "Measure" in data_type or data_type in {"IfcReal", "IfcNumericMeasure"}
    ):
        return isinstance(value, Number) and not isinstance(value, bool)
    return value is None or isinstance(value, (str, bool, Number, list, dict))


def _semantic_issues(document: dict[str, Any]) -> list[ValidationIssue]:
    registry = load_ifc2x3_registry()
    capabilities = load_capabilities()
    issues = _non_finite_number_issues(document)
    first_ids: dict[str, str] = {}

    for collection_name in ("entities", "relationships"):
        for index, record in enumerate(document[collection_name]):
            base = f"/{collection_name}/{index}"
            object_id = record["id"]
            if object_id in first_ids:
                issues.append(
                    _issue(
                        "DUPLICATE_ID",
                        f"{base}/id",
                        f"ID {object_id!r} is already used at {first_ids[object_id]}.",
                    )
                )
            else:
                first_ids[object_id] = f"{base}/id"

            ifc_class = record["ifc_class"]
            declaration = registry.declaration(ifc_class)
            state = capabilities.get(ifc_class)
            if declaration is None or declaration["kind"] != "entity":
                issues.append(
                    _issue(
                        "UNKNOWN_IFC_CLASS",
                        f"{base}/ifc_class",
                        f"{ifc_class!r} is not an IFC2X3 entity.",
                    )
                )
                continue
            expected_root = (
                "IfcRelationship" if collection_name == "relationships" else None
            )
            if expected_root and expected_root not in declaration["supertypes"]:
                issues.append(
                    _issue(
                        "INVALID_RELATIONSHIP_CLASS",
                        f"{base}/ifc_class",
                        f"{ifc_class!r} is not an IFC relationship.",
                    )
                )
            if not expected_root and (
                ifc_class == "IfcRelationship"
                or "IfcRelationship" in declaration["supertypes"]
            ):
                issues.append(
                    _issue(
                        "INVALID_ENTITY_CLASS",
                        f"{base}/ifc_class",
                        f"{ifc_class!r} belongs in relationships.",
                    )
                )
            if state != "generate" and collection_name != "relationships":
                issues.append(
                    _issue(
                        _CAPABILITY_CODES[state],
                        f"{base}/ifc_class",
                        f"{ifc_class!r} capability is {state}.",
                    )
                )

            global_id = record.get("global_id")
            if global_id is not None and (
                not isinstance(global_id, str) or not _GLOBAL_ID.fullmatch(global_id)
            ):
                issues.append(
                    _issue(
                        "INVALID_GLOBAL_ID",
                        f"{base}/global_id",
                        "GlobalId must be a 22-character compressed IFC identifier.",
                    )
                )

            allowed_attributes = {
                attribute["name"] for attribute in declaration["attributes"]
            }
            for name in record["attributes"]:
                if name not in allowed_attributes:
                    issues.append(
                        _issue(
                            "INVALID_IFC_ATTRIBUTE",
                            f"{base}/attributes/{name}",
                            f"{name!r} is not available on {ifc_class}.",
                        )
                    )

            for pset_name, values in record.get("property_sets", {}).items():
                pset_path = f"{base}/property_sets/{pset_name}"
                pset = registry.property_set(pset_name)
                if pset is None:
                    if not pset_name.startswith("custom:"):
                        issues.append(
                            _issue(
                                "UNNAMESPACED_CUSTOM_PROPERTY_SET",
                                pset_path,
                                "Custom property sets must use the custom: namespace.",
                            )
                        )
                    continue
                applicable = set(pset["applicable_classes"])
                lineage = {ifc_class, *declaration["supertypes"]}
                if applicable and not applicable.intersection(lineage):
                    issues.append(
                        _issue(
                            "PROPERTY_SET_NOT_APPLICABLE",
                            pset_path,
                            f"{pset_name} is not applicable to {ifc_class}.",
                        )
                    )
                for property_name, value in values.items():
                    property_path = f"{pset_path}/{property_name}"
                    property_record = pset["properties"].get(property_name)
                    if property_record is None:
                        issues.append(
                            _issue(
                                "UNKNOWN_STANDARD_PROPERTY",
                                property_path,
                                f"{property_name!r} is not declared by {pset_name}.",
                            )
                        )
                    elif not _property_type_matches(value, property_record):
                        issues.append(
                            _issue(
                                "INVALID_PROPERTY_TYPE",
                                property_path,
                                f"{property_name!r} has an invalid IFC value type.",
                            )
                        )
    issues.extend(validate_placement_graph(document))
    issues.extend(validate_geometry(document))
    issues.extend(validate_relationships(document))
    return _sort_issues(issues)


def validate_v2_document(document: Any) -> list[ValidationIssue]:
    validator = Draft202012Validator(load_schema_v2())
    structural = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    structural = _sort_issues(structural)
    if structural:
        return structural
    return _semantic_issues(document)
