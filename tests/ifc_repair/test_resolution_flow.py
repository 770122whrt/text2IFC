from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path

import pytest

from text2ifc_ifc_repair.index_models import (
    AliasFact,
    ElementRecord,
    IndexMetadata,
    PropertyFact,
    TypeRecord,
)
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import EXTRACTOR_VERSION
from text2ifc_ifc_repair.repair_intent import RepairIntent
from text2ifc_ifc_repair.registry import OperationDefinition, OperationRegistry


SOURCE_SHA = "sha256:" + "a" * 64
MODEL_FINGERPRINT = "sha256:" + "b" * 64


def _api():
    try:
        module = importlib.import_module("text2ifc_ifc_repair.resolution_flow")
    except ModuleNotFoundError:
        pytest.fail("Phase 9 resolution flow is not implemented")
    return module


def _registry(
    prototype_ifc_classes: tuple[str, ...] = ("IfcWindowStyle",),
) -> OperationRegistry:
    registry = OperationRegistry()
    for operation_type in ("fixture_move", "fixture_resize"):
        registry.register(
            OperationDefinition(
                operation_type=operation_type,
                target_ifc_classes=("IfcWall",),
                parameter_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["marker"],
                    "properties": {
                        "marker": {"type": "string"},
                        "opening": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "width_mm": {"type": "number"},
                                "height_mm": {"type": "number"},
                            },
                        },
                    },
                },
                context_adapter=lambda **kwargs: kwargs,
                precondition_checker=lambda **kwargs: (),
                applicator=lambda **kwargs: kwargs,
                postcondition_checker=lambda **kwargs: (),
                comparison_adapter=lambda **kwargs: kwargs,
                capability_constraints={"geometry": "straight_wall"},
                prototype_ifc_classes=prototype_ifc_classes,
                prototype_dimension_paths={
                    "width_mm": ("opening", "width_mm"),
                    "height_mm": ("opening", "height_mm"),
                },
            )
        )
    return registry


def _intent(
    *queries: dict,
    prototype: dict | None = None,
    prototype_ifc_classes: tuple[str, ...] = ("IfcWindowStyle",),
    parameters: dict | None = None,
) -> RepairIntent:
    operations = []
    for index, query in enumerate(queries):
        operations.append(
            {
                "operation_id": f"intent-{index + 1}",
                "operation_type": ("fixture_move", "fixture_resize")[index % 2],
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcWall"],
                    "max_candidates": 5,
                    "winner_margin": 10,
                    **query,
                },
                "parameters": {"marker": f"m{index + 1}", **(parameters or {})},
                "attribute_intents": [],
                "prototype_intent": prototype,
                "provenance": [
                    {"source_kind": "user_request", "reference": f"request:/operations/{index}", "excerpt": "repair wall"}
                ],
            }
        )
    return RepairIntent.from_dict(
        {
            "schema_version": "text2ifc/ifc-repair-intent/0.1",
            "request_id": "request-1",
            "source_request_hash": "sha256:" + "c" * 64,
            "model_fingerprint": MODEL_FINGERPRINT,
            "prompt_fingerprint": "sha256:" + "d" * 64,
            "operations": operations,
            "provenance": [
                {"source_kind": "user_request", "reference": "request:/text", "excerpt": "repair wall"}
            ],
        },
        registry=_registry(prototype_ifc_classes),
    )


def _record(guid: str, name: str, *, type_guid: str | None = None) -> ElementRecord:
    return ElementRecord(
        record_id=f"ifc:{guid}",
        ifc_global_id=guid,
        identity_reliable=True,
        ifc_class="IfcWall",
        name=name,
        long_name=None,
        tag=None,
        object_type="Basic Wall",
        type_name="Fixture Type" if type_guid else None,
        type_global_id=type_guid,
        storey_name="Level 1",
        storey_global_id="0STOREYAAAAAAAAAAAAAAA",
        geometry_capability="straight_wall",
        geometry_summary={"orientation": "east", "dimensions_mm": {"length": 4000}},
        facets={"editable_target": True},
        provenance={"source": "fixture"},
        aliases=(AliasFact(name.casefold(), name, "name", "fixture"),),
    )


def _type_record(
    guid: str = "0TYPEAAAAAAAAAAAAAAAAA",
    name: str = "Fixture Type",
    *,
    ifc_class: str = "IfcWindowStyle",
) -> TypeRecord:
    return TypeRecord(
        record_id=f"type:{guid}",
        ifc_global_id=guid,
        identity_reliable=True,
        ifc_class=ifc_class,
        name=name,
        applicable_occurrence=None,
        predefined_type=None,
        element_type=None,
        provenance={"source": "current_ifc", "step_id": 12},
        aliases=(AliasFact(name.casefold(), name, "name", "IfcTypeObject.Name"),),
        properties=(
            PropertyFact(
                "pset", "Dimensions", "Width", 915.0,
                "IfcLengthMeasure", None, False, "type:direct",
            ),
            PropertyFact(
                "pset", "Dimensions", "Height", 1830.0,
                "IfcLengthMeasure", None, False, "type:direct",
            ),
            PropertyFact(
                "pset", "Secret", "Private", "must-not-project",
                "IfcLabel", None, False, "type:direct",
            ),
        ),
    )


def _repository(
    tmp_path: Path,
    records: list[ElementRecord],
    *,
    types: list[TypeRecord] | None = None,
    source_sha: str = SOURCE_SHA,
) -> SQLiteIndexRepository:
    database = tmp_path / "targets.sqlite"
    metadata = IndexMetadata(source_sha, "IFC2X3", EXTRACTOR_VERSION, 123, "2026-07-20T00:00:00Z")
    with SQLiteIndexRepository.create(database, metadata) as writer:
        for type_record in types or []:
            writer.put_type_record(type_record)
        for record in records:
            writer.put_record(record)
        writer.publish()
    return SQLiteIndexRepository.open(database)


def test_exact_operations_create_one_fingerprint_bound_context_each(tmp_path: Path) -> None:
    api = _api()
    first = _record("0AAAAAAAAAAAAAAAAAAAAA", "east wall", type_guid="0TYPEAAAAAAAAAAAAAAAAA")
    second = _record("0BBBBBBBBBBBBBBBBBBBBB", "west wall")
    with _repository(tmp_path, [first, second]) as repository:
        result = api.resolve_repair_intent(
            _intent({"global_id": first.ifc_global_id}, {"global_id": second.ifc_global_id}),
            repository,
            expected_source_sha256=SOURCE_SHA,
        )

    assert result.status == "resolved"
    assert [item.operation_id for item in result.operations] == ["intent-1", "intent-2"]
    assert [item.target_global_id for item in result.operations] == [first.ifc_global_id, second.ifc_global_id]
    assert all(item.context["model_fingerprint"] == MODEL_FINGERPRINT for item in result.operations)
    assert all(item.context["model_constraints"]["source_ifc_sha256"] == SOURCE_SHA for item in result.operations)
    assert result.operations[0].authorized_semantics == (
        {"kind": "formal_type_binding", "global_id": "0TYPEAAAAAAAAAAAAAAAAA", "provenance": "current_ifc"},
    )


@pytest.mark.parametrize(
    ("queries", "expected"),
    [
        (({"global_id": "0MISSINGAAAAAAAAAAAAAAA"},), "not_found"),
        (({"names": ["same"]},), "ambiguous"),
        (({"global_id": "0AAAAAAAAAAAAAAAAAAAAA", "names": ["different"]},), "conflict"),
        (({"global_id": "0AAAAAAAAAAAAAAAAAAAAA", "geometry_capabilities": ["curved_wall"]},), "unsupported"),
    ],
)
def test_non_exact_resolution_returns_bounded_public_candidates(
    tmp_path: Path, queries: tuple[dict, ...], expected: str
) -> None:
    api = _api()
    records = [_record("0AAAAAAAAAAAAAAAAAAAAA", "same"), _record("0BBBBBBBBBBBBBBBBBBBBB", "same")]
    with _repository(tmp_path, records) as repository:
        result = api.resolve_repair_intent(_intent(*queries), repository, expected_source_sha256=SOURCE_SHA)

    assert result.status != "resolved" and result.reason_code == expected
    for candidate in result.candidates:
        assert set(candidate) == {"token", "public_id", "ifc_class", "name", "storey", "position", "evidence"}
        assert candidate["ifc_class"] == "IfcWall"
        assert isinstance(candidate["evidence"], list)


def test_stale_index_context_budget_and_missing_evidence_fail_closed(tmp_path: Path) -> None:
    api = _api()
    target = _record("0AAAAAAAAAAAAAAAAAAAAA", "east wall")
    with _repository(tmp_path / "stale", [target], source_sha="sha256:" + "f" * 64) as stale:
        stale_result = api.resolve_repair_intent(_intent({"global_id": target.ifc_global_id}), stale, expected_source_sha256=SOURCE_SHA)
    with _repository(tmp_path / "budget", [target]) as repository:
        budget_result = api.resolve_repair_intent(_intent({"global_id": target.ifc_global_id}), repository, expected_source_sha256=SOURCE_SHA, context_max_bytes=10)
    unreliable = _record("0CCCCCCCCCCCCCCCCCCCCC", "bad")
    unreliable = ElementRecord(**{**unreliable.__dict__, "ifc_global_id": None, "identity_reliable": False})
    with _repository(tmp_path / "evidence", [unreliable]) as repository:
        evidence_result = api.resolve_repair_intent(_intent({"names": ["bad"]}), repository, expected_source_sha256=SOURCE_SHA)

    assert stale_result.reason_code == "stale_index"
    assert budget_result.reason_code == "context_budget_exceeded"
    assert evidence_result.reason_code == "missing_evidence"


def test_similarity_never_authorizes_prototype_but_explicit_answer_does(tmp_path: Path) -> None:
    api = _api()
    target = _record("0AAAAAAAAAAAAAAAAAAAAA", "target")
    prototype = _type_record()
    request = _intent(
        {"global_id": target.ifc_global_id},
        prototype={
            "reference_kind": "selection_required",
            "reference": "candidate list",
            "source": {"source_kind": "user_request", "reference": "request:/prototype", "excerpt": "use a similar wall"},
        },
    )
    with _repository(tmp_path, [target], types=[prototype]) as repository:
        pending = api.resolve_repair_intent(
            request,
            repository,
            expected_source_sha256=SOURCE_SHA,
            operation_registry=_registry(),
        )
        resumed = api.authorize_prototype(
            pending,
            operation_id="intent-1",
            candidate_token=pending.candidates[0]["token"],
            authorized=True,
        )

    assert pending.status == "clarification_required"
    assert not any(item.get("kind") == "user_authorized_prototype" for item in pending.operations[0].authorized_semantics)
    assert resumed.operations[0].authorized_semantics[-1]["kind"] == "user_authorized_prototype"
    assert resumed.operations[0].authorized_semantics[-1]["authorization"] == "stored_user_answer"


@pytest.mark.parametrize(
    ("reference_kind", "reference", "expected_id", "expected_lookup"),
    [
        ("global_id", "0TYPEAAAAAAAAAAAAAAAAA", "0TYPEAAAAAAAAAAAAAAAAA", "type_global_id"),
        ("type_name", "  fixture   type ", "0TYPEAAAAAAAAAAAAAAAAA", "type_name"),
    ],
)
def test_explicit_named_prototype_is_resolved_with_request_provenance(
    tmp_path: Path,
    reference_kind: str,
    reference: str,
    expected_id: str,
    expected_lookup: str,
) -> None:
    target = _record("0AAAAAAAAAAAAAAAAAAAAA", "target")
    prototype = _type_record()
    request = _intent(
        {"global_id": target.ifc_global_id},
        prototype={
            "reference_kind": reference_kind,
            "reference": reference,
            "source": {"source_kind": "user_request", "reference": "request:/prototype", "excerpt": "use Fixture Type"},
        },
    )
    with _repository(tmp_path, [target], types=[prototype]) as repository:
        result = _api().resolve_repair_intent(request, repository, expected_source_sha256=SOURCE_SHA)
    assert result.status == "resolved"
    semantic = result.operations[0].authorized_semantics[-1]
    assert semantic["kind"] == "user_authorized_prototype"
    assert semantic["authorization"] == "explicit_request_reference"
    assert semantic["prototype_lookup"] == expected_lookup
    assert semantic["global_id"] == expected_id
    assert semantic["request_provenance"]["reference"] == "request:/prototype"


def test_selection_required_projects_one_bounded_candidate_per_type(tmp_path: Path) -> None:
    target = _record("0AAAAAAAAAAAAAAAAAAAAA", "target")
    shared_type = _type_record()
    occurrences = [
        _record(f"{index}BBBBBBBBBBBBBBBBBBBBB", f"window {index}", type_guid=shared_type.ifc_global_id)
        for index in range(1, 4)
    ]
    request = _intent(
        {"global_id": target.ifc_global_id},
        parameters={"opening": {"width_mm": 915.0, "height_mm": 1830.0}},
        prototype={
            "reference_kind": "selection_required",
            "reference": "915 x 1830 window",
            "source": {
                "source_kind": "user_request",
                "reference": "request:/prototype",
                "excerpt": "use a 915 x 1830 type",
            },
        },
    )
    decoys = [
        _type_record(
            "0DOORAAAAAAAAAAAAAAAAA",
            "Door with matching dimensions",
            ifc_class="IfcDoorStyle",
        ),
        _type_record(
            "0WINDOWBBBBBBBBBBBBBBBB",
            "Window with different dimensions",
        ),
    ]
    decoys[1] = TypeRecord(
        **{
            **decoys[1].__dict__,
            "properties": tuple(
                replace(fact, value=1200.0)
                if fact.property_name == "Width"
                else fact
                for fact in decoys[1].properties
            ),
        }
    )
    with _repository(
        tmp_path,
        [target, *occurrences],
        types=[shared_type, *decoys],
    ) as repository:
        pending = _api().resolve_repair_intent(
            request,
            repository,
            expected_source_sha256=SOURCE_SHA,
            operation_registry=_registry(),
        )

    assert pending.status == "clarification_required"
    assert len(pending.candidates) == 1
    candidate = pending.candidates[0]
    assert set(candidate) == {
        "candidate_kind", "token", "public_id", "ifc_class", "name",
        "dimensions", "occurrence_count", "storeys", "evidence",
    }
    assert candidate["candidate_kind"] == "type"
    assert candidate["dimensions"] == {"height_mm": 1830.0, "width_mm": 915.0}
    assert candidate["occurrence_count"] == 3
    assert "must-not-project" not in str(candidate)
    assert not pending.operations[0].authorized_semantics


def test_prototype_authorization_rejects_negative_and_tampered_tokens(tmp_path: Path) -> None:
    target = _record("0AAAAAAAAAAAAAAAAAAAAA", "target")
    request = _intent(
        {"global_id": target.ifc_global_id},
        prototype={
            "reference_kind": "selection_required",
            "reference": "candidate list",
            "source": {"source_kind": "user_request", "reference": "request:/prototype", "excerpt": "choose"},
        },
    )
    with _repository(tmp_path, [target], types=[_type_record()]) as repository:
        pending = _api().resolve_repair_intent(
            request,
            repository,
            expected_source_sha256=SOURCE_SHA,
            operation_registry=_registry(),
        )
    with pytest.raises(ValueError, match="PROTOTYPE_AUTHORIZATION_REQUIRED"):
        _api().authorize_prototype(
            pending, operation_id="intent-1",
            candidate_token=pending.candidates[0]["token"], authorized=False,
        )
    with pytest.raises(ValueError, match="PROTOTYPE_CANDIDATE_NOT_OFFERED"):
        _api().authorize_prototype(
            pending, operation_id="intent-1", candidate_token="tampered", authorized=True,
        )


def test_non_window_type_uses_the_same_human_readable_resolution(tmp_path: Path) -> None:
    target = _record("0AAAAAAAAAAAAAAAAAAAAA", "target")
    door_type = _type_record(
        "0DOORAAAAAAAAAAAAAAAAA", "Office Door Type", ifc_class="IfcDoorStyle"
    )
    request = _intent(
        {"global_id": target.ifc_global_id},
        prototype_ifc_classes=("IfcDoorStyle",),
        prototype={
            "reference_kind": "type_name",
            "reference": "office door type",
            "source": {"source_kind": "user_request", "reference": "request:/prototype", "excerpt": "use Office Door Type"},
        },
    )
    with _repository(tmp_path, [target], types=[door_type]) as repository:
        result = _api().resolve_repair_intent(
            request,
            repository,
            expected_source_sha256=SOURCE_SHA,
            operation_registry=_registry(("IfcDoorStyle",)),
        )
    assert result.status == "resolved"
    assert result.operations[0].authorized_semantics[-1]["global_id"] == door_type.ifc_global_id

