"""Evidence-backed semantic delta gate for a bounded repair attempt."""

from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence


def evaluate_repair_fact_delta(
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    allowed_change_paths: Sequence[str],
    evidence_by_path: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    """Reject repaired changes outside deterministic, evidence-backed paths."""
    before_leaves = _flatten(before)
    after_leaves = _flatten(after)
    changes: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for path in sorted(set(before_leaves) | set(after_leaves)):
        in_before = path in before_leaves
        in_after = path in after_leaves
        if in_before and in_after and before_leaves[path] == after_leaves[path]:
            continue
        if not in_before:
            kind = "added"
        elif not in_after:
            kind = "removed"
        else:
            kind = "changed"
        changes.append(
            {
                "path": path,
                "kind": kind,
                "before": copy.deepcopy(before_leaves.get(path)),
                "after": copy.deepcopy(after_leaves.get(path)),
            }
        )
        if not _matches_prefix(path, allowed_change_paths):
            issues.append(
                _issue(
                    "UNPERMITTED_FACT_DELTA",
                    path,
                    "Repair changed a path outside deterministic feedback.",
                )
            )
            continue
        evidence = _matching_evidence(path, evidence_by_path)
        if not evidence:
            issues.append(
                _issue(
                    "MISSING_DELTA_EVIDENCE",
                    path,
                    "Repair change has no existing user/schema/capability evidence.",
                )
            )
        elif any(_forbidden_evidence(ref) for ref in evidence):
            issues.append(
                _issue(
                    "FORBIDDEN_DELTA_EVIDENCE",
                    path,
                    "Supervisor-authored or aborted evidence cannot authorize repair.",
                )
            )
    return {
        "schema_version": "text2ifc/repair-fact-delta/1.0",
        "valid": not issues,
        "change_count": len(changes),
        "issue_count": len(issues),
        "changes": changes,
        "issues": issues,
    }


def _flatten(value: Any, path: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        if not value:
            return {path or "/": {}}
        result: dict[str, Any] = {}
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            result.update(_flatten(child, f"{path}/{token}"))
        return result
    if isinstance(value, list):
        if not value:
            return {path or "/": []}
        result = {}
        for index, child in enumerate(value):
            result.update(_flatten(child, f"{path}/{index}"))
        return result
    return {path or "/": copy.deepcopy(value)}


def _matches_prefix(path: str, prefixes: Sequence[str]) -> bool:
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _matching_evidence(
    path: str,
    evidence_by_path: Mapping[str, Sequence[str]],
) -> list[str]:
    matches = [
        (prefix, refs)
        for prefix, refs in evidence_by_path.items()
        if path == prefix or path.startswith(prefix.rstrip("/") + "/")
    ]
    if not matches:
        return []
    _, refs = max(matches, key=lambda item: len(item[0]))
    return [str(ref) for ref in refs]


def _forbidden_evidence(reference: str) -> bool:
    lowered = reference.lower()
    return lowered.startswith("supervisor:") or lowered.startswith("aborted:")


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}
