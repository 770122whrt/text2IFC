import json

from text2ifc_agent.interactive_cli_flow import _geometry_failure_requires_regeneration


def test_geometry_gate_failure_requires_regeneration_even_if_audit_accepts(tmp_path):
    (tmp_path / "geometry-feedback.json").write_text(
        json.dumps(
            {
                "success": False,
                "issues": [
                    {
                        "code": "WALL_SEGMENT_MISMATCH",
                        "path": "/walls/storey-2-wall-landing-corridor",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    audit_report = {"recommendation": "accept", "blocking": False}

    assert _geometry_failure_requires_regeneration(tmp_path, audit_report) is True


def test_geometry_regeneration_does_not_run_for_a_passing_gate(tmp_path):
    (tmp_path / "geometry-feedback.json").write_text(
        json.dumps({"success": True, "issues": []}), encoding="utf-8"
    )
    audit_report = {"recommendation": "accept", "blocking": False}

    assert _geometry_failure_requires_regeneration(tmp_path, audit_report) is False
