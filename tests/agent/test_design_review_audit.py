"""Offline A/B review contract: user acknowledgement must not erase a defect."""

import hashlib
import json

import pytest

from text2ifc_agent.live_pipeline import run_audit_report_stage
from tests.agent.test_phase6_1_live import _RecordingLiveProvider, _write_auditable_case_dir


def _context(root, decision="retain"):
    path = root / "design-brief/conversation.json"
    conversation = json.loads(path.read_text(encoding="utf-8"))
    answer = "我知道这个问题，请保留原要求并记录。" if decision == "retain" else "请按已确认的新位置修改，其他要求不变。"
    conversation.append({"turn_id": "turn-user-review", "role": "user", "content": answer})
    path.write_text(json.dumps(conversation, ensure_ascii=False), encoding="utf-8")
    source = root / "reference-review.json"
    source.write_text('{"source":"offline fixture","gap_mm":0}', encoding="utf-8")
    context = {
        "schema_version": "text2ifc/design-review-context/1.0",
        "conversation_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "concerns": [{
            "id": "walking-clearance",
            "description": "参考模型中上方梯段遮挡通行，局部净空为零。",
            "location": "一层至二层楼梯北端",
            "decision": decision,
            "decision_turn_id": "turn-user-review",
            "decision_quote": answer,
            "evidence_path": "reference-review.json",
            "evidence_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }],
    }
    (root / "design-review-context.json").write_text(json.dumps(context, ensure_ascii=False), encoding="utf-8")
    return context


def _audit(status="retained_known_issue"):
    return {
        "schema_version": "text2ifc/audit/3.0", "recommendation": "accept",
        "blocking": False, "deterministic_gate_status": "passed", "findings": [],
        "evidence_paths": ["generator/candidate.json", "design-review-context.json"],
        "design_review": {
            "scope": "limited_review_not_code_compliance",
            "concerns": [{"id": "walking-clearance", "status": status,
                          "description": "用户决定保留此已知净空问题。",
                          "evidence_paths": ["design-review-context.json", "generator/candidate.json"]}],
            "limitations": ["未进行完整建筑规范审查。"],
        },
    }


@pytest.mark.parametrize("decision,status", [("retain", "retained_known_issue"), ("revise", "not_verified")])
def test_public_audit_preserves_design_problem_separately_from_technical_acceptance(tmp_path, decision, status):
    root = _write_auditable_case_dir(tmp_path / decision)
    _context(root, decision)
    provider = _RecordingLiveProvider(_audit(status))
    result = run_audit_report_stage(provider=provider, case_dir=root, case_id=decision)
    assert result["valid"], json.loads((root / "audit/validation.json").read_text())
    assert "Audit Agent v3" in provider.prompt
    report = (root / "report.md").read_text(encoding="utf-8")
    assert "合理性问题与用户决定" in report
    assert status in report
    assert "未进行完整建筑规范审查" in report


@pytest.mark.parametrize("change", ["drop", "erase", "duplicate", "unknown", "bad_evidence", "downgrade"])
def test_audit_cannot_omit_erase_or_fabricate_acknowledged_issue(tmp_path, change):
    root = _write_auditable_case_dir(tmp_path / change)
    _context(root)
    payload = _audit()
    rows = payload["design_review"]["concerns"]
    if change == "drop":
        rows.clear()
    elif change == "erase":
        rows[0]["status"] = "resolved"
    elif change == "duplicate":
        rows.append(dict(rows[0]))
    elif change == "unknown":
        rows[0]["id"] = "another-building"
    elif change == "bad_evidence":
        rows[0]["evidence_paths"] = ["../private.json"]
    else:
        payload["schema_version"] = "text2ifc/audit/2.0"
        payload.pop("design_review")
    result = run_audit_report_stage(provider=_RecordingLiveProvider(payload), case_dir=root, case_id=change)
    assert not result["valid"]
    assert result["status"] == "blocked"
    errors = json.loads((root / "audit/validation.json").read_text(encoding="utf-8"))["issues"]
    assert any(row["code"].startswith("DESIGN_REVIEW") for row in errors)


@pytest.mark.parametrize("change", ["quote", "assistant", "stale", "evidence", "pending", "duplicate"])
def test_invalid_confirmation_context_stops_before_provider(tmp_path, change):
    root = _write_auditable_case_dir(tmp_path / change)
    context = _context(root)
    row = context["concerns"][0]
    if change == "quote":
        row["decision_quote"] = "用户从未说过的话"
    elif change == "assistant":
        path = root / "design-brief/conversation.json"
        turns = json.loads(path.read_text(encoding="utf-8"))
        turns[-1]["role"] = "assistant"
        path.write_text(json.dumps(turns), encoding="utf-8")
        context["conversation_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif change == "stale":
        context["conversation_sha256"] = "0" * 64
    elif change == "evidence":
        row["evidence_sha256"] = "0" * 64
    elif change == "pending":
        row["decision"] = "pending"
    else:
        context["concerns"].append(dict(row))
    (root / "design-review-context.json").write_text(json.dumps(context), encoding="utf-8")
    provider = _RecordingLiveProvider(_audit())
    with pytest.raises(ValueError, match="DESIGN_REVIEW"):
        run_audit_report_stage(provider=provider, case_dir=root, case_id=change)
    assert provider.prompt == ""
