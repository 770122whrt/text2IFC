import json

from text2ifc_agent.audit import collect_revision_audit_evidence
from text2ifc_agent.prompt_registry import render_prompt


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_revision_audit_evidence_collects_changes_scope_preservation_and_gates(tmp_path):
    candidate_hash = "sha256:" + "a" * 64
    _write(
        tmp_path / "candidate-revision.json",
        {
            "revision_id": "revision-01",
            "candidate_hash": candidate_hash,
            "expected_facts_hash": "sha256:" + "b" * 64,
        },
    )
    _write(
        tmp_path / "component-preservation.json",
        {
            "changed_ids": ["window-a"],
            "dependency_ids": ["wall-a"],
            "unrelated_component_preservation_rate": 1.0,
        },
    )
    _write(
        tmp_path / "revision-gates.json",
        {
            "valid": True,
            "plan": {"revision_binding": {"candidate_hash": candidate_hash}},
            "gate_results": {"candidate_hash": candidate_hash},
        },
    )
    _write(
        tmp_path / "changeset-round-01" / "change-scope.json",
        {"scope_id": "scope-revision-01", "entity_ids": ["window-a", "wall-a"]},
    )
    _write(
        tmp_path / "changeset-round-01" / "changeset.json",
        {
            "changeset_id": "changeset-revision-01",
            "source_issue_ids": ["issue-window-001"],
            "operations": [
                {
                    "operation_id": "operation-window",
                    "target_id": "window-a",
                    "changes": {"/attributes/ObjectPlacement/origin": [0, 0, 900]},
                    "evidence_refs": ["issue-window-001:/expected"],
                }
            ],
        },
    )
    _write(tmp_path / "ifc-verification.json", {"success": True})
    _write(tmp_path / "geometry-feedback.json", {"success": True, "issues": []})

    evidence = collect_revision_audit_evidence(tmp_path)

    assert evidence["status"] == "bound"
    assert evidence["revision"]["revision_id"] == "revision-01"
    assert evidence["changed_ids"] == ["window-a"]
    assert evidence["dependency_ids"] == ["wall-a"]
    assert evidence["operations"][0]["target_id"] == "window-a"
    assert evidence["source_issue_ids"] == ["issue-window-001"]
    assert evidence["gate_evidence"]["valid"] is True
    assert evidence["ifc_result"]["success"] is True


def test_revision_audit_evidence_reports_hash_mismatch_instead_of_claiming_bound(tmp_path):
    _write(
        tmp_path / "candidate-revision.json",
        {"revision_id": "revision-01", "candidate_hash": "sha256:" + "a" * 64},
    )
    _write(
        tmp_path / "revision-gates.json",
        {
            "plan": {"revision_binding": {"candidate_hash": "sha256:" + "b" * 64}},
            "gate_results": {},
        },
    )

    evidence = collect_revision_audit_evidence(tmp_path)

    assert evidence["status"] == "binding_failed"
    assert evidence["issues"][0]["code"] == "AUDIT_REVISION_HASH_MISMATCH"


def test_audit_prompt_requires_revision_evidence_and_keeps_gates_authoritative():
    rendered = render_prompt(
        template_id="audit.v2",
        inputs={
            "USER_REQUEST": "创建建筑",
            "CONVERSATION": [],
            "DESIGN_BRIEF": {"status": "ready"},
            "TERMINAL_DOCUMENT": {"schema_version": "bim-json/2.0"},
            "DETERMINISTIC_GATES": {"gate_summary_passed": True},
            "REVISION_EVIDENCE": {
                "revision": {"revision_id": "revision-01"},
                "changed_ids": ["window-a"],
                "operations": [],
            },
            "REPAIR_ROUTE": {"route": "no_repair_needed"},
            "METRICS": {},
            "EVIDENCE_PATHS": ["revision-gates.json"],
        },
    )

    assert "revision-01" in rendered["text"]
    assert "window-a" in rendered["text"]
    assert "deterministic" in rendered["text"].lower()
    assert "{{REVISION_EVIDENCE}}" not in rendered["text"]
