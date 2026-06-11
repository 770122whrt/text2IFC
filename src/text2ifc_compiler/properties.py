from typing import Any, Mapping

from ifcopenshell.api.pset.add_pset import add_pset
from ifcopenshell.api.pset.edit_pset import edit_pset


FALLBACK_PSET = "Pset_text2IFCProperties"

COMMON_PSET_BY_KIND = {
    "wall": "Pset_WallCommon",
    "column": "Pset_ColumnCommon",
    "beam": "Pset_BeamCommon",
}

COMMON_PROPERTY_NAMES = {
    "is_external": "IsExternal",
    "load_bearing": "LoadBearing",
}

SLAB_TYPES = {"FLOOR", "ROOF", "LANDING", "BASESLAB", "NOTDEFINED"}
STAIR_TYPES = {
    "STRAIGHT_RUN_STAIR",
    "TWO_STRAIGHT_RUN_STAIR",
    "QUARTER_WINDING_STAIR",
    "QUARTER_TURN_STAIR",
    "HALF_WINDING_STAIR",
    "HALF_TURN_STAIR",
    "TWO_QUARTER_WINDING_STAIR",
    "TWO_QUARTER_TURN_STAIR",
    "THREE_QUARTER_WINDING_STAIR",
    "THREE_QUARTER_TURN_STAIR",
    "SPIRAL_STAIR",
    "DOUBLE_RETURN_STAIR",
    "CURVED_RUN_STAIR",
    "TWO_CURVED_RUN_STAIR",
    "NOTDEFINED",
}
ROOF_TYPES = {
    "FLAT_ROOF",
    "SHED_ROOF",
    "GABLE_ROOF",
    "HIP_ROOF",
    "HIPPED_GABLE_ROOF",
    "GAMBREL_ROOF",
    "MANSARD_ROOF",
    "BARREL_ROOF",
    "RAINBOW_ROOF",
    "BUTTERFLY_ROOF",
    "PAVILION_ROOF",
    "DOME_ROOF",
    "FREEFORM",
    "NOTDEFINED",
}


def _write_pset(
    ifc_file: Any,
    element: Any,
    name: str,
    values: Mapping[str, Any],
) -> None:
    if not values:
        return
    pset = add_pset(ifc_file, product=element, name=name)
    edit_pset(ifc_file, pset=pset, properties=dict(values))


def _apply_compatible_predefined_type(
    element: Any, kind: str, value: str
) -> None:
    if kind == "slab" and value in SLAB_TYPES:
        element.PredefinedType = value
    elif kind == "stair" and value in STAIR_TYPES:
        element.ShapeType = value
    elif kind == "roof" and value in ROOF_TYPES:
        element.ShapeType = value


def apply_selected_properties(
    ifc_file: Any,
    element: Any,
    element_data: Mapping[str, Any],
) -> None:
    source_properties = element_data.get("properties")
    if not source_properties:
        return

    kind = element_data["kind"]
    common_values = {
        COMMON_PROPERTY_NAMES[source_name]: source_properties[source_name]
        for source_name in COMMON_PROPERTY_NAMES
        if source_name in source_properties
    }
    if common_values:
        _write_pset(
            ifc_file,
            element,
            COMMON_PSET_BY_KIND[kind],
            common_values,
        )

    predefined_type = source_properties.get("predefined_type")
    if predefined_type is not None:
        _apply_compatible_predefined_type(
            element, kind, predefined_type
        )
        _write_pset(
            ifc_file,
            element,
            FALLBACK_PSET,
            {"PredefinedType": predefined_type},
        )
