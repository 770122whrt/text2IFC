import importlib
import json

import pytest


def _changesets_module():
    try:
        return importlib.import_module("text2ifc_agent.changesets")
    except ModuleNotFoundError:
        pytest.fail("Phase 6.5 ChangeSet contract is not implemented")


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _valid_changeset(*, operation: dict | None = None) -> dict:
    return {
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "changeset_id": "changeset-revision-01",
        "base_revision_id": "revision-00",
        "base_candidate_hash": _hash("a"),
        "expected_facts_hash": _hash("b"),
        "source_issue_ids": ["issue-geometry-001"],
        "scope_id": "scope-revision-01",
        "operations": [
            operation
            or {
                "operation_id": "operation-001",
                "op": "update_entity",
                "target_id": "stair-storey-1-to-2",
                "target_component_hash": _hash("c"),
                "changes": {"/attributes/Representation/depth": 3000},
                "evidence_refs": ["issue-geometry-001:/expected"],
            }
        ],
    }


@pytest.mark.parametrize(
    "operation",
    [
        {
            "operation_id": "operation-add-entity",
            "op": "add_entity",
            "target_id": "wall-storey-2-east",
            "value": {
                "id": "wall-storey-2-east",
                "ifc_class": "IfcWall",
                "provenance": {"source": "issue-geometry-001"},
            },
            "evidence_refs": ["issue-geometry-001:/expected"],
        },
        {
            "operation_id": "operation-update-relationship",
            "op": "update_relationship",
            "target_id": "rel-window-host",
            "target_component_hash": _hash("d"),
            "changes": {"/relating": "wall-storey-2-east"},
            "evidence_refs": ["issue-geometry-001:/expected"],
        },
        {
            "operation_id": "operation-remove-entity",
            "op": "remove_entity",
            "target_id": "door-invented-extra",
            "target_component_hash": _hash("e"),
            "evidence_refs": ["issue-geometry-001:/actual"],
        },
    ],
)
def test_changeset_contract_accepts_id_addressed_operations(operation):
    module = _changesets_module()

    issues = module.validate_changeset(_valid_changeset(operation=operation))

    assert issues == []


def test_changeset_contract_has_a_meta_valid_local_schema():
    module = _changesets_module()

    schema = module.load_changeset_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].startswith("https://text2ifc.local/")
    assert "https://" not in json.dumps(schema.get("$defs", {}))


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (lambda value: value.update({"schema_version": "bim-json/2.0"}), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value.pop("base_candidate_hash"), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value.update({"source_issue_ids": []}), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value["operations"][0].update({"op": "replace_document"}), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value["operations"][0].update({"target_id": "/entities/12"}), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value["operations"][0].update({"changes": {}}), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value["operations"][0].update({"evidence_refs": []}), "SCHEMA_VALIDATION_ERROR"),
        (lambda value: value["operations"][0].update({"changes": {"/0/name": "bad"}}), "SCHEMA_VALIDATION_ERROR"),
    ],
)
def test_changeset_contract_rejects_invalid_shapes(mutate, expected_code):
    module = _changesets_module()
    document = _valid_changeset()
    mutate(document)

    issues = module.validate_changeset(document)

    assert issues
    assert expected_code in {issue.code for issue in issues}


def test_changeset_contract_rejects_duplicate_operation_ids_and_targets():
    module = _changesets_module()
    document = _valid_changeset()
    duplicate = dict(document["operations"][0])
    duplicate["operation_id"] = "operation-002"
    document["operations"].append(duplicate)

    issues = module.validate_changeset(document)

    assert {issue.code for issue in issues} == {"DUPLICATE_CHANGESET_TARGET"}


def test_changeset_contract_rejects_evidence_from_an_undeclared_issue():
    module = _changesets_module()
    document = _valid_changeset()
    document["operations"][0]["evidence_refs"] = ["issue-other:/expected"]

    issues = module.validate_changeset(document)

    assert {issue.code for issue in issues} == {"UNDECLARED_CHANGESET_EVIDENCE"}


def test_changeset_contract_rejects_empty_provenance_on_added_component():
    module = _changesets_module()
    operation = {
        "operation_id": "operation-add-entity",
        "op": "add_entity",
        "target_id": "wall-storey-1-south",
        "value": {
            "id": "wall-storey-1-south",
            "ifc_class": "IfcWall",
            "attributes": {},
            "property_sets": {},
            "provenance": {},
        },
        "evidence_refs": ["issue-geometry-001:/expected"],
    }

    issues = module.validate_changeset(_valid_changeset(operation=operation))

    assert [(issue.code, issue.path) for issue in issues] == [
        ("EMPTY_CHANGESET_PROVENANCE", "/operations/0/value/provenance")
    ]


def test_changeset_canonical_serialization_is_deterministic_and_non_mutating():
    module = _changesets_module()
    document = _valid_changeset()
    original = json.loads(json.dumps(document))

    first = module.canonical_changeset_json(document)
    second = module.canonical_changeset_json(document)

    assert first == second
    assert first.endswith("\n")
    assert document == original
