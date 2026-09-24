"""BIM JSON 2.4 geometry for constant-thickness, end-clipped wall hosts.

All computations are in millimetres. Representation placements are composed
before inspecting the section: a raw polygon's bounding box is not thickness.
The 0.1 mm allowance covers rounded authored coordinates, never a missing fact.
"""
from __future__ import annotations

import numpy as np

from .placement import _local_transform, world_transform_for

TOLERANCE_MM = 0.1


def representation_frame(rep):
    if rep.get('kind') != 'extruded_profile':
        raise ValueError('A vertical extruded profile is required.')
    direction = np.asarray(rep.get('direction'), dtype=float)
    if direction.shape != (3,) or not np.all(np.isfinite(direction)) or not np.allclose(direction[:2], 0, atol=1e-9) or direction[2] <= 0:
        raise ValueError('A positive local Z extrusion is required.')
    frame = np.array(_local_transform(rep['position'])) if 'position' in rep else np.eye(4)
    if not np.allclose(frame[:3, 2], [0, 0, 1], atol=1e-9):
        raise ValueError('Tilted representation positions are not supported for layered wall hosts.')
    return frame


def _cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def wall_section(rep):
    """Return convex section in product coordinates and its extrusion limits.

    Both long faces must lie at constant local Y. Bevels may truncate either
    end; concave notches, self intersections and tapered long faces are refused.
    """
    frame = representation_frame(rep)
    profile = rep.get('profile', {})
    if profile.get('kind') == 'rectangle':
        x, y = profile['x'] / 2, profile['y'] / 2
        raw = [[-x, -y], [x, -y], [x, y], [-x, y]]
    elif profile.get('kind') == 'polygon':
        raw = profile['points']
        if len(raw) < 4 or raw[0] != raw[-1]:
            raise ValueError('A closed wall section is required.')
        raw = raw[:-1]
    else:
        raise ValueError('Only rectangle or end-clipped polygon wall sections are supported.')
    points = np.array([(frame @ [p[0], p[1], 0, 1])[:2] for p in raw])
    if not np.all(np.isfinite(points)):
        raise ValueError('Wall section coordinates must be finite.')
    # Rounded collinear points can create an apparent notch whose extrapolated
    # edge is much farther away than the actual authored deviation. Collapse
    # only intermediate vertices within tolerance of their neighbour segment,
    # for validation only; the compiler retains every original profile point.
    changed = True
    while changed and len(points) > 3:
        changed = False
        for index, point in enumerate(points):
            a, b = points[index - 1], points[(index + 1) % len(points)]
            edge = b - a
            length = float(np.linalg.norm(edge))
            if length > 1e-9 and 0 < np.dot(point - a, edge) < length * length and abs(_cross(edge, point - a)) / length <= TOLERANCE_MM:
                points = np.delete(points, index, axis=0)
                changed = True
                break
    area = sum(_cross(a, b) for a, b in zip(points, np.roll(points, -1, axis=0))) / 2
    if abs(area) < 1e-6:
        raise ValueError('Wall section must have positive area.')
    if area < 0:
        points = points[::-1]
    # Every point must be on the inner side of every edge. This rejects both
    # concave and self-intersecting rings, including nonadjacent crossings.
    for a, b in zip(points, np.roll(points, -1, axis=0)):
        edge = b - a
        length = float(np.linalg.norm(edge))
        if length <= 1e-9 or any(_cross(edge, p - a) < -TOLERANCE_MM * length for p in points):
            raise ValueError('Wall section must be convex without repeated vertices.')
    low, high = float(points[:, 1].min()), float(points[:, 1].max())
    sides = []
    for y in (low, high):
        xs = points[np.abs(points[:, 1] - y) <= TOLERANCE_MM, 0]
        if len(xs) < 2 or np.ptp(xs) <= TOLERANCE_MM:
            raise ValueError('Wall section must have two parallel local-X long faces.')
        sides.append((float(xs.min()), float(xs.max())))
    if min(s[1] for s in sides) - max(s[0] for s in sides) <= TOLERANCE_MM or high - low <= TOLERANCE_MM:
        raise ValueError('The two wall faces must overlap and define positive thickness.')
    return points, low, high, float(frame[2, 3]), float(frame[2, 3] + rep['depth'])


def _intersection_area(points, x0, x1, y0, y1):
    """Clip the convex wall section by an aligned rectangle; tangency has area 0."""
    output = [np.array(p) for p in points]
    for axis, bound, sign in ((0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1)):
        before, output = output, []
        if not before:
            return 0.
        a = before[-1]
        for b in before:
            da, db = sign * (a[axis] - bound), sign * (b[axis] - bound)
            if (da >= 0) != (db >= 0):
                output.append(a + (b - a) * da / (da - db))
            if db >= 0:
                output.append(b)
            a = b
    if len(output) < 3:
        return 0.
    points = np.array(output) - output[0]
    return abs(sum(_cross(a, b) for a, b in zip(points, np.roll(points, -1, axis=0)))) / 2


def _aligned(matrix):
    rotation = matrix[:3, :3]
    # Opposite X/Y is the same plane and allows a reversed wall direction.
    return any(np.allclose(rotation, np.diag([sign, sign, 1]), atol=1e-9) for sign in (1, -1))


def filling_fit_messages(document, host_id, opening_id, filling_id):
    """Check real opening and filling envelopes, including representation offsets."""
    records = {r['id']: r for r in document['entities']}
    host_rep = records[host_id]['attributes']['Representation']
    opening_rep = records[opening_id]['attributes']['Representation']
    filling = records[filling_id]['attributes']['Representation']
    polygon, _, _, wall_z0, wall_z1 = wall_section(host_rep)
    if opening_rep.get('profile', {}).get('kind') != 'rectangle':
        raise ValueError('The opening must remain a rectangular vertical extrusion.')
    host_world = np.array(world_transform_for(document, host_id))
    opening_world = np.array(world_transform_for(document, opening_id)) @ representation_frame(opening_rep)
    fill_world = np.array(world_transform_for(document, filling_id))
    opening_in_host = np.linalg.inv(host_world) @ opening_world
    fill_in_opening = np.linalg.inv(opening_world) @ fill_world
    if not _aligned(opening_in_host) or not _aligned(fill_in_opening):
        raise ValueError('Filling, opening and wall axes must align, allowing a reversed planar direction.')
    messages = []
    ox, oy, oz = opening_in_host[:3, 3]
    hx, hy = opening_rep['profile']['x'] / 2, opening_rep['profile']['y'] / 2
    # IFC openings are Boolean cutters. A valid source cutter may cross a
    # clipped wall end; requiring complete containment changes the source.
    # Genuine disjoint/tangent cutters still fail using positive intersection.
    opening_area = _intersection_area(polygon, ox - hx, ox + hx, oy - hy, oy + hy)
    opening_height = min(oz + opening_rep['depth'], wall_z1) - max(oz, wall_z0)
    if opening_area <= 1e-6 or opening_height <= 1e-6:
        messages.append('The unchanged opening must intersect the wall with positive volume; tangency is insufficient.')
    fx, fy, fz = fill_in_opening[:3, 3]
    if abs(fx) + filling['width'] / 2 > hx + TOLERANCE_MM or fz < -TOLERANCE_MM or fz + filling['height'] > opening_rep['depth'] + TOLERANCE_MM:
        messages.append('Filling width, height or placement exceeds the unchanged opening.')
    if abs(fy) + filling['depth'] / 2 > hy + TOLERANCE_MM:
        messages.append('Input filling depth exceeds the unchanged opening depth.')
    fill_in_host = np.linalg.inv(host_world) @ fill_world
    x, y, z = fill_in_host[:3, 3]
    from .basic_filling import resolve_basic_filling
    parameters = resolve_basic_filling(filling, records[filling_id]['ifc_class'])['parameters']
    actual_depth = max(parameters['frame_depth'], parameters['panel_thickness'])
    fill_area = _intersection_area(polygon, x - filling['width'] / 2, x + filling['width'] / 2,
                                   y - actual_depth / 2, y + actual_depth / 2)
    fill_height = min(z + filling['height'], wall_z1) - max(z, wall_z0)
    if fill_area <= 1e-6 or fill_height <= 1e-6:
        messages.append('The filling envelope must overlap the wall with positive volume.')
    return messages
