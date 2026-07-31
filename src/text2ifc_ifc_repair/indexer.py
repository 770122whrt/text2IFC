from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.classification
import ifcopenshell.util.element
import ifcopenshell.util.unit

from .index_adapters import IndexAdapterRegistry, default_index_adapter_registry
from .index_models import (
    AliasFact,
    AssociationFact,
    ElementRecord,
    IndexDiagnostic,
    IndexMetadata,
    PropertyFact,
    RelationshipFact,
    TypeRecord,
)
from .index_store import SQLiteIndexRepository
from .semantic_facts import extract_property_facts
from .spatial import resolve_opening_storey


EXTRACTOR_VERSION = "text2ifc/ifc-indexer/0.4"
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
    type_entities = _indexed_types(model, entities)
    type_global_ids = [str(getattr(entity, "GlobalId", "") or "") for entity in type_entities]
    duplicate_type_ids = {
        global_id
        for global_id, count in Counter(type_global_ids).items()
        if global_id and count > 1
    }
    metadata = IndexMetadata(
        source_ifc_sha256="sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
        ifc_schema=model.schema,
        extractor_version=EXTRACTOR_VERSION,
        source_size_bytes=source.stat().st_size,
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    with SQLiteIndexRepository.create(database_path, metadata) as repository:
        for type_entity in type_entities:
            global_id = str(getattr(type_entity, "GlobalId", "") or "")
            identity_reliable = (
                bool(_IFC_GUID.fullmatch(global_id))
                and global_id not in duplicate_type_ids
            )
            record_id = (
                f"type:{global_id}"
                if identity_reliable
                else f"diagnostic:type:{type_entity.id()}"
            )
            repository.put_type_record(
                TypeRecord(
                    record_id=record_id,
                    ifc_global_id=global_id or None,
                    identity_reliable=identity_reliable,
                    ifc_class=type_entity.is_a(),
                    name=_text(getattr(type_entity, "Name", None)),
                    applicable_occurrence=_text(
                        getattr(type_entity, "ApplicableOccurrence", None)
                    ),
                    predefined_type=_text(getattr(type_entity, "PredefinedType", None)),
                    element_type=_text(getattr(type_entity, "ElementType", None)),
                    formal_attributes=_type_formal_attributes(type_entity),
                    representation_summary=_type_representation_summary(type_entity),
                    provenance={"source": "current_ifc", "step_id": type_entity.id()},
                    aliases=_type_aliases(type_entity),
                    properties=_properties(type_entity, should_inherit=False),
                    associations=_direct_associations(
                        type_entity,
                        occurrence_global_id=None,
                        occurrence_type_global_id=global_id or None,
                        inherited=False,
                    ),
                )
            )
            if not identity_reliable:
                code = (
                    "DUPLICATE_IFC_TYPE_GLOBAL_ID"
                    if global_id in duplicate_type_ids
                    else "UNRELIABLE_IFC_TYPE_GLOBAL_ID"
                )
                repository.put_diagnostic(
                    IndexDiagnostic(
                        code=code,
                        severity="error",
                        message="IFC Type identity cannot be used as semantic authority",
                        record_id=record_id,
                        ifc_global_id=global_id or None,
                        step_id=type_entity.id(),
                        evidence={"ifc_class": type_entity.is_a()},
                    )
                )
        for entity in entities:
            adapter = active_registry.adapter_for(entity)
            assert adapter is not None
            global_id = str(getattr(entity, "GlobalId", "") or "")
            identity_reliable = bool(_IFC_GUID.fullmatch(global_id)) and global_id not in duplicate_ids
            record_id = f"ifc:{global_id}" if identity_reliable else f"diagnostic:{entity.id()}"
            result = adapter.extract(entity)
            type_entity = _element_type(entity)
            storey = _element_storey(entity)
            facets = dict(result.facets)
            if storey is not None and getattr(storey, "Elevation", None) is not None:
                facets["storey_elevation_mm"] = float(storey.Elevation) * (
                    ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
                )
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
                facets=_json_safe(facets),
                provenance={"source": "current_ifc", "step_id": entity.id()},
                aliases=_aliases(entity, type_entity, storey),
                relationships=tuple(
                    sorted(relationships, key=lambda fact: (fact.kind, fact.target_global_id, fact.provenance))
                ),
                properties=_properties(entity),
                associations=_element_associations(entity, type_entity),
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


def _indexed_types(model: Any, entities: list[Any]) -> list[Any]:
    unique: dict[int, Any] = {}
    for entity in entities:
        type_entity = _element_type(entity)
        if type_entity is not None:
            unique[type_entity.id()] = type_entity
    for ifc_class in ("IfcWallType", "IfcWindowStyle", "IfcDoorStyle"):
        for type_entity in model.by_type(ifc_class):
            unique[type_entity.id()] = type_entity
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
    if entity.is_a("IfcOpeningElement"):
        voids = list(getattr(entity, "VoidsElements", ()))
        if len(voids) == 1:
            try:
                return resolve_opening_storey(
                    entity, voids[0].RelatingBuildingElement
                )
            except Exception:
                return None
    for fill in getattr(entity, "FillsVoids", ()):
        opening = fill.RelatingOpeningElement
        for void in getattr(opening, "VoidsElements", ()):
            host_storey = _element_storey(void.RelatingBuildingElement)
            if host_storey is not None:
                return host_storey
    for void in getattr(entity, "VoidsElements", ()):
        host_storey = _element_storey(void.RelatingBuildingElement)
        if host_storey is not None:
            return host_storey
    return None


def _storey_provenance(entity: Any) -> str:
    if entity.is_a("IfcSpace"):
        return "IfcRelAggregates"
    if getattr(entity, "ContainedInStructure", ()):
        return "IfcRelContainedInSpatialStructure"
    if entity.is_a("IfcOpeningElement"):
        return "hosted_opening_base_elevation"
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


def _type_aliases(entity: Any) -> tuple[AliasFact, ...]:
    values = (
        ("name", getattr(entity, "Name", None), "IfcTypeObject.Name"),
        (
            "applicable_occurrence",
            getattr(entity, "ApplicableOccurrence", None),
            "IfcTypeObject.ApplicableOccurrence",
        ),
        ("element_type", getattr(entity, "ElementType", None), "IfcElementType.ElementType"),
    )
    facts: dict[tuple[str, str], AliasFact] = {}
    for field, value, provenance in values:
        original = _text(value)
        if original:
            normalized = normalize_alias(original)
            facts[(field, normalized)] = AliasFact(
                normalized, original, field, provenance
            )
    return tuple(facts[key] for key in sorted(facts))


def _type_formal_attributes(entity: Any) -> dict[str, Any]:
    if not entity.is_a("IfcDoorStyle"):
        return {}
    return {
        "OperationType": _text(getattr(entity, "OperationType", None)),
        "ConstructionType": _text(getattr(entity, "ConstructionType", None)),
        "ParameterTakesPrecedence": bool(
            getattr(entity, "ParameterTakesPrecedence", False)
        ),
        "Sizeable": bool(getattr(entity, "Sizeable", False)),
    }


def _type_representation_summary(entity: Any) -> dict[str, Any]:
    maps = tuple(getattr(entity, "RepresentationMaps", ()) or ())
    signatures = [
        {
            "mapping_origin_class": item.MappingOrigin.is_a(),
            "mapped_representation_identifier": _text(
                item.MappedRepresentation.RepresentationIdentifier
            ),
            "mapped_representation_type": _text(
                item.MappedRepresentation.RepresentationType
            ),
            "item_classes": sorted(
                child.is_a() for child in item.MappedRepresentation.Items
            )[:64],
        }
        for item in maps[:16]
    ]
    canonical = json.dumps(
        signatures, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return {
        "representation_map_count": len(maps),
        "fingerprint": "sha256:"
        + hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "maps": signatures,
        "measurement_status": "not_measured" if maps else "not_applicable",
    }


def normalize_alias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[_:/\\|]+", " ", normalized)
    return " ".join(normalized.split())


def _properties(
    entity: Any, *, should_inherit: bool = True
) -> tuple[PropertyFact, ...]:
    try:
        facts = extract_property_facts(entity, should_inherit=should_inherit)
    except Exception:
        return ()
    return tuple(
        PropertyFact(
            set_kind=fact.set_kind,
            set_name=fact.set_name,
            property_name=fact.property_name,
            value=_json_safe(fact.value),
            value_type=fact.value_type,
            unit=fact.unit,
            inherited=fact.inherited,
            provenance=fact.provenance,
        )
        for fact in facts
    )


def _element_associations(
    entity: Any, type_entity: Any | None
) -> tuple[AssociationFact, ...]:
    occurrence_global_id = _text(getattr(entity, "GlobalId", None))
    type_global_id = _text(getattr(type_entity, "GlobalId", None))
    facts = list(
        _direct_associations(
            entity,
            occurrence_global_id=occurrence_global_id,
            occurrence_type_global_id=type_global_id,
            inherited=False,
        )
    )
    if type_entity is not None:
        facts.extend(
            _direct_associations(
                type_entity,
                occurrence_global_id=occurrence_global_id,
                occurrence_type_global_id=type_global_id,
                inherited=True,
            )
        )
    unique = {
        (
            fact.association_kind,
            fact.relationship_ref,
            fact.resource_ref,
            fact.inherited,
        ): fact
        for fact in facts
    }
    return tuple(unique[key] for key in sorted(unique))


def _direct_associations(
    entity: Any,
    *,
    occurrence_global_id: str | None,
    occurrence_type_global_id: str | None,
    inherited: bool,
) -> tuple[AssociationFact, ...]:
    facts: list[AssociationFact] = []
    for relationship in sorted(
        getattr(entity, "HasAssociations", ()), key=lambda item: item.id()
    ):
        if relationship.is_a("IfcRelAssociatesMaterial"):
            resource = relationship.RelatingMaterial
            kind = "material"
            names = _material_names(resource)
            semantic_value = {
                "names": list(names),
                "resource_class": resource.is_a(),
            }
            resource_name = names[0] if len(names) == 1 else None
        elif relationship.is_a("IfcRelAssociatesClassification"):
            resource = relationship.RelatingClassification
            kind = "classification"
            try:
                classification = ifcopenshell.util.classification.get_classification(
                    resource
                )
            except Exception:
                classification = None
            system = _text(getattr(classification, "Name", None)) or "unspecified"
            identification = _text(
                getattr(resource, "Identification", None)
                or getattr(resource, "ItemReference", None)
            )
            resource_name = _text(getattr(resource, "Name", None))
            semantic_value = {
                "system": system,
                "identification": identification,
                "name": resource_name,
            }
        else:
            continue
        facts.append(
            AssociationFact(
                association_kind=kind,
                relationship_ref=_entity_public_ref(relationship),
                relationship_ifc_class=relationship.is_a(),
                resource_ref=_entity_public_ref(resource),
                resource_ifc_class=resource.is_a(),
                resource_name=resource_name,
                semantic_value=_json_safe(semantic_value),
                inherited=inherited,
                occurrence_global_id=occurrence_global_id,
                occurrence_type_global_id=occurrence_type_global_id,
                provenance=(
                    f"current_ifc:#{entity.id()}",
                    f"{relationship.is_a()}:#{relationship.id()}",
                    f"{resource.is_a()}:#{resource.id()}",
                ),
            )
        )
    return tuple(facts)


def _material_names(resource: Any) -> tuple[str, ...]:
    names: set[str] = set()
    name = _text(getattr(resource, "Name", None))
    if name:
        names.add(name)
    for attribute in (
        "Materials",
        "MaterialLayers",
        "MaterialProfiles",
        "MaterialConstituents",
    ):
        for child in getattr(resource, attribute, ()) or ():
            nested = getattr(child, "Material", child)
            names.update(_material_names(nested))
    nested_set = getattr(resource, "ForLayerSet", None)
    if nested_set is not None:
        names.update(_material_names(nested_set))
    return tuple(sorted(names))


def _entity_public_ref(entity: Any) -> str:
    global_id = _text(getattr(entity, "GlobalId", None))
    return f"guid:{global_id}" if global_id else f"step:{entity.id()}"


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
