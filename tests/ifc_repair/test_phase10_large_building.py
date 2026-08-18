from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.benchmark_evaluation import (
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    evaluate_benchmark,
)
from text2ifc_ifc_repair.geometry import opening_position_in_wall_mm
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.repair_intent import hash_request
from text2ifc_ifc_repair.semantic_authoring import (
    parse_semantic_manifest,
    semantic_manifest_expected_facts,
)
from text2ifc_agent.providers import ProviderOutput


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"
OPENING_ID = "2cXV28XOjE6f6irhW0CO4t"
WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"
WINDOW_TYPE_NAME = "M_Fixed:0915 x 1830mm"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _levels(report: dict) -> dict[str, str]:
    return {
        level["level"]: level["status"]
        for level in report["operations"][0]["levels"]
    }


def test_large_building_damaged_ifc_plus_text_passes_production_and_private_l2(tmp_path: Path) -> None:
    original = ifcopenshell.open(str(SOURCE))
    window = original.by_guid(WINDOW_ID)
    opening = original.by_guid(OPENING_ID)
    wall = original.by_guid(WALL_ID)
    position = opening_position_in_wall_mm(opening, wall)
    fixture = tmp_path / "private-fixture"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=fixture,
        wall_global_id=WALL_ID,
        opening_global_id=OPENING_ID,
        window_global_id=WINDOW_ID,
        expected_source_sha256=SOURCE_SHA256,
    )
    damaged = fixture / "damaged.ifc"
    request = (
        f"请在墙 {wall.Name}（GlobalId {WALL_ID}）上恢复一扇宽 {float(window.OverallWidth)} mm、"
        f"高 {float(window.OverallHeight)} mm 的窗，窗台高 {float(position['sill_height'])} mm，"
        f"窗中心距 wall_local_start {float(position['center_offset'])} mm；使用现有 Window Type "
        f"{WINDOW_TYPE_NAME}。"
    )
    calls = {"stage1": 0, "stage2": 0}
    captured: dict[str, dict] = {}
    caller_hash = "sha256:" + _sha256(damaged)
    evidence_ref = "resolved:/operations/operation-1/context/candidate_targets/0"

    class Provider:
        def generate_candidate(self, **kwargs):
            stage = kwargs["state"]["stage"]
            if stage == "ifc_repair_intent":
                calls["stage1"] += 1
                payload = {
                        "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
                        "operations": [{
                        "operation_id": "operation-1",
                            "operation_type": "add_window_with_opening_to_wall",
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
                        "target_query": {
                            "schema_version": "text2ifc/ifc-target-query/0.1",
                            "allowed_ifc_classes": ["IfcWall"],
                            "global_id": WALL_ID,
                        },
                        "parameters": {
                            "position": {"reference": "wall_local_start", "center_offset_mm": float(position["center_offset"])},
                            "opening": {
                                "width_mm": float(window.OverallWidth),
                                "height_mm": float(window.OverallHeight),
                                "sill_height_mm": float(position["sill_height"]),
                            },
                            "window": {"fit_opening": True},
                        },
                            "attribute_intents": [],
                            "property_intents": [],
                            "semantic_bundle_refs": [],
                            "quantity_intents": [],
                            "occurrence_reuse_intent": None,
                        "prototype_intent": {
                            "reference_kind": "type_name",
                            "reference": WINDOW_TYPE_NAME,
                            "source": {"source_kind": "user_request", "reference": "request:/prototype", "excerpt": WINDOW_TYPE_NAME},
                        },
                            "provenance": [{"source_kind": "user_request", "reference": "request:/text", "excerpt": request}],
                        }],
                        "semantic_bundles": [],
                        "provenance": [{"source_kind": "user_request", "reference": "request:/text", "excerpt": request}],
                }
            else:
                calls["stage2"] += 1
                payload = {
                    "schema_version": "text2ifc/ifc-repair-changeset/0.1",
                    "changeset_id": "changeset-phase10-large-building",
                    "base_model_fingerprint": caller_hash,
                    "source_request_hash": hash_request(request),
                    "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
                    "evidence_refs": [evidence_ref],
                    "preconditions": ["target_exists", "opening_interval_available"],
                    "postconditions": ["opening_voids_wall", "window_fills_opening"],
                    "operations": [{
                        "operation_id": "operation-1",
                        "operation_type": "add_window_with_opening_to_wall",
                        "target": {"wall_global_id": WALL_ID},
                        "parameters": {
                            "position": {"reference": "wall_local_start", "center_offset_mm": float(position["center_offset"])},
                            "opening": {
                                "width_mm": float(window.OverallWidth),
                                "height_mm": float(window.OverallHeight),
                                "sill_height_mm": float(position["sill_height"]),
                            },
                            "window": {"fit_opening": True},
                        },
                        "evidence_refs": [evidence_ref],
                    }],
                }
            return ProviderOutput(text=json.dumps(payload), metadata={"provider": "offline-raw", "model": "phase10-fixture"})

    def capture_application(**kwargs):
        captured["application"] = apply_changeset(**kwargs)
        return captured["application"]

    api = RepairAPI(
        tmp_path / "runs",
        provider=Provider(),
        intent_schema_version="text2ifc/ifc-repair-intent/0.5",
        orchestrator_options={"apply_stage": capture_application},
    )
    result = api.start(damaged, request)

    assert calls == {"stage1": 1, "stage2": 1}
    assert _sha256(SOURCE) == SOURCE_SHA256
    assert result.complete_repair_success is True
    assert result.successful_artifact_publishable is True
    assert "successful_ifc" in result.artifacts
    run_dir = tmp_path / "runs" / result.run_directory
    repaired = run_dir / result.artifacts["successful_ifc"]
    assert ifcopenshell.open(str(repaired)).schema == "IFC2X3"
    public_report = json.loads((run_dir / result.artifacts["evaluation"]).read_text(encoding="utf-8"))
    assert _levels(public_report) == {"L1": "passed", "L2": "passed", "L3": "not_required"}
    changeset = json.loads((run_dir / "changeset.json").read_text(encoding="utf-8"))
    assert changeset["schema_version"] == "text2ifc/ifc-repair-changeset/0.2"
    assert changeset["binding_status"] == "bound"
    assert changeset["operations"][0]["semantic_assignments"]
    expected_facts = semantic_manifest_expected_facts(
        parse_semantic_manifest(
            json.loads(
                (
                    run_dir
                    / "changeset"
                    / "semantic-manifest-operation-1.json"
                ).read_text(encoding="utf-8")
            )
        )
    )

    benchmark = evaluate_benchmark(
        BenchmarkEvaluationInputs(
            production=ProductionEvaluationInputs(
                damaged_ifc_path=damaged,
                repaired_ifc_path=repaired,
                changeset=changeset,
                application_result=captured["application"],
                registry=api.registry,
                expected_facts_by_operation={"operation-1": expected_facts},
            ),
            private_original_ifc_path=SOURCE,
            private_mutation_mapping={
                "operation-1": {"wall": WALL_ID, "opening": OPENING_ID, "window": WINDOW_ID}
            },
        )
    )
    private_report = dict(benchmark.private_report)
    assert _levels(private_report) == {"L1": "passed", "L2": "passed", "L3": "not_required"}
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in run_dir.rglob("*.json")
    )
    assert OPENING_ID not in public_text
    assert WINDOW_ID not in public_text
