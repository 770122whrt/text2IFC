import hashlib
import json
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.compare import evaluate_repair_application
from text2ifc_ifc_repair.geometry import (
    opening_dimensions_mm,
    opening_position_in_wall_mm,
    product_geometry_bounds_in_host_mm,
)
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.projection import (
    project_public_repair_spec,
    render_repair_request,
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
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repair_case(tmp_path: Path) -> tuple[Path, str, dict]:
    case_dir = tmp_path / "case"
    mutation = remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    private_manifest = json.loads(
        (case_dir / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    public_spec = project_public_repair_spec(
        private_manifest, request_id="large-building-window-repair-001"
    )
    request = render_repair_request(public_spec)
    evidence = [
        "spec:/opening",
        "spec:/target/local_reference",
        "context:/candidate_targets/0",
    ]
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-window-repair-001",
        "base_model_fingerprint": "sha256:" + mutation["damaged_sha256"],
        "source_request_hash": "sha256:"
        + hashlib.sha256(request.encode("utf-8")).hexdigest(),
        "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
        "evidence_refs": evidence,
        "preconditions": ["target_exists"],
        "postconditions": ["opening_voids_wall", "window_fills_opening"],
        "operations": [
            {
                "operation_id": "operation-window-001",
                "operation_type": "add_window_with_opening_to_wall",
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
                    "window": {"fit_opening": True},
                },
                "evidence_refs": evidence,
            }
        ],
    }
    return case_dir / "damaged.ifc", request, changeset


def test_window_applicator_builds_centered_ifc2x3_chain_deterministically(
    tmp_path: Path,
) -> None:
    damaged, request, changeset = _repair_case(tmp_path)
    damaged_hash = _sha256(damaged)
    outputs = [tmp_path / "repaired-a.ifc", tmp_path / "repaired-b.ifc"]
    results = [
        apply_changeset(
            damaged_ifc_path=damaged,
            repair_request=request,
            changeset=changeset,
            output_path=output,
            registry=create_default_registry(),
        )
        for output in outputs
    ]

    assert all(result["valid"] and result["published"] for result in results)
    assert _sha256(damaged) == damaged_hash
    assert _sha256(outputs[0]) == _sha256(outputs[1])

    repaired = ifcopenshell.open(str(outputs[0]))
    assert len(repaired.by_type("IfcWindow")) == 42
    assert len(repaired.by_type("IfcOpeningElement")) == 60
    assert len(repaired.by_type("IfcRelFillsElement")) == 60
    assert len(repaired.by_type("IfcRelVoidsElement")) == 60

    changes = results[0]["operations"][0]["changes"]
    created = {item["role"]: repaired.by_guid(item["global_id"]) for item in changes["created"]}
    wall = repaired.by_guid(WALL_ID)
    opening = created["opening"]
    window = created["window"]
    assert opening.VoidsElements[0].RelatingBuildingElement == wall
    assert window.FillsVoids[0].RelatingOpeningElement == opening
    assert window.ObjectPlacement.PlacementRelTo == opening.ObjectPlacement
    assert float(window.OverallWidth) == 915.0
    assert float(window.OverallHeight) == 1830.0
    assert opening_dimensions_mm(opening) == {
        "width": 915.0,
        "depth": 200.0,
        "height": 1830.0,
    }
    position = opening_position_in_wall_mm(opening, wall)
    assert position["center_offset"] == 3042.5
    assert position["sill_height"] == 305.0
    assert position["geometry_bounds_mm"]["x"] == [2585.0, 3500.0]
    assert product_geometry_bounds_in_host_mm(window, wall) == position[
        "geometry_bounds_mm"
    ]
    assert results[0]["postconditions"][0]["valid"] is True

    evaluation = evaluate_repair_application(
        damaged_ifc_path=damaged,
        repaired_ifc_path=outputs[0],
        changeset=changeset,
        application_result=results[0],
        registry=create_default_registry(),
    )
    assert evaluation["l1"]["status"] == "passed"
    assert evaluation["l2"] == {
        "status": "not_evaluable",
        "reason": "Legacy Evaluation 0.1 has no authoritative L2 semantic assurance.",
        "assurance_error_code": "legacy_assurance_unavailable",
    }
    assert evaluation["complete_repair_success"] is False
    assert evaluation["successful_artifact_publishable"] is False
    assert evaluation["common"]["unexpected_changed_ids"] == []
    window_evaluation = evaluation["operations"][0]
    assert window_evaluation["valid"] is True
    assert window_evaluation["metrics"]["center_error_mm"] == 0.0
    assert window_evaluation["metrics"]["orientation_error_degrees"] == 0.0
    assert window_evaluation["metrics"]["restored_void_volume_m3"] == 0.33489
    assert window_evaluation["checks"]["duplicate_chain_absent"] is True
    assert window_evaluation["checks"]["window_geometry_fits_opening"] is True
