from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.index_models import AliasFact, ElementRecord, IndexMetadata, RelationshipFact
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository


ROOT = Path(__file__).resolve().parents[2]


def _api() -> dict[str, object]:
    try:
        from text2ifc_ifc_repair.retrievers import CandidateRetriever, VectorRetriever, VectorRetrieverError
        from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target
    except ModuleNotFoundError:
        pytest.fail("Phase 7 target query API is not implemented yet")
    return locals()


def _record(guid: str, name: str, **changes: object) -> ElementRecord:
    values = dict(
        record_id=f"ifc:{guid}", ifc_global_id=guid, identity_reliable=True,
        ifc_class="IfcWallStandardCase", name=name, long_name=None, tag=None,
        object_type="Basic Wall", type_name="Outside wall", type_global_id=None,
        storey_name="Level 1", storey_global_id="0STOREYAAAAAAAAAAAAAAA",
        geometry_capability="straight_wall",
        geometry_summary={"orientation": "east"},
        facets={"editable_target": True, "grid_labels": ["A"], "space_names": ["Office 101"]},
        provenance={"source": "fixture"},
        aliases=(AliasFact(name.casefold(), name, "name", "IfcRoot.Name"),),
        relationships=(), properties=(),
    )
    values.update(changes)
    return ElementRecord(**values)


def _repository(tmp_path: Path, records: list[ElementRecord], name: str = "targets.sqlite") -> Path:
    database = tmp_path / name
    metadata = IndexMetadata("sha256:" + "1" * 64, "IFC2X3", "fixture", 1, "2026-07-19T00:00:00Z")
    with SQLiteIndexRepository.create(database, metadata) as repository:
        for record in records:
            repository.put_record(record)
        repository.publish()
    return database


def test_target_schemas_freeze_exact_versions() -> None:
    query_schema = json.loads((ROOT / "schemas/agent/ifc-target-query-0.1.schema.json").read_text(encoding="utf-8"))
    resolution_schema = json.loads((ROOT / "schemas/agent/ifc-target-resolution-0.1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(query_schema)
    Draft202012Validator.check_schema(resolution_schema)
    assert query_schema["properties"]["schema_version"]["const"] == "text2ifc/ifc-target-query/0.1"
    assert resolution_schema["properties"]["schema_version"]["const"] == "text2ifc/ifc-target-resolution/0.1"


def test_exact_guid_resolves_with_schema_valid_audit_evidence(tmp_path: Path) -> None:
    api = _api(); target = _record("0AAAAAAAAAAAAAAAAAAAAA", "Outside wall")
    database = _repository(tmp_path, [target])
    query = api["TargetQuery"](allowed_ifc_classes=("IfcWall",), global_id=target.ifc_global_id)
    with SQLiteIndexRepository.open(database) as repository:
        result = api["resolve_target"](repository, query)
    assert result.status == "resolved" and result.resolved_target_id == target.record_id
    assert result.candidates[0].retriever == "structured"
    assert result.candidates[0].retriever_version
    schema = json.loads((ROOT / "schemas/agent/ifc-target-resolution-0.1.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(result.to_dict()))


@pytest.mark.parametrize("field,value", [("allowed_ifc_classes", ("IfcDoor",)), ("storey_name", "Level 9"), ("names", ("another wall",))])
def test_exact_guid_conflicting_selectors_never_override_constraints(tmp_path: Path, field: str, value: object) -> None:
    api = _api(); target = _record("0AAAAAAAAAAAAAAAAAAAAA", "Outside wall")
    database = _repository(tmp_path, [target])
    values = {"allowed_ifc_classes": ("IfcWall",), "global_id": target.ifc_global_id, field: value}
    with SQLiteIndexRepository.open(database) as repository:
        result = api["resolve_target"](repository, api["TargetQuery"](**values))
    assert result.status == "conflict" and result.resolved_target_id is None


def test_hard_storey_host_and_alias_filters_resolve_before_scoring(tmp_path: Path) -> None:
    api = _api(); host = "0HOSTAAAAAAAAAAAAAAAAA"
    wrong = _record("0AAAAAAAAAAAAAAAAAAAAA", "Meeting wall")
    right = _record("0BBBBBBBBBBBBBBBBBBBBB", "Meeting wall", storey_name="Level 2", relationships=(RelationshipFact("hosted_by_wall", host, "fixture"),))
    database = _repository(tmp_path, [wrong, right])
    query = api["TargetQuery"](allowed_ifc_classes=("IfcWall",), names=("MEETING WALL",), storey_name="Level 2", host_global_id=host)
    with SQLiteIndexRepository.open(database) as repository:
        result = api["resolve_target"](repository, query)
    assert result.status == "resolved" and result.resolved_target_id == right.record_id


def test_zero_match_and_same_name_tie_abstain(tmp_path: Path) -> None:
    api = _api(); records = [_record("0AAAAAAAAAAAAAAAAAAAAA", "same"), _record("0BBBBBBBBBBBBBBBBBBBBB", "same")]
    database = _repository(tmp_path, records)
    with SQLiteIndexRepository.open(database) as repository:
        missing = api["resolve_target"](repository, api["TargetQuery"](allowed_ifc_classes=("IfcDoor",), names=("none",)))
        tied = api["resolve_target"](repository, api["TargetQuery"](allowed_ifc_classes=("IfcWall",), names=("same",)))
    assert missing.status == "not_found" and missing.resolved_target_id is None
    assert tied.status == "ambiguous" and tied.resolved_target_id is None
    assert [hit.ifc_global_id for hit in tied.candidates] == sorted(hit.ifc_global_id for hit in tied.candidates)


def test_mandatory_spatial_direction_and_geometry_constraints(tmp_path: Path) -> None:
    api = _api(); target = _record("0AAAAAAAAAAAAAAAAAAAAA", "east office wall")
    database = _repository(tmp_path, [target])
    valid = api["TargetQuery"](allowed_ifc_classes=("IfcWall",), grid="A", space="Office 101", direction="east", geometry_capabilities=("straight_wall",))
    unsupported = api["TargetQuery"](allowed_ifc_classes=("IfcWall",), names=("east office wall",), geometry_capabilities=("curved_wall",))
    with SQLiteIndexRepository.open(database) as repository:
        resolved = api["resolve_target"](repository, valid)
        rejected = api["resolve_target"](repository, unsupported)
    assert resolved.status == "resolved"
    assert rejected.status == "unsupported" and rejected.resolved_target_id is None


def test_attribute_intent_is_preserved_and_evidence_has_all_states(tmp_path: Path) -> None:
    api = _api(); target = _record("0AAAAAAAAAAAAAAAAAAAAA", "outside wall", storey_name=None)
    database = _repository(tmp_path, [target])
    intents = ({"property": "FireRating", "value": "2h"},)
    query = api["TargetQuery"](allowed_ifc_classes=("IfcWall",), names=("outside wall",), attribute_intents=intents)
    with SQLiteIndexRepository.open(database) as repository:
        result = api["resolve_target"](repository, query)
    assert result.attribute_intents == intents
    states = {evidence.state for evidence in result.candidates[0].evidence}
    assert {"matched", "unavailable"} <= states


def test_vector_boundary_is_disabled_without_embedding_dependency() -> None:
    api = _api(); retriever = api["VectorRetriever"]()
    assert retriever.enabled is False
    with pytest.raises(api["VectorRetrieverError"]) as captured:
        retriever.retrieve(None, [])
    assert captured.value.code == "VECTOR_RETRIEVER_DISABLED"


def test_resolution_is_repeatable_and_does_not_mutate_query(tmp_path: Path) -> None:
    api = _api(); records = [_record("0BBBBBBBBBBBBBBBBBBBBB", "other"), _record("0AAAAAAAAAAAAAAAAAAAAA", "target")]
    database = _repository(tmp_path, records); query_data = {"allowed_ifc_classes": ("IfcWall",), "names": ("target",)}
    original = copy.deepcopy(query_data); query = api["TargetQuery"](**query_data)
    with SQLiteIndexRepository.open(database) as repository:
        first = api["resolve_target"](repository, query).canonical_json()
        second = api["resolve_target"](repository, query).canonical_json()
    assert first == second and query_data == original
