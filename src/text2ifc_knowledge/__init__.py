"""Deterministic IFC schema knowledge."""

from .express_registry import build_declaration_registry
from .psd_registry import build_property_registry
from .registry import IfcKnowledgeRegistry, load_ifc2x3_registry
from .property_search import (
    InMemoryVectorIndex,
    PropertyAlias,
    PropertyKnowledgeQuery,
    PropertyKnowledgeResolver,
    PropertyKnowledgeStore,
    build_standard_property_records,
)
from .sources import (
    ArchiveSafetyError,
    SourceIntegrityError,
    SourceManifestError,
    SourceSpec,
    download_source,
    inspect_zip_archive,
    load_source_manifest,
    verify_source_file,
)

__all__ = [
    "ArchiveSafetyError",
    "IfcKnowledgeRegistry",
    "InMemoryVectorIndex",
    "PropertyAlias",
    "PropertyKnowledgeQuery",
    "PropertyKnowledgeResolver",
    "PropertyKnowledgeStore",
    "SourceIntegrityError",
    "SourceManifestError",
    "SourceSpec",
    "build_declaration_registry",
    "build_property_registry",
    "build_standard_property_records",
    "download_source",
    "inspect_zip_archive",
    "load_ifc2x3_registry",
    "load_source_manifest",
    "verify_source_file",
]
