import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.mutation import remove_door


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
OPENING_ID = "2cXV28XOjE6f6irhW0COhu"


@pytest.mark.parametrize("preserve_opening", [False, True])
def test_door_mutation_records_identity_type_and_exact_scope(
    tmp_path: Path,
    preserve_opening: bool,
) -> None:
    output = tmp_path / (
        "preserve-opening" if preserve_opening else "remove-full-chain"
    )
    result = remove_door(
        source_path=SOURCE,
        output_dir=output,
        door_global_id=DOOR_ID,
        preserve_opening=preserve_opening,
    )

    damaged = ifcopenshell.open(str(output / "damaged.ifc"))
    report = json.loads(
        (output / "mutation_report.json").read_text(encoding="utf-8")
    )
    removed = report["removed_doors"][0]
    assert result["valid"] is True
    assert damaged.schema == "IFC2X3"
    with pytest.raises(RuntimeError):
        damaged.by_guid(DOOR_ID)
    try:
        surviving_opening = damaged.by_guid(OPENING_ID)
    except RuntimeError:
        surviving_opening = None
    assert (surviving_opening is not None) is preserve_opening
    assert removed == {
        "global_id": DOOR_ID,
        "name": "M_Single-Flush:Inside Door:353172",
        "type_global_id": "2cXV28XOjE6f6irhu0COgZ",
        "type_name": "M_Single-Flush:Inside Door",
        "operation_type": "SINGLE_SWING_RIGHT",
    }
    assert report["damage_scope"] == {
        "door_removed": True,
        "fill_removed": True,
        "opening_removed": not preserve_opening,
        "void_removed": not preserve_opening,
    }
