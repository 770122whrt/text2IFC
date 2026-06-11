import copy
import json
from pathlib import Path

import pytest

from text2ifc_contract.validation import validate_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract" / "fixtures" / "complete.json"


def _complete_document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _pairs(document):
    return [(issue.code, issue.path) for issue in validate_document(document)]


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    [
        (
            lambda doc: doc["site"].__setitem__("id", doc["project"]["id"]),
            "/site/id",
        ),
        (
            lambda doc: doc["storeys"][1].__setitem__(
                "id", doc["storeys"][0]["id"]
            ),
            "/storeys/1/id",
        ),
        (
            lambda doc: doc["elements"][1].__setitem__(
                "id", doc["elements"][0]["id"]
            ),
            "/elements/1/id",
        ),
        (
            lambda doc: doc["elements"][0].__setitem__(
                "id", doc["storeys"][0]["id"]
            ),
            "/elements/0/id",
        ),
    ],
)
def test_duplicate_ids_are_rejected_at_each_later_occurrence(
    mutation, expected_path
):
    document = _complete_document()
    mutation(document)

    assert ("DUPLICATE_ID", expected_path) in _pairs(document)


def test_unresolved_storey_reference_is_rejected_at_reference_path():
    document = _complete_document()
    document["elements"][0]["storey_id"] = "storey-missing"

    assert (
        "UNRESOLVED_STOREY_REFERENCE",
        "/elements/0/storey_id",
    ) in _pairs(document)


def test_multiple_semantic_issues_are_returned_in_deterministic_order():
    document = _complete_document()
    document["site"]["id"] = document["project"]["id"]
    document["elements"][0]["storey_id"] = "storey-missing"
    document["elements"][1]["id"] = document["elements"][0]["id"]

    issues = validate_document(document)

    assert [(issue.path, issue.code, issue.message) for issue in issues] == sorted(
        (issue.path, issue.code, issue.message) for issue in issues
    )
    assert _pairs(document) == [
        ("UNRESOLVED_STOREY_REFERENCE", "/elements/0/storey_id"),
        ("DUPLICATE_ID", "/elements/1/id"),
        ("DUPLICATE_ID", "/site/id"),
    ]


def test_semantic_validation_does_not_run_when_structure_is_invalid():
    document = _complete_document()
    document.pop("project")
    document["site"]["id"] = "building-001"
    document["elements"][0]["storey_id"] = "storey-missing"

    pairs = _pairs(document)

    assert ("REQUIRED_FIELD", "/project") in pairs
    assert all(
        code not in {"DUPLICATE_ID", "UNRESOLVED_STOREY_REFERENCE"}
        for code, _ in pairs
    )


def test_valid_document_has_no_semantic_issues_and_is_not_mutated():
    document = _complete_document()
    original = copy.deepcopy(document)

    assert validate_document(document) == []
    assert document == original
