"""Scene-family split helpers for Phase 3 Text-to-JSON data."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
DEFAULT_FAMILIES_PATH = (
    ROOT / "dataset" / "processed" / "bim-json-2.0" / "scene-families.json"
)
DEFAULT_OUTPUT_PATH = ROOT / "dataset" / "splits" / "bimnet-scene-splits.json"
SCHEMA_VERSION = "text2ifc/bimnet-scene-splits-v1"
SCENE_FAMILIES_SCHEMA_VERSION = "text2ifc/scene-families-v1"
POLICY = "scene-family-shuffle-70-15-15-v1"
DEFAULT_SEED = 20260614
CREATED_AT = "2026-06-14"
SPLIT_NAMES = ("train", "validation", "test")
REQUIRED_APPROVED_USES = frozenset(
    {"dataset-construction", "local-model-training"}
)


class SplitManifestError(ValueError):
    """Raised when a split manifest or source manifest is unsafe."""


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SplitManifestError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SplitManifestError(f"failed to read JSON from {_relative(path)}") from exc
    except json.JSONDecodeError as exc:
        raise SplitManifestError(
            f"invalid JSON in {_relative(path)} at line {exc.lineno}"
        ) from exc
    _require(isinstance(payload, dict), f"expected object in {_relative(path)}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SplitManifestError(f"failed to read JSONL from {_relative(path)}") from exc
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SplitManifestError(
                f"invalid JSONL record {index} in {_relative(path)}"
            ) from exc
        _require(
            isinstance(record, dict),
            f"expected object record {index} in {_relative(path)}",
        )
        records.append(record)
    _require(records != [], f"manifest {_relative(path)} has no records")
    return records


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value.lower())


def _require_unique(values: Iterable[str], *, label: str) -> None:
    seen: set[str] = set()
    for value in values:
        _require(value not in seen, f"duplicate {label}: {value}")
        seen.add(value)


def load_bimnet_manifest(path: Path | str) -> list[dict[str, Any]]:
    manifest_path = Path(path)
    records = _read_jsonl(manifest_path)
    ids: list[str] = []
    for index, record in enumerate(records, start=1):
        record_id = record.get("id")
        _require(isinstance(record_id, str) and record_id, f"record {index} missing id")
        ids.append(record_id)

        sha256 = record.get("sha256")
        _require(_is_sha256(sha256), f"{record_id} has invalid or missing sha256")

        schema = record.get("declared_schema")
        _require(schema == "IFC2X3", f"{record_id} declared_schema must be IFC2X3")

        _require(
            record.get("training_eligible") is True,
            f"{record_id} is not training_eligible",
        )

        approved_uses = record.get("approved_uses")
        _require(
            isinstance(approved_uses, list)
            and all(isinstance(value, str) for value in approved_uses),
            f"{record_id} approved_uses must be a list of strings",
        )
        missing_uses = sorted(REQUIRED_APPROVED_USES - set(approved_uses))
        _require(
            not missing_uses,
            f"{record_id} missing approved uses: {', '.join(missing_uses)}",
        )

        scene_family = record.get("scene_family")
        _require(
            isinstance(scene_family, str) and scene_family,
            f"{record_id} missing scene_family",
        )
        _require(
            isinstance(record.get("local_path"), str) and record["local_path"],
            f"{record_id} missing local_path",
        )

    _require_unique(ids, label="manifest id")
    return sorted(records, key=lambda item: item["id"])


def load_scene_families(path: Path | str) -> dict[str, Any]:
    families_path = Path(path)
    payload = _read_json(families_path)
    _require(
        payload.get("schema_version") == SCENE_FAMILIES_SCHEMA_VERSION,
        f"{_relative(families_path)} schema_version must be {SCENE_FAMILIES_SCHEMA_VERSION}",
    )
    _require(
        payload.get("split_assignment") is None,
        f"{_relative(families_path)} must not contain precomputed split_assignment",
    )
    families = payload.get("families")
    _require(isinstance(families, list) and families, "scene families are missing")

    scene_family_names: list[str] = []
    file_ids: list[str] = []
    for index, family_record in enumerate(families, start=1):
        _require(isinstance(family_record, dict), f"family record {index} is not an object")
        scene_family = family_record.get("scene_family")
        _require(
            isinstance(scene_family, str) and scene_family,
            f"family record {index} missing scene_family",
        )
        scene_family_names.append(scene_family)
        family_file_ids = family_record.get("file_ids")
        _require(
            isinstance(family_file_ids, list)
            and family_file_ids
            and all(isinstance(file_id, str) and file_id for file_id in family_file_ids),
            f"{scene_family} file_ids must be a non-empty string list",
        )
        file_ids.extend(family_file_ids)

    _require_unique(scene_family_names, label="scene_family")
    _require_unique(file_ids, label="scene family file_id")
    return payload


def _family_to_file_ids(families_payload: dict[str, Any]) -> dict[str, list[str]]:
    return {
        family_record["scene_family"]: sorted(family_record["file_ids"])
        for family_record in families_payload["families"]
    }


def _manifest_by_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in records}


def _validate_manifest_family_join(
    manifest_records: list[dict[str, Any]], families_payload: dict[str, Any]
) -> dict[str, list[str]]:
    family_to_file_ids = _family_to_file_ids(families_payload)
    manifest_records_by_id = _manifest_by_id(manifest_records)
    family_file_ids = {
        file_id
        for file_ids in family_to_file_ids.values()
        for file_id in file_ids
    }
    manifest_file_ids = set(manifest_records_by_id)
    _require(
        family_file_ids == manifest_file_ids,
        "scene family file IDs must exactly match the BIMNet manifest file IDs",
    )

    for scene_family, file_ids in family_to_file_ids.items():
        for file_id in file_ids:
            manifest_family = manifest_records_by_id[file_id]["scene_family"]
            _require(
                manifest_family == scene_family,
                f"{file_id} has scene_family {manifest_family}, expected {scene_family}",
            )
    return family_to_file_ids


def _stable_shuffle(values: Iterable[str], *, seed: int) -> list[str]:
    return sorted(
        values,
        key=lambda value: (
            hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest(),
            value,
        ),
    )


def _split_family_names(family_names: list[str], *, seed: int) -> dict[str, list[str]]:
    _require(len(family_names) >= 3, "at least three scene families are required")
    shuffled = _stable_shuffle(family_names, seed=seed)
    validation_count = max(1, round(len(shuffled) * 0.15))
    test_count = max(1, round(len(shuffled) * 0.15))
    train_count = len(shuffled) - validation_count - test_count
    _require(train_count > 0, "train split must contain at least one scene family")
    assignments = {
        "train": sorted(shuffled[:train_count]),
        "validation": sorted(shuffled[train_count : train_count + validation_count]),
        "test": sorted(shuffled[train_count + validation_count :]),
    }
    for split_name in SPLIT_NAMES:
        _require(assignments[split_name], f"{split_name} split is empty")
    return assignments


def _build_split_records(
    assigned_families: dict[str, list[str]],
    family_to_file_ids: dict[str, list[str]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        split_name: [
            {
                "scene_family": scene_family,
                "file_ids": family_to_file_ids[scene_family],
            }
            for scene_family in assigned_families[split_name]
        ]
        for split_name in SPLIT_NAMES
    }


def _build_counts(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    family_counts = {
        split_name: len(split_records)
        for split_name, split_records in splits.items()
    }
    file_counts = {
        split_name: sum(len(record["file_ids"]) for record in split_records)
        for split_name, split_records in splits.items()
    }
    family_counts["total"] = sum(family_counts.values())
    file_counts["total"] = sum(file_counts.values())
    return {"families": family_counts, "files": file_counts}


def build_scene_family_splits(
    manifest_path: Path | str,
    families_path: Path | str,
    *,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    families_file = Path(families_path)
    manifest_records = load_bimnet_manifest(manifest_file)
    families_payload = load_scene_families(families_file)
    family_to_file_ids = _validate_manifest_family_join(
        manifest_records, families_payload
    )
    assigned_families = _split_family_names(
        sorted(family_to_file_ids),
        seed=seed,
    )
    splits = _build_split_records(assigned_families, family_to_file_ids)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_manifest": _relative(manifest_file),
        "source_scene_families": _relative(families_file),
        "seed": seed,
        "policy": POLICY,
        "created_at": CREATED_AT,
        "authorization_scope": {
            "source": "Matterport3D/BIMNet",
            "license": "user-authorized-local-use",
            "redistribution_inferred": False,
            "required_approved_uses": sorted(REQUIRED_APPROVED_USES),
        },
        "counts": _build_counts(splits),
        "splits": splits,
    }
    check_scene_family_splits(payload)
    return payload


def check_scene_family_splits(payload: dict[str, Any]) -> None:
    _require(isinstance(payload, dict), "split payload must be an object")
    _require(
        payload.get("schema_version") == SCHEMA_VERSION,
        f"schema_version must be {SCHEMA_VERSION}",
    )
    splits = payload.get("splits")
    _require(isinstance(splits, dict), "splits must be an object")
    _require(set(splits) == set(SPLIT_NAMES), "splits must contain train, validation, test")

    family_owner: dict[str, str] = {}
    file_owner: dict[str, str] = {}
    family_counts: dict[str, int] = {}
    file_counts: dict[str, int] = {}
    for split_name in SPLIT_NAMES:
        split_records = splits[split_name]
        _require(isinstance(split_records, list), f"{split_name} must be a list")
        family_counts[split_name] = 0
        file_counts[split_name] = 0
        for family_record in split_records:
            _require(
                isinstance(family_record, dict),
                f"{split_name} contains a non-object family record",
            )
            scene_family = family_record.get("scene_family")
            _require(
                isinstance(scene_family, str) and scene_family,
                f"{split_name} record missing scene_family",
            )
            previous_split = family_owner.get(scene_family)
            _require(
                previous_split is None,
                f"scene_family {scene_family} appears in both {previous_split} and {split_name}",
            )
            family_owner[scene_family] = split_name
            family_counts[split_name] += 1

            file_ids = family_record.get("file_ids")
            _require(
                isinstance(file_ids, list)
                and file_ids
                and all(isinstance(file_id, str) and file_id for file_id in file_ids),
                f"{scene_family} file_ids must be a non-empty string list",
            )
            _require_unique(file_ids, label=f"{scene_family} file_id")
            for file_id in file_ids:
                previous_file_split = file_owner.get(file_id)
                _require(
                    previous_file_split is None,
                    f"file_id {file_id} appears in both {previous_file_split} and {split_name}",
                )
                file_owner[file_id] = split_name
            file_counts[split_name] += len(file_ids)

    for split_name in SPLIT_NAMES:
        _require(family_counts[split_name] > 0, f"{split_name} split is empty")

    family_counts["total"] = sum(family_counts.values())
    file_counts["total"] = sum(file_counts.values())
    expected_counts = {"families": family_counts, "files": file_counts}
    _require(payload.get("counts") == expected_counts, "split counts do not match payload")


def render_json(payload: Any) -> str:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def expected_split_manifest_text(
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    families_path: Path | str = DEFAULT_FAMILIES_PATH,
    seed: int = DEFAULT_SEED,
) -> str:
    return render_json(
        build_scene_family_splits(manifest_path, families_path, seed=seed)
    )


def write_split_manifest(
    output_path: Path | str = DEFAULT_OUTPUT_PATH,
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    families_path: Path | str = DEFAULT_FAMILIES_PATH,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    payload = build_scene_family_splits(manifest_path, families_path, seed=seed)
    atomic_write_text(Path(output_path), render_json(payload))
    return payload


def check_split_manifest(
    output_path: Path | str = DEFAULT_OUTPUT_PATH,
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    families_path: Path | str = DEFAULT_FAMILIES_PATH,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    output_file = Path(output_path)
    if not output_file.is_file():
        raise SplitManifestError(f"missing split manifest: {_relative(output_file)}")
    expected = expected_split_manifest_text(
        manifest_path=manifest_path,
        families_path=families_path,
        seed=seed,
    )
    actual = output_file.read_text(encoding="utf-8")
    if actual != expected:
        raise SplitManifestError(f"split manifest drift: {_relative(output_file)}")
    return json.loads(actual)
