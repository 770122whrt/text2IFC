from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import ifcopenshell
import pytest

from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.repair_intent import RepairIntent, fingerprint_text, hash_request
from text2ifc_ifc_repair.run_models import RunStage, RunStoreCode, RunStoreError


def _source(path: Path, *, name: str = "North wall") -> str:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcProject", GlobalId="0000000000000000000001", Name="Fixture")
    wall_id = "0000000000000000000002"
    model.create_entity("IfcWall", GlobalId=wall_id, Name=name)
    model.write(str(path))
    return wall_id


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _intent(
    request_id: str, text: str, names: list[str], registry, count: int = 1,
    prototype: dict[str, object] | None = None,
) -> RepairIntent:
    operations = []
    for index in range(count):
        operations.append({
            "operation_id": f"operation-{index + 1}",
            "operation_type": "add_window_with_opening_to_wall",
            "target_query": {
                "schema_version": "text2ifc/ifc-target-query/0.1",
                "allowed_ifc_classes": ["IfcWall"],
                "names": names,
            },
            "parameters": {
                "position": {"reference": "wall_local_start", "center_offset_mm": 1000.0 + index},
                "opening": {"width_mm": 900.0, "height_mm": 1800.0, "sill_height_mm": 300.0},
                "window": {"fit_opening": True},
            },
            "attribute_intents": [],
            "prototype_intent": prototype,
            "provenance": [{"source_kind": "user_request", "reference": "request:/text", "excerpt": text}],
        })
    return RepairIntent.from_dict({
        "schema_version": "text2ifc/ifc-repair-intent/0.1",
        "request_id": request_id,
        "source_request_hash": hash_request(text),
        "model_fingerprint": fingerprint_text("offline-fake-provider"),
        "prompt_fingerprint": "sha256:" + "1" * 64,
        "operations": operations,
        "provenance": [{"source_kind": "user_request", "reference": "request:/text", "excerpt": text}],
    }, registry=registry)


def _evaluation(publishable: bool) -> dict[str, object]:
    status = "passed" if publishable else "failed"
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1",
        "status": status,
        "reason": "offline fixture",
        "complete_repair_success": publishable,
        "successful_artifact_publishable": publishable,
        "diagnostic_artifact_retained": not publishable,
        "application": {"check_id": "application.valid", "status": "passed", "reason": "fixture"},
        "preservation": {"check_id": "preservation.valid", "status": "passed", "reason": "fixture"},
        "operations": [],
    }


def _api(
    tmp_path: Path, *, operation_count: int, apply_ok: bool, publishable: bool,
    calls: dict[str, int], target_names: list[str] | None = None,
    prototype: dict[str, object] | None = None,
) -> RepairAPI:
    def intent_stage(**kwargs):
        calls["stage1"] += 1
        return {"valid": True, "intent": _intent(
            kwargs["request_id"], kwargs["repair_request"], target_names or ["North wall"],
            kwargs["registry"], operation_count, prototype,
        )}

    def changeset_stage(**kwargs):
        calls["stage2"] += 1
        operations = [
            {"operation_id": item.operation_id, "operation_type": item.operation_type}
            for item in kwargs["resolved_operations"]
        ]
        return {"valid": True, "changeset": {"base_model_fingerprint": kwargs["resolved_operations"][0].context["model_constraints"]["source_ifc_sha256"], "operations": operations}}

    def apply_stage(**kwargs):
        calls["apply"] += 1
        if not apply_ok:
            return {"valid": False, "published": False, "audit": {"valid": False, "operation_audits": [{"operation_id": "operation-1", "valid": True}, {"operation_id": "operation-2", "valid": False}]}, "operations": [], "output": None}
        target = Path(kwargs["output_path"])
        shutil.copyfile(kwargs["damaged_ifc_path"], target)
        ids = [f"operation-{index + 1}" for index in range(operation_count)]
        return {"valid": True, "published": True, "audit": {"valid": True, "operation_audits": [{"operation_id": item, "valid": True} for item in ids]}, "operations": [{"operation_id": item} for item in ids], "output": {"path": str(target), "sha256": _sha(target).removeprefix("sha256:")}}

    def evaluate(_inputs):
        calls["evaluation"] += 1
        return _evaluation(publishable)

    evidence = SimpleNamespace(
        expected_facts_by_operation={f"operation-{index + 1}": () for index in range(operation_count)},
        applicability_by_operation={f"operation-{index + 1}": {} for index in range(operation_count)},
        conflicts=(),
    )
    return RepairAPI(
        tmp_path / "output",
        provider=object(),
        intent_stage=intent_stage,
        changeset_stage=changeset_stage,
        orchestrator_options={"apply_stage": apply_stage, "evaluation_stage": evaluate, "evidence_builder": lambda **_: evidence},
    )


def test_caller_ifc_and_text_reach_publishable_success_with_exact_call_counts(tmp_path: Path) -> None:
    source = tmp_path / "caller.ifc"
    _source(source)
    before = _sha(source)
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}

    result = _api(tmp_path, operation_count=1, apply_ok=True, publishable=True, calls=calls).start(source, "在 North wall 上修复一扇窗")

    assert calls == {"stage1": 1, "stage2": 1, "apply": 1, "evaluation": 1}
    assert _sha(source) == before
    assert result.status == "succeeded" and result.successful_artifact_publishable is True
    assert "successful_ifc" in result.artifacts
    run_dir = tmp_path / "output" / result.run_directory
    assert (run_dir / result.artifacts["successful_ifc"]).is_file()
    assert (run_dir / result.artifacts["manifest"]).is_file()


def test_multi_operation_failure_rolls_back_without_evaluation_or_success_path(tmp_path: Path) -> None:
    source = tmp_path / "caller.ifc"
    _source(source)
    before = _sha(source)
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}

    result = _api(tmp_path, operation_count=2, apply_ok=False, publishable=False, calls=calls).start(source, "在 North wall 上执行两个修复操作")

    assert calls == {"stage1": 1, "stage2": 1, "apply": 1, "evaluation": 0}
    assert _sha(source) == before
    assert result.status == "audit_failed"
    assert result.successful_artifact_publishable is False
    assert "successful_ifc" not in result.artifacts


def test_ambiguous_candidate_resume_validates_before_bound_state_commit(tmp_path: Path) -> None:
    source = tmp_path / "ambiguous.ifc"
    first_id = _source(source, name="same wall")
    model = ifcopenshell.open(str(source))
    model.create_entity("IfcWall", GlobalId="0000000000000000000003", Name="same wall")
    model.write(str(source))
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}
    api = _api(
        tmp_path, operation_count=1, apply_ok=True, publishable=True,
        calls=calls, target_names=["same wall"],
    )
    pending = api.start(source, "repair same wall")
    assert pending.status == "clarification_required"
    assert pending.clarification is not None
    clarification = pending.clarification
    selected = next(item for item in clarification.candidates if item.public_id == first_id)

    with pytest.raises(Exception):
        api.continue_with_answer(
            pending.run_id, {"kind": "select_candidate", "candidate_token": selected.token},
            clarification_id="stale-clarification", expected_state_version=pending.state_version,
        )
    assert api.store.load(pending.run_id).state_version == pending.state_version

    result = api.continue_with_answer(
        pending.run_id, {"kind": "select_candidate", "candidate_token": selected.token},
        clarification_id=clarification.clarification_id,
        expected_state_version=clarification.state_version,
    )
    assert result.status == "succeeded"
    run_dir = tmp_path / "output" / result.run_directory
    state = api.store.load(pending.run_id)
    context_ref = next(
        transition.stage_payload["api_context"]["path"]
        for transition in reversed(state.transitions)
        if "api_context" in transition.stage_payload
    )
    context = json.loads((run_dir / context_ref).read_text(encoding="utf-8"))
    query = context["intent"]["operations"][0]["target_query"]
    assert query["global_id"] == first_id
    assert "names" not in query and "exact_global_ids" not in query


def test_add_detail_can_span_two_real_api_clarification_rounds(tmp_path: Path) -> None:
    source = tmp_path / "ambiguous-detail.ifc"
    selected_id = _source(source, name="same wall")
    model = ifcopenshell.open(str(source))
    model.create_entity("IfcWall", GlobalId="0000000000000000000003", Name="same wall")
    model.write(str(source))
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}
    api = _api(
        tmp_path,
        operation_count=1,
        apply_ok=True,
        publishable=True,
        calls=calls,
        target_names=["same wall"],
    )

    def intent_stage(**kwargs):
        calls["stage1"] += 1
        intent = _intent(
            kwargs["request_id"],
            kwargs["repair_request"],
            ["same wall"],
            kwargs["registry"],
        )
        if calls["stage1"] >= 3:
            document = intent.to_dict()
            document["operations"][0]["target_query"].pop("names", None)
            document["operations"][0]["target_query"]["global_id"] = selected_id
            intent = RepairIntent.from_dict(document, registry=kwargs["registry"])
        return {"valid": True, "intent": intent}

    api._intent_stage = intent_stage
    first = api.start(source, "repair same wall")
    assert first.status == "clarification_required" and first.clarification is not None
    second = api.continue_with_answer(
        first.run_id,
        {"kind": "add_detail", "detail": "east side"},
        clarification_id=first.clarification.clarification_id,
        expected_state_version=first.state_version,
    )
    assert second.status == "clarification_required" and second.clarification is not None
    result = api.continue_with_answer(
        second.run_id,
        {"kind": "add_detail", "detail": "GlobalId is " + selected_id},
        clarification_id=second.clarification.clarification_id,
        expected_state_version=second.state_version,
    )

    assert result.status == "succeeded"
    assert calls["stage1"] == 3
    state = api.store.load(result.run_id)
    resume_bindings = [
        transition.stage_payload["intent"]
        for transition in state.transitions
        if "intent" in transition.stage_payload
        and str(transition.stage_payload["intent"]["path"]).startswith("intent/resume-")
    ]
    assert len(resume_bindings) == 2


def test_concurrent_clarification_attempt_cannot_overwrite_winner_bindings(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ambiguous-race.ifc"
    selected_id = _source(source, name="same wall")
    model = ifcopenshell.open(str(source))
    model.create_entity("IfcWall", GlobalId="0000000000000000000003", Name="same wall")
    model.write(str(source))
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}
    api = _api(
        tmp_path,
        operation_count=1,
        apply_ok=True,
        publishable=True,
        calls=calls,
        target_names=["same wall"],
    )
    call_lock = threading.Lock()

    def intent_stage(**kwargs):
        with call_lock:
            calls["stage1"] += 1
            call_number = calls["stage1"]
        intent = _intent(
            kwargs["request_id"], kwargs["repair_request"], ["same wall"], kwargs["registry"]
        )
        if call_number > 1:
            document = intent.to_dict()
            document["operations"][0]["target_query"].pop("names", None)
            document["operations"][0]["target_query"]["global_id"] = selected_id
            intent = RepairIntent.from_dict(document, registry=kwargs["registry"])
        return {"valid": True, "intent": intent}

    api._intent_stage = intent_stage
    pending = api.start(source, "repair same wall")
    assert pending.clarification is not None
    original_prepare = api.store.prepare_stage_directory

    def retrying_prepare(*args, **kwargs):
        for _ in range(100):
            try:
                return original_prepare(*args, **kwargs)
            except RunStoreError as error:
                if error.code != RunStoreCode.LOCKED.value:
                    raise
                time.sleep(0.01)
        raise AssertionError("stage preparation did not become available")

    api.store.prepare_stage_directory = retrying_prepare
    original_continue = api.store.continue_with_answer
    at_compare_and_swap = threading.Barrier(2)

    def synchronized_continue(*args, **kwargs):
        at_compare_and_swap.wait(timeout=10)
        return original_continue(*args, **kwargs)

    api.store.continue_with_answer = synchronized_continue

    def resume(detail: str):
        return api.continue_with_answer(
            pending.run_id,
            {"kind": "add_detail", "detail": detail},
            clarification_id=pending.clarification.clarification_id,
            expected_state_version=pending.state_version,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(resume, "east side"), pool.submit(resume, "west side")]
        outcomes = []
        failures = []
        for future in futures:
            try:
                outcomes.append(future.result(timeout=30))
            except Exception as error:
                failures.append(error)

    assert len(outcomes) == 1 and outcomes[0].status == "succeeded", "\n".join(
        "".join(traceback.format_exception(error)) for error in failures
    )
    assert len(failures) == 1
    state = api.store.load(pending.run_id)
    assert state.stage is not RunStage.CLARIFICATION_REQUIRED
    run_dir = api.store.runs_root / pending.run_id
    bound_contexts = [
        transition.stage_payload["api_context"]["path"]
        for transition in state.transitions
        if "api_context" in transition.stage_payload
    ]
    assert len(bound_contexts) == len(set(bound_contexts))
    assert all((run_dir / path).is_file() for path in bound_contexts)


def test_public_api_reaches_explicit_prototype_authorization(tmp_path: Path) -> None:
    source = tmp_path / "prototype.ifc"
    _source(source)
    model = ifcopenshell.open(str(source))
    prototype_wall = model.create_entity(
        "IfcWall", GlobalId="0000000000000000000003", Name="Prototype wall"
    )
    prototype_type = model.create_entity(
        "IfcWallType",
        GlobalId="0000000000000000000004",
        Name="Prototype wall type",
        PredefinedType="NOTDEFINED",
    )
    model.create_entity(
        "IfcRelDefinesByType",
        GlobalId="0000000000000000000005",
        RelatedObjects=[prototype_wall],
        RelatingType=prototype_type,
    )
    model.write(str(source))
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}
    prototype = {
        "reference_kind": "selection_required", "reference": "choose a prototype",
        "source": {"source_kind": "user_request", "reference": "request:/prototype", "excerpt": "use that wall"},
    }
    api = _api(
        tmp_path, operation_count=1, apply_ok=True, publishable=True,
        calls=calls, prototype=prototype,
    )
    pending = api.start(source, "repair North wall using a prototype")
    assert pending.status == "clarification_required"
    clarification = pending.clarification
    assert clarification is not None
    assert clarification.reason_code == "prototype_selection"
    assert clarification.answer_modes == ("authorize_prototype", "cancel")
    assert len(clarification.candidates) == 1
    assert clarification.candidates[0].public_id == str(prototype_type.GlobalId)
    assert clarification.candidates[0].candidate_kind == "type"
    assert clarification.candidates[0].occurrence_count == 1
    assert clarification.candidates[0].storeys == ()

    result = api.continue_with_answer(
        pending.run_id,
        {"kind": "authorize_prototype", "candidate_token": clarification.candidates[0].token, "authorized": True},
        clarification_id=clarification.clarification_id,
        expected_state_version=clarification.state_version,
    )
    assert result.status == "succeeded"
    state = api.store.load(pending.run_id)
    assert any(
        transition.answer is not None and transition.answer["kind"] == "authorize_prototype"
        for transition in state.transitions
    )
    assert calls["stage2"] == 1


def test_early_invalid_input_publishes_evaluation_and_hash_bound_manifest(tmp_path: Path) -> None:
    source = tmp_path / "invalid.ifc"
    ifcopenshell.file(schema="IFC4").write(str(source))
    api = RepairAPI(tmp_path / "output", provider=object())
    result = api.start(source, "repair invalid source")
    assert result.status == "invalid_input"
    assert {"manifest", "evaluation", "evidence"}.issubset(result.artifacts)
    run_dir = tmp_path / "output" / result.run_directory
    evaluation = json.loads((run_dir / result.artifacts["evaluation"]).read_text(encoding="utf-8"))
    assert evaluation["schema_version"] == "text2ifc/ifc-repair-evaluation-public/0.2"
    assert evaluation["successful_artifact_publishable"] is False
    assert api.read_result(result.run_id) == result


def test_public_api_cannot_disable_durable_terminal_publication(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="DURABLE_PUBLICATION_CANNOT_BE_DISABLED"):
        RepairAPI(
            tmp_path / "output",
            provider=object(),
            orchestrator_options={"defer_publication": False},
        )
