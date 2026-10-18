"""Bounded exact public Body reuse for horizontal rectangular beams.

Only a single direct rectangular SweptSolid is supported. Existing representation
items and their placements are immutable; each new occurrence owns new containers
and a new ObjectPlacement. Geometry authority always comes from the public IFC.
"""
from __future__ import annotations

from typing import Any
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np


def _body(member: Any) -> Any:
    from .public_geometry import _error
    bodies = [r for r in getattr(getattr(member, 'Representation', None), 'Representations', ())
              if r.RepresentationIdentifier == 'Body']
    if (not member.is_a('IfcBeam') or getattr(member, 'HasOpenings', ())
            or getattr(member, 'HasStructuralMember', ())
            or len(bodies) != 1 or len(bodies[0].Items) != 1
            or bodies[0].RepresentationType != 'SweptSolid'):
        raise _error('BEAM_BODY_UNSUPPORTED')
    solid = bodies[0].Items[0]
    if (not solid.is_a('IfcExtrudedAreaSolid') or not solid.SweptArea.is_a('IfcRectangleProfileDef')
            or solid.SweptArea.ProfileType != 'AREA'):
        raise _error('BEAM_BODY_UNSUPPORTED')
    return bodies[0]


def body_signature(member: Any) -> Any:
    """Exact forward Body graph values, independent of STEP numbering.

    Includes internal placements and null/default distinctions; container and
    context identities are independently retained by the copier.
    """
    def encode(value):
        if hasattr(value, 'is_a'):
            return [value.is_a(), *[encode(item) for item in value]]
        if isinstance(value, (tuple, list)):
            return [encode(item) for item in value]
        return value
    return encode(_body(member).Items)


def measure_beam(member: Any, *, relative_to: Any | None = None,
                 placement_world_mm: Any | None = None) -> dict:
    """Measure the actual end-face centres and horizontal/vertical section axes.

    Profile XDim can be vertical. Profile and solid internal offsets remain part
    of the centreline; they must never be conflated with the occurrence origin.
    """
    from .public_geometry import _error
    solid = _body(member).Items[0]
    profile = solid.SweptArea
    scale = ifcopenshell.util.unit.calculate_unit_scale(member.file) * 1000.
    placement = ifcopenshell.util.placement.get_local_placement(member.ObjectPlacement).copy()
    placement[:3, 3] *= scale
    if placement_world_mm is not None:
        placement = np.array(placement_world_mm, dtype=float)
    solid_frame = ifcopenshell.util.placement.get_axis2placement(solid.Position).copy()
    solid_frame[:3, 3] *= scale
    profile_frame = (np.eye(3) if profile.Position is None else
                     ifcopenshell.util.placement.get_axis2placement(profile.Position))
    profile_origin = np.array([*profile_frame[:2, 2] * scale, 0., 1.])
    frame = placement @ solid_frame
    start = (frame @ profile_origin)[:3]
    direction = np.array(solid.ExtrudedDirection.DirectionRatios, dtype=float)
    if (direction.shape != (3,) or not np.isfinite(direction).all()
            or not np.isclose(np.linalg.norm(direction), 1., atol=1e-7, rtol=0)
            or not np.allclose(direction, [0, 0, 1], atol=1e-7, rtol=0)
            or not all(np.isfinite(v) and v > 0 for v in (solid.Depth, profile.XDim, profile.YDim))):
        raise _error('BEAM_BODY_UNSUPPORTED')
    axis = frame[:3, :3] @ direction
    end = start + axis * float(solid.Depth) * scale
    profile_axes = frame[:3, :2] @ profile_frame[:2, :2]
    vertical = [i for i in (0, 1) if np.isclose(abs(profile_axes[2, i]), 1., atol=1e-7, rtol=0)]
    if abs(axis[2]) > 1e-7 or len(vertical) != 1:
        raise _error('STRUCTURAL_ORIENTATION_UNSUPPORTED')
    height_axis = vertical[0]
    dims = [float(profile.XDim) * scale, float(profile.YDim) * scale]
    if relative_to is not None:
        parent = ifcopenshell.util.placement.get_local_placement(relative_to.ObjectPlacement).copy()
        parent[:3, 3] *= scale
        inv = np.linalg.inv(parent)
        start, end = ((inv @ [*p, 1])[:3] for p in (start, end))
        axis = inv[:3, :3] @ axis
        if abs(axis[2]) > 1e-7:
            raise _error('STRUCTURAL_ORIENTATION_UNSUPPORTED')
    return {'axis_start_mm': tuple(round(float(v), 6) for v in start),
            'axis_end_mm': tuple(round(float(v), 6) for v in end),
            'axis_direction': tuple(round(float(v), 12) for v in axis),
            'axis_extent_mm': round(float(solid.Depth) * scale, 6),
            'section': {'shape': 'rectangle', 'width_mm': round(dims[1 - height_axis], 6),
                        'height_mm': round(dims[height_axis], 6)},
            'orientation': tuple(round(float(v), 12) for v in axis),
            'representation_type': 'SweptSolid'}


def copy_body(member: Any, reference: Any) -> None:
    body = _body(reference)
    measure_beam(reference)
    m = member.file
    representation = m.create_entity('IfcShapeRepresentation', ContextOfItems=body.ContextOfItems,
        RepresentationIdentifier='Body', RepresentationType=body.RepresentationType, Items=list(body.Items))
    member.Representation = m.create_entity('IfcProductDefinitionShape', Representations=[representation])


def measure_beam_installation(member: Any, requirement: Any, *, reference_model: Any | None = None) -> dict:
    from .public_geometry import _frame, _local_mesh
    source = member.file if reference_model is None else reference_model
    reference = source.by_guid(requirement['reference_id'])
    actual = ifcopenshell.util.placement.get_local_placement(member.ObjectPlacement).copy()
    actual[:3, 3] *= ifcopenshell.util.unit.calculate_unit_scale(member.file) * 1000.
    expected = _frame(requirement['placement_world_mm'])
    a, b = _local_mesh(member), _local_mesh(reference)
    graph_equal = body_signature(member) == body_signature(reference)
    mesh_equal = a.shape == b.shape and bool(np.allclose(a, b, atol=.001, rtol=0))
    translation = float(np.max(np.abs(actual[:3, 3] - expected[:3, 3])))
    rotation = float(np.max(np.abs(actual[:3, :3] - expected[:3, :3])))
    return {'valid': graph_equal and mesh_equal and translation <= .001 and rotation <= 1e-7,
            'body_graph_matches': graph_equal, 'reference_body_mesh_matches': mesh_equal,
            'translation_error_mm': translation, 'rotation_matrix_error': rotation}
