import importlib
import importlib.util


def _audit_module():
    name = "text2ifc_agent.audit"
    assert importlib.util.find_spec(name) is not None, "Audit Agent is missing"
    return importlib.import_module(name)


def _evidence():
    return {
        "input": "input.txt",
        "design_brief": "design-brief.json",
        "candidate": "candidate.json",
        "validation": "validation-feedback.json",
        "geometry": "geometry-feedback.json",
        "raw_response": "raw-response.txt",
    }


def test_audit_cannot_override_failed_geometry_gate():
    audit = _audit_module()

    report = audit.build_audit_report(
        deterministic_gates={"schema": True, "compile": True, "geometry": False},
        intent_coverage={"room_size": "covered"},
        mismatches=[],
        unsupported_facts=[],
        evidence=_evidence(),
        narrative_recommendation="accept",
    )

    assert report["deterministic_status"] == "failed"
    assert report["blocking"] is True
    assert report["recommendation"] == "reject"


def test_audit_flags_user_intent_mismatch():
    audit = _audit_module()

    report = audit.build_audit_report(
        deterministic_gates={"schema": True, "compile": True, "geometry": True},
        intent_coverage={"requested_window": "mismatch"},
        mismatches=[{"code": "WINDOW_HOST_MISMATCH", "message": "窗户不在东墙。"}],
        unsupported_facts=[],
        evidence=_evidence(),
    )

    assert report["blocking"] is True
    assert report["recommendation"] == "revise"
    assert report["mismatches"][0]["code"] == "WINDOW_HOST_MISMATCH"


def test_audit_missing_evidence_path_is_diagnostic_failure():
    audit = _audit_module()
    evidence = _evidence()
    del evidence["raw_response"]

    report = audit.build_audit_report(
        deterministic_gates={"schema": True, "compile": True, "geometry": True},
        intent_coverage={},
        mismatches=[],
        unsupported_facts=[],
        evidence=evidence,
    )

    assert report["blocking"] is True
    assert any(item["code"] == "MISSING_EVIDENCE" for item in report["diagnostics"])
