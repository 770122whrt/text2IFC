from pathlib import Path

import ifcopenshell.util.element
import pytest

from text2ifc_compiler import (
    compile_document,
    containment_map,
    hierarchy_snapshot,
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


def _psets(model, global_id: str) -> dict:
    return ifcopenshell.util.element.get_psets(model.by_guid(global_id))


def test_complete_fixture_satisfies_every_phase_two_contract(
    complete_document: dict,
    canonical_ids: set[str],
    tmp_path: Path,
) -> None:
    output = tmp_path / "complete-phase-two.ifc"

    result = compile_document(complete_document, output)

    assert result.success
    model = open_ifc(output)
    assert model.schema == "IFC2X3"
    assert verify_ifc(model) == ()

    assert hierarchy_snapshot(model) == {
        "project": {
            "id": "project-001",
            "name": "Complete contract project",
        },
        "site": {"id": "site-001", "name": "Main site"},
        "building": {"id": "building-001", "name": "Main building"},
        "storeys": [
            {"id": "storey-001", "name": "Ground floor", "elevation": 0.0},
            {
                "id": "storey-002",
                "name": "First floor",
                "elevation": 3000.0,
            },
        ],
    }
    assert containment_map(model) == {
        element["id"]: element["storey_id"]
        for element in complete_document["elements"]
    }
    assert {
        ifc_class: len(model.by_type(ifc_class))
        for ifc_class in IFC_CLASS_BY_KIND.values()
    } == {ifc_class: 1 for ifc_class in IFC_CLASS_BY_KIND.values()}

    for element in complete_document["elements"]:
        measured = measure_element_dimensions(model, element["id"])
        for name, expected in element["dimensions"].items():
            assert measured[name] == pytest.approx(expected, abs=1.0)

    identities = identity_map(model)
    assert set(identities) == canonical_ids
    assert len(set(identities.values())) == len(canonical_ids)

    wall_psets = _psets(model, identities["wall-001"])
    assert wall_psets["Pset_WallCommon"]["IsExternal"] is True
    assert wall_psets["Pset_WallCommon"]["LoadBearing"] is False

    for element in complete_document["elements"]:
        predefined_type = element.get("properties", {}).get(
            "predefined_type"
        )
        if predefined_type is None:
            continue
        psets = _psets(model, identities[element["id"]])
        assert (
            psets["Pset_text2IFCProperties"]["PredefinedType"]
            == predefined_type
        )

