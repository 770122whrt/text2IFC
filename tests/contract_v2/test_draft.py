from __future__ import annotations

import json
from pathlib import Path

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "minimal.json"


def formal():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def draft():
    partial = formal()
    partial["entities"][1]["attributes"]["ObjectPlacement"] = {
        "relative_to": "project-1"
    }
    return {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": partial,
        "missing_facts": [
            {
                "entity_id": "wall-1",
                "path": "/entities/1/attributes/ObjectPlacement/origin",
                "code": "MISSING_PLACEMENT_ORIGIN",
                "message": "Source position is unknown.",
            }
        ],
        "losses": [],
        "clarification_targets": [
            {
                "entity_id": "wall-1",
                "path": "/entities/1/attributes/ObjectPlacement/origin",
                "question": "What is the wall origin?",
            }
        ],
        "provenance": {"source": "test"},
    }


def pairs(issues):
    return {(issue.code, issue.path) for issue in issues}


def test_draft_envelope_validates_and_formal_loader_rejects_it() -> None:
    value = draft()

    assert validate_draft(value) == []
    assert ("INVALID_ENUM", "/schema_version") not in pairs(
        validate_v2_document(value)
    )
    assert validate_v2_document(value)


def test_draft_loader_rejects_formal_document_and_unlabeled_omissions() -> None:
    assert validate_draft(formal())

    value = draft()
    value["missing_facts"] = []
    assert ("UNDECLARED_OMISSION", "/missing_facts") in pairs(
        validate_draft(value)
    )


def test_missing_fact_paths_are_stable_and_addressable() -> None:
    value = draft()
    value["missing_facts"][0]["path"] = "/entities/99/missing"

    assert ("UNRESOLVED_DRAFT_PATH", "/missing_facts/0/path") in pairs(
        validate_draft(value)
    )
