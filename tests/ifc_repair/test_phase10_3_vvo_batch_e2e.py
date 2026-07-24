from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.benchmark_evaluation import (
    BenchmarkEvaluationInputs,
    ProductionEvaluationInputs,
    evaluate_benchmark,
)
from text2ifc_ifc_repair.mutation import remove_windows_and_openings_batch
from text2ifc_ifc_repair.projection import (
    project_public_batch_repair_spec,
    render_batch_repair_request,
)
from text2ifc_ifc_repair.repair_intent import hash_request


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"
SOURCE_SHA256 = "b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc"
TARGETS = (
    {
        "wall_global_id": "0jltRti3rFigAmdXYhXxuZ",
        "opening_global_id": "2IUEnGd5v4Yfg1ZkLtd0Yb",
        "window_global_id": "2IUEnGd5v4Yfg1ZlPtd0Yb",
    },
    {
        "wall_global_id": "0jltRti3rFigAmdXYhXxqI",
        "opening_global_id": "08xWVL$9z6JRwr3piJHoAz",
        "window_global_id": "08xWVL$9z6JRwr3oWJHoAz",
    },
    {
        "wall_global_id": "2HNE4WMQ1CXebZMaih8Xi_",
        "opening_global_id": "1B$rgWypT66viEf30I1iSa",
        "window_global_id": "1B$rgWypT66viEf2CI1iSa",
    },
    {
        "wall_global_id": "2CsmzAChHF6O6maGXlo6yJ",
        "opening_global_id": "2dYMXn0_5AKRbD_1mUIAqJ",
        "window_global_id": "2dYMXn0_5AKRbD_0yUIAqJ",
    },
    {
        "wall_global_id": "1cbLGwmrv8LAj2u11O6kyr",
        "opening_global_id": "3CUgKOb6T3Vgk4LBnR_Z8F",
        "window_global_id": "3CUgKOb6T3Vgk4LAzR_Z8F",
    },
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stage1_operation(item: dict, request: str) -> dict:
    target = item["target"]
    opening = item["opening"]
    prototype = item["window"]["prototype"]
    excerpt = (
        f"{target['global_id']} {opening['width_mm']}x{opening['height_mm']} "
        f"{prototype['name']}"
    )
    return {
        "operation_id": item["operation_id"],
        "operation_type": item["requested_operation_type"],
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWall"],
            "global_id": target["global_id"],
            "names": [target["description"]],
            "storey_name": item["storey"]["name"],
        },
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": target["local_reference"][
                    "opening_center_offset_mm"
                ],
            },
            "opening": dict(opening),
            "window": {"fit_opening": True},
        },
        "attribute_intents": [],
        "prototype_intent": {
            "reference_kind": "type_name",
            "reference": prototype["name"],
            "source": {
                "source_kind": "user_request",
                "reference": f"request:/operations/{item['operation_id']}/prototype",
                "excerpt": excerpt,
            },
        },
        "provenance": [
            {
                "source_kind": "user_request",
                "reference": f"request:/operations/{item['operation_id']}",
                "excerpt": excerpt,
            }
        ],
    }


def _stage2_operation(item: dict) -> dict:
    operation_id = item["operation_id"]
    target = item["target"]
    return {
        "operation_id": operation_id,
        "operation_type": item["requested_operation_type"],
        "target": {"wall_global_id": target["global_id"]},
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": target["local_reference"][
                    "opening_center_offset_mm"
                ],
            },
            "opening": dict(item["opening"]),
            "window": {"fit_opening": True},
        },
        "evidence_refs": [
            f"resolved:/operations/{operation_id}/context/candidate_targets/0"
        ],
    }


def test_vvo_one_text_one_changeset_repairs_five_windows_atomically(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    remove_windows_and_openings_batch(
        source_path=SOURCE,
        output_dir=fixture,
        targets=TARGETS,
        expected_source_sha256=SOURCE_SHA256,
    )
    private_manifest = json.loads(
        (fixture / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    public_spec = project_public_batch_repair_spec(
        private_manifest,
        request_id="vvo-five-window-offline-001",
    )
    request = render_batch_repair_request(public_spec)
    damaged = fixture / "damaged.ifc"
    damaged_fingerprint = "sha256:" + _sha256(damaged)
    calls = {"stage1": 0, "stage2": 0}
    captured: dict[str, dict] = {}

    class Provider:
        def generate_candidate(self, **kwargs):
            stage = kwargs["state"]["stage"]
            if stage == "ifc_repair_intent":
                calls["stage1"] += 1
                payload = {
                    "schema_version": "text2ifc/ifc-repair-intent-body/0.1",
                    "operations": [
                        _stage1_operation(item, request)
                        for item in public_spec["operations"]
                    ],
                    "provenance": [
                        {
                            "source_kind": "user_request",
                            "reference": "request:/text",
                            "excerpt": request,
                        }
                    ],
                }
            else:
                calls["stage2"] += 1
                operations = [
                    _stage2_operation(item) for item in public_spec["operations"]
                ]
                evidence_refs = [
                    ref
                    for operation in operations
                    for ref in operation["evidence_refs"]
                ]
                payload = {
                    "schema_version": "text2ifc/ifc-repair-changeset/0.1",
                    "changeset_id": "changeset-vvo-five-window-offline-001",
                    "base_model_fingerprint": damaged_fingerprint,
                    "source_request_hash": hash_request(request),
                    "scope": {
                        "target_ids": [
                            item["target"]["global_id"]
                            for item in public_spec["operations"]
                        ],
                        "forbidden_ids": [],
                    },
                    "evidence_refs": evidence_refs,
                    "preconditions": [
                        "target_exists",
                        "opening_interval_available",
                    ],
                    "postconditions": [
                        "opening_voids_wall",
                        "window_fills_opening",
                    ],
                    "operations": operations,
                }
            return ProviderOutput(
                text=json.dumps(payload, ensure_ascii=False),
                metadata={
                    "provider": "offline-deterministic",
                    "model": "phase10.3-five-window-fixture",
                },
            )

    def capture_application(**kwargs):
        captured["application"] = apply_changeset(**kwargs)
        return captured["application"]

    api = RepairAPI(
        tmp_path / "runs",
        provider=Provider(),
        orchestrator_options={"apply_stage": capture_application},
    )
    result = api.start(damaged, request)

    assert calls == {"stage1": 1, "stage2": 1}
    assert result.status == "succeeded"
    assert result.successful_artifact_publishable is True
    assert _sha256(SOURCE) == SOURCE_SHA256
    run_dir = tmp_path / "runs" / result.run_directory
    repaired_path = run_dir / result.artifacts["successful_ifc"]
    repaired = ifcopenshell.open(str(repaired_path))
    assert repaired.schema == "IFC2X3"
    assert len(repaired.by_type("IfcWindow")) == 23
    assert len(captured["application"]["operations"]) == 5

    changeset = json.loads(
        (run_dir / "changeset.json").read_text(encoding="utf-8")
    )
    assert changeset["schema_version"] == "text2ifc/ifc-repair-changeset/0.2"
    assert changeset["binding_status"] == "bound"
    assert len(changeset["operations"]) == 5
    assert [
        operation["operation_id"] for operation in changeset["operations"]
    ] == [item["operation_id"] for item in public_spec["operations"]]

    production = json.loads(
        (run_dir / result.artifacts["evaluation"]).read_text(encoding="utf-8")
    )
    assert len(production["operations"]) == 5
    for operation in production["operations"]:
        levels = {item["level"]: item["status"] for item in operation["levels"]}
        assert levels == {
            "L1": "passed",
            "L2": "passed",
            "L3": "not_required",
        }

    benchmark = evaluate_benchmark(
        BenchmarkEvaluationInputs(
            production=ProductionEvaluationInputs(
                damaged_ifc_path=damaged,
                repaired_ifc_path=repaired_path,
                changeset=changeset,
                application_result=captured["application"],
                registry=api.registry,
            ),
            private_original_ifc_path=SOURCE,
            private_mutation_mapping={
                item["operation_id"]: {
                    "wall": target["wall_global_id"],
                    "opening": target["opening_global_id"],
                    "window": target["window_global_id"],
                }
                for item, target in zip(public_spec["operations"], TARGETS)
            },
        )
    )
    private_report = dict(benchmark.private_report)
    assert len(private_report["operations"]) == 5
    for operation in private_report["operations"]:
        levels = {item["level"]: item["status"] for item in operation["levels"]}
        assert levels["L1"] == "passed"
        assert levels["L2"] == "passed"
        assert levels["L3"] == "not_required"

    provider_artifacts = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in run_dir.rglob("*")
        if path.is_file()
        and path.suffix in {".json", ".jsonl", ".md", ".txt"}
        and "terminal-bundles" not in path.parts
    )
    for target in TARGETS:
        assert target["opening_global_id"] not in provider_artifacts
        assert target["window_global_id"] not in provider_artifacts
    stage2_prompt = next(run_dir.rglob("changeset/attempt-*/rendered-prompt.md"))
    assert stage2_prompt.stat().st_size < 64 * 1024

