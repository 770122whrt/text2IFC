from __future__ import annotations

import ifcopenshell
import ifcopenshell.util.placement
import pytest

from text2ifc_contract.placement import world_transform_for

from .conftest import HXP


def _partial(result):
    document = result.draft["partial_document"] if result.draft else result.document
    assert document is not None
    return document


def test_exact_wall_class_local_placement_and_world_transform(hxp_result) -> None:
    document = _partial(hxp_result)
    walls = [
        item
        for item in document["entities"]
        if item["ifc_class"] == "IfcWallStandardCase"
    ]
    assert len(walls) == 34
    wall = next(item for item in walls if item["global_id"] == "226kTvWe52dBaVNzWNVUTS")
    assert wall["attributes"]["ObjectPlacement"]["relative_to"]

    source = ifcopenshell.open(str(HXP))
    source_wall = source.by_guid(wall["global_id"])
    expected = ifcopenshell.util.placement.get_local_placement(
        source_wall.ObjectPlacement
    )
    actual = world_transform_for(document, wall["id"])
    assert [row[3] for row in actual[:3]] == pytest.approx(
        expected[:3, 3], abs=1.0
    )


def test_extrusion_position_and_void_fill_endpoints_are_preserved(hxp_result) -> None:
    document = _partial(hxp_result)
    opening = next(
        item
        for item in document["entities"]
        if item.get("global_id") == "0BxgxoBvf7SuWh1Ua00iQW"
    )
    position = opening["attributes"]["Representation"]["position"]
    assert position["origin"] == pytest.approx(
        [1327.053521, 208.848496, 1380.0], abs=1e-6
    )

    by_global_id = {
        item.get("global_id"): item["id"] for item in document["entities"]
    }
    void = next(
        item
        for item in document["relationships"]
        if item.get("global_id") == "08eLF8nmP8MRT$q8WO66aa"
    )
    fill = next(
        item
        for item in document["relationships"]
        if item.get("global_id") == "0nM7SC9Bn6yxMy1XxvLwY4"
    )
    assert void["attributes"] == {
        "RelatingBuildingElement": by_global_id["2R3hYUonf5OxYPUpi0xGyt"],
        "RelatedOpeningElement": by_global_id["0BxgxoBvf7SuWh1Ua00iQW"],
    }
    assert fill["attributes"] == {
        "RelatingOpeningElement": by_global_id["37teTCsZT7Qe4JdU61Otbq"],
        "RelatedBuildingElement": by_global_id["37teTCsZT7Qe4JdVA1Otbq"],
    }
