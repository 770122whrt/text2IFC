"""Phase 6.3 complex-building regression fixture helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


FIXTURE_SCHEMA_VERSION = "text2ifc/phase6.3-complex-manual-review/1.0"


class ComplexFixtureError(ValueError):
    """Raised when a Phase 6.3 complex fixture is malformed."""


def load_complex_fixture(fixture_dir: Path | str) -> dict[str, Any]:
    """Load the Phase 6.3 Wave 0 complex fixture and manual review truth."""
    root = Path(fixture_dir)
    input_path = root / "input.txt"
    review_path = root / "expected-manual-review.json"
    if not input_path.is_file():
        raise ComplexFixtureError(f"missing fixture input: {input_path}")
    if not review_path.is_file():
        raise ComplexFixtureError(f"missing fixture review truth: {review_path}")

    review = _read_json(review_path)
    if review.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        raise ComplexFixtureError("unexpected complex fixture schema_version")
    expectations = review.get("expectations")
    if not isinstance(expectations, Mapping):
        raise ComplexFixtureError("complex fixture expectations must be an object")
    if expectations.get("production_rule") is not False:
        raise ComplexFixtureError("Wave 0 fixture truth must not be production logic")

    return {
        "fixture_dir": str(root),
        "input_text": input_path.read_text(encoding="utf-8"),
        "expectations": dict(expectations),
        "metadata": review,
    }


def assess_no_false_accept_baseline(
    expectations: Mapping[str, Any],
    candidate_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a Wave 0 no-false-accept decision for manual fixture evidence.

    This is deliberately fixture-facing baseline logic. Later Phase 6.3 waves
    generalize these checks into dynamic expected facts, gates, and routes.
    """
    issues: list[dict[str, Any]] = []
    compile_reopen_success = candidate_evidence.get("compile_reopen_success") is True
    if not compile_reopen_success:
        issues.append(
            _issue(
                "COMPILE_REOPEN_FAILED",
                expected=True,
                actual=candidate_evidence.get("compile_reopen_success"),
            )
        )

    expected_counts = {
        "IfcBuildingStorey": expectations.get("storey_count"),
        "IfcSpace": _sum_count(expectations.get("space_counts")),
        "IfcDoor": _count_total(expectations.get("door_counts")),
        "IfcWindow": _count_total(expectations.get("window_counts")),
    }
    observed_counts = candidate_evidence.get("counts", {})
    if isinstance(observed_counts, Mapping):
        for ifc_class, expected in expected_counts.items():
            if expected is None:
                continue
            actual = observed_counts.get(ifc_class)
            if actual != expected:
                issues.append(
                    _issue(
                        "REQUESTED_ENTITY_COUNT_MISMATCH",
                        path=f"/counts/{ifc_class}",
                        expected=expected,
                        actual=actual,
                    )
                )

    expected_doors_by_storey = expectations.get("door_counts", {})
    observed_doors_by_storey = candidate_evidence.get("doors_by_storey", {})
    if isinstance(expected_doors_by_storey, Mapping) and isinstance(
        observed_doors_by_storey, Mapping
    ):
        for storey_id, expected in expected_doors_by_storey.items():
            if storey_id == "total":
                continue
            actual = observed_doors_by_storey.get(storey_id, 0)
            if actual != expected:
                issues.append(
                    _issue(
                        "REQUESTED_DOORS_MISSING",
                        path=f"/doors_by_storey/{storey_id}",
                        expected=expected,
                        actual=actual,
                    )
                )

    obligations = expectations.get("opening_fill_obligations", {})
    if isinstance(obligations, Mapping):
        if obligations.get("doors_require_opening_and_fill") is True:
            _append_opening_fill_issue(
                issues,
                candidate_evidence,
                field="doors_with_opening_fill_count",
                expected=_count_total(expectations.get("door_counts")),
            )
        if obligations.get("windows_require_opening_and_fill") is True:
            _append_opening_fill_issue(
                issues,
                candidate_evidence,
                field="windows_with_opening_fill_count",
                expected=_count_total(expectations.get("window_counts")),
            )

    if candidate_evidence.get("containment_success") is False:
        issues.append(
            _issue(
                "CONTAINMENT_INCOMPLETE",
                path="/containment_success",
                expected=True,
                actual=False,
            )
        )

    accepted = compile_reopen_success and not issues
    return {
        "schema_version": "text2ifc/phase6.3-no-false-accept-baseline/1.0",
        "status": "accepted" if accepted else "blocked",
        "accepted": accepted,
        "compile_reopen_success": compile_reopen_success,
        "issues": issues,
    }


def _append_opening_fill_issue(
    issues: list[dict[str, Any]],
    candidate_evidence: Mapping[str, Any],
    *,
    field: str,
    expected: int | None,
) -> None:
    if expected is None:
        return
    actual = candidate_evidence.get(field)
    if actual != expected:
        issues.append(
            _issue(
                "OPENING_FILL_RELATIONSHIPS_MISSING",
                path=f"/{field}",
                expected=expected,
                actual=actual,
            )
        )


def _count_total(value: Any) -> int | None:
    if not isinstance(value, Mapping):
        return None
    total = value.get("total")
    return int(total) if isinstance(total, int) else None


def _sum_count(value: Any) -> int | None:
    if not isinstance(value, Mapping):
        return None
    total = 0
    for count in value.values():
        if not isinstance(count, int):
            return None
        total += count
    return total


def _issue(
    code: str,
    *,
    path: str = "/",
    expected: Any,
    actual: Any,
) -> dict[str, Any]:
    return {
        "code": code,
        "path": path,
        "expected": expected,
        "actual": actual,
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ComplexFixtureError(f"expected object in {path}")
    return payload
