import json

from text2ifc_agent.run_report import build_phase6_4_review_report


def test_phase6_4_report_links_core_trace_artifacts(tmp_path):
    case_dir = tmp_path / "case"
    (case_dir / "design-brief").mkdir(parents=True)
    (case_dir / "generator").mkdir()
    (case_dir / "audit").mkdir()
    _write_text(case_dir / "input.txt", "创建一个测试房间。")
    _write_json(case_dir / "conversation.json", [{"role": "user", "content": "创建一个测试房间。"}])
    _write_json(case_dir / "design-brief" / "design-brief.json", {"status": "ready"})
    _write_json(case_dir / "generator" / "candidate.json", {"schema_version": "bim-json/2.0"})
    _write_json(case_dir / "generator" / "validation.json", {"valid": True, "issues": []})
    _write_json(case_dir / "ifc-verification.json", {"success": False})
    _write_json(case_dir / "geometry-feedback.json", {"success": False, "issues": []})
    _write_json(case_dir / "audit" / "audit-report.json", {"recommendation": "revise", "blocking": True})
    _write_json(
        case_dir / "issues.json",
        {
            "schema_version": "text2ifc/issues/1.0",
            "issues": [
                {
                    "issue_id": "issue_missing_wall",
                    "source": "audit",
                    "severity": "blocking",
                    "owner": "generator",
                    "issue_type": "missing_entity",
                    "expected_fact_ref": None,
                    "actual_ref": "generator/candidate.json",
                    "evidence": "Wall is missing.",
                    "suggested_route": "regenerate_json",
                    "retryable": True,
                }
            ],
        },
    )
    _write_json(
        case_dir / "route-decision.json",
        {
            "schema_version": "text2ifc/route-decision/2.0",
            "final_status": "blocked",
            "route": "regenerate_json",
            "target_stage": "generator",
            "blocking_issue_ids": ["issue_missing_wall"],
        },
    )
    _write_json(
        case_dir / "feedback-rounds.json",
        {
            "schema_version": "text2ifc/feedback-rounds/1.0",
            "rounds": [{"round_index": 0, "attempted_action": "prepare_generator_feedback"}],
        },
    )
    _write_json(
        case_dir / "case-result.json",
        {
            "case_id": "blocked-case",
            "final_status": "blocked",
            "route": "regenerate_json",
            "failure_owner": "generator",
        },
    )

    report = build_phase6_4_review_report(case_dir=case_dir)
    text = report.read_text(encoding="utf-8")

    assert "## Original Input" in text
    assert "## Transcript" in text
    assert "## Design Brief" in text
    assert "## BIM JSON or Draft" in text
    assert "## Validation" in text
    assert "## Compiler and Reopen" in text
    assert "## Gates" in text
    assert "## Audit" in text
    assert "## Normalized Issues" in text
    assert "issue_missing_wall" in text
    assert "## Route Decision" in text
    assert "regenerate_json" in text
    assert "## Feedback Rounds" in text
    assert "prepare_generator_feedback" in text
    assert "## Final Status" in text
    assert "blocked" in text
    assert "[issues.json](issues.json)" in text


def _write_json(path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path, text):
    path.write_text(text + "\n", encoding="utf-8")
