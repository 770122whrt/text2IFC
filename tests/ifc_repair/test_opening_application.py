from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.geometry import (
    opening_dimensions_mm,
    opening_position_in_wall_mm,
)
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.operations import create_default_registry


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


def test_opening_only_creates_one_void_and_no_filling(tmp_path: Path) -> None:
    mutation_dir = tmp_path / "mutation"
    mutation = remove_window_and_opening(
        source_path=SOURCE,
        output_dir=mutation_dir,
        wall_global_id=WALL_ID,
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    damaged = mutation_dir / "damaged.ifc"
    request = "Create an empty 915 x 1830 mm wall opening at the stated position."
    evidence = ["request:/text"]
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-opening-only",
        "base_model_fingerprint": "sha256:" + mutation["damaged_sha256"],
        "source_request_hash": "sha256:"
        + hashlib.sha256(request.encode("utf-8")).hexdigest(),
        "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
        "evidence_refs": evidence,
        "preconditions": ["target_exists"],
        "postconditions": ["opening_voids_wall"],
        "operations": [
            {
                "operation_id": "opening-only-1",
                "operation_type": "add_opening_to_wall",
                "target": {"wall_global_id": WALL_ID},
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 3042.5,
                    },
                    "opening": {
                        "width_mm": 915.0,
                        "height_mm": 1830.0,
                        "sill_height_mm": 305.0,
                    },
                },
                "evidence_refs": evidence,
            }
        ],
    }
    output = tmp_path / "opening-only.ifc"
    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )
    assert result["valid"] is True
    assert result["published"] is True
    repaired = ifcopenshell.open(str(output))
    assert len(repaired.by_type("IfcOpeningElement")) == 60
    assert len(repaired.by_type("IfcRelVoidsElement")) == 60
    assert len(repaired.by_type("IfcWindow")) == 41
    assert len(repaired.by_type("IfcDoor")) == 18
    assert len(repaired.by_type("IfcRelFillsElement")) == 59
    assert len(repaired.by_type("IfcRelSpaceBoundary")) == len(
        ifcopenshell.open(str(damaged)).by_type("IfcRelSpaceBoundary")
    )
    created = {
        item["role"]: repaired.by_guid(item["global_id"])
        for item in result["operations"][0]["changes"]["created"]
    }
    opening = created["opening"]
    wall = repaired.by_guid(WALL_ID)
    assert len(opening.VoidsElements) == 1
    assert opening.VoidsElements[0].RelatingBuildingElement == wall
    assert len(opening.HasFillings) == 0
    assert opening_dimensions_mm(opening) == {
        "width": 915.0,
        "depth": 200.0,
        "height": 1830.0,
    }
    assert opening_position_in_wall_mm(opening, wall)["center_offset"] == 3042.5
