import copy
from pathlib import Path

import ifcopenshell.util.placement
import pytest

from text2ifc_compiler import (
    compile_document,
    identity_map,
    measure_element_dimensions,
    open_ifc,
    verify_ifc,
)


IFC_CLASS_BY_KIND = {
    "wall": "IfcWall",
    "column": "IfcColumn",
    "beam": "IfcBeam",
    "slab": "IfcSlab",
    "door": "IfcDoor",
    "window": "IfcWindow",
    "stair": "IfcStair",
    "stair_flight": "IfcStairFlight",
    "roof": "IfcRoof",
}

EXPECTED_DIMENSIONS = {
    "wall-001": {"length": 5000.0, "thickness": 240.0, "height": 3000.0},
    "column-001": {"width": 400.0, "depth": 400.0, "height": 3000.0},
    "beam-001": {"length": 5000.0, "width": 300.0, "height": 500.0},
    "slab-001": {"length": 8000.0, "width": 6000.0, "thickness": 200.0},
    "door-001": {"width": 900.0, "height": 2100.0},
    "window-001": {"width": 1200.0, "height": 1500.0},
    "stair-001": {"length": 4000.0, "width": 1200.0, "height": 3000.0},
    "stair-flight-001": {"run": 3000.0, "width": 1200.0, "rise": 1500.0},
    "roof-001": {"length": 8000.0, "width": 6000.0, "thickness": 300.0},
}


def _placement_x_by_bim_id(model) -> dict[str, float]:
    mapping = identity_map(model)
    result = {}
    for bim_json_id, global_id in mapping.items():
        entity = model.by_guid(global_id)
        if not entity.is_a("IfcElement"):
            continue
        assert entity.ObjectPlacement is not None
        matrix = ifcopenshell.util.placement.get_local_placement(
            entity.ObjectPlacement
        )
        result[bim_json_id] = float(matrix[0, 3])
    return result


def _expected_x_positions(document: dict) -> dict[str, float]:
    x_dimension_by_kind = {
        "wall": "length",
        "column": "width",
        "beam": "length",
        "slab": "length",
        "door": "width",
        "window": "width",
        "stair": "length",
        "stair_flight": "run",
        "roof": "length",
    }
    offset_mm = 0.0
    result: dict[str, float] = {}
    for element in document["elements"]:
        result[element["id"]] = offset_mm
        offset_mm += (
            element["dimensions"][x_dimension_by_kind[element["kind"]]]
            + 1000.0
        )
    return result


def test_all_family_counts_and_dimensions_are_recovered_within_one_mm(
    complete_document: dict, tmp_path: Path
) -> None:
    output = tmp_path / "geometry.ifc"
    result = compile_document(complete_document, output)
    assert result.success
    model = open_ifc(output)

    assert {
        ifc_class: len(model.by_type(ifc_class))
        for ifc_class in IFC_CLASS_BY_KIND.values()
    } == {ifc_class: 1 for ifc_class in IFC_CLASS_BY_KIND.values()}

    for bim_json_id, expected in EXPECTED_DIMENSIONS.items():
        measured = measure_element_dimensions(model, bim_json_id)
        assert measured.keys() == expected.keys()
        for name, expected_value in expected.items():
            assert measured[name] == pytest.approx(expected_value, abs=1.0)

    assert verify_ifc(model) == ()


def test_synthetic_placements_are_complete_stable_and_source_ordered(
    complete_document: dict, tmp_path: Path
) -> None:
    first = tmp_path / "first.ifc"
    second = tmp_path / "second.ifc"
    compile_document(complete_document, first)
    compile_document(complete_document, second)

    first_positions = _placement_x_by_bim_id(open_ifc(first))
    second_positions = _placement_x_by_bim_id(open_ifc(second))
    expected_positions = _expected_x_positions(complete_document)

    assert first_positions == second_positions == expected_positions
    assert len(set(first_positions.values())) == len(
        complete_document["elements"]
    )


def test_single_family_document_creates_no_other_element_classes(
    complete_document: dict, tmp_path: Path
) -> None:
    document = copy.deepcopy(complete_document)
    document["elements"] = [
        element
        for element in document["elements"]
        if element["kind"] == "wall"
    ]
    output = tmp_path / "wall-only.ifc"

    result = compile_document(document, output)
    assert result.success
    model = open_ifc(output)

    assert len(model.by_type("IfcWall")) == 1
    for kind, ifc_class in IFC_CLASS_BY_KIND.items():
        if kind != "wall":
            assert model.by_type(ifc_class) == []


def test_synthetic_placements_do_not_overlap_long_elements(
    complete_document: dict, tmp_path: Path
) -> None:
    document = copy.deepcopy(complete_document)
    first_wall = copy.deepcopy(document["elements"][0])
    second_wall = copy.deepcopy(first_wall)
    first_wall["id"] = "wall-long-a"
    first_wall["dimensions"]["length"] = 15_000.0
    second_wall["id"] = "wall-long-b"
    second_wall["dimensions"]["length"] = 20_000.0
    document["elements"] = [first_wall, second_wall]
    output = tmp_path / "long-walls.ifc"

    result = compile_document(document, output)
    assert result.success
    positions = _placement_x_by_bim_id(open_ifc(output))

    assert (
        positions["wall-long-a"] + first_wall["dimensions"]["length"]
        < positions["wall-long-b"]
    )
