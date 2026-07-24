"""Deterministic, non-destructive IFC repair case mutations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
from ifcopenshell.api.root.remove_product import remove_product

from text2ifc_text.splits import atomic_write_text

from .sample import FROZEN_COUNT_CLASSES, inspect_target_chain


MUTATION_SCHEMA_VERSION = "text2ifc/ifc-repair-mutation-private/0.1"
MUTATION_TYPE = "remove_window_and_opening"
BATCH_MUTATION_SCHEMA_VERSION = "text2ifc/ifc-repair-mutation-private/0.2"
BATCH_MUTATION_TYPE = "remove_windows_and_openings_batch"


def remove_window_and_opening(
    *,
    source_path: Path | str,
    output_dir: Path | str,
    wall_global_id: str,
    opening_global_id: str,
    window_global_id: str,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Create one damaged IFC and its trace artifacts without editing the source."""

    source = Path(source_path).resolve()
    output = Path(output_dir).resolve()
    source_sha256 = _sha256(source)
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise ValueError("SOURCE_IFC_FINGERPRINT_MISMATCH")
    if output.exists():
        raise FileExistsError(f"mutation output already exists: {output}")

    target = inspect_target_chain(
        source,
        wall_global_id=wall_global_id,
        opening_global_id=opening_global_id,
        window_global_id=window_global_id,
    )
    model = ifcopenshell.open(str(source))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    before_counts = _counts(model)
    opening = model.by_guid(opening_global_id)
    window = model.by_guid(window_global_id)
    wall = model.by_guid(wall_global_id)
    wall_volume_before = _element_volume_m3(wall)
    expected_closed_void_volume = _element_volume_m3(opening)
    opening_representation = _opening_representation_summary(opening)
    owner_history_snapshot = _snapshot_owner_history(model)

    remove_product(model, product=window)
    remove_product(model, product=opening)
    _restore_owner_history(model, owner_history_snapshot)
    _canonicalize_modified_relationship_sets(model)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        damaged_path = stage / "damaged.ifc"
        model.write(str(damaged_path))
        reopened = ifcopenshell.open(str(damaged_path))
        _verify_mutation(
            reopened,
            wall_global_id=wall_global_id,
            opening_global_id=opening_global_id,
            window_global_id=window_global_id,
        )
        after_counts = _counts(reopened)
        repaired_wall = reopened.by_guid(wall_global_id)
        wall_volume_after = _element_volume_m3(repaired_wall)
        wall_volume_delta = wall_volume_after - wall_volume_before
        target_region_closed = (
            abs(wall_volume_delta - expected_closed_void_volume) <= 1e-5
        )
        if not target_region_closed:
            raise ValueError("MUTATION_TARGET_REGION_NOT_CLOSED")
        damaged_sha256 = _sha256(damaged_path)
        private_manifest = {
            "schema_version": MUTATION_SCHEMA_VERSION,
            "mutation_type": MUTATION_TYPE,
            "source": {
                "path": source.as_posix(),
                "schema": "IFC2X3",
                "size_bytes": source.stat().st_size,
                "sha256": source_sha256,
            },
            "target": target,
            "opening_representation": opening_representation,
            "counts": {"before": before_counts, "after": after_counts},
            "damaged_ifc": {
                "path": "damaged.ifc",
                "sha256": damaged_sha256,
            },
        }
        report = {
            "schema_version": "text2ifc/ifc-repair-mutation-report/0.1",
            "valid": True,
            "mutation_type": MUTATION_TYPE,
            "source_sha256": source_sha256,
            "damaged_sha256": damaged_sha256,
            "removed_classes": [
                "IfcWindow",
                "IfcRelFillsElement",
                "IfcOpeningElement",
                "IfcRelVoidsElement",
            ],
            "counts": {"before": before_counts, "after": after_counts},
            "checks": {
                "schema_preserved": True,
                "target_chain_removed": True,
                "host_wall_preserved": True,
                "source_unchanged": _sha256(source) == source_sha256,
            },
            "geometry": {
                "host_wall_volume_before_m3": wall_volume_before,
                "host_wall_volume_after_m3": wall_volume_after,
                "host_wall_volume_delta_m3": wall_volume_delta,
                "expected_closed_void_volume_m3": expected_closed_void_volume,
                "target_region_closed": target_region_closed,
            },
        }
        atomic_write_text(
            stage / "mutation_manifest.private.json", _render_json(private_manifest)
        )
        atomic_write_text(stage / "mutation_report.json", _render_json(report))
        os.replace(stage, output)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise

    return {
        "valid": True,
        "mutation_type": MUTATION_TYPE,
        "source_sha256": source_sha256,
        "damaged_sha256": damaged_sha256,
        "artifacts": {
            "damaged_ifc": "damaged.ifc",
            "private_manifest": "mutation_manifest.private.json",
            "report": "mutation_report.json",
        },
    }


def remove_windows_and_openings_batch(
    *,
    source_path: Path | str,
    output_dir: Path | str,
    targets: tuple[dict[str, str], ...] | list[dict[str, str]],
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Remove multiple Window/Opening chains in one deterministic IFC write."""

    source = Path(source_path).resolve()
    output = Path(output_dir).resolve()
    source_sha256 = _sha256(source)
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise ValueError("SOURCE_IFC_FINGERPRINT_MISMATCH")
    if output.exists():
        raise FileExistsError(f"mutation output already exists: {output}")
    if not isinstance(targets, (tuple, list)) or not 1 <= len(targets) <= 16:
        raise ValueError("BATCH_TARGET_COUNT_INVALID")

    normalized_targets: list[dict[str, str]] = []
    for index, target in enumerate(targets, start=1):
        if not isinstance(target, dict):
            raise ValueError("BATCH_TARGET_INVALID")
        try:
            normalized_targets.append(
                {
                    "target_id": f"window-repair-{index:03d}",
                    "wall_global_id": str(target["wall_global_id"]),
                    "opening_global_id": str(target["opening_global_id"]),
                    "window_global_id": str(target["window_global_id"]),
                }
            )
        except KeyError as error:
            raise ValueError("BATCH_TARGET_INVALID") from error
    for field in ("wall_global_id", "opening_global_id", "window_global_id"):
        values = [target[field] for target in normalized_targets]
        if len(set(values)) != len(values):
            raise ValueError(f"BATCH_DUPLICATE_{field.upper()}")

    model = ifcopenshell.open(str(source))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    before_counts = _counts(model)
    owner_history_snapshot = _snapshot_owner_history(model)
    snapshots: list[dict[str, Any]] = []
    for target in normalized_targets:
        inspected = inspect_target_chain(
            source,
            wall_global_id=target["wall_global_id"],
            opening_global_id=target["opening_global_id"],
            window_global_id=target["window_global_id"],
        )
        wall = model.by_guid(target["wall_global_id"])
        opening = model.by_guid(target["opening_global_id"])
        window = model.by_guid(target["window_global_id"])
        snapshots.append(
            {
                "target_id": target["target_id"],
                "target": inspected,
                "wall_volume_before_m3": _element_volume_m3(wall),
                "expected_closed_void_volume_m3": _element_volume_m3(opening),
                "opening_representation": _opening_representation_summary(opening),
                "prototype": _window_type_snapshot(window),
            }
        )

    for target in normalized_targets:
        remove_product(model, product=model.by_guid(target["window_global_id"]))
    for target in normalized_targets:
        remove_product(model, product=model.by_guid(target["opening_global_id"]))
    _restore_owner_history(model, owner_history_snapshot)
    _canonicalize_modified_relationship_sets(model)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        damaged_path = stage / "damaged.ifc"
        model.write(str(damaged_path))
        reopened = ifcopenshell.open(str(damaged_path))
        for target in normalized_targets:
            _verify_mutation(
                reopened,
                wall_global_id=target["wall_global_id"],
                opening_global_id=target["opening_global_id"],
                window_global_id=target["window_global_id"],
            )
        after_counts = _counts(reopened)
        target_records: list[dict[str, Any]] = []
        geometry_records: list[dict[str, Any]] = []
        for snapshot in snapshots:
            target = snapshot["target"]
            wall = reopened.by_guid(target["wall"]["global_id"])
            wall_volume_after = _element_volume_m3(wall)
            wall_volume_delta = (
                wall_volume_after - snapshot["wall_volume_before_m3"]
            )
            expected = snapshot["expected_closed_void_volume_m3"]
            closed = abs(wall_volume_delta - expected) <= 1e-5
            if not closed:
                raise ValueError("MUTATION_TARGET_REGION_NOT_CLOSED")
            prototype_evidence = _surviving_type_evidence(
                reopened,
                snapshot["prototype"],
            )
            target_records.append(
                {
                    "target_id": snapshot["target_id"],
                    **target,
                    "opening_representation": snapshot[
                        "opening_representation"
                    ],
                    "prototype_evidence": prototype_evidence,
                }
            )
            geometry_records.append(
                {
                    "target_id": snapshot["target_id"],
                    "wall_global_id": target["wall"]["global_id"],
                    "host_wall_volume_before_m3": snapshot[
                        "wall_volume_before_m3"
                    ],
                    "host_wall_volume_after_m3": wall_volume_after,
                    "host_wall_volume_delta_m3": wall_volume_delta,
                    "expected_closed_void_volume_m3": expected,
                    "target_region_closed": closed,
                }
            )

        damaged_sha256 = _sha256(damaged_path)
        private_manifest = {
            "schema_version": BATCH_MUTATION_SCHEMA_VERSION,
            "mutation_type": BATCH_MUTATION_TYPE,
            "source": {
                "path": source.as_posix(),
                "schema": "IFC2X3",
                "size_bytes": source.stat().st_size,
                "sha256": source_sha256,
            },
            "targets": target_records,
            "counts": {"before": before_counts, "after": after_counts},
            "damaged_ifc": {
                "path": "damaged.ifc",
                "sha256": damaged_sha256,
            },
        }
        report = {
            "schema_version": "text2ifc/ifc-repair-mutation-report/0.2",
            "valid": True,
            "mutation_type": BATCH_MUTATION_TYPE,
            "target_count": len(target_records),
            "source_sha256": source_sha256,
            "damaged_sha256": damaged_sha256,
            "counts": {"before": before_counts, "after": after_counts},
            "checks": {
                "schema_preserved": True,
                "all_target_chains_removed": True,
                "all_host_walls_preserved": True,
                "all_target_regions_closed": all(
                    item["target_region_closed"] for item in geometry_records
                ),
                "source_unchanged": _sha256(source) == source_sha256,
                "single_model_write": True,
            },
            "geometry": {"targets": geometry_records},
        }
        atomic_write_text(
            stage / "mutation_manifest.private.json",
            _render_json(private_manifest),
        )
        atomic_write_text(stage / "mutation_report.json", _render_json(report))
        os.replace(stage, output)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise

    return {
        "valid": True,
        "mutation_type": BATCH_MUTATION_TYPE,
        "target_count": len(normalized_targets),
        "source_sha256": source_sha256,
        "damaged_sha256": damaged_sha256,
        "artifacts": {
            "damaged_ifc": "damaged.ifc",
            "private_manifest": "mutation_manifest.private.json",
            "report": "mutation_report.json",
        },
    }


def _counts(model: Any) -> dict[str, int]:
    return {
        ifc_class: len(model.by_type(ifc_class))
        for ifc_class in FROZEN_COUNT_CLASSES
    }


def _verify_mutation(
    model: Any,
    *,
    wall_global_id: str,
    opening_global_id: str,
    window_global_id: str,
) -> None:
    if model.schema != "IFC2X3":
        raise ValueError("MUTATED_IFC_SCHEMA_MISMATCH")
    if _by_guid_or_none(model, wall_global_id) is None:
        raise ValueError("MUTATION_REMOVED_HOST_WALL")
    if _by_guid_or_none(model, opening_global_id) is not None:
        raise ValueError("MUTATION_LEFT_TARGET_OPENING")
    if _by_guid_or_none(model, window_global_id) is not None:
        raise ValueError("MUTATION_LEFT_TARGET_WINDOW")


def _opening_representation_summary(opening: Any) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    representation = getattr(opening, "Representation", None)
    for shape in getattr(representation, "Representations", ()):
        items = []
        for item in shape.Items:
            item_summary: dict[str, Any] = {"ifc_class": item.is_a()}
            if item.is_a("IfcExtrudedAreaSolid"):
                item_summary.update(
                    {
                        "depth": float(item.Depth),
                        "extruded_direction": [
                            float(value)
                            for value in item.ExtrudedDirection.DirectionRatios
                        ],
                        "profile_ifc_class": item.SweptArea.is_a(),
                    }
                )
                if item.SweptArea.is_a("IfcRectangleProfileDef"):
                    item_summary["profile_x_dim"] = float(item.SweptArea.XDim)
                    item_summary["profile_y_dim"] = float(item.SweptArea.YDim)
            items.append(item_summary)
        summaries.append(
            {
                "identifier": shape.RepresentationIdentifier,
                "type": shape.RepresentationType,
                "items": items,
            }
        )
    return summaries


def _window_type_snapshot(window: Any) -> dict[str, Any]:
    relations = [
        relation
        for relation in window.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(relations) != 1:
        raise ValueError("WINDOW_TYPE_RELATIONSHIP_AMBIGUOUS")
    relating_type = relations[0].RelatingType
    return {
        "ifc_class": relating_type.is_a(),
        "global_id": relating_type.GlobalId,
        "name": relating_type.Name,
        "occurrence_count_before": sum(
            1 for item in relations[0].RelatedObjects if item.is_a("IfcWindow")
        ),
    }


def _surviving_type_evidence(
    model: Any,
    prototype: dict[str, Any],
) -> dict[str, Any]:
    relating_type = _by_guid_or_none(model, prototype["global_id"])
    if relating_type is None or relating_type.is_a() != prototype["ifc_class"]:
        raise ValueError("BATCH_PROTOTYPE_TYPE_NOT_SURVIVING")
    occurrence_count = sum(
        1
        for relation in relating_type.ObjectTypeOf
        for item in relation.RelatedObjects
        if item.is_a("IfcWindow")
    )
    if occurrence_count < 1:
        raise ValueError("BATCH_PROTOTYPE_OCCURRENCE_NOT_SURVIVING")
    return {
        "source": "damaged_ifc_surviving_type",
        "ifc_class": relating_type.is_a(),
        "global_id": relating_type.GlobalId,
        "name": relating_type.Name,
        "surviving_occurrence_count": occurrence_count,
    }


def _canonicalize_modified_relationship_sets(model: Any) -> None:
    # IfcOpenShell's remove_product updates this IFC SET through a Python set.
    # Sorting the affected semantic set prevents process-randomized STEP order.
    for relationship in model.by_type("IfcRelDefinesByType"):
        relationship.RelatedObjects = tuple(
            sorted(
                relationship.RelatedObjects,
                key=lambda entity: (getattr(entity, "GlobalId", ""), entity.id()),
            )
        )


def _snapshot_owner_history(model: Any) -> dict[str, Any]:
    histories = {
        history.id(): {
            "entity": history,
            "attributes": tuple(history),
        }
        for history in model.by_type("IfcOwnerHistory")
    }
    relationships = {
        relationship.id(): relationship.OwnerHistory
        for relationship in model.by_type("IfcRelationship")
    }
    return {"histories": histories, "relationships": relationships}


def _restore_owner_history(model: Any, snapshot: dict[str, Any]) -> None:
    original_histories = snapshot["histories"]
    for relationship in model.by_type("IfcRelationship"):
        original = snapshot["relationships"].get(relationship.id())
        if original is not None and relationship.OwnerHistory != original:
            relationship.OwnerHistory = original

    for history_id, saved in original_histories.items():
        try:
            current = model.by_id(history_id)
        except RuntimeError:
            continue
        if current is None or not current.is_a("IfcOwnerHistory"):
            continue
        for index, value in enumerate(saved["attributes"]):
            current[index] = value

    original_ids = set(original_histories)
    for history in list(model.by_type("IfcOwnerHistory")):
        if history.id() not in original_ids and not model.get_inverse(history):
            model.remove(history)


def _element_volume_m3(element: Any) -> float:
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, element)
    return float(ifcopenshell.util.shape.get_volume(shape.geometry))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _by_guid_or_none(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _render_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
