import hashlib
import json
from pathlib import Path

import ifcopenshell
import pytest

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
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_mutation_removes_target_chain_and_preserves_source(tmp_path: Path) -> None:
    output_dir = tmp_path / "case"

    result = remove_window_and_opening(
        source_path=SOURCE,
        output_dir=output_dir,
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )

    assert _sha256(SOURCE) == SOURCE_SHA256
    assert result["valid"] is True
    assert result["artifacts"] == {
        "damaged_ifc": "damaged.ifc",
        "private_manifest": "mutation_manifest.private.json",
        "report": "mutation_report.json",
    }

    damaged = ifcopenshell.open(str(output_dir / "damaged.ifc"))
    assert damaged.schema == "IFC2X3"
    remaining_global_ids = {
        entity.GlobalId for entity in damaged.by_type("IfcRoot")
    }
    assert "2cXV28XOjE6f6irgi0CO4t" not in remaining_global_ids
    assert "2cXV28XOjE6f6irhW0CO4t" not in remaining_global_ids
    assert "1F6umJ5H50aeL3A1As_wTm" in remaining_global_ids
    assert "2cXV28XOjE6f6irgi0CO7d" in remaining_global_ids
    assert len(damaged.by_type("IfcWindow")) == 41
    assert len(damaged.by_type("IfcOpeningElement")) == 59
    assert len(damaged.by_type("IfcRelFillsElement")) == 59
    assert len(damaged.by_type("IfcRelVoidsElement")) == 59
    assert len(damaged.by_type("IfcDoor")) == 18

    private_manifest = json.loads(
        (output_dir / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    assert private_manifest["mutation_type"] == "remove_window_and_opening"
    assert private_manifest["source"]["sha256"] == SOURCE_SHA256
    assert private_manifest["target"]["relationships"] == {
        "fills_step_id": 35191,
        "voids_step_id": 35179,
    }
    assert private_manifest["counts"]["before"]["IfcWindow"] == 42
    assert private_manifest["counts"]["after"]["IfcWindow"] == 41

    report = json.loads(
        (output_dir / "mutation_report.json").read_text(encoding="utf-8")
    )
    assert report["removed_windows"] == [
        {
            "target_id": "window-repair-001",
            "name": "M_Fixed:0915 x 1830mm:354395",
        }
    ]
    assert report["geometry"] == {
        "host_wall_volume_before_m3": pytest.approx(5.64422, abs=1e-5),
        "host_wall_volume_after_m3": pytest.approx(5.97911, abs=1e-5),
        "host_wall_volume_delta_m3": pytest.approx(0.33489, abs=1e-5),
        "expected_closed_void_volume_m3": pytest.approx(0.33489, abs=1e-5),
        "target_region_closed": True,
    }


def test_mutation_is_deterministic_for_the_same_hash_bound_recipe(
    tmp_path: Path,
) -> None:
    results = []
    for name in ("first", "second"):
        results.append(
            remove_window_and_opening(
                source_path=SOURCE,
                output_dir=tmp_path / name,
                wall_global_id="1F6umJ5H50aeL3A1As_wTm",
                opening_global_id="2cXV28XOjE6f6irhW0CO4t",
                window_global_id="2cXV28XOjE6f6irgi0CO4t",
                expected_source_sha256=SOURCE_SHA256,
            )
        )

    assert results[0]["damaged_sha256"] == results[1]["damaged_sha256"]
    assert (tmp_path / "first" / "mutation_report.json").read_bytes() == (
        tmp_path / "second" / "mutation_report.json"
    ).read_bytes()


def test_mutation_rejects_a_stale_source_binding(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="SOURCE_IFC_FINGERPRINT_MISMATCH"):
        remove_window_and_opening(
            source_path=SOURCE,
            output_dir=tmp_path / "case",
            wall_global_id="1F6umJ5H50aeL3A1As_wTm",
            opening_global_id="2cXV28XOjE6f6irhW0CO4t",
            window_global_id="2cXV28XOjE6f6irgi0CO4t",
            expected_source_sha256="0" * 64,
        )

    assert not (tmp_path / "case").exists()
