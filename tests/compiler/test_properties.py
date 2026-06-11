import copy
import json
from pathlib import Path

import ifcopenshell.util.element
import pytest

from text2ifc_compiler import compile_document, identity_map, open_ifc, verify_ifc


ROOT = Path(__file__).resolve().parents[2]
COMPLETE_FIXTURE = ROOT / "tests" / "contract" / "fixtures" / "complete.json"
FALLBACK_PSET = "Pset_text2IFCProperties"


def _property_document() -> dict:
    document = json.loads(COMPLETE_FIXTURE.read_text(encoding="utf-8"))
    templates = {
        element["kind"]: element for element in document["elements"]
    }

    def element(kind: str, suffix: str, properties: dict | None) -> dict:
        value = copy.deepcopy(templates[kind])
        value["id"] = f"{kind}-{suffix}"
        value["name"] = f"{kind} {suffix}"
        if properties is None:
            value.pop("properties", None)
        else:
            value["properties"] = properties
        return value

    document["elements"] = [
        element(
            "wall",
            "boolean-a",
            {"is_external": True, "load_bearing": False},
        ),
        element(
            "wall",
            "boolean-b",
            {"is_external": False, "load_bearing": True},
        ),
        element("wall", "no-properties", None),
        element("column", "load-true", {"load_bearing": True}),
        element("column", "load-false", {"load_bearing": False}),
        element("beam", "load-true", {"load_bearing": True}),
        element("beam", "load-false", {"load_bearing": False}),
        element("slab", "standard", {"predefined_type": "FLOOR"}),
        element("slab", "custom", {"predefined_type": "CUSTOM_SLAB"}),
        element("door", "standard", {"predefined_type": "DOOR"}),
        element("door", "custom", {"predefined_type": "CUSTOM_DOOR"}),
        element("window", "standard", {"predefined_type": "WINDOW"}),
        element("window", "custom", {"predefined_type": "CUSTOM_WINDOW"}),
        element(
            "stair",
            "standard",
            {"predefined_type": "STRAIGHT_RUN_STAIR"},
        ),
        element("stair", "custom", {"predefined_type": "CUSTOM_STAIR"}),
        element(
            "stair_flight", "standard", {"predefined_type": "STRAIGHT"}
        ),
        element(
            "stair_flight",
            "custom",
            {"predefined_type": "CUSTOM_FLIGHT"},
        ),
        element("roof", "standard", {"predefined_type": "FLAT_ROOF"}),
        element("roof", "custom", {"predefined_type": "CUSTOM_ROOF"}),
    ]
    return document


@pytest.fixture(scope="module")
def property_model(tmp_path_factory: pytest.TempPathFactory):
    document = _property_document()
    original = copy.deepcopy(document)
    output = tmp_path_factory.mktemp("properties") / "properties.ifc"

    result = compile_document(document, output)

    assert result.success
    assert document == original
    model = open_ifc(output)
    assert verify_ifc(model) == ()
    return model


def _entity(model, bim_json_id: str):
    return model.by_guid(identity_map(model)[bim_json_id])


def _psets(model, bim_json_id: str) -> dict:
    return ifcopenshell.util.element.get_psets(
        _entity(model, bim_json_id)
    )


@pytest.mark.parametrize(
    ("bim_json_id", "pset_name", "property_name", "expected"),
    [
        ("wall-boolean-a", "Pset_WallCommon", "IsExternal", True),
        ("wall-boolean-a", "Pset_WallCommon", "LoadBearing", False),
        ("wall-boolean-b", "Pset_WallCommon", "IsExternal", False),
        ("wall-boolean-b", "Pset_WallCommon", "LoadBearing", True),
        ("column-load-true", "Pset_ColumnCommon", "LoadBearing", True),
        ("column-load-false", "Pset_ColumnCommon", "LoadBearing", False),
        ("beam-load-true", "Pset_BeamCommon", "LoadBearing", True),
        ("beam-load-false", "Pset_BeamCommon", "LoadBearing", False),
    ],
)
def test_boolean_properties_round_trip_with_original_type(
    property_model,
    bim_json_id: str,
    pset_name: str,
    property_name: str,
    expected: bool,
) -> None:
    value = _psets(property_model, bim_json_id)[pset_name][property_name]

    assert value is expected
    assert isinstance(value, bool)


@pytest.mark.parametrize(
    ("kind", "standard", "custom"),
    [
        ("slab", "FLOOR", "CUSTOM_SLAB"),
        ("door", "DOOR", "CUSTOM_DOOR"),
        ("window", "WINDOW", "CUSTOM_WINDOW"),
        ("stair", "STRAIGHT_RUN_STAIR", "CUSTOM_STAIR"),
        ("stair_flight", "STRAIGHT", "CUSTOM_FLIGHT"),
        ("roof", "FLAT_ROOF", "CUSTOM_ROOF"),
    ],
)
def test_predefined_type_is_always_recoverable_without_coercion(
    property_model, kind: str, standard: str, custom: str
) -> None:
    standard_value = _psets(
        property_model, f"{kind}-standard"
    )[FALLBACK_PSET]["PredefinedType"]
    custom_value = _psets(
        property_model, f"{kind}-custom"
    )[FALLBACK_PSET]["PredefinedType"]

    assert standard_value == standard
    assert custom_value == custom
    assert isinstance(standard_value, str)
    assert isinstance(custom_value, str)


def test_compatible_predefined_types_populate_ifc2x3_attributes(
    property_model,
) -> None:
    standard_slab = _entity(property_model, "slab-standard")
    custom_slab = _entity(property_model, "slab-custom")
    standard_stair = _entity(property_model, "stair-standard")
    custom_stair = _entity(property_model, "stair-custom")
    standard_roof = _entity(property_model, "roof-standard")
    custom_roof = _entity(property_model, "roof-custom")

    assert standard_slab.PredefinedType == "FLOOR"
    assert custom_slab.PredefinedType is None
    assert standard_stair.ShapeType == "STRAIGHT_RUN_STAIR"
    assert custom_stair.ShapeType == "NOTDEFINED"
    assert standard_roof.ShapeType == "FLAT_ROOF"
    assert custom_roof.ShapeType == "NOTDEFINED"


def test_missing_optional_properties_remain_absent(property_model) -> None:
    psets = _psets(property_model, "wall-no-properties")

    assert "Pset_WallCommon" not in psets
    assert FALLBACK_PSET not in psets

