"""Regenerate deterministic IFC2X3 declaration and property registries."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

import ifcopenshell  # noqa: E402
import ifcopenshell.util.pset  # noqa: E402

from text2ifc_knowledge.express_registry import build_declaration_registry  # noqa: E402
from text2ifc_knowledge.psd_registry import build_property_registry  # noqa: E402
from text2ifc_knowledge.sources import (  # noqa: E402
    load_source_manifest,
    verify_source_file,
)


GENERATOR_VERSION = 1
MANIFEST_PATH = ROOT / "schemas" / "ifc" / "IFC2X3_TC1.sources.json"
OUTPUT_ROOT = ROOT / "schemas" / "ifc" / "generated" / "IFC2X3"


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(payload: dict) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _cross_check_psets(property_registry: dict) -> dict[str, int]:
    adapter = ifcopenshell.util.pset.get_template("IFC2X3")
    files = adapter.templates
    template_count = sum(
        len(file.by_type("IfcPropertySetTemplate")) for file in files
    )
    property_count = sum(
        len(file.by_type("IfcSimplePropertyTemplate")) for file in files
    )
    if template_count != property_registry["counts"]["property_sets"]:
        raise RuntimeError(
            "official PSD and IfcOpenShell property-set counts disagree: "
            f"{property_registry['counts']['property_sets']} != {template_count}"
        )
    if property_count != property_registry["counts"]["simple_properties"]:
        raise RuntimeError(
            "official PSD and IfcOpenShell simple-property counts disagree: "
            f"{property_registry['counts']['simple_properties']} != {property_count}"
        )
    for name in (
        "Pset_WallCommon",
        "Pset_SpaceCommon",
        "Pset_OpeningElementCommon",
    ):
        official = property_registry["property_sets"].get(name)
        adapted = adapter.get_by_name(name)
        if official is None or adapted is None:
            raise RuntimeError(f"representative property set missing: {name}")
        official_names = set(official["properties"])
        adapted_names = {item.Name for item in adapted.HasPropertyTemplates}
        if official_names != adapted_names:
            raise RuntimeError(f"property names disagree for {name}")
    return {
        "property_sets": template_count,
        "simple_property_templates": property_count,
    }


def main() -> int:
    source_manifest = load_source_manifest(MANIFEST_PATH)
    express_source = source_manifest.source("ifc2x3-tc1-express")
    psd_source = source_manifest.source("ifc2x3-tc1-html-psd")
    express_path = ROOT / express_source.local_path
    psd_path = ROOT / psd_source.cache_path

    verify_source_file(express_path, express_source)
    verify_source_file(psd_path, psd_source)

    declarations = build_declaration_registry(express_path)
    if declarations["counts"] != {"declarations": 980, "entities": 653}:
        raise RuntimeError(
            f"unexpected IFC2X3 declaration counts: {declarations['counts']}"
        )
    property_sets = build_property_registry(psd_path)
    if property_sets["counts"]["property_sets"] != 317:
        raise RuntimeError(
            f"unexpected IFC2X3 PSD count: {property_sets['counts']}"
        )
    adapter_counts = _cross_check_psets(property_sets)

    declaration_bytes = _canonical_json(declarations)
    property_bytes = _canonical_json(property_sets)
    declaration_path = OUTPUT_ROOT / "declarations.json"
    property_path = OUTPUT_ROOT / "property_sets.json"
    _atomic_write(declaration_path, declaration_bytes)
    _atomic_write(property_path, property_bytes)

    registry_manifest = {
        "schema": "IFC2X3",
        "generator_version": GENERATOR_VERSION,
        "ifcopenshell_version": ifcopenshell.version,
        "source_manifest_sha256": _sha256_file(MANIFEST_PATH),
        "sources": {
            source.id: {
                "role": source.role,
                "sha256": source.sha256,
                "url": source.url,
            }
            for source in source_manifest.sources
        },
        "cross_checks": {
            "ifcopenshell_pset_adapter": adapter_counts,
        },
        "outputs": {
            "declarations.json": {
                "sha256": _sha256_bytes(declaration_bytes),
                "counts": declarations["counts"],
            },
            "property_sets.json": {
                "sha256": _sha256_bytes(property_bytes),
                "counts": property_sets["counts"],
            },
        },
    }
    _atomic_write(
        OUTPUT_ROOT / "registry-manifest.json",
        _canonical_json(registry_manifest),
    )
    print(
        "generated IFC2X3 registry: "
        f"{declarations['counts']['declarations']} declarations, "
        f"{property_sets['counts']['property_sets']} property sets, "
        f"{property_sets['counts']['simple_properties']} simple properties"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
