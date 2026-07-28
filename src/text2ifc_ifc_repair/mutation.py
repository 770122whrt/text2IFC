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
import ifcopenshell.util.element
import ifcopenshell.util.shape
import ifcopenshell.util.unit
from ifcopenshell.api.root.remove_product import remove_product

from text2ifc_text.splits import atomic_write_text

from .sample import FROZEN_COUNT_CLASSES, inspect_target_chain


MUTATION_SCHEMA_VERSION = "text2ifc/ifc-repair-mutation-private/0.1"
MUTATION_TYPE = "remove_window_and_opening"
BATCH_MUTATION_SCHEMA_VERSION = "text2ifc/ifc-repair-mutation-private/0.2"
BATCH_MUTATION_TYPE = "remove_windows_and_openings_batch"
DOOR_MUTATION_SCHEMA_VERSION = "text2ifc/ifc-repair-door-mutation-private/0.1"
DOOR_BATCH_MUTATION_SCHEMA_VERSION = (
    "text2ifc/ifc-repair-door-mutation-private/0.2"
)


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
            "removed_windows": [
                {
                    "target_id": "window-repair-001",
                    "name": target["window"]["name"],
                }
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
    for field in ("opening_global_id", "window_global_id"):
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
                "requested_properties": _window_repair_properties(window),
                "requested_quantities": [
                    *_window_repair_quantities(window),
                    *_opening_repair_quantities(opening),
                ],
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
        wall_closure: dict[str, dict[str, float | bool]] = {}
        for snapshot in snapshots:
            wall_global_id = str(snapshot["target"]["wall"]["global_id"])
            closure = wall_closure.setdefault(
                wall_global_id,
                {
                    "wall_volume_before_m3": snapshot["wall_volume_before_m3"],
                    "expected_closed_void_volume_m3": 0.0,
                },
            )
            closure["expected_closed_void_volume_m3"] = float(
                closure["expected_closed_void_volume_m3"]
            ) + float(snapshot["expected_closed_void_volume_m3"])
        for wall_global_id, closure in wall_closure.items():
            wall_volume_after = _element_volume_m3(reopened.by_guid(wall_global_id))
            wall_volume_delta = wall_volume_after - float(
                closure["wall_volume_before_m3"]
            )
            expected = float(closure["expected_closed_void_volume_m3"])
            closure.update(
                {
                    "wall_volume_after_m3": wall_volume_after,
                    "wall_volume_delta_m3": wall_volume_delta,
                    "closed": abs(wall_volume_delta - expected) <= 1e-5,
                }
            )

        target_records: list[dict[str, Any]] = []
        geometry_records: list[dict[str, Any]] = []
        for snapshot in snapshots:
            target = snapshot["target"]
            closure = wall_closure[str(target["wall"]["global_id"])]
            closed = bool(closure["closed"])
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
                    "requested_properties": snapshot["requested_properties"],
                    "requested_quantities": snapshot["requested_quantities"],
                }
            )
            geometry_records.append(
                {
                    "target_id": snapshot["target_id"],
                    "wall_global_id": target["wall"]["global_id"],
                    "host_wall_volume_before_m3": closure[
                        "wall_volume_before_m3"
                    ],
                    "host_wall_volume_after_m3": closure["wall_volume_after_m3"],
                    "host_wall_volume_delta_m3": closure["wall_volume_delta_m3"],
                    "target_expected_closed_void_volume_m3": snapshot[
                        "expected_closed_void_volume_m3"
                    ],
                    "wall_expected_closed_void_volume_m3": closure[
                        "expected_closed_void_volume_m3"
                    ],
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
            "removed_windows": [
                {
                    "target_id": str(target["target_id"]),
                    "name": target["window"]["name"],
                }
                for target in target_records
            ],
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


def remove_door(
    *,
    source_path: Path | str,
    output_dir: Path | str,
    door_global_id: str,
    preserve_opening: bool,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Remove one valid Door fill chain, optionally retaining its Opening/void."""

    source = Path(source_path).resolve()
    output = Path(output_dir).resolve()
    source_sha256 = _sha256(source)
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise ValueError("SOURCE_IFC_FINGERPRINT_MISMATCH")
    if output.exists():
        raise FileExistsError(f"mutation output already exists: {output}")
    model = ifcopenshell.open(str(source))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    try:
        door = model.by_guid(door_global_id)
    except RuntimeError as error:
        raise ValueError("DOOR_NOT_FOUND") from error
    if door is None or not door.is_a("IfcDoor"):
        raise ValueError("DOOR_NOT_FOUND")
    if len(door.FillsVoids) != 1:
        raise ValueError("DOOR_FILL_CHAIN_INVALID")
    opening = door.FillsVoids[0].RelatingOpeningElement
    if len(opening.VoidsElements) != 1:
        raise ValueError("DOOR_OPENING_HOST_INVALID")
    wall = opening.VoidsElements[0].RelatingBuildingElement
    if not wall.is_a("IfcWall"):
        raise ValueError("DOOR_HOST_UNSUPPORTED")
    snapshot = _door_snapshot(door, opening, wall)
    opening_global_id = str(opening.GlobalId)
    before_counts = _counts(model)
    owner_history_snapshot = _snapshot_owner_history(model)
    remove_product(model, product=door)
    if not preserve_opening:
        remove_product(model, product=opening)
    _restore_owner_history(model, owner_history_snapshot)
    _canonicalize_modified_relationship_sets(model)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        damaged_path = stage / "damaged.ifc"
        model.write(str(damaged_path))
        reopened = ifcopenshell.open(str(damaged_path))
        if _optional_guid(reopened, door_global_id) is not None:
            raise ValueError("DOOR_MUTATION_REMOVE_FAILED")
        surviving_opening = _optional_guid(reopened, opening_global_id)
        if preserve_opening:
            if surviving_opening is None:
                raise ValueError("DOOR_MUTATION_OPENING_NOT_PRESERVED")
            if len(surviving_opening.HasFillings) != 0:
                raise ValueError("DOOR_MUTATION_OPENING_NOT_EMPTY")
            if len(surviving_opening.VoidsElements) != 1:
                raise ValueError("DOOR_MUTATION_VOID_NOT_PRESERVED")
        elif surviving_opening is not None:
            raise ValueError("DOOR_MUTATION_OPENING_REMOVE_FAILED")
        after_counts = _counts(reopened)
        damaged_sha256 = _sha256(damaged_path)
        mode = (
            "remove_door_preserve_opening"
            if preserve_opening
            else "remove_door_and_opening"
        )
        manifest = {
            "schema_version": DOOR_MUTATION_SCHEMA_VERSION,
            "mutation_type": mode,
            "source": {
                "path": source.as_posix(),
                "schema": "IFC2X3",
                "size_bytes": source.stat().st_size,
                "sha256": source_sha256,
            },
            "target": snapshot,
            "counts": {"before": before_counts, "after": after_counts},
            "damaged_ifc": {"path": "damaged.ifc", "sha256": damaged_sha256},
        }
        report = {
            "schema_version": "text2ifc/ifc-repair-door-mutation-report/0.1",
            "valid": True,
            "mutation_type": mode,
            "source_sha256": source_sha256,
            "damaged_sha256": damaged_sha256,
            "removed_doors": [
                {
                    "global_id": snapshot["door"]["global_id"],
                    "name": snapshot["door"]["name"],
                    "type_global_id": snapshot["door"]["type_global_id"],
                    "type_name": snapshot["door"]["type_name"],
                    "operation_type": snapshot["door"]["operation_type"],
                }
            ],
            "damage_scope": {
                "door_removed": True,
                "fill_removed": True,
                "opening_removed": not preserve_opening,
                "void_removed": not preserve_opening,
            },
            "counts": {"before": before_counts, "after": after_counts},
            "checks": {
                "schema_preserved": reopened.schema == "IFC2X3",
                "source_unchanged": _sha256(source) == source_sha256,
                "door_removed": _optional_guid(reopened, door_global_id) is None,
                "opening_preservation_matches_mode": (
                    (surviving_opening is not None) == preserve_opening
                ),
            },
        }
        atomic_write_text(
            stage / "mutation_manifest.private.json", _render_json(manifest)
        )
        atomic_write_text(stage / "mutation_report.json", _render_json(report))
        os.replace(stage, output)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return {
        "valid": True,
        "mutation_type": mode,
        "source_sha256": source_sha256,
        "damaged_sha256": damaged_sha256,
        "door": snapshot["door"],
        "opening": snapshot["opening"],
        "wall": snapshot["wall"],
        "artifacts": {
            "damaged_ifc": "damaged.ifc",
            "private_manifest": "mutation_manifest.private.json",
            "report": "mutation_report.json",
        },
    }


def remove_doors_batch(
    *,
    source_path: Path | str,
    output_dir: Path | str,
    door_global_ids: list[str] | tuple[str, ...],
    preserve_openings: bool = True,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Remove several Door fill chains in one in-memory mutation and one write."""

    source = Path(source_path).resolve()
    output = Path(output_dir).resolve()
    source_sha256 = _sha256(source)
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise ValueError("SOURCE_IFC_FINGERPRINT_MISMATCH")
    if output.exists():
        raise FileExistsError(f"mutation output already exists: {output}")
    normalized_ids = tuple(str(value) for value in door_global_ids)
    if not normalized_ids:
        raise ValueError("DOOR_BATCH_EMPTY")
    if len(set(normalized_ids)) != len(normalized_ids):
        raise ValueError("DOOR_BATCH_DUPLICATE_TARGET")

    model = ifcopenshell.open(str(source))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    records: list[dict[str, Any]] = []
    opening_ids: set[str] = set()
    doors: list[Any] = []
    openings: list[Any] = []
    for door_global_id in normalized_ids:
        door = _optional_guid(model, door_global_id)
        if door is None or not door.is_a("IfcDoor"):
            raise ValueError(f"DOOR_NOT_FOUND:{door_global_id}")
        if len(door.FillsVoids) != 1:
            raise ValueError(f"DOOR_FILL_CHAIN_INVALID:{door_global_id}")
        opening = door.FillsVoids[0].RelatingOpeningElement
        if len(opening.VoidsElements) != 1:
            raise ValueError(f"DOOR_OPENING_HOST_INVALID:{door_global_id}")
        wall = opening.VoidsElements[0].RelatingBuildingElement
        if not wall.is_a("IfcWall"):
            raise ValueError(f"DOOR_HOST_UNSUPPORTED:{door_global_id}")
        opening_id = str(opening.GlobalId)
        if opening_id in opening_ids:
            raise ValueError(f"DOOR_BATCH_SHARED_OPENING:{opening_id}")
        opening_ids.add(opening_id)
        doors.append(door)
        openings.append(opening)
        records.append(_door_snapshot(door, opening, wall))

    before_counts = _counts(model)
    owner_history_snapshot = _snapshot_owner_history(model)
    for door in doors:
        remove_product(model, product=door)
    if not preserve_openings:
        for opening in openings:
            remove_product(model, product=opening)
    _restore_owner_history(model, owner_history_snapshot)
    _canonicalize_modified_relationship_sets(model)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        damaged_path = stage / "damaged.ifc"
        model.write(str(damaged_path))
        reopened = ifcopenshell.open(str(damaged_path))
        for record in records:
            door_id = record["door"]["global_id"]
            opening_id = record["opening"]["global_id"]
            if _optional_guid(reopened, door_id) is not None:
                raise ValueError(f"DOOR_MUTATION_REMOVE_FAILED:{door_id}")
            surviving_opening = _optional_guid(reopened, opening_id)
            if preserve_openings:
                if surviving_opening is None:
                    raise ValueError(
                        f"DOOR_MUTATION_OPENING_NOT_PRESERVED:{opening_id}"
                    )
                if len(surviving_opening.HasFillings) != 0:
                    raise ValueError(
                        f"DOOR_MUTATION_OPENING_NOT_EMPTY:{opening_id}"
                    )
                if len(surviving_opening.VoidsElements) != 1:
                    raise ValueError(
                        f"DOOR_MUTATION_VOID_NOT_PRESERVED:{opening_id}"
                    )
            elif surviving_opening is not None:
                raise ValueError(
                    f"DOOR_MUTATION_OPENING_REMOVE_FAILED:{opening_id}"
                )
        after_counts = _counts(reopened)
        damaged_sha256 = _sha256(damaged_path)
        mode = (
            "remove_doors_preserve_openings_batch"
            if preserve_openings
            else "remove_doors_and_openings_batch"
        )
        manifest = {
            "schema_version": DOOR_BATCH_MUTATION_SCHEMA_VERSION,
            "mutation_type": mode,
            "source": {
                "path": source.as_posix(),
                "schema": "IFC2X3",
                "size_bytes": source.stat().st_size,
                "sha256": source_sha256,
            },
            "targets": records,
            "counts": {"before": before_counts, "after": after_counts},
            "damaged_ifc": {"path": "damaged.ifc", "sha256": damaged_sha256},
        }
        report = {
            "schema_version": (
                "text2ifc/ifc-repair-door-mutation-report/0.2"
            ),
            "valid": True,
            "mutation_type": mode,
            "source_sha256": source_sha256,
            "damaged_sha256": damaged_sha256,
            "removed_doors": [
                {
                    "global_id": item["door"]["global_id"],
                    "name": item["door"]["name"],
                    "type_global_id": item["door"]["type_global_id"],
                    "type_name": item["door"]["type_name"],
                    "operation_type": item["door"]["operation_type"],
                }
                for item in records
            ],
            "damage_scope": {
                "door_count": len(records),
                "doors_removed": True,
                "fills_removed": True,
                "openings_removed": not preserve_openings,
                "voids_removed": not preserve_openings,
            },
            "counts": {"before": before_counts, "after": after_counts},
            "checks": {
                "schema_preserved": reopened.schema == "IFC2X3",
                "source_unchanged": _sha256(source) == source_sha256,
                "all_doors_removed": all(
                    _optional_guid(reopened, item["door"]["global_id"]) is None
                    for item in records
                ),
                "opening_preservation_matches_mode": all(
                    (
                        _optional_guid(
                            reopened, item["opening"]["global_id"]
                        )
                        is not None
                    )
                    == preserve_openings
                    for item in records
                ),
                "single_model_write": True,
            },
        }
        atomic_write_text(
            stage / "mutation_manifest.private.json", _render_json(manifest)
        )
        atomic_write_text(stage / "mutation_report.json", _render_json(report))
        os.replace(stage, output)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise

    return {
        "valid": True,
        "mutation_type": mode,
        "target_count": len(records),
        "source_sha256": source_sha256,
        "damaged_sha256": damaged_sha256,
        "targets": records,
        "artifacts": {
            "damaged_ifc": "damaged.ifc",
            "private_manifest": "mutation_manifest.private.json",
            "report": "mutation_report.json",
        },
    }


def _door_snapshot(door: Any, opening: Any, wall: Any) -> dict[str, Any]:
    types = [
        relation.RelatingType
        for relation in door.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(types) > 1:
        raise ValueError("DOOR_TYPE_MAPPING_AMBIGUOUS")
    door_type = types[0] if types else None
    storeys = [
        relation.RelatingStructure
        for relation in door.ContainedInStructure
        if relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    return {
        "door": {
            "global_id": str(door.GlobalId),
            "name": None if door.Name is None else str(door.Name),
            "overall_width_mm": (
                None if door.OverallWidth is None else float(door.OverallWidth)
            ),
            "overall_height_mm": (
                None if door.OverallHeight is None else float(door.OverallHeight)
            ),
            "type_global_id": (
                None if door_type is None else str(door_type.GlobalId)
            ),
            "type_name": (
                None
                if door_type is None or door_type.Name is None
                else str(door_type.Name)
            ),
            "operation_type": (
                None
                if door_type is None
                else str(getattr(door_type, "OperationType", None))
            ),
        },
        "opening": {
            "global_id": str(opening.GlobalId),
            "name": None if opening.Name is None else str(opening.Name),
            "dimensions_mm": _opening_representation_summary(opening),
        },
        "wall": {
            "global_id": str(wall.GlobalId),
            "name": None if wall.Name is None else str(wall.Name),
            "ifc_class": wall.is_a(),
        },
        "storey": {
            "global_id": str(storeys[0].GlobalId) if len(storeys) == 1 else None,
            "name": (
                None
                if len(storeys) != 1 or storeys[0].Name is None
                else str(storeys[0].Name)
            ),
        },
    }


def _optional_guid(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


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


def _window_repair_properties(window: Any) -> list[dict[str, Any]]:
    """Expose every supported occurrence-direct scalar fact for user authorization.

    Type inheritance cannot recover occurrence-only facts.  The private mutation
    fixture therefore projects each ``IfcPropertySingleValue`` into the public
    request, while deliberately excluding inherited Type properties and
    unsupported complex/list/table values.
    """

    properties: list[dict[str, Any]] = []
    for relation in getattr(window, "IsDefinedBy", ()):
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        property_set = relation.RelatingPropertyDefinition
        if not property_set.is_a("IfcPropertySet"):
            continue
        for prop in property_set.HasProperties:
            if (
                not prop.is_a("IfcPropertySingleValue")
                or prop.NominalValue is None
            ):
                continue
            properties.append(
                {
                    "set_name": str(property_set.Name),
                    "property_name": str(prop.Name),
                    "value": prop.NominalValue.wrappedValue,
                    "requested_value_type": prop.NominalValue.is_a(),
                    "unit": _property_unit_token(window, prop),
                }
            )
    return sorted(
        properties,
        key=lambda item: (item["set_name"], item["property_name"]),
    )


def _window_repair_quantities(window: Any) -> list[dict[str, Any]]:
    """Expose occurrence-direct quantities so the rendered request can authorize them."""

    return _occurrence_repair_quantities(
        window,
        scope="window_occurrence",
    )


def _opening_repair_quantities(opening: Any) -> list[dict[str, Any]]:
    """Expose the damaged Opening quantities required for full replication."""

    return _occurrence_repair_quantities(
        opening,
        scope="opening_occurrence",
    )


def _occurrence_repair_quantities(
    entity: Any,
    *,
    scope: str,
) -> list[dict[str, Any]]:
    unit_tokens = {
        "IfcQuantityLength": _project_unit_token(entity.file, "LENGTHUNIT"),
        "IfcQuantityArea": _project_unit_token(entity.file, "AREAUNIT"),
    }
    quantities: list[dict[str, Any]] = []
    for relation in getattr(entity, "IsDefinedBy", ()):
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        quantity_set = relation.RelatingPropertyDefinition
        if not quantity_set.is_a("IfcElementQuantity"):
            continue
        for quantity in quantity_set.Quantities:
            if quantity.is_a("IfcQuantityLength"):
                value = quantity.LengthValue
            elif quantity.is_a("IfcQuantityArea"):
                value = quantity.AreaValue
            else:
                continue
            quantities.append(
                {
                    "set_name": str(quantity_set.Name),
                    "quantity_name": str(quantity.Name),
                    "value": float(value),
                    "value_type": quantity.is_a(),
                    "unit": unit_tokens[quantity.is_a()],
                    "scope": scope,
                }
            )
    return sorted(
        quantities,
        key=lambda item: (item["set_name"], item["quantity_name"]),
    )


def _project_unit_token(model: Any, unit_type: str) -> str | None:
    scale = float(ifcopenshell.util.unit.calculate_unit_scale(model, unit_type))
    candidates = {
        "LENGTHUNIT": ((1.0, "m"), (1e-2, "cm"), (1e-3, "mm")),
        "AREAUNIT": ((1.0, "m2"), (1e-4, "cm2"), (1e-6, "mm2")),
        "VOLUMEUNIT": ((1.0, "m3"), (1e-6, "cm3"), (1e-9, "mm3")),
    }[unit_type]
    return next(
        (
            token
            for expected, token in candidates
            if abs(scale - expected) <= 1e-12
        ),
        None,
    )


def _property_unit_token(window: Any, prop: Any) -> str | None:
    explicit = getattr(prop, "Unit", None)
    if explicit is not None and explicit.is_a("IfcSIUnit"):
        name = str(explicit.Name)
        prefix = None if explicit.Prefix is None else str(explicit.Prefix)
        return {
            ("METRE", None): "m",
            ("METRE", "CENTI"): "cm",
            ("METRE", "MILLI"): "mm",
            ("SQUARE_METRE", None): "m2",
            ("SQUARE_METRE", "CENTI"): "cm2",
            ("SQUARE_METRE", "MILLI"): "mm2",
            ("CUBIC_METRE", None): "m3",
            ("CUBIC_METRE", "CENTI"): "cm3",
            ("CUBIC_METRE", "MILLI"): "mm3",
        }.get((name, prefix))
    unit_type = {
        "IfcLengthMeasure": "LENGTHUNIT",
        "IfcAreaMeasure": "AREAUNIT",
        "IfcVolumeMeasure": "VOLUMEUNIT",
    }.get(prop.NominalValue.is_a())
    return (
        None
        if unit_type is None
        else _project_unit_token(window.file, unit_type)
    )


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
