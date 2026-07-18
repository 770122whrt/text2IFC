from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


INDEX_SCHEMA_VERSION = "text2ifc/ifc-index/0.1"


@dataclass(frozen=True)
class IndexMetadata:
    source_ifc_sha256: str
    ifc_schema: str
    extractor_version: str
    source_size_bytes: int
    created_at: str
    index_schema_version: str = INDEX_SCHEMA_VERSION


@dataclass(frozen=True)
class AliasFact:
    normalized_value: str
    original_value: str
    field: str
    provenance: str


@dataclass(frozen=True)
class RelationshipFact:
    kind: str
    target_global_id: str
    provenance: str


@dataclass(frozen=True)
class PropertyFact:
    set_kind: str
    set_name: str
    property_name: str
    value: Any
    value_type: str | None
    unit: str | None
    inherited: bool
    provenance: str


@dataclass(frozen=True)
class IndexDiagnostic:
    code: str
    severity: str
    message: str
    record_id: str | None = None
    ifc_global_id: str | None = None
    step_id: int | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ElementRecord:
    record_id: str
    ifc_global_id: str | None
    identity_reliable: bool
    ifc_class: str
    name: str | None
    long_name: str | None
    tag: str | None
    object_type: str | None
    type_name: str | None
    type_global_id: str | None
    storey_name: str | None
    storey_global_id: str | None
    geometry_capability: str
    geometry_summary: dict[str, Any] = field(default_factory=dict)
    facets: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    aliases: tuple[AliasFact, ...] = ()
    relationships: tuple[RelationshipFact, ...] = ()
    properties: tuple[PropertyFact, ...] = ()
