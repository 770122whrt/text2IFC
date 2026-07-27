from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest


SOURCE_HASH = "sha256:" + "1" * 64


def _api() -> dict[str, object]:
    try:
        import text2ifc_ifc_repair.index_models as index_models
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
    TypeRecord = getattr(index_models, "TypeRecord", None)
    AssociationFact = getattr(index_models, "AssociationFact", None)
    return locals()


def _metadata(**changes: object) -> object:
    values = {
        "source_ifc_sha256": SOURCE_HASH,
        "ifc_schema": "IFC2X3",
        "extractor_version": "text2ifc/ifc-indexer/0.2",
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


def _type_record(
    global_id: str = "0AAAAAAAAAAAAAAAAAAAAA",
    *,
    record_id: str | None = None,
    reliable: bool = True,
) -> object:
    api = _api()
    TypeRecord = api["TypeRecord"]
    assert TypeRecord is not None, "TypeRecord must be a first-class index model"
    return TypeRecord(
        record_id=record_id or f"type:{global_id}",
        ifc_global_id=global_id,
        identity_reliable=reliable,
        ifc_class="IfcWindowStyle",
        name="M_Fixed:0915 x 1830mm",
        applicable_occurrence=None,
        predefined_type=None,
        element_type=None,
        provenance={"source": "current_ifc", "step_id": 13039},
        aliases=(
            api["AliasFact"](
                normalized_value="m fixed 0915 x 1830mm",
                original_value="M_Fixed:0915 x 1830mm",
                field="name",
                provenance="IfcTypeObject.Name",
            ),
        ),
        properties=(
            api["PropertyFact"](
                set_kind="pset",
                set_name="Dimensions",
                property_name="Width",
                value=915.0,
                value_type="IfcLengthMeasure",
                unit=None,
                inherited=False,
                provenance="ifcopenshell.util.element.get_psets:direct",
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

    assert api["INDEX_SCHEMA_VERSION"] == "text2ifc/ifc-index/0.4"


def test_repository_round_trips_first_class_association_facts(tmp_path: Path) -> None:
    api = _api()
    AssociationFact = api["AssociationFact"]
    assert AssociationFact is not None, "association evidence must be first-class"
    association = AssociationFact(
        association_kind="material",
        relationship_ref="guid:0CCCCCCCCCCCCCCCCCCCCC",
        relationship_ifc_class="IfcRelAssociatesMaterial",
        resource_ref="step:81",
        resource_ifc_class="IfcMaterial",
        resource_name="Glass",
        semantic_value={"name": "Glass"},
        inherited=False,
        occurrence_global_id="1F6umJ5H50aeL3A1As_wTm",
        occurrence_type_global_id="0AAAAAAAAAAAAAAAAAAAAA",
        provenance=("current_ifc:#81", "IfcRelAssociatesMaterial:#82"),
    )
    record = replace(_record(), associations=(association,))
    database = tmp_path / "associations.sqlite"

    with api["SQLiteIndexRepository"].create(database, _metadata()) as repository:
        repository.put_record(record)
        repository.publish()

    with api["SQLiteIndexRepository"].open(database) as repository:
        assert repository.associations_for(record.record_id) == [association]
        assert repository.get_by_global_id(record.ifc_global_id).associations == (
            association,
        )


def test_repository_round_trips_type_records_in_dedicated_tables(tmp_path: Path) -> None:
    api = _api()
    SQLiteIndexRepository = api["SQLiteIndexRepository"]
    database = tmp_path / "types.sqlite"
    type_record = _type_record()
    level_2 = replace(
        _record("2BBBBBBBBBBBBBBBBBBBBB"),
        type_global_id=type_record.ifc_global_id,
        storey_name="Level 2",
    )
    level_1 = replace(
        _record("1AAAAAAAAAAAAAAAAAAAAA"),
        type_global_id=type_record.ifc_global_id,
        storey_name="Level 1",
    )

    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_type_record(type_record)
        repository.put_record(level_2)
        repository.put_record(level_1)
        repository.publish()

    with SQLiteIndexRepository.open(database) as repository:
        assert repository.get_type_by_global_id(type_record.ifc_global_id) == type_record
        assert list(repository.iter_type_records()) == [type_record]
        assert repository.find_type_aliases("m fixed 0915 x 1830mm") == [type_record]
        assert repository.type_occurrence_summary(type_record.ifc_global_id) == (
            2,
            ("Level 1", "Level 2"),
        )
        assert list(repository.iter_records()) == [level_1, level_2]


def test_repository_orders_type_records_and_denies_unreliable_lookup(tmp_path: Path) -> None:
    SQLiteIndexRepository = _api()["SQLiteIndexRepository"]
    database = tmp_path / "types.sqlite"
    second = _type_record("2BBBBBBBBBBBBBBBBBBBBB")
    first = _type_record("1AAAAAAAAAAAAAAAAAAAAA")
    unreliable = _type_record(
        "0CCCCCCCCCCCCCCCCCCCCC", record_id="diagnostic:type:42", reliable=False
    )

    with SQLiteIndexRepository.create(database, _metadata()) as repository:
        repository.put_type_record(second)
        repository.put_type_record(unreliable)
        repository.put_type_record(first)
        repository.publish()

    with SQLiteIndexRepository.open(database) as repository:
        assert [record.record_id for record in repository.iter_type_records()] == [
            unreliable.record_id,
            first.record_id,
            second.record_id,
        ]
        assert repository.get_type_by_global_id(unreliable.ifc_global_id) is None


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


def test_open_rejects_stale_v01_index_with_exact_failure_code(tmp_path: Path) -> None:
    api = _api()
    database = tmp_path / "stale.sqlite"
    with api["SQLiteIndexRepository"].create(
        database,
        _metadata(index_schema_version="text2ifc/ifc-index/0.1"),
    ) as repository:
        repository.put_record(_record())
        repository.publish()

    with pytest.raises(api["IndexStoreError"]) as caught:
        api["SQLiteIndexRepository"].open(
            database,
            expected_index_schema_version=api["INDEX_SCHEMA_VERSION"],
        )
    assert caught.value.code == "INDEX_SCHEMA_VERSION_MISMATCH"
