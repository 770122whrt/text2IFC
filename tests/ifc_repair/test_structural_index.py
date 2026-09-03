from __future__ import annotations

from collections import Counter
from pathlib import Path

import ifcopenshell
import pytest

import text2ifc_ifc_repair.index_adapters as index_adapters
from text2ifc_ifc_repair.index_models import INDEX_SCHEMA_VERSION, IndexMetadata
from text2ifc_ifc_repair.index_store import IndexStoreError, SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import EXTRACTOR_VERSION, build_ifc_index


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
VVO = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"


@pytest.mark.parametrize(
    ("source", "occurrence_counts", "type_counts"),
    (
        (D7N, {"IfcBeam": 10, "IfcColumn": 15}, {"IfcBeamType": 1, "IfcColumnType": 15}),
        (VVO, {"IfcBeam": 6, "IfcColumn": 5}, {"IfcBeamType": 3, "IfcColumnType": 2}),
    ),
)
def test_real_structural_inventory_and_types_round_trip_separately(
    tmp_path: Path,
    source: Path,
    occurrence_counts: dict[str, int],
    type_counts: dict[str, int],
) -> None:
    database = tmp_path / f"{source.stem}.sqlite"
    build_ifc_index(source, database)

    with SQLiteIndexRepository.open(database) as repository:
        records = [
            record
            for record in repository.iter_records()
            if record.ifc_class in occurrence_counts
        ]
        types = [
            record
            for record in repository.iter_type_records()
            if record.ifc_class in type_counts
        ]

        assert Counter(record.ifc_class for record in records) == occurrence_counts
        assert Counter(record.ifc_class for record in types) == type_counts
        assert all(record.identity_reliable for record in records)
        assert all(record.storey_global_id for record in records)
        assert all(record.type_global_id for record in records)
        assert all(record.provenance["source"] == "current_ifc" for record in records)
        assert all(
            record.facets["structural_evidence_authority"] == "diagnostic_only"
            for record in records
        )
        assert all(
            record.geometry_summary["axis_capability"]["status"]
            in {"measured_current_ifc", "unavailable"}
            for record in records
        )
        assert all(
            record.geometry_summary["section_capability"]["status"]
            in {"measured_current_ifc", "unavailable"}
            for record in records
        )
        assert all(
            {"contained_in_storey", "defined_by_type"}
            <= {relationship.kind for relationship in record.relationships}
            for record in records
        )
        assert all(record.provenance["source"] == "current_ifc" for record in types)


def test_structural_adapters_keep_unmeasurable_geometry_diagnostic_only(
    tmp_path: Path,
) -> None:
    assert getattr(index_adapters, "BeamIndexAdapter", None) is not None
    assert getattr(index_adapters, "ColumnIndexAdapter", None) is not None

    source = tmp_path / "unmeasurable-structural.ifc"
    model = ifcopenshell.file(schema="IFC2X3")
    storey = model.create_entity(
        "IfcBuildingStorey",
        GlobalId="0AAAAAAAAAAAAAAAAAAAAA",
        Name="Level 1",
        CompositionType="ELEMENT",
    )
    beam = model.create_entity(
        "IfcBeam", GlobalId="0BBBBBBBBBBBBBBBBBBBBB", Name="Bare Beam"
    )
    column = model.create_entity(
        "IfcColumn", GlobalId="0CCCCCCCCCCCCCCCCCCCCC", Name="Bare Column"
    )
    beam_type = model.create_entity(
        "IfcBeamType",
        GlobalId="0DDDDDDDDDDDDDDDDDDDDD",
        Name="Bare Beam Type",
        PredefinedType="NOTDEFINED",
    )
    column_type = model.create_entity(
        "IfcColumnType",
        GlobalId="0EEEEEEEEEEEEEEEEEEEEE",
        Name="Bare Column Type",
        PredefinedType="NOTDEFINED",
    )
    model.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId="0FFFFFFFFFFFFFFFFFFFFF",
        RelatedElements=[beam, column],
        RelatingStructure=storey,
    )
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId="0GGGGGGGGGGGGGGGGGGGGG",
        RelatedObjects=[beam],
        RelatingType=beam_type,
    )
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId="0HHHHHHHHHHHHHHHHHHHHH",
        RelatedObjects=[column],
        RelatingType=column_type,
    )
    model.write(str(source))

    database = tmp_path / "unmeasurable-structural.sqlite"
    build_ifc_index(source, database)

    with SQLiteIndexRepository.open(database) as repository:
        records = [
            repository.get_by_global_id(beam.GlobalId),
            repository.get_by_global_id(column.GlobalId),
        ]
        assert all(record is not None for record in records)
        assert all(
            record.geometry_capability == "structural_geometry_unmeasurable"
            for record in records
            if record is not None
        )
        assert all(
            record.facets["structural_evidence_authority"] == "diagnostic_only"
            for record in records
            if record is not None
        )
        assert all(
            record.geometry_summary["axis_capability"]["status"] == "unavailable"
            for record in records
            if record is not None
        )
        assert sum(
            diagnostic.code == "INDEX_STRUCTURAL_GEOMETRY_UNAVAILABLE"
            for diagnostic in repository.diagnostics()
        ) == 2


def test_mapped_rectangular_column_axis_is_measured_from_body_extrusion() -> None:
    model = ifcopenshell.open(str(VVO))
    column = model.by_guid("1rsYNObuDC4euALdw6WUK4")

    result = index_adapters.ColumnIndexAdapter().extract(column)
    axis = result.geometry_summary["axis_capability"]
    section = result.geometry_summary["section_capability"]

    assert result.geometry_capability == "measured_structural_member"
    assert axis["status"] == "measured_current_ifc"
    assert axis["provenance"] == (
        "IfcMappedItem/IfcExtrudedAreaSolid/IfcRectangleProfileDef"
    )
    assert axis["storey_global_id"] == "1vTeahUkP60PdWqwCTjeRs"
    assert axis["storey_local_start_mm"] == pytest.approx(
        [-3307.42670197247, -9061.78314004458, 0.0]
    )
    assert axis["storey_local_end_mm"] == pytest.approx(
        [-3307.42670197247, -9061.78314004458, 3712.05999269584]
    )
    assert axis["world_direction"] == pytest.approx([0.0, 0.0, 1.0])
    assert axis["length_mm"] == pytest.approx(3712.05999269584)
    assert section["world_profile_x_direction"] == pytest.approx(
        [0.0, -1.0, 0.0]
    )
    assert section["storey_local_profile_x_direction"] == pytest.approx(
        [0.0, -1.0, 0.0]
    )


def test_mapped_circular_column_remains_outside_rectangular_restoration() -> None:
    model = ifcopenshell.open(str(D7N))
    column = model.by_guid("3dldEzenf9LvnDJYNNzLsH")

    result = index_adapters.ColumnIndexAdapter().extract(column)

    assert result.geometry_capability == "structural_geometry_unmeasurable"
    assert (
        result.geometry_summary["axis_capability"]["status"]
        == "unavailable"
    )
    assert (
        result.geometry_summary["section_capability"]["status"]
        == "unavailable"
    )
    assert (
        result.geometry_summary["section_capability"]["candidate_count"]
        == 0
    )


def test_stale_structural_index_is_rejected_by_default_then_atomically_rebuilt(
    tmp_path: Path,
) -> None:
    database = tmp_path / "structural.sqlite"
    stale_metadata = IndexMetadata(
        source_ifc_sha256="sha256:" + "0" * 64,
        ifc_schema="IFC2X3",
        extractor_version="text2ifc/ifc-indexer/0.4",
        source_size_bytes=1,
        created_at="2026-08-03T00:00:00Z",
        index_schema_version="text2ifc/ifc-index/0.4",
    )
    with SQLiteIndexRepository.create(database, stale_metadata) as repository:
        repository.publish()

    with pytest.raises(IndexStoreError) as captured:
        SQLiteIndexRepository.open(database)
    assert captured.value.code == "INDEX_SCHEMA_VERSION_MISMATCH"

    build_ifc_index(D7N, database)
    with SQLiteIndexRepository.open(database) as repository:
        assert repository.metadata.index_schema_version == INDEX_SCHEMA_VERSION
        assert repository.metadata.extractor_version == EXTRACTOR_VERSION
        counts = Counter(record.ifc_class for record in repository.iter_records())
        assert counts["IfcBeam"] == 10
        assert counts["IfcColumn"] == 15

    assert INDEX_SCHEMA_VERSION == "text2ifc/ifc-index/0.5"
    assert EXTRACTOR_VERSION == "text2ifc/ifc-indexer/0.7"
    assert not list(tmp_path.glob("*.building-*"))
