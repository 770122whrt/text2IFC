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
from text2ifc_ifc_repair.semantic_authoring import (
    parse_semantic_manifest,
    semantic_manifest_expected_facts,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"
SOURCE_SHA256 = "b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc"
CASE = json.loads(
    (
        ROOT
        / "dataset"
        / "manifests"
        / "ifc-repair-cases"
        / "vvo-five-window-001.private.json"
    ).read_text(encoding="utf-8")
)
CASE_ID = CASE["case_id"]
TARGETS = tuple(CASE["targets"])


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
        "property_intents": [
            {
                "intent_kind": "exact_property",
                "set_name": prop["set_name"],
                "property_name": prop["property_name"],
                "raw_value": prop["value"],
                "raw_unit": prop.get("unit"),
                "requested_value_type": prop["requested_value_type"],
                "scope": "occurrence_direct",
                "source": {
                    "source_kind": "user_request",
                    "reference": (
                        f"request:/operations/{item['operation_id']}/properties/{index}"
                    ),
                    "excerpt": (
                        f"{prop['set_name']}.{prop['property_name']}={prop['value']}"
                    ),
                },
            }
            for index, prop in enumerate(item.get("requested_properties", ()))
        ],
        "semantic_bundle_refs": [],
        "quantity_intents": [
            {
                "scope": quantity.get("scope", "window_occurrence"),
                "set_name": quantity["set_name"],
                "quantity_name": quantity["quantity_name"],
                "value": quantity["value"],
                "value_type": quantity["value_type"],
                "unit": quantity.get("unit"),
                "source": {
                    "source_kind": "user_request",
                    "reference": (
                        f"request:/operations/{item['operation_id']}/quantities/{index}"
                    ),
                    "excerpt": (
                        f"{quantity['set_name']}.{quantity['quantity_name']}="
                        f"{quantity['value']} {quantity.get('unit') or ''}"
                    ).strip(),
                },
            }
            for index, quantity in enumerate(
                item.get("requested_quantities", ())
            )
        ],
        "occurrence_reuse_intent": None,
        "prototype_intent": {
            "reference_kind": (
                "global_id" if prototype.get("global_id") else "type_name"
            ),
            "reference": prototype.get("global_id") or prototype["name"],
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
        request_id=f"{CASE_ID}-offline-001",
    )
    request = render_batch_repair_request(public_spec)
    (tmp_path / "public-spec.json").write_text(
        json.dumps(public_spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (tmp_path / "request.txt").write_text(request, encoding="utf-8")
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
                    "schema_version": "text2ifc/ifc-repair-intent-body/0.4",
                    "operations": [
                        _stage1_operation(item, request)
                        for item in public_spec["operations"]
                    ],
                    "semantic_bundles": [],
                    "provenance": [
                        {
                            "source_kind": "user_request",
                            "reference": "request:/text",
                            "excerpt": request[:2048],
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
                    "changeset_id": f"changeset-{CASE_ID}-offline-001",
                    "base_model_fingerprint": damaged_fingerprint,
                    "source_request_hash": hash_request(request),
                    "scope": {
                        "target_ids": list(
                            dict.fromkeys(
                                item["target"]["global_id"]
                                for item in public_spec["operations"]
                            )
                        ),
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
        intent_schema_version="text2ifc/ifc-repair-intent/0.4",
        orchestrator_options={"apply_stage": capture_application},
    )
    result = api.start(damaged, request)
    confirmation_count = 0
    while result.status == "clarification_required":
        clarification = result.clarification
        assert clarification is not None
        assert clarification.reason_code == "property_confirmation"
        preview = clarification.property_preview
        assert preview is not None
        result = api.continue_with_answer(
            result.run_id,
            {
                "kind": "confirm_property",
                "preview_hash": preview["preview_hash"],
            },
            clarification_id=clarification.clarification_id,
            expected_state_version=result.state_version,
        )
        confirmation_count += 1
        assert confirmation_count <= len(public_spec["operations"])

    assert calls == {"stage1": 1, "stage2": 1}
    assert result.status == "succeeded"
    assert result.successful_artifact_publishable is True
    assert _sha256(SOURCE) == SOURCE_SHA256
    run_dir = tmp_path / "runs" / result.run_directory
    repaired_path = run_dir / result.artifacts["successful_ifc"]
    repaired = ifcopenshell.open(str(repaired_path))
    assert repaired.schema == "IFC2X3"
    source_window_count = len(
        ifcopenshell.open(str(SOURCE)).by_type("IfcWindow")
    )
    assert len(repaired.by_type("IfcWindow")) == source_window_count
    assert len(captured["application"]["operations"]) == 5

    changeset = json.loads(
        (run_dir / "changeset.json").read_text(encoding="utf-8")
    )
    assert changeset["schema_version"] == "text2ifc/ifc-repair-changeset/0.3"
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
                expected_facts_by_operation={
                    operation["operation_id"]: semantic_manifest_expected_facts(
                        parse_semantic_manifest(
                            json.loads(
                                (
                                    run_dir
                                    / "changeset"
                                    / (
                                        "semantic-manifest-"
                                        f"{operation['operation_id']}.json"
                                    )
                                ).read_text(encoding="utf-8")
                            )
                        )
                    )
                    for operation in changeset["operations"]
                },
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
    (tmp_path / "private-ground-truth-evaluation.json").write_text(
        json.dumps(private_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    assert len(private_report["operations"]) == 5
    for operation in private_report["operations"]:
        levels = {item["level"]: item["status"] for item in operation["levels"]}
        assert levels["L1"] == "passed"
        assert levels["L2"] == "passed", operation
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

    invalid_changeset = json.loads(json.dumps(changeset))
    operations_by_wall: dict[str, list[dict]] = {}
    for operation in invalid_changeset["operations"]:
        operations_by_wall.setdefault(
            operation["target"]["wall_global_id"], []
        ).append(operation)
    same_wall = next(
        (items for items in operations_by_wall.values() if len(items) >= 2),
        None,
    )
    if same_wall is not None:
        same_wall[1]["parameters"]["position"]["center_offset_mm"] = (
            same_wall[0]["parameters"]["position"]["center_offset_mm"]
        )
        same_wall[1]["parameters"]["opening"]["sill_height_mm"] = (
            same_wall[0]["parameters"]["opening"]["sill_height_mm"]
        )
        expected_rejection = "BATCH_OPENING_OVERLAP"
    else:
        invalid_changeset["operations"][0]["parameters"]["position"][
            "center_offset_mm"
        ] = 0.0
        expected_rejection = "OPENING_OUTSIDE_WALL_HORIZONTAL"
    rejected_output = tmp_path / "must-not-publish.ifc"
    damaged_before = _sha256(damaged)
    rejected = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=invalid_changeset,
        output_path=rejected_output,
        registry=api.registry,
    )
    assert rejected["valid"] is False
    assert rejected["published"] is False
    assert any(
        issue["code"] == expected_rejection
        for issue in rejected["audit"]["issues"]
    )
    assert not rejected_output.exists()
    assert _sha256(damaged) == damaged_before
