from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest


SOURCE_HASH = "sha256:" + "1" * 64


def _api() -> dict[str, object]:
    try:
        from text2ifc_ifc_repair.index_models import (
            INDEX_SCHEMA_VERSION,
            AliasFact,
            ElementRecord,
            IndexDiagnostic,
            IndexMetadata,
            PropertyFact,
            RelationshipFact,
        )
        from text2ifc_ifc_repair.index_store import (
            IndexStoreError,
            SQLiteIndexRepository,
        )
    except ModuleNotFoundError:
        pytest.fail("Phase 7 index repository API is not implemented yet")
    return locals()


def _metadata(**changes: object) -> object:
    values = {
        "source_ifc_sha256": SOURCE_HASH,
        "ifc_schema": "IFC2X3",
        "extractor_version": "text2ifc/ifc-indexer/0.1",
        "source_size_bytes": 1234,
        "created_at": "2026-07-19T00:00:00Z",
    }
    values.update(changes)
    return _api()["IndexMetadata"](**values)


def _record(
    global_id: str = "1F6umJ5H50aeL3A1As_wTm",
    *,
    record_id: str | None = None,
    reliable: bool = True,
) -> object:
    api = _api()
    return api["ElementRecord"](
        record_id=record_id or f"ifc:{global_id}",
        ifc_global_id=global_id,
        identity_reliable=reliable,
        ifc_class="IfcWallStandardCase",
        name="Basic Wall:Outside wall:346660",
        long_name=None,
        tag="346660",
        object_type="Basic Wall:Outside wall",
        type_name="Outside wall",
        type_global_id="0AAAAAAAAAAAAAAAAAAAAA",
        storey_name="Level 1",
        storey_global_id="0BBBBBBBBBBBBBBBBBBBBB",
        geometry_capability="straight_wall",
        geometry_summary={"axis_start_mm": [0.0, 0.0, 0.0]},
        facets={"wall": {"thickness_mm": 200.0}},
        provenance={"source": "ifc"},
        aliases=(
            api["AliasFact"](
                normalized_value="outside wall",
                original_value="Outside Wall",
                field="type_name",
                provenance="IfcWallType.Name",
            ),
            api["AliasFact"](
                normalized_value="x'); drop table elements;--",
                original_value="x'); DROP TABLE elements;--",
                field="name",
                provenance="IfcRoot.Name",
            ),
        ),
        relationships=(
            api["RelationshipFact"](
                kind="contained_in",
                target_global_id="0BBBBBBBBBBBBBBBBBBBBB",
                provenance="IfcRelContainedInSpatialStructure",
            ),
        ),
        properties=(
            api["PropertyFact"](
                set_kind="pset",
                set_name="Dimensions",
                property_name="Width",
                value=915.0,
                value_type="IfcLengthMeasure",
                unit="millimetre",
                inherited=True,
                provenance="ifcopenshell.util.element.get_psets",
            ),
        ),
    )


def test_repository_round_trips_versioned_element_records(tmp_path: Path) -> None:
    api = _api()
    SQLiteIndexRepository = api["SQLiteIndexRepository"]
    database = tmp_path / "model.sqlite"
    record = _record()

    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_record(record)
        repository.put_diagnostic(
            api["IndexDiagnostic"](
                code="INDEX_GEOMETRY_UNAVAILABLE",
                severity="warning",
                message="fixture",
                record_id=record.record_id,
                ifc_global_id=record.ifc_global_id,
                step_id=42,
                evidence={"field": "geometry"},
            )
        )
        repository.publish()

    with SQLiteIndexRepository.open(database) as repository:
        assert repository.metadata == _metadata()
        assert repository.get_by_global_id(record.ifc_global_id) == record
        assert list(repository.iter_records()) == [record]
        assert repository.find_aliases("outside wall") == [record]
        assert repository.find_aliases("x'); drop table elements;--") == [record]
        assert repository.properties_for(record.record_id) == list(record.properties)
        assert repository.relationships_from(record.record_id) == list(
            record.relationships
        )
        assert repository.diagnostics()[0].code == "INDEX_GEOMETRY_UNAVAILABLE"

    assert api["INDEX_SCHEMA_VERSION"] == "text2ifc/ifc-index/0.1"


def test_repository_orders_records_independent_of_insert_order(tmp_path: Path) -> None:
    SQLiteIndexRepository = _api()["SQLiteIndexRepository"]
    database = tmp_path / "model.sqlite"
    second = _record("2BBBBBBBBBBBBBBBBBBBBB")
    first = _record("1AAAAAAAAAAAAAAAAAAAAA")
    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_record(second)
        repository.put_record(first)
        repository.publish()

    with SQLiteIndexRepository.open(database) as repository:
        assert [record.record_id for record in repository.iter_records()] == [
            first.record_id,
            second.record_id,
        ]


def test_repository_rejects_duplicate_reliable_global_ids(tmp_path: Path) -> None:
    api = _api()
    IndexStoreError = api["IndexStoreError"]
    SQLiteIndexRepository = api["SQLiteIndexRepository"]
    database = tmp_path / "model.sqlite"
    first = _record(record_id="ifc:first")
    duplicate = replace(first, record_id="ifc:duplicate")
    with pytest.raises(IndexStoreError) as captured:
        with SQLiteIndexRepository.create(database, _metadata()) as repository:
            repository.put_record(first)
            repository.put_record(duplicate)
    assert captured.value.code == "DUPLICATE_RELIABLE_GLOBAL_ID"
    assert not database.exists()


def test_unreliable_identity_is_diagnostic_only(tmp_path: Path) -> None:
    SQLiteIndexRepository = _api()["SQLiteIndexRepository"]
    database = tmp_path / "model.sqlite"
    unreliable = _record(record_id="diagnostic:42", reliable=False)
    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_record(unreliable)
        repository.publish()

    with SQLiteIndexRepository.open(database) as repository:
        assert repository.get_by_global_id(unreliable.ifc_global_id) is None
        assert list(repository.iter_records())[0].identity_reliable is False


def test_failed_build_does_not_replace_published_database(tmp_path: Path) -> None:
    SQLiteIndexRepository = _api()["SQLiteIndexRepository"]
    database = tmp_path / "model.sqlite"
    original = _record()
    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_record(original)
        repository.publish()
    original_bytes = database.read_bytes()

    with pytest.raises(RuntimeError, match="fixture failure"):
        with SQLiteIndexRepository.create(database, _metadata()) as repository:
            repository.put_record(_record("2BBBBBBBBBBBBBBBBBBBBB"))
            raise RuntimeError("fixture failure")

    assert database.read_bytes() == original_bytes
    assert not list(tmp_path.glob("*.building-*"))


def test_open_rejects_source_and_schema_version_mismatch(tmp_path: Path) -> None:
    api = _api()
    IndexStoreError = api["IndexStoreError"]
    SQLiteIndexRepository = api["SQLiteIndexRepository"]
    database = tmp_path / "model.sqlite"
    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_record(_record())
        repository.publish()

    with pytest.raises(IndexStoreError) as source_error:
        SQLiteIndexRepository.open(
            database, expected_source_ifc_sha256="sha256:" + "2" * 64
        )
    assert source_error.value.code == "INDEX_SOURCE_FINGERPRINT_MISMATCH"

    with pytest.raises(IndexStoreError) as version_error:
        SQLiteIndexRepository.open(
            database, expected_index_schema_version="text2ifc/ifc-index/9.9"
        )
    assert version_error.value.code == "INDEX_SCHEMA_VERSION_MISMATCH"
