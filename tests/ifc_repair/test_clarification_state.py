from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_ifc_repair.run_models import (
    CLARIFICATION_SCHEMA_PATH,
    RESULT_SCHEMA_PATH,
    RUN_STATE_SCHEMA_PATH,
    Clarification,
    ClarificationCandidate,
    RunStage,
    RunStoreCode,
    RunStoreError,
    load_run_schema,
)
from text2ifc_ifc_repair.run_store import RunStore


def _start(tmp_path: Path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "source.ifc"
    source.write_bytes(b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n")
    store = RunStore(tmp_path / "output")
    state = store.start_run(
        source_path=source,
        request_id="request-clarification",
        request_text="把二层窗修好",
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
    return store, source, state


def _candidate(token: str = "candidate-a") -> ClarificationCandidate:
    return ClarificationCandidate(
        token=token,
        public_id="2uY$public",
        ifc_class="IfcWindow",
        name="二层窗",
        storey="二层",
        position="东侧轴网 A/2",
        evidence=("名称匹配", "楼层匹配"),
    )


def _pause(
    store: RunStore,
    state,
    *,
    reason: str = "ambiguous_target",
    modes: tuple[str, ...] = ("select_candidate", "add_detail", "cancel"),
):
    clarification = Clarification(
        clarification_id="clarification-001",
        run_id=state.run_id,
        state_version=state.state_version + 1,
        operation_id="operation-001",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code=reason,
        question="请选择目标，或补充更多定位信息。",
        answer_modes=modes,
        candidates=(_candidate(),),
    )
    return store.transition(
        state.run_id,
        to_stage=RunStage.CLARIFICATION_REQUIRED,
        expected_state_version=state.state_version,
        clarification=clarification,
    )


def test_all_exact_schemas_are_valid_draft_2020_12() -> None:
    for path in (RUN_STATE_SCHEMA_PATH, CLARIFICATION_SCHEMA_PATH, RESULT_SCHEMA_PATH):
        schema = load_run_schema(path)
        Draft202012Validator.check_schema(schema)
        assert schema["$id"].startswith("text2ifc/ifc-repair-")
        assert schema["additionalProperties"] is False


@pytest.mark.parametrize(
    ("reason", "modes"),
    (
        ("ambiguous_target", ("select_candidate", "add_detail", "cancel")),
        ("selector_conflict", ("select_candidate", "add_detail", "cancel")),
        ("missing_required_parameter", ("add_detail", "cancel")),
        ("prototype_selection", ("authorize_prototype", "cancel")),
        ("additional_target_detail", ("add_detail", "cancel")),
    ),
)
def test_one_clarification_contract_covers_every_reason(
    tmp_path: Path, reason: str, modes: tuple[str, ...]
) -> None:
    store, _, state = _start(tmp_path)
    paused = _pause(store, state, reason=reason, modes=modes)
    public = paused.clarification.to_dict()

    Draft202012Validator(load_run_schema(CLARIFICATION_SCHEMA_PATH)).validate(public)
    assert public["run_id"] == state.run_id
    assert public["state_version"] == paused.state_version
    assert public["operation_id"] == "operation-001"
    assert public["answer_schema"]["properties"]["kind"]["enum"] == list(modes)
    assert public["candidates"][0]["evidence"] == ["名称匹配", "楼层匹配"]
    answer_validator = Draft202012Validator(public["answer_schema"])
    if "select_candidate" in modes:
        assert not answer_validator.is_valid({"kind": "select_candidate"})
        assert answer_validator.is_valid(
            {"kind": "select_candidate", "candidate_token": "candidate-a"}
        )


@pytest.mark.parametrize(
    "answer",
    (
        {"kind": "select_candidate", "candidate_token": "not-listed"},
        {"kind": "select_candidate"},
        {"kind": "add_detail", "detail": ""},
        {"kind": "authorize_prototype", "candidate_token": "candidate-a"},
        {"kind": "unexpected"},
        {"kind": "select_candidate", "candidate_token": "candidate-a", "extra": True},
    ),
)
def test_invalid_or_out_of_list_answers_are_rejected_without_mutation(
    tmp_path: Path, answer: dict[str, object]
) -> None:
    store, _, state = _start(tmp_path)
    paused = _pause(store, state)

    with pytest.raises(RunStoreError) as invalid:
        store.continue_with_answer(
            state.run_id,
            clarification_id="clarification-001",
            expected_state_version=paused.state_version,
            answer=answer,
        )

    assert invalid.value.code == RunStoreCode.ANSWER_INVALID.value
    assert store.load(state.run_id) == paused


def test_candidate_detail_prototype_cancel_and_eof_have_typed_outcomes(tmp_path: Path) -> None:
    cases = (
        ({"kind": "select_candidate", "candidate_token": "candidate-a"}, RunStage.INTENT_READY),
        ({"kind": "add_detail", "detail": "靠近 A/2 轴的东侧窗"}, RunStage.INTENT_READY),
        ({"kind": "cancel"}, RunStage.CANCELLED),
        ({"kind": "eof"}, RunStage.CANCELLED),
    )
    for index, (answer, expected_stage) in enumerate(cases):
        case_root = tmp_path / str(index)
        store, _, state = _start(case_root)
        paused = _pause(store, state)
        resumed = store.continue_with_answer(
            state.run_id,
            clarification_id="clarification-001",
            expected_state_version=paused.state_version,
            answer=answer,
        )
        assert resumed.stage is expected_stage
        assert resumed.transitions[-1].answer == answer

    store, _, state = _start(tmp_path / "prototype")
    paused = _pause(
        store,
        state,
        reason="prototype_selection",
        modes=("authorize_prototype", "cancel"),
    )
    authorized = store.continue_with_answer(
        state.run_id,
        clarification_id="clarification-001",
        expected_state_version=paused.state_version,
        answer={
            "kind": "authorize_prototype",
            "candidate_token": "candidate-a",
            "authorized": True,
        },
    )
    assert authorized.stage is RunStage.INTENT_READY


def test_replayed_or_stale_answer_is_rejected_after_process_restart(tmp_path: Path) -> None:
    store, _, state = _start(tmp_path)
    paused = _pause(store, state)
    restarted = RunStore(store.root)
    resumed = restarted.continue_with_answer(
        state.run_id,
        clarification_id="clarification-001",
        expected_state_version=paused.state_version,
        answer={"kind": "select_candidate", "candidate_token": "candidate-a"},
    )

    with pytest.raises(RunStoreError) as replayed:
        restarted.continue_with_answer(
            state.run_id,
            clarification_id="clarification-001",
            expected_state_version=paused.state_version,
            answer={"kind": "select_candidate", "candidate_token": "candidate-a"},
        )
    assert replayed.value.code == RunStoreCode.STATE_CONFLICT.value
    assert restarted.load(state.run_id) == resumed


def test_clarification_result_is_identical_for_all_adapters(tmp_path: Path) -> None:
    store, _, state = _start(tmp_path)
    paused = _pause(store, state)
    result = store.read_result(state.run_id)
    payload = result.to_dict()

    Draft202012Validator(load_run_schema(RESULT_SCHEMA_PATH)).validate(payload)
    assert result.status == "clarification_required"
    assert result.clarification == paused.clarification
    assert payload["clarification"]["clarification_id"] == "clarification-001"
    assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload


def test_question_and_candidates_reject_private_or_oversized_payloads(tmp_path: Path) -> None:
    store, _, state = _start(tmp_path)
    private = Clarification(
        clarification_id="clarification-private",
        run_id=state.run_id,
        state_version=state.state_version + 1,
        operation_id="operation-001",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="ambiguous_target",
        question="private_original_ifc 中的真实答案是什么？",
        answer_modes=("select_candidate",),
        candidates=(_candidate(),),
    )
    with pytest.raises(RunStoreError) as rejected:
        store.transition(
            state.run_id,
            to_stage=RunStage.CLARIFICATION_REQUIRED,
            expected_state_version=state.state_version,
            clarification=private,
        )
    assert rejected.value.code == RunStoreCode.PUBLIC_RECORD_INVALID.value

    oversized = Clarification(
        clarification_id="clarification-large",
        run_id=state.run_id,
        state_version=state.state_version + 1,
        operation_id="operation-001",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="additional_target_detail",
        question="窗" * 20_000,
        answer_modes=("add_detail",),
        candidates=(),
    )
    with pytest.raises(RunStoreError) as bounded:
        store.transition(
            state.run_id,
            to_stage=RunStage.CLARIFICATION_REQUIRED,
            expected_state_version=state.state_version,
            clarification=oversized,
        )
    assert bounded.value.code == RunStoreCode.PUBLIC_RECORD_TOO_LARGE.value
