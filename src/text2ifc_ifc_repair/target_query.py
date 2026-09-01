from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator

from .index_models import ElementRecord
from .index_store import IndexRepository
from .indexer import normalize_alias
from .retrievers import CandidateFusion, CandidateRetriever, StructuredRetriever


QUERY_SCHEMA_VERSION = "text2ifc/ifc-target-query/0.1"
RESOLUTION_SCHEMA_VERSION = "text2ifc/ifc-target-resolution/0.1"
SCORE_VERSION = "text2ifc/target-score/0.1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class TargetQuery:
    allowed_ifc_classes: tuple[str, ...]
    global_id: str | None = None
    names: tuple[str, ...] = ()
    storey_name: str | None = None
    storey_global_id: str | None = None
    host_global_id: str | None = None
    grid: str | None = None
    space: str | None = None
    direction: str | None = None
    geometry_capabilities: tuple[str, ...] = ()
    geometry_constraints: tuple[dict[str, Any], ...] = ()
    attribute_intents: tuple[dict[str, Any], ...] = ()
    max_candidates: int = 5
    winner_margin: int = 10
    schema_version: str = QUERY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.allowed_ifc_classes:
            raise ValueError("TARGET_QUERY_CLASSES_REQUIRED")
        if not 1 <= self.max_candidates <= 10 or self.winner_margin < 1:
            raise ValueError("TARGET_QUERY_BUDGET_INVALID")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> TargetQuery:
        payload = dict(value)
        errors = sorted(_query_validator().iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            raise ValueError(f"TARGET_QUERY_SCHEMA_INVALID: {errors[0].message}")
        for key in ("allowed_ifc_classes", "names", "geometry_capabilities"):
            if key in payload:
                payload[key] = tuple(payload[key])
        payload["geometry_constraints"] = tuple(
            dict(item) for item in payload.get("geometry_constraints", ())
        )
        payload["attribute_intents"] = tuple(dict(item) for item in payload.get("attribute_intents", ()))
        return cls(**payload)


@dataclass(frozen=True)
class CandidateEvidence:
    field: str
    state: str
    query_value: Any
    candidate_value: Any
    provenance: str


@dataclass(frozen=True)
class CandidateHit:
    record_id: str
    ifc_global_id: str | None
    retriever: str
    retriever_version: str
    source_score: int
    fused_score: int
    matched_fields: tuple[str, ...]
    evidence: tuple[CandidateEvidence, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["matched_fields"] = list(self.matched_fields)
        result["evidence"] = [asdict(item) for item in self.evidence]
        return result


@dataclass(frozen=True)
class ResolutionResult:
    status: str
    resolved_target_id: str | None
    candidates: tuple[CandidateHit, ...] = ()
    attribute_intents: tuple[dict[str, Any], ...] = ()
    schema_version: str = RESOLUTION_SCHEMA_VERSION
    score_version: str = SCORE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "score_version": self.score_version,
            "status": self.status,
            "resolved_target_id": self.resolved_target_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "attribute_intents": [dict(item) for item in self.attribute_intents],
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def resolve_target(
    repository: IndexRepository,
    query: TargetQuery,
    *,
    retrievers: Sequence[CandidateRetriever] | None = None,
) -> ResolutionResult:
    all_records = [record for record in repository.iter_records() if record.identity_reliable]
    exact = repository.get_by_global_id(query.global_id) if query.global_id else None
    if query.global_id and exact is None:
        return _result("not_found", query)

    universe = [exact] if exact is not None else all_records
    eligible: list[ElementRecord] = []
    unsupported: list[ElementRecord] = []
    conflict = False
    for record in universe:
        hard_state, geometry_only = _hard_constraint_state(query, record)
        if hard_state:
            eligible.append(record)
        elif geometry_only:
            unsupported.append(record)
        elif exact is not None:
            conflict = True
    if conflict:
        return _result("conflict", query, candidates=_hits(query, universe, retrievers))
    if not eligible:
        status = "unsupported" if unsupported else "not_found"
        return _result(status, query, candidates=_hits(query, unsupported, retrievers))

    hits = _hits(query, eligible, retrievers)
    if query.names:
        hits = tuple(hit for hit in hits if any(field.startswith("name") or field.startswith("alias") or field == "type_name" for field in hit.matched_fields))
    if not hits:
        return _result("not_found", query)
    limited = hits[: query.max_candidates]
    if len(limited) > 1 and limited[0].fused_score - limited[1].fused_score < query.winner_margin:
        return _result("ambiguous", query, candidates=limited)
    return _result("resolved", query, resolved_target_id=limited[0].record_id, candidates=limited)


def _hits(
    query: TargetQuery,
    records: Sequence[ElementRecord],
    retrievers: Sequence[CandidateRetriever] | None,
) -> tuple[CandidateHit, ...]:
    active = tuple(retrievers or (StructuredRetriever(),))
    retrieved = CandidateFusion().fuse([retriever.retrieve(query, records) for retriever in active])
    return tuple(
        CandidateHit(
            record_id=item.record.record_id,
            ifc_global_id=item.record.ifc_global_id,
            retriever=item.retriever,
            retriever_version=item.retriever_version,
            source_score=item.source_score,
            fused_score=item.source_score,
            matched_fields=item.matched_fields,
            evidence=_candidate_evidence(query, item.record),
        )
        for item in retrieved
    )


def _result(
    status: str,
    query: TargetQuery,
    *,
    resolved_target_id: str | None = None,
    candidates: Sequence[CandidateHit] = (),
) -> ResolutionResult:
    result = ResolutionResult(status, resolved_target_id, tuple(candidates), tuple(dict(item) for item in query.attribute_intents))
    errors = list(_resolution_validator().iter_errors(result.to_dict()))
    if errors:
        raise RuntimeError(f"TARGET_RESOLUTION_SCHEMA_INVALID: {errors[0].message}")
    return result


def normalized_name_score(names: Iterable[str], record: ElementRecord) -> tuple[int, tuple[str, ...]]:
    requested = {normalize_alias(name) for name in names if name.strip()}
    if not requested:
        return 0, ()
    scores = {"name": 100, "long_name": 90, "tag": 85, "object_type": 75, "type_name": 70, "storey_name": 30}
    values: list[tuple[str, str]] = []
    for field_name in scores:
        value = getattr(record, field_name)
        if value:
            values.append((field_name, normalize_alias(value)))
    values.extend((f"alias:{alias.field}", alias.normalized_value) for alias in record.aliases)
    matched: list[tuple[int, str]] = []
    for field_name, value in values:
        if value in requested:
            base = scores.get(field_name.removeprefix("alias:"), 60)
            matched.append((base, field_name))
    if not matched:
        return 0, ()
    return max(score for score, _ in matched), tuple(sorted(field for _, field in matched))


def _hard_constraint_state(query: TargetQuery, record: ElementRecord) -> tuple[bool, bool]:
    if not _class_allowed(record.ifc_class, query.allowed_ifc_classes):
        return False, False
    if query.storey_name and normalize_alias(record.storey_name or "") != normalize_alias(query.storey_name):
        return False, False
    if query.storey_global_id and record.storey_global_id != query.storey_global_id:
        return False, False
    if query.host_global_id and not any(fact.kind == "hosted_by_wall" and fact.target_global_id == query.host_global_id for fact in record.relationships):
        return False, False
    if query.grid and normalize_alias(query.grid) not in {normalize_alias(str(value)) for value in record.facets.get("grid_labels", [])}:
        return False, False
    if query.space and normalize_alias(query.space) not in {normalize_alias(str(value)) for value in record.facets.get("space_names", [])}:
        return False, False
    if query.direction and normalize_alias(str(record.geometry_summary.get("orientation", ""))) != normalize_alias(query.direction):
        return False, False
    if query.geometry_capabilities and record.geometry_capability not in query.geometry_capabilities:
        return False, True
    if any(
        not _geometry_constraint_matches(constraint, record)
        for constraint in query.geometry_constraints
    ):
        return False, False
    if query.global_id and record.ifc_global_id != query.global_id:
        return False, False
    if query.global_id and query.names and normalized_name_score(query.names, record)[0] == 0:
        return False, False
    return True, False


def _class_allowed(actual: str, allowed: Sequence[str]) -> bool:
    return any(actual == expected or (expected == "IfcWall" and actual == "IfcWallStandardCase") for expected in allowed)


def _candidate_evidence(query: TargetQuery, record: ElementRecord) -> tuple[CandidateEvidence, ...]:
    entries = [
        _evidence("global_id", query.global_id, record.ifc_global_id, "IfcRoot.GlobalId"),
        _evidence("ifc_class", list(query.allowed_ifc_classes), record.ifc_class, "IfcProduct.is_a", matched=_class_allowed(record.ifc_class, query.allowed_ifc_classes)),
        _evidence("name", list(query.names) if query.names else None, record.name, "aliases", matched=normalized_name_score(query.names, record)[0] > 0 if query.names else None),
        _evidence("storey", query.storey_name or query.storey_global_id, record.storey_name or record.storey_global_id, "spatial_relationship"),
        _evidence(
            "geometry_capability",
            (
                list(query.geometry_capabilities)
                if query.geometry_capabilities
                else None
            ),
            record.geometry_capability,
            "adapter",
            matched=(
                record.geometry_capability in query.geometry_capabilities
                if query.geometry_capabilities
                else None
            ),
        ),
    ]
    entries.extend(
        _evidence(
            f"geometry:{constraint['field']}",
            {
                "value": constraint["value"],
                "tolerance_mm": constraint["tolerance_mm"],
            },
            _geometry_constraint_value(str(constraint["field"]), record),
            "ifc_geometry",
            matched=_geometry_constraint_matches(constraint, record),
        )
        for constraint in query.geometry_constraints
    )
    return tuple(entries)


def _geometry_constraint_matches(
    constraint: Mapping[str, Any], record: ElementRecord
) -> bool:
    actual = _geometry_constraint_value(str(constraint["field"]), record)
    if actual is None:
        return False
    return abs(actual - float(constraint["value"])) <= float(
        constraint["tolerance_mm"]
    )


def _geometry_constraint_value(
    field_name: str, record: ElementRecord
) -> float | None:
    if field_name == "storey_elevation_mm":
        value = record.facets.get("storey_elevation_mm")
    else:
        dimension_keys = {
            "wall_length_mm": ("length",),
            "wall_height_mm": ("height",),
            "wall_thickness_mm": ("thickness",),
            # Hosted openings measure width/height/depth; opening fillings
            # (Window/Door) carry the same opening size as OverallWidth/Height.
            "opening_width_mm": ("width", "overall_width"),
            "opening_height_mm": ("height", "overall_height"),
            "opening_depth_mm": ("depth",),
        }.get(field_name)
        if dimension_keys is not None:
            dimensions = record.geometry_summary.get("dimensions_mm", {})
            value = next(
                (dimensions[key] for key in dimension_keys if key in dimensions),
                None,
            )
        else:
            position_key = {
                "opening_center_offset_mm": "center_offset_mm",
                "opening_sill_height_mm": "sill_height_mm",
                "opening_normal_offset_mm": "normal_offset_mm",
            }.get(field_name)
            if position_key is None:
                return None
            value = record.geometry_summary.get(
                "wall_local_position_mm", {}
            ).get(position_key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _evidence(field: str, requested: Any, actual: Any, provenance: str, matched: bool | None = None) -> CandidateEvidence:
    if requested is None or actual is None:
        state = "unavailable"
    elif matched is not None:
        state = "matched" if matched else "mismatched"
    else:
        state = "matched" if normalize_alias(str(requested)) == normalize_alias(str(actual)) else "mismatched"
    return CandidateEvidence(field, state, requested, actual, provenance)


def _query_validator() -> Draft202012Validator:
    schema = json.loads((PROJECT_ROOT / "schemas/agent/ifc-target-query-0.1.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _resolution_validator() -> Draft202012Validator:
    schema = json.loads((PROJECT_ROOT / "schemas/agent/ifc-target-resolution-0.1.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


__all__ = [
    "CandidateEvidence",
    "CandidateHit",
    "QUERY_SCHEMA_VERSION",
    "RESOLUTION_SCHEMA_VERSION",
    "ResolutionResult",
    "SCORE_VERSION",
    "TargetQuery",
    "resolve_target",
]
