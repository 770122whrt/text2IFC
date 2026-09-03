from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.index_models import AliasFact, ElementRecord, IndexMetadata, PropertyFact
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target


ROOT = Path(__file__).resolve().parents[2]


def _api() -> dict[str, object]:
    try:
        from text2ifc_ifc_repair.target_context import TargetContextError, build_target_context, canonical_target_context_json
    except ModuleNotFoundError:
        pytest.fail("Phase 7 target context API is not implemented yet")
    return locals()


def _record(index: int, *, properties: tuple[PropertyFact, ...] = ()) -> ElementRecord:
    guid = f"0{index:021d}"
    name = f"wall {index}"
    return ElementRecord(
        f"ifc:{guid}", guid, True, "IfcWall", name, None, None, None, "wall type", None,
        "Level 1", "0STOREYAAAAAAAAAAAAAAA", "straight_wall",
        {"orientation": "east"}, {"editable_target": True, "private_payload": "must-not-project"},
        {"source": "fixture"}, (AliasFact(name, name, "name", "fixture"),), (), properties,
    )


def _database(tmp_path: Path, records: list[ElementRecord]) -> Path:
    path = tmp_path / "context.sqlite"
    metadata = IndexMetadata("sha256:" + "a" * 64, "IFC2X3", "fixture", 1, "2026-07-19T00:00:00Z")
    with SQLiteIndexRepository.create(path, metadata) as repository:
        for record in records: repository.put_record(record)
        repository.publish()
    return path


def test_context_schema_and_normal_diagnostic_candidate_caps(tmp_path: Path) -> None:
    api = _api(); records = [_record(index) for index in range(7)]; database = _database(tmp_path, records)
    query = TargetQuery(allowed_ifc_classes=("IfcWall",), max_candidates=10)
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)
        normal = api["build_target_context"](repository, query, result)
        diagnostic = api["build_target_context"](repository, query, result, diagnostic=True)
    assert len(normal["candidate_targets"]) == 5
    assert normal["context_budget"]["max_candidates"] == 5
    assert len(diagnostic["candidate_targets"]) == 7
    assert diagnostic["context_budget"]["max_candidates"] == 10
    schema = json.loads((ROOT / "schemas/agent/ifc-target-context-0.1.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == "text2ifc/ifc-target-context/0.1"
    assert not list(Draft202012Validator(schema).iter_errors(normal))


def test_context_measurement_is_canonical_and_property_intent_is_allowlisted(tmp_path: Path) -> None:
    api = _api(); properties = (
        PropertyFact("pset", "Pset_WallCommon", "FireRating", "2h", "IfcLabel", None, True, "fixture"),
        PropertyFact("pset", "Secret", "Unrelated", "do-not-send", "IfcLabel", None, True, "fixture"),
    )
    record = _record(1, properties=properties); database = _database(tmp_path, [record])
    query = TargetQuery(allowed_ifc_classes=("IfcWall",), global_id=record.ifc_global_id, attribute_intents=({"property": "FireRating"},))
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)
        context = api["build_target_context"](repository, query, result, operation_hints=("add_window",))
    rendered = api["canonical_target_context_json"](context)
    size = len(rendered.encode("utf-8"))
    assert context["context_budget"]["actual_bytes"] == size
    assert context["context_budget"]["estimated_tokens"] == (size + 3) // 4
    assert context["candidate_targets"][0]["properties"][0]["property_name"] == "FireRating"
    assert "Unrelated" not in rendered and "private_payload" not in rendered
    assert {item["state"] for item in context["candidate_targets"][0]["evidence"]} >= {"matched", "unavailable"}


def test_context_budget_exceeded_is_explicit_and_resolved_candidate_is_pinned(tmp_path: Path) -> None:
    api = _api(); record = _record(1); database = _database(tmp_path, [record])
    query = TargetQuery(allowed_ifc_classes=("IfcWall",), global_id=record.ifc_global_id)
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(repository, query)
        context = api["build_target_context"](repository, query, result, max_bytes=12000)
        assert context["candidate_targets"][0]["target_id"] == result.resolved_target_id
        with pytest.raises(api["TargetContextError"]) as captured:
            api["build_target_context"](repository, query, result, max_bytes=10)
    assert captured.value.code == "TARGET_CONTEXT_BUDGET_EXCEEDED"
