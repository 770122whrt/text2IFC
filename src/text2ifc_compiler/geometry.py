from typing import Any, Mapping

import numpy
from ifcopenshell.api.geometry.add_mesh_representation import (
    add_mesh_representation,
)
from ifcopenshell.api.geometry.assign_representation import (
    assign_representation,
)
from ifcopenshell.api.geometry.edit_object_placement import (
    edit_object_placement,
)


BOX_DIMENSIONS_BY_KIND = {
    "wall": ("length", "thickness", "height"),
    "column": ("width", "depth", "height"),
    "beam": ("length", "width", "height"),
    "slab": ("length", "width", "thickness"),
    "stair": ("length", "width", "height"),
    "stair_flight": ("run", "width", "rise"),
    "roof": ("length", "width", "thickness"),
}


def mm_to_m(value: float) -> float:
    return float(value) / 1000.0


def _box_representation(
    ifc_file: Any, body_context: Any, dimensions_m: tuple[float, float, float]
) -> Any:
    x, y, z = dimensions_m
    vertices = [
        (0.0, 0.0, 0.0),
        (x, 0.0, 0.0),
        (x, y, 0.0),
        (0.0, y, 0.0),
        (0.0, 0.0, z),
        (x, 0.0, z),
        (x, y, z),
        (0.0, y, z),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return add_mesh_representation(
        ifc_file,
        context=body_context,
        vertices=[vertices],
        faces=[faces],
    )


def add_element_geometry(
    ifc_file: Any,
    element: Any,
    element_data: Mapping[str, Any],
    body_context: Any,
    source_index: int,
) -> None:
    placement = numpy.eye(4)
    placement[0, 3] = source_index * 10.0
    edit_object_placement(
        ifc_file,
        product=element,
        matrix=placement,
        is_si=True,
    )

    kind = element_data["kind"]
    dimensions = element_data["dimensions"]
    if kind in {"door", "window"}:
        element.OverallWidth = dimensions["width"]
        element.OverallHeight = dimensions["height"]
        return

    dimension_names = BOX_DIMENSIONS_BY_KIND[kind]
    representation = _box_representation(
        ifc_file,
        body_context,
        tuple(mm_to_m(dimensions[name]) for name in dimension_names),
    )
    assign_representation(
        ifc_file, product=element, representation=representation
    )
