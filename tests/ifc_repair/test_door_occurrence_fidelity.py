from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.occurrence_fidelity import (
    GENERIC_SCHEMA_VERSION,
    compare_occurrence_snapshots,
    snapshot_ifc_occurrence,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "dataset"
    / "external"
    / "bim-whale-ifc-samples"
    / "LargeBuilding"
    / "IFC"
    / "LargeBuilding.ifc"
)
DOOR_ID = "2cXV28XOjE6f6irgi0COhu"


def test_generic_door_occurrence_snapshot_is_scoped_and_schema_valid() -> None:
    model = ifcopenshell.open(str(SOURCE))
    expected = snapshot_ifc_occurrence(
        model,
        DOOR_ID,
        scope="door_occurrence",
        role="door",
    )

    report = compare_occurrence_snapshots(
        expected=expected,
        actual=expected,
        required_fact_keys=expected.facts,
        schema_version=GENERIC_SCHEMA_VERSION,
    )

    assert report["schema_version"] == GENERIC_SCHEMA_VERSION
    assert report["mapping"]["actual"]["ifc_class"] == "IfcDoor"
    assert report["mapping"]["actual"]["scope"] == "door_occurrence"
    assert report["mapping"]["actual"]["role"] == "door"
    assert report["mapping"]["actual"]["related_opening_global_id"]
    assert report["occurrence_fidelity_success"] is True
    assert report["counts"]["wrong_value"] == 0
