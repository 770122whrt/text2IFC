"""Deterministic IFC schema knowledge."""

from .express_registry import build_declaration_registry
from .psd_registry import build_property_registry
from .registry import IfcKnowledgeRegistry, load_ifc2x3_registry
from .sources import (
    ArchiveSafetyError,
    SourceIntegrityError,
    SourceManifestError,
    inspect_zip_archive,
    load_source_manifest,
    verify_source_file,
)

__all__ = [
    "ArchiveSafetyError",
    "IfcKnowledgeRegistry",
    "SourceIntegrityError",
    "SourceManifestError",
    "build_declaration_registry",
    "build_property_registry",
    "inspect_zip_archive",
    "load_ifc2x3_registry",
    "load_source_manifest",
    "verify_source_file",
]
