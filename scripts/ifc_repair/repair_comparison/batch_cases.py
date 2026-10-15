"""Admit dataset inputs, select two rounds, and copy a public-only projection.

This adapter reads indexes and admission metadata, and hashes opaque input bytes.
It does not parse IFC, read reference/mutation files, grant live-stage admission,
or inherit a mother's human acceptance. The returned metadata is host-side; only
``materialize_public(...)["cases"]`` describes the runnable public projection.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import stat

from .budget import budget_level_for_primary_targets
from .contracts import relative_path, safe_path, sha256


SCHEMA = "repair-comparison-batch-inputs/0.1"
PROPERTY_UNITS_REQUEST_CONVENTION = "existing-ifc-property-units/1.0"
_PROPERTY_UNITS_REQUEST_NOTICE = (
    "属性更改中的数值沿用该属性在 IFC 中的有效单位（属性未单独指定时沿用项目对应单位），"
    "保留原属性类型和单位；上述几何尺寸的毫米约定不适用于属性值。单位缺失或冲突时请提出澄清。"
)
_FULL = "text2ifc/ifc-repair-dataset-summary/1.0"
_PILOT = "text2ifc/dataset-pilot-report/1.0"
_COLLECTION = "text2ifc/dataset-pilot-collection/1.0"
_CASE_SCHEMAS = {"text2ifc/ifc-repair-dataset-case/1.0", "text2ifc/ifc-repair-dataset-case/1.1"}
_PRIMARY_CLASSES = {"door", "window", "beam", "column"}
_ADMISSION_FIELDS = (
    "schema_version", "status", "machine_validated", "human_reviewed",
    "source_unchanged", "private_identity_leakage", "information_sufficient",
    "wall_check_passed", "wall_check_applicable", "independent_mesh_check_passed",
)


def _need(condition, code):
    if not condition:
        raise ValueError(code)


def _identifier(value, code="INVALID_CASE_ID"):
    _need(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value)
          and not value.endswith(".") and value.split(".")[0].upper()
          not in {"CON", "PRN", "AUX", "NUL", *{f"COM{i}" for i in range(1, 10)},
                  *{f"LPT{i}" for i in range(1, 10)}}, code)
    return value


def _hash(value):
    _need(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "INVALID_INPUT_DIGEST")
    return value


def _count(value, code):
    _need(type(value) is int and value >= 0, code)
    return value


def _file(path):
    path = safe_path(Path(path))
    _need(path.is_file(), "INPUT_FILE_MISSING:" + str(path))
    return path


def _json(path):
    value = json.loads(_file(path).read_text(encoding="utf-8"))
    _need(isinstance(value, dict), "METADATA_OBJECT_REQUIRED")
    return value


def _level(meta):
    counts = meta.get("deleted_counts")
    _need(isinstance(counts, dict) and set(counts) <= _PRIMARY_CLASSES, "INVALID_PRIMARY_TARGET_COUNTS")
    deleted = sum(_count(n, "INVALID_PRIMARY_TARGET_COUNTS") for n in counts.values())
    properties = _count(meta.get("property_changes"), "INVALID_PRIMARY_TARGET_COUNTS")
    declared = meta.get("primary_target_count")
    if declared is not None:
        primary = _count(declared, "INVALID_PRIMARY_TARGET_COUNTS")
        _need(max(1, deleted) <= primary <= deleted + properties, "INVALID_PRIMARY_TARGET_COUNTS")
        basis = "declared_distinct_primary_targets"
    elif "property_target_count" in meta:
        property_targets = _count(meta["property_target_count"], "INVALID_PRIMARY_TARGET_COUNTS")
        _need((properties == property_targets == 0) or 1 <= property_targets <= properties,
              "INVALID_PRIMARY_TARGET_COUNTS")
        primary, basis = deleted + property_targets, "declared_distinct_property_targets"
    else:
        # Current builder recipes change at most one property on a surviving
        # product, disjoint from primary deleted products. More property writes
        # need an authored distinct-product count; operation count is insufficient.
        _need(properties <= 1, "PRIMARY_TARGET_COUNT_REQUIRED")
        primary, basis = deleted + properties, "builder_disjoint_primary_targets"
    level = budget_level_for_primary_targets(primary)
    reviewed = meta.get("level") or (meta.get("severity") if meta.get("severity") in {"S1", "S2", "S3"} else None)
    if reviewed is not None:
        _need(reviewed == level, "REVIEWED_LEVEL_MISMATCH")
    category = "mixed" if deleted and properties else "geometry" if deleted else "property"
    return level, primary, category, basis


def _completion(root):
    _need(not (root / "STOPPED-BY-USER.json").exists(), "DATASET_STOPPED")
    summary_path, index_path, build_path = (_file(root / name) for name in ("summary.json", "cases.csv", "build.json"))
    snapshots = {str(path): sha256(path) for path in (summary_path, index_path, build_path)}
    summary, build = _json(summary_path), _json(build_path)
    kind = summary.get("schema_version")
    _need(kind in {_FULL, _PILOT} and summary.get("status") == "complete", "DATASET_NOT_COMPLETE")
    _need(type(summary.get("target_cases")) is int and summary["target_cases"] > 0
          and summary.get("machine_validated_cases") == summary["target_cases"], "DATASET_INDEX_INCONSISTENT")
    expected_builds = {"text2ifc/dataset-pilot-build/1.0", _COLLECTION} if kind == _PILOT else {"text2ifc/ifc-repair-dataset-build/1.0"}
    _need(build.get("schema_version") in expected_builds, "DATASET_BUILD_MISMATCH")
    unchanged = "source_hashes_unchanged" if kind == _PILOT else "all_sources_unchanged"
    _need(summary.get(unchanged) is True, "DATASET_SOURCE_ADMISSION_INVALID")
    if "sources_manifest_sha256" in summary:
        manifest_path = _file(root / "sources.json")
        expected_manifest = _hash(summary["sources_manifest_sha256"])
        _need(sha256(manifest_path) == expected_manifest, "DATASET_SOURCE_MANIFEST_BINDING_FAILED")
        snapshots[str(manifest_path)] = expected_manifest
    if kind == _PILOT:
        _need(summary.get("unique_damaged_bytes") is True and not summary.get("worker_errors"), "DATASET_SOURCE_ADMISSION_INVALID")
    source_rows = summary.get("sources" if kind == _PILOT else "source_results")
    _need(isinstance(source_rows, list) and bool(source_rows), "DATASET_SOURCE_ADMISSION_INVALID")
    sources = {}
    for source in source_rows:
        _need(isinstance(source, dict), "DATASET_SOURCE_ADMISSION_INVALID")
        identifier = _identifier(source.get("source_id"), "INVALID_SOURCE_ID")
        _need(identifier not in sources and source.get("status") == "complete"
              and source.get("source_unchanged") is True, "DATASET_SOURCE_ADMISSION_INVALID")
        if kind == _PILOT:
            _need(source.get("source_native_passed") is True, "DATASET_SOURCE_ADMISSION_INVALID")
        sources[identifier] = {key: source[key] for key in
                               ("source_id", "status", "source_unchanged", "source_native_passed", "source_sha256")
                               if key in source}
    _need(summary.get("source_models") == len(sources), "DATASET_SOURCE_ADMISSION_INVALID")
    with index_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _need({"case_id", "path", "status", "family", "severity"} <= set(reader.fieldnames or []), "DATASET_INDEX_INCONSISTENT")
        rows = list(reader)
    _need(len(rows) >= summary["target_cases"], "DATASET_INDEX_INCONSISTENT")
    attempted = summary.get("attempted_cases")
    _need(type(attempted) is int and (attempted >= len(rows) if kind == _PILOT else attempted == len(rows)), "DATASET_INDEX_INCONSISTENT")
    if build.get("schema_version") == _COLLECTION:
        integrity_path = _file(root / "integrity.json")
        integrity = _json(integrity_path)
        snapshots[str(integrity_path)] = sha256(integrity_path)
        configuration = build.get("configuration")
        _need(isinstance(configuration, dict), "DATASET_COLLECTION_BINDING_FAILED")
        chosen = configuration.get("sources")
        _need(isinstance(chosen, list) and all(isinstance(c, dict) for c in chosen), "DATASET_COLLECTION_BINDING_FAILED")
        selected_ids = [c.get("source_id") for c in chosen]
        _need(len(selected_ids) == len(sources) and set(selected_ids) == set(sources), "DATASET_COLLECTION_BINDING_FAILED")
        per_source = configuration.get("cases_per_ifc")
        program = configuration.get("program_sha256")
        _need(type(per_source) is int and per_source > 0 and per_source * len(sources) == summary["target_cases"]
              and program == summary.get("program_sha256") == integrity.get("program_sha256"), "DATASET_COLLECTION_BINDING_FAILED")
        _hash(program)
        _need(integrity.get("schema_version") == "text2ifc/dataset-pilot-integrity/1.0"
              and integrity.get("passed") is True and integrity.get("source_hashes_unchanged") is True
              and integrity.get("distinct_source_sha256") == len(sources)
              and all(integrity.get(name) == summary["target_cases"] for name in
                      ("sealed_cases", "native_zero_findings_cases", "prompt_checked_cases", "distinct_damaged_sha256")),
              "DATASET_COLLECTION_BINDING_FAILED")
        checked_paths = integrity.get("checked_paths")
        passed_paths = [row["path"] for row in rows if row["status"] == "passed"]
        _need(isinstance(checked_paths, list) and len(checked_paths) == len(passed_paths)
              and set(checked_paths) == set(passed_paths), "DATASET_COLLECTION_BINDING_FAILED")
        for selection in chosen:
            result_path = _file(root / "sources" / selection["source_id"] / "result.json")
            expected = _hash(selection.get("result_sha256"))
            _need(sha256(result_path) == expected, "DATASET_COLLECTION_BINDING_FAILED")
            snapshots[str(result_path)] = expected
    return summary, sources, rows, snapshots


def load_candidates(dataset_root: Path) -> list[dict]:
    """Load a completed full or pilot batch, failing closed on stale bindings.

    Full indexes keep their case IDs. Pilot local IDs are retained as
    ``dataset_case_id`` and qualified by source in the host runner's ``case_id``.
    Optional ``approved_answer_card_path`` is exposed only when case metadata
    explicitly supplies ``answer_card_approved=true``; its contents are unread.
    """
    root = safe_path(Path(dataset_root))
    summary, sources, rows, snapshots = _completion(root)
    candidates, identifiers, paths = [], set(), set()
    for row in rows:
        if row.get("status") != "passed":
            _need(row.get("status") == "failed", "DATASET_INDEX_INCONSISTENT")
            continue
        relative = relative_path(row["path"])
        parts = relative.split("/")
        _need(len(parts) == 4 and parts[0] == "sources" and parts[2] == "cases", "INVALID_CASE_PATH")
        source_id = _identifier(parts[1], "INVALID_SOURCE_ID")
        _need(source_id in sources and row.get("source_id", source_id) == source_id, "DATASET_SOURCE_ADMISSION_INVALID")
        _identifier(parts[3])
        folder = safe_path(root / relative)
        _need(folder.is_relative_to(root) and str(folder).casefold() not in paths, "INVALID_CASE_PATH")
        paths.add(str(folder).casefold())
        dataset_id = _identifier(row["case_id"])
        case_id = _identifier(f"{source_id}-{dataset_id}" if dataset_id == folder.name else dataset_id)
        _need(case_id.casefold() not in identifiers, "DUPLICATE_CASE_ID")
        identifiers.add(case_id.casefold())
        metadata_path = _file(folder / "case.json")
        meta = _json(metadata_path)
        _need(meta.get("schema_version") in _CASE_SCHEMAS and meta.get("status") == "passed"
              and meta.get("machine_validated") is True and meta.get("source_unchanged") is True
              and meta.get("private_identity_leakage") is False, "CASE_ADMISSION_INVALID:" + case_id)
        for flag in ("information_sufficient", "wall_check_passed", "independent_mesh_check_passed"):
            required = meta["schema_version"] == "text2ifc/ifc-repair-dataset-case/1.1"
            _need((not required and flag not in meta) or meta.get(flag) is True, "CASE_ADMISSION_INVALID:" + case_id)
        for key in ("family", "severity", "source_sha256", "damaged_sha256", "primary_prompt", "machine_validated", "human_reviewed"):
            _need(key not in row or row[key] == str(meta.get(key)), "CASE_INDEX_METADATA_MISMATCH:" + case_id)
        for key in _PRIMARY_CLASSES:
            _need(key not in row or row[key] == str(meta.get("deleted_counts", {}).get(key, 0)),
                  "CASE_INDEX_METADATA_MISMATCH:" + case_id)
        for key in ("properties", "property_changes"):
            _need(key not in row or row[key] == str(meta.get("property_changes")), "CASE_INDEX_METADATA_MISMATCH:" + case_id)
        source_hash = _hash(meta.get("source_sha256"))
        source_admission = sources[source_id]
        _need("source_sha256" not in source_admission or source_admission["source_sha256"] == source_hash,
              "CASE_SOURCE_BINDING_FAILED:" + case_id)
        level, count, category, level_basis = _level(meta)
        model = _file(folder / "public/model.ifc")
        primary = meta.get("primary_prompt")
        use_primary = bool(primary and (folder / "public/request.txt").is_file())
        variant = primary if use_primary else "world"
        _need(variant in {"world", "host_wall", "storey_local"}, "CASE_REQUEST_BINDING_FAILED:" + case_id)
        request = _file(folder / "public" / ("request.txt" if use_primary else "request-world.txt"))
        templates = meta.get("prompt_templates")
        _need(isinstance(templates, dict) and isinstance(templates.get(variant), dict)
              and templates[variant].get("applicable") is True, "CASE_REQUEST_BINDING_FAILED:" + case_id)
        input_digests = {"model.ifc": _hash(meta.get("damaged_sha256")), "request.txt": _hash(templates[variant].get("sha256"))}
        _need(sha256(model) == input_digests["model.ifc"] and sha256(request) == input_digests["request.txt"],
              "CASE_INPUT_BINDING_FAILED:" + case_id)
        # Validate the public and metadata bindings in the seal. Private evidence
        # hashes remain the upstream curator's responsibility and are never opened.
        seal_path = _file(folder / "private/seal.json")
        seal = _json(seal_path).get("sha256")
        _need(isinstance(seal, dict) and seal.get("case.json") == sha256(metadata_path)
              and seal.get("public/model.ifc") == input_digests["model.ifc"]
              and seal.get("public/" + request.name) == input_digests["request.txt"], "CASE_SEAL_BINDING_FAILED:" + case_id)
        bindings = {**snapshots, str(metadata_path): sha256(metadata_path), str(seal_path): sha256(seal_path)}
        admission = {key: meta[key] for key in _ADMISSION_FIELDS if key in meta}
        admission.update(dataset_status=summary["status"], dataset_schema=summary["schema_version"],
                         source=source_admission, metadata_bindings=bindings,
                         public_seal_bindings_verified=True,
                         full_private_seal_verified=False, live_stage_admission=False,
                         level_basis=level_basis)
        candidate = {"case_id": case_id, "dataset_case_id": dataset_id, "dataset_root": str(root),
                     "dataset_path": relative, "model_path": str(model), "request_path": str(request),
                     "request_variant": variant, "family": meta["family"], "severity": meta["severity"],
                     "category": category, "level": level, "primary_target_count": count,
                     "source_id": source_id, "source_sha256": source_hash,
                     "input_digests": input_digests, "upstream_admission": admission}
        card = meta.get("approved_answer_card_path")
        if card is not None:
            _need(meta.get("answer_card_approved") is True, "ANSWER_CARD_NOT_APPROVED")
            card_relative = relative_path(card)
            _need(card_relative.startswith("private/") and card_relative.endswith(".json"), "INVALID_ANSWER_CARD_PATH")
            card_path = _file(folder / card_relative)
            _need(card_path.is_relative_to(folder / "private"), "INVALID_ANSWER_CARD_PATH")
            candidate["approved_answer_card_path"] = str(card_path)
        candidates.append(candidate)
    _need(len(candidates) == summary["machine_validated_cases"], "DATASET_INDEX_INCONSISTENT")
    _need({c["source_id"] for c in candidates} == set(sources), "DATASET_INDEX_INCONSISTENT")
    _need(all(sha256(_file(Path(path))) == value for path, value in snapshots.items()), "DATASET_CHANGED_DURING_LOAD")
    return sorted(candidates, key=lambda c: c["case_id"])


def _source_group(candidate):
    return candidate.get("source_sha256") or candidate["source_id"]


def _pair_safe_path(path):
    """Reject all Windows reparse points as well as links/junctions/hardlinks."""
    absolute = Path(path).absolute()
    for entry in (absolute, *absolute.parents):
        if entry.exists() or entry.is_symlink():
            _need(not getattr(entry.lstat(), "st_file_attributes", 0)
                  & stat.FILE_ATTRIBUTE_REPARSE_POINT, "LINK_PATH_NOT_ALLOWED")
    return safe_path(absolute)


def _pair_public_relative(value, suffix):
    relative = relative_path(value)
    parts = relative.split("/")
    _need(all(part and part == part.strip() and not part.endswith((".", " ")) for part in parts),
          "INVALID_RELATIVE_PATH")
    _need(not any(re.search(r"original|gold|reference|mutation|private|pristine|ground[_-]?truth",
                           part, flags=re.IGNORECASE) for part in parts), "PRIVATE_INPUT_NOT_ALLOWED")
    _need(Path(relative).suffix.lower() == suffix, "INVALID_PUBLIC_INPUT_PATH")
    return relative


def _pair_public_path(root, value, suffix):
    relative = _pair_public_relative(value, suffix)
    path = _pair_safe_path(root / relative)
    _need(path.is_relative_to(root) and path.suffix.lower() == suffix, "INVALID_PUBLIC_INPUT_PATH")
    _need(path.is_file(), "INPUT_FILE_MISSING:" + str(path))
    _need(path.stat().st_size > 0, "EMPTY_INPUT:" + relative)
    return path


def _pair_delivery(root, index, rows, receipt_path):
    """Read host-only receipt metadata; never open reference or mutation inputs."""
    summary_path = _pair_safe_path(Path(receipt_path))
    batch = root.parent
    _need(root.name == "public" and summary_path == batch / "private/finalization/summary.json"
          and index == root / "inputs.csv", "DELIVERY_RECEIPT_PATH_BINDING_FAILED")
    _need(not (summary_path.parent / "failed.json").exists()
          and not (batch / "private/evaluation/export-failed.json").exists(), "DELIVERY_FAILED_RECEIPT_PRESENT")
    bindings = {str(summary_path): sha256(_file(summary_path))}
    summary = _json(summary_path)
    _need(summary.get("schema_version") == "text2ifc/dataset-offline-delivery/1.3"
          and summary.get("status") == "complete", "DELIVERY_SUMMARY_INVALID")
    authority = summary.get("authority_sha256")
    _need(isinstance(authority, dict), "DELIVERY_AUTHORITY_BINDING_FAILED")
    evidence = []
    for relative in ("private/evaluation/export.json", "private/finalization/checks.json"):
        path = _pair_safe_path(batch / relative)
        expected = authority.get(str(path))
        _need(expected is not None and sha256(_file(path)) == _hash(expected), "DELIVERY_AUTHORITY_BINDING_FAILED")
        bindings[str(path)] = expected
        evidence.append(_json(path))
    export, checks = evidence
    _need(checks.get("schema_version") == summary["schema_version"] and checks.get("passed") is True,
          "DELIVERY_CHECKS_INVALID")
    _need(export.get("schema_version") == "text2ifc/dataset-pair-export/1.1"
          and export.get("status") == "complete" and export.get("public_root") == str(root)
          and export.get("source_root") == str(batch / "private/production")
          and export.get("request_profile") == "text2ifc/dataset-request/1.4"
          and all(type(export.get(key)) is int and export[key] > 0 and export[key] == summary.get(key)
                  for key in ("pairs", "distinct_damages", "source_models")), "DELIVERY_EXPORT_INVALID")
    hashes, provenance, bound = (export.get(key) for key in
                                  ("public_file_sha256", "pair_provenance", "bound_hashes"))
    allowed = {"inputs.csv", *[row[key] for row in rows for key in ("ifc_path", "request_path")]}
    _need(isinstance(hashes, dict) and set(hashes) == allowed
          and hashes.get("inputs.csv") == sha256(index), "DELIVERY_INDEX_BINDING_FAILED")
    _need(isinstance(provenance, list) and len(provenance) == len(rows) == export["pairs"]
          and all(isinstance(pair, dict) and pair.get("case_id") == row["case_id"]
                  and pair.get("public_row") == row for pair, row in zip(provenance, rows, strict=True))
          and isinstance(bound, dict), "DELIVERY_MAPPING_BINDING_FAILED")
    return {"export": export, "bindings": bindings, "pairs": dict(zip((r["case_id"] for r in rows), provenance)),
            "native_cache": {}}


def _pair_native_delivery(delivery, row, digests):
    """Verify the selected byte/receipt/seal chain, not the private authoring tree."""
    import ifcopenshell

    export = delivery["export"]
    pair = delivery["pairs"][row["case_id"]]
    hashes = export["public_file_sha256"]
    _need(digests["model.ifc"] == hashes.get(row["ifc_path"]) == pair.get("model_sha256")
          and digests["request.txt"] == hashes.get(row["request_path"]) == pair.get("public_request_sha256"),
          "DELIVERY_PUBLIC_INPUT_BINDING_FAILED")
    relative = relative_path(pair.get("case_path"))
    parts = relative.split("/")
    _need(len(parts) == 4 and parts[:3] == ["sources", pair.get("source_id"), "cases"],
          "DELIVERY_CASE_PATH_BINDING_FAILED")
    _identifier(parts[1], "DELIVERY_CASE_PATH_BINDING_FAILED")
    _identifier(parts[3], "DELIVERY_CASE_PATH_BINDING_FAILED")
    folder = _pair_safe_path(Path(export["source_root"]) / relative)
    cache_key = (str(folder), digests["model.ifc"])
    if cache_key in delivery["native_cache"]:
        return delivery["native_cache"][cache_key]
    bindings = dict(delivery["bindings"])
    documents = []
    for name in ("private/seal.json", "private/validation.json"):
        path = _pair_safe_path(folder / name)
        expected = export["bound_hashes"].get(str(path))
        _need(expected is not None and sha256(_file(path)) == _hash(expected), "DELIVERY_NATIVE_BINDING_FAILED")
        bindings[str(path)] = expected
        documents.append(_json(path))
    seal, native = documents
    sealed = seal.get("sha256")
    _need(seal.get("schema_version") == "text2ifc/ifc-repair-dataset-seal/1.0" and isinstance(sealed, dict)
          and sealed.get("public/model.ifc") == digests["model.ifc"]
          and sealed.get("private/validation.json") == bindings[str(folder / "private/validation.json")],
          "DELIVERY_SEAL_BINDING_FAILED")
    _need(native.get("passed") is True and type(native.get("finding_count")) is int
          and native["finding_count"] == 0 and native.get("express_rules") is True
          and native.get("schema") == "IFC2X3" and native.get("ifcopenshell_version") == ifcopenshell.version,
          "DELIVERY_NATIVE_RECEIPT_INVALID")
    validation = {key: native[key] for key in
                  ("passed", "finding_count", "express_rules", "schema", "ifcopenshell_version")}
    validation.update(reused=True, scope="Selected public IFC bytes and sealed native/EXPRESS receipt; no fresh native run")
    result = {"machine_validated": True, "human_reviewed": False,
              "native_validation": validation, "metadata_bindings": bindings}
    delivery["native_cache"][cache_key] = result
    return result


def load_pair_candidates(root: Path, *, default_level=None, index_path=None,
                         case_ids=None, delivery_receipt=None) -> list[dict]:
    """Load authored public pairs without parsing IFC or inferring task metadata.

    An optional UTF-8 ``inputs.csv`` selects paths beneath root, including folders.
    Otherwise only top-level, case-insensitive same-stem IFC/TXT pairs are scanned.
    CSV order defines ordinals. Selection checks every row but reads input bytes
    only for selected IDs. An explicit finalization summary can reuse selected
    hash-bound native receipts; it never grants live-stage admission.
    """
    root = _pair_safe_path(root)
    _need(root.is_dir(), "INPUT_ROOT_MISSING")
    _need(default_level is None or default_level in {"S1", "S2", "S3"}, "INVALID_DEFAULT_LEVEL")
    if index_path is None:
        index = root / "inputs.csv"
        index = _pair_safe_path(index) if index.exists() or index.is_symlink() else None
    else:
        supplied = Path(index_path)
        # Explicit absolute index locations are allowed only within this root.
        _need(".." not in supplied.parts, "INVALID_INDEX_PATH")
        index = _pair_safe_path(supplied if supplied.is_absolute() else root / relative_path(str(supplied)))
        _need(index.is_relative_to(root), "INVALID_INDEX_PATH")
    snapshots = {}
    if index is not None:
        _need(index.is_file(), "INPUT_INDEX_MISSING")
        snapshots[str(index)] = sha256(index)
        with index.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            required = {"case_id", "ifc_path", "request_path", "level"}
            _need(required <= set(fields) and set(fields) <= required | {"primary_target_count", "task_kind"}
                  and len(set(fields)) == len(fields), "INVALID_INPUT_INDEX_COLUMNS")
            rows = list(reader)
        _need(all(None not in row and all(value is not None for value in row.values()) for row in rows),
              "INVALID_INPUT_INDEX_ROW")
    else:
        _need(default_level is not None, "DEFAULT_LEVEL_REQUIRED")
        pairs = {}
        for entry in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
            suffix = entry.suffix.lower()
            if suffix not in {".ifc", ".txt"}:
                continue
            path = _pair_public_path(root, entry.name, suffix)
            pair = pairs.setdefault(path.stem.casefold(), {})
            _need(suffix not in pair, "DUPLICATE_INPUT_PATH")
            pair[suffix] = path.name
        _need(all(set(pair) == {".ifc", ".txt"} for pair in pairs.values()), "MISSING_PAIR")
        rows = [{"case_id": Path(pair[".ifc"]).stem, "ifc_path": pair[".ifc"],
                 "request_path": pair[".txt"], "level": default_level} for pair in pairs.values()]
    _need(bool(rows), "NO_PUBLIC_CASES")
    selected = None
    if case_ids is not None:
        _need(isinstance(case_ids, (list, tuple)) and bool(case_ids), "CASE_SELECTION_REQUIRED")
        _need(len(set(case_ids)) == len(case_ids), "DUPLICATE_CASE_SELECTION")
        selected = set(case_ids)
        _need(selected <= {row["case_id"] for row in rows}, "UNKNOWN_CASE_SELECTION")
    delivery = _pair_delivery(root, index, rows, delivery_receipt) if delivery_receipt is not None else None
    candidates, identifiers, used_paths = [], set(), set()
    for row in rows:
        identifier = _identifier(row["case_id"])
        _need(len(identifier) <= 101, "INVALID_PAIR_CASE_ID")
        _need(identifier.casefold() not in identifiers, "DUPLICATE_CASE_ID")
        identifiers.add(identifier.casefold())
        level = row["level"]
        _need(level in {"S1", "S2", "S3"}, "INVALID_PAIR_LEVEL")
        kind = row.get("task_kind") or "unknown"
        _need(kind in {"unknown", "geometry", "property", "mixed"}
              and row.get("task_kind") != "unknown", "INVALID_TASK_KIND")
        count_text = row.get("primary_target_count") or ""
        _need(not count_text or re.fullmatch(r"[1-9][0-9]*", count_text), "INVALID_PRIMARY_TARGET_COUNT")
        count = int(count_text) if count_text else None
        if count is not None:
            _need(budget_level_for_primary_targets(count) == level, "PAIR_LEVEL_MISMATCH")
        model = root / _pair_public_relative(row["ifc_path"], ".ifc")
        request = root / _pair_public_relative(row["request_path"], ".txt")
        keys = {str(model).casefold(), str(request).casefold()}
        _need(not keys & used_paths, "DUPLICATE_INPUT_PATH")
        used_paths.update(keys)
        if selected is not None and identifier not in selected:
            continue
        model = _pair_public_path(root, row["ifc_path"], ".ifc")
        request = _pair_public_path(root, row["request_path"], ".txt")
        _need(request.read_text(encoding="utf-8-sig").strip(), "EMPTY_INPUT:" + request.name)
        digests = {"model.ifc": sha256(model), "request.txt": sha256(request)}
        bindings = {**snapshots, str(model): digests["model.ifc"], str(request): digests["request.txt"]}
        admission = _pair_native_delivery(delivery, row, digests) if delivery else {}
        bindings.update(admission.get("metadata_bindings", {}))
        basis = "declared_primary_target_count" if count is not None else "declared_index_level" if index else "explicit_default_level"
        candidates.append({"case_id": identifier, "dataset_case_id": identifier,
                           "dataset_root": str(root), "dataset_path": row["ifc_path"],
                           "input_kind": "public_pair", "model_path": str(model), "request_path": str(request),
                           "request_variant": "authored", "family": kind, "severity": level,
                           "category": kind, "level": level, "primary_target_count": count,
                           "source_id": identifier, "source_sha256": digests["model.ifc"],
                           "input_digests": digests, "upstream_admission": {**admission,
                               "status": "declared_public_input", "live_stage_admission": False,
                               "source_sha256_basis": "supplied_public_ifc_bytes",
                               "level_basis": basis, "metadata_bindings": bindings}})
    # Recheck each shared metadata file once, not once per CSV row. This still
    # detects changes made while another selected input was being read.
    final_bindings = {path: value for case in candidates
                      for path, value in case["upstream_admission"]["metadata_bindings"].items()}
    _need(all(sha256(_file(Path(path))) == value for path, value in final_bindings.items()),
          "INPUTS_CHANGED_DURING_LOAD")
    return candidates


def select_rounds(candidates, seed=42, second_count=2) -> dict:
    """Choose two S1 smoke cases, then one or two disjoint follow-up cases.

    Seeded order is stable under index reordering. Round one prefers pure geometry
    and pure property cases from distinct source bytes. Missing S1 categories or
    counts remain explicit; no invented or harder case fills a simple-case gap.
    """
    _need(type(seed) is int, "INVALID_SELECTION_SEED")
    _need(type(second_count) is int and second_count in {1, 2}, "INVALID_SECOND_ROUND_COUNT")
    pool = sorted(candidates, key=lambda c: c["case_id"])
    ids = [_identifier(c["case_id"]) for c in pool]
    _need(len({identifier.casefold() for identifier in ids}) == len(ids), "DUPLICATE_CASE_ID")
    _need(all(c.get("level") in {"S1", "S2", "S3"} and c.get("category") in {"geometry", "property", "mixed"}
              and c.get("source_id") for c in pool), "INVALID_SELECTION_CANDIDATE")
    random.Random(seed).shuffle(pool)
    simple = [c for c in pool if c["level"] == "S1"]
    geometry = [c for c in simple if c["category"] == "geometry"]
    properties = [c for c in simple if c["category"] == "property"]
    if geometry and properties:
        pair = next(((g, p) for g in geometry for p in properties if _source_group(g) != _source_group(p)),
                    (geometry[0], properties[0]))
        first = list(pair)
    else:
        first = simple[:1]
        if first:
            remaining = [c for c in simple if c["case_id"] != first[0]["case_id"]]
            if remaining:
                first.append(next((c for c in remaining if _source_group(c) != _source_group(first[0])), remaining[0]))
    first_ids = {c["case_id"] for c in first}
    remaining = [c for c in pool if c["case_id"] not in first_ids]
    used_sources = {_source_group(c) for c in first}
    second = []
    while remaining and len(second) < second_count:
        # Keep follow-up work bounded while preferring another independent source.
        chosen = min(remaining, key=lambda c: (int(c["level"][1]), _source_group(c) in used_sources))
        second.append(chosen)
        remaining.remove(chosen)
        used_sources.add(_source_group(chosen))
    missing = [f"{category}_S1" for category in ("geometry", "property")
               if not any(c["category"] == category for c in first)]
    distinct = len({_source_group(c) for c in first}) == 2
    if len(first) == 2 and not distinct:
        missing.append("distinct_round1_sources")
    coverage = {"round1": {"requested_count": 2, "selected_count": len(first), "shortfall": 2 - len(first),
                            "distinct_sources": distinct, "categories": sorted({c["category"] for c in first})},
                "round2": {"requested_count": second_count, "selected_count": len(second), "shortfall": second_count - len(second)},
                "available_count": len(pool), "available_simple_count": len(simple)}
    return {"schema_version": SCHEMA, "seed": seed, "round1": first, "round2": second,
            "coverage": coverage, "missing_coverage": missing}


def request_convention_parts(version=None) -> tuple[dict | None, bytes]:
    """Return detached host metadata and exact public appendix bytes, without I/O."""
    _need(version in (None, PROPERTY_UNITS_REQUEST_CONVENTION), "INVALID_REQUEST_CONVENTION")
    if version is None:
        return None, b""
    appendix = ("\n\n" + _PROPERTY_UNITS_REQUEST_NOTICE + "\n").encode("utf-8")
    return {
        "version": version,
        "text": _PROPERTY_UNITS_REQUEST_NOTICE,
        "sha256": hashlib.sha256(_PROPERTY_UNITS_REQUEST_NOTICE.encode("utf-8")).hexdigest(),
        "appendix_sha256": hashlib.sha256(appendix).hexdigest(),
    }, appendix


def materialize_public(candidates, destination, *, request_convention=None) -> dict:
    """Copy only model.ifc/request.txt to a fresh, non-overlapping directory.

    ``cases`` is an allowlisted public projection; ``bindings`` is host-side input
    provenance. No metadata, reference IFC, mutation, or answer card is copied.
    Source metadata and bytes are rechecked before and after the copy. Any failed
    partial copy is retained for diagnosis; existing destinations are never reused.
    An optional fixed request convention appends public guidance only after the
    original input bindings pass, retaining separate source and effective hashes.
    """
    convention, appendix = request_convention_parts(request_convention)
    destination = safe_path(Path(destination))
    if destination.exists():
        raise FileExistsError(destination)
    prepared, identifiers = [], set()
    resolved_paths, snapshot = {}, {}

    def bind(path, expected, error, *, public_input=False):
        # Resolve each spelling once while collecting the snapshot. Hashes are
        # never cached across validation phases; each phase rechecks safe paths.
        supplied = Path(path).absolute()
        if supplied not in resolved_paths:
            resolved_paths[supplied] = _file(supplied)
        canonical = resolved_paths[supplied]
        existing = snapshot.get(canonical)
        _need(existing is None or existing[0] == expected, error)
        if existing is None or public_input:
            snapshot[canonical] = (expected, error)

    def verify_snapshot():
        for path, (expected, error) in snapshot.items():
            _need(sha256(_file(path)) == expected, error)

    for candidate in candidates:
        identifier = _identifier(candidate.get("case_id"))
        _need(identifier.casefold() not in identifiers, "DUPLICATE_CASE_ID")
        identifiers.add(identifier.casefold())
        model, request = (_file(candidate[name]) for name in ("model_path", "request_path"))
        input_root = safe_path(Path(candidate.get("dataset_root", model.parent.parent)))
        if candidate.get("input_kind") == "public_pair":
            input_root = _pair_safe_path(input_root)
            _need(model.is_relative_to(input_root) and request.is_relative_to(input_root), "INVALID_PUBLIC_INPUT_PATH")
            model = _pair_public_path(input_root, model.relative_to(input_root).as_posix(), ".ifc")
            request = _pair_public_path(input_root, request.relative_to(input_root).as_posix(), ".txt")
        else:
            _need(model.name == "model.ifc" and model.parent.name == "public" and request.parent == model.parent
                  and request.name in {"request.txt", "request-world.txt", "request-host_wall.txt", "request-storey_local.txt"},
                  "INVALID_PUBLIC_INPUT_PATH")
        _need(not destination.is_relative_to(input_root) and not input_root.is_relative_to(destination), "SOURCE_OUTPUT_OVERLAP")
        inputs = candidate.get("input_digests")
        _need(isinstance(inputs, dict) and set(inputs) == {"model.ifc", "request.txt"}, "INVALID_INPUT_DIGEST")
        _hash(candidate.get("source_sha256"))
        for name, path in (("model.ifc", model), ("request.txt", request)):
            resolved_paths[path] = path
            bind(path, _hash(inputs[name]), "CASE_INPUT_BINDING_FAILED:" + identifier, public_input=True)
        metadata = candidate.get("upstream_admission", {}).get("metadata_bindings", {})
        _need(isinstance(metadata, dict) and bool(metadata), "CASE_METADATA_BINDING_REQUIRED")
        for path, expected in metadata.items():
            bind(path, expected, "CASE_METADATA_BINDING_FAILED:" + identifier)
        prepared.append((candidate, model, request, metadata))
    _need(bool(prepared), "NO_PUBLIC_CASES")
    # Reject all conflicting bindings and validate the complete input snapshot
    # before creating any output. Public inputs duplicated in metadata hash once.
    verify_snapshot()
    destination.mkdir(parents=True, exist_ok=False)
    public_cases, bindings = [], {}
    for candidate, model, request, metadata in prepared:
        identifier = candidate["case_id"]
        public = destination / identifier / "public"
        public.mkdir(parents=True, exist_ok=False)
        for name, source in (("model.ifc", model), ("request.txt", request)):
            target = public / name
            shutil.copyfile(source, target)
            _need(sha256(target) == candidate["input_digests"][name] == sha256(source),
                  "CASE_INPUT_BINDING_FAILED:" + identifier)
        effective_inputs = dict(candidate["input_digests"])
        if convention is not None:
            target = public / "request.txt"
            original_request = target.read_bytes()
            _need(hashlib.sha256(original_request).hexdigest() == candidate["input_digests"]["request.txt"],
                  "CASE_INPUT_BINDING_FAILED:" + identifier)
            effective_request = original_request + appendix
            target.write_bytes(effective_request)
            effective_inputs["request.txt"] = hashlib.sha256(effective_request).hexdigest()
            _need(sha256(target) == effective_inputs["request.txt"], "CASE_INPUT_BINDING_FAILED:" + identifier)
        public_cases.append({"case_id": identifier, "level": candidate["level"], "source_id": candidate["source_id"],
                             "model_path": str(public / "model.ifc"), "request_path": str(public / "request.txt"),
                             "input_digests": dict(effective_inputs)})
        bindings[identifier] = {"source_id": candidate["source_id"], "source_sha256": candidate["source_sha256"],
                                "dataset_case_id": candidate.get("dataset_case_id", identifier),
                                "input_digests": dict(effective_inputs),
                                "metadata_bindings": dict(metadata), "source_inputs_unchanged": True}
        if convention is not None:
            bindings[identifier].update(
                source_input_digests=dict(candidate["input_digests"]),
                request_convention=dict(convention),
            )
    # A different work unit may change an earlier input while later cases copy.
    # Recheck every unique source/metadata binding before returning success,
    # including fresh path safety checks. Shared receipts need no per-case reread.
    verify_snapshot()
    result = {"schema_version": SCHEMA, "destination": str(destination), "cases": public_cases, "bindings": bindings}
    if convention is not None:
        # Bind the effective request bytes after every case has been copied,
        # including a request changed while a later case was materialized.
        for public_case in public_cases:
            _need(sha256(_file(public_case["request_path"])) == public_case["input_digests"]["request.txt"],
                  "CASE_INPUT_BINDING_FAILED:" + public_case["case_id"])
        result["request_convention"] = dict(convention)
    return result
