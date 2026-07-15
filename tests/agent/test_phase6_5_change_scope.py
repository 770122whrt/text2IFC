import importlib

import pytest


def _module():
    try:
        return importlib.import_module("text2ifc_agent.change_scope")
    except ModuleNotFoundError:
        pytest.fail("Phase 6.5 deterministic dependency scope is not implemented")


def _entity(entity_id: str, ifc_class: str) -> dict:
    return {"id": entity_id, "ifc_class": ifc_class, "attributes": {}}


def _relationship(relationship_id: str, ifc_class: str, **attributes) -> dict:
    return {"id": relationship_id, "ifc_class": ifc_class, "attributes": attributes}


def _opening_candidate() -> dict:
    return {
        "entities": [
            _entity("storey-1", "IfcBuildingStorey"),
            _entity("wall-1", "IfcWall"),
            _entity("opening-1", "IfcOpeningElement"),
            _entity("door-1", "IfcDoor"),
            _entity("wall-unrelated", "IfcWall"),
        ],
        "relationships": [
            _relationship(
                "void-1",
                "IfcRelVoidsElement",
                RelatingBuildingElement="wall-1",
                RelatedOpeningElement="opening-1",
            ),
            _relationship(
                "fill-1",
                "IfcRelFillsElement",
                RelatingOpeningElement="opening-1",
                RelatedBuildingElement="door-1",
            ),
            _relationship(
                "containment-1",
                "IfcRelContainedInSpatialStructure",
                RelatingStructure="storey-1",
                RelatedElements=["wall-1", "wall-unrelated"],
            ),
        ],
    }


def _issue(issue_id: str, actual_ref: str) -> dict:
    return {
        "issue_id": issue_id,
        "actual_ref": actual_ref,
        "expected_fact_ref": "expected-facts:/walls/wall-1",
        "evidence": "The named component failed a deterministic geometry gate.",
    }


def test_scope_derives_host_opening_filling_and_containment_closure():
    module = _module()

    result = module.derive_change_scope(
        candidate=_opening_candidate(),
        issues=[_issue("issue-wall-001", "entity:wall-1#/attributes/Representation")],
        scope_id="scope-revision-01",
        base_revision_id="revision-00",
    )

    assert result["issues"] == []
    scope = result["scope"]
    assert set(scope["entity_ids"]) == {"storey-1", "wall-1", "opening-1", "door-1"}
    assert set(scope["relationship_ids"]) == {"void-1", "fill-1", "containment-1"}
    assert scope["allowed_paths"]["wall-1"] == ["/attributes/Representation"]
    assert scope["allowed_paths"]["void-1"] == ["/attributes"]
    assert scope["allowed_paths"]["fill-1"] == ["/attributes"]
    assert scope["allowed_paths"]["containment-1"] == ["/attributes"]
    assert scope["forbidden_ids"] == ["wall-unrelated"]
    assert all(item["reason"] for item in scope["dependencies"])


def test_scope_uses_explicit_stair_opening_hint_without_guessing_coordinates():
    module = _module()
    candidate = {
        "entities": [
            _entity("stair-1", "IfcStair"),
            _entity("flight-1", "IfcStairFlight"),
            _entity("slab-2", "IfcSlab"),
            _entity("opening-stair", "IfcOpeningElement"),
            _entity("wall-unrelated", "IfcWall"),
        ],
        "relationships": [
            _relationship(
                "aggregate-stair",
                "IfcRelAggregates",
                RelatingObject="stair-1",
                RelatedObjects=["flight-1"],
            ),
            _relationship(
                "void-slab-stair",
                "IfcRelVoidsElement",
                RelatingBuildingElement="slab-2",
                RelatedOpeningElement="opening-stair",
            ),
        ],
    }

    result = module.derive_change_scope(
        candidate=candidate,
        issues=[_issue("issue-stair-001", "entity:stair-1#/attributes/ObjectPlacement")],
        scope_id="scope-revision-01",
        base_revision_id="revision-00",
        dependency_hints=[
            {
                "target_id": "stair-1",
                "dependency_id": "opening-stair",
                "relationship_type": "stair_opening",
                "reason": "Expected facts bind the stair endpoint to this slab opening.",
                "allowed_paths": ["/attributes/ObjectPlacement", "/attributes/Representation"],
            }
        ],
    )

    assert result["issues"] == []
    scope = result["scope"]
    assert set(scope["entity_ids"]) == {"stair-1", "flight-1", "slab-2", "opening-stair"}
    assert set(scope["relationship_ids"]) == {"aggregate-stair", "void-slab-stair"}
    assert scope["allowed_paths"]["opening-stair"] == [
        "/attributes/ObjectPlacement",
        "/attributes/Representation",
    ]
    assert "wall-unrelated" in scope["forbidden_ids"]


def test_scope_blocks_array_index_issue_refs_instead_of_broadening_scope():
    module = _module()

    result = module.derive_change_scope(
        candidate=_opening_candidate(),
        issues=[_issue("issue-index-001", "/entities/12/attributes/Representation")],
        scope_id="scope-revision-01",
        base_revision_id="revision-00",
    )

    assert result["scope"] is None
    assert {issue["code"] for issue in result["issues"]} == {"CHANGESET_TARGET_UNRESOLVED"}


def test_scope_blocks_unknown_stable_ids_and_invalid_dependency_hints():
    module = _module()

    result = module.derive_change_scope(
        candidate=_opening_candidate(),
        issues=[_issue("issue-wall-001", "entity:missing-wall#/attributes")],
        scope_id="scope-revision-01",
        base_revision_id="revision-00",
        dependency_hints=[
            {
                "target_id": "missing-wall",
                "dependency_id": "missing-opening",
                "relationship_type": "stair_opening",
                "reason": "Unknown hint must not authorize model-wide changes.",
            }
        ],
    )

    assert result["scope"] is None
    assert {issue["code"] for issue in result["issues"]} == {
        "CHANGESET_TARGET_UNRESOLVED",
        "CHANGESET_DEPENDENCY_UNRESOLVED",
    }


def test_scope_output_is_deterministic_for_reordered_candidate_collections():
    module = _module()
    first = _opening_candidate()
    second = _opening_candidate()
    second["entities"].reverse()
    second["relationships"].reverse()
    kwargs = {
        "issues": [_issue("issue-wall-001", "entity:wall-1#/attributes/Representation")],
        "scope_id": "scope-revision-01",
        "base_revision_id": "revision-00",
    }

    first_scope = module.derive_change_scope(candidate=first, **kwargs)["scope"]
    second_scope = module.derive_change_scope(candidate=second, **kwargs)["scope"]

    assert first_scope == second_scope
