from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import pytest

from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.run_models import RunStoreError

from tests.ifc_repair.test_property_resolution_api import (
    _api,
    _confirmed,
    _runtime,
    _source,
)


class _SimulatedProcessDeath(BaseException):
    pass


def _restart(api: RepairAPI, *, runtime: Any | None = None) -> RepairAPI:
    return RepairAPI(
        api.store.root,
        provider=api.provider,
        registry=api.registry,
        intent_stage=api._intent_stage,
        index_stage=api._index_stage,
        changeset_stage=api._changeset_stage,
        orchestrator_factory=api._orchestrator_factory,
        orchestrator_options=api._orchestrator_options,
        intent_schema_version=api._intent_schema_version,
        property_knowledge_runtime=(
            api._property_knowledge_runtime if runtime is None else runtime
        ),
        property_resolution_stage=api._property_resolution_stage,
    )


def _crash_after_checkpoint(
    api: RepairAPI,
    checkpoint: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transition = api.store.transition

    def crash_after_commit(*args: Any, **kwargs: Any):
        committed = transition(*args, **kwargs)
        payload = kwargs.get("stage_payload")
        property_payload = (
            payload.get("property_resolution")
            if isinstance(payload, Mapping)
            else None
        )
        if (
            isinstance(property_payload, Mapping)
            and property_payload.get("checkpoint") == checkpoint
        ):
            raise _SimulatedProcessDeath(checkpoint)
        return committed

    monkeypatch.setattr(api.store, "transition", crash_after_commit)


@pytest.mark.parametrize(
    ("checkpoint", "expected_before_restart"),
    [
        ("candidates", {"vector": 1, "property_resolution": 0}),
        ("decision", {"vector": 1, "property_resolution": 1}),
        ("admissibility", {"vector": 1, "property_resolution": 1}),
    ],
)
def test_restart_reuses_every_committed_property_boundary_without_repeat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    checkpoint: str,
    expected_before_restart: dict[str, int],
) -> None:
    source = tmp_path / f"source-{checkpoint}.ifc"
    _source(source)
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[_confirmed()],
    )
    _crash_after_checkpoint(api, checkpoint, monkeypatch)
    run_id = f"repair-recovery-{checkpoint}"

    with pytest.raises(_SimulatedProcessDeath, match=checkpoint):
        api.start(
            source,
            "Set the selected beam load bearing to true.",
            run_id=run_id,
        )

    assert events.count("vector") == expected_before_restart["vector"]
    assert events.count("property_resolution") == expected_before_restart[
        "property_resolution"
    ]
    state = api.store.load(run_id)
    assert state.stage.value == "intent_ready"
    claim_root = (
        api.store.runs_root
        / run_id
        / "property-resolution"
        / "operation-001"
        / "claim-001"
    )
    committed_bytes = {
        name: (claim_root / name).read_bytes()
        for name in (
            "query.json",
            "candidate-set.json",
            "decision-result-provider.json",
        )
        if (claim_root / name).is_file()
    }

    restarted = _restart(api)
    result = restarted.resume(run_id)

    assert result.status == "succeeded"
    assert events.count("vector") == 1
    assert events.count("property_resolution") == 1
    assert events.count("stage2") == 1
    assert len(provider.calls) == 1
    assert {
        name: (claim_root / name).read_bytes()
        for name in committed_bytes
    } == committed_bytes


def test_restart_rejects_changed_runtime_versions_before_provider_or_stage2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source-version.ifc"
    _source(source)
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[_confirmed()],
    )
    _crash_after_checkpoint(api, "candidates", monkeypatch)
    run_id = "repair-recovery-version"
    with pytest.raises(_SimulatedProcessDeath):
        api.start(
            source,
            "Set the selected beam load bearing to true.",
            run_id=run_id,
        )

    changed = _runtime(events)
    changed.health = replace(
        changed.health,
        embedding_model_version="fixture-semantic/changed",
    )
    restarted = _restart(api, runtime=changed)
    result = restarted.resume(run_id)

    assert result.status == "provider_failed"
    assert result.reason_code == "PROPERTY_RUNTIME_VERSION_CHANGED"
    assert provider.calls == []
    assert "stage2" not in events


def test_restart_rejects_changed_policy_before_provider_or_stage2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source-policy.ifc"
    _source(source)
    api, events, provider = _api(
        tmp_path,
        kind="natural",
        decisions=[_confirmed()],
    )
    _crash_after_checkpoint(api, "candidates", monkeypatch)
    run_id = "repair-recovery-policy"
    with pytest.raises(_SimulatedProcessDeath):
        api.start(
            source,
            "Set the selected beam load bearing to true.",
            run_id=run_id,
        )

    changed = _runtime(events)
    changed.policy["minimum_retrieval_score"] = 0.6
    result = _restart(api, runtime=changed).resume(run_id)

    assert result.status == "provider_failed"
    assert result.reason_code == "PROPERTY_POLICY_CHANGED"
    assert provider.calls == []
    assert "stage2" not in events


def test_property_clarification_state_version_cancel_and_duplicate_are_bound(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-cancel.ifc"
    _source(source)
    first_id = "candidate:1:ifc2x3:Pset_BeamCommon.LoadBearing"
    second_id = "candidate:2:ifc2x3:Pset_BeamCommon.IsExternal"
    api, events, _provider = _api(
        tmp_path,
        kind="natural",
        decisions=[
            {
                "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                "decision": "clarification_required",
                "selected_candidate_id": None,
                "conflicting_candidate_ids": [first_id, second_id],
                "clarification_question": "Which property?",
            }
        ],
    )
    pending = api.start(source, "Set the selected beam property.")
    assert pending.clarification is not None

    with pytest.raises(RunStoreError):
        api.continue_with_answer(
            pending.run_id,
            {"kind": "cancel"},
            clarification_id=pending.clarification.clarification_id,
            expected_state_version=pending.state_version - 1,
        )

    cancelled = api.continue_with_answer(
        pending.run_id,
        {"kind": "cancel"},
        clarification_id=pending.clarification.clarification_id,
        expected_state_version=pending.state_version,
    )
    assert cancelled.status == "cancelled"
    assert cancelled.successful_artifact_publishable is False
    assert "successful_ifc" not in cancelled.artifacts
    assert "stage2" not in events

    with pytest.raises((RunStoreError, ValueError)):
        api.continue_with_answer(
            pending.run_id,
            {"kind": "cancel"},
            clarification_id=pending.clarification.clarification_id,
            expected_state_version=pending.state_version,
        )


def test_terminal_publication_read_is_idempotent_and_resume_is_rejected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-terminal.ifc"
    _source(source)
    api, events, _provider = _api(
        tmp_path,
        kind="natural",
        decisions=[_confirmed()],
    )
    result = api.start(source, "Set the selected beam load bearing to true.")

    assert api.read_result(result.run_id) == result
    assert _restart(api).read_result(result.run_id) == result
    with pytest.raises(RunStoreError):
        _restart(api).resume(result.run_id)
    assert events.count("stage2") == 1
