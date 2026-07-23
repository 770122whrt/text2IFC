"""Frozen, exact-versioned records for one durable IFC repair run."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUN_STATE_SCHEMA_VERSION = "text2ifc/ifc-repair-run-state/0.1"
CLARIFICATION_SCHEMA_VERSION = "text2ifc/ifc-repair-clarification/0.1"
RESULT_SCHEMA_VERSION = "text2ifc/ifc-repair-result/0.1"
TRANSITION_SCHEMA_VERSION = "text2ifc/ifc-repair-transition/0.1"
ORCHESTRATOR_VERSION = "0.1"
RUN_STATE_SCHEMA_PATH = Path("schemas/agent/ifc-repair-run-state-0.1.schema.json")
CLARIFICATION_SCHEMA_PATH = Path("schemas/agent/ifc-repair-clarification-0.1.schema.json")
RESULT_SCHEMA_PATH = Path("schemas/agent/ifc-repair-result-0.1.schema.json")


class RunStage(str, Enum):
    CREATED = "created"
    SOURCE_VALIDATED = "source_validated"
    INDEX_READY = "index_ready"
    INTENT_READY = "intent_ready"
    TARGETS_RESOLVED = "targets_resolved"
    CHANGESET_READY = "changeset_ready"
    APPLICATION_READY = "application_ready"
    EVALUATED = "evaluated"
    CLARIFICATION_REQUIRED = "clarification_required"
    SUCCEEDED = "succeeded"
    NOT_PUBLISHABLE = "not_publishable"
    UNSUPPORTED = "unsupported"
    INVALID_INPUT = "invalid_input"
    PROVIDER_FAILED = "provider_failed"
    AUDIT_FAILED = "audit_failed"
    APPLICATION_FAILED = "application_failed"
    CANCELLED = "cancelled"


TERMINAL_STAGES = frozenset(
    {
        RunStage.SUCCEEDED,
        RunStage.NOT_PUBLISHABLE,
        RunStage.UNSUPPORTED,
        RunStage.INVALID_INPUT,
        RunStage.PROVIDER_FAILED,
        RunStage.AUDIT_FAILED,
        RunStage.APPLICATION_FAILED,
        RunStage.CANCELLED,
    }
)


class RunStoreCode(str, Enum):
    INVALID_RUN_ID = "RUN_ID_INVALID"
    RUN_ALREADY_EXISTS = "RUN_ALREADY_EXISTS"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    PATH_ESCAPE = "RUN_PATH_ESCAPE"
    SYMLINK_REJECTED = "RUN_SYMLINK_REJECTED"
    SOURCE_INVALID = "RUN_SOURCE_INVALID"
    SOURCE_CHANGED = "RUN_SOURCE_CHANGED"
    STATE_CONFLICT = "RUN_STATE_CONFLICT"
    INVALID_TRANSITION = "RUN_TRANSITION_INVALID"
    TERMINAL_IMMUTABLE = "RUN_TERMINAL_IMMUTABLE"
    LOCKED = "RUN_LOCKED"
    TAMPER_DETECTED = "RUN_TAMPER_DETECTED"
    SCHEMA_INVALID = "RUN_SCHEMA_INVALID"
    ANSWER_INVALID = "CLARIFICATION_ANSWER_INVALID"
    PUBLIC_RECORD_INVALID = "PUBLIC_RECORD_INVALID"
    PUBLIC_RECORD_TOO_LARGE = "PUBLIC_RECORD_TOO_LARGE"


class RunStoreError(ValueError):
    """Stable fail-closed error returned by the persistence boundary."""

    def __init__(self, code: RunStoreCode | str, detail: str) -> None:
        self.code = code.value if isinstance(code, RunStoreCode) else str(code)
        self.detail = detail
        super().__init__(f"{self.code}: {detail}")


@dataclass(frozen=True)
class SourceBinding:
    reference: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SourceBinding":
        return cls(str(value["reference"]), str(value["sha256"]), int(value["size_bytes"]))


@dataclass(frozen=True)
class ClarificationCandidate:
    token: str
    public_id: str
    ifc_class: str
    name: str | None
    storey: str | None
    position: str | None
    evidence: tuple[str, ...]
    candidate_kind: str = "target"
    dimensions: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    occurrence_count: int = 0
    storeys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "public_id": self.public_id,
            "ifc_class": self.ifc_class,
            "name": self.name,
            "storey": self.storey,
            "position": self.position,
            "evidence": list(self.evidence),
            "candidate_kind": self.candidate_kind,
            "dimensions": thaw_json(self.dimensions),
            "occurrence_count": self.occurrence_count,
            "storeys": list(self.storeys),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ClarificationCandidate":
        return cls(
            token=str(value["token"]),
            public_id=str(value["public_id"]),
            ifc_class=str(value["ifc_class"]),
            name=None if value["name"] is None else str(value["name"]),
            storey=None if value["storey"] is None else str(value["storey"]),
            position=None if value["position"] is None else str(value["position"]),
            evidence=tuple(str(item) for item in value["evidence"]),
            candidate_kind=str(value.get("candidate_kind", "target")),
            dimensions=MappingProxyType(dict(value.get("dimensions") or {})),
            occurrence_count=int(value.get("occurrence_count", 0)),
            storeys=tuple(str(item) for item in value.get("storeys", ())),
        )


@dataclass(frozen=True)
class Clarification:
    clarification_id: str
    run_id: str
    state_version: int
    operation_id: str
    stage: RunStage
    resume_stage: RunStage
    reason_code: str
    question: str
    answer_modes: tuple[str, ...]
    candidates: tuple[ClarificationCandidate, ...] = ()
    property_preview: Mapping[str, Any] | None = None
    schema_version: str = CLARIFICATION_SCHEMA_VERSION

    @property
    def answer_schema(self) -> dict[str, Any]:
        conditions: list[dict[str, Any]] = []
        required_by_mode = {
            "select_candidate": ("candidate_token",),
            "add_detail": ("detail",),
            "authorize_prototype": ("candidate_token", "authorized"),
            "confirm_property": ("preview_hash",),
            "reject_property": ("preview_hash",),
        }
        for mode in self.answer_modes:
            required = required_by_mode.get(mode, ())
            conditions.append(
                {
                    "if": {"properties": {"kind": {"const": mode}}},
                    "then": {
                        "required": ["kind", *required],
                        "maxProperties": 1 + len(required),
                    },
                }
            )
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["kind"],
            "properties": {
                "kind": {"enum": list(self.answer_modes)},
                "candidate_token": {"type": "string", "minLength": 1, "maxLength": 128},
                "detail": {"type": "string", "minLength": 1, "maxLength": 4096},
                "authorized": {"const": True},
                "preview_hash": {
                    "type": "string",
                    "pattern": "^sha256:[0-9a-f]{64}$",
                },
            },
            "allOf": conditions,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "clarification_id": self.clarification_id,
            "run_id": self.run_id,
            "state_version": self.state_version,
            "operation_id": self.operation_id,
            "stage": self.stage.value,
            "resume_stage": self.resume_stage.value,
            "reason_code": self.reason_code,
            "question": self.question,
            "answer_modes": list(self.answer_modes),
            "answer_schema": self.answer_schema,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "property_preview": (
                None if self.property_preview is None else thaw_json(self.property_preview)
            ),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Clarification":
        return cls(
            clarification_id=str(value["clarification_id"]),
            run_id=str(value["run_id"]),
            state_version=int(value["state_version"]),
            operation_id=str(value["operation_id"]),
            stage=RunStage(str(value["stage"])),
            resume_stage=RunStage(str(value["resume_stage"])),
            reason_code=str(value["reason_code"]),
            question=str(value["question"]),
            answer_modes=tuple(str(item) for item in value["answer_modes"]),
            candidates=tuple(
                ClarificationCandidate.from_dict(item) for item in value["candidates"]
            ),
            property_preview=(
                None
                if value.get("property_preview") is None
                else freeze_json(value["property_preview"])
            ),
        )


@dataclass(frozen=True)
class RunTransition:
    transition_id: int
    state_version: int
    from_stage: RunStage | None
    to_stage: RunStage
    created_at: str
    previous_hash: str | None
    stage_hash: str
    record_hash: str
    stage_payload: Mapping[str, Any]
    clarification: Clarification | None = None
    answer: Mapping[str, Any] | None = None
    reason_code: str | None = None
    result_artifacts: Mapping[str, str] = MappingProxyType({})
    schema_version: str = TRANSITION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "transition_id": self.transition_id,
            "state_version": self.state_version,
            "from_stage": None if self.from_stage is None else self.from_stage.value,
            "to_stage": self.to_stage.value,
            "created_at": self.created_at,
            "previous_hash": self.previous_hash,
            "stage_hash": self.stage_hash,
            "record_hash": self.record_hash,
            "stage_payload": thaw_json(self.stage_payload),
            "clarification": (
                None if self.clarification is None else self.clarification.to_dict()
            ),
            "answer": None if self.answer is None else thaw_json(self.answer),
            "reason_code": self.reason_code,
            "result_artifacts": dict(self.result_artifacts),
        }

    def hash_payload(self) -> dict[str, Any]:
        value = self.to_dict()
        del value["record_hash"]
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RunTransition":
        clarification = value["clarification"]
        return cls(
            transition_id=int(value["transition_id"]),
            state_version=int(value["state_version"]),
            from_stage=(
                None if value["from_stage"] is None else RunStage(str(value["from_stage"]))
            ),
            to_stage=RunStage(str(value["to_stage"])),
            created_at=str(value["created_at"]),
            previous_hash=(
                None if value["previous_hash"] is None else str(value["previous_hash"])
            ),
            stage_hash=str(value["stage_hash"]),
            record_hash=str(value["record_hash"]),
            stage_payload=freeze_json(value["stage_payload"]),
            clarification=(
                None if clarification is None else Clarification.from_dict(clarification)
            ),
            answer=(None if value["answer"] is None else freeze_json(value["answer"])),
            reason_code=(None if value["reason_code"] is None else str(value["reason_code"])),
            result_artifacts=MappingProxyType(
                {str(key): str(item) for key, item in value["result_artifacts"].items()}
            ),
        )


@dataclass(frozen=True)
class RunState:
    run_id: str
    state_version: int
    request_id: str
    request_hash: str
    source: SourceBinding
    stage: RunStage
    transitions: tuple[RunTransition, ...]
    clarification: Clarification | None = None
    reason_code: str | None = None
    result_artifacts: Mapping[str, str] = MappingProxyType({})
    schema_version: str = RUN_STATE_SCHEMA_VERSION
    orchestrator_version: str = ORCHESTRATOR_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "orchestrator_version": self.orchestrator_version,
            "run_id": self.run_id,
            "state_version": self.state_version,
            "request_id": self.request_id,
            "request_hash": self.request_hash,
            "source": self.source.to_dict(),
            "stage": self.stage.value,
            "transitions": [item.to_dict() for item in self.transitions],
            "clarification": (
                None if self.clarification is None else self.clarification.to_dict()
            ),
            "reason_code": self.reason_code,
            "result_artifacts": dict(self.result_artifacts),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RunState":
        clarification = value["clarification"]
        return cls(
            run_id=str(value["run_id"]),
            state_version=int(value["state_version"]),
            request_id=str(value["request_id"]),
            request_hash=str(value["request_hash"]),
            source=SourceBinding.from_dict(value["source"]),
            stage=RunStage(str(value["stage"])),
            transitions=tuple(RunTransition.from_dict(item) for item in value["transitions"]),
            clarification=(
                None if clarification is None else Clarification.from_dict(clarification)
            ),
            reason_code=(None if value["reason_code"] is None else str(value["reason_code"])),
            result_artifacts=MappingProxyType(
                {str(key): str(item) for key, item in value["result_artifacts"].items()}
            ),
        )


@dataclass(frozen=True)
class RunResult:
    run_id: str
    state_version: int
    status: str
    reason_code: str | None
    complete_repair_success: bool
    successful_artifact_publishable: bool
    run_directory: str
    artifacts: Mapping[str, str]
    clarification: Clarification | None = None
    schema_version: str = RESULT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state_version": self.state_version,
            "status": self.status,
            "reason_code": self.reason_code,
            "complete_repair_success": self.complete_repair_success,
            "successful_artifact_publishable": self.successful_artifact_publishable,
            "run_directory": self.run_directory,
            "artifacts": dict(self.artifacts),
            "clarification": (
                None if self.clarification is None else self.clarification.to_dict()
            ),
        }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def hash_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_run_schema(path: Path) -> dict[str, Any]:
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


def freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    return value


def thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


__all__ = [
    "CLARIFICATION_SCHEMA_PATH", "CLARIFICATION_SCHEMA_VERSION", "ORCHESTRATOR_VERSION",
    "RESULT_SCHEMA_PATH", "RESULT_SCHEMA_VERSION", "RUN_STATE_SCHEMA_PATH",
    "RUN_STATE_SCHEMA_VERSION", "TERMINAL_STAGES", "Clarification",
    "ClarificationCandidate", "RunResult", "RunStage", "RunState", "RunStoreCode",
    "RunStoreError", "RunTransition", "SourceBinding", "canonical_json", "freeze_json",
    "hash_json", "load_run_schema", "thaw_json",
]
