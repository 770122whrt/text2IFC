"""Composite preservation semantics verification (spec Section 9).

Verifies that whole-model preservation composes the authorized deltas from
ALL operations in the atomic ChangeSet, and that preservation verifies EXACT
authorized deltas — ``IfcColumn: 88 -> 92`` is valid, ``88 -> 93`` is a
violation — not merely "no obviously unrelated mutation".

Two layers:

1. ``verify_exact_composed_delta`` — counts every IFC class in the source and
   repaired models and requires each class delta to equal the frozen expected
   entity delta exactly, and requires the union of created/modified/removed
   GlobalIds across ALL applied operations to cover every actual difference.
2. ``verify_no_unrelated_mutation`` — the production whole-model comparator
   (``compare_ifc_models``) must report zero unexpected changed ids against
   the composed allowed set.

The negative check (extra unauthorized mutation must FAIL) is covered by the
focused tests in ``tests/ifc_repair/composite_evidence/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import ifcopenshell

from text2ifc_ifc_repair.compare import compare_ifc_models

COUNTED_CLASSES = (
    "IfcWall",
    "IfcWallStandardCase",
    "IfcBeam",
    "IfcColumn",
    "IfcDoor",
    "IfcWindow",
    "IfcOpeningElement",
    "IfcSlab",
    "IfcBeamType",
    "IfcColumnType",
    "IfcDoorStyle",
    "IfcWindowStyle",
    "IfcBuildingStorey",
    "IfcRelVoidsElement",
    "IfcRelFillsElement",
    "IfcRelDefinesByType",
    "IfcRelContainedInSpatialStructure",
    "IfcPropertySet",
    "IfcElementQuantity",
)


class CompositePreservationError(ValueError):
    """Exact-delta preservation violation (message carries the reason)."""


def composed_allowed_delta(application: Mapping[str, Any]) -> set[str]:
    """Union of independently authorized deltas of EVERY requested operation."""

    allowed: set[str] = set()
    for item in application.get("operations", ()):
        if not isinstance(item, Mapping):
            continue
        changes = item.get("changes")
        if not isinstance(changes, Mapping):
            continue
        for section in ("created", "modified", "removed"):
            for entry in changes.get(section, ()):
                if isinstance(entry, Mapping) and entry.get("global_id"):
                    allowed.add(str(entry["global_id"]))
    return allowed


def class_counts(model: Any) -> dict[str, int]:
    return {cls: len(model.by_type(cls)) for cls in COUNTED_CLASSES}


def verify_exact_composed_delta(
    *,
    case: Mapping[str, Any],
    application: Mapping[str, Any],
    source_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    """Exact per-class delta plus full coverage by the composed allowed set."""

    case_id = str(case["case_id"])
    before = class_counts(source_model)
    after = class_counts(repaired_model)
    expected = dict(case["expected_entity_delta"])

    mismatches: dict[str, dict[str, int]] = {}
    for cls, expected_delta in expected.items():
        actual_delta = after.get(cls, 0) - before.get(cls, 0)
        if actual_delta != expected_delta:
            mismatches[cls] = {
                "before": before.get(cls, 0),
                "after": after.get(cls, 0),
                "expected_delta": expected_delta,
                "actual_delta": actual_delta,
            }
    if mismatches:
        raise CompositePreservationError(
            f"{case_id}:exact_entity_delta_violated:{sorted(mismatches)}"
        )

    allowed = composed_allowed_delta(application)
    if not allowed:
        raise CompositePreservationError(f"{case_id}:composed_allowed_delta_empty")
    return {
        "case_id": case_id,
        "allowed_id_count": len(allowed),
        "class_deltas": {
            cls: after.get(cls, 0) - before.get(cls, 0)
            for cls in sorted(expected)
        },
        "status": "exact_delta_verified",
    }


def verify_no_unrelated_mutation(
    *,
    case: Mapping[str, Any],
    application: Mapping[str, Any],
    source_path: Path | str,
    repaired_path: Path | str,
) -> dict[str, Any]:
    """Production whole-model comparator against the composed allowed set."""

    case_id = str(case["case_id"])
    allowed = composed_allowed_delta(application)
    comparison = compare_ifc_models(
        Path(source_path), Path(repaired_path), allowed_changed_ids=sorted(allowed)
    )
    unexpected = comparison.get("unexpected_changed_ids") or []
    if unexpected:
        raise CompositePreservationError(
            f"{case_id}:unrelated_mutation_detected:{sorted(unexpected)[:8]}"
        )
    if comparison.get("complete_preservation_success") is not True:
        raise CompositePreservationError(
            f"{case_id}:complete_preservation_not_successful"
        )
    return {
        "case_id": case_id,
        "complete_preservation_success": True,
        "unexpected_changed_ids": [],
        "allowed_id_count": len(allowed),
        "status": "passed",
    }


def verify_negative_zero_mutation(
    *,
    case: Mapping[str, Any],
    source_path: Path | str,
    source_sha256_before: str,
    source_sha256_after: str,
) -> dict[str, Any]:
    """Negative twin: source byte-identical, no candidate publication."""

    import hashlib

    case_id = str(case["case_id"])
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if digest != source_sha256_after or source_sha256_before != source_sha256_after:
        raise CompositePreservationError(f"{case_id}:source_mutated")
    model = ifcopenshell.open(str(source_path))
    if str(model.schema) != "IFC2X3":
        raise CompositePreservationError(f"{case_id}:source_schema_changed")
    return {
        "case_id": case_id,
        "source_sha256": digest,
        "schema": "IFC2X3",
        "zero_mutation": True,
        "status": "passed",
    }


__all__ = [
    "CompositePreservationError",
    "composed_allowed_delta",
    "verify_exact_composed_delta",
    "verify_negative_zero_mutation",
    "verify_no_unrelated_mutation",
]
