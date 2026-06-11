from __future__ import annotations

import copy
import json
from pathlib import Path

from text2ifc_contract.migration_v2 import migrate_v1_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract" / "fixtures" / "complete.json"


def test_v1_migration_is_deterministic_preserving_and_never_fabricates_space() -> None:
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    original = copy.deepcopy(source)

    first = migrate_v1_document(source, "complete.json")
    second = migrate_v1_document(source, "complete.json")

    assert first == second
    assert source == original
    assert first["draft_version"] == "bim-json-draft/1.0"
    assert first["target_schema_version"] == "bim-json/2.0"
    entities = first["partial_document"]["entities"]
    assert len(entities) == 14
    assert {entity["id"] for entity in entities} == {
        source["project"]["id"],
        source["site"]["id"],
        source["building"]["id"],
        *(item["id"] for item in source["storeys"]),
        *(item["id"] for item in source["elements"]),
    }
    assert not any(entity["ifc_class"] == "IfcSpace" for entity in entities)
    assert not any(
        "origin" in entity.get("attributes", {}).get("ObjectPlacement", {})
        for entity in entities
    )


def test_v1_migration_lists_per_entity_placement_and_unknown_space_coverage() -> None:
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = migrate_v1_document(source, "complete.json")
    missing = result["missing_facts"]

    element_ids = {item["id"] for item in source["elements"]}
    placement_entity_ids = {
        item["entity_id"]
        for item in missing
        if item["code"] == "MISSING_OBJECT_PLACEMENT"
    }
    assert element_ids <= placement_entity_ids
    assert any(item["code"] == "UNKNOWN_SPACE_COVERAGE" for item in missing)

    by_id = {item["id"]: item for item in result["partial_document"]["entities"]}
    for element in source["elements"]:
        migrated = by_id[element["id"]]
        assert migrated["attributes"]["Representation"]["dimensions"] == element[
            "dimensions"
        ]
