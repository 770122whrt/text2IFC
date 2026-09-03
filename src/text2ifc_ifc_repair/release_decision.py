"""Authoritative fail-closed L0/L1/L2 release decision."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "text2ifc/ifc-repair-release-decision/0.1"


def build_release_decision(
    *,
    l0_pass: bool,
    production_evaluation: Mapping[str, Any],
    blocking_findings: Iterable[Mapping[str, Any]] = (),
    warnings: Iterable[Mapping[str, Any]] = (),
    diagnostics: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    operations = production_evaluation.get("operations")
    l1_pass = _all_operation_levels_pass(operations, "L1")
    l2_pass = _all_operation_levels_pass(operations, "L2")
    blockers = [dict(item) for item in blocking_findings]
    evaluation_publishable = (
        production_evaluation.get(
            "successful_artifact_publishable"
        )
        is True
    )
    publishable = bool(
        l0_pass
        and l1_pass
        and l2_pass
        and evaluation_publishable
        and not blockers
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "l0_pass": bool(l0_pass),
        "l1_pass": l1_pass,
        "l2_pass": l2_pass,
        "publishable": publishable,
        "blocking_findings": blockers,
        "warnings": [dict(item) for item in warnings],
        "diagnostics": [dict(item) for item in diagnostics],
        "production_evaluation_status": production_evaluation.get(
            "status", "missing"
        ),
    }


def _all_operation_levels_pass(
    operations: Any,
    level_name: str,
) -> bool:
    if not isinstance(operations, list) or not operations:
        return False
    for operation in operations:
        levels = operation.get("levels")
        if not isinstance(levels, list):
            return False
        matching = [
            level
            for level in levels
            if level.get("level") == level_name
        ]
        if len(matching) != 1 or matching[0].get("status") != "passed":
            return False
    return True


__all__ = ["SCHEMA_VERSION", "build_release_decision"]
