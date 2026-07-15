import json

from text2ifc_agent.run_report import build_live_run_report


def _write(path, payload, *, text=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if text:
        path.write_text(str(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")


def _base_report_case(root):
    for stage in ("design-brief", "generator", "audit"):
        _write(root / stage / "prompt-rendered.md", f"{stage} prompt", text=True)
        _write(root / stage / "response.raw.json", {"id": f"response-{stage}", "stop_reason": "end_turn"})
        _write(root / stage / "model-text.txt", "{}", text=True)
        _write(root / stage / "validation.json", {"valid": True, "issues": []})
        _write(root / stage / "metrics.json", {"response_id": f"response-{stage}", "evidence_class": "unit"})
    _write(root / "design-brief" / "input.txt", "创建建筑", text=True)
    _write(root / "design-brief" / "request.redacted.json", {"request": {"model": "unit"}})
    _write(root / "design-brief" / "conversation.json", [{"role": "user", "content": "创建建筑"}])
    _write(root / "design-brief" / "design-brief.json", {"status": "ready"})
    _write(root / "generator" / "candidate.json", {"schema_version": "bim-json/2.0"})
    _write(root / "audit" / "audit-report.json", {"recommendation": "accept", "blocking": False})
    _write(root / "repair" / "route.json", {"route": "no_repair_needed", "provider_call_count": 0})
    _write(root / "repair" / "repair-attempts.json", [])
    _write(root / "repair" / "metrics.json", {"evidence_class": "deterministic-no-call"})


def test_generated_report_embeds_revision_package_scope_operations_and_timing(tmp_path):
    root = tmp_path / "case"
    _base_report_case(root)
    candidate_hash = "sha256:" + "a" * 64
    _write(
        root / "candidate-revision.json",
        {"revision_id": "revision-01", "candidate_hash": candidate_hash, "expected_facts_hash": "sha256:" + "b" * 64},
    )
    _write(
        root / "component-preservation.json",
        {"changed_ids": ["window-a"], "dependency_ids": ["wall-a"], "unrelated_component_preservation_rate": 1.0},
    )
    _write(
        root / "revision-gates.json",
        {
            "valid": True,
            "plan": {
                "revision_binding": {"candidate_hash": candidate_hash},
                "local_gates": ["opening_filling_geometry"],
                "global_gates": ["ifc_compile", "ifc_reopen", "audit"],
            },
            "gate_results": {"candidate_hash": candidate_hash},
        },
    )
    _write(
        root / "changeset-round-01" / "change-scope.json",
        {"scope_id": "scope-revision-01", "entity_ids": ["window-a", "wall-a"]},
    )
    _write(
        root / "changeset-round-01" / "changeset.json",
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
    _write(
        root / "generator-staged" / "package-records.json",
        {"packages": [{"package_id": "package-storey-1", "status": "accepted", "response_id": "response-package-1", "attempt_count": 1}]},
    )
    _write(root / "ifc-verification.json", {"success": True})
    _write(root / "geometry-feedback.json", {"success": True, "issues": []})
    progress = [
        {"sequence": 1, "elapsed_seconds": 0.0, "stage": "generator", "status": "started"},
        {"sequence": 2, "elapsed_seconds": 2.5, "stage": "generator", "status": "formal"},
        {"sequence": 3, "elapsed_seconds": 2.5, "stage": "audit", "status": "started"},
        {"sequence": 4, "elapsed_seconds": 3.75, "stage": "audit", "status": "accepted"},
    ]
    _write(root / "progress.jsonl", "\n".join(json.dumps(item) for item in progress) + "\n", text=True)

    report_path = build_live_run_report(case_dir=root)
    report = report_path.read_text(encoding="utf-8")

    assert "## Revision and ChangeSet History" in report
    assert "revision-01" in report
    assert "window-a" in report
    assert "wall-a" in report
    assert "operation-window" in report
    assert "issue-window-001" in report
    assert "unrelated_component_preservation_rate" in report
    assert "## Generation Packages" in report
    assert "package-storey-1" in report
    assert "response-package-1" in report
    assert "## Stage Timing" in report
    assert "generator: `2.5` seconds" in report
    assert "audit: `1.25` seconds" in report
    assert "changeset-round-01/changeset.json" in report


def test_legacy_report_without_revision_sidecars_remains_valid(tmp_path):
    root = tmp_path / "legacy"
    _base_report_case(root)

    report = build_live_run_report(case_dir=root).read_text(encoding="utf-8")

    assert "## Revision and ChangeSet History" not in report
    assert "Generated from trace sidecars" in report
