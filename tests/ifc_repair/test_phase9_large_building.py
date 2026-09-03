from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.geometry import opening_position_in_wall_mm
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.repair_intent import hash_request
from text2ifc_agent.providers import ProviderOutput


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"


def test_large_building_uses_public_api_and_phase10_closes_l2(tmp_path: Path) -> None:
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
    evidence_ref = "resolved:/operations/operation-1/context/candidate_targets/0"

    class RawProvider:
        def generate_candidate(self, **kwargs):
            stage = kwargs["state"]["stage"]
            if stage == "ifc_repair_intent":
                calls["stage1"] += 1
                response = {
                        "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
                        "operations": [{
                            "operation_id": "operation-1", "operation_type": "add_window_with_opening_to_wall",
                            "routing_intent": {
                                "component_family": "window",
                                    "action": "add_with_opening",
                                    "operation_profile": "window.add-with-opening",
                                    "source": {
                                        "source_kind": "public_capability",
                                        "reference": "capability:/window.add-with-opening",
                                        "excerpt": "window add with opening",
                                    },
                                },
                        "target_query": {"schema_version": "text2ifc/ifc-target-query/0.1", "allowed_ifc_classes": ["IfcWall"], "global_id": str(wall.GlobalId)},
                        "parameters": {
                            "position": {"reference": "wall_local_start", "center_offset_mm": float(position["center_offset"])},
                            "opening": {"width_mm": float(window.OverallWidth), "height_mm": float(window.OverallHeight), "sill_height_mm": float(position["sill_height"])},
                            "window": {"fit_opening": True},
                        },
                            "attribute_intents": [],
                            "property_intents": [],
                            "semantic_bundle_refs": [],
                            "quantity_intents": [],
                            "occurrence_reuse_intent": None,
                        "prototype_intent": {
                            "reference_kind": "type_name",
                            "reference": "M_Fixed:0915 x 1830mm",
                            "source": {
                                "source_kind": "user_request",
                                "reference": "request:/prototype",
                                "excerpt": "M_Fixed:0915 x 1830mm",
                            },
                        },
                            "provenance": [{"source_kind": "user_request", "reference": "request:/text", "excerpt": text}],
                        }],
                        "semantic_bundles": [],
                        "provenance": [{"source_kind": "user_request", "reference": "request:/text", "excerpt": text}],
                }
            else:
                calls["stage2"] += 1
                response = {
            "schema_version": "text2ifc/ifc-repair-changeset/0.1",
            "changeset_id": "changeset-phase9-large-building",
            "base_model_fingerprint": caller_hash,
            "source_request_hash": hash_request(text),
            "scope": {"target_ids": [str(wall.GlobalId)], "forbidden_ids": []},
            "evidence_refs": [evidence_ref],
            "preconditions": ["target_exists", "opening_interval_available"],
            "postconditions": ["opening_voids_wall", "window_fills_opening"],
            "operations": [{
                "operation_id": "operation-1", "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": str(wall.GlobalId)},
                "parameters": {
                    "position": {"reference": "wall_local_start", "center_offset_mm": float(position["center_offset"])},
                    "opening": {"width_mm": float(window.OverallWidth), "height_mm": float(window.OverallHeight), "sill_height_mm": float(position["sill_height"])},
                    "window": {"fit_opening": True},
                },
                "evidence_refs": [evidence_ref],
            }],
                }
            return ProviderOutput(text=json.dumps(response), metadata={"provider": "offline-raw", "model": "raw-offline-model"})

    api = RepairAPI(
        tmp_path / "output",
        provider=RawProvider(),
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
    )

    # The production caller supplies only the damaged IFC and natural text.
    result = api.start(caller_ifc, text)

    assert calls == {"stage1": 1, "stage2": 1}
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert "sha256:" + hashlib.sha256(caller_ifc.read_bytes()).hexdigest() == caller_hash
    assert result.complete_repair_success is True
    assert result.successful_artifact_publishable is True
    assert "successful_ifc" in result.artifacts
    assert "diagnostic_candidate" not in result.artifacts
    run_dir = tmp_path / "output" / result.run_directory
    resolution = json.loads((run_dir / "resolution.json").read_text(encoding="utf-8"))
    prototype_authority = next(
        item
        for item in resolution["operations"][0]["authorized_semantics"]
        if item["kind"] == "user_authorized_prototype"
    )
    assert prototype_authority["global_id"] == "2cXV28XOjE6f6irhu0CO_c"
    assert prototype_authority["authorization"] == "explicit_request_reference"
    evaluation = json.loads((run_dir / result.artifacts["evaluation"]).read_text(encoding="utf-8"))
    assert "PROTOTYPE_TYPE_FACT_CONFLICT" not in json.dumps(evaluation)
    levels = {item["level"]: item["status"] for item in evaluation["operations"][0]["levels"]}
    assert levels["L1"] == "passed"
    assert levels["L2"] == "passed"
    assert levels["L3"] == "not_required"
