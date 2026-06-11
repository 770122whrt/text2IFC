from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from text2ifc_contract.schema import load_draft_schema, load_schema_v2
from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "minimal.json"
V1_SCHEMA = ROOT / "schemas" / "bim-json" / "1.0" / "schema.json"
V1_SHA256 = "fdb96ce17a29c8ce63a4e750ec963700e85731d2bc7e2ae209aaf187cdbe7a60"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def issue_pairs(value):
    return {(issue.code, issue.path) for issue in validate_v2_document(value)}


def test_formal_minimal_document_validates_without_changing_v1() -> None:
    value = document()
    original = copy.deepcopy(value)

    assert validate_v2_document(value) == []
    assert value == original
    assert hashlib.sha256(V1_SCHEMA.read_bytes()).hexdigest() == V1_SHA256


def test_formal_schema_and_draft_schema_are_separate_local_draft_2020_12() -> None:
    formal = load_schema_v2()
    draft = load_draft_schema()

    assert formal["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert draft["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert formal["$id"] != draft["$id"]
    assert formal["properties"]["schema_version"]["const"] == "bim-json/2.0"
    assert draft["properties"]["draft_version"]["const"] == "bim-json-draft/1.0"


def test_formal_structure_requires_exact_version_schema_and_graph_fields() -> None:
    value = document()
    value.pop("schema_version")
    assert ("REQUIRED_FIELD", "/schema_version") in issue_pairs(value)

    value = document()
    value["ifc_schema"] = "IFC4"
    assert ("INVALID_ENUM", "/ifc_schema") in issue_pairs(value)

    value = document()
    value["unexpected"] = True
    assert ("UNSUPPORTED_FIELD", "/unexpected") in issue_pairs(value)


def test_entity_ids_are_unique_across_entities_and_relationships() -> None:
    value = document()
    value["relationships"].append(
        {
            "id": "wall-1",
            "ifc_class": "IfcRelVoidsElement",
            "attributes": {},
            "provenance": {"source": "test"},
        }
    )

    assert ("DUPLICATE_ID", "/relationships/0/id") in issue_pairs(value)
