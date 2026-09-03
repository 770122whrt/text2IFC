from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.compare import compare_ifc_models
from text2ifc_ifc_repair.mutation import remove_window_and_opening


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
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"


def _damaged(tmp_path: Path) -> Path:
    case_dir = tmp_path / "case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    return case_dir / "damaged.ifc"


def test_common_comparator_accepts_semantically_identical_rewrite(
    tmp_path: Path,
) -> None:
    before = _damaged(tmp_path)
    after = tmp_path / "rewritten.ifc"
    ifcopenshell.open(str(before)).write(str(after))

    report = compare_ifc_models(before, after, allowed_changed_ids=[])

    assert report["complete_preservation_success"] is True
    assert report["schema_preserved"] is True
    assert report["added_ids"] == []
    assert report["removed_ids"] == []
    assert report["modified_ids"] == []
    assert report["unexpected_changed_ids"] == []


def test_common_comparator_detects_unexpected_wall_drift(tmp_path: Path) -> None:
    before = _damaged(tmp_path)
    after = tmp_path / "modified.ifc"
    model = ifcopenshell.open(str(before))
    model.by_guid(WALL_ID).Name = "unexpected rename"
    model.write(str(after))

    report = compare_ifc_models(before, after, allowed_changed_ids=[])

    assert report["complete_preservation_success"] is False
    assert report["modified_ids"] == [WALL_ID]
    assert report["unexpected_changed_ids"] == [WALL_ID]
    assert report["drift"][WALL_ID]["before"]["name"] == (
        "Basic Wall:Outside wall:346660"
    )
    assert report["drift"][WALL_ID]["after"]["name"] == "unexpected rename"
