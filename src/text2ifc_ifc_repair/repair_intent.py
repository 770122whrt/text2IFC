"""Exact-versioned public RepairIntent domain contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .registry import OperationRegistry, OperationRegistryError
from .target_query import TargetQuery


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPAIR_INTENT_SCHEMA_VERSION = "text2ifc/ifc-repair-intent/0.1"
REPAIR_INTENT_SCHEMA_PATH = Path("schemas/agent/ifc-repair-intent-0.1.schema.json")
MAX_OPERATIONS = 16
MAX_PROVENANCE_EXCERPT_CHARS = 2048


class RepairIntentError(ValueError):
    """Stable fail-closed RepairIntent validation failure."""

    def __init__(self, code: str, detail: str, *, path: str = "") -> None:
        self.code = code
        self.detail = detail
        self.path = path
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class PublicProvenance:
    source_kind: str
    reference: str
    excerpt: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PublicProvenance":
        return cls(
            source_kind=str(value["source_kind"]),
            reference=str(value["reference"]),
            excerpt=str(value["excerpt"]),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "source_kind": self.source_kind,
            "reference": self.reference,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class AttributeIntent:
    intent_kind: str
    name: str
    value: Any
    source: PublicProvenance

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AttributeIntent":
        return cls(
            intent_kind=str(value["intent_kind"]),
            name=str(value["name"]),
            value=value["value"],
            source=PublicProvenance.from_dict(value["source"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_kind": self.intent_kind,
            "name": self.name,
            "value": self.value,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class PrototypeIntent:
    reference_kind: str
    reference: str
    source: PublicProvenance

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PrototypeIntent":
        return cls(
            reference_kind=str(value["reference_kind"]),
            reference=str(value["reference"]),
            source=PublicProvenance.from_dict(value["source"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_kind": self.reference_kind,
            "reference": self.reference,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class OperationIntent:
    operation_id: str
    operation_type: str
    target_query: TargetQuery
    parameters: Mapping[str, Any]
    attribute_intents: tuple[AttributeIntent, ...]
    prototype_intent: PrototypeIntent | None
    provenance: tuple[PublicProvenance, ...]
    _target_query_document: Mapping[str, Any]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OperationIntent":
        target_document = _json_copy(value["target_query"])
        prototype = value["prototype_intent"]
        return cls(
            operation_id=str(value["operation_id"]),
            operation_type=str(value["operation_type"]),
            target_query=TargetQuery.from_dict(target_document),
            parameters=_json_copy(value["parameters"]),
            attribute_intents=tuple(
                AttributeIntent.from_dict(item) for item in value["attribute_intents"]
            ),
            prototype_intent=(
                None if prototype is None else PrototypeIntent.from_dict(prototype)
            ),
            provenance=tuple(
                PublicProvenance.from_dict(item) for item in value["provenance"]
            ),
            _target_query_document=target_document,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "target_query": _json_copy(self._target_query_document),
            "parameters": _json_copy(self.parameters),
            "attribute_intents": [item.to_dict() for item in self.attribute_intents],
            "prototype_intent": (
                None if self.prototype_intent is None else self.prototype_intent.to_dict()
            ),
            "provenance": [item.to_dict() for item in self.provenance],
        }


@dataclass(frozen=True)
class RepairIntent:
    request_id: str
    source_request_hash: str
    model_fingerprint: str
    prompt_fingerprint: str
    operations: tuple[OperationIntent, ...]
    provenance: tuple[PublicProvenance, ...]
    schema_version: str = REPAIR_INTENT_SCHEMA_VERSION

    @classmethod
    def from_dict(
        cls,
        value: Mapping[str, Any],
        *,
        registry: OperationRegistry,
    ) -> "RepairIntent":
        payload = _json_copy(value)
        errors = sorted(
            _validator().iter_errors(payload),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            error = errors[0]
            raise RepairIntentError(
                "REPAIR_INTENT_SCHEMA_INVALID",
                error.message,
                path=_pointer(error.absolute_path),
            )

        operation_ids = [str(item["operation_id"]) for item in payload["operations"]]
        if len(operation_ids) != len(set(operation_ids)):
            raise RepairIntentError(
                "REPAIR_INTENT_DUPLICATE_OPERATION_ID",
                "Operation IDs must be unique within one RepairIntent.",
                path="/operations",
            )

        operations: list[OperationIntent] = []
        for index, raw_operation in enumerate(payload["operations"]):
            operation_type = str(raw_operation["operation_type"])
            try:
                definition = registry.require(operation_type)
            except OperationRegistryError as error:
                raise RepairIntentError(
                    "REPAIR_INTENT_UNSUPPORTED_OPERATION",
                    error.detail,
                    path=f"/operations/{index}/operation_type",
                ) from error
            query = raw_operation["target_query"]
            if not _has_target_selector(query):
                raise RepairIntentError(
                    "REPAIR_INTENT_TARGET_SELECTOR_REQUIRED",
                    "At least one public target selector is required.",
                    path=f"/operations/{index}/target_query",
                )
            if not set(query["allowed_ifc_classes"]).issubset(
                definition.target_ifc_classes
            ):
                raise RepairIntentError(
                    "REPAIR_INTENT_TARGET_CLASS_NOT_ALLOWED",
                    operation_type,
                    path=f"/operations/{index}/target_query/allowed_ifc_classes",
                )
            parameter_issues = registry.validate_parameters(raw_operation)
            if parameter_issues:
                issue = parameter_issues[0]
                raise RepairIntentError(
                    "REPAIR_INTENT_PARAMETER_SCHEMA_INVALID",
                    issue.message,
                    path=f"/operations/{index}{issue.path}",
                )
            operations.append(OperationIntent.from_dict(raw_operation))

        return cls(
            request_id=str(payload["request_id"]),
            source_request_hash=str(payload["source_request_hash"]),
            model_fingerprint=str(payload["model_fingerprint"]),
            prompt_fingerprint=str(payload["prompt_fingerprint"]),
            operations=tuple(operations),
            provenance=tuple(
                PublicProvenance.from_dict(item) for item in payload["provenance"]
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "source_request_hash": self.source_request_hash,
            "model_fingerprint": self.model_fingerprint,
            "prompt_fingerprint": self.prompt_fingerprint,
            "operations": [operation.to_dict() for operation in self.operations],
            "provenance": [item.to_dict() for item in self.provenance],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @property
    def intent_hash(self) -> str:
        return fingerprint_text(self.canonical_json())


def load_repair_intent_schema() -> dict[str, Any]:
    return json.loads(
        (PROJECT_ROOT / REPAIR_INTENT_SCHEMA_PATH).read_text(encoding="utf-8")
    )


def hash_request(request_text: str) -> str:
    return fingerprint_text(request_text)


def fingerprint_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validator() -> Draft202012Validator:
    return Draft202012Validator(load_repair_intent_schema())


def _has_target_selector(query: Mapping[str, Any]) -> bool:
    scalar_fields = (
        "global_id",
        "storey_name",
        "storey_global_id",
        "host_global_id",
        "grid",
        "space",
        "direction",
    )
    return any(query.get(field) for field in scalar_fields) or any(
        query.get(field) for field in ("names", "geometry_capabilities")
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _json_copy(value: Any) -> Any:
    return json.loads(_canonical_json(value))


def _pointer(parts: Any) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else ""


__all__ = [
    "AttributeIntent",
    "MAX_OPERATIONS",
    "MAX_PROVENANCE_EXCERPT_CHARS",
    "OperationIntent",
    "PrototypeIntent",
    "PublicProvenance",
    "REPAIR_INTENT_SCHEMA_PATH",
    "REPAIR_INTENT_SCHEMA_VERSION",
    "RepairIntent",
    "RepairIntentError",
    "fingerprint_text",
    "hash_request",
    "load_repair_intent_schema",
]
