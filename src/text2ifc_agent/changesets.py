"""Schema-backed contract for component-scoped BIM JSON changes."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import ValidationIssue


CHANGESET_SCHEMA_VERSION = "text2ifc/bim-json-changeset/1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHANGESET_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "bim-json-changeset-1.0.schema.json"
)


@lru_cache(maxsize=1)
def _cached_changeset_schema() -> dict[str, Any]:
    schema = json.loads(CHANGESET_SCHEMA_PATH.read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def load_changeset_schema() -> dict[str, Any]:
    """Return a copy of the canonical ChangeSet JSON Schema."""

    return copy.deepcopy(_cached_changeset_schema())


def validate_changeset(document: Any) -> list[ValidationIssue]:
    """Return stable structural and semantic ChangeSet diagnostics."""

    validator = Draft202012Validator(_cached_changeset_schema())
    issues = [
        ValidationIssue(
            code="SCHEMA_VALIDATION_ERROR",
            path=_pointer(error.absolute_path),
            message=error.message,
        )
        for error in validator.iter_errors(document)
    ]
    if issues or not isinstance(document, dict):
        return _sort_issues(issues)
    issues.extend(_semantic_issues(document))
    return _sort_issues(issues)


def canonical_changeset_json(document: Any) -> str:
    """Serialize one valid ChangeSet deterministically without mutation."""

    issues = validate_changeset(document)
    if issues:
        raise ValueError(f"invalid ChangeSet: {issues[0].code} at {issues[0].path}")
    return json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _semantic_issues(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    operation_ids: set[str] = set()
    targets: set[tuple[str, str]] = set()
    declared_issues = set(document["source_issue_ids"])
    for index, operation in enumerate(document["operations"]):
        operation_id = operation["operation_id"]
        if operation_id in operation_ids:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_CHANGESET_OPERATION_ID",
                    path=f"/operations/{index}/operation_id",
                    message=f"Operation ID {operation_id!r} is duplicated.",
                )
            )
        operation_ids.add(operation_id)

        collection = "relationship" if operation["op"].endswith("relationship") else "entity"
        target = (collection, operation["target_id"])
        if target in targets:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_CHANGESET_TARGET",
                    path=f"/operations/{index}/target_id",
                    message=f"ChangeSet target {target[1]!r} is duplicated.",
                )
            )
        targets.add(target)

        if operation["op"] in {"add_entity", "add_relationship"}:
            provenance = operation["value"].get("provenance")
            if not isinstance(provenance, dict) or not provenance:
                issues.append(
                    ValidationIssue(
                        code="EMPTY_CHANGESET_PROVENANCE",
                        path=f"/operations/{index}/value/provenance",
                        message=(
                            "Added components require non-empty provenance tied "
                            "to existing evidence."
                        ),
                    )
                )

        for evidence_index, evidence_ref in enumerate(operation["evidence_refs"]):
            issue_id = evidence_ref.split(":/", 1)[0]
            if issue_id not in declared_issues:
                issues.append(
                    ValidationIssue(
                        code="UNDECLARED_CHANGESET_EVIDENCE",
                        path=f"/operations/{index}/evidence_refs/{evidence_index}",
                        message=f"Evidence references undeclared issue {issue_id!r}.",
                    )
                )
    return issues


def _assert_local_references(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise ValueError(f"Remote schema references are forbidden: {child!r}")
            _assert_local_references(child)
    elif isinstance(value, list):
        for child in value:
            _assert_local_references(child)


def _pointer(parts: Iterable[Any]) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else "/"


def _sort_issues(issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
    return sorted(set(issues), key=lambda issue: (issue.path, issue.code, issue.message))
