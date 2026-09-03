from __future__ import annotations

from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.run_artifacts import publish_terminal_artifacts


def test_requested_property_l2_failure_never_exposes_successful_ifc(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.ifc"
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity(
        "IfcProject",
        GlobalId="0000000000000000000001",
        Name="Fixture",
    )
    model.write(str(candidate))
    evaluation = {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "status": "failed",
        "complete_repair_success": False,
        "successful_artifact_publishable": False,
        "diagnostic_artifact_retained": True,
        "application": {"status": "passed"},
        "preservation": {"status": "passed"},
        "operations": [
            {
                "operation_id": "operation-1",
                "operation_type": "add_window_with_opening_to_wall",
                "status": "failed",
                "levels": [
                    {"level": "L1", "status": "passed", "checks": []},
                    {
                        "level": "L2",
                        "status": "failed",
                        "checks": [
                            {
                                "check_id": "explicit.pset-Custom_Asset.AssetCode",
                                "status": "failed",
                            }
                        ],
                    },
                    {"level": "L3", "status": "not_required", "checks": []},
                ],
            }
        ],
    }
    result = publish_terminal_artifacts(
        run_directory=tmp_path,
        terminal_status="l2_failed",
        evaluation=evaluation,
        candidate_ifc_path=candidate,
        evidence={"requested_property": "mismatch"},
        promote=False,
    )
    assert result.successful_ifc is None
    assert result.diagnostic_candidate is not None
