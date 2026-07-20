from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import ifcopenshell

from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.geometry import opening_position_in_wall_mm
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.run_models import thaw_json
from tests.ifc_repair.test_phase9_offline_e2e import _intent


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"


def test_large_building_uses_public_api_and_keeps_current_l2_nonpublishable(tmp_path: Path) -> None:
    original = ifcopenshell.open(str(SOURCE))
    window = next(item for item in original.by_type("IfcWindow") if item.FillsVoids and item.FillsVoids[0].RelatingOpeningElement.VoidsElements)
    opening = window.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    position = opening_position_in_wall_mm(opening, wall)
    mutation_dir = tmp_path / "private-benchmark-setup"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=mutation_dir,
        wall_global_id=str(wall.GlobalId),
        opening_global_id=str(opening.GlobalId),
        window_global_id=str(window.GlobalId),
        expected_source_sha256=SOURCE_SHA256,
    )
    caller_ifc = mutation_dir / "damaged.ifc"
    caller_hash = "sha256:" + hashlib.sha256(caller_ifc.read_bytes()).hexdigest()
    text = f"请在 {wall.Name} 上恢复宽 {float(window.OverallWidth)} mm、高 {float(window.OverallHeight)} mm 的外窗"
    calls = {"stage1": 0, "stage2": 0}

    def intent_stage(**kwargs):
        calls["stage1"] += 1
        intent = _intent(kwargs["request_id"], kwargs["repair_request"], [str(wall.Name)], kwargs["registry"])
        document = intent.to_dict()
        parameters = document["operations"][0]["parameters"]
        parameters["position"]["center_offset_mm"] = float(position["center_offset"])
        parameters["opening"] = {
            "width_mm": float(window.OverallWidth),
            "height_mm": float(window.OverallHeight),
            "sill_height_mm": float(position["sill_height"]),
        }
        return {"valid": True, "intent": type(intent).from_dict(document, registry=kwargs["registry"])}

    def changeset_stage(**kwargs):
        calls["stage2"] += 1
        operation = kwargs["resolved_operations"][0]
        evidence = list(operation.evidence_pointers)
        return {"valid": True, "changeset": {
            "schema_version": "text2ifc/ifc-repair-changeset/0.1",
            "changeset_id": "changeset-phase9-large-building",
            "base_model_fingerprint": caller_hash,
            "source_request_hash": kwargs["source_request_hash"],
            "scope": {"target_ids": list(operation.scope_ids), "forbidden_ids": []},
            "evidence_refs": evidence,
            "preconditions": ["target_exists", "opening_interval_available"],
            "postconditions": ["opening_voids_wall", "window_fills_opening"],
            "operations": [{
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "target": {"wall_global_id": operation.target_global_id},
                "parameters": thaw_json(operation.parameters),
                "evidence_refs": evidence,
            }],
        }}

    evidence = SimpleNamespace(
        expected_facts_by_operation={"operation-1": ()},
        applicability_by_operation={"operation-1": {}},
        conflicts=(),
    )
    api = RepairAPI(
        tmp_path / "output",
        provider=object(),
        intent_stage=intent_stage,
        changeset_stage=changeset_stage,
        orchestrator_options={"evidence_builder": lambda **_: evidence},
    )

    # The production caller supplies only the damaged IFC and natural text.
    result = api.start(caller_ifc, text)

    assert calls == {"stage1": 1, "stage2": 1}
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert "sha256:" + hashlib.sha256(caller_ifc.read_bytes()).hexdigest() == caller_hash
    assert result.complete_repair_success is False
    assert result.successful_artifact_publishable is False
    assert "successful_ifc" not in result.artifacts
    assert "diagnostic_candidate" in result.artifacts
    run_dir = tmp_path / "output" / result.run_directory
    evaluation = json.loads((run_dir / result.artifacts["evaluation"]).read_text(encoding="utf-8"))
    levels = {item["level"]: item["status"] for item in evaluation["operations"][0]["levels"]}
    assert levels["L1"] == "passed"
    assert levels["L2"] in {"failed", "partial", "not_evaluable"}
    assert levels["L3"] == "not_required"
