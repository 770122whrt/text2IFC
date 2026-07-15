import json

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.changeset_stage import run_changeset_stage
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.revisions import hash_json_value


class RecordingProvider:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def generate_live(self, *, session_id, prompt, schema, state):
        self.calls.append(
            {"session_id": session_id, "prompt": prompt, "schema": schema, "state": state}
        )
        text = json.dumps(self.payload, ensure_ascii=False)
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="fake",
            http_status=200,
            request={"model": "fake", "messages": [{"role": "user", "content": prompt}]},
            response={
                "id": "response-changeset-001",
                "model": "fake",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
            events=(),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "fake", "response_id": "response-changeset-001"},
            ),
        )


def _candidate():
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            {
                "id": "project-a",
                "ifc_class": "IfcProject",
                "attributes": {"Name": "Project"},
                "property_sets": {},
                "provenance": {"source": "test"},
            },
            {
                "id": "wall-a",
                "ifc_class": "IfcWall",
                "attributes": {"Name": "Wrong"},
                "property_sets": {},
                "provenance": {"source": "test"},
            },
        ],
        "relationships": [],
        "provenance": {"source": "test"},
    }


def _expected():
    return {"schema_version": "text2ifc/expected-facts/1.0", "walls": [{"id": "wall-a"}]}


def _revision(candidate, expected):
    index = build_candidate_index(candidate)
    return {
        "revision_id": "revision-00",
        "candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected),
    }


def _scope():
    return {
        "schema_version": "text2ifc/change-scope/1.0",
        "scope_id": "scope-revision-01",
        "base_revision_id": "revision-00",
        "source_issue_ids": ["issue-wall-001"],
        "entity_ids": ["wall-a"],
        "relationship_ids": [],
        "allowed_paths": {"wall-a": ["/attributes/Name"]},
        "dependencies": [],
        "forbidden_ids": ["project-a"],
    }


def _issues():
    return [
        {
            "issue_id": "issue-wall-001",
            "actual_ref": "entity:wall-a#/attributes/Name",
            "expected": "Correct",
            "actual": "Wrong",
        }
    ]


def _changeset(candidate, expected):
    index = build_candidate_index(candidate)
    return {
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "changeset_id": "changeset-revision-01",
        "base_revision_id": "revision-00",
        "base_candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected),
        "source_issue_ids": ["issue-wall-001"],
        "scope_id": "scope-revision-01",
        "operations": [
            {
                "operation_id": "operation-wall-name",
                "op": "update_entity",
                "target_id": "wall-a",
                "target_component_hash": index["component_hashes"]["wall-a"],
                "changes": {"/attributes/Name": "Correct"},
                "evidence_refs": ["issue-wall-001:/expected"],
            }
        ],
    }


def _run(tmp_path, provider):
    candidate = _candidate()
    expected = _expected()
    return run_changeset_stage(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-a",
        call_index=1,
        user_request="修正墙名称。",
        conversation=[{"role": "user", "content": "名称应为Correct"}],
        design_brief={"status": "ready", "known_facts": {"wall_name": "Correct"}},
        expected_facts=expected,
        candidate=candidate,
        base_revision=_revision(candidate, expected),
        scope=_scope(),
        issues=_issues(),
        trace_level="debug",
    )


def test_changeset_stage_sends_only_scoped_components_and_writes_live_evidence(tmp_path):
    candidate = _candidate()
    expected = _expected()
    provider = RecordingProvider(_changeset(candidate, expected))

    result = _run(tmp_path, provider)

    assert result["valid"] is True
    assert result["classification"] == "changeset"
    assert result["response_id"] == "response-changeset-001"
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call["state"] == {
        "case_id": "case-a",
        "stage": "changeset",
        "call_index": 1,
    }
    assert call["schema"]["title"] == "text2IFC BIM JSON ChangeSet 1.0"
    renderer = json.loads((tmp_path / "prompt-render-input.json").read_text(encoding="utf-8"))
    assert set(renderer["SCOPED_COMPONENTS"]) == {"wall-a"}
    assert "project-a" not in json.dumps(renderer["SCOPED_COMPONENTS"])
    assert (tmp_path / "changeset.json").is_file()
    assert (tmp_path / "response.raw.json").is_file()
    assert (tmp_path / "metrics.json").is_file()


def test_changeset_stage_accepts_canonical_draft_instead_of_inventing_facts(tmp_path):
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {"entities": {"wall-a": {"attributes": {}}}},
        "missing_facts": [
            {
                "entity_id": "wall-a",
                "path": "/entities/wall-a/attributes/Name",
                "code": "MISSING_USER_FACT",
                "message": "User fact is missing.",
            }
        ],
        "losses": [],
        "clarification_targets": [
            {
                "entity_id": "wall-a",
                "path": "/entities/wall-a/attributes/Name",
                "question": "墙名称是什么？",
            }
        ],
        "provenance": {"source": "test"},
    }
    provider = RecordingProvider(draft)

    result = _run(tmp_path, provider)

    assert result["valid"] is True
    assert result["classification"] == "draft"
    assert (tmp_path / "draft.json").is_file()
    assert not (tmp_path / "changeset.json").exists()


def test_changeset_stage_blocks_full_bim_json_replacement(tmp_path):
    provider = RecordingProvider(_candidate())

    result = _run(tmp_path, provider)

    assert result["valid"] is False
    assert result["classification"] == "invalid"
    assert "CHANGESET_OUTPUT_CONTRACT_ERROR" in {
        issue["code"] for issue in result["diagnostics"]
    }
    assert not (tmp_path / "changeset.json").exists()


def test_changeset_stage_blocks_stale_model_binding_before_application(tmp_path):
    candidate = _candidate()
    expected = _expected()
    stale = _changeset(candidate, expected)
    stale["base_candidate_hash"] = "sha256:" + "0" * 64
    provider = RecordingProvider(stale)

    result = _run(tmp_path, provider)

    assert result["valid"] is False
    assert result["classification"] == "invalid"
    assert "CHANGESET_OUTPUT_BINDING_ERROR" in {
        issue["code"] for issue in result["diagnostics"]
    }


def test_changeset_stage_binds_malformed_system_hash_and_preserves_raw_value(tmp_path):
    candidate = _candidate()
    expected = _expected()
    payload = _changeset(candidate, expected)
    malformed_hash = payload["expected_facts_hash"][:-1]
    payload["expected_facts_hash"] = malformed_hash
    provider = RecordingProvider(payload)

    result = _run(tmp_path, provider)

    assert result["valid"] is True
    accepted = json.loads((tmp_path / "changeset.json").read_text(encoding="utf-8"))
    raw_parsed = json.loads(
        (tmp_path / "provider-parsed-output.json").read_text(encoding="utf-8")
    )
    validation = json.loads((tmp_path / "validation.json").read_text(encoding="utf-8"))
    assert accepted["expected_facts_hash"] == hash_json_value(expected)
    assert raw_parsed["expected_facts_hash"] == malformed_hash
    assert validation["normalizations"] == [
        {
            "code": "CONTROL_FIELD_BOUND",
            "path": "/expected_facts_hash",
            "message": "Malformed system control field was bound to the authorized value.",
        }
    ]


def test_changeset_stage_accepts_nonempty_authorized_issue_subset(tmp_path):
    candidate = _candidate()
    expected = _expected()
    payload = _changeset(candidate, expected)
    provider = RecordingProvider(payload)
    scope = _scope()
    scope["source_issue_ids"].append("issue-wall-002")

    result = run_changeset_stage(
        provider=provider,
        output_dir=tmp_path,
        case_id="case-a",
        call_index=1,
        user_request="Fix the named wall.",
        conversation=[{"role": "user", "content": "Fix issue-wall-001 first."}],
        design_brief={"status": "ready", "known_facts": {"wall_name": "Correct"}},
        expected_facts=expected,
        candidate=candidate,
        base_revision=_revision(candidate, expected),
        scope=scope,
        issues=_issues(),
        trace_level="debug",
    )

    assert result["valid"] is True


def test_changeset_stage_rejects_issue_outside_authorized_scope(tmp_path):
    candidate = _candidate()
    expected = _expected()
    payload = _changeset(candidate, expected)
    payload["source_issue_ids"] = ["issue-unknown"]
    payload["operations"][0]["evidence_refs"] = ["issue-unknown:/expected"]
    provider = RecordingProvider(payload)

    result = _run(tmp_path, provider)

    assert result["valid"] is False
    assert "CHANGESET_OUTPUT_BINDING_ERROR" in {
        issue["code"] for issue in result["diagnostics"]
    }
