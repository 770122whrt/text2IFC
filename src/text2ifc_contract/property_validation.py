"""Shared IFC2X3 property identity, applicability and value checks."""
from numbers import Number
from typing import Any
from text2ifc_contract.validation import ValidationIssue
from text2ifc_knowledge.registry import load_ifc2x3_registry

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


def validate_property_sets(ifc_class, property_sets, *, path, extended=True, registry=None):
    registry = registry or load_ifc2x3_registry()
    declaration = registry.declaration(ifc_class)
    if declaration is None:
        return [ValidationIssue('UNKNOWN_IFC_CLASS', path, 'Property target requires a known IFC class.')]
    issues = []
    for pset_name, values in property_sets.items():
        pset_path = f"{path}/{pset_name}"
        pset = registry.property_set(pset_name)
        if pset is None:
            if not pset_name.startswith("custom:"):
                issues.append(
                    ValidationIssue(
                        "UNNAMESPACED_CUSTOM_PROPERTY_SET",
                        pset_path,
                        "Custom property sets must use the custom: namespace.",
                    )
                )
            continue
        applicable = set(pset["applicable_classes"])
        lineage = {ifc_class, *declaration["supertypes"]}
        if extended:
            from .materials import TYPE_OCCURRENCE
            occurrence = TYPE_OCCURRENCE.get(ifc_class)
            if occurrence:
                lineage.update({occurrence, *registry.declaration(occurrence)["supertypes"]})
        if applicable and not applicable.intersection(lineage):
            issues.append(
                ValidationIssue(
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
                    ValidationIssue(
                        "UNKNOWN_STANDARD_PROPERTY",
                        property_path,
                        f"{property_name!r} is not declared by {pset_name}.",
                    )
                )
            elif not _property_type_matches(value, property_record):
                issues.append(
                    ValidationIssue(
                        "INVALID_PROPERTY_TYPE",
                        property_path,
                        f"{property_name!r} has an invalid IFC value type.",
                    )
                )
    return issues
