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


def test_review_brief_is_explicit_and_does_not_silently_change_ordinary_generation():
    from text2ifc_agent import interactive_cli_flow, live_pipeline
    from text2ifc_agent.prompt_registry import load_prompt_registry
    assert interactive_cli_flow.DESIGN_BRIEF_TEMPLATE_ID == live_pipeline.DESIGN_BRIEF_TEMPLATE_ID == "design-brief.v2.3"
    assert interactive_cli_flow.DESIGN_REVIEW_BRIEF_TEMPLATE_ID == live_pipeline.DESIGN_REVIEW_BRIEF_TEMPLATE_ID == "design-brief.v2.4"
    registry = load_prompt_registry()
    assert registry["design-brief.v2.3"]["sha256"] != registry["design-brief.v2.4"]["sha256"]
    assert registry["audit.v2"]["sha256"] != registry["audit.v3"]["sha256"]


def test_public_brief_stage_can_explicitly_select_the_review_contract(tmp_path):
    from text2ifc_agent.live_pipeline import complete_room_case, run_design_brief_stage
    root = _write_auditable_case_dir(tmp_path / "reference")
    brief = json.loads((root / "design-brief/design-brief.json").read_text(encoding="utf-8"))
    brief["schema_version"] = "text2ifc/design-brief/2.1"
    brief['known_facts']['semantic_requirements'] = []
    provider = _RecordingLiveProvider(brief)
    target = tmp_path / "review-brief"
    result = run_design_brief_stage(provider=provider, output_dir=target,
                                    case=complete_room_case(), design_review_enabled=True)
    assert result["valid"]
    trace = json.loads((target / "trace-manifest.json").read_text(encoding="utf-8"))
    assert trace["template_id"] == "design-brief.v2.4"


def test_retained_design_problem_never_overrides_a_failed_hard_gate(tmp_path):
    from text2ifc_agent.live_pipeline import _validate_live_audit_output
    root = _write_auditable_case_dir(tmp_path / "hard-gate")
    context = _context(root)
    issues = _validate_live_audit_output(_audit(), case_dir=root,
                                       deterministic_gates={"geometry_success": False}, review_context=context)
    assert any(issue["code"] == "AUDIT_OVERRIDE_ATTEMPT" for issue in issues)


def test_review_brief_cannot_generate_without_bound_decision_context(tmp_path):
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_generation import _write_ready_design_brief_call
    store = SessionStore.open(tmp_path / "sessions.sqlite", artifact_root=tmp_path)
    session = store.create_session(original_input="保留已知问题并说明。")
    try:
        _write_ready_design_brief_call(session.run_dir)
        path = session.run_dir / "calls/01-design-brief/metrics.json"
        metrics = json.loads(path.read_text(encoding="utf-8"))
        metrics["prompt_template_id"] = "design-brief.v2.4"
        path.write_text(json.dumps(metrics), encoding="utf-8")
        store.mark_session_status(session.session_id, "ready")
        def forbidden():
            raise AssertionError("Missing context must stop before Provider creation")
        with pytest.raises(ValueError, match="DESIGN_REVIEW_CONTEXT_REQUIRED"):
            run_ready_session_to_ifc(store=store, session=session.session_hash, provider_factory=forbidden)
        assert not (session.run_dir / "output.ifc").exists()
    finally:
        store.close()


@pytest.mark.parametrize("change", ["removed", "rebound"])
def test_final_acceptance_rechecks_the_same_context_before_compile(tmp_path, monkeypatch, change):
    from text2ifc_agent import live_pipeline
    root = _write_auditable_case_dir(tmp_path / change)
    context = _context(root)
    result = run_audit_report_stage(provider=_RecordingLiveProvider(_audit()), case_dir=root, case_id=change)
    assert result["valid"]
    if change == "removed":
        (root / "design-review-context.json").unlink()  # Only this isolated pytest fixture.
    else:
        context["concerns"][0]["description"] = "篡改了冻结的问题描述"
        (root / "design-review-context.json").write_text(json.dumps(context), encoding="utf-8")
    calls = []
    def gate(**kwargs):
        calls.append(kwargs)
        raise AssertionError("must not compile after changed review context")
    monkeypatch.setattr(live_pipeline, "run_candidate_gate_stage", gate)
    with pytest.raises(ValueError, match="DESIGN_REVIEW"):
        live_pipeline.run_final_acceptance_stage(case_dir=root, output_dir=root, case_id=change)
    assert calls == []


@pytest.mark.parametrize("decision", ["retain", "revise"])
def test_public_generation_keeps_review_in_final_session_report(tmp_path, decision):
    import ifcopenshell
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_generation import (
        PHASE6_1_COMPLETE, _SequenceLiveProvider, _write_ready_design_brief_call,
    )
    store = SessionStore.open(tmp_path / "sessions.sqlite", artifact_root=tmp_path)
    session = store.create_session(original_input="按确认的要求建模，记录已知问题。")
    try:
        _write_ready_design_brief_call(session.run_dir)
        design = session.run_dir / "design-brief"
        design.mkdir()
        call = session.run_dir / "calls/01-design-brief"
        (design / "conversation.json").write_bytes((call / "conversation.json").read_bytes())
        _context(session.run_dir, decision)
        (call / "conversation.json").write_bytes((design / "conversation.json").read_bytes())
        store.mark_session_status(session.session_id, "ready")
        candidate = json.loads((PHASE6_1_COMPLETE / "generator/candidate.json").read_text(encoding="utf-8"))
        provider = _SequenceLiveProvider([candidate, _audit("retained_known_issue" if decision == "retain" else "not_verified")])
        result = run_ready_session_to_ifc(store=store, session=session.session_hash, provider_factory=lambda: provider)
        assert result.status == "compiled"
        assert len(provider.session_ids) == 2
        assert ifcopenshell.open(str(session.run_dir / "output.ifc")).schema == "IFC2X3"
        report = (session.run_dir / "report.md").read_text(encoding="utf-8")
        assert "合理性问题与用户决定" in report
        assert "未进行完整建筑规范审查" in report
    finally:
        store.close()
