"""Exact-versioned public RepairIntent domain contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .property_intent import ExactPropertyIntent, NaturalLanguagePropertyIntent
from .registry import OperationRegistry, OperationRegistryError
from .target_query import TargetQuery


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPAIR_INTENT_SCHEMA_VERSION = "text2ifc/ifc-repair-intent/0.1"
REPAIR_INTENT_SCHEMA_PATH = Path("schemas/agent/ifc-repair-intent-0.1.schema.json")
REPAIR_INTENT_BODY_SCHEMA_VERSION = "text2ifc/ifc-repair-intent-body/0.1"
REPAIR_INTENT_BODY_SCHEMA_PATH = Path(
    "schemas/agent/ifc-repair-intent-body-0.1.schema.json"
)
REPAIR_INTENT_SCHEMA_VERSION_0_2 = "text2ifc/ifc-repair-intent/0.2"
REPAIR_INTENT_SCHEMA_PATH_0_2 = Path(
    "schemas/agent/ifc-repair-intent-0.2.schema.json"
)
REPAIR_INTENT_BODY_SCHEMA_VERSION_0_2 = (
    "text2ifc/ifc-repair-intent-body/0.2"
)
REPAIR_INTENT_BODY_SCHEMA_PATH_0_2 = Path(
    "schemas/agent/ifc-repair-intent-body-0.2.schema.json"
)
REPAIR_INTENT_SCHEMA_VERSION_0_3 = "text2ifc/ifc-repair-intent/0.3"
REPAIR_INTENT_SCHEMA_PATH_0_3 = Path(
    "schemas/agent/ifc-repair-intent-0.3.schema.json"
)
REPAIR_INTENT_BODY_SCHEMA_VERSION_0_3 = (
    "text2ifc/ifc-repair-intent-body/0.3"
)
REPAIR_INTENT_BODY_SCHEMA_PATH_0_3 = Path(
    "schemas/agent/ifc-repair-intent-body-0.3.schema.json"
)
_SCHEMA_PATHS = {
    REPAIR_INTENT_SCHEMA_VERSION: REPAIR_INTENT_SCHEMA_PATH,
    REPAIR_INTENT_SCHEMA_VERSION_0_2: REPAIR_INTENT_SCHEMA_PATH_0_2,
    REPAIR_INTENT_SCHEMA_VERSION_0_3: REPAIR_INTENT_SCHEMA_PATH_0_3,
}
_BODY_SCHEMA_PATHS = {
    REPAIR_INTENT_BODY_SCHEMA_VERSION: REPAIR_INTENT_BODY_SCHEMA_PATH,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_2: REPAIR_INTENT_BODY_SCHEMA_PATH_0_2,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_3: REPAIR_INTENT_BODY_SCHEMA_PATH_0_3,
}


@dataclass(frozen=True)
class RepairIntentLimits:
    """Single authority for public Stage 1 content and retry bounds."""

    max_operations: int = 16
    max_provenance_excerpt_chars: int = 2048
    max_request_bytes: int = 16 * 1024
    max_provider_response_bytes: int = 256 * 1024
    max_correction_attempts: int = 2
    max_attempt_excerpt_chars: int = 4096
    public_source_kinds: tuple[str, ...] = (
        "user_request",
        "public_capability",
        "public_clarification",
    )
    private_canary_terms: tuple[str, ...] = (
        "mutation_manifest.private.json",
        "private_original_ifc",
        "mutation_mapping",
        "benchmark_gold",
        "gold_ifc",
    )


DEFAULT_REPAIR_INTENT_LIMITS = RepairIntentLimits()
MAX_OPERATIONS = DEFAULT_REPAIR_INTENT_LIMITS.max_operations
MAX_PROVENANCE_EXCERPT_CHARS = (
    DEFAULT_REPAIR_INTENT_LIMITS.max_provenance_excerpt_chars
)


class RepairIntentCode(str, Enum):
    SCHEMA_INVALID = "REPAIR_INTENT_SCHEMA_INVALID"
    DUPLICATE_OPERATION_ID = "REPAIR_INTENT_DUPLICATE_OPERATION_ID"
    UNSUPPORTED_OPERATION = "REPAIR_INTENT_UNSUPPORTED_OPERATION"
    TARGET_SELECTOR_REQUIRED = "REPAIR_INTENT_TARGET_SELECTOR_REQUIRED"
    TARGET_CLASS_NOT_ALLOWED = "REPAIR_INTENT_TARGET_CLASS_NOT_ALLOWED"
    PARAMETER_SCHEMA_INVALID = "REPAIR_INTENT_PARAMETER_SCHEMA_INVALID"
    REQUEST_ID_MISMATCH = "REPAIR_INTENT_REQUEST_ID_MISMATCH"
    REQUEST_HASH_MISMATCH = "REPAIR_INTENT_REQUEST_HASH_MISMATCH"
    PROMPT_FINGERPRINT_MISMATCH = "REPAIR_INTENT_PROMPT_FINGERPRINT_MISMATCH"
    MODEL_FINGERPRINT_MISMATCH = "REPAIR_INTENT_MODEL_FINGERPRINT_MISMATCH"
    REQUEST_TOO_LARGE = "REPAIR_REQUEST_TOO_LARGE"
    ATTEMPT_BUDGET_INVALID = "REPAIR_INTENT_ATTEMPT_BUDGET_INVALID"
    PROVIDER_RESPONSE_TOO_LARGE = "PROVIDER_RESPONSE_TOO_LARGE"
    PROVIDER_REQUEST_FAILED = "REPAIR_INTENT_PROVIDER_FAILED"
    RETRY_EXHAUSTED = "REPAIR_INTENT_RETRY_EXHAUSTED"
    PROPERTY_INCOMPLETE = "REPAIR_INTENT_PROPERTY_INCOMPLETE"


class RepairIntentError(ValueError):
    """Stable fail-closed RepairIntent validation failure."""

    def __init__(
        self, code: RepairIntentCode | str, detail: str, *, path: str = ""
    ) -> None:
        self.code = code.value if isinstance(code, RepairIntentCode) else code
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
    property_intents: tuple[
        ExactPropertyIntent | NaturalLanguagePropertyIntent, ...
    ] = ()
    _has_property_intents_field: bool = False

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OperationIntent":
        target_document = _freeze_json(value["target_query"])
        prototype = value["prototype_intent"]
        return cls(
            operation_id=str(value["operation_id"]),
            operation_type=str(value["operation_type"]),
            target_query=TargetQuery.from_dict(_thaw_json(target_document)),
            parameters=_freeze_json(value["parameters"]),
            attribute_intents=tuple(
                AttributeIntent.from_dict(item) for item in value["attribute_intents"]
            ),
            property_intents=tuple(
                _property_intent_from_dict(item)
                for item in value.get("property_intents", ())
            ),
            prototype_intent=(
                None if prototype is None else PrototypeIntent.from_dict(prototype)
            ),
            provenance=tuple(
                PublicProvenance.from_dict(item) for item in value["provenance"]
            ),
            _target_query_document=target_document,
            _has_property_intents_field="property_intents" in value,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "target_query": _thaw_json(self._target_query_document),
            "parameters": _thaw_json(self.parameters),
            "attribute_intents": [item.to_dict() for item in self.attribute_intents],
            "prototype_intent": (
                None if self.prototype_intent is None else self.prototype_intent.to_dict()
            ),
            "provenance": [item.to_dict() for item in self.provenance],
        }
        if self._has_property_intents_field:
            payload["property_intents"] = [
                item.to_dict() for item in self.property_intents
            ]
        return payload


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
        require_complete: bool = True,
    ) -> "RepairIntent":
        payload = _json_copy(value)
        schema_version = str(payload.get("schema_version", ""))
        errors = sorted(
            _validator(schema_version).iter_errors(payload),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            error = errors[0]
            raise RepairIntentError(
                RepairIntentCode.SCHEMA_INVALID,
                error.message,
                path=_pointer(error.absolute_path),
            )

        operation_ids = [str(item["operation_id"]) for item in payload["operations"]]
        if len(operation_ids) != len(set(operation_ids)):
            raise RepairIntentError(
                RepairIntentCode.DUPLICATE_OPERATION_ID,
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
                    RepairIntentCode.UNSUPPORTED_OPERATION,
                    error.detail,
                    path=f"/operations/{index}/operation_type",
                ) from error
            query = raw_operation["target_query"]
            if not _has_target_selector(query):
                raise RepairIntentError(
                    RepairIntentCode.TARGET_SELECTOR_REQUIRED,
                    "At least one public target selector is required.",
                    path=f"/operations/{index}/target_query",
                )
            if not set(query["allowed_ifc_classes"]).issubset(
                definition.target_ifc_classes
            ):
                raise RepairIntentError(
                    RepairIntentCode.TARGET_CLASS_NOT_ALLOWED,
                    operation_type,
                    path=f"/operations/{index}/target_query/allowed_ifc_classes",
                )
            parameter_issues = (
                registry.validate_parameters(raw_operation)
                if require_complete
                else registry.validate_partial_parameters(raw_operation)
            )
            if parameter_issues:
                issue = parameter_issues[0]
                raise RepairIntentError(
                    RepairIntentCode.PARAMETER_SCHEMA_INVALID,
                    issue.message,
                    path=f"/operations/{index}{issue.path}",
                )
            if require_complete:
                for property_index, property_intent in enumerate(
                    raw_operation.get("property_intents", ())
                ):
                    missing = _property_intent_from_dict(property_intent).missing_fields
                    if missing:
                        raise RepairIntentError(
                            RepairIntentCode.PROPERTY_INCOMPLETE,
                            ",".join(missing),
                            path=(
                                f"/operations/{index}/property_intents/"
                                f"{property_index}"
                            ),
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
            schema_version=schema_version,
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


def load_repair_intent_schema(
    version: str = REPAIR_INTENT_SCHEMA_VERSION,
) -> dict[str, Any]:
    path = _SCHEMA_PATHS.get(version)
    if path is None:
        raise RepairIntentError(
            RepairIntentCode.SCHEMA_INVALID,
            f"Unsupported RepairIntent schema version: {version}",
            path="/schema_version",
        )
    return json.loads(
        (PROJECT_ROOT / path).read_text(encoding="utf-8")
    )


def load_repair_intent_body_schema(
    version: str = REPAIR_INTENT_BODY_SCHEMA_VERSION,
) -> dict[str, Any]:
    path = _BODY_SCHEMA_PATHS.get(version)
    if path is None:
        raise RepairIntentError(
            RepairIntentCode.SCHEMA_INVALID,
            f"Unsupported RepairIntent body schema version: {version}",
            path="/schema_version",
        )
    return json.loads(
        (PROJECT_ROOT / path).read_text(encoding="utf-8")
    )


def hash_request(request_text: str) -> str:
    return fingerprint_text(request_text)


def fingerprint_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validator(version: str) -> Draft202012Validator:
    return Draft202012Validator(load_repair_intent_schema(version))


def _property_intent_from_dict(
    value: Mapping[str, Any],
) -> ExactPropertyIntent | NaturalLanguagePropertyIntent:
    if value.get("intent_kind") == "natural_language_property":
        return NaturalLanguagePropertyIntent.from_dict(value)
    return ExactPropertyIntent.from_dict(value)


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


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _pointer(parts: Any) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else ""


__all__ = [
    "AttributeIntent",
    "DEFAULT_REPAIR_INTENT_LIMITS",
    "MAX_OPERATIONS",
    "MAX_PROVENANCE_EXCERPT_CHARS",
    "OperationIntent",
    "PrototypeIntent",
    "PublicProvenance",
    "REPAIR_INTENT_BODY_SCHEMA_PATH",
    "REPAIR_INTENT_BODY_SCHEMA_PATH_0_2",
    "REPAIR_INTENT_BODY_SCHEMA_VERSION",
    "REPAIR_INTENT_BODY_SCHEMA_VERSION_0_2",
    "REPAIR_INTENT_BODY_SCHEMA_PATH_0_3",
    "REPAIR_INTENT_BODY_SCHEMA_VERSION_0_3",
    "REPAIR_INTENT_SCHEMA_PATH",
    "REPAIR_INTENT_SCHEMA_PATH_0_2",
    "REPAIR_INTENT_SCHEMA_VERSION",
    "REPAIR_INTENT_SCHEMA_VERSION_0_2",
    "REPAIR_INTENT_SCHEMA_PATH_0_3",
    "REPAIR_INTENT_SCHEMA_VERSION_0_3",
    "RepairIntent",
    "RepairIntentCode",
    "RepairIntentError",
    "RepairIntentLimits",
    "fingerprint_text",
    "hash_request",
    "load_repair_intent_schema",
    "load_repair_intent_body_schema",
]
