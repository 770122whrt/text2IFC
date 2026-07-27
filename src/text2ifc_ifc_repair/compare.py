"""Normalized semantic and geometric preservation comparison for IFC files."""

from __future__ import annotations

import hashlib
import contextlib
import io
import json
import math
import time
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.classification
import ifcopenshell.util.element
import ifcopenshell.util.placement

from .registry import OperationRegistry


COMPARISON_SCHEMA_VERSION = "text2ifc/ifc-repair-comparison/0.1"
IFCOPENSHELL_COMPARISON_SCHEMA_VERSION = (
    "text2ifc/ifcopenshell-comparison/0.1"
)
FINGERPRINT_ALGORITHM_VERSION = "text2ifc/ifc-root-fingerprint/0.2"
DEFAULT_COMPARISON_TIMEOUT_SECONDS = 120.0
ALIGNED_FAST_PATH_MAX_DIRTY_RECORDS = 100_000


class ComparisonIntegrityError(RuntimeError):
    """The global preservation comparison cannot produce trustworthy evidence."""


class ComparisonTimeoutError(ComparisonIntegrityError):
    """The global preservation comparison exceeded its blocking time budget."""


@dataclass(frozen=True)
class _RootFingerprint:
    entity: Any
    digest: bytes


@dataclass(frozen=True)
class _AttributeMetadata:
    name: str
    type_text: bytes
    type_info: Any


class _ModelFingerprinter:
    """Hash one immutable IFC graph while memoizing shared non-root entities."""

    def __init__(self, model: Any, *, deadline: float) -> None:
        self.model = model
        self.deadline = deadline
        self.entity_cache: dict[int, bytes] = {}
        self.attribute_metadata_cache: dict[
            str, tuple[_AttributeMetadata, ...]
        ] = {}
        self.aggregate_type_cache: dict[str, tuple[str, Any]] = {}
        self.entity_hash_count = 0
        self.cache_hits = 0
        self.cycle_edges = 0
        self.root_count = 0

    def root_index(self) -> dict[str, _RootFingerprint]:
        result: dict[str, _RootFingerprint] = {}
        for index, entity in enumerate(self.model.by_type("IfcRoot")):
            if index % 256 == 0:
                self._check_deadline()
            raw_global_id = getattr(entity, "GlobalId", None)
            global_id = str(raw_global_id or "").strip()
            if not global_id:
                raise ComparisonIntegrityError(
                    f"EMPTY_ROOT_GLOBAL_ID:{entity.is_a()}:step={entity.id()}"
                )
            if global_id in result:
                raise ComparisonIntegrityError(
                    f"DUPLICATE_ROOT_GLOBAL_ID:{global_id}"
                )
            digest, _ = self._fingerprint_entity(
                entity,
                active=(),
                is_root=True,
            )
            result[global_id] = _RootFingerprint(entity=entity, digest=digest)
            self.root_count += 1
        self._check_deadline()
        return result

    def fingerprint_value(self, value: Any, *, type_info: Any = None) -> bytes:
        digest, _ = self._fingerprint_value(
            value,
            type_info=type_info,
            active=(),
        )
        return digest

    def fingerprint_root(self, entity: Any) -> _RootFingerprint:
        digest, _ = self._fingerprint_entity(
            entity,
            active=(),
            is_root=True,
        )
        self.root_count += 1
        return _RootFingerprint(entity=entity, digest=digest)

    def metrics(self) -> dict[str, int]:
        return {
            "hashed_non_root_entities": self.entity_hash_count,
            "shared_entity_cache_hits": self.cache_hits,
            "cached_non_root_entities": len(self.entity_cache),
            "cycle_edges": self.cycle_edges,
            "root_count": self.root_count,
            "schema_declaration_count": len(self.attribute_metadata_cache),
        }

    def _fingerprint_value(
        self,
        value: Any,
        *,
        type_info: Any,
        active: tuple[int, ...],
    ) -> tuple[bytes, bool]:
        if value is None:
            return _encode_record("null"), False
        if isinstance(value, bool):
            return _encode_record("bool", b"1" if value else b"0"), False
        if isinstance(value, int):
            return _encode_record("int", str(value).encode("ascii")), False
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ComparisonIntegrityError(
                    f"NON_FINITE_FLOAT:{value!r}"
                )
            return _encode_record("float", value.hex().encode("ascii")), False
        if isinstance(value, str):
            return _encode_record("string", value.encode("utf-8")), False
        if isinstance(value, (tuple, list)):
            aggregate_kind, element_type = self._aggregate_type(type_info)
            children = [
                self._fingerprint_value(
                    child,
                    type_info=element_type,
                    active=active,
                )
                for child in value
            ]
            child_digests = [digest for digest, _ in children]
            if aggregate_kind in {"set", "bag"}:
                child_digests.sort()
            return (
                _digest_record(
                    f"aggregate:{aggregate_kind}",
                    *child_digests,
                ),
                any(has_cycle for _, has_cycle in children),
            )
        if hasattr(value, "is_a") and hasattr(value, "id"):
            global_id = str(getattr(value, "GlobalId", None) or "").strip()
            if value.is_a("IfcRoot"):
                if not global_id:
                    raise ComparisonIntegrityError(
                        f"EMPTY_ROOT_REFERENCE:{value.is_a()}:step={value.id()}"
                    )
                return (
                    _digest_record(
                        "root-reference",
                        value.is_a().encode("utf-8"),
                        global_id.encode("utf-8"),
                    ),
                    False,
                )
            return self._fingerprint_entity(
                value,
                active=active,
                is_root=False,
            )
        raise ComparisonIntegrityError(
            f"UNSUPPORTED_FINGERPRINT_VALUE:{type(value).__name__}"
        )

    def _fingerprint_entity(
        self,
        entity: Any,
        *,
        active: tuple[int, ...],
        is_root: bool,
    ) -> tuple[bytes, bool]:
        step_id = int(entity.id())
        cacheable = not is_root and step_id > 0
        if cacheable and step_id in self.entity_cache:
            self.cache_hits += 1
            return self.entity_cache[step_id], False
        if step_id > 0 and step_id in active:
            self.cycle_edges += 1
            distance = len(active) - active.index(step_id)
            return (
                _digest_record(
                    "cycle-reference",
                    entity.is_a().encode("utf-8"),
                    str(distance).encode("ascii"),
                ),
                True,
            )
        if self.entity_hash_count % 1024 == 0:
            self._check_deadline()
        next_active = active + ((step_id,) if step_id > 0 else ())
        entity_class = entity.is_a()
        declared_attributes = self._attribute_metadata(entity)
        if declared_attributes is None:
            if len(entity) != 1:
                raise ComparisonIntegrityError(
                    f"UNSUPPORTED_TYPED_VALUE:{entity_class}"
                )
            wrapped_digest, contains_cycle = self._fingerprint_value(
                entity[0],
                type_info=None,
                active=next_active,
            )
            return (
                _digest_record(
                    "typed-value",
                    entity_class.encode("utf-8"),
                    wrapped_digest,
                ),
                contains_cycle,
            )
        attribute_records: list[bytes] = []
        contains_cycle = False
        for index in range(len(entity)):
            attribute = declared_attributes[index]
            child_digest, child_cycle = self._fingerprint_value(
                entity[index],
                type_info=attribute.type_info,
                active=next_active,
            )
            contains_cycle = contains_cycle or child_cycle
            attribute_records.append(
                _encode_record(
                    "attribute",
                    str(index).encode("ascii"),
                    attribute.name.encode("utf-8"),
                    attribute.type_text,
                    child_digest,
                )
            )
        digest = _digest_record(
            "root-entity" if is_root else "entity",
            str(self.model.schema).encode("utf-8"),
            entity_class.encode("utf-8"),
            *attribute_records,
        )
        if cacheable and not contains_cycle:
            self.entity_cache[step_id] = digest
            self.entity_hash_count += 1
        return digest, contains_cycle

    def _attribute_metadata(
        self,
        entity: Any,
    ) -> tuple[_AttributeMetadata, ...] | None:
        entity_class = entity.is_a()
        cached = self.attribute_metadata_cache.get(entity_class)
        if cached is not None:
            return cached
        declaration = entity.wrapped_data.declaration().as_entity()
        if declaration is None:
            return None
        metadata = tuple(
            _AttributeMetadata(
                name=attribute.name(),
                type_text=str(attribute.type_of_attribute()).encode("utf-8"),
                type_info=attribute.type_of_attribute(),
            )
            for attribute in declaration.all_attributes()
        )
        self.attribute_metadata_cache[entity_class] = metadata
        return metadata

    def _aggregate_type(self, type_info: Any) -> tuple[str, Any]:
        if type_info is None:
            return "list", None
        type_key = str(type_info)
        cached = self.aggregate_type_cache.get(type_key)
        if cached is not None:
            return cached
        try:
            aggregation = type_info.as_aggregation_type()
        except (AttributeError, RuntimeError):
            result = ("list", None)
        else:
            if aggregation is None:
                result = ("list", None)
            else:
                result = (
                    str(aggregation.type_of_aggregation_string()).lower(),
                    aggregation.type_of_element(),
                )
        self.aggregate_type_cache[type_key] = result
        return result

    def _check_deadline(self) -> None:
        if time.perf_counter() > self.deadline:
            raise ComparisonTimeoutError(
                "COMPARISON_TIMEOUT:"
                f"roots={self.root_count}:"
                f"cached_entities={len(self.entity_cache)}"
            )


def _encode_record(tag: str, *parts: bytes) -> bytes:
    encoded = bytearray()
    for part in (tag.encode("utf-8"), *parts):
        encoded.extend(len(part).to_bytes(8, "big"))
        encoded.extend(part)
    return bytes(encoded)


def _digest_record(tag: str, *parts: bytes) -> bytes:
    digest = hashlib.sha256()
    digest.update(
        _encode_record(
            FINGERPRINT_ALGORITHM_VERSION,
            tag.encode("utf-8"),
            *parts,
        )
    )
    return digest.digest()


def evaluate_repair_application(
    *,
    damaged_ifc_path: Path | str,
    repaired_ifc_path: Path | str,
    changeset: Mapping[str, Any],
    application_result: Mapping[str, Any],
    registry: OperationRegistry,
) -> dict[str, Any]:
    """Retain the 0.1 surface while disclosing unavailable L2 assurance."""

    from .evaluation import evaluate_independent_l1

    allowed_changed_ids = {
        str(item["global_id"])
        for operation_result in application_result.get("operations", [])
        for change_kind in ("created", "modified", "removed")
        for item in operation_result.get("changes", {}).get(change_kind, [])
        if item.get("global_id")
    }
    common = compare_ifc_models(
        damaged_ifc_path,
        repaired_ifc_path,
        allowed_changed_ids=allowed_changed_ids,
    )
    before_model = ifcopenshell.open(str(Path(damaged_ifc_path)))
    after_model = ifcopenshell.open(str(Path(repaired_ifc_path)))
    operation_results_by_id = {
        str(item["operation_id"]): item
        for item in application_result.get("operations", [])
    }
    operation_evaluations = []
    for operation in changeset["operations"]:
        application = operation_results_by_id.get(str(operation["operation_id"]), {})
        operation_evaluations.append(
            {
                "operation_id": operation["operation_id"],
                "operation_type": operation["operation_type"],
                **registry.dispatch(
                    "comparison_adapter",
                    operation,
                    before_model=before_model,
                    after_model=after_model,
                    application=application.get("changes", {}),
                ),
            }
        )
    application_postconditions_valid = all(
        item.get("valid", False)
        for item in application_result.get("postconditions", [])
    )
    l1_result = evaluate_independent_l1(
        damaged_ifc_path=damaged_ifc_path,
        repaired_ifc_path=repaired_ifc_path,
        changeset=changeset,
        application_result=application_result,
        registry=registry,
    )
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation/0.1",
        "complete_repair_success": False,
        "successful_artifact_publishable": False,
        "application_postconditions_valid": application_postconditions_valid,
        "tolerances": {
            "linear_mm": 0.1,
            "orientation_degrees": 0.1,
            "volume_m3": 1e-5,
        },
        "common": common,
        "operations": operation_evaluations,
        "l1": _l1_compatibility_projection(l1_result),
        "l2": {
            "status": "not_evaluable",
            "reason": (
                "Legacy Evaluation 0.1 has no authoritative L2 semantic assurance."
            ),
            "assurance_error_code": "legacy_assurance_unavailable",
        },
    }


def _l1_compatibility_projection(level: Any) -> dict[str, Any]:
    """Project Evaluation 0.2 checks without changing legacy comparator fields."""

    return {
        "status": level.status.value,
        "reason": level.reason,
        "checks": [
            {
                "check_id": check.check_id,
                "status": check.status.value,
                "reason": check.reason,
            }
            for check in level.checks
        ],
    }


def compare_ifc_models(
    before_path: Path | str,
    after_path: Path | str,
    *,
    allowed_changed_ids: Iterable[str],
) -> dict[str, Any]:
    """Compare IFC semantics by GlobalId without relying on STEP order."""

    before = ifcopenshell.open(str(Path(before_path)))
    after = ifcopenshell.open(str(Path(after_path)))
    allowed = set(allowed_changed_ids)
    try:
        profiled = profile_normalized_model_diff(before, after)
    except ComparisonIntegrityError as error:
        error_text = str(error)
        return {
            "schema_version": COMPARISON_SCHEMA_VERSION,
            "comparison_status": "not_evaluable",
            "comparison_error_code": error_text.split(":", 1)[0],
            "comparison_error": error_text,
            "before_readable": True,
            "after_readable": True,
            "before_schema": before.schema,
            "after_schema": after.schema,
            "schema_preserved": before.schema == after.schema,
            "added_ids": [],
            "removed_ids": [],
            "modified_ids": [],
            "allowed_changed_ids": sorted(allowed),
            "unexpected_changed_ids": [],
            "drift": {},
            "comparison_metrics": None,
            "complete_preservation_success": False,
        }
    actual_changes = profiled["changes"]
    added = [item["global_id"] for item in actual_changes["created"]]
    removed = [item["global_id"] for item in actual_changes["removed"]]
    modified = [item["global_id"] for item in actual_changes["modified"]]
    changed = set(added) | set(removed) | set(modified)
    unexpected = sorted(changed - allowed)
    drift = {
        item["global_id"]: {"before": item["before"], "after": item["after"]}
        for item in actual_changes["modified"]
    }
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "comparison_status": "passed",
        "comparison_error_code": None,
        "comparison_error": None,
        "before_readable": True,
        "after_readable": True,
        "before_schema": before.schema,
        "after_schema": after.schema,
        "schema_preserved": before.schema == after.schema,
        "added_ids": added,
        "removed_ids": removed,
        "modified_ids": modified,
        "allowed_changed_ids": sorted(allowed),
        "unexpected_changed_ids": unexpected,
        "drift": drift,
        "comparison_metrics": profiled["metrics"],
        "complete_preservation_success": (
            before.schema == after.schema and not unexpected
        ),
    }


def normalized_model_diff(before_model: Any, after_model: Any) -> dict[str, Any]:
    """Return deterministic actual IfcRoot changes from independently opened models."""

    return profile_normalized_model_diff(before_model, after_model)["changes"]


def profile_normalized_model_diff(
    before_model: Any,
    after_model: Any,
    *,
    timeout_seconds: float = DEFAULT_COMPARISON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return actual root changes plus bounded comparator performance evidence."""

    started = time.perf_counter()
    deadline = started + max(0.0, float(timeout_seconds))
    fast_result = _aligned_step_comparison(
        before_model,
        after_model,
        started=started,
        deadline=deadline,
        timeout_seconds=float(timeout_seconds),
    )
    if fast_result is not None:
        return fast_result
    return _complete_fingerprint_comparison(
        before_model,
        after_model,
        started=started,
        deadline=deadline,
        timeout_seconds=float(timeout_seconds),
    )


def _complete_fingerprint_comparison(
    before_model: Any,
    after_model: Any,
    *,
    started: float,
    deadline: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    before_builder = _ModelFingerprinter(before_model, deadline=deadline)
    before_started = time.perf_counter()
    before_index = before_builder.root_index()
    before_seconds = time.perf_counter() - before_started
    after_builder = _ModelFingerprinter(after_model, deadline=deadline)
    after_started = time.perf_counter()
    after_index = after_builder.root_index()
    after_seconds = time.perf_counter() - after_started
    detail_started = time.perf_counter()
    before_ids = set(before_index)
    after_ids = set(after_index)
    created = [
        _diff_fact(
            "created",
            global_id,
            None,
            _fingerprinted_root_snapshot(
                after_index[global_id],
                after_builder,
            ),
        )
        for global_id in sorted(after_ids - before_ids)
    ]
    removed = [
        _diff_fact(
            "removed",
            global_id,
            _fingerprinted_root_snapshot(
                before_index[global_id],
                before_builder,
            ),
            None,
        )
        for global_id in sorted(before_ids - after_ids)
    ]
    modified = [
        _diff_fact(
            "modified",
            global_id,
            _fingerprinted_root_snapshot(
                before_index[global_id],
                before_builder,
            ),
            _fingerprinted_root_snapshot(
                after_index[global_id],
                after_builder,
            ),
        )
        for global_id in sorted(before_ids & after_ids)
        if before_index[global_id].digest != after_index[global_id].digest
    ]
    detail_seconds = time.perf_counter() - detail_started
    finished = time.perf_counter()
    return {
        "changes": {
            "created": created,
            "modified": modified,
            "removed": removed,
        },
        "metrics": {
            "algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
            "strategy": "complete_semantic_fingerprint",
            "timeout_seconds": timeout_seconds,
            "before_root_count": len(before_index),
            "after_root_count": len(after_index),
            "before_fingerprint_seconds": round(before_seconds, 6),
            "after_fingerprint_seconds": round(after_seconds, 6),
            "detail_seconds": round(detail_seconds, 6),
            "total_seconds": round(finished - started, 6),
            "before": before_builder.metrics(),
            "after": after_builder.metrics(),
        },
    }


def _aligned_step_comparison(
    before_model: Any,
    after_model: Any,
    *,
    started: float,
    deadline: float,
    timeout_seconds: float,
) -> dict[str, Any] | None:
    """Use equal STEP records to locate candidates, then hash candidates semantically."""

    root_started = time.perf_counter()
    before_roots = _validated_root_entities(before_model, deadline=deadline)
    after_roots = _validated_root_entities(after_model, deadline=deadline)
    root_index_seconds = time.perf_counter() - root_started

    record_started = time.perf_counter()
    before_records: dict[int, str] = {}
    for index, entity in enumerate(before_model):
        if index % 8192 == 0:
            _check_comparison_deadline(deadline, stage="aligned-before-records")
        before_records[int(entity.id())] = str(entity)
    before_entity_count = len(before_records)
    dirty_before: set[int] = set()
    dirty_after: set[int] = set()
    after_entity_count = 0
    for index, entity in enumerate(after_model):
        if index % 8192 == 0:
            _check_comparison_deadline(deadline, stage="aligned-after-records")
        after_entity_count += 1
        step_id = int(entity.id())
        before_record = before_records.pop(step_id, None)
        if before_record is None:
            dirty_after.add(step_id)
        elif before_record != str(entity):
            dirty_before.add(step_id)
            dirty_after.add(step_id)
    dirty_before.update(before_records)
    record_seconds = time.perf_counter() - record_started
    dirty_record_count = len(dirty_before) + len(dirty_after)
    if dirty_record_count > ALIGNED_FAST_PATH_MAX_DIRTY_RECORDS:
        return None

    propagation_started = time.perf_counter()
    before_dirty_roots, before_visited = _dirty_root_ids(
        before_model,
        dirty_before,
        deadline=deadline,
    )
    after_dirty_roots, after_visited = _dirty_root_ids(
        after_model,
        dirty_after,
        deadline=deadline,
    )
    propagation_seconds = time.perf_counter() - propagation_started

    before_ids = set(before_roots)
    after_ids = set(after_roots)
    candidate_ids = sorted(
        (before_dirty_roots | after_dirty_roots) & before_ids & after_ids
    )
    before_builder = _ModelFingerprinter(before_model, deadline=deadline)
    after_builder = _ModelFingerprinter(after_model, deadline=deadline)
    fingerprint_started = time.perf_counter()
    before_entries = {
        global_id: before_builder.fingerprint_root(before_roots[global_id])
        for global_id in sorted((before_ids - after_ids) | set(candidate_ids))
    }
    before_fingerprint_seconds = time.perf_counter() - fingerprint_started
    fingerprint_started = time.perf_counter()
    after_entries = {
        global_id: after_builder.fingerprint_root(after_roots[global_id])
        for global_id in sorted((after_ids - before_ids) | set(candidate_ids))
    }
    after_fingerprint_seconds = time.perf_counter() - fingerprint_started

    detail_started = time.perf_counter()
    created = [
        _diff_fact(
            "created",
            global_id,
            None,
            _fingerprinted_root_snapshot(
                after_entries[global_id],
                after_builder,
            ),
        )
        for global_id in sorted(after_ids - before_ids)
    ]
    removed = [
        _diff_fact(
            "removed",
            global_id,
            _fingerprinted_root_snapshot(
                before_entries[global_id],
                before_builder,
            ),
            None,
        )
        for global_id in sorted(before_ids - after_ids)
    ]
    modified = [
        _diff_fact(
            "modified",
            global_id,
            _fingerprinted_root_snapshot(
                before_entries[global_id],
                before_builder,
            ),
            _fingerprinted_root_snapshot(
                after_entries[global_id],
                after_builder,
            ),
        )
        for global_id in candidate_ids
        if before_entries[global_id].digest != after_entries[global_id].digest
    ]
    detail_seconds = time.perf_counter() - detail_started
    finished = time.perf_counter()
    return {
        "changes": {
            "created": created,
            "modified": modified,
            "removed": removed,
        },
        "metrics": {
            "algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
            "strategy": "aligned_step_certificate",
            "timeout_seconds": timeout_seconds,
            "before_root_count": len(before_roots),
            "after_root_count": len(after_roots),
            "before_entity_count": before_entity_count,
            "after_entity_count": after_entity_count,
            "dirty_before_record_count": len(dirty_before),
            "dirty_after_record_count": len(dirty_after),
            "candidate_root_count": len(candidate_ids),
            "before_propagated_entity_count": before_visited,
            "after_propagated_entity_count": after_visited,
            "root_index_seconds": round(root_index_seconds, 6),
            "record_scan_seconds": round(record_seconds, 6),
            "propagation_seconds": round(propagation_seconds, 6),
            "before_fingerprint_seconds": round(
                before_fingerprint_seconds,
                6,
            ),
            "after_fingerprint_seconds": round(
                after_fingerprint_seconds,
                6,
            ),
            "detail_seconds": round(detail_seconds, 6),
            "total_seconds": round(finished - started, 6),
            "before": before_builder.metrics(),
            "after": after_builder.metrics(),
        },
    }


def _validated_root_entities(
    model: Any,
    *,
    deadline: float,
) -> dict[str, Any]:
    roots: dict[str, Any] = {}
    for index, entity in enumerate(model.by_type("IfcRoot")):
        if index % 1024 == 0:
            _check_comparison_deadline(deadline, stage="root-identity-index")
        global_id = str(getattr(entity, "GlobalId", None) or "").strip()
        if not global_id:
            raise ComparisonIntegrityError(
                f"EMPTY_ROOT_GLOBAL_ID:{entity.is_a()}:step={entity.id()}"
            )
        if global_id in roots:
            raise ComparisonIntegrityError(
                f"DUPLICATE_ROOT_GLOBAL_ID:{global_id}"
            )
        roots[global_id] = entity
    return roots


def _dirty_root_ids(
    model: Any,
    dirty_step_ids: set[int],
    *,
    deadline: float,
) -> tuple[set[str], int]:
    roots: set[str] = set()
    queue = deque(sorted(dirty_step_ids))
    visited: set[int] = set()
    while queue:
        if len(visited) % 1024 == 0:
            _check_comparison_deadline(deadline, stage="dirty-root-propagation")
        step_id = queue.popleft()
        if step_id in visited:
            continue
        visited.add(step_id)
        try:
            entity = model.by_id(step_id)
        except RuntimeError:
            continue
        if entity.is_a("IfcRoot"):
            global_id = str(getattr(entity, "GlobalId", None) or "").strip()
            if global_id:
                roots.add(global_id)
            continue
        for inverse in model.get_inverse(entity):
            inverse_step_id = int(inverse.id())
            if inverse_step_id > 0 and inverse_step_id not in visited:
                queue.append(inverse_step_id)
    return roots, len(visited)


def _check_comparison_deadline(deadline: float, *, stage: str) -> None:
    if time.perf_counter() > deadline:
        raise ComparisonTimeoutError(f"COMPARISON_TIMEOUT:stage={stage}")


def _fingerprinted_root_snapshot(
    entry: _RootFingerprint,
    builder: _ModelFingerprinter,
) -> dict[str, Any]:
    snapshot = _root_snapshot(entry.entity, fingerprinter=builder)
    snapshot["content_sha256"] = "sha256:" + entry.digest.hex()
    return snapshot


def _diff_fact(
    change_kind: str,
    global_id: str,
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> dict[str, Any]:
    snapshot = after if after is not None else before
    assert snapshot is not None
    ifc_class = str(snapshot["ifc_class"])
    return {
        "change_kind": change_kind,
        "global_id": global_id,
        "ifc_class": ifc_class,
        "is_relationship": ifc_class.startswith("IfcRel"),
        "before": before,
        "after": after,
    }


def _model_snapshot(model: Any) -> dict[str, Any]:
    return {
        str(entity.GlobalId): _root_snapshot(entity)
        for entity in model.by_type("IfcRoot")
    }


def _root_snapshot(
    entity: Any,
    *,
    fingerprinter: _ModelFingerprinter | None = None,
) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "ifc_class": entity.is_a(),
        "name": getattr(entity, "Name", None),
        "attributes": _root_attributes(entity),
    }
    if entity.is_a("IfcProduct"):
        snapshot["placement"] = _placement_snapshot(entity)
        snapshot["containers"] = sorted(
            str(relation.RelatingStructure.GlobalId)
            for relation in getattr(entity, "ContainedInStructure", ())
        )
        snapshot["types"] = _type_ids(entity)
        snapshot["geometry"] = _geometry_snapshot(
            entity,
            fingerprinter=fingerprinter,
        )
    return snapshot


def _root_attributes(entity: Any) -> dict[str, Any]:
    excluded = {
        "GlobalId",
        "OwnerHistory",
        "Name",
        "Description",
        "ObjectPlacement",
        "Representation",
        "RepresentationMaps",
    }
    attributes: dict[str, Any] = {}
    for index in range(len(entity)):
        name = entity.attribute_name(index)
        if name in excluded:
            continue
        attributes[name] = _normalize_value(entity[index], depth=0, seen=set())
    return attributes


def _normalize_value(value: Any, *, depth: int, seen: set[int]) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        normalized = [
            _normalize_value(child, depth=depth, seen=seen) for child in value
        ]
        return sorted(normalized, key=_canonical_sort_key)
    if hasattr(value, "is_a") and hasattr(value, "id"):
        global_id = getattr(value, "GlobalId", None)
        if global_id:
            return {"ifc_class": value.is_a(), "global_id": str(global_id)}
        if depth >= 2 or value.id() in seen:
            return {
                "ifc_class": value.is_a(),
                "name": getattr(value, "Name", None),
            }
        child_seen = set(seen)
        child_seen.add(value.id())
        attributes = {}
        for index in range(len(value)):
            name = value.attribute_name(index)
            if name in {"OwnerHistory", "Representation", "RepresentationMaps"}:
                continue
            attributes[name] = _normalize_value(
                value[index], depth=depth + 1, seen=child_seen
            )
        return {"ifc_class": value.is_a(), "attributes": attributes}
    return str(value)


def _placement_snapshot(entity: Any) -> list[list[float]] | None:
    if getattr(entity, "ObjectPlacement", None) is None:
        return None
    matrix = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
    return [
        [round(float(value), 6) for value in row]
        for row in matrix.tolist()
    ]


def _type_ids(entity: Any) -> list[str]:
    ids = []
    for relation in getattr(entity, "IsDefinedBy", ()):
        if relation.is_a("IfcRelDefinesByType"):
            ids.append(str(relation.RelatingType.GlobalId))
    for relation in getattr(entity, "IsTypedBy", ()):
        ids.append(str(relation.RelatingType.GlobalId))
    return sorted(set(ids))


def _geometry_snapshot(
    entity: Any,
    *,
    fingerprinter: _ModelFingerprinter | None = None,
) -> dict[str, Any] | None:
    representation = getattr(entity, "Representation", None)
    if representation is None:
        return None
    if fingerprinter is not None:
        representation_index = next(
            (
                index
                for index in range(len(entity))
                if entity.attribute_name(index) == "Representation"
            ),
            None,
        )
        type_info = None
        if representation_index is not None:
            declaration = entity.wrapped_data.declaration().as_entity()
            type_info = declaration.all_attributes()[
                representation_index
            ].type_of_attribute()
        digest = fingerprinter.fingerprint_value(
            representation,
            type_info=type_info,
        )
        return {
            "available": True,
            "representation_sha256": "sha256:" + digest.hex(),
        }
    normalized = _normalize_representation_value(
        representation, depth=0, seen=set()
    )
    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "available": True,
        "representation_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def _normalize_representation_value(
    value: Any,
    *,
    depth: int,
    seen: set[int],
) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        return [
            _normalize_representation_value(child, depth=depth, seen=seen)
            for child in value
        ]
    if hasattr(value, "is_a") and hasattr(value, "id"):
        global_id = getattr(value, "GlobalId", None)
        if global_id:
            return {"ifc_class": value.is_a(), "global_id": str(global_id)}
        if depth >= 12 or value.id() in seen:
            return {"ifc_class": value.is_a(), "cycle": True}
        child_seen = set(seen)
        child_seen.add(value.id())
        return {
            "ifc_class": value.is_a(),
            "attributes": {
                value.attribute_name(index): _normalize_representation_value(
                    value[index], depth=depth + 1, seen=child_seen
                )
                for index in range(len(value))
            },
        }
    return str(value)


def _canonical_sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compare_ifc_with_ifcdiff(
    before_path: Path | str,
    after_path: Path | str,
    *,
    relationships: Iterable[str] = (
        "attributes",
        "geometry",
        "type",
        "property",
        "container",
        "aggregate",
        "classification",
    ),
    is_shallow: bool = False,
    filter_elements: str | None = None,
) -> dict[str, Any]:
    """Run the official IfcOpenShell IfcDiff engine for same-GlobalId facts."""

    try:
        from ifcdiff import IfcDiff
    except ImportError as exc:  # pragma: no cover - dependency contract
        raise RuntimeError("IFCDIFF_DEPENDENCY_MISSING") from exc

    before = ifcopenshell.open(str(Path(before_path)))
    after = ifcopenshell.open(str(Path(after_path)))
    requested = tuple(dict.fromkeys(str(item) for item in relationships))
    engine = IfcDiff(
        before,
        after,
        relationships=list(requested),
        is_shallow=is_shallow,
        filter_elements=filter_elements,
    )
    # IfcDiff currently prints progress messages as a library side effect. Keep
    # programmatic/CLI output machine-readable without changing its behavior.
    with contextlib.redirect_stdout(io.StringIO()):
        engine.diff()
    try:
        package_version = version("ifcdiff")
    except PackageNotFoundError:  # pragma: no cover - editable installations
        package_version = "unknown"
    return {
        "schema_version": IFCOPENSHELL_COMPARISON_SCHEMA_VERSION,
        "engine": f"IfcOpenShell.IfcDiff/{package_version}",
        "before_schema": before.schema,
        "after_schema": after.schema,
        "relationships": list(requested),
        "is_shallow": is_shallow,
        "filter_elements": filter_elements,
        "added_ids": sorted(str(item) for item in engine.added_elements),
        "deleted_ids": sorted(str(item) for item in engine.deleted_elements),
        "changed": _json_safe(engine.change_register),
    }


def compare_mapped_elements(
    before_path: Path | str,
    after_path: Path | str,
    *,
    mappings: Iterable[Mapping[str, str]],
) -> dict[str, Any]:
    """Compare semantically equivalent elements even when repair changes GUID."""

    before = ifcopenshell.open(str(Path(before_path)))
    after = ifcopenshell.open(str(Path(after_path)))
    elements: list[dict[str, Any]] = []
    for mapping in mappings:
        before_id = str(mapping["before_global_id"])
        after_id = str(mapping["after_global_id"])
        before_element = _by_guid_or_none(before, before_id)
        after_element = _by_guid_or_none(after, after_id)
        if before_element is None or after_element is None:
            elements.append(
                {
                    "role": str(mapping["role"]),
                    "before_global_id": before_id,
                    "after_global_id": after_id,
                    "status": "missing",
                    "before_found": before_element is not None,
                    "after_found": after_element is not None,
                }
            )
            continue
        before_snapshot = _mapped_element_snapshot(before_element)
        after_snapshot = _mapped_element_snapshot(after_element)
        elements.append(
            {
                "role": str(mapping["role"]),
                "before_global_id": before_id,
                "after_global_id": after_id,
                "identity_changed": before_id != after_id,
                "status": "compared",
                **{
                    section: _mapping_diff(
                        before_snapshot[section], after_snapshot[section]
                    )
                    for section in before_snapshot
                },
            }
        )
    return {
        "schema_version": IFCOPENSHELL_COMPARISON_SCHEMA_VERSION,
        "engine": "IfcOpenShell.util.element/mapped",
        "before_schema": before.schema,
        "after_schema": after.schema,
        "elements": elements,
    }


def _mapped_element_snapshot(element: Any) -> dict[str, Mapping[str, Any]]:
    return {
        "attributes": _comparison_attributes(element),
        "direct_properties": _flatten_psets(
            ifcopenshell.util.element.get_psets(element, should_inherit=False)
        ),
        "effective_properties": _flatten_psets(
            ifcopenshell.util.element.get_psets(element, should_inherit=True)
        ),
        "type": _type_snapshot(element),
        "materials": _material_snapshot(element),
        "classifications": _classification_snapshot(element),
        "container": _entity_reference_snapshot(
            ifcopenshell.util.element.get_container(element)
        ),
        "host": _host_snapshot(element),
    }


def _comparison_attributes(element: Any) -> dict[str, Any]:
    excluded = {
        "id",
        "type",
        "GlobalId",
        "OwnerHistory",
        "ObjectPlacement",
        "Representation",
    }
    return {
        str(key): _json_safe(value)
        for key, value in element.get_info().items()
        if key not in excluded
    }


def _flatten_psets(psets: Mapping[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for set_name, values in sorted(psets.items()):
        if not isinstance(values, Mapping):
            continue
        for property_name, value in sorted(values.items()):
            if property_name == "id":
                continue
            flattened[f"{set_name}.{property_name}"] = _json_safe(value)
    return flattened


def _type_snapshot(element: Any) -> dict[str, Any]:
    return _entity_reference_snapshot(ifcopenshell.util.element.get_type(element))


def _material_snapshot(element: Any) -> dict[str, Any]:
    materials = ifcopenshell.util.element.get_materials(
        element, should_inherit=True
    )
    return {
        f"{material.is_a()}:{getattr(material, 'Name', None)}:{getattr(material, 'Category', None)}": {
            "ifc_class": material.is_a(),
            "name": getattr(material, "Name", None),
            "category": getattr(material, "Category", None),
        }
        for material in materials
    }


def _classification_snapshot(element: Any) -> dict[str, Any]:
    references = ifcopenshell.util.classification.get_references(element)
    result: dict[str, Any] = {}
    for reference in references:
        key = (
            getattr(reference, "ItemReference", None)
            or getattr(reference, "Identification", None)
            or getattr(reference, "Name", None)
            or f"#{reference.id()}"
        )
        result[str(key)] = {
            "ifc_class": reference.is_a(),
            "identification": getattr(reference, "ItemReference", None)
            or getattr(reference, "Identification", None),
            "name": getattr(reference, "Name", None),
        }
    return result


def _host_snapshot(element: Any) -> dict[str, Any]:
    opening = ifcopenshell.util.element.get_filled_void(element)
    if opening is None:
        return {}
    relations = tuple(getattr(opening, "VoidsElements", ()))
    if not relations:
        return {}
    return _entity_reference_snapshot(relations[0].RelatingBuildingElement)


def _entity_reference_snapshot(entity: Any | None) -> dict[str, Any]:
    if entity is None:
        return {}
    return {
        "entity": {
            "global_id": getattr(entity, "GlobalId", None),
            "ifc_class": entity.is_a(),
            "name": getattr(entity, "Name", None),
        }
    }


def _mapping_diff(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, Any]:
    before_keys = set(before)
    after_keys = set(after)
    changed = {
        key: {"before": before[key], "after": after[key]}
        for key in sorted(before_keys & after_keys)
        if before[key] != after[key]
    }
    added = {key: after[key] for key in sorted(after_keys - before_keys)}
    removed = {key: before[key] for key in sorted(before_keys - after_keys)}
    return {
        "complete_match": not changed and not added and not removed,
        "equal_count": sum(
            before[key] == after[key] for key in before_keys & after_keys
        ),
        "changed": changed,
        "added": added,
        "removed": removed,
    }


def _by_guid_or_none(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return sorted(
            (_json_safe(item) for item in value),
            key=_canonical_sort_key,
        )
    if hasattr(value, "is_a"):
        return {
            "ifc_class": value.is_a(),
            "global_id": getattr(value, "GlobalId", None),
            "name": getattr(value, "Name", None),
        }
    return str(value)
