import json
from pathlib import Path

from scripts.agent import run_phase6_5_deterministic_matrix


REQUIRED_GATES = {
    "bim_json_schema",
    "bim_json_semantics",
    "relationship_integrity",
    "expected_fact_coverage",
    "unrelated_component_preservation",
    "ifc_compile",
    "ifc_reopen",
    "generated_ifc_geometry",
    "audit",
    "secret_scan",
}


def test_deterministic_matrix_covers_success_and_failure_routes(tmp_path):
    output_root = tmp_path / "phase6.5-matrix"

    summary = run_phase6_5_deterministic_matrix.run_matrix(output_root)

    assert summary["schema_version"] == "text2ifc/phase6.5-deterministic-matrix/1.0"
    assert summary["evidence_class"] == "deterministic_fixture"
    assert summary["case_count"] == 8
    assert summary["accepted_count"] == 3
    assert summary["false_accept_count"] == 0
    assert {row["case_id"] for row in summary["cases"]} == {
        "two-storey-accepted",
        "three-storey-accepted",
        "scoped-repair-accepted",
        "draft-missing-fact",
        "scope-violation",
        "stale-binding",
        "unsupported-request",
        "non-improving",
    }
    assert (output_root / "matrix-result.json").is_file()
    assert (output_root / "matrix-report.md").is_file()
    for row in summary["cases"]:
        assert REQUIRED_GATES <= set(row["gates"])
        assert isinstance(row["timings_seconds"], dict)
        assert row["artifact_refs"]
        assert row["issue_delta"]["after"] <= row["issue_delta"]["before"] or row[
            "outcome"
        ] == "blocked"
        case_dir = output_root / row["case_id"]
        stored = json.loads((case_dir / "case-result.json").read_text(encoding="utf-8"))
        assert stored == row
        if row["outcome"] == "accepted":
            assert row["gates"]["ifc_compile"] is True
            assert row["gates"]["ifc_reopen"] is True
            assert (case_dir / "output.ifc").is_file()


def test_canonical_case_coordinates_are_fixture_data_not_production_constants():
    root = Path(__file__).resolve().parents[2]
    two = json.loads(
        (root / "dataset/processed/agent-demo/phase6.5-cases/two-storey-case.json").read_text(
            encoding="utf-8"
        )
    )
    three = json.loads(
        (root / "dataset/processed/agent-demo/phase6.5-cases/three-storey-case.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(two["design_brief"]["known_facts"]["storeys"]) == 2
    assert len(three["design_brief"]["known_facts"]["storeys"]) == 3
    assert two["design_brief"]["known_facts"]["stair"]["end_elevation_mm"] == 3150
    assert three["design_brief"]["known_facts"]["stairs"][1]["end_elevation_mm"] == 6300
