"""Frozen T1 family: lossless Audit context, not LLM quality measurements."""

from copy import deepcopy
import importlib
import json

import pytest

from text2ifc_agent import live_pipeline
from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import ProviderOutputError
from tests.agent.test_phase6_1_live import _RecordingLiveProvider, _write_auditable_case_dir
from tests.agent.test_design_review_audit import _context, _audit


def _module():
    # Import inside tests so a missing implementation produces individual REDs.
    return importlib.import_module("text2ifc_agent.audit_context")


def _check(family="wall", *, success=True):
    return {"success": success, "revision": "current", "issues": [] if success else [
        {"code": "BAD_DIMENSION", "component_ids": [family + "-01"], "actual": 150, "expected": 0}],
        "measurements": [{"id": f"{family}-{i}", "name": "三层北侧构件", "height_mm": 3000,
                          "material": "砖", "evidence_path": "geometry-feedback.json"} for i in range(30)]}


def _inputs(family="wall", *, review=False):
    check = _check(family)
    inputs = {
        "USER_REQUEST": "按照已确认的尺寸建模，不要添加材料性能。",
        "CONVERSATION": [{"turn_id": "u1", "role": "user", "content": "第一层与二层相同，第三层的窗不同。"}],
        "DESIGN_BRIEF": {"known_facts": {"dimensions": [13200, 16800], "material": "砖"}},
        "TERMINAL_DOCUMENT": {"entities": [{"id": family + "-01", "attributes": {"Name": "北侧"}}]},
        "DETERMINISTIC_GATES": {"geometry_success": True, "geometry_feedback": check},
        "REVISION_EVIDENCE": {"status": "passed", "geometry_result": deepcopy(check),
                              "gate_evidence": {"local": deepcopy(check), "global": deepcopy(check)}},
        # The old prompt does not send this local-only key. Do not count it.
        "GATE_SUMMARY": {"local_only": "不应发送" * 1000},
        "REPAIR_ROUTE": {"route": "repair_attempted"}, "METRICS": {"calls": 2},
        "EVIDENCE_PATHS": ["generator/candidate.json", "geometry-feedback.json"],
    }
    if review:
        inputs["DESIGN_REVIEW_CONTEXT"] = {"concerns": [{"id": "gap", "decision": "retain", "decision_quote": "就是这样做"}]}
    return inputs


def _render(inputs, *, review=False, mode="deduplicated"):
    return _module().render_audit_context(inputs=inputs, review_enabled=review, mode=mode)


@pytest.mark.parametrize("family", ["wall", "window", "stair-flight"])
@pytest.mark.parametrize("review", [False, True])
def test_smaller_actual_prompt_preserves_all_transmitted_values(family, review):
    inputs = _inputs(family, review=review)
    before = deepcopy(inputs)
    baseline = render_prompt(template_id="audit.v3" if review else "audit.v2", inputs=inputs)
    rendered, record = _render(inputs, review=review)
    assert record["effective_mode"] == "deduplicated"
    assert record["roundtrip_verified"] is True
    assert record["baseline"]["utf8_bytes"] == len(baseline["text"].encode("utf-8"))
    assert record["selected"]["utf8_bytes"] < record["baseline"]["utf8_bytes"]
    assert record["selected"]["estimated_input_tokens"] < record["baseline"]["estimated_input_tokens"]
    assert record["actual_provider_tokens"] is None
    restored = _module().restore_audit_evidence(rendered["inputs"]["AUDIT_EVIDENCE_CONTEXT"])
    assert restored == {key: inputs[key] for key in ("DETERMINISTIC_GATES", "REVISION_EVIDENCE")}
    for key in baseline["inputs"]:
        if key not in restored:
            assert rendered["inputs"][key] == baseline["inputs"][key]
    assert "不应发送" not in rendered["text"]
    assert inputs == before
    assert _render(inputs, review=review) == (rendered, record)


@pytest.mark.parametrize("mutation", ["revision", "success", "actual", "order", "scalar_types"])
def test_near_duplicates_never_hide_conflicts_or_typed_values(mutation):
    inputs = _inputs()
    changed = inputs["REVISION_EVIDENCE"]["gate_evidence"]["local"]
    if mutation == "revision":
        changed["revision"] = "previous"
    elif mutation == "success":
        changed["success"] = False
        changed["issues"] = [{"code": "FAILED", "value": 0}]
    elif mutation == "actual":
        changed["measurements"][0]["height_mm"] = 2800
    elif mutation == "order":
        changed["measurements"].reverse()
    else:
        changed["values"] = [None, 0, False, 0.0, "0", [], {}]
    rendered, _ = _render(inputs)
    restored = _module().restore_audit_evidence(rendered["inputs"]["AUDIT_EVIDENCE_CONTEXT"])
    # JSON spelling distinguishes 0/False/0.0 as well as list order.
    for key in restored:
        assert json.dumps(restored[key], sort_keys=True) == json.dumps(inputs[key], sort_keys=True)


@pytest.mark.parametrize("review", [False, True])
def test_default_is_the_identical_registered_full_prompt(review):
    inputs = _inputs(review=review)
    rendered, record = _render(inputs, review=review, mode="full")
    assert rendered == render_prompt(template_id="audit.v3" if review else "audit.v2", inputs=inputs)
    assert record["effective_mode"] == "full"


@pytest.mark.parametrize("reason", ["small", "marker_collision"])
def test_unhelpful_or_ambiguous_encoding_falls_back_without_losing_data(reason):
    inputs = _inputs()
    if reason == "small":
        inputs["DETERMINISTIC_GATES"] = {"geometry_success": True}
        inputs["REVISION_EVIDENCE"] = {"status": "not_applicable"}
    else:
        inputs["REVISION_EVIDENCE"]["original"] = {"audit_ref": "user-owned-value"}
    rendered, record = _render(inputs)
    assert record["effective_mode"] == "full"
    assert record["fallback_reason"]
    assert rendered == render_prompt(template_id="audit.v2", inputs=inputs)


@pytest.mark.parametrize("damage", ["missing", "cycle", "version", "mixed_marker", "unused"])
def test_damaged_internal_references_fail_closed(damage):
    rendered, _ = _render(_inputs())
    bundle = deepcopy(rendered["inputs"]["AUDIT_EVIDENCE_CONTEXT"])
    key = next(iter(bundle["values"]))
    if damage == "missing":
        del bundle["values"][key]
    elif damage == "cycle":
        bundle["values"][key] = {"audit_ref": key}
    elif damage == "version":
        bundle["schema_version"] = "unknown"
    elif damage == "mixed_marker":
        bundle["values"][key] = {"audit_ref": key, "success": True}
    else:
        bundle["values"]["UNUSED"] = {"success": False}
    with pytest.raises(ValueError, match="AUDIT_CONTEXT"):
        _module().restore_audit_evidence(bundle)


def _ordinary_audit():
    return {"schema_version": "text2ifc/audit/2.0", "recommendation": "accept", "blocking": False,
            "deterministic_gate_status": "passed", "findings": [],
            "evidence_paths": ["generator/candidate.json", "repair/route.json"]}


def _public_case(tmp_path, monkeypatch, *, failed=False, review=False):
    root = _write_auditable_case_dir(tmp_path / "case")
    check = _check(success=not failed)
    (root / "geometry-feedback.json").write_text(json.dumps(check, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(live_pipeline, "collect_revision_audit_evidence", lambda _: {
        "status": "passed", "geometry_result": deepcopy(check), "previous_passed": _check(),
        "gate_evidence": {"local": deepcopy(check), "global": deepcopy(check)}})
    if review:
        _context(root)
    return root


@pytest.mark.parametrize("review", [False, True])
@pytest.mark.parametrize("failed", [False, True])
def test_public_audit_uses_compact_wire_but_original_hard_gates(tmp_path, monkeypatch, review, failed):
    root = _public_case(tmp_path, monkeypatch, failed=failed, review=review)
    provider = _RecordingLiveProvider(_audit() if review else _ordinary_audit())
    result = live_pipeline.run_audit_report_stage(provider=provider, case_dir=root, case_id="fixture",
                                                  audit_context_mode="deduplicated")
    assert result["valid"] is (not failed)
    record = json.loads((root / "audit/audit-context.json").read_text(encoding="utf-8"))
    assert record["effective_mode"] == "deduplicated"
    wire = json.loads((root / "audit/prompt-wire-input.json").read_text(encoding="utf-8"))
    full = json.loads((root / "audit/prompt-render-input.json").read_text(encoding="utf-8"))
    restored = _module().restore_audit_evidence(wire["AUDIT_EVIDENCE_CONTEXT"])
    assert restored["DETERMINISTIC_GATES"] == full["DETERMINISTIC_GATES"]
    if failed:
        validation = json.loads((root / "audit/validation.json").read_text(encoding="utf-8"))
        assert any(issue["code"] == "AUDIT_OVERRIDE_ATTEMPT" for issue in validation["issues"])
    rendered = render_prompt(template_id="audit.v5" if review else "audit.v4", inputs=wire)
    assert provider.prompt == rendered["text"]


def test_public_bad_encoding_stops_before_provider(tmp_path, monkeypatch):
    root = _public_case(tmp_path, monkeypatch)
    provider = _RecordingLiveProvider(_ordinary_audit())
    monkeypatch.setattr(_module(), "restore_audit_evidence", lambda _: {})
    with pytest.raises(ValueError, match="AUDIT_CONTEXT"):
        live_pipeline.run_audit_report_stage(provider=provider, case_dir=root, case_id="fixture",
                                              audit_context_mode="deduplicated")
    assert provider.prompt == ""


def test_public_unknown_mode_stops_before_provider(tmp_path):
    root = _write_auditable_case_dir(tmp_path / "case")
    provider = _RecordingLiveProvider(_ordinary_audit())
    with pytest.raises(ValueError, match="AUDIT_CONTEXT"):
        live_pipeline.run_audit_report_stage(provider=provider, case_dir=root, case_id="fixture",
                                              audit_context_mode="summarize")
    assert provider.prompt == ""


def test_failed_and_resumed_calls_preserve_exact_compact_input(tmp_path, monkeypatch):
    root = _public_case(tmp_path, monkeypatch)
    class FailingProvider:
        prompts = []

        def generate_live(self, *, prompt, **kwargs):
            self.prompts.append(prompt)
            raise ProviderOutputError("fixture malformed response")

    provider = FailingProvider()
    for index in range(2):
        with pytest.raises(ProviderOutputError):
            live_pipeline.run_audit_report_stage(provider=provider, case_dir=root, case_id="fixture",
                                                  audit_context_mode="deduplicated")
        folders = sorted((root / "audit-failures").iterdir())
        assert len(folders) == index + 1
        for folder, prompt in zip(folders, provider.prompts):
            assert (folder / "prompt-rendered.md").read_text(encoding="utf-8").rstrip("\n") == prompt.rstrip("\n")
            wire = json.loads((folder / "prompt-wire-input.json").read_text(encoding="utf-8"))
            assert render_prompt(template_id="audit.v4", inputs=wire)["text"].rstrip("\n") == prompt.rstrip("\n")
            assert json.loads((folder / "audit-context.json").read_text(encoding="utf-8"))["roundtrip_verified"]


def test_invalid_model_json_is_still_blocked_in_compact_mode(tmp_path, monkeypatch):
    root = _public_case(tmp_path, monkeypatch)
    provider = _RecordingLiveProvider(_ordinary_audit(), fenced=True)
    result = live_pipeline.run_audit_report_stage(provider=provider, case_dir=root, case_id="fixture",
                                                  audit_context_mode="deduplicated")
    assert not result["valid"]
