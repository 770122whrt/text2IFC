from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.run_artifacts import publish_terminal_artifacts


TERMINAL_STATUSES = (
    "clarification_required",
    "unsupported",
    "provider_invalid",
    "provider_exhausted",
    "resolution_failed",
    "context_failed",
    "audit_failed",
    "application_failed",
    "l1_failed",
    "l2_failed",
    "l2_partial",
    "l2_not_evaluable",
    "succeeded",
)


def _evaluation(status: str) -> dict[str, object]:
    publishable = status == "succeeded"
    evaluation_status = "passed" if publishable else (
        "partial" if status == "l2_partial" else "not_evaluable" if status == "l2_not_evaluable" else "failed"
    )
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1",
        "status": evaluation_status,
        "reason": status,
        "complete_repair_success": publishable,
        "successful_artifact_publishable": publishable,
        "diagnostic_artifact_retained": not publishable,
        "application": {"check_id": "application.valid", "status": evaluation_status, "reason": status},
        "preservation": {"check_id": "preservation.valid", "status": evaluation_status, "reason": status},
        "operations": [],
    }


def _candidate(path: Path) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcProject", GlobalId="0000000000000000000001")
    model.write(str(path))


@pytest.mark.parametrize("terminal_status", TERMINAL_STATUSES)
def test_every_terminal_writes_evaluation_and_only_canonical_pass_publishes_success(
    tmp_path: Path, terminal_status: str
) -> None:
    run = tmp_path / terminal_status
    run.mkdir()
    candidate = run / "staging-candidate.ifc"
    if terminal_status not in {
        "clarification_required", "unsupported", "provider_invalid", "provider_exhausted",
        "resolution_failed", "context_failed", "audit_failed", "application_failed",
    }:
        _candidate(candidate)

    artifacts = publish_terminal_artifacts(
        run_directory=run,
        terminal_status=terminal_status,
        evaluation=_evaluation(terminal_status),
        candidate_ifc_path=candidate if candidate.exists() else None,
        evidence={"terminal_status": terminal_status},
    )

    assert Path(artifacts.evaluation_path).is_file()
    assert json.loads(Path(artifacts.evaluation_path).read_text(encoding="utf-8"))[
        "schema_version"
    ].endswith("/0.2")
    assert (artifacts.successful_ifc is not None) is (terminal_status == "succeeded")
    assert artifacts.successful_ifc != artifacts.diagnostic_candidate
    if terminal_status == "succeeded":
        assert artifacts.diagnostic_candidate is None
    elif candidate.exists() or terminal_status.startswith(("l1_", "l2_")):
        assert artifacts.successful_ifc is None

    manifest = json.loads(Path(artifacts.manifest_path).read_text(encoding="utf-8"))
    for item in manifest["artifacts"]:
        artifact_path = run / item["path"]
        assert artifact_path.is_file()
        assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == item["sha256"]


@pytest.mark.parametrize("status", ["failed", "partial", "not_evaluable"])
def test_nonpassing_evaluation_flag_cannot_be_promoted_even_with_success_terminal_name(
    tmp_path: Path, status: str
) -> None:
    run = tmp_path / status
    run.mkdir()
    candidate = run / "candidate.ifc"
    _candidate(candidate)
    evaluation = _evaluation("succeeded")
    evaluation["status"] = status
    evaluation["complete_repair_success"] = False
    evaluation["successful_artifact_publishable"] = False

    artifacts = publish_terminal_artifacts(
        run_directory=run,
        terminal_status="succeeded",
        evaluation=evaluation,
        candidate_ifc_path=candidate,
        evidence={"diagnostic": status},
    )

    assert artifacts.successful_ifc is None
    assert artifacts.diagnostic_candidate is not None

