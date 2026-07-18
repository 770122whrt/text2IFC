from __future__ import annotations

from collections import Counter
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.index_store import SQLiteIndexRepository


ROOT = Path(__file__).resolve().parents[2]
LARGE_BUILDING = (
    ROOT
    / "dataset"
    / "external"
    / "bim-whale-ifc-samples"
    / "LargeBuilding"
    / "IFC"
    / "LargeBuilding.ifc"
)


def _api() -> dict[str, object]:
    try:
        from text2ifc_ifc_repair.index_adapters import (
            AdapterResult,
            IndexAdapterRegistry,
            default_index_adapter_registry,
        )
        from text2ifc_ifc_repair.indexer import IndexBuildError, build_ifc_index
    except ModuleNotFoundError:
        pytest.fail("Phase 7 IFC indexer API is not implemented yet")
    return locals()


def test_large_building_indexes_initial_scope_and_source_identity(tmp_path: Path) -> None:
    build_ifc_index = _api()["build_ifc_index"]
    database = tmp_path / "large.sqlite"
    build_ifc_index(LARGE_BUILDING, database)

    with SQLiteIndexRepository.open(database) as repository:
        records = list(repository.iter_records())
        counts = Counter(record.ifc_class for record in records)
        assert sum(counts[name] for name in ("IfcWall", "IfcWallStandardCase")) == 18
        assert counts["IfcDoor"] == 18
        assert counts["IfcWindow"] == 42
        assert counts["IfcSpace"] == 8
        assert repository.metadata.ifc_schema == "IFC2X3"
        assert repository.metadata.source_ifc_sha256.startswith("sha256:")
        assert len(repository.metadata.source_ifc_sha256) == 71


def test_large_building_retains_engineering_relationship_and_property_evidence(
    tmp_path: Path,
) -> None:
    build_ifc_index = _api()["build_ifc_index"]
    database = tmp_path / "large.sqlite"
    build_ifc_index(LARGE_BUILDING, database)

    with SQLiteIndexRepository.open(database) as repository:
        wall = repository.get_by_global_id("1F6umJ5H50aeL3A1As_wTm")
        assert wall is not None
        assert wall.storey_name == "Level 1"
        assert wall.geometry_capability == "straight_wall"
        assert wall.geometry_summary["coordinate_basis"]["reference"] == "wall_local_start"
        assert len(wall.geometry_summary["coordinate_basis"]["axis_direction"]) == 3
        assert wall.facets["editable_target"] is True

        window = repository.get_by_global_id("2cXV28XOjE6f6irgi0CO$D")
        assert window is not None
        relation_kinds = {fact.kind for fact in window.relationships}
        assert {"fills_opening", "hosted_by_wall"} <= relation_kinds
        width = [
            fact
            for fact in window.properties
            if fact.set_name == "Dimensions" and fact.property_name == "Width"
        ]
        assert len(width) == 1
        assert width[0].value == pytest.approx(915.0)
        assert width[0].value_type == "IfcLengthMeasure"

        space = next(record for record in repository.iter_records() if record.ifc_class == "IfcSpace")
        assert space.storey_name is not None
        assert space.facets["editable_target"] is False
        assert any(fact.kind == "decomposes_from" for fact in space.relationships)


def test_duplicate_global_ids_are_diagnostic_and_never_reliable(tmp_path: Path) -> None:
    build_ifc_index = _api()["build_ifc_index"]
    source = tmp_path / "duplicate.ifc"
    model = ifcopenshell.file(schema="IFC2X3")
    global_id = "0AAAAAAAAAAAAAAAAAAAAA"
    model.create_entity("IfcWall", GlobalId=global_id, Name="first")
    model.create_entity("IfcWall", GlobalId=global_id, Name="second")
    model.write(str(source))

    database = tmp_path / "duplicate.sqlite"
    build_ifc_index(source, database)
    with SQLiteIndexRepository.open(database) as repository:
        assert repository.get_by_global_id(global_id) is None
        assert len(list(repository.iter_records())) == 2
        assert all(not record.identity_reliable for record in repository.iter_records())
        assert any(
            diagnostic.code == "DUPLICATE_IFC_GLOBAL_ID"
            for diagnostic in repository.diagnostics()
        )


def test_non_ifc2x3_source_does_not_publish_database(tmp_path: Path) -> None:
    api = _api()
    source = tmp_path / "ifc4.ifc"
    ifcopenshell.file(schema="IFC4").write(str(source))
    database = tmp_path / "ifc4.sqlite"

    with pytest.raises(api["IndexBuildError"]) as captured:
        api["build_ifc_index"](source, database)
    assert captured.value.code == "UNSUPPORTED_IFC_SCHEMA"
    assert not database.exists()


def test_registry_adds_a_new_family_without_changing_common_index_loop(
    tmp_path: Path,
) -> None:
    api = _api()

    class FixtureAdapter:
        ifc_classes = ("IfcBuildingElementProxy",)

        def extract(self, entity: object) -> object:
            return api["AdapterResult"](
                geometry_capability="fixture",
                facets={"fixture": {"registered": True}, "editable_target": False},
            )

    registry = api["default_index_adapter_registry"]()
    registry.register(FixtureAdapter())
    source = tmp_path / "extension.ifc"
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity(
        "IfcBuildingElementProxy",
        GlobalId="0BBBBBBBBBBBBBBBBBBBBB",
        Name="registered extension",
    )
    model.write(str(source))

    database = tmp_path / "extension.sqlite"
    api["build_ifc_index"](source, database, registry=registry)
    with SQLiteIndexRepository.open(database) as repository:
        record = repository.get_by_global_id("0BBBBBBBBBBBBBBBBBBBBB")
        assert record is not None
        assert record.facets["fixture"]["registered"] is True
