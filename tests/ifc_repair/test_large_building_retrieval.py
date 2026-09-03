from __future__ import annotations

from pathlib import Path

from text2ifc_ifc_repair.index_models import AliasFact, ElementRecord, IndexMetadata
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.retrievers import VectorRetriever
from text2ifc_ifc_repair.target_context import build_target_context, canonical_target_context_json
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target


ROOT = Path(__file__).resolve().parents[2]
LARGE_BUILDING = ROOT / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"


def test_large_building_wall_space_and_context_acceptance(tmp_path: Path) -> None:
    database = tmp_path / "large-building.sqlite"
    build_ifc_index(LARGE_BUILDING, database)
    wall_query = TargetQuery(
        allowed_ifc_classes=("IfcWall",),
        names=("Basic Wall:Outside wall:346660",),
        storey_name="Level 1",
        direction="east",
    )
    space_query = TargetQuery(
        allowed_ifc_classes=("IfcSpace",), names=("8",), storey_name="Level 1"
    )
    with SQLiteIndexRepository.open(database) as repository:
        wall_result = resolve_target(repository, wall_query)
        assert wall_result.status == "resolved"
        assert wall_result.resolved_target_id == "ifc:1F6umJ5H50aeL3A1As_wTm"
        space_result = resolve_target(repository, space_query)
        assert space_result.status == "resolved"
        first_context = build_target_context(
            repository, wall_query, wall_result, operation_hints=("add_window",)
        )
        second_context = build_target_context(
            repository, wall_query, wall_result, operation_hints=("add_window",)
        )
    assert canonical_target_context_json(first_context) == canonical_target_context_json(second_context)
    assert first_context["context_budget"]["actual_bytes"] <= 12_000
    assert first_context["model_constraints"]["vector_retrieval"] == "disabled"
    assert VectorRetriever.enabled is False


def test_controlled_duplicate_name_fixture_abstains(tmp_path: Path) -> None:
    database = tmp_path / "ambiguous.sqlite"
    metadata = IndexMetadata("sha256:" + "1" * 64, "IFC2X3", "fixture", 1, "2026-07-19T00:00:00Z")
    records = []
    for marker in ("A", "B"):
        guid = f"0{marker * 21}"
        records.append(
            ElementRecord(
                f"ifc:{guid}", guid, True, "IfcWall", "duplicate wall", None, None,
                None, None, None, "Level 1", None, "straight_wall", {},
                {"editable_target": True}, {},
                (AliasFact("duplicate wall", "duplicate wall", "name", "fixture"),), (), (),
            )
        )
    with SQLiteIndexRepository.create(database, metadata) as repository:
        for record in records:
            repository.put_record(record)
        repository.publish()
    with SQLiteIndexRepository.open(database) as repository:
        result = resolve_target(
            repository,
            TargetQuery(allowed_ifc_classes=("IfcWall",), names=("duplicate wall",)),
        )
    assert result.status == "ambiguous"
    assert result.resolved_target_id is None
