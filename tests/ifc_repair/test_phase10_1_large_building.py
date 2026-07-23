from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import pytest

from text2ifc_agent.providers import ProviderOutput
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
from text2ifc_ifc_repair.semantic_facts import (
    EvidenceSourceKind,
    extract_ifc_semantic_facts,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"
OPENING_ID = "2cXV28XOjE6f6irhW0CO4t"
WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"
TYPE_ID = "2cXV28XOjE6f6irhu0CO_c"
TYPE_NAME = "M_Fixed:0915 x 1830mm"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _levels(report: dict) -> dict[str, str]:
    return {
        level["level"]: level["status"]
        for level in report["operations"][0]["levels"]
    }


def _direct_property(element, set_name: str, property_name: str):
    matches = []
    for relation in element.IsDefinedBy:
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        pset = relation.RelatingPropertyDefinition
        if not pset.is_a("IfcPropertySet") or pset.Name != set_name:
            continue
        matches.extend(prop for prop in pset.HasProperties if prop.Name == property_name)
    assert len(matches) == 1
    return matches[0]


def _without_step_ids(value):
    if isinstance(value, dict):
        return {
            key: _without_step_ids(child)
            for key, child in value.items()
            if key != "id"
        }
    if isinstance(value, list):
        return [_without_step_ids(child) for child in value]
    return value


def _same_type_occurrence_ids(model) -> tuple[str, ...]:
    window_type = model.by_guid(TYPE_ID)
    return tuple(sorted(
        str(item.GlobalId)
        for relation in window_type.ObjectTypeOf
        for item in relation.RelatedObjects
        if item.is_a("IfcWindow") and str(item.GlobalId) != WINDOW_ID
    ))


def _same_type_semantic_hash(
    model, occurrence_ids: tuple[str, ...] | None = None
) -> str:
    window_type = model.by_guid(TYPE_ID)
    if occurrence_ids is None:
        occurrence_ids = _same_type_occurrence_ids(model)
    payload = {
        "type": {
            "GlobalId": str(window_type.GlobalId),
            "Name": window_type.Name,
            "Description": window_type.Description,
            "ElementType": getattr(window_type, "ElementType", None),
            "psets": _without_step_ids(
                ifcopenshell.util.element.get_psets(
                    window_type, should_inherit=False, verbose=True
                )
            ),
        },
        "occurrences": {
            global_id: {
                "Name": model.by_guid(global_id).Name,
                "ObjectType": model.by_guid(global_id).ObjectType,
                "Tag": model.by_guid(global_id).Tag,
                "OverallWidth": model.by_guid(global_id).OverallWidth,
                "OverallHeight": model.by_guid(global_id).OverallHeight,
                "psets": _without_step_ids(
                    ifcopenshell.util.element.get_psets(
                        model.by_guid(global_id), should_inherit=True, verbose=True
                    )
                ),
            }
            for global_id in occurrence_ids
        },
    }
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize(
    ("case_id", "set_name", "property_name", "value", "prototype"),
    [
        (
            "exact-standard-occurrence",
            "Pset_WindowCommon",
            "FireRating",
            "EI30",
            {
                "reference_kind": "type_name",
                "reference": TYPE_NAME,
                "source": {
                    "source_kind": "user_request",
                    "reference": "request:/prototype",
                    "excerpt": TYPE_NAME,
                },
            },
        ),
        (
            "custom-property-confirmation",
            "Custom_Asset",
            "AssetCode",
            "W-007",
            None,
        ),
    ],
)
def test_large_building_exact_property_public_pipeline(
    tmp_path: Path,
    case_id: str,
    set_name: str,
    property_name: str,
    value: str,
    prototype: dict | None,
) -> None:
    original = ifcopenshell.open(str(SOURCE))
    original_window = original.by_guid(WINDOW_ID)
    wall = original.by_guid(WALL_ID)
    position = opening_position_in_wall_mm(
        original.by_guid(OPENING_ID),
        wall,
    )
    fixture = tmp_path / case_id / "fixture"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=fixture,
        wall_global_id=WALL_ID,
        opening_global_id=OPENING_ID,
        window_global_id=WINDOW_ID,
        expected_source_sha256=SOURCE_SHA256,
    )
    damaged = fixture / "damaged.ifc"
    damaged_model = ifcopenshell.open(str(damaged))
    same_type_occurrence_ids = _same_type_occurrence_ids(damaged_model)
    same_type_before = _same_type_semantic_hash(
        damaged_model, same_type_occurrence_ids
    )
    request = (
        f"On wall GlobalId {WALL_ID}, add a 915 x 1830 mm window at "
        f"wall_local_start {float(position['center_offset'])} mm with sill "
        f"{float(position['sill_height'])} mm; set {set_name}.{property_name}={value}."
        + (f" Reuse Window Type {TYPE_NAME}." if prototype else "")
    )
    damaged_fingerprint = "sha256:" + _sha(damaged)
    evidence_ref = "resolved:/operations/operation-1/context/candidate_targets/0"
    calls = {"stage1": 0, "stage2": 0}
    captured = {}

    class Provider:
        def generate_candidate(self, **kwargs):
            if kwargs["state"]["stage"] == "ifc_repair_intent":
                calls["stage1"] += 1
                payload = {
                    "schema_version": "text2ifc/ifc-repair-intent-body/0.2",
                    "operations": [
                        {
                            "operation_id": "operation-1",
                            "operation_type": "add_window_with_opening_to_wall",
                            "target_query": {
                                "schema_version": "text2ifc/ifc-target-query/0.1",
                                "allowed_ifc_classes": ["IfcWall"],
                                "global_id": WALL_ID,
                            },
                            "parameters": {
                                "position": {
                                    "reference": "wall_local_start",
                                    "center_offset_mm": float(position["center_offset"]),
                                },
                                "opening": {
                                    "width_mm": float(original_window.OverallWidth),
                                    "height_mm": float(original_window.OverallHeight),
                                    "sill_height_mm": float(position["sill_height"]),
                                },
                                "window": {"fit_opening": True},
                            },
                            "attribute_intents": [],
                            "property_intents": [
                                {
                                    "intent_kind": "pset_property",
                                    "set_name": set_name,
                                    "property_name": property_name,
                                    "value": value,
                                    "requested_value_type": None,
                                    "requested_unit": None,
                                    "scope": None,
                                    "source": {
                                        "source_kind": "user_request",
                                        "reference": "request:/properties/0",
                                        "excerpt": f"{set_name}.{property_name}={value}",
                                    },
                                }
                            ],
                            "prototype_intent": prototype,
                            "provenance": [
                                {
                                    "source_kind": "user_request",
                                    "reference": "request:/text",
                                    "excerpt": request,
                                }
                            ],
                        }
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
                payload = {
                    "schema_version": "text2ifc/ifc-repair-changeset/0.1",
                    "changeset_id": f"changeset-{case_id}",
                    "base_model_fingerprint": damaged_fingerprint,
                    "source_request_hash": hash_request(request),
                    "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
                    "evidence_refs": [evidence_ref],
                    "preconditions": ["target_exists", "opening_interval_available"],
                    "postconditions": ["opening_voids_wall", "window_fills_opening"],
                    "operations": [
                        {
                            "operation_id": "operation-1",
                            "operation_type": "add_window_with_opening_to_wall",
                            "target": {"wall_global_id": WALL_ID},
                            "parameters": {
                                "position": {
                                    "reference": "wall_local_start",
                                    "center_offset_mm": float(position["center_offset"]),
                                },
                                "opening": {
                                    "width_mm": 915.0,
                                    "height_mm": 1830.0,
                                    "sill_height_mm": float(position["sill_height"]),
                                },
                                "window": {"fit_opening": True},
                            },
                            "evidence_refs": [evidence_ref],
                        }
                    ],
                }
            return ProviderOutput(
                text=json.dumps(payload),
                metadata={"provider": "offline-raw", "model": "phase10.1-fixture"},
            )

    def capture_application(**kwargs):
        captured["application"] = apply_changeset(**kwargs)
        return captured["application"]

    api = RepairAPI(
        tmp_path / case_id / "runs",
        provider=Provider(),
        intent_schema_version="text2ifc/ifc-repair-intent/0.2",
        orchestrator_options={"apply_stage": capture_application},
    )
    initial = api.start(damaged, request)
    if prototype is None:
        assert initial.status == "clarification_required"
        assert initial.clarification.reason_code == "property_confirmation"
        preview = initial.clarification.property_preview
        assert preview["value_type"] == "IfcLabel"
        assert preview["scope"] == "occurrence_direct"
        final = api.continue_with_answer(
            initial.run_id,
            {
                "kind": "confirm_property",
                "preview_hash": preview["preview_hash"],
            },
            clarification_id=initial.clarification.clarification_id,
            expected_state_version=initial.state_version,
        )
    else:
        final = initial

    assert calls == {"stage1": 1, "stage2": 1}
    run_dir = tmp_path / case_id / "runs" / final.run_directory
    failure_evidence = dict(final.artifacts)
    if not final.successful_artifact_publishable and "manifest" in final.artifacts:
        manifest_payload = json.loads(
            (run_dir / final.artifacts["manifest"]).read_text(encoding="utf-8")
        )
        failure_evidence["manifest_payload"] = manifest_payload
        evidence_record = next(
            (
                item
                for item in manifest_payload["artifacts"]
                if str(item.get("path", "")).endswith("evidence.json")
            ),
            None,
        )
        if evidence_record is not None:
            failure_evidence["terminal_evidence"] = json.loads(
                (run_dir / evidence_record["path"]).read_text(encoding="utf-8")
            )
    if not final.successful_artifact_publishable:
        terminal = failure_evidence.get("terminal_evidence", failure_evidence)
        evaluation_payload = {}
        if "evaluation" in final.artifacts:
            evaluation_payload = json.loads(
                (run_dir / final.artifacts["evaluation"]).read_text(encoding="utf-8")
            )
        actual_quantity_facts = []
        candidate_key = (
            "successful_ifc"
            if "successful_ifc" in final.artifacts
            else "diagnostic_candidate"
        )
        if candidate_key in final.artifacts and "application" in captured:
            diagnostic_model = ifcopenshell.open(
                str(run_dir / final.artifacts[candidate_key])
            )
            diagnostic_window_id = next(
                item["global_id"]
                for item in captured["application"]["operations"][0]["changes"]["created"]
                if item["role"] == "window"
            )
            diagnostic_policy = api.registry.require_evaluation_policy(
                "add_window_with_opening_to_wall"
            )
            actual_quantity_facts = [
                {
                    "fact_key": fact.fact_key,
                    "value": fact.value,
                    "value_type": fact.value_type,
                    "unit": fact.unit,
                    "inherited": fact.inherited,
                }
                for fact in extract_ifc_semantic_facts(
                    diagnostic_model.by_guid(diagnostic_window_id),
                    policy=diagnostic_policy,
                    source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
                    source_ref="diagnostic",
                    provenance=("diagnostic",),
                )
                if fact.fact_key.startswith("quantity:")
            ]
        def collect_failures(value, path="$"):
            failures = []
            if isinstance(value, dict):
                if value.get("status") in {"failed", "blocked"}:
                    failures.append(
                        {
                            "path": path,
                            "code": value.get("code"),
                            "status": value.get("status"),
                            "reason": value.get("reason"),
                        }
                    )
                for key, child in value.items():
                    failures.extend(collect_failures(child, f"{path}.{key}"))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    failures.extend(collect_failures(child, f"{path}[{index}]"))
            return failures
        application_checks = [
            check
            for check in terminal.get("evidence", {})
            .get("application", {})
            .get("audit", {})
            .get("checks", [])
            if check.get("status") != "passed"
        ]
        production_checks = [
            check
            for check in terminal.get("evidence", {})
            .get("production_evaluation", {})
            .get("operations", [{}])[0]
            .get("checks", [])
            if check.get("status") != "passed"
        ]
        pytest.fail(
            json.dumps(
                {
                    "terminal_status": terminal.get("terminal_status"),
                    "application_checks": application_checks,
                    "production_checks": production_checks,
                    "production_levels": terminal.get("evidence", {})
                    .get("production_evaluation", {})
                    .get("operations", [{}])[0]
                    .get("levels", []),
                    "failures": collect_failures(terminal),
                    "evaluation_failures": collect_failures(evaluation_payload),
                    "evaluation": evaluation_payload,
                    "actual_quantity_facts": actual_quantity_facts,
                },
                ensure_ascii=False,
            )
        )
    repaired_path = run_dir / final.artifacts["successful_ifc"]
    repaired = ifcopenshell.open(str(repaired_path))
    application = captured["application"]
    new_window_id = next(
        item["global_id"]
        for item in application["operations"][0]["changes"]["created"]
        if item["role"] == "window"
    )
    new_window = repaired.by_guid(new_window_id)
    prop = _direct_property(new_window, set_name, property_name)
    assert prop.NominalValue.is_a() == "IfcLabel"
    assert prop.NominalValue.wrappedValue == value
    bound_type_ids = {
        str(rel.RelatingType.GlobalId)
        for rel in new_window.IsDefinedBy
        if rel.is_a("IfcRelDefinesByType")
    }
    if prototype:
        assert bound_type_ids == {TYPE_ID}
    else:
        assert TYPE_ID not in bound_type_ids
        assert len(bound_type_ids) == 1
        assert repaired.by_guid(next(iter(bound_type_ids))).Name.startswith(
            "Text2IFC generated window type"
        )
    report = json.loads(
        (run_dir / final.artifacts["evaluation"]).read_text(encoding="utf-8")
    )
    assert _levels(report) == {
        "L1": "passed",
        "L2": "passed",
        "L3": "not_required",
    }
    assert (
        _same_type_semantic_hash(repaired, same_type_occurrence_ids)
        == same_type_before
    )
    changeset = json.loads((run_dir / "changeset.json").read_text(encoding="utf-8"))
    benchmark = evaluate_benchmark(
        BenchmarkEvaluationInputs(
            production=ProductionEvaluationInputs(
                damaged_ifc_path=damaged,
                repaired_ifc_path=repaired_path,
                changeset=changeset,
                application_result=application,
                registry=api.registry,
            ),
            private_original_ifc_path=SOURCE,
            private_mutation_mapping={
                "operation-1": {
                    "wall": WALL_ID,
                    "opening": OPENING_ID,
                    "window": WINDOW_ID,
                }
            },
        )
    )
    private_levels = _levels(dict(benchmark.private_report))
    assert private_levels["L1"] == "passed"
    assert private_levels["L3"] == "not_required"
    assert private_levels["L2"] == ("passed" if prototype else "failed")
    assert _sha(damaged) == damaged_fingerprint.removeprefix("sha256:")
    assert _sha(SOURCE) == SOURCE_SHA256
