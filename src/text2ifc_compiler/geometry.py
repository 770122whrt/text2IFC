import math
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

X_DIMENSION_BY_KIND = {
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


def mm_to_m(value: float) -> float:
    return float(value) / 1000.0


def element_x_extent_m(element_data: Mapping[str, Any]) -> float:
    dimension_name = X_DIMENSION_BY_KIND[element_data["kind"]]
    return mm_to_m(element_data["dimensions"][dimension_name])


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
    x_offset_m: float,
) -> None:
    placement = numpy.eye(4)
    placement[0, 3] = x_offset_m
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


def _axis2placement3d(ifc_file: Any, value: Mapping[str, Any]) -> Any:
    return ifc_file.createIfcAxis2Placement3D(
        ifc_file.createIfcCartesianPoint(
            tuple(float(item) for item in value["origin"])
        ),
        ifc_file.createIfcDirection(
            tuple(float(item) for item in value["axis"])
        ),
        ifc_file.createIfcDirection(
            tuple(float(item) for item in value["ref_direction"])
        ),
    )


def _default_solid_position(
    direction: list[float],
) -> tuple[dict[str, list[float]], list[float]]:
    magnitude = math.sqrt(sum(item * item for item in direction))
    axis = [item / magnitude for item in direction]
    candidate = [1.0, 0.0, 0.0]
    if abs(sum(a * b for a, b in zip(axis, candidate))) > 0.9:
        candidate = [0.0, 1.0, 0.0]
    projection = sum(a * b for a, b in zip(axis, candidate))
    ref_direction = [
        candidate[index] - projection * axis[index] for index in range(3)
    ]
    ref_magnitude = math.sqrt(sum(item * item for item in ref_direction))
    ref_direction = [item / ref_magnitude for item in ref_direction]
    return (
        {
            "origin": [0.0, 0.0, 0.0],
            "axis": axis,
            "ref_direction": ref_direction,
        },
        [0.0, 0.0, 1.0],
    )


def _default_stair_solid_position(
    direction: list[float],
) -> tuple[dict[str, list[float]], list[float]]:
    """Keep a step-profile's positive second coordinate aligned with global +Z."""
    magnitude = math.sqrt(sum(item * item for item in direction))
    horizontal = [direction[0] / magnitude, direction[1] / magnitude, 0.0]
    return (
        {
            "origin": [0.0, 0.0, 0.0],
            "axis": [-horizontal[0], -horizontal[1], 0.0],
            "ref_direction": [horizontal[1], -horizontal[0], 0.0],
        },
        [0.0, 0.0, 1.0],
    )


def assign_v2_placement(
    ifc_file: Any,
    product: Any,
    placement: Mapping[str, Any],
    parent: Any | None,
) -> None:
    parent_placement = (
        getattr(parent, "ObjectPlacement", None) if parent is not None else None
    )
    product.ObjectPlacement = ifc_file.createIfcLocalPlacement(
        parent_placement,
        _axis2placement3d(ifc_file, placement),
    )


def _v2_profile(ifc_file: Any, profile: Mapping[str, Any]) -> Any:
    if profile["kind"] == "rectangle":
        profile_position = ifc_file.createIfcAxis2Placement2D(
            ifc_file.createIfcCartesianPoint((0.0, 0.0)),
            ifc_file.createIfcDirection((1.0, 0.0)),
        )
        return ifc_file.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            ProfileName=None,
            Position=profile_position,
            XDim=float(profile["x"]),
            YDim=float(profile["y"]),
        )
    points = [
        ifc_file.createIfcCartesianPoint(
            tuple(float(coordinate) for coordinate in point)
        )
        for point in profile["points"]
    ]
    return ifc_file.create_entity(
        "IfcArbitraryClosedProfileDef",
        ProfileType="AREA",
        ProfileName=None,
        OuterCurve=ifc_file.createIfcPolyline(points),
    )


def add_v2_geometry(
    ifc_file: Any,
    product: Any,
    representation: Mapping[str, Any],
    body_context: Any,
) -> None:
    direction = [float(item) for item in representation["direction"]]
    if "position" in representation:
        position = representation["position"]
        extrusion_direction = direction
    elif product.is_a("IfcStair") and direction[2] == 0:
        position, extrusion_direction = _default_stair_solid_position(direction)
    else:
        position, extrusion_direction = _default_solid_position(direction)
    solid = ifc_file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=_v2_profile(ifc_file, representation["profile"]),
        Position=_axis2placement3d(ifc_file, position),
        ExtrudedDirection=ifc_file.createIfcDirection(
            tuple(extrusion_direction)
        ),
        Depth=float(representation["depth"]),
    )
    shape = ifc_file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid],
    )
    assign_representation(ifc_file, product=product, representation=shape)
