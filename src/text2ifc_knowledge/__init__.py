"""Deterministic IFC schema knowledge."""

from .express_registry import build_declaration_registry
from .psd_registry import build_property_registry
from .registry import IfcKnowledgeRegistry, load_ifc2x3_registry
from .property_search import (
    BgeM3EmbeddingProvider,
    InMemoryVectorIndex,
    PropertyAlias,
    PropertyKnowledgeQuery,
    PropertyKnowledgeResolver,
    PropertyKnowledgeStore,
    PropertyResolutionPolicy,
    QdrantVectorIndex,
    build_project_property_records,
    build_standard_property_records,
    collection_fingerprint,
    create_default_property_resolver,
    default_standard_corpus_fingerprint,
    load_reviewed_aliases,
    load_property_resolution_policy,
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
    "BgeM3EmbeddingProvider",
    "IfcKnowledgeRegistry",
    "InMemoryVectorIndex",
    "PropertyAlias",
    "PropertyKnowledgeQuery",
    "PropertyKnowledgeResolver",
    "PropertyKnowledgeStore",
    "PropertyResolutionPolicy",
    "QdrantVectorIndex",
    "SourceIntegrityError",
    "SourceManifestError",
    "SourceSpec",
    "build_declaration_registry",
    "build_project_property_records",
    "build_property_registry",
    "build_standard_property_records",
    "collection_fingerprint",
    "create_default_property_resolver",
    "default_standard_corpus_fingerprint",
    "download_source",
    "inspect_zip_archive",
    "load_ifc2x3_registry",
    "load_reviewed_aliases",
    "load_property_resolution_policy",
    "load_source_manifest",
    "verify_source_file",
]
