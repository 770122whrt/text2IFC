"""Alias-free, non-executable property retrieval runtime for Stage 1.5."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from jsonschema import Draft202012Validator

from .property_search import (
    BgeM3EmbeddingProvider,
    PROPERTY_RECORD_SCHEMA_VERSION,
    QdrantVectorIndex,
    SUPPORTED_AUTHORABLE_VALUE_TYPES,
    PropertyKnowledgeRecord,
    build_standard_property_records,
)
from .registry import IfcKnowledgeRegistry, load_ifc2x3_registry


PROPERTY_QUERY_SCHEMA_VERSION = "text2ifc/ifc-property-resolution-query/0.2"
PROPERTY_CANDIDATE_SET_SCHEMA_VERSION = "text2ifc/ifc-property-candidate-set/0.1"
DEFAULT_CORPUS_VERSION = "ifc2x3-property-records/0.2"
DEFAULT_EMBEDDING_MODEL_ID = "BAAI/bge-m3"
DEFAULT_EMBEDDING_MODEL_VERSION = "configured"
DEFAULT_DOCUMENT_RENDERER_VERSION = "property-record-text/0.1"
DEFAULT_COLLECTION_VERSION = "ifc2x3-property-vector/0.2"
DEFAULT_COLLECTION_NAME = "ifc2x3_property_resolution_v02"
PROPERTY_BGE_MODEL_PATH_ENV = "TEXT2IFC_PROPERTY_BGE_MODEL_PATH"
PROPERTY_BGE_MODEL_VERSION_ENV = "TEXT2IFC_PROPERTY_BGE_MODEL_VERSION"
PROPERTY_BGE_DEVICE_ENV = "TEXT2IFC_PROPERTY_BGE_DEVICE"
PROPERTY_QDRANT_PATH_ENV = "TEXT2IFC_PROPERTY_QDRANT_PATH"
PROPERTY_QDRANT_URL_ENV = "TEXT2IFC_PROPERTY_QDRANT_URL"
PROPERTY_QDRANT_COLLECTION_ENV = "TEXT2IFC_PROPERTY_QDRANT_COLLECTION"


class PropertyRuntimeError(ValueError):
    """Stable fail-closed error raised before any Provider call."""


class PropertyRuntimeConfigurationError(ValueError):
    """Invalid production runtime configuration; never repaired by fallback."""


@dataclass(frozen=True)
class PropertyRuntimeConfig:
    project_root: Path
    embedding_model_path: str
    embedding_model_version: str
    qdrant_path: Path | None
    qdrant_url: str | None
    collection_name: str
    device: str | None
    local_files_only: bool = True

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "embedding_model_path": self.embedding_model_path,
            "embedding_model_version": self.embedding_model_version,
            "qdrant_path": (
                None if self.qdrant_path is None else str(self.qdrant_path)
            ),
            "qdrant_url": self.qdrant_url,
            "collection_name": self.collection_name,
            "device": self.device,
            "local_files_only": self.local_files_only,
        }


@dataclass(frozen=True)
class PropertyRuntimeHealth:
    status: str
    reason_code: str | None
    runtime_mode: str
    acceptance_eligible: bool
    corpus_version: str
    embedding_model_id: str
    embedding_model_version: str
    document_renderer_version: str
    collection_version: str
    collection_status: str | None
    record_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PropertyRetrievalResult:
    query: dict[str, Any]
    candidate_set: dict[str, Any]
    health: dict[str, Any]


class PropertyKnowledgeRuntime:
    """Produces bounded retrieval evidence; it never authorizes IFC writes."""

    def __init__(
        self,
        *,
        registry: IfcKnowledgeRegistry | None,
        records: Iterable[PropertyKnowledgeRecord],
        vector_index: Any | None,
        policy: Mapping[str, Any] | None,
        health: PropertyRuntimeHealth,
    ) -> None:
        self.registry = registry
        self.records = tuple(records)
        self.vector_index = vector_index
        self.policy = None if policy is None else dict(policy)
        self.health = health
        self._records_by_id = {record.record_id: record for record in self.records}

    def retrieve(
        self,
        *,
        run_id: str,
        request_id: str,
        model_id: str,
        operation_id: str,
        operation_type: str,
        claim_id: str,
        property_phrase: str,
        target_ifc_class: str,
        raw_value: object,
        raw_unit: str | None,
        scope: str | None,
        project_length_unit: str = "m",
    ) -> PropertyRetrievalResult:
        if self.health.status != "ready":
            raise PropertyRuntimeError(
                self.health.reason_code or "PROPERTY_RUNTIME_NOT_READY"
            )
        if self.registry is None or self.vector_index is None or self.policy is None:
            raise PropertyRuntimeError("PROPERTY_RUNTIME_NOT_READY")

        phrase = property_phrase.strip()
        if not phrase:
            raise PropertyRuntimeError("PROPERTY_QUERY_INVALID")
        query_id = f"property-query:{run_id}:{operation_id}:{claim_id}"
        query = {
            "schema_version": PROPERTY_QUERY_SCHEMA_VERSION,
            "query_id": query_id,
            "run_id": run_id,
            "request_id": request_id,
            "model_id": model_id,
            "operation_id": operation_id,
            "operation_type": operation_type,
            "claim_id": claim_id,
            "property_phrase": phrase,
            "target_ifc_class": target_ifc_class,
            "raw_value": raw_value,
            "raw_value_kind": _raw_value_kind(raw_value),
            "raw_unit": raw_unit,
            "scope": scope,
            "corpus_version": self.health.corpus_version,
        }

        eligible = tuple(
            record
            for record in self.records
            if _eligible_for_request(
                record,
                registry=self.registry,
                target_ifc_class=target_ifc_class,
                scope=scope,
            )
        )
        allowed_ids = frozenset(record.record_id for record in eligible)
        hits = self.vector_index.search_allowed(
            _render_query_text(
                property_phrase=phrase,
                target_ifc_class=target_ifc_class,
                scope=scope,
                operation_type=operation_type,
            ),
            allowed_record_ids=allowed_ids,
            limit=int(self.policy["max_candidates"]),
        )
        for hit in hits:
            if hit.record_id not in allowed_ids:
                raise PropertyRuntimeError("PROPERTY_VECTOR_INELIGIBLE_HIT")

        minimum_score = float(self.policy["minimum_retrieval_score"])
        ranked = sorted(
            (
                (self._records_by_id[hit.record_id], float(hit.score))
                for hit in hits
                if float(hit.score) >= minimum_score
            ),
            key=lambda item: (-item[1], _public_record_id(item[0])),
        )[: int(self.policy["max_candidates"])]
        candidates = [
            _public_candidate(record, score=score, rank=rank)
            for rank, (record, score) in enumerate(ranked, start=1)
        ]
        candidate_set = {
            "schema_version": PROPERTY_CANDIDATE_SET_SCHEMA_VERSION,
            "candidate_set_id": f"property-candidates:{run_id}:{operation_id}:{claim_id}",
            "query_id": query_id,
            "corpus_version": self.health.corpus_version,
            "embedding_model": {
                "model_id": self.health.embedding_model_id,
                "model_version": self.health.embedding_model_version,
            },
            "document_renderer_version": self.health.document_renderer_version,
            "collection_version": self.health.collection_version,
            "candidates": candidates,
        }
        return PropertyRetrievalResult(
            query=query,
            candidate_set=candidate_set,
            health=self.health.to_dict(),
        )


def create_property_runtime(
    *,
    registry: IfcKnowledgeRegistry,
    standard_records: Iterable[PropertyKnowledgeRecord],
    project_records: Iterable[PropertyKnowledgeRecord],
    vector_index: Any,
    policy_document: Mapping[str, Any],
    corpus_version: str,
    embedding_model_version: str,
    document_renderer_version: str,
    collection_version: str,
    runtime_mode: str,
) -> PropertyKnowledgeRuntime:
    policy = _validate_policy(policy_document)
    if runtime_mode not in {"production", "offline_test"}:
        raise PropertyRuntimeError("PROPERTY_RUNTIME_MODE_INVALID")
    records = _active_public_records((*standard_records, *project_records))
    if not records:
        raise PropertyRuntimeError("PROPERTY_CORPUS_EMPTY")
    storage_version = _storage_version(
        corpus_version=corpus_version,
        embedding_model_version=embedding_model_version,
        document_renderer_version=document_renderer_version,
        collection_version=collection_version,
    )
    collection_status = vector_index.ensure_versioned(
        records,
        collection_version=storage_version,
    )
    embedding_model_id = str(
        getattr(vector_index.embedding_provider, "model_id", "unknown")
    )
    health = PropertyRuntimeHealth(
        status="ready",
        reason_code=None,
        runtime_mode=runtime_mode,
        acceptance_eligible=runtime_mode == "production",
        corpus_version=corpus_version,
        embedding_model_id=embedding_model_id,
        embedding_model_version=embedding_model_version,
        document_renderer_version=document_renderer_version,
        collection_version=collection_version,
        collection_status=str(collection_status),
        record_count=len(records),
    )
    return PropertyKnowledgeRuntime(
        registry=registry,
        records=records,
        vector_index=vector_index,
        policy=policy,
        health=health,
    )


def load_property_runtime_config(
    environ: Mapping[str, str] | None = None,
    *,
    project_root: Path | str | None = None,
) -> PropertyRuntimeConfig:
    """Resolve one local-only production BGE/Qdrant configuration."""

    env = os.environ if environ is None else environ
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    configured_model = str(env.get(PROPERTY_BGE_MODEL_PATH_ENV, "")).strip()
    repository_model = root / ".cache/models/BAAI-bge-m3"
    if configured_model:
        embedding_model_path = str(_resolve_config_path(root, configured_model))
    elif repository_model.is_dir():
        embedding_model_path = str(repository_model.resolve())
    else:
        embedding_model_path = DEFAULT_EMBEDDING_MODEL_ID

    configured_version = str(
        env.get(PROPERTY_BGE_MODEL_VERSION_ENV, "")
    ).strip()
    embedding_model_version = configured_version or (
        "BAAI-bge-m3-local/phase12.1"
        if embedding_model_path != DEFAULT_EMBEDDING_MODEL_ID
        else DEFAULT_EMBEDDING_MODEL_VERSION
    )

    configured_qdrant_path = str(env.get(PROPERTY_QDRANT_PATH_ENV, "")).strip()
    qdrant_url = str(env.get(PROPERTY_QDRANT_URL_ENV, "")).strip() or None
    if configured_qdrant_path and qdrant_url:
        raise PropertyRuntimeConfigurationError(
            "PROPERTY_QDRANT_LOCATION_AMBIGUOUS"
        )
    qdrant_path = (
        None
        if qdrant_url
        else _resolve_config_path(
            root,
            configured_qdrant_path or ".cache/property-resolution/qdrant",
        )
    )
    collection_name = str(
        env.get(PROPERTY_QDRANT_COLLECTION_ENV, DEFAULT_COLLECTION_NAME)
    ).strip()
    if not collection_name:
        raise PropertyRuntimeConfigurationError(
            "PROPERTY_QDRANT_COLLECTION_REQUIRED"
        )
    device = str(env.get(PROPERTY_BGE_DEVICE_ENV, "")).strip() or None
    return PropertyRuntimeConfig(
        project_root=root,
        embedding_model_path=embedding_model_path,
        embedding_model_version=embedding_model_version,
        qdrant_path=qdrant_path,
        qdrant_url=qdrant_url,
        collection_name=collection_name,
        device=device,
    )


def create_property_runtime_from_environment(
    environ: Mapping[str, str] | None = None,
    *,
    project_root: Path | str | None = None,
) -> PropertyKnowledgeRuntime:
    """Construct the production runtime used by API, preflight and live paths."""

    config = load_property_runtime_config(
        environ,
        project_root=project_root,
    )
    return create_default_property_runtime(
        project_root=config.project_root,
        qdrant_path=config.qdrant_path,
        qdrant_url=config.qdrant_url,
        collection_name=config.collection_name,
        runtime_mode="production",
        embedding_model_path=config.embedding_model_path,
        embedding_model_version=config.embedding_model_version,
        device=config.device,
    )


def _resolve_config_path(root: Path, value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve()


def create_default_property_runtime(
    *,
    project_root: Path | str | None = None,
    qdrant_path: Path | str | None = None,
    qdrant_url: str | None = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    policy_path: Path | str | None = None,
    policy_document: Mapping[str, Any] | None = None,
    runtime_mode: str = "production",
    corpus_version: str = DEFAULT_CORPUS_VERSION,
    embedding_model_path: str = DEFAULT_EMBEDDING_MODEL_ID,
    embedding_model_version: str = DEFAULT_EMBEDDING_MODEL_VERSION,
    document_renderer_version: str = DEFAULT_DOCUMENT_RENDERER_VERSION,
    collection_version: str = DEFAULT_COLLECTION_VERSION,
    device: str | None = None,
    project_records: Iterable[PropertyKnowledgeRecord] = (),
    embedding_provider_factory: Callable[..., Any] | None = None,
    vector_index_factory: Callable[..., Any] | None = None,
) -> PropertyKnowledgeRuntime:
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    resolved_policy_path = (
        Path(policy_path)
        if policy_path is not None
        else root / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
    )
    if policy_document is None:
        if not resolved_policy_path.is_file():
            return _not_ready_runtime(
                reason_code="PROPERTY_POLICY_UNAVAILABLE",
                runtime_mode=runtime_mode,
                corpus_version=corpus_version,
                embedding_model_id=embedding_model_path,
                embedding_model_version=embedding_model_version,
                document_renderer_version=document_renderer_version,
                collection_version=collection_version,
            )
        try:
            policy_document = json.loads(
                resolved_policy_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return _not_ready_runtime(
                reason_code="PROPERTY_POLICY_INVALID",
                runtime_mode=runtime_mode,
                corpus_version=corpus_version,
                embedding_model_id=embedding_model_path,
                embedding_model_version=embedding_model_version,
                document_renderer_version=document_renderer_version,
                collection_version=collection_version,
            )
    elif runtime_mode != "offline_test":
        return _not_ready_runtime(
            reason_code="PROPERTY_POLICY_INVALID",
            runtime_mode=runtime_mode,
            corpus_version=corpus_version,
            embedding_model_id=embedding_model_path,
            embedding_model_version=embedding_model_version,
            document_renderer_version=document_renderer_version,
            collection_version=collection_version,
        )

    embedding_factory = embedding_provider_factory or BgeM3EmbeddingProvider
    try:
        embedding_provider = embedding_factory(
            model_path=embedding_model_path,
            model_version=embedding_model_version,
            device=device,
            local_files_only=True,
        )
    except Exception:
        return _not_ready_runtime(
            reason_code="BGE_M3_UNAVAILABLE",
            runtime_mode=runtime_mode,
            corpus_version=corpus_version,
            embedding_model_id=embedding_model_path,
            embedding_model_version=embedding_model_version,
            document_renderer_version=document_renderer_version,
            collection_version=collection_version,
        )

    index_factory = vector_index_factory or QdrantVectorIndex
    if qdrant_path is None and qdrant_url is None:
        qdrant_path = root / ".cache/property-resolution/qdrant"
    try:
        vector_index = index_factory(
            embedding_provider,
            collection_name=collection_name,
            path=qdrant_path,
            url=qdrant_url,
        )
    except Exception:
        return _not_ready_runtime(
            reason_code="QDRANT_UNAVAILABLE",
            runtime_mode=runtime_mode,
            corpus_version=corpus_version,
            embedding_model_id=str(
                getattr(embedding_provider, "model_id", embedding_model_path)
            ),
            embedding_model_version=embedding_model_version,
            document_renderer_version=document_renderer_version,
            collection_version=collection_version,
        )

    registry = load_ifc2x3_registry(root)
    standard_records = build_standard_property_records(
        registry,
        corpus_fingerprint=corpus_version,
    )
    try:
        return create_property_runtime(
            registry=registry,
            standard_records=standard_records,
            project_records=project_records,
            vector_index=vector_index,
            policy_document=policy_document,
            corpus_version=corpus_version,
            embedding_model_version=embedding_model_version,
            document_renderer_version=document_renderer_version,
            collection_version=collection_version,
            runtime_mode=runtime_mode,
        )
    except PropertyRuntimeError:
        raise
    except Exception as error:
        reason = (
            "BGE_M3_UNAVAILABLE"
            if "BGE" in str(error).upper() or "SENTENCE" in str(error).upper()
            else "QDRANT_UNAVAILABLE"
        )
        return _not_ready_runtime(
            reason_code=reason,
            runtime_mode=runtime_mode,
            corpus_version=corpus_version,
            embedding_model_id=str(
                getattr(embedding_provider, "model_id", embedding_model_path)
            ),
            embedding_model_version=embedding_model_version,
            document_renderer_version=document_renderer_version,
            collection_version=collection_version,
        )


def _active_public_records(
    records: Iterable[PropertyKnowledgeRecord],
) -> tuple[PropertyKnowledgeRecord, ...]:
    active: dict[tuple[str, str, str], PropertyKnowledgeRecord] = {}
    for record in records:
        if record.authority not in {"ifc2x3_psd", "current_ifc_project"}:
            continue
        if not record.authorable:
            continue
        if record.template_type != "TypePropertySingleValue":
            continue
        if record.value_type not in SUPPORTED_AUTHORABLE_VALUE_TYPES:
            continue
        key = (record.authority, record.canonical_path, record.record_id)
        active[key] = record
    return tuple(active[key] for key in sorted(active))


def _eligible_for_request(
    record: PropertyKnowledgeRecord,
    *,
    registry: IfcKnowledgeRegistry,
    target_ifc_class: str,
    scope: str | None,
) -> bool:
    if scope != "occurrence_direct":
        return False
    if not record.is_applicable(target_ifc_class, registry):
        return False
    if (
        record.authority == "current_ifc_project"
        and record.definition
        and "ownership=type_inherited" in record.definition
    ):
        return False
    if record.value_type is None:
        return False
    return True


def _raw_value_kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    raise PropertyRuntimeError("PROPERTY_QUERY_INVALID")


def _render_query_text(
    *,
    property_phrase: str,
    target_ifc_class: str,
    scope: str | None,
    operation_type: str,
) -> str:
    return " ".join(
        (
            property_phrase,
            f"class {target_ifc_class}",
            f"scope {scope or 'none'}",
            f"operation {operation_type}",
        )
    )


def _public_record_id(record: PropertyKnowledgeRecord) -> str:
    if record.authority == "ifc2x3_psd":
        return f"ifc2x3:{record.canonical_path}"
    target = record.applicable_classes[0] if record.applicable_classes else "IfcObject"
    return f"project:{target}:{record.canonical_path}"


def _public_candidate(
    record: PropertyKnowledgeRecord,
    *,
    score: float,
    rank: int,
) -> dict[str, Any]:
    public_id = _public_record_id(record)
    unit = record.unit_types[0] if len(record.unit_types) == 1 else None
    return {
        "candidate_id": f"candidate:{rank}:{public_id}",
        "record_id": public_id,
        "rank": rank,
        "score": score,
        "canonical_path": record.canonical_path,
        "set_name": record.set_name,
        "property_name": record.property_name,
        "definition": record.definition or record.canonical_path,
        "applicable_classes": list(record.applicable_classes),
        "template_type": record.template_type,
        "value_type": record.value_type,
        "unit": unit,
        "standard_status": (
            "standard" if record.authority == "ifc2x3_psd" else "project_custom"
        ),
        "source": {
            "kind": (
                "ifc2x3_psd"
                if record.authority == "ifc2x3_psd"
                else "project_record"
            ),
            "reference": record.source_ref or record.canonical_path,
        },
    }


def _validate_policy(document: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "schemas/ifc/knowledge/property_resolution_policy.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        value = dict(document)
        errors = tuple(Draft202012Validator(schema).iter_errors(value))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise PropertyRuntimeError("PROPERTY_POLICY_INVALID") from error
    if errors:
        raise PropertyRuntimeError("PROPERTY_POLICY_INVALID")
    return value


def _storage_version(
    *,
    corpus_version: str,
    embedding_model_version: str,
    document_renderer_version: str,
    collection_version: str,
) -> str:
    return "|".join(
        (
            collection_version,
            f"records={PROPERTY_RECORD_SCHEMA_VERSION}",
            f"corpus={corpus_version}",
            f"model={embedding_model_version}",
            f"renderer={document_renderer_version}",
        )
    )


def _not_ready_runtime(
    *,
    reason_code: str,
    runtime_mode: str,
    corpus_version: str,
    embedding_model_id: str,
    embedding_model_version: str,
    document_renderer_version: str,
    collection_version: str,
) -> PropertyKnowledgeRuntime:
    return PropertyKnowledgeRuntime(
        registry=None,
        records=(),
        vector_index=None,
        policy=None,
        health=PropertyRuntimeHealth(
            status="not_ready",
            reason_code=reason_code,
            runtime_mode=runtime_mode,
            acceptance_eligible=False,
            corpus_version=corpus_version,
            embedding_model_id=embedding_model_id,
            embedding_model_version=embedding_model_version,
            document_renderer_version=document_renderer_version,
            collection_version=collection_version,
            collection_status=None,
            record_count=0,
        ),
    )


__all__ = [
    "PropertyKnowledgeRuntime",
    "PropertyRetrievalResult",
    "PropertyRuntimeConfig",
    "PropertyRuntimeConfigurationError",
    "PropertyRuntimeError",
    "PropertyRuntimeHealth",
    "create_default_property_runtime",
    "create_property_runtime",
    "create_property_runtime_from_environment",
    "load_property_runtime_config",
]
