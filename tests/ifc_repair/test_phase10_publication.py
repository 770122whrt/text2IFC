from __future__ import annotations

from pathlib import Path

import pytest
import ifcopenshell

from text2ifc_ifc_repair.run_artifacts import publish_terminal_artifacts


def _evaluation(*, application: bool, reopen: bool, l1: bool, l2: bool) -> dict:
    passed = application and reopen and l1 and l2
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "status": "passed" if passed else "failed",
        "complete_repair_success": passed,
        "successful_artifact_publishable": passed,
        "diagnostic_artifact_retained": not passed,
        "application": {"status": "passed" if application else "failed"},
        "preservation": {"status": "passed" if reopen else "failed"},
        "operations": [{
            "operation_id": "operation-1",
            "operation_type": "add_window_with_opening_to_wall",
            "status": "passed" if passed else "failed",
            "levels": [
                {"level": "L1", "status": "passed" if l1 else "failed", "checks": []},
                {"level": "L2", "status": "passed" if l2 else "failed", "checks": []},
                {"level": "L3", "status": "not_required", "checks": []},
            ],
        }],
    }


@pytest.mark.parametrize(
    ("application", "reopen", "l1", "l2"),
    [
        (False, True, True, True),
        (True, False, True, True),
        (True, True, False, True),
        (True, True, True, False),
    ],
)
def test_any_terminal_gate_failure_omits_successful_ifc(
    tmp_path: Path, application: bool, reopen: bool, l1: bool, l2: bool
) -> None:
    candidate = tmp_path / "candidate.ifc"
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcProject", GlobalId="0000000000000000000001", Name="Fixture")
    model.write(str(candidate))
    result = publish_terminal_artifacts(
        run_directory=tmp_path,
        terminal_status="not_publishable",
        evaluation=_evaluation(application=application, reopen=reopen, l1=l1, l2=l2),
        candidate_ifc_path=candidate,
        evidence={"test": "phase10-terminal-truth-table"},
        promote=False,
    )
    assert result.successful_ifc is None
    assert result.diagnostic_candidate is not None
