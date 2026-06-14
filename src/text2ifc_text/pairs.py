"""Deterministic Text-to-BIM-JSON pair generation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from text2ifc_contract.validation_v2 import validate_v2_document

from .splits import ROOT, atomic_write_text, render_json


DEFAULT_GOLD_MANIFEST_PATH = (
    ROOT / "dataset" / "processed" / "text2json" / "gold-set-manifest.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "dataset" / "processed" / "text2json"
PAIR_MANIFEST_SCHEMA_VERSION = "text2ifc/text2json-pair-manifest-v1"
PAIR_STYLES = ("concise", "enumerated", "spatial", "property_focused")
TEMPLATE_VERSION = "v1"


class PairGenerationError(ValueError):
    """Raised when pair generation would be unsafe or nondeterministic."""


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PairGenerationError(f"missing gold or target JSON: {_relative(path)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PairGenerationError(f"invalid JSON in {_relative(path)}") from exc
    if not isinstance(payload, dict):
        raise PairGenerationError(f"expected object in {_relative(path)}")
    return payload


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _target_hash(target: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(target).encode("utf-8")).hexdigest()


def _record_id(source_file_id: str, style: str, target_sha256: str) -> str:
    digest = hashlib.sha256(
        f"{source_file_id}:{style}:{TEMPLATE_VERSION}:{target_sha256}".encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    return f"{source_file_id}:{style}:{digest}"


def _class_counts(target: dict[str, Any]) -> dict[str, int]:
    return dict(
        sorted(Counter(entity["ifc_class"] for entity in target["entities"]).items())
    )


def _named_entities(target: dict[str, Any], classes: set[str]) -> list[str]:
    names: list[str] = []
    for entity in target["entities"]:
        if entity["ifc_class"] not in classes:
            continue
        name = entity["attributes"].get("Name") or entity["id"]
        names.append(f"{entity['ifc_class']} {entity['id']} named {name}")
    return sorted(names)


def _relationship_counts(target: dict[str, Any]) -> dict[str, int]:
    return dict(
        sorted(
            Counter(relation["ifc_class"] for relation in target["relationships"]).items()
        )
    )


def _property_summary(target: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for entity in target["entities"]:
        for pset_name, properties in sorted(entity.get("property_sets", {}).items()):
            if not properties:
                continue
            names = ", ".join(sorted(properties))
            rows.append(f"{entity['id']} {pset_name}: {names}")
    return rows


def _render_text(target: dict[str, Any], *, style: str, source_file_id: str) -> str:
    counts = _class_counts(target)
    class_text = ", ".join(f"{count} {name}" for name, count in counts.items())
    if style == "concise":
        return (
            f"Create a formal BIM JSON 2.0 IFC2X3 model for {source_file_id}. "
            f"The supported target contains {len(target['entities'])} semantic "
            f"entities and {len(target['relationships'])} explicit relationships: "
            f"{class_text}."
        )
    if style == "enumerated":
        items = _named_entities(target, set(counts))
        return (
            f"Create BIM JSON 2.0 for {source_file_id} with these IFC classes: "
            + "; ".join(items[:80])
            + "."
        )
    if style == "spatial":
        spatial = _named_entities(
            target,
            {"IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcSpace"},
        )
        relation_counts = _relationship_counts(target)
        relation_text = ", ".join(
            f"{count} {name}" for name, count in relation_counts.items()
        )
        if not relation_text:
            relation_text = "no explicit void/fill relationships"
        return (
            f"Create the spatial BIM JSON 2.0 structure for {source_file_id}. "
            f"Use parent-relative ObjectPlacement from the target. Spatial objects: "
            + "; ".join(spatial)
            + f". Relationships: {relation_text}."
        )
    if style == "property_focused":
        properties = _property_summary(target)
        property_text = "; ".join(properties[:80]) if properties else "no scalar property sets"
        return (
            f"Create BIM JSON 2.0 for {source_file_id} and preserve the supported "
            f"scalar property sets present in the target: {property_text}."
        )
    raise PairGenerationError(f"unsupported text style: {style}")


def _load_formal_records(gold_manifest_path: Path) -> list[dict[str, Any]]:
    manifest = _read_json(gold_manifest_path)
    if manifest.get("schema_version") != "text2ifc/text2json-gold-set-v1":
        raise PairGenerationError("gold manifest schema_version is invalid")
    records = manifest.get("records")
    if not isinstance(records, list):
        raise PairGenerationError("gold manifest records must be a list")
    formal_records = [
        record for record in records if record.get("target_kind") == "formal"
    ]
    if not formal_records:
        raise PairGenerationError("gold manifest has no formal targets")
    return sorted(formal_records, key=lambda record: record["source_file_id"])


def build_pair_records(gold_manifest_path: Path | str) -> list[dict[str, Any]]:
    manifest_path = Path(gold_manifest_path)
    records: list[dict[str, Any]] = []
    for gold_record in _load_formal_records(manifest_path):
        target_path = ROOT / gold_record["target_json_path"]
        target = _read_json(target_path)
        issues = validate_v2_document(target)
        if issues:
            first = issues[0]
            raise PairGenerationError(
                f"{gold_record['source_file_id']} target is not formal: "
                f"{first.code} at {first.path}"
            )
        target_sha256 = _target_hash(target)
        for style in PAIR_STYLES:
            records.append(
                {
                    "record_id": _record_id(
                        gold_record["source_file_id"], style, target_sha256
                    ),
                    "target_kind": "formal",
                    "input_text": _render_text(
                        target,
                        style=style,
                        source_file_id=gold_record["source_file_id"],
                    ),
                    "target_json_path": gold_record["target_json_path"],
                    "target_sha256": target_sha256,
                    "split": gold_record["split"],
                    "scene_family": gold_record["scene_family"],
                    "source_file_id": gold_record["source_file_id"],
                    "source_sha256": gold_record["source_sha256"],
                    "text_style": style,
                    "template_id": f"{style}-{TEMPLATE_VERSION}",
                    "review_status": "generated",
                }
            )
    return sorted(records, key=lambda record: record["record_id"])


def build_pair_manifest(
    records: list[dict[str, Any]],
    *,
    source_manifest: Path | str,
) -> dict[str, Any]:
    split_counts = Counter(record["split"] for record in records)
    style_counts = Counter(record["text_style"] for record in records)
    target_kind_counts = Counter(record["target_kind"] for record in records)
    review_counts = Counter(record["review_status"] for record in records)
    return {
        "schema_version": PAIR_MANIFEST_SCHEMA_VERSION,
        "source_gold_manifest": _relative(Path(source_manifest)),
        "record_count": len(records),
        "counts_by_split": dict(sorted(split_counts.items())),
        "counts_by_style": dict(sorted(style_counts.items())),
        "counts_by_target_kind": dict(sorted(target_kind_counts.items())),
        "counts_by_review_status": dict(sorted(review_counts.items())),
        "records": [
            {
                "record_id": record["record_id"],
                "split": record["split"],
                "scene_family": record["scene_family"],
                "source_file_id": record["source_file_id"],
                "text_style": record["text_style"],
                "target_kind": record["target_kind"],
                "target_json_path": record["target_json_path"],
            }
            for record in records
        ],
    }


def _render_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(_canonical_json(record) + "\n" for record in records)


def build_pair_outputs(
    *,
    gold_manifest_path: Path | str = DEFAULT_GOLD_MANIFEST_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> tuple[dict[str, Any], dict[Path, str]]:
    records = build_pair_records(gold_manifest_path)
    manifest = build_pair_manifest(records, source_manifest=gold_manifest_path)
    output_root = Path(output_dir)
    outputs: dict[Path, str] = {
        output_root / "pair-manifest.json": render_json(manifest)
    }
    for split in sorted({record["split"] for record in records}):
        split_records = [record for record in records if record["split"] == split]
        outputs[output_root / "pairs" / f"{split}.jsonl"] = _render_jsonl(
            split_records
        )
    return manifest, outputs


def write_pair_artifacts(
    *,
    gold_manifest_path: Path | str = DEFAULT_GOLD_MANIFEST_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    manifest, outputs = build_pair_outputs(
        gold_manifest_path=gold_manifest_path,
        output_dir=output_dir,
    )
    for path, content in outputs.items():
        atomic_write_text(path, content)
    return manifest


def check_pair_artifacts(
    *,
    gold_manifest_path: Path | str = DEFAULT_GOLD_MANIFEST_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    manifest, outputs = build_pair_outputs(
        gold_manifest_path=gold_manifest_path,
        output_dir=output_dir,
    )
    for path, expected in outputs.items():
        if not path.is_file():
            raise PairGenerationError(f"missing pair artifact: {_relative(path)}")
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            raise PairGenerationError(f"pair artifact drift: {_relative(path)}")
    return manifest
