"""Deterministic IFC2X3 to BIM JSON 2.0 extraction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.unit

from text2ifc_contract.capabilities import load_capabilities
from text2ifc_knowledge.registry import load_ifc2x3_registry

from .geometry import (
    extract_extrusion,
    geometry_loss_kind,
    representation_items,
)
from .identity import semantic_id
from .inventory import category
from .losses import loss, sort_losses
from .materials import extract_material_assignments
from .placement import extract_object_placement
from .properties import native_attributes, property_sets
from .relationships import (
    explicit_relationship,
    relationship_category,
    relationship_loss_kind,
)
from .verification import verify_output


MAX_IFC_BYTES = 100 * 1024 * 1024
MAX_SEMANTIC_ENTITIES = 100_000


@dataclass(frozen=True)
class ExtractionResult:
    source_path: Path
    source_sha256: str
    document: dict[str, Any] | None = None
    draft: dict[str, Any] | None = None
    inventory: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def losses(self) -> list[dict[str, Any]]:
        if self.draft is None:
            return []
        return list(self.draft.get("losses", []))


def _source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_ref(entity, source_sha256: str) -> str:
    global_id = getattr(entity, "GlobalId", None)
    token = global_id if global_id else semantic_id(entity, source_sha256)
    return f"sha256:{source_sha256}#{entity.is_a()}:{token}"


def _project_relative_path(path: Path) -> str:
    root = Path(__file__).resolve().parents[2]
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_semantic_product(entity) -> bool:
    return (
        entity.is_a("IfcProduct")
        or entity.is_a("IfcProject")
        or entity.is_a("IfcTypeObject")
    )


def _requires_geometry(ifc_class: str, registry) -> bool:
    declaration = registry.declaration(ifc_class)
    return declaration is not None and (
        ifc_class == "IfcSpace" or "IfcElement" in declaration["supertypes"]
    )


def _all_representation_items(entity) -> list:
    representation = getattr(entity, "Representation", None)
    if representation is None:
        return []
    return [
        item
        for shape in representation.Representations or ()
        for item in shape.Items or ()
    ]


def extract_ifc2x3(path: str | Path) -> ExtractionResult:
    source_path = Path(path).resolve()
    size = source_path.stat().st_size
    if size > MAX_IFC_BYTES:
        raise ValueError(f"IFC file exceeds {MAX_IFC_BYTES} bytes")
    source_sha256 = _source_hash(source_path)
    ifc_file = ifcopenshell.open(str(source_path))
    if ifc_file.schema != "IFC2X3":
        raise ValueError(f"expected IFC2X3, got {ifc_file.schema}")

    registry = load_ifc2x3_registry()
    capabilities = load_capabilities()
    length_factor = ifcopenshell.util.unit.calculate_unit_scale(ifc_file) * 1000.0
    source_entities = [
        entity for entity in ifc_file if _is_semantic_product(entity)
    ]
    if len(source_entities) > MAX_SEMANTIC_ENTITIES:
        raise ValueError("semantic entity limit exceeded")

    entity_ids = {
        entity.id(): semantic_id(entity, source_sha256)
        for entity in source_entities
    }
    placement_owners = {
        entity.ObjectPlacement.id(): entity_ids[entity.id()]
        for entity in source_entities
        if getattr(entity, "ObjectPlacement", None) is not None
    }
    ordered_entities = sorted(
        source_entities, key=lambda entity: entity_ids[entity.id()]
    )
    entity_index = {
        entity.id(): index for index, entity in enumerate(ordered_entities)
    }

    records: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    missing_facts: list[dict[str, Any]] = []
    represented_properties = 0
    reported_properties = 0
    representation_source = 0
    representation_reported = 0
    represented_entities = 0
    represented_material_relations: set[int] = set()

    for entity in ordered_entities:
        index = entity_index[entity.id()]
        object_id = entity_ids[entity.id()]
        ifc_class = entity.is_a()
        source_ref = _source_ref(entity, source_sha256)
        attributes = native_attributes(entity)
        psets, pset_represented, pset_reported = property_sets(entity)
        materials, material_relation_ids = extract_material_assignments(
            entity, length_factor
        )
        represented_material_relations.update(material_relation_ids)
        represented_properties += pset_represented
        reported_properties += pset_reported
        if pset_reported:
            losses.append(
                loss(
                    source_ref,
                    f"/entities/{index}/property_sets",
                    "UNSUPPORTED_PROPERTY_VALUE",
                    f"{pset_reported} property values are not scalar JSON values.",
                )
            )

        capability = capabilities[ifc_class]
        if capability == "generate":
            represented_entities += 1
        else:
            losses.append(
                loss(
                    source_ref,
                    f"/entities/{index}/ifc_class",
                    "CLASS_CAPABILITY",
                    f"{ifc_class} capability is {capability}.",
                )
            )

        if entity.is_a("IfcProduct"):
            placement = extract_object_placement(
                entity, placement_owners, entity_ids, length_factor
            )
            if placement is None:
                path_value = f"/entities/{index}/attributes/ObjectPlacement"
                missing_facts.append(
                    {
                        "entity_id": object_id,
                        "path": path_value,
                        "code": "MISSING_OBJECT_PLACEMENT",
                        "message": "Source product has no resolvable local placement.",
                    }
                )
            else:
                attributes["ObjectPlacement"] = placement

        all_items = _all_representation_items(entity)
        body_items = representation_items(entity)
        representation_source += len(all_items)
        representation = None
        for item in body_items:
            extracted = extract_extrusion(item, length_factor)
            if extracted is not None and representation is None:
                representation = extracted
                continue
            representation_reported += 1
            geometry_loss = loss(
                source_ref,
                f"/entities/{index}/attributes/Representation",
                geometry_loss_kind(item.is_a()),
                f"{item.is_a()} cannot be represented by the formal profile.",
            )
            geometry_loss["source_item_class"] = item.is_a()
            geometry_loss["substitution"] = "none"
            losses.append(geometry_loss)
        non_body_count = len(all_items) - len(body_items)
        if non_body_count > 0:
            # Axis and annotation representations are compiler-derived.
            pass
        if representation is not None:
            attributes["Representation"] = representation
        elif _requires_geometry(ifc_class, registry):
            path_value = f"/entities/{index}/attributes/Representation"
            if not body_items:
                losses.append(
                    loss(
                        source_ref,
                        path_value,
                        "MISSING_REPRESENTATION",
                        "Source product has no supported Body representation.",
                    )
                )

        record = {
            "id": object_id,
            "ifc_class": ifc_class,
            "attributes": attributes,
            "property_sets": psets,
            "provenance": {
                "source_ref": source_ref,
                "source_sha256": source_sha256,
            },
        }
        if materials:
            record["materials"] = materials
        global_id = getattr(entity, "GlobalId", None)
        if global_id:
            record["global_id"] = global_id
        records.append(record)

    relationship_records: list[dict[str, Any]] = []
    source_relationships = list(ifc_file.by_type("IfcRelationship"))
    represented_relationships = 0
    material_count = 0
    material_represented = 0
    type_count = 0
    type_represented = 0
    connection_count = 0
    connection_represented = 0
    for relation in source_relationships:
        ifc_class = relation.is_a()
        if ifc_class == "IfcRelAssociatesMaterial":
            material_count += 1
            if relation.id() in represented_material_relations:
                material_represented += 1
                represented_relationships += 1
                continue
        if ifc_class == "IfcRelDefinesByType":
            type_count += 1
            if capabilities[relation.RelatingType.is_a()] != "generate":
                losses.append(
                    loss(
                        _source_ref(relation, source_sha256),
                        "/relationships",
                        "TYPE_RELATIONSHIP",
                        (
                            f"{ifc_class} to {relation.RelatingType.is_a()} "
                            "is outside the supported type reuse profile."
                        ),
                    )
                )
                continue
        if ifc_class.startswith("IfcRelConnects"):
            connection_count += 1
        state = relationship_category(ifc_class)
        if state == "represented":
            represented_relationships += 1
        attributes = explicit_relationship(relation, entity_ids)
        if attributes is not None:
            relation_record = {
                "id": semantic_id(relation, source_sha256),
                "ifc_class": ifc_class,
                "attributes": attributes,
                "provenance": {
                    "source_ref": _source_ref(relation, source_sha256),
                    "source_sha256": source_sha256,
                },
            }
            if getattr(relation, "GlobalId", None):
                relation_record["global_id"] = relation.GlobalId
            relationship_records.append(relation_record)
            if ifc_class == "IfcRelDefinesByType":
                type_represented += 1
            elif ifc_class.startswith("IfcRelConnects"):
                connection_represented += 1
        if state == "reported":
            kind = relationship_loss_kind(ifc_class)
            losses.append(
                loss(
                    _source_ref(relation, source_sha256),
                    "/relationships",
                    kind,
                    f"{ifc_class} is outside the initial semantic profile.",
                )
            )
    relationship_records.sort(key=lambda item: item["id"])

    provenance = {
        "source_path": _project_relative_path(source_path),
        "source_sha256": source_sha256,
        "ifc_schema": ifc_file.schema,
        "extractor": "text2ifc/ifc2x3-v1",
    }
    document = {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": records,
        "relationships": relationship_records,
        "provenance": provenance,
    }

    property_source = represented_properties + reported_properties
    inventory = {
        "entities": category(len(source_entities), represented_entities),
        "relationships": category(
            len(source_relationships), represented_relationships
        ),
        "properties": category(property_source, represented_properties),
        "representations": category(
            representation_source,
            representation_source - representation_reported,
        ),
        "materials": category(material_count, material_represented),
        "types": category(type_count, type_represented),
        "connections": category(connection_count, connection_represented),
    }

    losses = sort_losses(losses)
    draft = None
    formal = document
    if losses or missing_facts:
        draft = {
            "draft_version": "bim-json-draft/1.0",
            "target_schema_version": "bim-json/2.0",
            "partial_document": document,
            "missing_facts": sorted(
                missing_facts,
                key=lambda item: (item["path"], item["code"], item["entity_id"]),
            ),
            "losses": losses,
            "clarification_targets": [],
            "provenance": provenance,
        }
        formal = None

    verify_output(formal, draft, inventory)
    return ExtractionResult(
        source_path=source_path,
        source_sha256=source_sha256,
        document=formal,
        draft=draft,
        inventory=inventory,
    )
