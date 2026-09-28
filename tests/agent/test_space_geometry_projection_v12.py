"""Geometry facts must survive Brief -> Expected Facts -> geometry expectations."""
import copy
import math
import json

import pytest

from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def brief():
    return {"schema_version": "text2ifc/design-brief/1.0", "status": "ready", "known_facts": {
        "storeys": [{"id": "ground", "elevation_mm": -200, "spaces": [
            {"id": "room-a", "polygon": [[0,0],[3000,0],[3000,1000],[1000,1000],[1000,2000],[0,2000],[0,0]],
             "z_mm": [100, 2500]}]}, {"id": "reference-only", "elevation_mm": 3000}]}}


def derive(value, **kwargs):
    expected = build_expected_facts(case_id="independent", design_brief=value)
    return build_design_geometry_expectation(case_id="independent", design_brief=value, expected_facts=expected, **kwargs)


def test_polygon_z_survive_projection_and_do_not_invent_storey_height():
    value = brief(); original = copy.deepcopy(value)
    result = derive(value)
    assert result["complete"], result["unresolved"]
    assert result["spaces"]["room-a"]["bbox"] == {"x": [0,3], "y": [0,2], "z": [.1,2.5]}
    assert result["spaces"]["room-a"]["geometry_basis"] == "polygon_bounds_and_world_z"
    assert result["schema_version"] == "text2ifc/design-geometry-expectation/1.2"
    assert value == original


@pytest.mark.parametrize("z", [[2500,100], [100,100], [True,2500], [0,math.inf], [0,math.nan], [0]])
def test_invalid_explicit_z_cannot_fall_back_to_storey_height(z):
    value = brief(); floor = value["known_facts"]["storeys"][0]
    floor["net_height_mm"] = 3000; floor["spaces"][0]["z_mm"] = z
    result = derive(value)
    assert "room-a" not in result["spaces"]
    assert any(r["reason"] == "space_geometry_invalid_or_conflicting" for r in result["unresolved"])


@pytest.mark.parametrize("patch", [
    {"bounds": {"x": [0,9000], "y": [0,2000]}},
    {"height_mm": 9000},
    {"polygon": [[0,0],[3000,2000],[0,2000],[3000,0],[0,0]]},
    {"polygon": [[0,0],[1,1],[2,2]]},
])
def test_conflicting_or_invalid_space_geometry_is_not_silently_selected(patch):
    value = brief(); value["known_facts"]["storeys"][0]["spaces"][0].update(patch)
    result = derive(value)
    assert not result["spaces"] and not result["complete"]


def test_missing_space_height_still_blocks_without_fabricated_default():
    value = brief(); del value["known_facts"]["storeys"][0]["spaces"][0]["z_mm"]
    result = derive(value)
    assert not result["complete"] and not result["spaces"]


def test_old_v11_retains_historical_missing_geometry_result():
    result = derive(brief(), schema_version="text2ifc/design-geometry-expectation/1.1")
    assert not result["spaces"] and len(result["unresolved"]) == 3


def test_missing_height_blocks_inferred_interior_wall_but_not_explicit_room_z():
    value = brief(); value["known_facts"]["storeys"][0]["walls"] = {"interior": [
        {"id": "partition", "connects": ["room-a", "room-b"]}]}
    result = derive(value)
    assert "room-a" in result["spaces"]
    assert not result["complete"]
    assert any(r["reason"] in {"storey_elevation_or_net_height_missing", "explicit_wall_geometry_missing"} for r in result["unresolved"])


@pytest.mark.parametrize("bounds", [
    {"x": [True,3000], "y": [0,2000]},
    {"x": [0,3000], "y": [0,2000], "x_min": 10, "x_max": 3000, "y_min": 0, "y_max": 2000},
])
def test_bounds_validate_original_values_and_conflicting_aliases(bounds):
    value = brief(); room = value["known_facts"]["storeys"][0]["spaces"][0]
    room.pop("polygon"); room["bounds"] = bounds
    assert not derive(value)["complete"]


def test_space_projection_does_not_round_before_submillimetre_comparison():
    value = brief(); room = value["known_facts"]["storeys"][0]["spaces"][0]
    room["z_mm"] = [100.0004, 2500.0004]
    assert derive(value)["spaces"]["room-a"]["bbox"]["z"] == [100.0004/1000, 2500.0004/1000]


@pytest.mark.parametrize("invalid", [False, True])
def test_public_case_geometry_keeps_space_only_expectations(tmp_path, invalid):
    from text2ifc_agent.live_pipeline import _semantic_geometry_expectation_from_case
    value = brief()
    if invalid:
        value["known_facts"]["storeys"][0]["spaces"][0]["z_mm"] = [1,1]
    facts = build_expected_facts(case_id="independent", design_brief=value)
    (tmp_path / "design-brief.json").write_text(json.dumps(value), encoding="utf-8")
    (tmp_path / "expected-facts.json").write_text(json.dumps(facts), encoding="utf-8")
    result = _semantic_geometry_expectation_from_case(case_root=tmp_path, case_id="independent", candidate={"entities": []})
    assert result is not None
    assert result["schema_version"] == "text2ifc/design-geometry-expectation/1.2"
    if invalid:
        assert not result["complete"] and result["unresolved"]
    else:
        assert result["spaces"]["room-a"]["bbox"]["z"] == [.1,2.5]


@pytest.mark.parametrize("explicit", [False, True])
def test_legacy_dimension_only_request_retains_checks_but_invalid_location_cannot_fallback(tmp_path, explicit):
    from text2ifc_agent.live_pipeline import _semantic_geometry_expectation_from_case
    value = {"known_facts": {
        "space": {"shape": "rectangle", "length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
        "walls": {"count": 4, "enclosure": "closed", "thickness_mm": 300}}}
    if explicit:
        value["known_facts"]["space"]["z_mm"] = None
    facts = build_expected_facts(case_id="legacy", design_brief=value)
    (tmp_path / "design-brief.json").write_text(json.dumps(value), encoding="utf-8")
    (tmp_path / "expected-facts.json").write_text(json.dumps(facts), encoding="utf-8")
    result = _semantic_geometry_expectation_from_case(case_root=tmp_path, case_id="legacy", candidate={"entities": []})
    if explicit:
        assert result is not None and not result["complete"]
    else:
        assert result is None  # Existing dimension gate applies; no fabricated world location.
