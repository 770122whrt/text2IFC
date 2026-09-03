from __future__ import annotations

from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index


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


def test_large_building_openings_are_first_class_measured_targets(
    tmp_path: Path,
) -> None:
    database = tmp_path / "large.sqlite"
    build_ifc_index(LARGE_BUILDING, database)
    with SQLiteIndexRepository.open(database) as repository:
        openings = [
            item
            for item in repository.iter_records()
            if item.ifc_class == "IfcOpeningElement"
        ]
        assert len(openings) == 60
        measured = [
            item
            for item in openings
            if item.geometry_capability == "measured_hosted_opening"
        ]
        assert measured
        opening = measured[0]
        assert opening.identity_reliable
        assert opening.facets["editable_target"] is True
        assert len(opening.facets["host_wall_global_ids"]) == 1
        assert opening.facets["fill_state"] in {"empty", "filled"}
        assert opening.storey_global_id
        assert set(opening.geometry_summary["dimensions_mm"]) == {
            "width",
            "height",
            "depth",
        }
        assert opening.geometry_summary["wall_local_position_mm"][
            "reference"
        ] == "wall_local_start"


def test_empty_opening_and_door_style_formal_facts_round_trip(
    tmp_path: Path,
) -> None:
    model = ifcopenshell.open(str(LARGE_BUILDING))
    opening = min(
        model.by_type("IfcOpeningElement"),
        key=lambda item: str(item.GlobalId),
    )
    for relation in tuple(opening.HasFillings):
        model.remove(relation)
    source = tmp_path / "one-empty-opening.ifc"
    model.write(str(source))
    database = tmp_path / "one-empty-opening.sqlite"
    build_ifc_index(source, database)

    reopened = ifcopenshell.open(str(source))
    direct_styles = {
        str(item.GlobalId): item for item in reopened.by_type("IfcDoorStyle")
    }
    with SQLiteIndexRepository.open(database) as repository:
        record = repository.get_by_global_id(str(opening.GlobalId))
        assert record is not None
        assert record.facets["fill_state"] == "empty"
        assert record.facets["filling_global_ids"] == []
        styles = [
            item
            for item in repository.iter_type_records()
            if item.ifc_class == "IfcDoorStyle" and item.identity_reliable
        ]
        assert styles
        style = styles[0]
        direct = direct_styles[str(style.ifc_global_id)]
        assert style.formal_attributes == {
            "OperationType": str(direct.OperationType),
            "ConstructionType": str(direct.ConstructionType),
            "ParameterTakesPrecedence": bool(
                direct.ParameterTakesPrecedence
            ),
            "Sizeable": bool(direct.Sizeable),
        }
        assert style.name is not None
        assert style.representation_summary[
            "representation_map_count"
        ] == len(direct.RepresentationMaps or ())
        assert style.representation_summary["fingerprint"].startswith("sha256:")


def test_unhosted_opening_is_diagnostic_only(tmp_path: Path) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    opening = model.create_entity(
        "IfcOpeningElement",
        GlobalId="0AAAAAAAAAAAAAAAAAAAAA",
        Name="orphan opening",
    )
    source = tmp_path / "orphan.ifc"
    model.write(str(source))
    database = tmp_path / "orphan.sqlite"
    build_ifc_index(source, database)
    with SQLiteIndexRepository.open(database) as repository:
        record = repository.get_by_global_id(str(opening.GlobalId))
        assert record is not None
        assert record.facets["editable_target"] is False
        assert record.geometry_capability == "opening_topology_invalid"
        assert any(
            item.code == "INDEX_OPENING_HOST_INVALID"
            for item in repository.diagnostics()
        )
