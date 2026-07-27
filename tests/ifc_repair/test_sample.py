from pathlib import Path

from text2ifc_ifc_repair.sample import (
    inspect_sample,
    inspect_sample_capabilities,
    inspect_target_chain,
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


def test_large_building_source_identity_and_counts_are_frozen() -> None:
    inventory = inspect_sample(SOURCE)

    assert inventory == {
        "schema": "IFC2X3",
        "size_bytes": 1_292_595,
        "sha256": "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725",
        "counts": {
            "IfcProject": 1,
            "IfcSite": 1,
            "IfcBuilding": 1,
            "IfcBuildingStorey": 2,
            "IfcSpace": 8,
            "IfcWall": 18,
            "IfcOpeningElement": 60,
            "IfcWindow": 42,
            "IfcDoor": 18,
            "IfcRelFillsElement": 60,
            "IfcRelVoidsElement": 60,
        },
    }


def test_target_chain_and_wall_local_start_are_frozen() -> None:
    target = inspect_target_chain(
        SOURCE,
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )

    assert target["wall"] == {
        "ifc_class": "IfcWallStandardCase",
        "step_id": 1105,
        "global_id": "1F6umJ5H50aeL3A1As_wTm",
        "name": "Basic Wall:Outside wall:346660",
        "storey": "Level 1",
        "geometry_capability": "straight_wall",
        "axis_start_mm": [0.0, 0.0, 0.0],
        "axis_end_mm": [8200.0, 0.0, 0.0],
        "length_mm": 8200.0,
        "local_reference": "wall_local_start",
    }
    assert target["opening"] == {
        "ifc_class": "IfcOpeningElement",
        "step_id": 35174,
        "global_id": "2cXV28XOjE6f6irhW0CO4t",
        "wall_local_origin_mm": [3500.0, 100.0, 305.0],
        "wall_local_geometry_bounds_mm": {
            "x": [2585.0, 3500.0],
            "y": [-100.0, 100.0],
            "z": [305.0, 2135.0],
        },
        "geometric_center_offset_mm": 3042.5,
        "sill_height_mm": 305.0,
    }
    assert target["window"] == {
        "ifc_class": "IfcWindow",
        "step_id": 13695,
        "global_id": "2cXV28XOjE6f6irgi0CO4t",
        "name": "M_Fixed:0915 x 1830mm:354395",
        "width_mm": 915.0,
        "height_mm": 1830.0,
    }
    assert target["relationships"] == {
        "fills_step_id": 35191,
        "voids_step_id": 35179,
    }


def test_large_building_has_only_supported_straight_walls() -> None:
    capabilities = inspect_sample_capabilities(SOURCE)

    assert capabilities == {
        "straight_wall_count": 18,
        "unsupported_wall_count": 0,
        "valid_window_opening_wall_chain_count": 42,
    }
