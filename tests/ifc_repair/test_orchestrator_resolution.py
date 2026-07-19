from __future__ import annotations

import importlib
from dataclasses import dataclass

import pytest


def _api():
    try:
        return importlib.import_module("text2ifc_ifc_repair.orchestrator")
    except ModuleNotFoundError:
        pytest.fail("Phase 9 repair orchestrator is not implemented")


@dataclass(frozen=True)
class _Resolution:
    status: str
    reason_code: str | None = None
    operations: tuple[object, ...] = ()
    candidates: tuple[dict, ...] = ()


@pytest.mark.parametrize(
    "status",
    [
        "not_found",
        "ambiguous",
        "conflict",
        "unsupported",
        "missing_required_parameter",
        "stale_index",
        "context_budget_exceeded",
        "missing_evidence",
    ],
)
def test_every_non_exact_status_makes_zero_stage2_audit_and_apply_calls(tmp_path, status: str) -> None:
    api = _api()
    calls = {"stage2": 0, "audit": 0, "apply": 0}

    def counted(name):
        def call(*args, **kwargs):
            calls[name] += 1
            return {"name": name}
        return call

    orchestrator = api.RepairOrchestrator(
        run_directory=tmp_path,
        resolver=lambda *args, **kwargs: _Resolution(status="clarification_required", reason_code=status),
        changeset_stage=counted("stage2"),
        audit_stage=counted("audit"),
        apply_stage=counted("apply"),
    )
    result = orchestrator.start(intent=object(), repository=object(), expected_source_sha256="sha256:" + "a" * 64)

    assert result.status == "clarification_required"
    assert result.reason_code == status
    assert calls == {"stage2": 0, "audit": 0, "apply": 0}


def test_only_complete_resolution_reaches_stage2_and_stops_before_audit_apply(tmp_path) -> None:
    api = _api()
    calls = {"stage2": 0, "audit": 0, "apply": 0}

    def stage2(*args, **kwargs):
        calls["stage2"] += 1
        return {"schema_version": "text2ifc/ifc-repair-changeset/0.1", "changeset_id": "changeset-1", "operations": []}

    orchestrator = api.RepairOrchestrator(
        run_directory=tmp_path,
        resolver=lambda *args, **kwargs: _Resolution(status="resolved", operations=(object(),)),
        changeset_stage=stage2,
        audit_stage=lambda *args, **kwargs: calls.__setitem__("audit", calls["audit"] + 1),
        apply_stage=lambda *args, **kwargs: calls.__setitem__("apply", calls["apply"] + 1),
    )
    result = orchestrator.start(intent=object(), repository=object(), expected_source_sha256="sha256:" + "a" * 64)

    assert result.status == "changeset_ready"
    assert calls == {"stage2": 1, "audit": 0, "apply": 0}
    assert (tmp_path / "resolution.json").is_file()
    assert (tmp_path / "changeset.json").is_file()


def test_resume_reuses_persisted_intent_and_index_without_repeating_resolution(tmp_path) -> None:
    api = _api()
    calls = {"resolve": 0, "stage2": 0}

    def resolver(*args, **kwargs):
        calls["resolve"] += 1
        return _Resolution(status="clarification_required", reason_code="ambiguous", candidates=({"token": "candidate-a"},))

    orchestrator = api.RepairOrchestrator(
        run_directory=tmp_path,
        resolver=resolver,
        prototype_authorizer=lambda result, **answer: _Resolution(status="resolved", operations=(object(),)),
        changeset_stage=lambda *args, **kwargs: calls.__setitem__("stage2", calls["stage2"] + 1) or {"operations": []},
        audit_stage=lambda *args, **kwargs: pytest.fail("Audit must remain disconnected in Plan 09-03"),
        apply_stage=lambda *args, **kwargs: pytest.fail("Apply must remain disconnected in Plan 09-03"),
    )
    first = orchestrator.start(intent={"immutable": True}, repository=object(), expected_source_sha256="sha256:" + "a" * 64)
    resumed = orchestrator.continue_with_answer({"operation_id": "intent-1", "candidate_token": "candidate-a", "authorized": True})

    assert first.status == "clarification_required"
    assert resumed.status == "changeset_ready"
    assert calls == {"resolve": 1, "stage2": 1}

