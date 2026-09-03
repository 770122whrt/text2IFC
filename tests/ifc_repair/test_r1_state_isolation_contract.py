from __future__ import annotations

import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from scripts.ifc_repair import validate_success_cases as proof_validator
from tests.ifc_repair.test_beam_application import D7N
from text2ifc_ifc_repair.api import _terminal_failure_evaluation
from text2ifc_ifc_repair.run_artifacts import publish_terminal_artifacts
from text2ifc_ifc_repair.run_models import RunStage
from text2ifc_ifc_repair.run_store import RunStore


H4_REASON_CODE = "STRUCTURAL_ANALYSIS_UNSUPPORTED"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _artifact_entry(run_root: Path, path: Path, role: str) -> dict[str, Any]:
    return {
        "path": path.relative_to(run_root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
        "role": role,
    }


def _validated_h4_state(
    tmp_path: Path,
    *,
    run_id: str = "repair-r1-h4-authoritative",
    evidence_payload: dict[str, Any] | None = None,
    evaluation_payload: dict[str, Any] | None = None,
    extra_terminal_artifact: bool = False,
) -> tuple[RunStore, Any, Path, dict[str, Path]]:
    fixture_root = tmp_path / run_id
    source = fixture_root / "source.ifc"
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(D7N, source)

    store = RunStore(fixture_root / "runtime")
    state = store.start_run(
        source_path=source,
        request_id=f"request-{run_id}",
        request_text="Add a Beam and a structural analysis node atomically.",
        run_id=run_id,
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=state.state_version,
        stage_payload={"ifc_schema": "IFC2X3"},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.INDEX_READY,
        expected_state_version=state.state_version,
        stage_payload={"index": "fixture"},
    )

    run_root = store.runs_root / run_id
    published = publish_terminal_artifacts(
        run_directory=run_root,
        terminal_status=RunStage.UNSUPPORTED.value,
        evaluation=(
            _terminal_failure_evaluation(H4_REASON_CODE)
            if evaluation_payload is None
            else evaluation_payload
        ),
        candidate_ifc_path=None,
        evidence=(
            {"reason_code": H4_REASON_CODE, "stage": state.stage.value}
            if evidence_payload is None
            else evidence_payload
        ),
        promote=False,
    )
    assert published.prepared_root is not None
    if extra_terminal_artifact:
        prepared_root = Path(published.prepared_root)
        extra = prepared_root / "diagnostic" / "unexpected.json"
        _write_json(extra, {"unexpected": True})
        manifest_document = proof_validator._read_json(Path(published.manifest_path))
        first_public_path = Path(manifest_document["artifacts"][0]["path"])
        public_bundle_root = Path(*first_public_path.parts[:2])
        extra_entry = _artifact_entry(prepared_root, extra, "public_evidence")
        extra_entry["path"] = (
            public_bundle_root / "diagnostic" / "unexpected.json"
        ).as_posix()
        manifest_document["artifacts"].append(extra_entry)
        _write_json(Path(published.manifest_path), manifest_document)
    result_artifacts = {
        "manifest": Path(published.manifest_path).relative_to(run_root).as_posix(),
        "evaluation": Path(published.evaluation_path).relative_to(run_root).as_posix(),
        "evidence": Path(published.evidence_path).relative_to(run_root).as_posix(),
    }
    state = store.commit_terminal_publication(
        state.run_id,
        prepared_root=Path(published.prepared_root).relative_to(run_root).as_posix(),
        to_stage=RunStage.UNSUPPORTED,
        expected_state_version=state.state_version,
        reason_code=H4_REASON_CODE,
        stage_payload={"reason_code": H4_REASON_CODE},
        result_artifacts=result_artifacts,
    )

    state_path = run_root / "state.json"
    validated = proof_validator._load_validated_r1_state(state_path)
    # Exercise RunStore's terminal-manifest verification too; this fixture is not
    # a hand-authored substitute for the retained production state.
    assert store.read_result(run_id).state_version == validated.state_version
    manifest = run_root / validated.result_artifacts["manifest"]
    evaluation = run_root / validated.result_artifacts["evaluation"]
    evidence = run_root / validated.result_artifacts["evidence"]
    case_result = run_root / "provider-evidence" / "case-result.json"
    _write_json(case_result, _live_case_result(store, run_id))
    roles = {
        "repair_input_ifc": source,
        "runtime_state": state_path,
        "live_provider_case_result": case_result,
        "live_retained_artifact_0001": manifest,
        "live_retained_artifact_0002": evaluation,
        "live_retained_artifact_0003": evidence,
    }
    return store, validated, source, roles


def _live_case_result(store: RunStore, run_id: str) -> dict[str, Any]:
    result = store.read_result(run_id)
    return {
        "case_id": "H4",
        "status": "passed",
        "contract_pass": True,
        "final": {
            "status": result.status,
            "reason_code": result.reason_code,
            "run_id": result.run_id,
            "state_version": result.state_version,
            "complete_repair_success": result.complete_repair_success,
            "successful_artifact_publishable": (
                result.successful_artifact_publishable
            ),
            "artifacts": dict(result.artifacts),
        },
    }


def test_r1_live_case_result_accepts_exact_validated_runstore_terminal(
    tmp_path: Path,
) -> None:
    store, state, _source, _roles = _validated_h4_state(tmp_path)
    case_result = _live_case_result(store, state.run_id)

    proof_validator._audit_r1_case_result_state_binding(
        case_result=case_result,
        validated_state=state,
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("run_id", "repair-r1-h4-spliced"),
        ("state_version", 999),
        ("status", "succeeded"),
        ("reason_code", None),
        ("complete_repair_success", True),
        ("successful_artifact_publishable", True),
        ("artifacts", {"successful_ifc": "published/forged.ifc"}),
    ),
)
def test_r1_live_case_result_rejects_every_terminal_field_drift(
    tmp_path: Path,
    field: str,
    replacement: Any,
) -> None:
    store, state, _source, _roles = _validated_h4_state(tmp_path)
    case_result = _live_case_result(store, state.run_id)
    case_result["final"][field] = replacement

    with pytest.raises(ValueError, match="proof.live.case_result_state_binding"):
        proof_validator._audit_r1_case_result_state_binding(
            case_result=case_result,
            validated_state=state,
        )


def test_r1_live_case_result_rejects_a_terminal_spliced_from_another_run(
    tmp_path: Path,
) -> None:
    authoritative_store, authoritative_state, _source, _roles = (
        _validated_h4_state(tmp_path, run_id="repair-r1-h4-authoritative")
    )
    foreign_store, foreign_state, _source, _roles = _validated_h4_state(
        tmp_path,
        run_id="repair-r1-h4-foreign",
    )
    assert authoritative_state.state_version == foreign_state.state_version
    case_result = _live_case_result(foreign_store, foreign_state.run_id)

    with pytest.raises(ValueError, match="proof.live.case_result_state_binding"):
        proof_validator._audit_r1_case_result_state_binding(
            case_result=case_result,
            validated_state=authoritative_state,
        )

    # Keep the authoritative RunStore read in the test path so a foreign result
    # cannot pass merely because both runs happen to share the same version.
    assert authoritative_store.read_result(authoritative_state.run_id).run_id != (
        case_result["final"]["run_id"]
    )


def test_r1_h4_no_mutation_artifacts_accepts_only_source_and_failure_bundle(
    tmp_path: Path,
) -> None:
    _store, state, source, roles = _validated_h4_state(tmp_path)

    proof_validator._audit_r1_h4_no_mutation_artifacts(
        roles=roles,
        source_ifc_path=source,
        validated_state=state,
    )


def test_r1_h4_rejects_hash_valid_but_semantically_tampered_failure_evidence(
    tmp_path: Path,
) -> None:
    store, state, source, roles = _validated_h4_state(
        tmp_path,
        evidence_payload={
            "reason_code": "FORGED_REASON",
            "stage": RunStage.INDEX_READY.value,
        },
    )

    # This is deliberately not a hash-failure test: the tamper is present before
    # the production publication commit, so the RunStore chain is self-consistent.
    assert store.read_result(state.run_id).reason_code == H4_REASON_CODE
    with pytest.raises(ValueError, match="proof.h4.failure_terminal_evidence"):
        proof_validator._audit_r1_h4_no_mutation_artifacts(
            roles=roles,
            source_ifc_path=source,
            validated_state=state,
        )


def test_r1_h4_rejects_hash_valid_but_forged_failure_evaluation(
    tmp_path: Path,
) -> None:
    evaluation = _terminal_failure_evaluation(H4_REASON_CODE)
    evaluation["status"] = "passed"
    store, state, source, roles = _validated_h4_state(
        tmp_path,
        evaluation_payload=evaluation,
    )

    assert store.read_result(state.run_id).reason_code == H4_REASON_CODE
    with pytest.raises(ValueError, match="proof.h4.failure_terminal_evidence"):
        proof_validator._audit_r1_h4_no_mutation_artifacts(
            roles=roles,
            source_ifc_path=source,
            validated_state=state,
        )


@pytest.mark.parametrize(
    "tamper",
    ("extra_top_level", "extra_nested_check", "wrong_check_id"),
)
def test_r1_h4_rejects_hash_valid_failure_evaluation_shape_drift(
    tmp_path: Path,
    tamper: str,
) -> None:
    evaluation = _terminal_failure_evaluation(H4_REASON_CODE)
    if tamper == "extra_top_level":
        evaluation["candidate"] = {"published": True}
    elif tamper == "extra_nested_check":
        evaluation["application"]["l0_pass"] = True
    else:
        evaluation["preservation"]["check_id"] = "forged.preservation"
    store, state, source, roles = _validated_h4_state(
        tmp_path,
        evaluation_payload=evaluation,
    )

    assert store.read_result(state.run_id).reason_code == H4_REASON_CODE
    with pytest.raises(ValueError, match="proof.h4.failure_terminal_evidence"):
        proof_validator._audit_r1_h4_no_mutation_artifacts(
            roles=roles,
            source_ifc_path=source,
            validated_state=state,
        )


def test_r1_h4_rejects_a_hash_valid_extra_terminal_artifact(
    tmp_path: Path,
) -> None:
    store, state, source, roles = _validated_h4_state(
        tmp_path,
        extra_terminal_artifact=True,
    )

    assert store.read_result(state.run_id).reason_code == H4_REASON_CODE
    with pytest.raises(ValueError, match="proof.h4.failure_terminal_evidence"):
        proof_validator._audit_r1_h4_no_mutation_artifacts(
            roles=roles,
            source_ifc_path=source,
            validated_state=state,
        )


def test_r1_state_loader_verifies_terminal_failure_manifest_hashes(
    tmp_path: Path,
) -> None:
    _store, _state, _source, roles = _validated_h4_state(tmp_path)
    manifest = roles["live_retained_artifact_0001"]
    _write_json(manifest, {})

    with pytest.raises(ValueError, match="proof.runtime_state.invalid"):
        proof_validator._load_validated_r1_state(roles["runtime_state"])


@pytest.mark.parametrize(
    "hidden_artifact_kind",
    ("ifc", "changeset", "application"),
)
def test_r1_h4_no_mutation_artifacts_rejects_unknown_role_payloads(
    tmp_path: Path,
    hidden_artifact_kind: str,
) -> None:
    _store, state, source, roles = _validated_h4_state(tmp_path)
    run_root = roles["runtime_state"].parent
    hidden = run_root / "diagnostics" / (
        "opaque.ifc" if hidden_artifact_kind == "ifc" else "opaque.json"
    )
    if hidden_artifact_kind == "ifc":
        hidden.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, hidden)
    elif hidden_artifact_kind == "changeset":
        _write_json(
            hidden,
            {
                "schema_version": "text2ifc/ifc-repair-changeset/0.4",
                "changeset_id": "hidden-h4-changeset",
                "binding_status": "bound",
                "operations": [],
            },
        )
    else:
        _write_json(
            hidden,
            {
                "valid": True,
                "published": False,
                "operations": [],
            },
        )
    roles = deepcopy(roles)
    roles["live_retained_artifact_9999"] = hidden

    with pytest.raises(ValueError, match="proof.h4.no_mutation_artifacts"):
        proof_validator._audit_r1_h4_no_mutation_artifacts(
            roles=roles,
            source_ifc_path=source,
            validated_state=state,
        )
