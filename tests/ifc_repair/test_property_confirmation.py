from __future__ import annotations

from pathlib import Path

import pytest

from text2ifc_ifc_repair.property_intent import (
    PropertyConfirmationPreview,
    authorize_custom_property,
    resolve_exact_property_intent,
)
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_ifc_repair.run_models import Clarification, RunStage, RunStoreError
from text2ifc_ifc_repair.run_store import RunStore
from text2ifc_knowledge.registry import load_ifc2x3_registry


REQUEST_HASH = "sha256:" + "a" * 64
MODEL_HASH = "sha256:" + "b" * 64
TARGET_ID = "0TARGETAAAAAAAAAAAAAAAA"


def _source() -> PublicProvenance:
    return PublicProvenance(
        "user_request",
        "request:/properties/0",
        "set Custom_Asset.AssetCode to W-007",
    )


def _preview() -> PropertyConfirmationPreview:
    from text2ifc_ifc_repair.property_intent import ExactPropertyIntent

    intent = ExactPropertyIntent(
        set_name="Custom_Asset",
        property_name="AssetCode",
        value="W-007",
        requested_value_type=None,
        requested_unit=None,
        scope=None,
        source=_source(),
    )
    resolution = resolve_exact_property_intent(
        intent,
        target_ifc_class="IfcWindow",
        existing_facts=(),
        registry=load_ifc2x3_registry(),
    )
    return PropertyConfirmationPreview.create(
        resolution,
        operation_id="window-1",
        target_global_id=TARGET_ID,
        request_hash=REQUEST_HASH,
        model_fingerprint=MODEL_HASH,
        source=intent.source,
    )


def _start_store(tmp_path: Path) -> tuple[RunStore, object]:
    source = tmp_path / "source.ifc"
    source.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
    store = RunStore(tmp_path / "runs")
    state = store.start_run(
        source_path=source,
        request_id="request-property",
        request_text="add custom property",
    )
    for stage in (
        RunStage.SOURCE_VALIDATED,
        RunStage.INDEX_READY,
        RunStage.INTENT_READY,
    ):
        state = store.transition(
            state.run_id,
            to_stage=stage,
            expected_state_version=state.state_version,
            stage_payload={"stage": stage.value},
        )
    return store, state


def test_preview_hash_binds_request_model_target_tuple_value_and_scope() -> None:
    preview = _preview()
    payload = preview.to_dict()
    assert payload["scope"] == "occurrence_direct"
    assert payload["target_global_id"] == TARGET_ID
    assert payload["request_hash"] == REQUEST_HASH
    assert payload["model_fingerprint"] == MODEL_HASH

    for field, changed in (
        ("target_global_id", "0OTHERAAAAAAAAAAAAAAAAA"),
        ("request_hash", "sha256:" + "c" * 64),
        ("model_fingerprint", "sha256:" + "d" * 64),
        ("property_name", "OtherCode"),
        ("value", "W-008"),
        ("scope", "type_owned"),
    ):
        altered = dict(payload)
        altered[field] = changed
        with pytest.raises(ValueError, match="PREVIEW_HASH_MISMATCH"):
            PropertyConfirmationPreview.from_dict(altered)


def test_only_exact_affirmative_hash_bound_answer_authorizes() -> None:
    preview = _preview()
    fact = authorize_custom_property(
        preview,
        answer_kind="confirm_property",
        preview_hash=preview.preview_hash,
        confirmation_ref="run:repair-test/clarify-004",
    )
    assert fact.ownership == "occurrence_direct"
    assert fact.confirmation_hash == preview.preview_hash
    assert fact.classification == "custom_confirmed"

    with pytest.raises(ValueError, match="CONFIRMATION_REQUIRED"):
        authorize_custom_property(
            preview,
            answer_kind="reject_property",
            preview_hash=preview.preview_hash,
            confirmation_ref="run:repair-test/clarify-004",
        )
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        authorize_custom_property(
            preview,
            answer_kind="confirm_property",
            preview_hash="sha256:" + "0" * 64,
            confirmation_ref="run:repair-test/clarify-004",
        )


def test_property_question_preview_and_answer_survive_reload_and_replay_fails(
    tmp_path: Path,
) -> None:
    store, state = _start_store(tmp_path)
    preview = _preview()
    question = Clarification(
        clarification_id="property-confirmation-004",
        run_id=state.run_id,
        state_version=state.state_version + 1,
        operation_id="window-1",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="property_confirmation",
        question="Confirm this exact custom occurrence property?",
        answer_modes=("confirm_property", "reject_property", "cancel"),
        candidates=(),
        property_preview=preview.to_dict(),
    )
    paused = store.transition(
        state.run_id,
        to_stage=RunStage.CLARIFICATION_REQUIRED,
        expected_state_version=state.state_version,
        clarification=question,
        stage_payload={"preview_hash": preview.preview_hash},
    )

    restarted = RunStore(store.root)
    loaded = restarted.load(state.run_id)
    assert loaded.clarification.property_preview["preview_hash"] == preview.preview_hash
    resumed = restarted.continue_with_answer(
        state.run_id,
        clarification_id=question.clarification_id,
        expected_state_version=paused.state_version,
        answer={"kind": "confirm_property", "preview_hash": preview.preview_hash},
    )
    assert resumed.transitions[-1].answer["preview_hash"] == preview.preview_hash

    with pytest.raises(RunStoreError):
        restarted.continue_with_answer(
            state.run_id,
            clarification_id=question.clarification_id,
            expected_state_version=paused.state_version,
            answer={"kind": "confirm_property", "preview_hash": preview.preview_hash},
        )


def test_free_form_yes_and_changed_preview_hash_are_rejected_without_mutation(
    tmp_path: Path,
) -> None:
    store, state = _start_store(tmp_path)
    preview = _preview()
    question = Clarification(
        clarification_id="property-confirmation-004",
        run_id=state.run_id,
        state_version=state.state_version + 1,
        operation_id="window-1",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="property_confirmation",
        question="Confirm?",
        answer_modes=("confirm_property", "reject_property"),
        property_preview=preview.to_dict(),
    )
    paused = store.transition(
        state.run_id,
        to_stage=RunStage.CLARIFICATION_REQUIRED,
        expected_state_version=state.state_version,
        clarification=question,
    )
    for answer in (
        {"kind": "add_detail", "detail": "yes"},
        {"kind": "confirm_property", "preview_hash": "sha256:" + "9" * 64},
        {"kind": "confirm_property"},
    ):
        with pytest.raises(RunStoreError):
            store.continue_with_answer(
                state.run_id,
                clarification_id=question.clarification_id,
                expected_state_version=paused.state_version,
                answer=answer,
            )
        assert store.load(state.run_id) == paused
