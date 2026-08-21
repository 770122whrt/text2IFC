"""Bounded IFC2X3 property records, storage, retrieval and resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence

from .registry import IfcKnowledgeRegistry, check_registry_files, load_ifc2x3_registry


PROPERTY_RECORD_SCHEMA_VERSION = "text2ifc/property-knowledge-record/0.1"
PROPERTY_QUERY_SCHEMA_VERSION = "text2ifc/property-knowledge-query/0.1"
PROPERTY_DECISION_SCHEMA_VERSION = "text2ifc/property-resolution-decision/0.1"
SUPPORTED_AUTHORABLE_VALUE_TYPES = frozenset(
    {
        "IfcBoolean",
        "IfcIdentifier",
        "IfcInteger",
        "IfcLabel",
        "IfcLengthMeasure",
        "IfcLogical",
        "IfcReal",
        "IfcText",
    }
)

_WINDOWS_TORCH_RUNTIME_HANDLES: list[Any] = []


def _prepare_windows_torch_runtime(
    *,
    os_name: str | None = None,
    system_root: Path | str | None = None,
    dll_loader: Callable[[str], Any] | None = None,
) -> tuple[Any, ...]:
    """Load the OS MSVC runtime before Torch when Python ships older DLLs."""

    active_os = os.name if os_name is None else os_name
    if active_os != "nt":
        return ()
    root_value = system_root or os.environ.get("SystemRoot")
    if not root_value:
        raise RuntimeError("BGE_M3_WINDOWS_RUNTIME_UNAVAILABLE")
    system32 = Path(root_value) / "System32"
    paths = tuple(
        system32 / name
        for name in (
            "msvcp140.dll",
            "vcruntime140.dll",
            "vcruntime140_1.dll",
        )
    )
    if not all(path.is_file() for path in paths):
        raise RuntimeError("BGE_M3_WINDOWS_RUNTIME_UNAVAILABLE")
    if dll_loader is None:
        import ctypes

        dll_loader = ctypes.WinDLL
    try:
        handles = tuple(dll_loader(str(path)) for path in paths)
    except (AttributeError, OSError) as error:
        raise RuntimeError("BGE_M3_WINDOWS_RUNTIME_UNAVAILABLE") from error
    _WINDOWS_TORCH_RUNTIME_HANDLES.extend(handles)
    return handles


def _stable_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class PropertyKnowledgeRecord:
    record_id: str
    authority: str
    set_name: str
    property_name: str
    applicable_classes: tuple[str, ...]
    template_type: str
    value_type: str | None
    unit_types: tuple[str, ...]
    definition: str | None
    source_ref: str
    source_hash: str
    authorable: bool
    schema_version: str = PROPERTY_RECORD_SCHEMA_VERSION

    @property
    def canonical_path(self) -> str:
        return f"{self.set_name}.{self.property_name}"

    @property
    def search_text(self) -> str:
        values = [self.set_name, self.property_name]
        if self.definition:
            values.append(self.definition)
        return " ".join(values)

    def is_applicable(
        self,
        target_ifc_class: str,
        registry: IfcKnowledgeRegistry,
    ) -> bool:
        if target_ifc_class in self.applicable_classes:
            return True
        declaration = registry.entity(target_ifc_class)
        if declaration is None:
            return False
        supertypes = tuple(str(item) for item in declaration.get("supertypes", ()))
        return any(item in self.applicable_classes for item in supertypes)

    def to_dict(self) -> dict:
        value = asdict(self)
        value["applicable_classes"] = list(self.applicable_classes)
        value["unit_types"] = list(self.unit_types)
        return value

    @classmethod
    def from_dict(cls, value: dict) -> "PropertyKnowledgeRecord":
        return cls(
            record_id=str(value["record_id"]),
            authority=str(value["authority"]),
            set_name=str(value["set_name"]),
            property_name=str(value["property_name"]),
            applicable_classes=tuple(value["applicable_classes"]),
            template_type=str(value["template_type"]),
            value_type=(
                None if value.get("value_type") is None else str(value["value_type"])
            ),
            unit_types=tuple(value.get("unit_types", ())),
            definition=(
                None if value.get("definition") is None else str(value["definition"])
            ),
            source_ref=str(value["source_ref"]),
            source_hash=str(value["source_hash"]),
            authorable=bool(value["authorable"]),
            schema_version=str(
                value.get("schema_version", PROPERTY_RECORD_SCHEMA_VERSION)
            ),
        )


def build_standard_property_records(
    registry: IfcKnowledgeRegistry,
    *,
    corpus_fingerprint: str,
) -> tuple[PropertyKnowledgeRecord, ...]:
    records: list[PropertyKnowledgeRecord] = []
    for set_name in sorted(registry.property_sets):
        pset = registry.property_sets[set_name]
        applicable = tuple(str(item) for item in pset.get("applicable_classes", ()))
        for property_name in sorted(pset.get("properties", {})):
            definition = pset["properties"][property_name]
            template_type = str(definition["template_type"])
            value_type = definition.get("data_type")
            identity = {
                "schema": "IFC2X3",
                "set_name": set_name,
                "property_name": property_name,
                "source_hash": corpus_fingerprint,
            }
            records.append(
                PropertyKnowledgeRecord(
                    record_id=_stable_hash(identity),
                    authority="ifc2x3_psd",
                    set_name=set_name,
                    property_name=property_name,
                    applicable_classes=applicable,
                    template_type=template_type,
                    value_type=None if value_type is None else str(value_type),
                    unit_types=tuple(
                        str(item) for item in definition.get("unit_types", ())
                    ),
                    definition=(
                        None
                        if definition.get("definition") is None
                        else str(definition["definition"])
                    ),
                    source_ref=str(pset.get("source_path", "")),
                    source_hash=corpus_fingerprint,
                    authorable=(
                        template_type == "TypePropertySingleValue"
                        and value_type in SUPPORTED_AUTHORABLE_VALUE_TYPES
                    ),
                )
            )
    return tuple(records)


def build_project_property_records(
    element_records: Iterable[Any],
    *,
    source_ifc_sha256: str,
) -> tuple[PropertyKnowledgeRecord, ...]:
    """Aggregate observed project paths without embedding their values."""

    grouped: dict[
        tuple[str, str, str, str | None, bool],
        set[str],
    ] = {}
    for element in element_records:
        target_class = str(element.ifc_class)
        for fact in getattr(element, "properties", ()):
            if getattr(fact, "kind", None) != "pset":
                continue
            key = (
                str(fact.set_name),
                str(fact.property_name),
                target_class,
                (
                    None
                    if getattr(fact, "value_type", None) is None
                    else str(fact.value_type)
                ),
                bool(getattr(fact, "inherited", False)),
            )
            grouped.setdefault(key, set()).add(str(element.ifc_global_id))
    records: list[PropertyKnowledgeRecord] = []
    for (set_name, property_name, target_class, value_type, inherited), ids in sorted(
        grouped.items()
    ):
        identity = {
            "source_ifc_sha256": source_ifc_sha256,
            "set_name": set_name,
            "property_name": property_name,
            "target_ifc_class": target_class,
            "value_type": value_type,
            "inherited": inherited,
        }
        records.append(
            PropertyKnowledgeRecord(
                record_id=_stable_hash(identity),
                authority="current_ifc_project",
                set_name=set_name,
                property_name=property_name,
                applicable_classes=(target_class,),
                template_type="TypePropertySingleValue",
                value_type=value_type,
                unit_types=(),
                definition=(
                    f"Observed on {len(ids)} {target_class} occurrence(s); "
                    f"ownership={'type_inherited' if inherited else 'occurrence_direct'}."
                ),
                source_ref=f"ifc:{source_ifc_sha256}",
                source_hash=source_ifc_sha256,
                authorable=value_type in SUPPORTED_AUTHORABLE_VALUE_TYPES,
            )
        )
    return tuple(records)


@dataclass(frozen=True)
class CorpusBuildResult:
    status: str
    corpus_fingerprint: str
    record_count: int


class PropertyKnowledgeStore:
    """SQLite authority cache. Vector payloads are intentionally separate."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS property_records (
                    record_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_property_records (
                    source_ifc_sha256 TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(source_ifc_sha256, record_id)
                );
                """
            )

    @property
    def corpus_fingerprint(self) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key='standard_corpus_fingerprint'"
            ).fetchone()
        return None if row is None else str(row[0])

    def ensure_standard_corpus(
        self,
        *,
        corpus_fingerprint: str,
        records: Iterable[PropertyKnowledgeRecord],
    ) -> CorpusBuildResult:
        materialized = tuple(records)
        previous = self.corpus_fingerprint
        if previous == corpus_fingerprint:
            return CorpusBuildResult("reused", corpus_fingerprint, len(self.load_records()))
        with self._connect() as connection:
            connection.execute("DELETE FROM property_records")
            connection.executemany(
                "INSERT INTO property_records(record_id, payload_json) VALUES (?, ?)",
                (
                    (
                        record.record_id,
                        json.dumps(
                            record.to_dict(),
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    )
                    for record in materialized
                ),
            )
            connection.execute(
                """
                INSERT INTO metadata(key, value)
                VALUES ('standard_corpus_fingerprint', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (corpus_fingerprint,),
            )
        return CorpusBuildResult(
            "built" if previous is None else "rebuilt",
            corpus_fingerprint,
            len(materialized),
        )

    def load_records(self) -> tuple[PropertyKnowledgeRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM property_records ORDER BY record_id"
            ).fetchall()
        return tuple(
            PropertyKnowledgeRecord.from_dict(json.loads(str(row[0]))) for row in rows
        )

    def ensure_project_corpus(
        self,
        *,
        source_ifc_sha256: str,
        records: Iterable[PropertyKnowledgeRecord],
    ) -> CorpusBuildResult:
        materialized = tuple(records)
        with self._connect() as connection:
            existing = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM project_property_records
                    WHERE source_ifc_sha256=?
                    """,
                    (source_ifc_sha256,),
                ).fetchone()[0]
            )
            if existing:
                return CorpusBuildResult(
                    "reused", source_ifc_sha256, existing
                )
            connection.executemany(
                """
                INSERT INTO project_property_records(
                    source_ifc_sha256, record_id, payload_json
                ) VALUES (?, ?, ?)
                """,
                (
                    (
                        source_ifc_sha256,
                        record.record_id,
                        json.dumps(
                            record.to_dict(),
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    )
                    for record in materialized
                ),
            )
        return CorpusBuildResult(
            "built", source_ifc_sha256, len(materialized)
        )

    def load_project_records(
        self,
        source_ifc_sha256: str,
    ) -> tuple[PropertyKnowledgeRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json FROM project_property_records
                WHERE source_ifc_sha256=?
                ORDER BY record_id
                """,
                (source_ifc_sha256,),
            ).fetchall()
        return tuple(
            PropertyKnowledgeRecord.from_dict(json.loads(str(row[0])))
            for row in rows
        )


@dataclass(frozen=True)
class PropertyAlias:
    alias: str
    set_name: str
    property_name: str
    language: str
    review_status: str


@dataclass(frozen=True)
class PropertyResolutionPolicy:
    policy_id: str
    version: str
    max_candidates: int
    vector_min_score: float
    vector_min_margin: float


def load_property_resolution_policy(
    path: Path | str | None = None,
) -> PropertyResolutionPolicy:
    policy_path = (
        Path(path)
        if path is not None
        else Path(__file__).resolve().parents[2]
        / "schemas"
        / "ifc"
        / "knowledge"
        / "property_resolution_policy.json"
    )
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    return PropertyResolutionPolicy(
        policy_id=str(payload["policy_id"]),
        version=str(payload["version"]),
        max_candidates=int(payload["max_candidates"]),
        vector_min_score=float(payload["vector_min_score"]),
        vector_min_margin=float(payload["vector_min_margin"]),
    )


def load_reviewed_aliases(
    path: Path | str | None = None,
) -> tuple[PropertyAlias, ...]:
    alias_path = (
        Path(path)
        if path is not None
        else Path(__file__).resolve().parents[2]
        / "schemas"
        / "ifc"
        / "knowledge"
        / "property_aliases.json"
    )
    payload = json.loads(alias_path.read_text(encoding="utf-8"))
    aliases = tuple(
        PropertyAlias(
            alias=str(item["alias"]),
            set_name=str(item["set_name"]),
            property_name=str(item["property_name"]),
            language=str(item["language"]),
            review_status=str(item["review_status"]),
        )
        for item in payload["aliases"]
    )
    keys: set[tuple[str, str]] = set()
    for alias in aliases:
        key = (alias.language, _normalize(alias.alias))
        if key in keys:
            raise ValueError("PROPERTY_ALIAS_DUPLICATE")
        keys.add(key)
    return aliases


def default_standard_corpus_fingerprint() -> str:
    return _stable_hash(check_registry_files())


def create_default_property_resolver(
    *,
    vector_index: InMemoryVectorIndex | None = None,
) -> "PropertyKnowledgeResolver":
    registry = load_ifc2x3_registry()
    policy = load_property_resolution_policy()
    return PropertyKnowledgeResolver(
        registry=registry,
        records=build_standard_property_records(
            registry,
            corpus_fingerprint=default_standard_corpus_fingerprint(),
        ),
        aliases=load_reviewed_aliases(),
        vector_index=vector_index,
        max_candidates=policy.max_candidates,
        vector_min_score=policy.vector_min_score,
        vector_min_margin=policy.vector_min_margin,
    )


@dataclass(frozen=True)
class PropertyKnowledgeQuery:
    target_ifc_class: str
    phrase: str
    raw_value: object
    raw_unit: str | None = None
    scope: str | None = None
    project_length_unit: str = "m"
    schema_version: str = PROPERTY_QUERY_SCHEMA_VERSION


@dataclass(frozen=True)
class ResolvedExactProperty:
    set_name: str
    property_name: str
    value: object
    requested_value_type: str
    requested_unit: str | None
    scope: str


@dataclass(frozen=True)
class PropertyCandidate:
    record: PropertyKnowledgeRecord
    retrieval_paths: tuple[str, ...]
    keyword_score: float | None = None
    vector_score: float | None = None


@dataclass(frozen=True)
class PropertyResolutionDecision:
    status: str
    reason_code: str
    exact_intent: ResolvedExactProperty | None
    candidates: tuple[PropertyCandidate, ...]
    schema_version: str = PROPERTY_DECISION_SCHEMA_VERSION


class EmbeddingProvider(Protocol):
    model_id: str
    model_fingerprint: str

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


@dataclass(frozen=True)
class VectorHit:
    record_id: str
    score: float


class InMemoryVectorIndex:
    """Deterministic test/local vector seam; not an authority store."""

    def __init__(self, embedding_provider: EmbeddingProvider) -> None:
        self.embedding_provider = embedding_provider
        self._vectors: dict[str, tuple[float, ...]] = {}
        self._collection_version: str | None = None

    def build(self, records: Iterable[PropertyKnowledgeRecord]) -> None:
        materialized = tuple(records)
        embedded = self.embedding_provider.embed(
            [record.search_text for record in materialized]
        )
        if len(embedded) != len(materialized):
            raise ValueError("EMBEDDING_COUNT_MISMATCH")
        self._vectors = {
            record.record_id: tuple(float(value) for value in vector)
            for record, vector in zip(materialized, embedded, strict=True)
        }

    def search(self, text: str, *, limit: int = 10) -> tuple[VectorHit, ...]:
        query = tuple(float(value) for value in self.embedding_provider.embed([text])[0])
        hits = [
            VectorHit(record_id, _cosine(query, vector))
            for record_id, vector in self._vectors.items()
        ]
        return tuple(
            item
            for item in sorted(hits, key=lambda item: (-item.score, item.record_id))
            if item.score > 0.0
        )[:limit]

    def ensure_versioned(
        self,
        records: Iterable[PropertyKnowledgeRecord],
        *,
        collection_version: str,
    ) -> str:
        if self._vectors and self._collection_version == collection_version:
            return "reused"
        status = "rebuilt" if self._vectors else "built"
        self.build(records)
        self._collection_version = collection_version
        return status

    def search_allowed(
        self,
        text: str,
        *,
        allowed_record_ids: Iterable[str],
        limit: int,
    ) -> tuple[VectorHit, ...]:
        allowed = frozenset(str(item) for item in allowed_record_ids)
        if not allowed:
            return ()
        query = tuple(float(value) for value in self.embedding_provider.embed([text])[0])
        hits = (
            VectorHit(record_id, _cosine(query, vector))
            for record_id, vector in self._vectors.items()
            if record_id in allowed
        )
        return tuple(
            item
            for item in sorted(hits, key=lambda item: (-item.score, item.record_id))
            if item.score > 0.0
        )[:limit]


class BgeM3EmbeddingProvider:
    """Lazy local BGE-M3 adapter; importing this module never loads Torch."""

    model_id = "BAAI/bge-m3"

    def __init__(
        self,
        *,
        model_path: str = "BAAI/bge-m3",
        model_version: str = "configured",
        device: str | None = None,
        local_files_only: bool = True,
    ) -> None:
        self.model_path = model_path
        self.model_version = model_version
        self.device = device
        self.local_files_only = local_files_only
        self._model: Any | None = None
        self.model_fingerprint = _embedding_model_fingerprint(
            model_path,
            model_version=model_version,
        )

    def _load(self) -> Any:
        if self._model is None:
            _prepare_windows_torch_runtime()
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as error:
                raise RuntimeError("BGE_M3_DEPENDENCY_UNAVAILABLE") from error
            self._model = SentenceTransformer(
                self.model_path,
                device=self.device,
                local_files_only=self.local_files_only,
            )
        return self._model

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        vectors = self._load().encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [tuple(float(value) for value in vector) for vector in vectors]


class QdrantVectorIndex:
    """Rebuildable vector index backed by Qdrant local storage or service."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        *,
        collection_name: str,
        path: Path | str | None = None,
        url: str | None = None,
    ) -> None:
        if (path is None) == (url is None):
            raise ValueError("QDRANT_EXACTLY_ONE_LOCATION_REQUIRED")
        try:
            from qdrant_client import QdrantClient
        except ImportError as error:
            raise RuntimeError("QDRANT_DEPENDENCY_UNAVAILABLE") from error
        self.embedding_provider = embedding_provider
        self.collection_name = collection_name
        self._client = (
            QdrantClient(path=str(path)) if path is not None else QdrantClient(url=url)
        )

    def ensure(
        self,
        records: Iterable[PropertyKnowledgeRecord],
        *,
        collection_fingerprint: str,
    ) -> str:
        from qdrant_client.models import (
            Distance,
            PointStruct,
            VectorParams,
        )

        materialized = tuple(records)
        if not materialized:
            raise ValueError("PROPERTY_CORPUS_EMPTY")
        collections = {
            item.name for item in self._client.get_collections().collections
        }
        if self.collection_name in collections:
            info = self._client.get_collection(self.collection_name)
            payload = getattr(info, "config", None)
            del payload
            sample = self._client.scroll(
                self.collection_name,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )[0]
            if (
                sample
                and sample[0].payload
                and sample[0].payload.get("collection_fingerprint")
                == collection_fingerprint
            ):
                return "reused"
            self._client.delete_collection(self.collection_name)
        vectors = self.embedding_provider.embed(
            [record.search_text for record in materialized]
        )
        size = len(vectors[0])
        self._client.create_collection(
            self.collection_name,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE),
        )
        points = [
            PointStruct(
                id=index,
                vector=list(vector),
                payload={
                    "record_id": record.record_id,
                    "collection_fingerprint": collection_fingerprint,
                },
            )
            for index, (record, vector) in enumerate(
                zip(materialized, vectors, strict=True)
            )
        ]
        for offset in range(0, len(points), 128):
            self._client.upsert(
                collection_name=self.collection_name,
                points=points[offset : offset + 128],
                wait=True,
            )
        return "built"

    def ensure_versioned(
        self,
        records: Iterable[PropertyKnowledgeRecord],
        *,
        collection_version: str,
    ) -> str:
        from qdrant_client.models import (
            Distance,
            PointStruct,
            VectorParams,
        )

        materialized = tuple(records)
        if not materialized:
            raise ValueError("PROPERTY_CORPUS_EMPTY")
        collections = {
            item.name for item in self._client.get_collections().collections
        }
        existed = self.collection_name in collections
        if existed:
            sample = self._client.scroll(
                self.collection_name,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )[0]
            if (
                sample
                and sample[0].payload
                and sample[0].payload.get("collection_version") == collection_version
            ):
                return "reused"
            self._client.delete_collection(self.collection_name)
        vectors = self.embedding_provider.embed(
            [record.search_text for record in materialized]
        )
        if len(vectors) != len(materialized):
            raise ValueError("EMBEDDING_COUNT_MISMATCH")
        self._client.create_collection(
            self.collection_name,
            vectors_config=VectorParams(
                size=len(vectors[0]),
                distance=Distance.COSINE,
            ),
        )
        points = [
            PointStruct(
                id=index,
                vector=list(vector),
                payload={
                    "record_id": record.record_id,
                    "collection_version": collection_version,
                },
            )
            for index, (record, vector) in enumerate(
                zip(materialized, vectors, strict=True)
            )
        ]
        for offset in range(0, len(points), 128):
            self._client.upsert(
                collection_name=self.collection_name,
                points=points[offset : offset + 128],
                wait=True,
            )
        return "rebuilt" if existed else "built"

    def search(self, text: str, *, limit: int = 10) -> tuple[VectorHit, ...]:
        vector = list(self.embedding_provider.embed([text])[0])
        response = self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return tuple(
            VectorHit(str(item.payload["record_id"]), float(item.score))
            for item in response.points
            if item.payload and item.payload.get("record_id")
        )

    def search_allowed(
        self,
        text: str,
        *,
        allowed_record_ids: Iterable[str],
        limit: int,
    ) -> tuple[VectorHit, ...]:
        from qdrant_client.models import FieldCondition, Filter, MatchAny

        allowed = sorted({str(item) for item in allowed_record_ids})
        if not allowed:
            return ()
        vector = list(self.embedding_provider.embed([text])[0])
        response = self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="record_id",
                        match=MatchAny(any=allowed),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )
        return tuple(
            VectorHit(str(item.payload["record_id"]), float(item.score))
            for item in response.points
            if item.payload and item.payload.get("record_id")
        )

    def close(self) -> None:
        self._client.close()


def collection_fingerprint(
    *,
    corpus_fingerprint: str,
    aliases: Iterable[PropertyAlias],
    embedding_provider: EmbeddingProvider,
) -> str:
    return _stable_hash(
        {
            "record_schema_version": PROPERTY_RECORD_SCHEMA_VERSION,
            "corpus_fingerprint": corpus_fingerprint,
            "aliases": [
                asdict(item)
                for item in sorted(
                    aliases,
                    key=lambda value: (
                        value.language,
                        _normalize(value.alias),
                        value.set_name,
                        value.property_name,
                    ),
                )
            ],
            "embedding_model_id": embedding_provider.model_id,
            "embedding_model_fingerprint": embedding_provider.model_fingerprint,
        }
    )


def _embedding_model_fingerprint(
    model_path: str,
    *,
    model_version: str,
) -> str:
    path = Path(model_path)
    if path.is_dir():
        if not any(
            (path / name).is_file()
            for name in ("pytorch_model.bin", "model.safetensors")
        ):
            raise ValueError("BGE_M3_WEIGHT_FILE_MISSING")
    return ":".join(
        (
            "configured",
            BgeM3EmbeddingProvider.model_id,
            model_version,
        )
    )


class PropertyKnowledgeResolver:
    def __init__(
        self,
        *,
        registry: IfcKnowledgeRegistry,
        records: Iterable[PropertyKnowledgeRecord],
        aliases: Iterable[PropertyAlias],
        vector_index: Any | None = None,
        max_candidates: int = 5,
        vector_min_score: float = 0.50,
        vector_min_margin: float = 0.03,
    ) -> None:
        self.registry = registry
        self.records = tuple(records)
        self.aliases = tuple(aliases)
        self.vector_index = vector_index
        self.max_candidates = max_candidates
        self.vector_min_score = vector_min_score
        self.vector_min_margin = vector_min_margin
        self._by_path = {
            (record.set_name, record.property_name): record for record in self.records
        }
        self._by_id = {record.record_id: record for record in self.records}

    def resolve(self, query: PropertyKnowledgeQuery) -> PropertyResolutionDecision:
        applicable = tuple(
            record
            for record in self.records
            if record.authorable
            and record.is_applicable(query.target_ifc_class, self.registry)
        )
        canonical = self._canonical_exact(query.phrase, applicable)
        if canonical is not None:
            return self._resolved(query, canonical, "CANONICAL_EXACT", ("exact",))

        alias = self._alias_exact(query.phrase, applicable)
        if alias is not None:
            return self._resolved(
                query, alias, "REVIEWED_ALIAS_EXACT", ("reviewed_alias",)
            )

        keyword = self._keyword_candidates(query.phrase, applicable)
        vector = self._vector_candidates(query.phrase, applicable)
        candidates = self._fuse(keyword, vector)
        if keyword and vector and keyword[0][0].record_id == vector[0][0].record_id:
            top_record, keyword_score = keyword[0]
            vector_score = vector[0][1]
            vector_margin = (
                vector_score - vector[1][1]
                if len(vector) > 1
                else 1.0
            )
            if (
                vector_score >= self.vector_min_score
                and vector_margin >= self.vector_min_margin
            ):
                return self._resolved(
                    query,
                    top_record,
                    "HYBRID_CONSENSUS",
                    ("keyword", "vector"),
                    keyword_score=keyword_score,
                    vector_score=vector_score,
                    candidates=candidates,
                )
        if vector and not keyword:
            return PropertyResolutionDecision(
                status="clarification_required",
                reason_code="VECTOR_ONLY_NOT_AUTHORIZED",
                exact_intent=None,
                candidates=candidates,
            )
        if candidates:
            return PropertyResolutionDecision(
                status="clarification_required",
                reason_code="PROPERTY_CANDIDATES_AMBIGUOUS",
                exact_intent=None,
                candidates=candidates,
            )
        if _split_exact_path(query.phrase) is not None:
            return PropertyResolutionDecision(
                status="custom_confirmation_required",
                reason_code="UNKNOWN_PROPERTY",
                exact_intent=None,
                candidates=(),
            )
        return PropertyResolutionDecision(
            status="clarification_required",
            reason_code="PROPERTY_NOT_RESOLVED",
            exact_intent=None,
            candidates=(),
        )

    def _canonical_exact(
        self,
        phrase: str,
        records: Sequence[PropertyKnowledgeRecord],
    ) -> PropertyKnowledgeRecord | None:
        path = _split_exact_path(phrase)
        if path is None:
            return None
        matches = [
            record
            for record in records
            if (record.set_name, record.property_name) == path
        ]
        return matches[0] if len(matches) == 1 else None

    def _alias_exact(
        self,
        phrase: str,
        records: Sequence[PropertyKnowledgeRecord],
    ) -> PropertyKnowledgeRecord | None:
        normalized = _normalize(phrase)
        allowed = {record.record_id for record in records}
        matches = {
            record.record_id: record
            for alias in self.aliases
            if alias.review_status == "reviewed"
            and _normalize(alias.alias) == normalized
            and (
                record := self._by_path.get((alias.set_name, alias.property_name))
            )
            is not None
            and record.record_id in allowed
        }
        return next(iter(matches.values())) if len(matches) == 1 else None

    def _keyword_candidates(
        self,
        phrase: str,
        records: Sequence[PropertyKnowledgeRecord],
    ) -> list[tuple[PropertyKnowledgeRecord, float]]:
        normalized = _normalize(phrase)
        allowed = {record.record_id for record in records}
        scores: dict[str, float] = {}
        for alias in self.aliases:
            if alias.review_status != "reviewed":
                continue
            token = _normalize(alias.alias)
            record = self._by_path.get((alias.set_name, alias.property_name))
            if (
                record is not None
                and record.record_id in allowed
                and token
                and token in normalized
            ):
                scores[record.record_id] = max(
                    scores.get(record.record_id, 0.0),
                    len(token) / max(1, len(normalized)),
                )
        return sorted(
            ((self._by_id[record_id], score) for record_id, score in scores.items()),
            key=lambda item: (-item[1], item[0].canonical_path),
        )

    def _vector_candidates(
        self,
        phrase: str,
        records: Sequence[PropertyKnowledgeRecord],
    ) -> list[tuple[PropertyKnowledgeRecord, float]]:
        if self.vector_index is None:
            return []
        allowed = {record.record_id for record in records}
        return [
            (self._by_id[hit.record_id], hit.score)
            for hit in self.vector_index.search(phrase, limit=self.max_candidates * 4)
            if hit.record_id in allowed
        ][: self.max_candidates]

    def _fuse(
        self,
        keyword: Sequence[tuple[PropertyKnowledgeRecord, float]],
        vector: Sequence[tuple[PropertyKnowledgeRecord, float]],
    ) -> tuple[PropertyCandidate, ...]:
        values: dict[str, dict[str, object]] = {}
        for path, group in (("keyword", keyword), ("vector", vector)):
            for record, score in group:
                value = values.setdefault(
                    record.record_id,
                    {"record": record, "paths": set(), "keyword": None, "vector": None},
                )
                value["paths"].add(path)
                value[path] = score
        candidates = [
            PropertyCandidate(
                record=value["record"],
                retrieval_paths=tuple(sorted(value["paths"])),
                keyword_score=value["keyword"],
                vector_score=value["vector"],
            )
            for value in values.values()
        ]
        return tuple(
            sorted(
                candidates,
                key=lambda item: (
                    -len(item.retrieval_paths),
                    -(item.keyword_score or 0.0),
                    -(item.vector_score or 0.0),
                    item.record.canonical_path,
                ),
            )[: self.max_candidates]
        )

    def _resolved(
        self,
        query: PropertyKnowledgeQuery,
        record: PropertyKnowledgeRecord,
        reason_code: str,
        retrieval_paths: tuple[str, ...],
        *,
        keyword_score: float | None = None,
        vector_score: float | None = None,
        candidates: tuple[PropertyCandidate, ...] | None = None,
    ) -> PropertyResolutionDecision:
        if record.value_type is None:
            raise ValueError("PROPERTY_VALUE_TYPE_REQUIRED")
        value, unit = normalize_property_value(
            query.raw_value,
            raw_unit=query.raw_unit,
            value_type=record.value_type,
            project_length_unit=query.project_length_unit,
        )
        top = PropertyCandidate(
            record=record,
            retrieval_paths=retrieval_paths,
            keyword_score=keyword_score,
            vector_score=vector_score,
        )
        status = (
            "standard_resolved"
            if record.authority == "ifc2x3_psd"
            else "custom_confirmation_required"
        )
        return PropertyResolutionDecision(
            status=status,
            reason_code=reason_code,
            exact_intent=ResolvedExactProperty(
                set_name=record.set_name,
                property_name=record.property_name,
                value=value,
                requested_value_type=record.value_type,
                requested_unit=unit,
                scope=query.scope or "occurrence_direct",
            ),
            candidates=candidates or (top,),
        )


_LENGTH_FACTORS_TO_METRES = {
    "mm": 0.001,
    "毫米": 0.001,
    "cm": 0.01,
    "厘米": 0.01,
    "m": 1.0,
    "米": 1.0,
}
_LENGTH_FACTORS_TO_METRES.update(
    {"毫米": 0.001, "厘米": 0.01, "米": 1.0}
)


def normalize_property_value(
    raw_value: object,
    *,
    raw_unit: str | None,
    value_type: str,
    project_length_unit: str = "m",
) -> tuple[object, str | None]:
    if value_type in {"IfcBoolean", "IfcLogical"}:
        if not isinstance(raw_value, bool):
            raise ValueError("PROPERTY_VALUE_TYPE_INCOMPATIBLE")
        return raw_value, None
    if value_type == "IfcInteger":
        if not isinstance(raw_value, int) or isinstance(raw_value, bool):
            raise ValueError("PROPERTY_VALUE_TYPE_INCOMPATIBLE")
        return raw_value, None
    if value_type in {"IfcLabel", "IfcText", "IfcIdentifier"}:
        if not isinstance(raw_value, str):
            raise ValueError("PROPERTY_VALUE_TYPE_INCOMPATIBLE")
        return raw_value, None
    if value_type == "IfcLengthMeasure":
        if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
            raise ValueError("PROPERTY_VALUE_TYPE_INCOMPATIBLE")
        source = raw_unit or project_length_unit
        if source not in _LENGTH_FACTORS_TO_METRES:
            raise ValueError("PROPERTY_UNIT_UNSUPPORTED")
        if project_length_unit not in _LENGTH_FACTORS_TO_METRES:
            raise ValueError("PROJECT_LENGTH_UNIT_UNSUPPORTED")
        metres = float(raw_value) * _LENGTH_FACTORS_TO_METRES[source]
        normalized = metres / _LENGTH_FACTORS_TO_METRES[project_length_unit]
        return normalized, project_length_unit
    if value_type == "IfcReal":
        if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
            raise ValueError("PROPERTY_VALUE_TYPE_INCOMPATIBLE")
        if isinstance(raw_value, float) and not math.isfinite(raw_value):
            raise ValueError("PROPERTY_VALUE_INVALID")
        if raw_unit is not None:
            raise ValueError("PROPERTY_UNIT_FAMILY_UNSUPPORTED")
        return raw_value, None
    raise ValueError("PROPERTY_VALUE_TYPE_UNSUPPORTED")


def _split_exact_path(value: str) -> tuple[str, str] | None:
    stripped = value.strip()
    if stripped.count(".") != 1:
        return None
    set_name, property_name = stripped.split(".", 1)
    if not set_name or not property_name:
        return None
    return set_name, property_name


def _normalize(value: str) -> str:
    return re.sub(r"[\s_\-.:/]+", "", value).casefold()


def _cosine(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != len(second):
        raise ValueError("EMBEDDING_DIMENSION_MISMATCH")
    numerator = sum(a * b for a, b in zip(first, second, strict=True))
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0
    return numerator / (first_norm * second_norm)


__all__ = [
    "BgeM3EmbeddingProvider",
    "CorpusBuildResult",
    "EmbeddingProvider",
    "InMemoryVectorIndex",
    "PropertyAlias",
    "PropertyCandidate",
    "PropertyKnowledgeQuery",
    "PropertyKnowledgeRecord",
    "PropertyKnowledgeResolver",
    "PropertyKnowledgeStore",
    "PropertyResolutionDecision",
    "PropertyResolutionPolicy",
    "QdrantVectorIndex",
    "ResolvedExactProperty",
    "VectorHit",
    "build_project_property_records",
    "build_standard_property_records",
    "collection_fingerprint",
    "create_default_property_resolver",
    "default_standard_corpus_fingerprint",
    "load_property_resolution_policy",
    "load_reviewed_aliases",
    "normalize_property_value",
]
