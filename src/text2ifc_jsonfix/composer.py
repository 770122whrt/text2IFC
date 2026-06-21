"""Deterministic, validation-gated BIM JSON patch composition."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

from text2ifc_contract.validation import ValidationIssue
from text2ifc_contract.validation_v2 import validate_v2_document

from .diagnostics import CompositionDiagnostic, diagnostic
from .validation import validate_patch_document


@dataclass(frozen=True)
class ProvenanceEvent:
    collection: str
    object_id: str
    path: str
    origin: str
    layer_id: str
    layer_kind: str
    operation: str
    layer_provenance: dict[str, Any]
    previous_value: Any = None
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompositionResult:
    document: dict[str, Any]
    diagnostics: tuple[CompositionDiagnostic, ...]
    formal_issues: tuple[ValidationIssue, ...]
    provenance_events: tuple[ProvenanceEvent, ...]

    @property
    def formal_valid(self) -> bool:
        return not self.formal_issues

    @property
    def valid(self) -> bool:
        return self.formal_valid and not any(
            item.severity == "error" for item in self.diagnostics
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "formal_valid": self.formal_valid,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "formal_issues": [
                {
                    "code": item.code,
                    "path": item.path,
                    "message": item.message,
                }
                for item in self.formal_issues
            ],
            "provenance_events": [
                item.to_dict() for item in self.provenance_events
            ],
            "document": self.document,
        }


def _error_result(
    base_document: dict[str, Any],
    diagnostics: Iterable[CompositionDiagnostic],
    *,
    formal_issues: Iterable[ValidationIssue] = (),
) -> CompositionResult:
    return CompositionResult(
        document=copy.deepcopy(base_document),
        diagnostics=tuple(diagnostics),
        formal_issues=tuple(formal_issues),
        provenance_events=(),
    )


def _object_index(document: dict[str, Any]) -> dict[str, tuple[str, dict]]:
    return {
        record["id"]: (collection, record)
        for collection in ("entities", "relationships")
        for record in document[collection]
    }


def _operation_path(patch_index: int, layer_index: int, operation_index: int) -> str:
    return (
        f"/patches/{patch_index}/layers/{layer_index}/operations/"
        f"{operation_index}"
    )


def _set_value(
    container: dict[str, Any],
    key: str,
    value: Any,
    operation: dict[str, Any],
    *,
    path: str,
    layer_id: str,
    operation_index: int,
) -> tuple[CompositionDiagnostic | None, Any]:
    existed = key in container
    previous = container.get(key)
    if existed and previous != value and not operation.get("overwrite"):
        return (
            diagnostic(
                "SOURCE_FACT_CONFLICT",
                path,
                "The patch would overwrite an existing fact without explicit intent.",
                layer_id=layer_id,
                operation_index=operation_index,
            ),
            previous,
        )
    container[key] = copy.deepcopy(value)
    if existed and previous != value and operation.get("overwrite"):
        return (
            diagnostic(
                "SOURCE_FACT_OVERWRITTEN",
                path,
                "An existing fact was explicitly overwritten and remains auditable.",
                severity="warning",
                layer_id=layer_id,
                operation_index=operation_index,
            ),
            previous,
        )
    return None, previous


def _resolve_record(
    candidate: dict[str, Any],
    target: dict[str, Any],
    *,
    path: str,
    layer_id: str,
    operation_index: int,
) -> tuple[dict[str, Any] | None, CompositionDiagnostic | None]:
    collection = target["collection"]
    object_id = target["id"]
    if collection not in {"entities", "relationships"}:
        return None, diagnostic(
            "INVALID_TARGET_COLLECTION",
            f"{path}/target/collection",
            "This operation requires an entity or relationship target.",
            layer_id=layer_id,
            operation_index=operation_index,
        )
    matches = [
        record for record in candidate[collection] if record["id"] == object_id
    ]
    if not matches:
        return None, diagnostic(
            "TARGET_NOT_FOUND",
            f"{path}/target/id",
            f"Target {object_id!r} does not exist in {collection}.",
            layer_id=layer_id,
            operation_index=operation_index,
        )
    if len(matches) > 1:
        return None, diagnostic(
            "AMBIGUOUS_TARGET_ID",
            f"{path}/target/id",
            f"Target {object_id!r} resolves to more than one record.",
            layer_id=layer_id,
            operation_index=operation_index,
        )
    return matches[0], None


def _add_record(
    candidate: dict[str, Any],
    operation: dict[str, Any],
    *,
    expected_collection: str,
    path: str,
    layer_id: str,
    operation_index: int,
) -> tuple[CompositionDiagnostic | None, ProvenanceEvent | None]:
    target = operation["target"]
    value = operation["value"]
    if target["collection"] != expected_collection:
        return (
            diagnostic(
                "INVALID_TARGET_COLLECTION",
                f"{path}/target/collection",
                f"This operation must target {expected_collection}.",
                layer_id=layer_id,
                operation_index=operation_index,
            ),
            None,
        )
    if not isinstance(value, dict) or value.get("id") != target["id"]:
        return (
            diagnostic(
                "TARGET_VALUE_ID_MISMATCH",
                f"{path}/value/id",
                "The added record id must match the semantic target id.",
                layer_id=layer_id,
                operation_index=operation_index,
            ),
            None,
        )
    if target["id"] in _object_index(candidate):
        return (
            diagnostic(
                "DUPLICATE_TARGET_ID",
                f"{path}/target/id",
                f"Semantic id {target['id']!r} is already in use.",
                layer_id=layer_id,
                operation_index=operation_index,
            ),
            None,
        )
    candidate[expected_collection].append(copy.deepcopy(value))
    return None, ProvenanceEvent(
        collection=expected_collection,
        object_id=target["id"],
        path=f"/{expected_collection}/{target['id']}",
        origin="patch",
        layer_id=layer_id,
        layer_kind="",
        operation=operation["op"],
        layer_provenance={},
        value=copy.deepcopy(value),
    )


def _apply_operation(
    candidate: dict[str, Any],
    operation: dict[str, Any],
    *,
    path: str,
    layer: dict[str, Any],
    operation_index: int,
) -> tuple[list[CompositionDiagnostic], ProvenanceEvent | None]:
    operation_name = operation["op"]
    target = operation["target"]
    layer_id = layer["id"]
    diagnostics: list[CompositionDiagnostic] = []

    if operation_name in {"add_entity", "add_relationship"}:
        expected = (
            "entities" if operation_name == "add_entity" else "relationships"
        )
        issue, event = _add_record(
            candidate,
            operation,
            expected_collection=expected,
            path=path,
            layer_id=layer_id,
            operation_index=operation_index,
        )
        if issue:
            return [issue], None
    elif operation_name in {"mark_missing", "mark_unsupported_loss"}:
        event = ProvenanceEvent(
            collection=target["collection"],
            object_id=target["id"],
            path=target.get("path", ""),
            origin="patch",
            layer_id=layer_id,
            layer_kind="",
            operation=operation_name,
            layer_provenance={},
            value=copy.deepcopy(operation["value"]),
        )
        diagnostics.append(
            diagnostic(
                operation_name.upper(),
                path,
                "The patch records an explicit unresolved fact without modifying Formal BIM JSON.",
                severity="info",
                layer_id=layer_id,
                operation_index=operation_index,
            )
        )
    elif operation_name == "request_tombstone":
        event = ProvenanceEvent(
            collection=target["collection"],
            object_id=target["id"],
            path=target.get("path", ""),
            origin="patch",
            layer_id=layer_id,
            layer_kind="",
            operation=operation_name,
            layer_provenance={},
            value=copy.deepcopy(operation["value"]),
        )
        diagnostics.append(
            diagnostic(
                "TOMBSTONE_REVIEW_PENDING",
                path,
                "Deletion-like intent is recorded but not applied.",
                severity="info",
                layer_id=layer_id,
                operation_index=operation_index,
            )
        )
    else:
        record, issue = _resolve_record(
            candidate,
            target,
            path=path,
            layer_id=layer_id,
            operation_index=operation_index,
        )
        if issue:
            return [issue], None
        assert record is not None

        if operation_name == "set_property":
            property_set = target.get("property_set")
            property_name = target.get("property")
            if not property_set or not property_name:
                return [
                    diagnostic(
                        "PROPERTY_TARGET_INCOMPLETE",
                        f"{path}/target",
                        "set_property requires property_set and property.",
                        layer_id=layer_id,
                        operation_index=operation_index,
                    )
                ], None
            values = record.setdefault("property_sets", {}).setdefault(
                property_set, {}
            )
            fact_path = (
                f"/{target['collection']}/{target['id']}/property_sets/"
                f"{property_set}/{property_name}"
            )
            issue, previous = _set_value(
                values,
                property_name,
                operation["value"],
                operation,
                path=fact_path,
                layer_id=layer_id,
                operation_index=operation_index,
            )
        elif operation_name == "set_material":
            fact_path = (
                f"/{target['collection']}/{target['id']}/materials"
            )
            issue, previous = _set_value(
                record,
                "materials",
                operation["value"],
                operation,
                path=fact_path,
                layer_id=layer_id,
                operation_index=operation_index,
            )
        elif operation_name == "set_attribute":
            target_path = target.get("path")
            if not target_path:
                return [
                    diagnostic(
                        "ATTRIBUTE_TARGET_INCOMPLETE",
                        f"{path}/target/path",
                        "set_attribute requires an attributes path.",
                        layer_id=layer_id,
                        operation_index=operation_index,
                    )
                ], None
            tokens = target_path.split(".")
            if tokens[0] == "attributes":
                tokens = tokens[1:]
            if not tokens:
                return [
                    diagnostic(
                        "ATTRIBUTE_TARGET_INCOMPLETE",
                        f"{path}/target/path",
                        "set_attribute must name a concrete attribute.",
                        layer_id=layer_id,
                        operation_index=operation_index,
                    )
                ], None
            container = record.setdefault("attributes", {})
            for token in tokens[:-1]:
                child = container.get(token)
                if child is None:
                    child = {}
                    container[token] = child
                if not isinstance(child, dict):
                    return [
                        diagnostic(
                            "ATTRIBUTE_PATH_CONFLICT",
                            f"{path}/target/path",
                            "The attribute path crosses a non-object value.",
                            layer_id=layer_id,
                            operation_index=operation_index,
                        )
                    ], None
                container = child
            fact_path = (
                f"/{target['collection']}/{target['id']}/attributes/"
                + "/".join(tokens)
            )
            issue, previous = _set_value(
                container,
                tokens[-1],
                operation["value"],
                operation,
                path=fact_path,
                layer_id=layer_id,
                operation_index=operation_index,
            )
        else:
            return [
                diagnostic(
                    "UNSUPPORTED_PATCH_OPERATION",
                    f"{path}/op",
                    f"Operation {operation_name!r} is not composable.",
                    layer_id=layer_id,
                    operation_index=operation_index,
                )
            ], None

        if issue and issue.severity == "error":
            return [issue], None
        if issue:
            diagnostics.append(issue)
        event = ProvenanceEvent(
            collection=target["collection"],
            object_id=target["id"],
            path=fact_path,
            origin="patch",
            layer_id=layer_id,
            layer_kind="",
            operation=operation_name,
            layer_provenance={},
            previous_value=copy.deepcopy(previous),
            value=copy.deepcopy(operation["value"]),
        )

    assert event is not None
    event = ProvenanceEvent(
        **{
            **event.to_dict(),
            "layer_kind": layer["kind"],
            "layer_provenance": copy.deepcopy(layer["provenance"]),
        }
    )
    return diagnostics, event


def compose_patches(
    base_document: dict[str, Any],
    patches: Sequence[dict[str, Any]],
) -> CompositionResult:
    base_issues = validate_v2_document(base_document)
    if base_issues:
        return _error_result(
            base_document,
            [
                diagnostic(
                    "BASE_DOCUMENT_INVALID",
                    issue.path,
                    issue.message,
                )
                for issue in base_issues
            ],
            formal_issues=base_issues,
        )

    base_document_id = base_document.get("provenance", {}).get("document_id")
    if not isinstance(base_document_id, str) or not base_document_id:
        return _error_result(
            base_document,
            [
                diagnostic(
                    "BASE_DOCUMENT_ID_MISSING",
                    "/provenance/document_id",
                    "The immutable base document needs a provenance document_id.",
                )
            ],
        )

    candidate = copy.deepcopy(base_document)
    diagnostics: list[CompositionDiagnostic] = []
    events: list[ProvenanceEvent] = []

    for patch_index, patch in enumerate(patches):
        patch_issues = validate_patch_document(patch)
        if patch_issues:
            return _error_result(
                base_document,
                [
                    diagnostic(
                        "PATCH_INVALID",
                        f"/patches/{patch_index}{issue.path}",
                        f"{issue.code}: {issue.message}",
                    )
                    for issue in patch_issues
                ],
            )
        if patch["target_document_id"] != base_document_id:
            return _error_result(
                base_document,
                [
                    diagnostic(
                        "TARGET_DOCUMENT_MISMATCH",
                        f"/patches/{patch_index}/target_document_id",
                        "The patch targets a different immutable base document.",
                    )
                ],
            )
        for layer_index, layer in enumerate(patch["layers"]):
            for operation_index, operation in enumerate(layer["operations"]):
                path = _operation_path(
                    patch_index, layer_index, operation_index
                )
                operation_diagnostics, event = _apply_operation(
                    candidate,
                    operation,
                    path=path,
                    layer=layer,
                    operation_index=operation_index,
                )
                diagnostics.extend(operation_diagnostics)
                if any(
                    item.severity == "error"
                    for item in operation_diagnostics
                ):
                    return _error_result(base_document, diagnostics)
                if event is not None:
                    events.append(event)

    formal_issues = tuple(validate_v2_document(candidate))
    if formal_issues:
        diagnostics.extend(
            diagnostic(
                "COMPOSED_DOCUMENT_INVALID",
                issue.path,
                f"{issue.code}: {issue.message}",
            )
            for issue in formal_issues
        )
    return CompositionResult(
        document=candidate,
        diagnostics=tuple(diagnostics),
        formal_issues=formal_issues,
        provenance_events=tuple(events),
    )
