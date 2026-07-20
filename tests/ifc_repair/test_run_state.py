from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from text2ifc_ifc_repair.run_models import (
    Clarification,
    ClarificationCandidate,
    RunStage,
    RunStoreCode,
    RunStoreError,
)
from text2ifc_ifc_repair.run_store import RunStore


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "source.ifc"
    path.write_bytes(b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n")
    return path


@pytest.fixture
def store(tmp_path: Path) -> RunStore:
    return RunStore(tmp_path / "output")


def _start(store: RunStore, source: Path, *, run_id: str | None = None):
    return store.start_run(
        source_path=source,
        request_id="request-001",
        request_text="修复二层外窗",
        run_id=run_id,
    )


def _clarification(run_id: str, version: int) -> Clarification:
    return Clarification(
        clarification_id="clarify-target-001",
        run_id=run_id,
        state_version=version + 1,
        operation_id="operation-001",
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code="ambiguous_target",
        question="请选择需要修复的窗。",
        answer_modes=("select_candidate", "add_detail", "cancel"),
        candidates=(
            ClarificationCandidate(
                token="candidate-001",
                public_id="3hY$public",
                ifc_class="IfcWindow",
                name="二层外窗 A",
                storey="二层",
                position="东侧",
                evidence=("名称完全匹配", "楼层匹配"),
            ),
            ClarificationCandidate(
                token="candidate-002",
                public_id="2Yx$public",
                ifc_class="IfcWindow",
                name="二层外窗 B",
                storey="二层",
                position="西侧",
                evidence=("名称部分匹配",),
            ),
        ),
    )


def test_start_creates_unique_bound_run_without_modifying_source(
    store: RunStore, source: Path
) -> None:
    before = source.read_bytes()
    first = _start(store, source)
    second = _start(store, source)

    assert first.run_id != second.run_id
    assert first.stage is RunStage.CREATED
    assert first.state_version == 0
    assert first.source.sha256 == _sha256(source)
    assert first.source.size_bytes == len(before)
    assert first.request_hash.startswith("sha256:")
    assert source.read_bytes() == before
    assert (store.runs_root / first.run_id / "state.json").is_file()
    assert (store.runs_root / first.run_id / "transitions" / "000000.json").is_file()


def test_duplicate_run_id_and_output_directory_are_never_overwritten(
    store: RunStore, source: Path
) -> None:
    _start(store, source, run_id="repair-fixed-run")
    state_before = (store.runs_root / "repair-fixed-run" / "state.json").read_bytes()

    with pytest.raises(RunStoreError) as duplicate:
        _start(store, source, run_id="repair-fixed-run")

    assert duplicate.value.code == RunStoreCode.RUN_ALREADY_EXISTS.value
    assert (store.runs_root / "repair-fixed-run" / "state.json").read_bytes() == state_before


@pytest.mark.parametrize(
    "run_id",
    ("../escape", "..\\escape", "nested/run", "nested\\run", ".", ""),
)
def test_run_id_path_traversal_is_rejected(
    store: RunStore, source: Path, run_id: str
) -> None:
    with pytest.raises(RunStoreError) as invalid:
        _start(store, source, run_id=run_id)
    assert invalid.value.code == RunStoreCode.INVALID_RUN_ID.value


def test_symlink_run_escape_is_rejected(store: RunStore, source: Path, tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable")
    outside = tmp_path / "outside"
    outside.mkdir()
    store.runs_root.mkdir(parents=True, exist_ok=True)
    link = store.runs_root / "repair-linked-run"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not permitted")

    with pytest.raises(RunStoreError) as escaped:
        _start(store, source, run_id="repair-linked-run")
    assert escaped.value.code in {
        RunStoreCode.PATH_ESCAPE.value,
        RunStoreCode.RUN_ALREADY_EXISTS.value,
    }
    assert list(outside.iterdir()) == []


def test_transition_history_is_hash_chained_and_monotonic(
    store: RunStore, source: Path
) -> None:
    created = _start(store, source)
    validated = store.transition(
        created.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=0,
        stage_payload={"ifc_schema": "IFC2X3"},
    )
    indexed = store.transition(
        created.run_id,
        to_stage=RunStage.INDEX_READY,
        expected_state_version=1,
        stage_payload={"index_path": "artifacts/index.sqlite"},
    )

    assert [item.transition_id for item in indexed.transitions] == [0, 1, 2]
    assert [item.state_version for item in indexed.transitions] == [0, 1, 2]
    assert indexed.transitions[1].previous_hash == created.transitions[0].record_hash
    assert indexed.transitions[2].previous_hash == validated.transitions[1].record_hash
    assert indexed.transitions[1].stage_hash == validated.transitions[1].stage_hash


def test_invalid_transition_stale_version_and_terminal_mutation_fail_closed(
    store: RunStore, source: Path
) -> None:
    state = _start(store, source)
    with pytest.raises(RunStoreError) as invalid:
        store.transition(
            state.run_id,
            to_stage=RunStage.SUCCEEDED,
            expected_state_version=0,
        )
    assert invalid.value.code == RunStoreCode.INVALID_TRANSITION.value

    validated = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=0,
    )
    with pytest.raises(RunStoreError) as stale:
        store.transition(
            state.run_id,
            to_stage=RunStage.INDEX_READY,
            expected_state_version=0,
        )
    assert stale.value.code == RunStoreCode.STATE_CONFLICT.value

    terminal = store.transition(
        state.run_id,
        to_stage=RunStage.INVALID_INPUT,
        expected_state_version=validated.state_version,
        reason_code="IFC_SCHEMA_UNSUPPORTED",
    )
    with pytest.raises(RunStoreError) as immutable:
        store.transition(
            state.run_id,
            to_stage=RunStage.SOURCE_VALIDATED,
            expected_state_version=terminal.state_version,
        )
    assert immutable.value.code == RunStoreCode.TERMINAL_IMMUTABLE.value


def test_changed_source_and_tampered_transition_are_detected(
    store: RunStore, source: Path
) -> None:
    state = _start(store, source)
    source.write_bytes(source.read_bytes() + b"tampered")
    with pytest.raises(RunStoreError) as changed:
        store.load(state.run_id)
    assert changed.value.code == RunStoreCode.SOURCE_CHANGED.value

    source.write_bytes(b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n")
    transition_path = store.runs_root / state.run_id / "transitions" / "000000.json"
    transition = json.loads(transition_path.read_text(encoding="utf-8"))
    transition["stage_payload"] = {"forged": True}
    transition_path.write_text(json.dumps(transition), encoding="utf-8")
    with pytest.raises(RunStoreError) as tampered:
        store.load(state.run_id)
    assert tampered.value.code == RunStoreCode.TAMPER_DETECTED.value


def test_interrupted_temp_file_is_ignored_on_restart(
    store: RunStore, source: Path
) -> None:
    state = _start(store, source)
    run_dir = store.runs_root / state.run_id
    (run_dir / ".state.json.interrupted.tmp").write_text('{"broken":', encoding="utf-8")
    (run_dir / "transitions" / ".000001.interrupted.tmp").write_text(
        '{"broken":', encoding="utf-8"
    )

    restarted = RunStore(store.root).load(state.run_id)
    assert restarted == state
    assert restarted.state_version == 0


def test_restart_recovers_last_committed_state_after_interrupted_state_replace(
    store: RunStore, source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _start(store, source)
    atomic_write = store._atomic_write_json

    def interrupt_state_replace(
        target: Path, payload: dict[str, object], *, replace_existing: bool = True
    ) -> None:
        if target.name == "state.json" and target.exists():
            raise OSError("simulated interruption before state commit")
        atomic_write(target, payload, replace_existing=replace_existing)

    monkeypatch.setattr(store, "_atomic_write_json", interrupt_state_replace)
    with pytest.raises(OSError, match="simulated interruption"):
        store.transition(
            state.run_id,
            to_stage=RunStage.SOURCE_VALIDATED,
            expected_state_version=state.state_version,
        )

    restarted = RunStore(store.root)
    assert restarted.load(state.run_id) == state
    recovered = restarted.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=state.state_version,
    )
    assert recovered.state_version == 1
    assert recovered.stage is RunStage.SOURCE_VALIDATED
    assert [item.transition_id for item in recovered.transitions] == [0, 1]


def test_artifact_reference_rejects_path_traversal(store: RunStore, source: Path) -> None:
    state = _start(store, source)
    with pytest.raises(RunStoreError) as escaped:
        store.transition(
            state.run_id,
            to_stage=RunStage.INVALID_INPUT,
            expected_state_version=0,
            result_artifacts={"manifest": "../outside.json"},
        )
    assert escaped.value.code == RunStoreCode.PATH_ESCAPE.value
    assert store.load(state.run_id) == state


def test_lock_contention_rejects_racing_mutation_without_history_loss(
    store: RunStore, source: Path
) -> None:
    state = _start(store, source)
    run_dir = store.runs_root / state.run_id
    before = (store.runs_root / state.run_id / "state.json").read_bytes()

    with store._exclusive_lock(run_dir):
        with pytest.raises(RunStoreError) as locked:
            store.transition(
                state.run_id,
                to_stage=RunStage.SOURCE_VALIDATED,
                expected_state_version=0,
            )
    assert locked.value.code == RunStoreCode.LOCKED.value
    assert (store.runs_root / state.run_id / "state.json").read_bytes() == before
    recovered = store.transition(
        state.run_id, to_stage=RunStage.SOURCE_VALIDATED, expected_state_version=0,
    )
    assert recovered.stage is RunStage.SOURCE_VALIDATED


def test_terminal_reads_are_idempotent_and_compact(store: RunStore, source: Path) -> None:
    state = _start(store, source)
    validated = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=0,
    )
    manifest = store.runs_root / state.run_id / "published" / "manifest.json"
    manifest.parent.mkdir()
    manifest.write_text(
        '{"artifacts":[],"schema_version":"text2ifc/ifc-repair-artifact-manifest/0.1"}\n',
        encoding="utf-8",
    )
    terminal = store.transition(
        state.run_id,
        to_stage=RunStage.INVALID_INPUT,
        expected_state_version=validated.state_version,
        reason_code="SOURCE_INVALID",
        result_artifacts={"manifest": "published/manifest.json"},
    )

    first = store.read_result(state.run_id)
    second = RunStore(store.root).read_result(state.run_id)
    assert first == second
    assert first.state_version == terminal.state_version
    assert first.status == RunStage.INVALID_INPUT.value
    assert first.artifacts == {"manifest": "published/manifest.json"}
    encoded = json.dumps(first.to_dict(), ensure_ascii=False)
    assert len(encoded.encode("utf-8")) <= 16 * 1024
    assert "ISO-10303-21" not in encoded
    assert "evaluation" not in first.to_dict()


def test_stage_artifact_hash_is_verified_on_every_resume(store: RunStore, source: Path) -> None:
    state = _start(store, source)
    stage = store.prepare_stage_directory(state.run_id, "index")
    artifact = stage / "targets.sqlite"
    artifact.write_bytes(b"immutable-index")
    committed = store.transition(
        state.run_id, to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=state.state_version,
        stage_payload={"index": store.artifact_binding(
            state.run_id, "index/targets.sqlite", "text2ifc/ifc-index/0.1"
        )},
    )
    assert store.load(state.run_id) == committed
    artifact.write_bytes(b"tampered-index")
    with pytest.raises(RunStoreError) as tampered:
        store.load(state.run_id)
    assert tampered.value.code == RunStoreCode.TAMPER_DETECTED.value


def test_terminal_manifest_and_referenced_content_are_verified(store: RunStore, source: Path) -> None:
    state = _start(store, source)
    published = store.runs_root / state.run_id / "published"
    published.mkdir()
    evaluation = published / "evaluation.json"
    evaluation.write_text('{"status":"failed"}\n', encoding="utf-8")
    digest = hashlib.sha256(evaluation.read_bytes()).hexdigest()
    manifest = published / "manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": "text2ifc/ifc-repair-artifact-manifest/0.1",
        "artifacts": [{"path": "published/evaluation.json", "sha256": digest}],
    }), encoding="utf-8")
    store.transition(
        state.run_id, to_stage=RunStage.INVALID_INPUT,
        expected_state_version=state.state_version,
        stage_payload={"manifest": store.artifact_binding(
            state.run_id, "published/manifest.json", "text2ifc/ifc-repair-artifact-manifest/0.1"
        )},
        result_artifacts={"manifest": "published/manifest.json", "evaluation": "published/evaluation.json"},
    )
    assert store.read_result(state.run_id).status == "invalid_input"
    evaluation.write_text('{"status":"passed"}\n', encoding="utf-8")
    with pytest.raises(RunStoreError) as tampered:
        store.read_result(state.run_id)
    assert tampered.value.code == RunStoreCode.TAMPER_DETECTED.value


def test_stage_directory_rejects_real_reparse_or_symlink_without_privilege_skip(
    store: RunStore, source: Path, tmp_path: Path,
) -> None:
    state = _start(store, source)
    run_dir = store.runs_root / state.run_id
    outside = tmp_path / "outside"
    outside.mkdir()
    stage = run_dir / "index"
    if os.name == "nt":
        created = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(stage), str(outside)],
            capture_output=True, text=True, check=False,
        )
        assert created.returncode == 0, created.stderr
    else:
        stage.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RunStoreError) as escaped:
        store.prepare_stage_directory(state.run_id, "index")
    assert escaped.value.code == RunStoreCode.PATH_ESCAPE.value


def test_completed_stage_hash_is_not_replaced_or_rerun_after_clarification(
    store: RunStore, source: Path
) -> None:
    state = _start(store, source)
    validated = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=0,
        stage_payload={"fingerprint": _sha256(source)},
    )
    indexed = store.transition(
        state.run_id,
        to_stage=RunStage.INDEX_READY,
        expected_state_version=1,
        stage_payload={"index": "artifacts/index.sqlite"},
    )
    intent = store.transition(
        state.run_id,
        to_stage=RunStage.INTENT_READY,
        expected_state_version=2,
        stage_payload={"intent_hash": "sha256:" + "1" * 64},
    )
    paused = store.transition(
        state.run_id,
        to_stage=RunStage.CLARIFICATION_REQUIRED,
        expected_state_version=3,
        clarification=_clarification(state.run_id, 3),
    )
    before = {item.to_stage.value: item.stage_hash for item in paused.transitions[:4]}

    resumed = store.continue_with_answer(
        state.run_id,
        clarification_id="clarify-target-001",
        expected_state_version=paused.state_version,
        answer={"kind": "select_candidate", "candidate_token": "candidate-001"},
    )

    after = {item.to_stage.value: item.stage_hash for item in resumed.transitions[:4]}
    assert before == after
    assert resumed.stage is RunStage.INTENT_READY
    assert resumed.state_version == paused.state_version + 1
    assert len(resumed.transitions) == len(paused.transitions) + 1
