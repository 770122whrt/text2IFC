from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence, runtime_checkable

from .index_models import ElementRecord


STRUCTURED_RETRIEVER_VERSION = "text2ifc/structured-retriever/0.1"


@dataclass(frozen=True)
class RetrievedCandidate:
    record: ElementRecord
    retriever: str
    retriever_version: str
    source_score: int
    matched_fields: tuple[str, ...] = ()


@runtime_checkable
class CandidateRetriever(Protocol):
    name: str
    version: str

    def retrieve(
        self, query: Any, candidates: Sequence[ElementRecord]
    ) -> list[RetrievedCandidate]: ...


class StructuredRetriever:
    name = "structured"
    version = STRUCTURED_RETRIEVER_VERSION

    def retrieve(self, query: Any, candidates: Sequence[ElementRecord]) -> list[RetrievedCandidate]:
        from .target_query import normalized_name_score

        retrieved = []
        for record in candidates:
            score, fields = normalized_name_score(query.names, record)
            if query.global_id == record.ifc_global_id:
                score += 1000
                fields = (*fields, "global_id")
            retrieved.append(
                RetrievedCandidate(record, self.name, self.version, score, tuple(sorted(set(fields))))
            )
        return retrieved


class CandidateFusion:
    version = "text2ifc/candidate-fusion/0.1"

    def fuse(self, groups: Sequence[Sequence[RetrievedCandidate]]) -> list[RetrievedCandidate]:
        fused: dict[str, RetrievedCandidate] = {}
        for group in groups:
            for item in group:
                current = fused.get(item.record.record_id)
                if current is None or item.source_score > current.source_score:
                    fused[item.record.record_id] = item
        return sorted(
            fused.values(),
            key=lambda item: (-item.source_score, item.record.ifc_global_id or "", item.record.record_id),
        )


class VectorRetrieverError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class VectorRetriever:
    """Reserved extension boundary; no embedding or network dependency."""

    name = "vector"
    version = "text2ifc/vector-retriever/0.1-disabled"
    enabled = False

    def retrieve(self, query: Any, candidates: Sequence[ElementRecord]) -> list[RetrievedCandidate]:
        raise VectorRetrieverError(
            "VECTOR_RETRIEVER_DISABLED",
            "Vector retrieval is reserved but disabled in Phase 7",
        )


__all__ = [
    "CandidateFusion",
    "CandidateRetriever",
    "RetrievedCandidate",
    "StructuredRetriever",
    "VectorRetriever",
    "VectorRetrieverError",
]
