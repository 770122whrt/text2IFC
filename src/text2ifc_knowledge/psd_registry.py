"""Generate standard property metadata from official IFC2X3 PSD XML."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from lxml import etree

from .sources import ArchiveSafetyError, inspect_zip_archive


class PsdParseError(ValueError):
    pass


def _local_name(element) -> str:
    return etree.QName(element).localname


def _direct_child(element, name: str):
    for child in element:
        if _local_name(child) == name:
            return child
    return None


def _direct_text(element, name: str) -> str | None:
    child = _direct_child(element, name)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _descendants(element, name: str):
    return [item for item in element.iter() if _local_name(item) == name]


def _property_record(property_def) -> dict[str, Any]:
    property_type = _direct_child(property_def, "PropertyType")
    if property_type is None or not len(property_type):
        raise PsdParseError("PropertyDef has no PropertyType")
    type_node = property_type[0]
    template_type = _local_name(type_node)
    data_types = []
    if template_type != "TypeComplexProperty":
        data_types = [
            item.get("type")
            for item in _descendants(type_node, "DataType")
            if item.get("type")
        ]
    reference_type = type_node.get("reftype")
    units = sorted(
        {
            value
            for item in _descendants(type_node, "UnitType")
            if (value := item.get("type"))
        }
    )
    enum_items = [
        item.text.strip()
        for item in _descendants(type_node, "EnumItem")
        if item.text and item.text.strip()
    ]
    record: dict[str, Any] = {
        "template_type": template_type,
        "data_type": data_types[0] if data_types else None,
    }
    if len(data_types) > 1:
        record["data_types"] = data_types
    if reference_type:
        record["reference_type"] = reference_type
    if enum_items:
        record["enum_items"] = enum_items
    if units:
        record["unit_types"] = units
    if template_type == "TypeComplexProperty":
        record["complex_name"] = type_node.get("name")
        nested: dict[str, dict[str, Any]] = {}
        for nested_def in type_node:
            if _local_name(nested_def) != "PropertyDef":
                continue
            nested_name = _direct_text(nested_def, "Name")
            if not nested_name:
                raise PsdParseError("complex property contains an unnamed child")
            if nested_name in nested:
                raise PsdParseError(
                    f"complex property contains duplicate child {nested_name!r}"
                )
            nested[nested_name] = _property_record(nested_def)
        record["properties"] = dict(sorted(nested.items()))
    return record


def _parse_property_set(xml_bytes: bytes, source_path: str) -> tuple[str, dict[str, Any]]:
    upper = xml_bytes.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise PsdParseError(f"DTD or entity declaration in {source_path}")
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        huge_tree=False,
        recover=False,
    )
    try:
        root = etree.fromstring(xml_bytes, parser=parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise PsdParseError(f"invalid PSD XML {source_path}: {exc}") from exc

    name = _direct_text(root, "Name")
    if not name:
        raise PsdParseError(f"property set has no Name: {source_path}")
    applicable = _direct_child(root, "ApplicableClasses")
    applicable_classes = []
    if applicable is not None:
        applicable_classes = sorted(
            {
                item.text.strip()
                for item in _descendants(applicable, "ClassName")
                if item.text and item.text.strip()
            }
        )

    property_defs = _direct_child(root, "PropertyDefs")
    properties: dict[str, dict[str, Any]] = {}
    if property_defs is not None:
        for property_def in property_defs:
            if _local_name(property_def) != "PropertyDef":
                continue
            property_name = _direct_text(property_def, "Name")
            if not property_name:
                raise PsdParseError(f"unnamed property in {source_path}")
            if property_name in properties:
                raise PsdParseError(
                    f"duplicate property {property_name!r} in {source_path}"
                )
            properties[property_name] = _property_record(property_def)

    return name, {
        "name": name,
        "applicable_classes": applicable_classes,
        "properties": dict(sorted(properties.items())),
        "source_path": source_path,
    }


def build_property_registry(archive_path: str | Path) -> dict[str, Any]:
    try:
        members = inspect_zip_archive(archive_path)
    except ArchiveSafetyError as exc:
        raise PsdParseError(str(exc)) from exc

    psd_names = sorted(
        member.name
        for member in members
        if "/psd/" in member.name.lower() and member.name.lower().endswith(".xml")
    )
    property_sets: dict[str, dict[str, Any]] = {}
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for source_path in psd_names:
                name, record = _parse_property_set(
                    archive.read(source_path),
                    source_path,
                )
                if name in property_sets:
                    raise PsdParseError(f"duplicate property set: {name!r}")
                property_sets[name] = record
    except PsdParseError:
        raise
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise PsdParseError(f"cannot read PSD archive: {exc}") from exc

    property_definition_count = sum(
        len(record["properties"]) for record in property_sets.values()
    )
    complex_count = 0
    simple_count = 0

    def count_record(record: dict[str, Any]) -> None:
        nonlocal complex_count, simple_count
        if record["template_type"] == "TypeComplexProperty":
            complex_count += 1
            for nested in record.get("properties", {}).values():
                count_record(nested)
        else:
            simple_count += 1

    for property_set in property_sets.values():
        for property_record in property_set["properties"].values():
            count_record(property_record)

    return {
        "schema": "IFC2X3",
        "counts": {
            "property_sets": len(property_sets),
            "property_definitions": property_definition_count,
            "complex_properties": complex_count,
            "simple_properties": simple_count,
        },
        "property_sets": dict(sorted(property_sets.items())),
    }
