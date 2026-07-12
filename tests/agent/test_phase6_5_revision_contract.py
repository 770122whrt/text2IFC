import importlib
import json

import pytest


def _revisions_module():
    try:
        return importlib.import_module("text2ifc_agent.revisions")
    except ModuleNotFoundError:
        pytest.fail("Phase 6.5 revision and scope contracts are not implemented")


def _candidate() -> dict:
    return {
        "schema_version": "bim-json/2.0",
        "entities": [
            {"id": "storey-1", "ifc_class": "IfcBuildingStorey", "attributes": {}},
            {"id": "wall-1", "ifc_class": "IfcWall", "attributes": {}},
        ],
        "relationships": [
            {
                "id": "rel-contained-wall-1",
                "ifc_class": "IfcRelContainedInSpatialStructure",
                "relating": "storey-1",
                "related": ["wall-1"],
            }
        ],
    }


def _expected_facts() -> dict:
    return {"schema_version": "text2ifc/expected-facts/1.0", "storeys": []}


def _revision(module, *, sequence: int = 0) -> dict:
    candidate = _candidate()
    expected = _expected_facts()
    return {
        "schema_version": "text2ifc/bim-json-revision/1.0",
        "revision_id": f"revision-{sequence:02d}",
        "sequence": sequence,
        "parent_revision_id": None if sequence == 0 else f"revision-{sequence - 1:02d}",
        "candidate_hash": module.hash_json_value(candidate),
        "expected_facts_hash": module.hash_json_value(expected),
        "component_hashes": {
            "storey-1": module.hash_json_value(candidate["entities"][0]),
            "wall-1": module.hash_json_value(candidate["entities"][1]),
            "rel-contained-wall-1": module.hash_json_value(candidate["relationships"][0]),
        },
        "source_route": "initial_generation" if sequence == 0 else "changeset",
        "artifacts": {"candidate": f"revisions/revision-{sequence:02d}/candidate.json"},
    }


def _scope() -> dict:
    return {
        "schema_version": "text2ifc/change-scope/1.0",
        "scope_id": "scope-revision-01",
        "base_revision_id": "revision-00",
        "source_issue_ids": ["issue-wall-geometry-001"],
        "entity_ids": ["wall-1"],
        "relationship_ids": ["rel-contained-wall-1"],
        "allowed_paths": {
            "wall-1": ["/attributes/ObjectPlacement/location"],
            "rel-contained-wall-1": ["/related"],
        },
        "dependencies": [
            {
                "target_id": "wall-1",
                "dependency_id": "rel-contained-wall-1",
                "relationship_type": "containment",
                "reason": "The wall containment may need to follow the corrected wall.",
            }
        ],
        "forbidden_ids": ["storey-1"],
    }


def test_revision_contract_binds_candidate_expected_facts_and_components():
    module = _revisions_module()
    candidate = _candidate()
    expected = _expected_facts()
    revision = _revision(module)

    issues = module.validate_revision_record(
        revision,
        candidate=candidate,
        expected_facts=expected,
    )

    assert issues == []


def test_revision_contract_rejects_stale_candidate_and_expected_facts_hashes():
    module = _revisions_module()
    revision = _revision(module)
    changed_candidate = _candidate()
    changed_candidate["entities"][1]["attributes"]["Name"] = "changed"
    changed_expected = _expected_facts()
    changed_expected["storeys"].append({"id": "storey-1"})

    issues = module.validate_revision_record(
        revision,
        candidate=changed_candidate,
        expected_facts=changed_expected,
    )

    assert {issue.code for issue in issues} == {
        "REVISION_CANDIDATE_HASH_MISMATCH",
        "REVISION_EXPECTED_FACTS_HASH_MISMATCH",
        "REVISION_COMPONENT_HASH_MISMATCH",
    }


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda value: value.pop("candidate_hash"), "REVISION_CONTRACT_ERROR"),
        (lambda value: value.update({"source_route": "replace_everything"}), "REVISION_CONTRACT_ERROR"),
        (lambda value: value.update({"sequence": -1}), "REVISION_CONTRACT_ERROR"),
        (lambda value: value.update({"parent_revision_id": "revision-parent"}), "REVISION_PARENT_CONFLICT"),
    ],
)
def test_revision_contract_rejects_invalid_records(mutate, code):
    module = _revisions_module()
    revision = _revision(module)
    mutate(revision)

    issues = module.validate_revision_record(revision)

    assert code in {issue.code for issue in issues}


def test_scope_contract_accepts_explicit_targets_paths_and_dependency_reasons():
    module = _revisions_module()

    issues = module.validate_change_scope(_scope())

    assert issues == []


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda value: value.update({"source_issue_ids": []}), "CHANGE_SCOPE_CONTRACT_ERROR"),
        (lambda value: value["entity_ids"].append("storey-1"), "CHANGE_SCOPE_FORBIDDEN_OVERLAP"),
        (lambda value: value["allowed_paths"].update({"unknown-wall": ["/attributes"]}), "CHANGE_SCOPE_UNKNOWN_PATH_TARGET"),
        (lambda value: value["dependencies"][0].update({"dependency_id": "unknown-rel"}), "CHANGE_SCOPE_UNKNOWN_DEPENDENCY"),
        (lambda value: value["dependencies"][0].update({"reason": ""}), "CHANGE_SCOPE_CONTRACT_ERROR"),
        (lambda value: value["entity_ids"].append("/entities/12"), "CHANGE_SCOPE_CONTRACT_ERROR"),
    ],
)
def test_scope_contract_rejects_ambiguous_or_unsafe_scope(mutate, code):
    module = _revisions_module()
    scope = _scope()
    mutate(scope)

    issues = module.validate_change_scope(scope)

    assert code in {issue.code for issue in issues}


def test_revision_and_scope_canonical_writes_do_not_mutate_inputs(tmp_path):
    module = _revisions_module()
    revision = _revision(module)
    scope = _scope()
    before_revision = json.loads(json.dumps(revision))
    before_scope = json.loads(json.dumps(scope))

    revision_path = module.write_revision_record(tmp_path / "revision.json", revision)
    scope_path = module.write_change_scope(tmp_path / "scope.json", scope)

    assert json.loads(revision_path.read_text(encoding="utf-8")) == revision
    assert json.loads(scope_path.read_text(encoding="utf-8")) == scope
    assert revision == before_revision
    assert scope == before_scope
