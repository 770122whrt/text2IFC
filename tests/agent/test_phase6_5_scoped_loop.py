import json
from pathlib import Path

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.revisions import hash_json_value
from text2ifc_agent.scoped_loop import resolve_issue_component_refs, run_scoped_changeset_round


MINIMAL = Path(__file__).resolve().parents[1] / "contract_v2" / "fixtures" / "minimal.json"


def _candidate():
    return json.loads(MINIMAL.read_text(encoding="utf-8"))


def _expected():
    return {"schema_version": "text2ifc/expected-facts/1.0", "storeys": []}


def _issue():
    return {
        "issue_id": "issue-wall-001",
        "source": "deterministic_gate",
        "severity": "blocking",
        "owner": "generator",
        "issue_type": "semantic_mismatch",
        "expected_fact_ref": "expected-facts:/walls/wall-1/name",
        "actual_ref": "/entities/1/attributes/Name",
        "evidence": "Wall name differs from the expected fact.",
        "suggested_route": "regenerate_json",
        "retryable": True,
        "expected": "Corrected wall",
        "actual": "Wall 1",
    }


class ChangeSetProvider:
    def __init__(
        self,
        candidate,
        expected,
        *,
        violate_scope_once=False,
        invalid_contract_once=False,
    ):
        self.candidate = candidate
        self.expected = expected
        self.violate_scope_once = violate_scope_once
        self.invalid_contract_once = invalid_contract_once
        self.calls = []

    def generate_live(self, *, session_id, prompt, schema, state):
        self.calls.append({"session_id": session_id, "prompt": prompt, "schema": schema, "state": state})
        index = build_candidate_index(self.candidate)
        changes = {"/attributes/Name": "Corrected wall"}
        if self.violate_scope_once and len(self.calls) == 1:
            changes = {"/attributes/ObjectPlacement/axis": [0, 1, 0]}
        payload = {
            "schema_version": "text2ifc/bim-json-changeset/1.0",
            "changeset_id": "changeset-revision-01",
            "base_revision_id": "revision-00",
            "base_candidate_hash": index["candidate_hash"],
            "expected_facts_hash": hash_json_value(self.expected),
            "source_issue_ids": ["issue-wall-001"],
            "scope_id": "scope-revision-01",
            "operations": [
                {
                    "operation_id": "operation-wall-name",
                    "op": "update_entity",
                    "target_id": "wall-1",
                    "target_component_hash": index["component_hashes"]["wall-1"],
                    "changes": changes,
                    "evidence_refs": ["issue-wall-001:/expected"],
                }
            ],
        }
        if self.invalid_contract_once and len(self.calls) == 1:
            payload["operations"][0]["evidence_refs"] = ["issue-wall-001:"]
        text = json.dumps(payload, ensure_ascii=False)
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={"model": "fake", "messages": [{"role": "user", "content": prompt}]},
            response={
                "id": "response-scoped-001",
                "model": "fake",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
            events=(),
            output=ProviderOutput(text=text, metadata={"provider": "fake"}),
        )


def test_resolve_issue_component_refs_converts_exact_collection_index_to_stable_id():
    candidate = _candidate()

    resolved = resolve_issue_component_refs(candidate=candidate, issues=[_issue()])

    assert resolved["issues"] == []
    assert resolved["resolved"][0]["actual_ref"] == "entity:wall-1#/attributes/Name"
    assert resolved["resolved"][0]["actual"] == "Wall 1"


def test_resolve_issue_component_refs_blocks_out_of_range_index_without_guessing():
    issue = _issue()
    issue["actual_ref"] = "/entities/99/attributes/Name"

    resolved = resolve_issue_component_refs(candidate=_candidate(), issues=[issue])

    assert resolved["resolved"] == []
    assert resolved["issues"][0]["code"] == "CHANGESET_TARGET_UNRESOLVED"


def test_scoped_round_applies_changeset_and_preserves_unrelated_components(tmp_path):
    candidate = _candidate()
    expected = _expected()
    provider = ChangeSetProvider(candidate, expected)
    before = build_candidate_index(candidate)

    result = run_scoped_changeset_round(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-a",
        round_number=1,
        user_request="修正墙名称。",
        conversation=[{"role": "user", "content": "墙名称应为 Corrected wall。"}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        candidate=candidate,
        issues=[_issue()],
        trace_level="debug",
    )

    assert result["valid"] is True
    assert result["revision"]["revision_id"] == "revision-01"
    wall = next(entity for entity in result["candidate"]["entities"] if entity["id"] == "wall-1")
    assert wall["attributes"]["Name"] == "Corrected wall"
    after = build_candidate_index(result["candidate"])
    assert after["component_hashes"]["project-1"] == before["component_hashes"]["project-1"]
    assert result["preservation"]["unrelated_component_preservation_rate"] == 1.0
    assert (tmp_path / "change-scope.json").is_file()
    assert (tmp_path / "changeset.json").is_file()
    assert (tmp_path / "revisions" / "revision-01" / "candidate.json").is_file()
    assert provider.calls[0]["state"]["stage"] == "changeset"


def test_scoped_round_uses_component_issues_for_scope_and_keeps_global_evidence(tmp_path):
    candidate = _candidate()
    expected = _expected()
    provider = ChangeSetProvider(candidate, expected)
    global_issue = {
        **_issue(),
        "issue_id": "issue-compile-001",
        "actual_ref": "/output.ifc",
        "evidence": "COMPILE_REOPEN_FAILED: output could not be reopened.",
    }

    result = run_scoped_changeset_round(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-context-evidence",
        round_number=1,
        user_request="Correct the wall name.",
        conversation=[{"role": "user", "content": "Correct the wall name."}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        candidate=candidate,
        issues=[_issue(), global_issue],
        trace_level="debug",
    )

    assert result["valid"] is True
    assert provider.calls
    prompt = provider.calls[0]["prompt"]
    assert "issue-wall-001" in prompt
    assert "issue-compile-001" in prompt
    scope = json.loads((tmp_path / "change-scope.json").read_text(encoding="utf-8"))
    assert scope["source_issue_ids"] == ["issue-wall-001"]
    resolution = json.loads((tmp_path / "scope-resolution.json").read_text(encoding="utf-8"))
    assert resolution["context_issue_ids"] == ["issue-compile-001"]


def test_scoped_round_retries_one_application_scope_violation_without_mutating_base(tmp_path):
    candidate = _candidate()
    expected = _expected()
    provider = ChangeSetProvider(candidate, expected, violate_scope_once=True)
    before = build_candidate_index(candidate)

    result = run_scoped_changeset_round(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-application-retry",
        round_number=1,
        user_request="Correct the wall name.",
        conversation=[{"role": "user", "content": "Correct the wall name."}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        candidate=candidate,
        issues=[_issue()],
        trace_level="debug",
    )

    assert result["valid"] is True
    assert len(provider.calls) == 2
    assert "CHANGESET_SCOPE_VIOLATION" in provider.calls[1]["prompt"]
    assert (tmp_path / "attempt-02" / "application.json").is_file()
    assert (tmp_path / "revisions" / "revision-01" / "candidate.json").is_file()
    assert build_candidate_index(candidate) == before
    wall = next(
        entity for entity in result["candidate"]["entities"] if entity["id"] == "wall-1"
    )
    assert wall["attributes"]["Name"] == "Corrected wall"


def test_scoped_round_retries_one_invalid_changeset_with_schema_feedback(tmp_path):
    candidate = _candidate()
    expected = _expected()
    provider = ChangeSetProvider(candidate, expected, invalid_contract_once=True)
    before = build_candidate_index(candidate)

    result = run_scoped_changeset_round(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-contract-retry",
        round_number=1,
        user_request="Correct the wall name.",
        conversation=[{"role": "user", "content": "Correct the wall name."}],
        design_brief={"status": "ready"},
        expected_facts=expected,
        candidate=candidate,
        issues=[_issue()],
        trace_level="debug",
    )

    assert result["valid"] is True
    assert len(provider.calls) == 2
    assert "SCHEMA_VALIDATION_ERROR" in provider.calls[1]["prompt"]
    assert "/operations/0" in provider.calls[1]["prompt"]
    assert (tmp_path / "attempt-02" / "changeset.json").is_file()
    assert build_candidate_index(candidate) == before
