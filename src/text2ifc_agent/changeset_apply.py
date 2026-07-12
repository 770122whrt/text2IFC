"""Transactional application of authorized BIM JSON ChangeSets."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from text2ifc_agent.candidate_index import CandidateIndexError, build_candidate_index
from text2ifc_agent.changesets import validate_changeset
from text2ifc_agent.revisions import (
    hash_json_value,
    validate_change_scope,
    validate_revision_record,
)
from text2ifc_contract.validation_v2 import validate_v2_document


def apply_changeset(
    *,
    candidate: Mapping[str, Any],
    changeset: Mapping[str, Any],
    scope: Mapping[str, Any],
    base_revision: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply a valid ChangeSet atomically or return no promoted candidate."""

    try:
        before_index = build_candidate_index(candidate)
    except CandidateIndexError as error:
        return _failure("CHANGESET_BASE_CANDIDATE_INVALID", "/candidate", str(error))

    issues = _preflight_issues(
        candidate=candidate,
        before_index=before_index,
        changeset=changeset,
        scope=scope,
        base_revision=base_revision,
        expected_facts=expected_facts,
    )
    if issues:
        return _failure_many(issues)

    composed = copy.deepcopy(dict(candidate))
    try:
        _apply_operations(composed, changeset["operations"])
    except (KeyError, IndexError, TypeError, ValueError) as error:
        return _failure("CHANGESET_APPLICATION_ERROR", "/operations", str(error))
    composed["entities"] = sorted(composed["entities"], key=lambda item: item["id"])
    composed["relationships"] = sorted(
        composed["relationships"], key=lambda item: item["id"]
    )

    formal_issues = validate_v2_document(composed)
    if formal_issues:
        return _failure_many(
            [
                _issue(
                    "CHANGESET_CANDIDATE_INVALID",
                    issue.path,
                    f"{issue.code}: {issue.message}",
                )
                for issue in formal_issues
            ]
        )

    after_index = build_candidate_index(composed)
    preservation = _preservation_report(before_index, after_index, scope)
    if preservation["forbidden_drift_ids"]:
        return _failure(
            "CHANGESET_SCOPE_VIOLATION",
            "/preservation/forbidden_drift_ids",
            "Applied result changed components outside the authorized scope.",
        )

    sequence = int(base_revision["sequence"]) + 1
    revision_id = f"revision-{sequence:02d}"
    revision = {
        "schema_version": "text2ifc/bim-json-revision/1.0",
        "revision_id": revision_id,
        "sequence": sequence,
        "parent_revision_id": base_revision["revision_id"],
        "candidate_hash": after_index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected_facts),
        "component_hashes": after_index["component_hashes"],
        "source_route": "changeset",
        "artifacts": {
            "candidate": f"revisions/{revision_id}/candidate.json",
            "changeset": f"revisions/{revision_id}/changeset.json",
        },
    }
    revision_issues = validate_revision_record(
        revision,
        candidate=composed,
        expected_facts=expected_facts,
    )
    if revision_issues:
        return _failure_many(
            [
                _issue("CHANGESET_REVISION_INVALID", issue.path, issue.message)
                for issue in revision_issues
            ]
        )
    return {
        "valid": True,
        "candidate": composed,
        "revision": revision,
        "preservation": preservation,
        "issues": [],
    }


def _preflight_issues(
    *,
    candidate: Mapping[str, Any],
    before_index: Mapping[str, Any],
    changeset: Mapping[str, Any],
    scope: Mapping[str, Any],
    base_revision: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    changeset_contract = validate_changeset(changeset)
    issues.extend(
        _issue("CHANGESET_CONTRACT_ERROR", issue.path, issue.message)
        for issue in changeset_contract
    )
    scope_contract = validate_change_scope(scope)
    issues.extend(
        _issue("CHANGESET_SCOPE_CONTRACT_ERROR", issue.path, issue.message)
        for issue in scope_contract
    )
    if issues:
        return _sorted_issues(issues)

    current_hash = before_index["candidate_hash"]
    if current_hash != base_revision.get("candidate_hash"):
        issues.append(
            _issue(
                "CHANGESET_BASE_HASH_MISMATCH",
                "/base_candidate_hash",
                "Current candidate does not match the bound base revision.",
            )
        )
    if changeset["base_candidate_hash"] != base_revision.get("candidate_hash"):
        issues.append(
            _issue(
                "CHANGESET_BASE_HASH_MISMATCH",
                "/base_candidate_hash",
                "ChangeSet base hash does not match the bound revision.",
            )
        )
    if changeset["expected_facts_hash"] != hash_json_value(expected_facts):
        issues.append(
            _issue(
                "CHANGESET_EXPECTED_FACTS_HASH_MISMATCH",
                "/expected_facts_hash",
                "ChangeSet expected-facts hash is stale.",
            )
        )
    if (
        changeset["base_revision_id"] != base_revision.get("revision_id")
        or scope["base_revision_id"] != base_revision.get("revision_id")
        or changeset["scope_id"] != scope["scope_id"]
    ):
        issues.append(
            _issue(
                "CHANGESET_SCOPE_BINDING_MISMATCH",
                "/scope_id",
                "ChangeSet, scope, and base revision bindings must agree.",
            )
        )
    if set(changeset["source_issue_ids"]) != set(scope["source_issue_ids"]):
        issues.append(
            _issue(
                "CHANGESET_SCOPE_BINDING_MISMATCH",
                "/source_issue_ids",
                "ChangeSet and scope must bind the same source Issues.",
            )
        )
    revision_contract = validate_revision_record(
        base_revision,
        candidate=candidate,
        expected_facts=expected_facts,
    )
    issues.extend(
        _issue("CHANGESET_BASE_REVISION_INVALID", issue.path, issue.message)
        for issue in revision_contract
        if issue.code
        not in {
            "REVISION_CANDIDATE_HASH_MISMATCH",
            "REVISION_EXPECTED_FACTS_HASH_MISMATCH",
        }
    )
    if issues:
        return _sorted_issues(issues)

    entities = before_index["entities"]
    relationships = before_index["relationships"]
    component_hashes = before_index["component_hashes"]
    allowed_entities = set(scope["entity_ids"])
    allowed_relationships = set(scope["relationship_ids"])
    removals = {
        operation["target_id"]
        for operation in changeset["operations"]
        if operation["op"].startswith("remove_")
    }
    for index, operation in enumerate(changeset["operations"]):
        op = operation["op"]
        target_id = operation["target_id"]
        is_entity = op.endswith("entity")
        collection = entities if is_entity else relationships
        allowed = allowed_entities if is_entity else allowed_relationships
        path = f"/operations/{index}"
        if target_id not in allowed:
            issues.append(
                _issue(
                    "CHANGESET_SCOPE_VIOLATION",
                    f"{path}/target_id",
                    f"Target {target_id!r} is outside the allowed scope.",
                )
            )
        if op.startswith("add_"):
            if target_id in collection:
                issues.append(
                    _issue(
                        "CHANGESET_TARGET_ALREADY_EXISTS",
                        f"{path}/target_id",
                        f"Target {target_id!r} already exists.",
                    )
                )
            if operation["value"].get("id") != target_id:
                issues.append(
                    _issue(
                        "CHANGESET_TARGET_ID_MISMATCH",
                        f"{path}/value/id",
                        "Added value ID must equal target_id.",
                    )
                )
            continue
        if target_id not in collection:
            issues.append(
                _issue(
                    "CHANGESET_TARGET_NOT_FOUND",
                    f"{path}/target_id",
                    f"Target {target_id!r} does not exist.",
                )
            )
            continue
        if operation["target_component_hash"] != component_hashes[target_id]:
            issues.append(
                _issue(
                    "CHANGESET_TARGET_HASH_MISMATCH",
                    f"{path}/target_component_hash",
                    f"Target {target_id!r} changed since the ChangeSet was prepared.",
                )
            )
        if op.startswith("update_"):
            permitted = scope["allowed_paths"].get(target_id, [])
            for change_path in operation["changes"]:
                if change_path in {"/id", "/ifc_class"}:
                    issues.append(
                        _issue(
                            "CHANGESET_IMMUTABLE_FIELD",
                            f"{path}/changes/{_escape(change_path)}",
                            "Stable identity and IFC class cannot be updated.",
                        )
                    )
                elif not any(_path_allowed(change_path, prefix) for prefix in permitted):
                    issues.append(
                        _issue(
                            "CHANGESET_SCOPE_VIOLATION",
                            f"{path}/changes/{_escape(change_path)}",
                            f"Path {change_path!r} is outside the authorized field scope.",
                        )
                    )
        elif is_entity:
            referenced_by = [
                relationship_id
                for relationship_id, relationship in relationships.items()
                if relationship_id not in removals
                and _contains_id(relationship.get("attributes"), target_id)
            ]
            if referenced_by:
                issues.append(
                    _issue(
                        "CHANGESET_DEPENDENCY_VIOLATION",
                        f"{path}/target_id",
                        f"Removing {target_id!r} would orphan {sorted(referenced_by)}.",
                    )
                )
    return _sorted_issues(issues)


def _apply_operations(candidate: dict[str, Any], operations: Sequence[Mapping[str, Any]]) -> None:
    for operation in operations:
        op = operation["op"]
        collection_name = "entities" if op.endswith("entity") else "relationships"
        collection = candidate[collection_name]
        target_id = operation["target_id"]
        if op.startswith("add_"):
            collection.append(copy.deepcopy(operation["value"]))
            continue
        target_index = next(
            index for index, component in enumerate(collection) if component["id"] == target_id
        )
        if op.startswith("remove_"):
            del collection[target_index]
            continue
        target = collection[target_index]
        for pointer, value in sorted(operation["changes"].items()):
            _set_pointer(target, pointer, copy.deepcopy(value))


def _set_pointer(target: Any, pointer: str, value: Any) -> None:
    tokens = [_unescape(token) for token in pointer.lstrip("/").split("/")]
    if not tokens or tokens == [""]:
        raise ValueError("root replacement is forbidden")
    current = target
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    final = tokens[-1]
    if isinstance(current, list):
        current[int(final)] = value
    else:
        current[final] = value


def _preservation_report(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    scope: Mapping[str, Any],
) -> dict[str, Any]:
    before_hashes = before["component_hashes"]
    after_hashes = after["component_hashes"]
    all_ids = set(before_hashes) | set(after_hashes)
    changed = sorted(
        component_id
        for component_id in all_ids
        if before_hashes.get(component_id) != after_hashes.get(component_id)
    )
    authorized = set(scope["entity_ids"]) | set(scope["relationship_ids"])
    unrelated = sorted(all_ids - authorized)
    preserved_unrelated = [
        component_id
        for component_id in unrelated
        if before_hashes.get(component_id) == after_hashes.get(component_id)
    ]
    rate = len(preserved_unrelated) / len(unrelated) if unrelated else 1.0
    dependency_ids = sorted(
        {
            dependency["dependency_id"]
            for dependency in scope.get("dependencies", [])
        }
    )
    return {
        "schema_version": "text2ifc/component-preservation/1.0",
        "changed_ids": changed,
        "dependency_ids": dependency_ids,
        "unchanged_ids": sorted(all_ids - set(changed)),
        "forbidden_drift_ids": sorted(set(changed) - authorized),
        "unrelated_component_count": len(unrelated),
        "unrelated_component_preservation_rate": rate,
    }


def _path_allowed(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def _contains_id(value: Any, target_id: str) -> bool:
    if isinstance(value, str):
        return value == target_id
    if isinstance(value, Mapping):
        return any(_contains_id(child, target_id) for child in value.values())
    if isinstance(value, list):
        return any(_contains_id(child, target_id) for child in value)
    return False


def _unescape(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _sorted_issues(issues: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    return [
        dict(issue)
        for issue in sorted(issues, key=lambda item: (item["code"], item["path"], item["message"]))
    ]


def _failure(code: str, path: str, message: str) -> dict[str, Any]:
    return _failure_many([_issue(code, path, message)])


def _failure_many(issues: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    return {
        "valid": False,
        "candidate": None,
        "revision": None,
        "preservation": None,
        "issues": _sorted_issues(issues),
    }
