from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.element

from .index_adapters import IndexAdapterRegistry, default_index_adapter_registry
from .index_models import (
    AliasFact,
    ElementRecord,
    IndexDiagnostic,
    IndexMetadata,
    PropertyFact,
    RelationshipFact,
)
from .index_store import SQLiteIndexRepository


EXTRACTOR_VERSION = "text2ifc/ifc-indexer/0.1"
_IFC_GUID = re.compile(r"^[0-9A-Za-z_$]{22}$")


class IndexBuildError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def build_ifc_index(
    source_path: str | Path,
    database_path: str | Path,
    *,
    registry: IndexAdapterRegistry | None = None,
) -> IndexMetadata:
    source = Path(source_path)
    try:
        model = ifcopenshell.open(str(source))
    except Exception as error:
        raise IndexBuildError("INVALID_IFC", f"Unable to parse IFC: {error}") from error
    if model.schema != "IFC2X3":
        raise IndexBuildError(
            "UNSUPPORTED_IFC_SCHEMA", f"Expected IFC2X3, received {model.schema}"
        )

    active_registry = registry or default_index_adapter_registry()
    entities = _registered_entities(model, active_registry)
    global_ids = [str(getattr(entity, "GlobalId", "") or "") for entity in entities]
    duplicate_ids = {
        global_id for global_id, count in Counter(global_ids).items() if global_id and count > 1
    }
    metadata = IndexMetadata(
        source_ifc_sha256="sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
        ifc_schema=model.schema,
        extractor_version=EXTRACTOR_VERSION,
        source_size_bytes=source.stat().st_size,
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    with SQLiteIndexRepository.create(database_path, metadata) as repository:
        for entity in entities:
            adapter = active_registry.adapter_for(entity)
            assert adapter is not None
            global_id = str(getattr(entity, "GlobalId", "") or "")
            identity_reliable = bool(_IFC_GUID.fullmatch(global_id)) and global_id not in duplicate_ids
            record_id = f"ifc:{global_id}" if identity_reliable else f"diagnostic:{entity.id()}"
            result = adapter.extract(entity)
            type_entity = _element_type(entity)
            storey = _element_storey(entity)
            relationships = list(result.relationships)
            if storey is not None and getattr(storey, "GlobalId", None):
                relationships.append(
                    RelationshipFact(
                        "contained_in_storey",
                        str(storey.GlobalId),
                        _storey_provenance(entity),
                    )
                )
            record = ElementRecord(
                record_id=record_id,
                ifc_global_id=global_id or None,
                identity_reliable=identity_reliable,
                ifc_class=entity.is_a(),
                name=_text(getattr(entity, "Name", None)),
                long_name=_text(getattr(entity, "LongName", None)),
                tag=_text(getattr(entity, "Tag", None)),
                object_type=_text(getattr(entity, "ObjectType", None)),
                type_name=_text(getattr(type_entity, "Name", None)),
                type_global_id=_text(getattr(type_entity, "GlobalId", None)),
                storey_name=_text(getattr(storey, "Name", None)),
                storey_global_id=_text(getattr(storey, "GlobalId", None)),
                geometry_capability=result.geometry_capability,
                geometry_summary=_json_safe(result.geometry_summary),
                facets=_json_safe(result.facets),
                provenance={"source": "current_ifc", "step_id": entity.id()},
                aliases=_aliases(entity, type_entity, storey),
                relationships=tuple(
                    sorted(relationships, key=lambda fact: (fact.kind, fact.target_global_id, fact.provenance))
                ),
                properties=_properties(entity),
            )
            repository.put_record(record)
            if not identity_reliable:
                code = "DUPLICATE_IFC_GLOBAL_ID" if global_id in duplicate_ids else "UNRELIABLE_IFC_GLOBAL_ID"
                repository.put_diagnostic(
                    IndexDiagnostic(
                        code=code,
                        severity="error",
                        message="IFC identity cannot be used as a mutation binding",
                        record_id=record_id,
                        ifc_global_id=global_id or None,
                        step_id=entity.id(),
                        evidence={"ifc_class": entity.is_a()},
                    )
                )
            for code, message, evidence in result.warnings:
                repository.put_diagnostic(
                    IndexDiagnostic(
                        code=code,
                        severity="warning",
                        message=message,
                        record_id=record_id,
                        ifc_global_id=global_id or None,
                        step_id=entity.id(),
                        evidence=_json_safe(evidence),
                    )
                )
        repository.publish()
    return metadata


def _registered_entities(model: Any, registry: IndexAdapterRegistry) -> list[Any]:
    unique: dict[int, Any] = {}
    for ifc_class in registry.ifc_classes:
        for entity in model.by_type(ifc_class):
            unique[entity.id()] = entity
    return [unique[step_id] for step_id in sorted(unique)]


def _element_type(entity: Any) -> Any | None:
    try:
        return ifcopenshell.util.element.get_type(entity)
    except Exception:
        return None


def _element_storey(entity: Any) -> Any | None:
    for relation in getattr(entity, "ContainedInStructure", ()):
        structure = relation.RelatingStructure
        if structure.is_a("IfcBuildingStorey"):
            return structure
    if entity.is_a("IfcSpace"):
        for relation in getattr(entity, "Decomposes", ()):
            parent = relation.RelatingObject
            if parent.is_a("IfcBuildingStorey"):
                return parent
    for fill in getattr(entity, "FillsVoids", ()):
        opening = fill.RelatingOpeningElement
        for void in getattr(opening, "VoidsElements", ()):
            host_storey = _element_storey(void.RelatingBuildingElement)
            if host_storey is not None:
                return host_storey
    return None


def _storey_provenance(entity: Any) -> str:
    if entity.is_a("IfcSpace"):
        return "IfcRelAggregates"
    if getattr(entity, "ContainedInStructure", ()):
        return "IfcRelContainedInSpatialStructure"
    return "hosted_element_traversal"


def _aliases(entity: Any, type_entity: Any | None, storey: Any | None) -> tuple[AliasFact, ...]:
    values = (
        ("name", getattr(entity, "Name", None), "IfcRoot.Name"),
        ("long_name", getattr(entity, "LongName", None), "IfcSpatialStructureElement.LongName"),
        ("tag", getattr(entity, "Tag", None), "IfcElement.Tag"),
        ("object_type", getattr(entity, "ObjectType", None), "IfcObject.ObjectType"),
        ("type_name", getattr(type_entity, "Name", None), "IfcTypeObject.Name"),
        ("storey_name", getattr(storey, "Name", None), "IfcBuildingStorey.Name"),
    )
    facts: dict[tuple[str, str], AliasFact] = {}
    for field, value, provenance in values:
        original = _text(value)
        if not original:
            continue
        normalized = normalize_alias(original)
        facts[(field, normalized)] = AliasFact(normalized, original, field, provenance)
    return tuple(facts[key] for key in sorted(facts))


def normalize_alias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[_:/\\|]+", " ", normalized)
    return " ".join(normalized.split())


def _properties(entity: Any) -> tuple[PropertyFact, ...]:
    try:
        sets = ifcopenshell.util.element.get_psets(
            entity, psets_only=False, qtos_only=False, should_inherit=True, verbose=True
        )
    except Exception:
        return ()
    facts: list[PropertyFact] = []
    for set_name, members in sets.items():
        if not isinstance(members, dict):
            continue
        for property_name, payload in members.items():
            if property_name == "id" or not isinstance(payload, dict) or "value" not in payload:
                continue
            property_class = str(payload.get("class") or "")
            facts.append(
                PropertyFact(
                    set_kind="quantity" if property_class.startswith("IfcQuantity") else "pset",
                    set_name=str(set_name),
                    property_name=str(property_name),
                    value=_json_safe(payload.get("value")),
                    value_type=_text(payload.get("value_type") or property_class),
                    unit=_text(payload.get("unit")),
                    inherited=True,
                    provenance="ifcopenshell.util.element.get_psets",
                )
            )
    return tuple(
        sorted(facts, key=lambda fact: (fact.set_kind, fact.set_name, fact.property_name, repr(fact.value)))
    )


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "is_a"):
        return {"ifc_class": value.is_a(), "step_id": value.id()}
    return str(value)


def _text(value: Any) -> str | None:
    return None if value is None else str(value)


__all__ = ["EXTRACTOR_VERSION", "IndexBuildError", "build_ifc_index", "normalize_alias"]
