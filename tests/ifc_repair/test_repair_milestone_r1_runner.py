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
    calls = 0

    def forbidden_transport():
        nonlocal calls
        calls += 1
        raise AssertionError("unapproved run must not construct Provider")

    result = runner.run_r1_acceptance(
        tmp_path / "blocked",
        manifest_path=MANIFEST,
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
