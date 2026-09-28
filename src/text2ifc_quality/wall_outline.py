"""Check the uncut wall footprint using IfcOpenShell world geometry and GEOS.

This measures a plan footprint, not full 3-D solid equivalence. Opening/fill and
world-Z checks are separate. Symmetric buffered containment checks every segment
of the boundary; the reported GEOS Hausdorff distance is a discrete diagnostic.
"""
import ifcopenshell.geom
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union


def check_wall_outline(wall, expected_points, tolerance):
    settings = ifcopenshell.geom.settings()
    settings.set('use-world-coords', True)
    settings.set('convert-back-units', False)
    settings.set('disable-opening-subtractions', True)
    settings.set('context-identifiers', ['Body'])
    settings.set('mesher-linear-deflection', .0001)
    shape = ifcopenshell.geom.create_shape(settings, wall)
    vertices = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces, dtype=int).reshape(-1, 3)
    if not len(faces) or not np.isfinite(vertices).all() or len(faces) > 50000:
        raise ValueError('Wall has no finite bounded Body mesh')
    triangles = [Polygon(vertices[face,:2]) for face in faces]
    actual = unary_union([p for p in triangles if p.area > 1e-15])
    expected = Polygon(expected_points)
    if not actual.is_valid or actual.is_empty or not expected.is_valid or expected.area <= 0:
        raise ValueError('Invalid measured or requested wall footprint')
    same_topology = (actual.geom_type == 'Polygon' and len(actual.interiors) == len(expected.interiors))
    limit = tolerance + 1e-9  # metre-scale numerical noise, not additional design tolerance
    agrees = (same_topology and expected.boundary.buffer(limit, quad_segs=64).covers(actual.boundary)
              and actual.boundary.buffer(limit, quad_segs=64).covers(expected.boundary))
    return {'passed': bool(agrees), 'topology_equal': same_topology,
            'discrete_boundary_distance_mm': float(expected.boundary.hausdorff_distance(actual.boundary)*1000),
            'linear_tolerance_mm': tolerance*1000,
            'method': 'ifcopenshell_uncut_world_mesh_xy_union_symmetric_boundary_buffer'}
