from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.ifc_repair import validate_success_cases as proof_validator
from text2ifc_ifc_repair.run_models import (
    Clarification,
    ClarificationCandidate,
    RunStage,
    RunStoreCode,
    RunStoreError,
)
from text2ifc_ifc_repair.run_store import RunStore


H3_REQUEST = "将 Level 2 中 819 mm × 759 mm 类型的窗设置为外窗。"
H3_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "dataset/external/ifc-bench/projects/duplex/arc.ifc"
)
H3_SELECTED = "IfcWindow:1hOSvn6df7F8_7GcBWlS2V"
H3_OFFERED = (
    "IfcWindow:1hOSvn6df7F8_7GcBWlS1M",
    H3_SELECTED,
    "IfcWindow:1hOSvn6df7F8_7GcBWlS4Q",
    "IfcWindow:1hOSvn6df7F8_7GcBWlSga",
    "IfcWindow:1hOSvn6df7F8_7GcBWlSnC",
)


def _initial_intent(*, request_hash: str) -> dict[str, Any]:
    source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": H3_REQUEST,
    }
    return {
        "schema_version": "text2ifc/ifc-repair-intent/0.8",
        "request_id": "r1-H3",
        "source_request_hash": request_hash,
        "model_fingerprint": "sha256:" + "2" * 64,
        "prompt_fingerprint": "sha256:" + "3" * 64,
        "operations": [
            {
                "operation_id": "h3-window-property",
                "operation_type": "set_occurrence_properties",
                "routing_intent": {
                    "component_family": "window",
                    "action": "set_properties",
                    "operation_profile": "occurrence.set-properties",
                    "source": source,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcWindow"],
                    "names": ["819mm x 759mm"],
                    "storey_name": "Level 2",
                    "max_candidates": 5,
                    "winner_margin": 10,
                },
                "parameters": {},
                "attribute_intents": [],
                "property_intents": [
                    {
                        "intent_kind": "natural_language_property",
                        "property_phrase": "外窗",
                        "raw_value": True,
                        "raw_unit": None,
                        "scope": "occurrence_direct",
                        "source": source,
                    }
                ],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": None,
                "provenance": [source],
            }
        ],
        "unsupported_requests": [],
        "semantic_bundles": [],
        "provenance": [source],
    }


def _hash_valid_h3_state(
    tmp_path: Path,
    *,
    offered_identities: tuple[str, ...] = H3_OFFERED,
    selected_identity: str = H3_SELECTED,
    complete: bool = True,
):
    store = RunStore(tmp_path / "runtime")
    state = store.start_run(
        source_path=H3_SOURCE,
        request_id="r1-H3",
        request_text=H3_REQUEST,
        run_id="repair-r1-h3-final-authority",
    )
    intent = _initial_intent(request_hash=state.request_hash)
    run_root = store.runs_root / state.run_id
    intent_dir = run_root / "intent"
    intent_dir.mkdir()
    intent_path = intent_dir / "repair-intent.json"
    intent_path.write_text(
        json.dumps(intent, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    state = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=state.state_version,
        stage_payload={},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.INDEX_READY,
        expected_state_version=state.state_version,
        stage_payload={},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.INTENT_READY,
        expected_state_version=state.state_version,
        stage_payload={
            "intent": store.artifact_binding(
                state.run_id,
                "intent/repair-intent.json",
                "text2ifc/ifc-repair-intent/0.8",
            )
        },
    )

    candidates = tuple(
        ClarificationCandidate(
            token=f"candidate:{index}",
            public_id=identity.split(":", 1)[1],
            ifc_class=identity.split(":", 1)[0],
            name=f"Level 2 window {index}",
            storey="Level 2",
            position=None,
            evidence=("frozen H3 target replay fixture",),
        )
        for index, identity in enumerate(reversed(offered_identities), start=1)
    )
    selected_token = next(
        candidate.token
        for candidate in candidates
        if f"{candidate.ifc_class}:{candidate.public_id}" == selected_identity
    )
    clarification = Clarification(
        clarification_id="clarify-h3-target",
        run_id=state.run_id,
        state_version=state.state_version + 1,
        operation_id="h3-window-property",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="ambiguous_target",
        question="请选择需要设置为外窗的目标窗。",
        answer_modes=("select_candidate", "add_detail", "cancel"),
        candidates=candidates,
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.CLARIFICATION_REQUIRED,
        expected_state_version=state.state_version,
        clarification=clarification,
        reason_code="ambiguous_target",
        stage_payload={},
    )
    if not complete:
        return store, store.load(state.run_id), intent, clarification
    state = store.continue_with_answer(
        state.run_id,
        clarification_id=clarification.clarification_id,
        expected_state_version=state.state_version,
        answer={"kind": "select_candidate", "candidate_token": selected_token},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.TARGETS_RESOLVED,
        expected_state_version=state.state_version,
        stage_payload={},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.CHANGESET_READY,
        expected_state_version=state.state_version,
        stage_payload={},
    )
    store.transition(
        state.run_id,
        to_stage=RunStage.SUCCEEDED,
        expected_state_version=state.state_version,
        stage_payload={},
    )
    return store, store.load(state.run_id), intent, clarification


def test_h3_final_authority_projects_stable_selection_and_replays_exact_target(
    tmp_path: Path,
) -> None:
    _, state, initial_intent, _ = _hash_valid_h3_state(tmp_path)
    frozen_initial = deepcopy(initial_intent)

    replay = proof_validator._audit_r1_h3_final_target_resolution_replay(
        source_ifc_path=H3_SOURCE,
        initial_intent=initial_intent,
        state=state,
        expected_selected_identity=H3_SELECTED,
        scratch_root=tmp_path / "target-replay",
    )

    assert replay["status"] == "resolved"
    assert replay["resolved_identity"] == H3_SELECTED
    assert replay["projected_intent"]["operations"][0]["target_query"] == {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWindow"],
        "max_candidates": 5,
        "winner_margin": 10,
        "global_id": H3_SELECTED.split(":", 1)[1],
    }
    assert initial_intent == frozen_initial


def test_h3_final_authority_rejects_a_forged_stable_identity(
    tmp_path: Path,
) -> None:
    forged = H3_OFFERED[0]
    _, state, initial_intent, _ = _hash_valid_h3_state(
        tmp_path,
        selected_identity=forged,
    )

    with pytest.raises(ValueError, match="proof.h3.selected_identity"):
        proof_validator._audit_r1_h3_final_target_resolution_replay(
            source_ifc_path=H3_SOURCE,
            initial_intent=initial_intent,
            state=state,
            expected_selected_identity=H3_SELECTED,
            scratch_root=tmp_path / "target-replay",
        )


def test_h3_hash_valid_state_rejects_a_non_offered_candidate_token(
    tmp_path: Path,
) -> None:
    store, state, _, clarification = _hash_valid_h3_state(
        tmp_path,
        complete=False,
    )

    with pytest.raises(RunStoreError) as rejected:
        store.continue_with_answer(
            state.run_id,
            clarification_id=clarification.clarification_id,
            expected_state_version=state.state_version,
            answer={
                "kind": "select_candidate",
                "candidate_token": "candidate:not-offered",
            },
        )

    assert rejected.value.code == RunStoreCode.ANSWER_INVALID.value
