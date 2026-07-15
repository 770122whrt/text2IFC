import json

from text2ifc_agent.revision_gates import build_revision_gate_plan, write_revision_gate_evidence


def _candidate():
    return {
        "entities": [
            {"id": "wall-a", "ifc_class": "IfcWall", "attributes": {}},
            {"id": "space-a", "ifc_class": "IfcSpace", "attributes": {}},
            {"id": "window-a", "ifc_class": "IfcWindow", "attributes": {}},
            {"id": "stair-a", "ifc_class": "IfcStair", "attributes": {}},
            {"id": "slab-a", "ifc_class": "IfcSlab", "attributes": {}},
        ],
        "relationships": [],
    }


def _revision():
    return {
        "revision_id": "revision-03",
        "candidate_hash": "sha256:" + "a" * 64,
        "expected_facts_hash": "sha256:" + "b" * 64,
    }


def test_local_gate_plan_selects_only_changed_component_families():
    plan = build_revision_gate_plan(
        candidate=_candidate(),
        revision=_revision(),
        changed_ids=["window-a"],
        dependency_ids=["wall-a"],
        preservation={"unrelated_component_preservation_rate": 1.0},
        final=False,
    )

    assert plan["mode"] == "local_feedback"
    assert plan["local_gates"] == [
        "opening_filling_relationships",
        "opening_filling_geometry",
        "wall_host_geometry",
    ]
    assert "stair_vertical_connection" in plan["skipped_local_gates"]
    assert "compile_reopen" not in plan["local_gates"]
    assert plan["revision_binding"]["candidate_hash"] == _revision()["candidate_hash"]


def test_final_gate_plan_always_requires_complete_global_chain():
    plan = build_revision_gate_plan(
        candidate=_candidate(),
        revision=_revision(),
        changed_ids=["window-a"],
        dependency_ids=["wall-a"],
        preservation={"unrelated_component_preservation_rate": 1.0},
        final=True,
    )

    assert plan["mode"] == "final_acceptance"
    assert plan["global_gates"] == [
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
    ]
    assert plan["global_gates_mandatory"] is True


def test_revision_gate_evidence_rejects_hash_drift_and_persists_plan(tmp_path):
    plan = build_revision_gate_plan(
        candidate=_candidate(),
        revision=_revision(),
        changed_ids=["stair-a", "slab-a"],
        dependency_ids=[],
        preservation={"unrelated_component_preservation_rate": 1.0},
        final=True,
    )
    result = write_revision_gate_evidence(
        output_path=tmp_path / "revision-gates.json",
        plan=plan,
        gate_results={
            "revision_id": "revision-03",
            "candidate_hash": "sha256:" + "0" * 64,
            "gates": {},
        },
    )

    assert result["valid"] is False
    assert result["issues"][0]["code"] == "REVISION_GATE_HASH_MISMATCH"
    persisted = json.loads((tmp_path / "revision-gates.json").read_text(encoding="utf-8"))
    assert persisted == result
