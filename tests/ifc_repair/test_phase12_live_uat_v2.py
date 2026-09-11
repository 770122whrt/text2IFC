from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest
from scripts.ifc_repair import run_phase12_live_uat_v2 as live_v2


ROOT = Path(__file__).resolve().parents[2]


def test_v2_live_runner_is_directly_executable() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/ifc_repair/run_phase12_live_uat_v2.py",
            "--help",
        ),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--require-green-preflight" in completed.stdout


def test_v2_live_runner_requires_admission_without_running_preflight_or_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    transport_constructed = False

    def forbidden_transport() -> object:
        nonlocal transport_constructed
        transport_constructed = True
        pytest.fail("missing admission must block before Provider transport")

    monkeypatch.setattr(
        live_v2.base,
        "run_preflight",
        lambda *_args, **_kwargs: pytest.fail(
            "V2 missing admission must not automatically run Full Preflight"
        ),
    )

    result = live_v2.run_live_uat_v2(
        tmp_path / "run",
        transport_factory=forbidden_transport,
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "LIVE_ADMISSION_REQUIRED"
    assert result["preflight"]["status"] == "not_run"
    assert result["transport_calls"] == 0
    assert transport_constructed is False


def test_v2_changed_scope_admission_binds_current_zero_network_evidence() -> None:
    admission = live_v2._load_v2_changed_scope_admission(
        ROOT
        / "dataset/processed/ifc-repair-runs/phase12-live-v2"
        / "admission-20260903/changed-scope-admission-v2.json"
    )

    assert admission["status"] == "passed"
    assert admission["mode"] == "changed_scope_evidence_reuse_v2"
    assert admission["provider_calls"] == 0
    assert admission["network_transport_attempted"] is False


def test_v2_live_contract_uses_the_persisted_vvo_restoration_damage() -> None:
    expected = (
        ROOT
        / "dataset/processed/ifc-repair-runs"
        / "phase12-plan07-v2-restoration-20260903T-live-baseline"
        / "accepted/phase12-v2-vvo-beam-column-atomic-restoration/damaged.ifc"
    ).resolve()

    assert live_v2.SOURCE.resolve() == expected
    assert live_v2.SOURCE.is_file()
    assert live_v2.FROZEN_SOURCE_SHA256 == (
        "sha256:636135b4bc12ea3e45d9a7155f714834"
        "ff5eaaba1f2d3d2e7a5ae84a525a59aa"
    )
    assert (
        "sha256:" + hashlib.sha256(live_v2.SOURCE.read_bytes()).hexdigest()
        == live_v2.FROZEN_SOURCE_SHA256
    )


def test_v2_live_contract_is_versioned_and_uses_real_vvo_geometry() -> None:
    by_id = {case.case_id: case for case in live_v2.DEFAULT_CASES}

    assert live_v2.LIVE_CASE_CONTRACT_VERSION == (
        "phase12-plan07-live-cases/0.2"
    )
    assert list(by_id) == [
        "complete",
        "clarification-resume",
        "window-semantic-canary",
        "program-guard",
    ]
    assert 'Storey named "标高7"' in live_v2.COMPLETE_REQUEST
    assert "(-3316.629521, -3863.522838, 0)" in live_v2.COMPLETE_REQUEST
    assert "(-3316.629521, -8803.522838, 0)" in live_v2.COMPLETE_REQUEST
    assert "455 mm wide and 570 mm high" in live_v2.COMPLETE_REQUEST
    assert 'Storey named "标高0"' in live_v2.COMPLETE_REQUEST
    assert "(-3307.426702, -9061.783140, 3712.059993)" in (
        live_v2.COMPLETE_REQUEST
    )
    assert "500 mm wide and 500 mm deep" in live_v2.COMPLETE_REQUEST
    assert 'Storey named "标高0"' in live_v2.CLARIFICATION_REQUEST
    assert "2IUEnGd5v4Yfg1ZlPtd0c_" in live_v2.WINDOW_SEMANTIC_REQUEST
    assert 'Storey named "标高7"' in live_v2.PROGRAM_GUARD_REQUEST
    assert live_v2._case_matrix_sha256(live_v2.DEFAULT_CASES) == (
        live_v2.FROZEN_CASE_MATRIX_SHA256
    )
def test_v2_cli_requires_explicit_admission_for_live_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(live_v2.base, "_environment", lambda _path: {})
    monkeypatch.setattr(
        live_v2,
        "_config_ready",
        lambda _environment: {"status": "ready"},
    )
    monkeypatch.setattr(
        live_v2,
        "run_live_uat_v2",
        lambda *_args, **_kwargs: pytest.fail("runner must not be invoked"),
    )

    with pytest.raises(SystemExit) as error:
        live_v2.main(["--require-green-preflight"])

    assert error.value.code == 2
