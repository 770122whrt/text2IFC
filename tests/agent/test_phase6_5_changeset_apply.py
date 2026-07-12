import importlib
import json
from pathlib import Path

import pytest

from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.revisions import hash_json_value


MINIMAL = Path(__file__).resolve().parents[1] / "contract_v2" / "fixtures" / "minimal.json"
COMPLETE = Path(__file__).resolve().parents[1] / "contract_v2" / "fixtures" / "complete.json"


def _module():
    try:
        return importlib.import_module("text2ifc_agent.changeset_apply")
    except ModuleNotFoundError:
        pytest.fail("Phase 6.5 immutable ChangeSet applicator is not implemented")


def _candidate(path: Path = MINIMAL) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_facts() -> dict:
    return {"schema_version": "text2ifc/expected-facts/1.0", "storeys": []}


def _revision(candidate: dict, expected_facts: dict) -> dict:
    index = build_candidate_index(candidate)
    return {
        "schema_version": "text2ifc/bim-json-revision/1.0",
        "revision_id": "revision-00",
        "sequence": 0,
        "parent_revision_id": None,
        "candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected_facts),
        "component_hashes": index["component_hashes"],
        "source_route": "initial_generation",
        "artifacts": {"candidate": "revisions/revision-00/candidate.json"},
    }


def _scope(*, entity_ids=None, relationship_ids=None, paths=None, forbidden_ids=None) -> dict:
    return {
        "schema_version": "text2ifc/change-scope/1.0",
        "scope_id": "scope-revision-01",
        "base_revision_id": "revision-00",
        "source_issue_ids": ["issue-wall-001"],
        "entity_ids": entity_ids or ["wall-1"],
        "relationship_ids": relationship_ids or [],
        "allowed_paths": paths or {"wall-1": ["/attributes/Name"]},
        "dependencies": [],
        "forbidden_ids": forbidden_ids or ["project-1"],
    }


def _changeset(candidate: dict, expected_facts: dict, *, operation=None) -> dict:
    index = build_candidate_index(candidate)
    return {
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "changeset_id": "changeset-revision-01",
        "base_revision_id": "revision-00",
        "base_candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected_facts),
        "source_issue_ids": ["issue-wall-001"],
        "scope_id": "scope-revision-01",
        "operations": [
            operation
            or {
                "operation_id": "operation-wall-name",
                "op": "update_entity",
                "target_id": "wall-1",
                "target_component_hash": index["component_hashes"]["wall-1"],
                "changes": {"/attributes/Name": "Corrected wall"},
                "evidence_refs": ["issue-wall-001:/expected"],
            }
        ],
    }


def _apply(module, candidate, changeset, scope, expected_facts):
    return module.apply_changeset(
        candidate=candidate,
        changeset=changeset,
        scope=scope,
        base_revision=_revision(candidate, expected_facts),
        expected_facts=expected_facts,
    )


def test_apply_changeset_updates_copy_and_creates_deterministic_revision():
    module = _module()
    candidate = _candidate()
    expected = _expected_facts()
    before = json.loads(json.dumps(candidate))
    changeset = _changeset(candidate, expected)

    first = _apply(module, candidate, changeset, _scope(), expected)
    second = _apply(module, candidate, changeset, _scope(), expected)

    assert first["valid"] is True
    assert first["issues"] == []
    assert first["candidate"] == second["candidate"]
    assert first["revision"]["candidate_hash"] == second["revision"]["candidate_hash"]
    assert first["revision"]["sequence"] == 1
    assert first["revision"]["parent_revision_id"] == "revision-00"
    wall = next(item for item in first["candidate"]["entities"] if item["id"] == "wall-1")
    assert wall["attributes"]["Name"] == "Corrected wall"
    assert candidate == before
    assert first["preservation"]["changed_ids"] == ["wall-1"]
    assert first["preservation"]["forbidden_drift_ids"] == []
    assert first["preservation"]["unrelated_component_preservation_rate"] == 1.0


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda candidate, changeset, scope: candidate["entities"][1]["attributes"].update({"Name": "stale"}), "CHANGESET_BASE_HASH_MISMATCH"),
        (lambda candidate, changeset, scope: changeset["operations"][0].update({"target_component_hash": "sha256:" + "0" * 64}), "CHANGESET_TARGET_HASH_MISMATCH"),
        (lambda candidate, changeset, scope: changeset["operations"][0].update({"changes": {"/attributes/Representation/depth": 1}}), "CHANGESET_SCOPE_VIOLATION"),
        (lambda candidate, changeset, scope: changeset["operations"][0].update({"target_id": "wall-missing"}), "CHANGESET_TARGET_NOT_FOUND"),
        (lambda candidate, changeset, scope: changeset.update({"scope_id": "scope-other"}), "CHANGESET_SCOPE_BINDING_MISMATCH"),
    ],
)
def test_apply_changeset_blocks_stale_or_unauthorized_operations(mutation, code):
    module = _module()
    candidate = _candidate()
    expected = _expected_facts()
    revision = _revision(candidate, expected)
    changeset = _changeset(candidate, expected)
    scope = _scope()
    mutation(candidate, changeset, scope)

    result = module.apply_changeset(
        candidate=candidate,
        changeset=changeset,
        scope=scope,
        base_revision=revision,
        expected_facts=expected,
    )

    assert result["valid"] is False
    assert result["candidate"] is None
    assert code in {issue["code"] for issue in result["issues"]}


def test_apply_changeset_adds_and_removes_entities_by_id():
    module = _module()
    candidate = _candidate()
    expected = _expected_facts()
    door = {
        "id": "door-new",
        "ifc_class": "IfcDoor",
        "attributes": {
            "Name": "New door",
            "ObjectPlacement": {
                "relative_to": "project-1",
                "origin": [0, 0, 0],
                "axis": [0, 0, 1],
                "ref_direction": [1, 0, 0],
            },
            "Representation": {
                "kind": "extruded_profile",
                "profile": {"kind": "rectangle", "x": 900, "y": 100},
                "depth": 2100,
                "direction": [0, 0, 1],
            },
        },
        "property_sets": {},
        "provenance": {"source": "issue-wall-001"},
    }
    add = {
        "operation_id": "operation-add-door",
        "op": "add_entity",
        "target_id": "door-new",
        "value": door,
        "evidence_refs": ["issue-wall-001:/expected"],
    }
    add_scope = _scope(
        entity_ids=["door-new"],
        paths={"door-new": ["/attributes"]},
        forbidden_ids=["project-1", "wall-1"],
    )

    added = _apply(module, candidate, _changeset(candidate, expected, operation=add), add_scope, expected)

    assert added["valid"] is True
    assert "door-new" in {item["id"] for item in added["candidate"]["entities"]}

    added_candidate = added["candidate"]
    remove = {
        "operation_id": "operation-remove-door",
        "op": "remove_entity",
        "target_id": "door-new",
        "target_component_hash": build_candidate_index(added_candidate)["component_hashes"]["door-new"],
        "evidence_refs": ["issue-wall-001:/actual"],
    }
    remove_changeset = _changeset(added_candidate, expected, operation=remove)
    remove_changeset["base_revision_id"] = added["revision"]["revision_id"]
    remove_scope = _scope(
        entity_ids=["door-new"],
        paths={"door-new": ["/attributes"]},
        forbidden_ids=["project-1", "wall-1"],
    )
    remove_scope["base_revision_id"] = added["revision"]["revision_id"]

    removed = module.apply_changeset(
        candidate=added_candidate,
        changeset=remove_changeset,
        scope=remove_scope,
        base_revision=added["revision"],
        expected_facts=expected,
    )

    assert removed["valid"] is True
    assert "door-new" not in {item["id"] for item in removed["candidate"]["entities"]}


def test_apply_changeset_rejects_implicit_cascade_delete():
    module = _module()
    candidate = _candidate(COMPLETE)
    expected = _expected_facts()
    index = build_candidate_index(candidate)
    remove = {
        "operation_id": "operation-remove-wall",
        "op": "remove_entity",
        "target_id": "wall-1",
        "target_component_hash": index["component_hashes"]["wall-1"],
        "evidence_refs": ["issue-wall-001:/actual"],
    }
    scope = _scope(
        entity_ids=["wall-1"],
        paths={"wall-1": ["/attributes"]},
        forbidden_ids=sorted(set(index["component_hashes"]) - {"wall-1"}),
    )

    result = _apply(module, candidate, _changeset(candidate, expected, operation=remove), scope, expected)

    assert result["valid"] is False
    assert result["candidate"] is None
    assert "CHANGESET_DEPENDENCY_VIOLATION" in {issue["code"] for issue in result["issues"]}


def test_apply_changeset_rejects_a_composed_candidate_that_is_not_formal():
    module = _module()
    candidate = _candidate()
    expected = _expected_facts()
    invalid = _changeset(candidate, expected)
    invalid["operations"][0]["changes"] = {
        "/attributes/ObjectPlacement/relative_to": "missing-parent"
    }
    scope = _scope(paths={"wall-1": ["/attributes/ObjectPlacement/relative_to"]})

    result = _apply(module, candidate, invalid, scope, expected)

    assert result["valid"] is False
    assert result["candidate"] is None
    assert "CHANGESET_CANDIDATE_INVALID" in {issue["code"] for issue in result["issues"]}
