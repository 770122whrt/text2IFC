from __future__ import annotations

import json
from pathlib import Path

from scripts.ifc_repair import run_repair_milestone_r1 as runner


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = (
    ROOT
    / "docs/validation/repair-milestone-r1/"
    "repair-r1-execution-manifest.json"
)


def test_r1_execution_manifest_binds_frozen_cases_models_and_resume_answers() -> None:
    loaded = runner.load_execution_manifest(MANIFEST)

    assert loaded["execution_order"] == [
        "E1", "E2", "E3", "E4", "M1", "M2",
        "M3", "H1", "H2", "H3", "H4", "A1",
    ]
    assert set(loaded["models"]) == {
        "R1-DPX-ARC",
        "R1-WRH-ARC",
        "R1-S65-STR",
        "R1-BW-TALL",
    }
    assert [case["case_id"] for case in loaded["cases"]] == (
        loaded["execution_order"]
    )
    assert loaded["resume_bindings"]["M1"]["kind"] == "add_detail"
    assert loaded["resume_bindings"]["H3"]["stable_public_identity"] == (
        "1hOSvn6df7F8_7GcBWlS2V"
    )
    serialized = json.dumps(loaded["public_cases"], ensure_ascii=False)
    for forbidden in (
        "evaluation_only_expected",
        "private_gold",
        "mutation_truth",
        "pristine",
    ):
        assert forbidden not in serialized


def test_r1_runner_readiness_never_constructs_provider(
    tmp_path: Path,
) -> None:
    calls = 0

    def forbidden_transport():
        nonlocal calls
        calls += 1
        raise AssertionError("readiness must not construct Provider")

    result = runner.run_r1_acceptance(
        tmp_path / "readiness",
        manifest_path=MANIFEST,
        execute_genuine=False,
        transport_factory=forbidden_transport,
    )

    assert result["status"] == "ready_for_genuine_authorization"
    assert result["transport_calls"] == 0
    assert result["case_count"] == 12
    assert calls == 0


def test_r1_runner_cannot_execute_while_manifest_is_unapproved(
    tmp_path: Path,
) -> None:
    manifest_document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_document["status"] = runner.PREPARED_STATUS
    unapproved_manifest = tmp_path / "unapproved-manifest.json"
    unapproved_manifest.write_text(
        json.dumps(manifest_document, ensure_ascii=False),
        encoding="utf-8",
    )
    calls = 0

    def forbidden_transport():
        nonlocal calls
        calls += 1
        raise AssertionError("unapproved run must not construct Provider")

    result = runner.run_r1_acceptance(
        tmp_path / "blocked",
        manifest_path=unapproved_manifest,
        execute_genuine=True,
        authorization_reference="not-sufficient-without-manifest-approval",
        transport_factory=forbidden_transport,
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "R1_GENUINE_AUTHORIZATION_REQUIRED"
    assert result["transport_calls"] == 0
    assert calls == 0


def test_r1_runner_requires_offline_admission_and_plan07_result_before_provider(
    tmp_path: Path,
) -> None:
    manifest_document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_document["status"] = runner.AUTHORIZED_STATUS
    authorized_manifest = tmp_path / "authorized-manifest.json"
    authorized_manifest.write_text(
        json.dumps(manifest_document, ensure_ascii=False),
        encoding="utf-8",
    )
    calls = 0

    def forbidden_transport():
        nonlocal calls
        calls += 1
        raise AssertionError("missing admission must not construct Provider")

    result = runner.run_r1_acceptance(
        tmp_path / "blocked-without-admission",
        manifest_path=authorized_manifest,
        execute_genuine=True,
        authorization_reference="reviewed-authorization",
        transport_factory=forbidden_transport,
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "R1_PREFLIGHT_AND_PLAN07_EVIDENCE_REQUIRED"
    assert result["transport_calls"] == 0
    assert calls == 0


def test_r1_plan07_result_binds_sibling_green_full_preflight(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run_root = tmp_path / "plan07"
    preflight_root = run_root / "preflight"
    preflight_root.mkdir(parents=True)
    preflight = {
        "schema_version": "text2ifc/phase12-live-preflight/0.4",
        "status": "passed",
        "evidence_sha256": "sha256:" + "1" * 64,
    }
    (preflight_root / "preflight.json").write_text(
        json.dumps(preflight),
        encoding="utf-8",
    )
    result_path = run_root / "live-uat-result.json"
    result_path.write_text(
        json.dumps({"preflight": preflight}),
        encoding="utf-8",
    )
    captured: dict[str, Path] = {}

    monkeypatch.setattr(
        runner.live_curator,
        "audit_live_uat_result",
        lambda _document: {"status": "passed"},
    )

    def load_green(path: Path) -> dict[str, object]:
        captured["path"] = Path(path).resolve()
        return {
            **preflight,
            "mode": "full_preflight_evidence_reuse",
            "evidence_path": (
                preflight_root / "preflight.json"
            ).relative_to(ROOT).as_posix(),
            "evidence_file_sha256": "sha256:" + "2" * 64,
        }

    monkeypatch.setattr(
        runner.live,
        "_load_green_full_preflight_evidence",
        load_green,
    )

    loaded = runner._load_plan07_result(result_path)

    assert captured["path"] == (preflight_root / "preflight.json").resolve()
    assert loaded["preflight"]["status"] == "passed"
    assert loaded["preflight"]["evidence_sha256"] == preflight[
        "evidence_sha256"
    ]


def test_r1_plan07_result_revalidates_curated_preflight_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run_root = tmp_path / "proof" / "provider-evidence"
    preflight_root = run_root / "preflight"
    snapshot = preflight_root / "external-artifacts" / "proof-manifest.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text('{"case_count": 22}\n', encoding="utf-8")
    preflight = {
        "schema_version": "text2ifc/phase12-live-preflight/0.4",
        "status": "passed",
        "evidence_sha256": "sha256:" + "1" * 64,
    }
    preflight_path = preflight_root / "preflight.json"
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    source_reference = "E:/repository/proof/manifest.json"
    retention = {
        "schema_version": "text2ifc/phase12-live-proof-preflight-retention/0.1",
        "preflight_sha256": "sha256:" + runner._sha256_path(preflight_path),
        "retained": [
            {
                "check_name": "proof",
                "evidence_kind": "declared_artifact",
                "source_reference": source_reference,
                "retained_path": "external-artifacts/proof-manifest.json",
                "sha256": "sha256:" + runner._sha256_path(snapshot),
                "size_bytes": snapshot.stat().st_size,
            }
        ],
    }
    (preflight_root / "retained-artifacts.json").write_text(
        json.dumps(retention), encoding="utf-8"
    )
    result_path = run_root / "live-uat-result.json"
    result_path.write_text(json.dumps({"preflight": preflight}), encoding="utf-8")
    monkeypatch.setattr(
        runner.live_curator,
        "audit_live_uat_result",
        lambda _document: {"status": "passed"},
    )
    captured = {}

    def load_green(path: Path, *, artifact_overrides=None):
        captured["path"] = Path(path).resolve()
        captured["overrides"] = artifact_overrides
        return {
            **preflight,
            "mode": "full_preflight_evidence_reuse",
            "evidence_path": preflight_path.relative_to(ROOT).as_posix(),
            "evidence_file_sha256": runner._sha256_path(preflight_path),
        }

    monkeypatch.setattr(
        runner.live,
        "_load_green_full_preflight_evidence",
        load_green,
    )

    loaded = runner._load_plan07_result(result_path)

    assert loaded["preflight"]["status"] == "passed"
    assert captured["overrides"] == {source_reference: snapshot.resolve()}

def test_r1_prerequisite_accepts_plan07_full_preflight_without_old_admission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plan07_path = tmp_path / "plan07" / "live-uat-result.json"
    plan07_path.parent.mkdir()
    plan07_path.write_text("{}", encoding="utf-8")
    plan07 = {
        "path": plan07_path.as_posix(),
        "sha256": "sha256:" + "3" * 64,
        "audit": {"status": "passed"},
        "preflight": {
            "path": "plan07/preflight/preflight.json",
            "sha256": "sha256:" + "4" * 64,
            "status": "passed",
            "evidence_sha256": "sha256:" + "5" * 64,
        },
    }
    monkeypatch.setattr(runner, "_load_plan07_result", lambda _path: plan07)

    evidence = runner._load_r1_prerequisite_evidence(
        plan07_result_path=plan07_path,
        admission_evidence_path=None,
    )

    assert evidence == {
        "full_preflight": plan07["preflight"],
        "plan07_result": plan07,
    }


def test_public_cases_carry_declarative_outcome_not_case_id_branching() -> None:
    """Contract evaluation must be driven by frozen expected outcomes.

    The runner's contract function may not switch on case ids; every case
    declares its frozen outcome class from the acceptance freeze, and the
    guard expectation is derived from that outcome, not from an identity.
    """
    loaded = runner.load_execution_manifest(MANIFEST)

    by_id = {case["case_id"]: case for case in loaded["public_cases"]}
    assert by_id["H4"]["expected_outcome"] == (
        "unsupported_program_zero_mutation"
    )
    assert by_id["H4"]["expect_program_guard"] is True
    assert by_id["H4"]["expect_resume"] is False
    for case_id in ("E1", "E2", "E3", "E4", "M2", "M3", "H1", "H2", "A1"):
        assert by_id[case_id]["expected_outcome"] in {
            "success",
            "atomic_success",
        }
        assert by_id[case_id]["expect_program_guard"] is False
        assert by_id[case_id]["expect_resume"] is False
    for case_id in ("M1", "H3"):
        assert by_id[case_id]["expect_resume"] is True
        assert by_id[case_id]["expect_program_guard"] is False


def _guard_final(mutating: bool) -> dict:
    return {
        "status": "unsupported",
        "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        "successful_artifact_publishable": False,
        "program_guard_evidence": {
            "source_reference": "fixture",
            "source_sha256_before": "sha256:x",
            "source_sha256_after": "sha256:x",
            "source_unchanged": True,
            "stage2_attempts": 0 if not mutating else 1,
            "candidate_output_paths": [],
            "mutation_attempted": mutating,
        },
    }


def test_guard_contract_passes_only_with_zero_mutation_evidence() -> None:
    ok = runner._case_contract_pass(
        "unsupported_program_zero_mutation",
        _guard_final(mutating=False),
        live_evidence_pass=True,
        private_evidence_detected=False,
        expect_resume=False,
    )
    mutated = runner._case_contract_pass(
        "unsupported_program_zero_mutation",
        _guard_final(mutating=True),
        live_evidence_pass=True,
        private_evidence_detected=False,
        expect_resume=False,
    )
    missing_evidence = dict(_guard_final(mutating=False))
    missing_evidence["program_guard_evidence"] = None
    crashed_pre_fix = runner._case_contract_pass(
        "unsupported_program_zero_mutation",
        missing_evidence,
        live_evidence_pass=True,
        private_evidence_detected=False,
        expect_resume=False,
    )
    assert ok is True
    assert mutated is False
    # A None guard evidence must be a contract failure, never an exception:
    # this is the exact crash observed on the first 12-case run.
    assert crashed_pre_fix is False


def test_success_contract_requires_resume_answer_only_when_declared() -> None:
    def _success_final(applied: bool) -> dict:
        return {
            "status": "succeeded",
            "complete_repair_success": True,
            "successful_artifact_publishable": True,
            "clarification_answer_applied": applied,
            "strict_reopen_verification": {
                "status": "passed",
                "l0_pass": True,
                "l1_pass": True,
                "l2_pass": True,
            },
        }

    resume_required = runner._case_contract_pass(
        "success",
        _success_final(applied=False),
        live_evidence_pass=True,
        private_evidence_detected=False,
        expect_resume=True,
    )
    resume_satisfied = runner._case_contract_pass(
        "success",
        _success_final(applied=True),
        live_evidence_pass=True,
        private_evidence_detected=False,
        expect_resume=True,
    )
    plain_success = runner._case_contract_pass(
        "success",
        _success_final(applied=False),
        live_evidence_pass=True,
        private_evidence_detected=False,
        expect_resume=False,
    )
    assert resume_required is False
    assert resume_satisfied is True
    assert plain_success is True
