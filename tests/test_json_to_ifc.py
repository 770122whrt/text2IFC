import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps" / "python312"))
sys.path.insert(0, str(ROOT / "scripts" / "ifc_pipeline"))

import ifcopenshell
import ifcopenshell.util.element as util_element

from roundtrip import create_ifc_from_json


def _minimal_model():
    return {
        "schema": "IFC2X3",
        "project": {"name": "JSON to IFC test project"},
        "site": {"name": "Test site"},
        "building": {"name": "Test building", "num_storeys": 2},
        "storeys": [
            {"name": "Level 1", "elevation": 0.0},
            {"name": "Level 2", "elevation": 3000.0},
        ],
        "materials": ["Concrete"],
        "material_assignments": {},
        "walls": [
            {
                "name": "External wall",
                "storey": "Level 1",
                "is_external": True,
                "load_bearing": False,
                "profile": {
                    "type": "rectangle",
                    "x_dim": 5000.0,
                    "y_dim": 240.0,
                    "depth": 3000.0,
                },
            }
        ],
        "columns": [],
        "beams": [],
        "slabs": [],
        "doors": [
            {
                "name": "Main door",
                "storey": "Level 1",
                "width": 900.0,
                "height": 2100.0,
            }
        ],
        "windows": [
            {
                "name": "Front window",
                "storey": "Level 1",
                "width": 1200.0,
                "height": 1500.0,
            }
        ],
        "stairs": [],
        "stair_flights": [],
        "roofs": [],
    }


def test_json_to_ifc_preserves_storey_elevations(tmp_path):
    out_path = tmp_path / "model.ifc"

    create_ifc_from_json(_minimal_model(), str(out_path))

    ifc = ifcopenshell.open(str(out_path))
    elevations = {storey.Name: storey.Elevation for storey in ifc.by_type("IfcBuildingStorey")}
    assert elevations == {"Level 1": 0.0, "Level 2": 3000.0}


def test_json_to_ifc_writes_wall_common_properties(tmp_path):
    out_path = tmp_path / "model.ifc"

    create_ifc_from_json(_minimal_model(), str(out_path))

    ifc = ifcopenshell.open(str(out_path))
    wall = ifc.by_type("IfcWall")[0]
    psets = util_element.get_psets(wall)
    assert psets["Pset_WallCommon"]["IsExternal"] is True
    assert psets["Pset_WallCommon"]["LoadBearing"] is False


def test_json_to_ifc_preserves_door_and_window_dimensions(tmp_path):
    out_path = tmp_path / "model.ifc"

    create_ifc_from_json(_minimal_model(), str(out_path))

    ifc = ifcopenshell.open(str(out_path))
    door = ifc.by_type("IfcDoor")[0]
    window = ifc.by_type("IfcWindow")[0]
    assert door.OverallWidth == 900.0
    assert door.OverallHeight == 2100.0
    assert window.OverallWidth == 1200.0
    assert window.OverallHeight == 1500.0
