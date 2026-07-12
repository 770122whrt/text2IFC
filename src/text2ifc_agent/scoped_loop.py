"""Deterministic preparation and application of scoped model corrections."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .candidate_index import build_candidate_index
from .change_scope import derive_change_scope
from .changeset_apply import apply_changeset
from .changeset_stage import run_changeset_stage
from .issues import Issue
from .revisions import hash_json_value


_COLLECTION_REF = re.compile(
    r"^/(?P<collection>entities|relationships)/(?P<selector>[^/]+)(?P<path>/.*)$"
)
_STABLE_REF = re.compile(r"^(entity|relationship):[A-Za-z][A-Za-z0-9._:-]*#/.*$")


def resolve_issue_component_refs(
    *,
    candidate: Mapping[str, Any],
    issues: Sequence[Issue | Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve exact candidate collection refs to stable component refs."""

    resolved: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for issue in issues:
        payload = issue.to_dict() if isinstance(issue, Issue) else dict(issue)
        actual_ref = str(payload.get("actual_ref") or "")
        if _STABLE_REF.fullmatch(actual_ref):
            resolved.append(payload)
            continue
        match = _COLLECTION_REF.fullmatch(actual_ref)
        if match is None:
            diagnostics.append(_unresolved(payload, actual_ref))
            continue
        collection_name = match.group("collection")
        collection = candidate.get(collection_name)
        component = _resolve_component(collection, match.group("selector"))
        if component is None:
            diagnostics.append(_unresolved(payload, actual_ref))
            continue
        kind = "entity" if collection_name == "entities" else "relationship"
        payload["actual_ref"] = f"{kind}:{component['id']}#{match.group('path')}"
        resolved.append(payload)
    return {"resolved": resolved, "issues": diagnostics}


def run_scoped_changeset_round(
    *,
    provider: Any,
    output_dir: Path | str,
    case_id: str,
    round_number: int,
    user_request: str,
    conversation: list[dict[str, Any]],
    design_brief: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
    candidate: Mapping[str, Any],
    issues: Sequence[Issue | Mapping[str, Any]],
    trace_level: str | None = "debug",
    base_revision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate, validate, and transactionally apply one bounded ChangeSet."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    revision = dict(base_revision or _initial_revision(candidate, expected_facts))
    resolved = resolve_issue_component_refs(candidate=candidate, issues=issues)
    if resolved["issues"]:
        return _blocked("scope_unresolved", resolved["issues"])

    next_sequence = int(revision["sequence"]) + 1
    scope_result = derive_change_scope(
        candidate=candidate,
        issues=resolved["resolved"],
        scope_id=f"scope-revision-{next_sequence:02d}",
        base_revision_id=str(revision["revision_id"]),
    )
    if scope_result["scope"] is None:
        return _blocked("scope_unresolved", scope_result["issues"])
    scope = scope_result["scope"]
    _write_json(output / "base-revision.json", revision)
    _write_json(output / "resolved-issues.json", {"issues": resolved["resolved"]})
    _write_json(output / "change-scope.json", scope)

    stage = run_changeset_stage(
        provider=provider,
        output_dir=output,
        case_id=case_id,
        call_index=round_number,
        user_request=user_request,
        conversation=conversation,
        design_brief=design_brief,
        expected_facts=expected_facts,
        candidate=candidate,
        base_revision=revision,
        scope=scope,
        issues=resolved["resolved"],
        trace_level=trace_level,
    )
    if not stage["valid"] or stage["classification"] != "changeset":
        return {
            **_blocked(stage["classification"], stage["diagnostics"]),
            "stage": stage,
            "scope": scope,
        }

    changeset = _read_json(output / "changeset.json")
    applied = apply_changeset(
        candidate=candidate,
        changeset=changeset,
        scope=scope,
        base_revision=revision,
        expected_facts=expected_facts,
    )
    _write_json(
        output / "application.json",
        {
            "valid": applied["valid"],
            "issues": applied["issues"],
            "preservation": applied["preservation"],
            "revision": applied["revision"],
        },
    )
    if not applied["valid"]:
        return {
            **_blocked("application_blocked", applied["issues"]),
            "stage": stage,
            "scope": scope,
        }

    new_revision = applied["revision"]
    revision_dir = output / "revisions" / str(new_revision["revision_id"])
    revision_dir.mkdir(parents=True, exist_ok=True)
    _write_json(revision_dir / "candidate.json", applied["candidate"])
    _write_json(revision_dir / "changeset.json", changeset)
    _write_json(revision_dir / "revision.json", new_revision)
    return {
        "valid": True,
        "status": "applied",
        "candidate": applied["candidate"],
        "revision": new_revision,
        "preservation": applied["preservation"],
        "issues": [],
        "scope": scope,
        "stage": stage,
    }


def _initial_revision(
    candidate: Mapping[str, Any], expected_facts: Mapping[str, Any]
) -> dict[str, Any]:
    index = build_candidate_index(candidate)
    return {
        "schema_version": "text2ifc/bim-json-revision/1.0",
        "revision_id": "revision-00",
        "sequence": 0,
        "parent_revision_id": None,
        "candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected_facts),
        "component_hashes": index["component_hashes"],
        "source_route": "initial_generation",
        "artifacts": {"candidate": "revisions/revision-00/candidate.json"},
    }


def _resolve_component(collection: Any, selector: str) -> Mapping[str, Any] | None:
    if not isinstance(collection, list):
        return None
    if selector.isdigit():
        index = int(selector)
        if 0 <= index < len(collection) and isinstance(collection[index], Mapping):
            return collection[index]
        return None
    return next(
        (
            component
            for component in collection
            if isinstance(component, Mapping) and component.get("id") == selector
        ),
        None,
    )


def _unresolved(issue: Mapping[str, Any], reference: str) -> dict[str, str]:
    return {
        "code": "CHANGESET_TARGET_UNRESOLVED",
        "path": str(issue.get("issue_id") or "/"),
        "message": f"Issue reference {reference!r} cannot be resolved to one stable component.",
    }


def _blocked(status: str, issues: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "valid": False,
        "status": status,
        "candidate": None,
        "revision": None,
        "preservation": None,
        "issues": [dict(issue) for issue in issues],
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
