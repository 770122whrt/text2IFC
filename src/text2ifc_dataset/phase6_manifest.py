"""Split-safe Phase 6 training and evaluation manifest construction."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_MANIFEST = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
DEFAULT_SPLIT_MANIFEST = ROOT / "dataset" / "splits" / "bimnet-scene-splits.json"
DEFAULT_GOLD_MANIFEST = (
    ROOT / "dataset" / "processed" / "text2json" / "gold-set-manifest.json"
)
DEFAULT_PAIRS_DIR = ROOT / "dataset" / "processed" / "text2json" / "pairs"
DEFAULT_OUTPUT = (
    ROOT / "dataset" / "processed" / "phase6" / "training-manifest.json"
)
SCHEMA_VERSION = "text2ifc/phase6-training-manifest-v1"
SPLITS = ("train", "validation", "test")
REQUIRED_RECORD_FIELDS = (
    "record_id",
    "pair_path",
    "source_file_id",
    "source_sha256",
    "scene_family",
    "split",
    "license_status",
    "license_source",
    "approved_uses",
    "eligible_uses",
    "training_eligible",
    "target_kind",
    "formal_target_path",
    "formal_target_sha256",
    "loss_sidecar_path",
    "loss_sidecar_sha256",
    "loss_count",
    "projection_omission_count",
    "text_style",
    "template_id",
    "review_status",
)


class Phase6ManifestError(ValueError):
    """Raised when Phase 6 data would violate provenance or split policy."""


def build_phase6_manifest(
    *,
    source_manifest_path: Path | str = DEFAULT_SOURCE_MANIFEST,
    split_manifest_path: Path | str = DEFAULT_SPLIT_MANIFEST,
    gold_manifest_path: Path | str = DEFAULT_GOLD_MANIFEST,
    pairs_dir: Path | str = DEFAULT_PAIRS_DIR,
) -> dict[str, Any]:
    source_path = Path(source_manifest_path)
    split_path = Path(split_manifest_path)
    gold_path = Path(gold_manifest_path)
    pair_root = Path(pairs_dir)

    sources = _source_records(source_path)
    split_payload = _read_json(split_path)
    split_by_source = _split_assignments(split_payload)
    gold_payload = _read_json(gold_path)
    gold_records = _gold_records(gold_payload)
    pair_records = [
        record
        for split in SPLITS
        for record in _read_jsonl(pair_root / f"{split}.jsonl")
    ]

    records: list[dict[str, Any]] = []
    validated_targets: dict[str, str] = {}
    for pair in sorted(pair_records, key=lambda item: str(item.get("record_id", ""))):
        source_id = _required_string(pair, "source_file_id", "pair record")
        source = sources.get(source_id)
        _require(source is not None, f"{source_id} is absent from source manifest")
        split = _required_string(pair, "split", source_id)
        _require(split in SPLITS, f"{source_id} has invalid split {split!r}")
        expected_split = split_by_source.get(source_id)
        _require(
            expected_split is not None,
            f"{source_id} is absent from split manifest",
        )
        _require(
            split == expected_split["split"],
            f"{source_id} pair split {split} != split manifest {expected_split['split']}",
        )
        scene_family = _required_string(pair, "scene_family", source_id)
        _require(
            scene_family == expected_split["scene_family"],
            f"{source_id} scene_family does not match split manifest",
        )
        _require(
            scene_family == source["scene_family"],
            f"{source_id} scene_family does not match source manifest",
        )
        source_sha256 = _required_sha256(pair, "source_sha256", source_id)
        _require(
            source_sha256 == source["sha256"],
            f"{source_id} source_sha256 does not match source manifest",
        )

        gold = gold_records.get(source_id)
        _require(gold is not None, f"{source_id} is absent from gold manifest")
        _require(gold.get("target_kind") == "formal", f"{source_id} target is not formal")
        _require(gold.get("split") == split, f"{source_id} gold split does not match")
        _require(
            gold.get("scene_family") == scene_family,
            f"{source_id} gold scene_family does not match",
        )
        formal_target_path = _required_string(
            gold, "target_json_path", f"{source_id} gold record"
        )
        _require(
            pair.get("target_json_path") == formal_target_path,
            f"{source_id} pair target path does not match gold manifest",
        )
        if formal_target_path not in validated_targets:
            validated_targets[formal_target_path] = _validated_target_sha256(
                _resolve(formal_target_path)
            )
        target_sha256 = validated_targets[formal_target_path]
        _require(
            pair.get("target_sha256") == target_sha256,
            f"{source_id} formal target hash does not match pair record",
        )

        sidecar_path = _required_string(
            gold, "sidecar_path", f"{source_id} gold record"
        )
        sidecar_file = _resolve(sidecar_path)
        sidecar = _read_json(sidecar_file)
        for field, expected in (
            ("source_file_id", source_id),
            ("source_sha256", source_sha256),
            ("scene_family", scene_family),
            ("split", split),
        ):
            _require(
                sidecar.get(field) == expected,
                f"{source_id} loss sidecar {field} does not match",
            )

        approved_uses = _string_list(source.get("approved_uses"), f"{source_id} approved_uses")
        license_status = _required_string(source, "license", source_id)
        source_training_eligible = source.get("training_eligible") is True
        training_eligible = (
            split == "train"
            and source_training_eligible
            and "local-model-training" in approved_uses
        )
        eligible_uses = (
            ["local-model-training", "model-evaluation"]
            if training_eligible
            else ["model-evaluation"]
        )
        records.append(
            {
                "record_id": _required_string(pair, "record_id", source_id),
                "pair_path": _relative(pair_root / f"{split}.jsonl"),
                "source_file_id": source_id,
                "source_sha256": source_sha256,
                "scene_family": scene_family,
                "split": split,
                "license_status": license_status,
                "license_source": _relative(source_path),
                "approved_uses": approved_uses,
                "eligible_uses": eligible_uses,
                "training_eligible": training_eligible,
                "target_kind": "formal",
                "formal_target_path": formal_target_path,
                "formal_target_sha256": target_sha256,
                "loss_sidecar_path": sidecar_path,
                "loss_sidecar_sha256": _file_sha256(sidecar_file),
                "loss_count": _required_nonnegative_int(sidecar, "loss_count", source_id),
                "projection_omission_count": _required_nonnegative_int(
                    sidecar, "projection_omission_count", source_id
                ),
                "text_style": _required_string(pair, "text_style", source_id),
                "template_id": _required_string(pair, "template_id", source_id),
                "review_status": _required_string(pair, "review_status", source_id),
            }
        )

    split_counts = Counter(record["split"] for record in records)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_artifacts": {
            "source_manifest": _relative(source_path),
            "split_manifest": _relative(split_path),
            "gold_manifest": _relative(gold_path),
            "pairs_dir": _relative(pair_root),
        },
        "authorization_scope": split_payload.get("authorization_scope", {}),
        "policy": {
            "training_split": "train-only",
            "evaluation_splits": ["validation", "test"],
            "formal_targets_only": True,
            "loss_sidecars_required": True,
            "scene_family_isolation": True,
            "redistribution_inferred": False,
        },
        "counts": {
            "records": len(records),
            "by_split": dict(sorted(split_counts.items())),
            "training_eligible": sum(
                1 for record in records if record["training_eligible"]
            ),
            "formal_targets": len(
                {record["formal_target_path"] for record in records}
            ),
            "source_files": len({record["source_file_id"] for record in records}),
            "scene_families": len({record["scene_family"] for record in records}),
        },
        "records": records,
    }
    validate_phase6_manifest(payload)
    return payload


def validate_phase6_manifest(
    payload: Mapping[str, Any],
    *,
    root: Path | str = ROOT,
) -> None:
    _require(isinstance(payload, Mapping), "manifest must be an object")
    _require(
        payload.get("schema_version") == SCHEMA_VERSION,
        f"schema_version must be {SCHEMA_VERSION}",
    )
    records = payload.get("records")
    _require(isinstance(records, list) and records, "records must be a non-empty list")
    resolved_root = Path(root)
    seen_ids: set[str] = set()
    family_owner: dict[str, str] = {}
    validated_targets: set[str] = set()
    for index, record in enumerate(records):
        _require(isinstance(record, Mapping), f"record {index} must be an object")
        missing = [field for field in REQUIRED_RECORD_FIELDS if field not in record]
        _require(
            not missing,
            f"record {index} missing required fields: {', '.join(missing)}",
        )
        record_id = _required_string(record, "record_id", f"record {index}")
        _require(record_id not in seen_ids, f"duplicate record_id: {record_id}")
        seen_ids.add(record_id)
        split = _required_string(record, "split", record_id)
        _require(split in SPLITS, f"{record_id} has invalid split")
        scene_family = _required_string(record, "scene_family", record_id)
        previous_split = family_owner.get(scene_family)
        _require(
            previous_split in (None, split),
            f"scene_family {scene_family} appears in both {previous_split} and {split}",
        )
        family_owner[scene_family] = split
        _required_sha256(record, "source_sha256", record_id)
        _required_sha256(record, "formal_target_sha256", record_id)
        _required_sha256(record, "loss_sidecar_sha256", record_id)
        _required_string(record, "license_status", record_id)
        _required_string(record, "license_source", record_id)
        _string_list(record.get("approved_uses"), f"{record_id} approved_uses")
        eligible_uses = _string_list(
            record.get("eligible_uses"), f"{record_id} eligible_uses"
        )
        _require(record.get("target_kind") == "formal", f"{record_id} is not formal")
        training_eligible = record.get("training_eligible")
        _require(
            isinstance(training_eligible, bool),
            f"{record_id} training_eligible must be boolean",
        )
        if split == "train":
            _require(
                training_eligible is True,
                f"{record_id} train record must be training_eligible",
            )
            _require(
                "local-model-training" in eligible_uses,
                f"{record_id} train eligible_uses missing local-model-training",
            )
        else:
            _require(
                training_eligible is False,
                f"{record_id} {split} record cannot be training_eligible",
            )
            _require(
                eligible_uses == ["model-evaluation"],
                f"{record_id} {split} eligible_uses must be model-evaluation only",
            )
        target_path = _required_string(record, "formal_target_path", record_id)
        sidecar_path = _required_string(record, "loss_sidecar_path", record_id)
        target_file = _resolve_from(resolved_root, target_path)
        sidecar_file = _resolve_from(resolved_root, sidecar_path)
        _require(target_file.is_file(), f"{record_id} formal_target_path does not exist")
        _require(sidecar_file.is_file(), f"{record_id} loss_sidecar_path does not exist")
        _require(
            _file_sha256(sidecar_file) == record["loss_sidecar_sha256"],
            f"{record_id} loss sidecar hash mismatch",
        )
        if target_path not in validated_targets:
            _require(
                _validated_target_sha256(target_file)
                == record["formal_target_sha256"],
                f"{record_id} formal target hash mismatch",
            )
            validated_targets.add(target_path)
        _required_nonnegative_int(record, "loss_count", record_id)
        _required_nonnegative_int(record, "projection_omission_count", record_id)

    expected_counts = {
        "records": len(records),
        "by_split": dict(
            sorted(Counter(record["split"] for record in records).items())
        ),
        "training_eligible": sum(
            1 for record in records if record["training_eligible"]
        ),
        "formal_targets": len(
            {record["formal_target_path"] for record in records}
        ),
        "source_files": len({record["source_file_id"] for record in records}),
        "scene_families": len({record["scene_family"] for record in records}),
    }
    _require(payload.get("counts") == expected_counts, "manifest counts do not match")


def write_phase6_manifest(
    output_path: Path | str = DEFAULT_OUTPUT,
    **build_kwargs: Any,
) -> dict[str, Any]:
    payload = build_phase6_manifest(**build_kwargs)
    _atomic_write(Path(output_path), render_manifest(payload))
    return payload


def check_phase6_manifest(
    output_path: Path | str = DEFAULT_OUTPUT,
    **build_kwargs: Any,
) -> dict[str, Any]:
    path = Path(output_path)
    _require(path.is_file(), f"missing Phase 6 manifest: {_relative(path)}")
    expected = build_phase6_manifest(**build_kwargs)
    actual = path.read_text(encoding="utf-8")
    _require(actual == render_manifest(expected), f"manifest drift: {_relative(path)}")
    return expected


def render_manifest(payload: Any) -> str:
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


def _source_records(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in _read_jsonl(path):
        source_id = _required_string(record, "id", "source record")
        _require(source_id not in result, f"duplicate source id: {source_id}")
        _required_sha256(record, "sha256", source_id)
        _required_string(record, "scene_family", source_id)
        _required_string(record, "license", source_id)
        _string_list(record.get("approved_uses"), f"{source_id} approved_uses")
        _require(
            record.get("training_eligible") is True,
            f"{source_id} source is not training_eligible",
        )
        result[source_id] = record
    return result


def _split_assignments(payload: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    splits = payload.get("splits")
    _require(isinstance(splits, Mapping), "split manifest missing splits")
    result: dict[str, dict[str, str]] = {}
    family_owner: dict[str, str] = {}
    for split in SPLITS:
        families = splits.get(split)
        _require(isinstance(families, list), f"split manifest missing {split}")
        for family in families:
            _require(isinstance(family, Mapping), f"{split} family must be object")
            scene_family = _required_string(family, "scene_family", split)
            previous = family_owner.get(scene_family)
            _require(
                previous is None,
                f"scene_family {scene_family} appears in both {previous} and {split}",
            )
            family_owner[scene_family] = split
            file_ids = family.get("file_ids")
            _require(
                isinstance(file_ids, list) and file_ids,
                f"{scene_family} file_ids missing",
            )
            for source_id in file_ids:
                _require(
                    isinstance(source_id, str) and source_id,
                    f"{scene_family} has invalid file_id",
                )
                _require(source_id not in result, f"duplicate split source: {source_id}")
                result[source_id] = {
                    "split": split,
                    "scene_family": scene_family,
                }
    return result


def _gold_records(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    records = payload.get("records")
    _require(isinstance(records, list), "gold manifest records missing")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        _require(isinstance(record, dict), "gold record must be object")
        source_id = _required_string(record, "source_file_id", "gold record")
        _require(source_id not in result, f"duplicate gold source: {source_id}")
        result[source_id] = record
    return result


def _read_json(path: Path) -> dict[str, Any]:
    _require(path.is_file(), f"missing JSON file: {_relative(path)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Phase6ManifestError(f"invalid JSON in {_relative(path)}") from exc
    _require(isinstance(value, dict), f"expected JSON object in {_relative(path)}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    _require(path.is_file(), f"missing JSONL file: {_relative(path)}")
    records = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Phase6ManifestError(
                f"invalid JSONL record {line_number} in {_relative(path)}"
            ) from exc
        _require(isinstance(record, dict), f"JSONL record {line_number} is not object")
        records.append(record)
    _require(records, f"JSONL file has no records: {_relative(path)}")
    return records


def _required_string(
    value: Mapping[str, Any],
    field: str,
    label: str,
) -> str:
    result = value.get(field)
    _require(
        isinstance(result, str) and result.strip(),
        f"{label} missing {field}",
    )
    return result


def _required_sha256(
    value: Mapping[str, Any],
    field: str,
    label: str,
) -> str:
    result = _required_string(value, field, label)
    _require(
        len(result) == 64 and all(character in "0123456789abcdef" for character in result),
        f"{label} has invalid {field}",
    )
    return result


def _required_nonnegative_int(
    value: Mapping[str, Any],
    field: str,
    label: str,
) -> int:
    result = value.get(field)
    _require(
        isinstance(result, int) and not isinstance(result, bool) and result >= 0,
        f"{label} has invalid {field}",
    )
    return result


def _string_list(value: Any, label: str) -> list[str]:
    _require(
        isinstance(value, list)
        and all(isinstance(item, str) and item for item in value),
        f"{label} must be a string list",
    )
    return sorted(set(value))


def _canonical_sha256(payload: Any) -> str:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validated_target_sha256(path: Path) -> str:
    stat = path.stat()
    return _cached_validated_target_sha256(
        str(path.resolve()),
        stat.st_mtime_ns,
        stat.st_size,
    )


@lru_cache(maxsize=256)
def _cached_validated_target_sha256(
    resolved_path: str,
    mtime_ns: int,
    size: int,
) -> str:
    del mtime_ns, size
    target = _read_json(Path(resolved_path))
    issues = validate_v2_document(target)
    if issues:
        first = issues[0]
        raise Phase6ManifestError(
            f"{_relative(Path(resolved_path))} formal target invalid: "
            f"{first.code} at {first.path}"
        )
    return _canonical_sha256(target)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(path: str) -> Path:
    return _resolve_from(ROOT, path)


def _resolve_from(root: Path, path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Phase6ManifestError(message)
