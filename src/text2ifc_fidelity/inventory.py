from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import ifcopenshell


SCHEMA_VERSION = "text2ifc/phase4-fidelity-inventory-v1"
SUPPORTED_PRODUCT_CLASSES = {
    "IfcBeam",
    "IfcColumn",
    "IfcDoor",
    "IfcOpeningElement",
    "IfcRoof",
    "IfcSlab",
    "IfcSpace",
    "IfcStair",
    "IfcStairFlight",
    "IfcWall",
    "IfcWallStandardCase",
    "IfcWindow",
}


def build_fidelity_inventory(
    manifest_path: str | Path,
    splits_path: str | Path,
) -> dict[str, Any]:
    manifest = _read_jsonl(Path(manifest_path))
    splits_payload = _read_json(Path(splits_path))
    split_by_file_id = _split_by_file_id(splits_payload)
    root = Path(manifest_path).resolve().parents[2]

    records = []
    for source in sorted(manifest, key=lambda item: item["id"]):
        source_path = root / source["local_path"]
        metrics = _metrics_for_ifc(source_path)
        record = {
            "id": source["id"],
            "scene_family": source["scene_family"],
            "split": split_by_file_id[source["id"]],
            "declared_schema": source["declared_schema"],
            "local_path": source["local_path"],
            "sha256": source["sha256"],
            "sha256_verified": _sha256(source_path) == source["sha256"],
            "metrics": metrics,
            "fact_classification": _fact_classification(metrics),
        }
        records.append(record)

    return {
        "schema_version": SCHEMA_VERSION,
        "source_manifest": _posix_path(Path(manifest_path)),
        "source_splits": _posix_path(Path(splits_path)),
        "counts": {
            "files": {
                "total": len(records),
                "train": _count_split(records, "train"),
                "validation": _count_split(records, "validation"),
                "test": _count_split(records, "test"),
            }
        },
        "records": records,
    }


def _metrics_for_ifc(path: Path) -> dict[str, Any]:
    model = ifcopenshell.open(str(path))
    representation_kinds = Counter()
    for shape in _safe_by_type(model, "IfcShapeRepresentation"):
        representation_type = getattr(shape, "RepresentationType", None)
        if representation_type:
            representation_kinds[str(representation_type)] += 1
        for item in getattr(shape, "Items", ()) or ():
            representation_kinds[item.is_a()] += 1

    product_classes = Counter(
        product.is_a() for product in _safe_by_type(model, "IfcProduct")
    )
    connection_classes = (
        "IfcRelConnectsElements",
        "IfcRelConnectsPathElements",
        "IfcRelConnectsPortToElement",
        "IfcRelConnectsPorts",
        "IfcRelConnectsStructuralActivity",
        "IfcRelConnectsStructuralMember",
        "IfcRelConnectsWithEccentricity",
        "IfcRelConnectsWithRealizingElements",
    )
    brep_classes = (
        "IfcFacetedBrep",
        "IfcAdvancedBrep",
        "IfcManifoldSolidBrep",
    )
    tessellation_classes = (
        "IfcTriangulatedFaceSet",
        "IfcPolygonalFaceSet",
        "IfcTessellatedItem",
        "IfcFaceBasedSurfaceModel",
    )

    return {
        "material_associations": _count_by_type(model, "IfcRelAssociatesMaterial"),
        "material_layers": _count_by_type(model, "IfcMaterialLayer"),
        "type_relationships": _count_by_type(model, "IfcRelDefinesByType"),
        "connection_topology": sum(_count_by_type(model, name) for name in connection_classes),
        "representation_kinds": dict(sorted(representation_kinds.items())),
        "mapped_geometry": _count_by_type(model, "IfcMappedItem"),
        "brep": sum(_count_by_type(model, name) for name in brep_classes),
        "tessellation": sum(_count_by_type(model, name) for name in tessellation_classes),
        "openings": _count_by_type(model, "IfcOpeningElement"),
        "spaces": _count_by_type(model, "IfcSpace"),
        "product_classes": dict(sorted(product_classes.items())),
    }


def _fact_classification(metrics: dict[str, Any]) -> dict[str, Any]:
    product_classes = metrics["product_classes"]
    supported_products = sum(
        count
        for ifc_class, count in product_classes.items()
        if ifc_class in SUPPORTED_PRODUCT_CLASSES
    )
    deferred_products = sum(
        count
        for ifc_class, count in product_classes.items()
        if ifc_class not in SUPPORTED_PRODUCT_CLASSES
    )
    return {
        "already_supported": {
            "openings": metrics["openings"],
            "spaces": metrics["spaces"],
            "supported_product_classes": supported_products,
        },
        "phase4_candidate": {
            "material_associations": metrics["material_associations"],
            "material_layers": metrics["material_layers"],
            "type_relationships": metrics["type_relationships"],
            "connection_topology": metrics["connection_topology"],
            "mapped_geometry": metrics["mapped_geometry"],
        },
        "explicit_loss": {
            "brep": metrics["brep"],
            "tessellation": metrics["tessellation"],
        },
        "deferred": {
            "unsupported_product_classes": deferred_products,
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_by_file_id(splits_payload: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for split_name, families in splits_payload["splits"].items():
        for family in families:
            for file_id in family["file_ids"]:
                result[file_id] = split_name
    return result


def _count_split(records: list[dict[str, Any]], split: str) -> int:
    return sum(1 for record in records if record["split"] == split)


def _safe_by_type(model: Any, ifc_class: str) -> list[Any]:
    try:
        return list(model.by_type(ifc_class))
    except RuntimeError:
        return []


def _count_by_type(model: Any, ifc_class: str) -> int:
    return len(_safe_by_type(model, ifc_class))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _posix_path(path: Path) -> str:
    return path.as_posix()
