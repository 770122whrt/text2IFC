import importlib
import json
from pathlib import Path

import pytest


FIXTURE = Path(__file__).resolve().parents[1] / "contract_v2" / "fixtures" / "minimal.json"


def _module():
    try:
        return importlib.import_module("text2ifc_agent.candidate_index")
    except ModuleNotFoundError:
        pytest.fail("Phase 6.5 candidate index is not implemented")


def _candidate() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_candidate_index_resolves_entities_and_relationships_by_stable_id():
    module = _module()
    candidate = _candidate()
    candidate["relationships"].append(
        {
            "id": "rel-wall-storey",
            "ifc_class": "IfcRelContainedInSpatialStructure",
            "attributes": {
                "RelatingStructure": "project-1",
                "RelatedElements": ["wall-1"],
            },
            "provenance": {"source": "test"},
        }
    )

    index = module.build_candidate_index(candidate)

    assert set(index["entities"]) == {"project-1", "wall-1"}
    assert set(index["relationships"]) == {"rel-wall-storey"}
    assert index["entities"]["wall-1"]["ifc_class"] == "IfcWall"
    assert index["relationships"]["rel-wall-storey"]["ifc_class"] == "IfcRelContainedInSpatialStructure"
    assert set(index["component_hashes"]) == {"project-1", "wall-1", "rel-wall-storey"}


def test_candidate_index_hashes_are_independent_of_collection_order():
    module = _module()
    first = _candidate()
    second = _candidate()
    second["entities"].reverse()

    first_index = module.build_candidate_index(first)
    second_index = module.build_candidate_index(second)

    assert first_index["component_hashes"] == second_index["component_hashes"]
    assert first_index["candidate_hash"] == second_index["candidate_hash"]


@pytest.mark.parametrize("collection", ["entities", "relationships"])
def test_candidate_index_rejects_duplicate_ids(collection):
    module = _module()
    candidate = _candidate()
    if collection == "relationships":
        candidate["relationships"] = [
            {"id": "duplicate", "ifc_class": "IfcRelVoidsElement", "attributes": {}},
            {"id": "duplicate", "ifc_class": "IfcRelFillsElement", "attributes": {}},
        ]
    else:
        candidate["entities"].append(dict(candidate["entities"][0]))

    with pytest.raises(module.CandidateIndexError, match="duplicate"):
        module.build_candidate_index(candidate)


def test_candidate_index_rejects_cross_collection_id_collisions():
    module = _module()
    candidate = _candidate()
    candidate["relationships"].append(
        {"id": "wall-1", "ifc_class": "IfcRelVoidsElement", "attributes": {}}
    )

    with pytest.raises(module.CandidateIndexError, match="both entity and relationship"):
        module.build_candidate_index(candidate)


def test_candidate_index_does_not_mutate_the_candidate():
    module = _module()
    candidate = _candidate()
    before = json.loads(json.dumps(candidate))

    module.build_candidate_index(candidate)

    assert candidate == before
