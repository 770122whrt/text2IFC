"""Native opening solids described as proven world-vertical prisms.

This reads authored extrusion geometry and its placements. It never promotes a
mesh bounding box to a solid. Version 0.8 renderers and observations stay frozen.
"""
from __future__ import annotations

import copy
import math
import re
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from shapely.geometry import MultiPoint, Polygon

from .observation import all_items
from .wall_details_v08 import explicit_description

VERSION = 'text2ifc/ifc2text-opening-detail/0.9'
_EPS_MM = 1e-6


def read_opening_solid(entity: Any, scale_mm: float) -> dict:
    """Return the true XY profile only after proving a vertical prism exists.

Direct single extrusions with rectangle or straight-edged closed polygon
profiles are supported. Rectangles extruded horizontally can also describe a
vertical prism (common in Revit IFC): matching bottom/top vertex sets prove it.
Mappings, curved profiles, holes, and arbitrary tilted solids remain explicit
unsupported observations in this version.
"""
    def unsupported(reason):
        return {'schema_version': VERSION, 'status': 'unsupported', 'reason': reason}

    if not math.isfinite(scale_mm) or scale_mm <= 0:
        return unsupported('INVALID_LENGTH_UNIT')
    representations = getattr(getattr(entity, 'Representation', None), 'Representations', ()) or ()
    items = [item for rep in representations if rep.RepresentationIdentifier == 'Body' for item in rep.Items]
    if len(items) != 1 or items[0].is_a() != 'IfcExtrudedAreaSolid':
        return unsupported('REQUIRES_SINGLE_EXTRUDED_SOLID')
    solid = items[0]
    profile = solid.SweptArea
    profile_matrix = np.eye(4)
    if profile.is_a() == 'IfcRectangleProfileDef':
        x, y = float(profile.XDim) / 2., float(profile.YDim) / 2.
        if not all(math.isfinite(v) and v > 0 for v in (x, y)):
            return unsupported('INVALID_PROFILE')
        points = [[-x, -y], [x, -y], [x, y], [-x, y]]
        if profile.Position:
            profile_matrix = ifcopenshell.util.placement.get_axis2placement(profile.Position)
    elif profile.is_a() == 'IfcArbitraryClosedProfileDef' and profile.OuterCurve.is_a('IfcPolyline'):
        points = [list(point.Coordinates) for point in profile.OuterCurve.Points]
        if len(points) < 4 or points[0] != points[-1] or any(len(point) != 2 for point in points):
            return unsupported('INVALID_CLOSED_PROFILE')
        points = points[:-1]
    else:
        return unsupported('UNSUPPORTED_PROFILE')
    if not np.isfinite(np.asarray(points, dtype=float)).all():
        return unsupported('NONFINITE_GEOMETRY')
    polygon_local = Polygon(points)
    if not polygon_local.is_valid or polygon_local.area <= 0:
        return unsupported('INVALID_PROFILE')
    direction = np.asarray(solid.ExtrudedDirection.DirectionRatios, dtype=float)
    magnitude = float(np.linalg.norm(direction))
    if direction.shape != (3,) or not math.isfinite(magnitude) or magnitude <= 0:
        return unsupported('INVALID_EXTRUSION_DIRECTION')
    depth = float(solid.Depth)
    if not math.isfinite(depth) or depth <= 0:
        return unsupported('INVALID_EXTRUSION_DEPTH')
    product_matrix = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
    solid_matrix = product_matrix @ ifcopenshell.util.placement.get_axis2placement(solid.Position)
    matrix = solid_matrix @ profile_matrix
    base = np.array([(matrix @ np.array([p[0], p[1], 0., 1.]))[:3] for p in points]) * scale_mm
    vector = (solid_matrix[:3, :3] @ (direction / magnitude)) * depth * scale_mm
    if not np.isfinite(base).all() or not np.isfinite(vector).all():
        return unsupported('NONFINITE_GEOMETRY')
    end = base + vector
    vertices = np.vstack((base, end))
    low_z, high_z = float(vertices[:, 2].min()), float(vertices[:, 2].max())
    if high_z - low_z <= _EPS_MM:
        return unsupported('NOT_WORLD_VERTICAL_PRISM')
    if np.linalg.norm(vector[:2]) <= _EPS_MM and np.ptp(base[:, 2]) <= _EPS_MM:
        bottom = base if vector[2] > 0 else end
        polygon = Polygon(bottom[:, :2])
        proof = 'native_profile_with_world_vertical_extrusion'
    elif profile.is_a() == 'IfcRectangleProfileDef':
        low = vertices[np.abs(vertices[:, 2] - low_z) <= _EPS_MM, :2]
        high = vertices[np.abs(vertices[:, 2] - high_z) <= _EPS_MM, :2]
        # A native rectangle extrusion is a convex prism. Exactly two z planes
        # with equal four-point XY sets prove this is its exact vertical profile.
        if len(low) != 4 or len(high) != 4:
            return unsupported('NOT_WORLD_VERTICAL_PRISM')
        distances = np.linalg.norm(low[:, None, :] - high[None, :, :], axis=2)
        if np.any(distances.min(axis=0) > _EPS_MM) or np.any(distances.min(axis=1) > _EPS_MM):
            return unsupported('NOT_WORLD_VERTICAL_PRISM')
        polygon = MultiPoint(low).convex_hull
        if not isinstance(polygon, Polygon) or len(polygon.exterior.coords) != 5:
            return unsupported('DEGENERATE_PRISM')
        proof = 'native_rectangle_extrusion_with_matching_top_bottom_vertices'
    else:
        return unsupported('NOT_WORLD_VERTICAL_PRISM')
    if not polygon.is_valid or polygon.area <= _EPS_MM:
        return unsupported('INVALID_PROFILE')
    return {
        'schema_version': VERSION, 'status': 'supported_vertical_prism',
        'source_profile_type': profile.is_a(), 'coordinate_frame': 'world',
        'geometry_role': 'opening_cutting_solid', 'proof': proof,
        'bottom_outline_xy_mm': [[float(x), float(y)] for x, y in polygon.exterior.coords],
        'bottom_z_mm': low_z, 'height_mm': high_z - low_z,
        'direction': 'world_positive_z', 'area_mm2': float(polygon.area),
    }


def enrich_opening_details(source: str | Path, facts: dict) -> dict:
    result = copy.deepcopy(facts)
    model = ifcopenshell.open(str(source))
    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.
    for category, item in all_items(result):
        if category != 'openings':
            continue
        try:
            detail = read_opening_solid(model.by_guid(item['source_global_id']), scale)
        except (ValueError, TypeError, RuntimeError, AttributeError) as error:
            detail = {'schema_version': VERSION, 'status': 'unsupported', 'reason': type(error).__name__}
        item['opening_solid_detail'] = detail
    result['opening_detail_version'] = VERSION
    return result


def _number(value):
    if not math.isfinite(float(value)):
        raise ValueError('NONFINITE_OPENING_COORDINATE')
    return f'{float(value):.6f}'.rstrip('0').rstrip('.') or '0'


def _detail_text(item):
    detail = item.get('opening_solid_detail', {})
    prefix = '**开口 ' + item['label'] + ' 的切割实体**：'
    if detail.get('status') != 'supported_vertical_prism':
        return prefix + '本次不能提取可重建轮廓；原因 ' + str(detail.get('reason', 'unavailable')) + '。不得把表格外包尺寸当成矩形截面。'
    points = detail['bottom_outline_xy_mm']
    ring = '→'.join('(' + ','.join(_number(v) for v in point) + ')' for point in points)
    # Serialization must preserve shape and explicit closure at the chosen precision.
    rounded = Polygon([[float(_number(v)) for v in point] for point in points])
    original = Polygon(points)
    if not rounded.is_valid or rounded.area <= 0 or rounded.boundary.hausdorff_distance(original.boundary) > .00001:
        raise ValueError('OPENING_PROFILE_DISPLAY_LOSS')
    return prefix + '底面闭合外轮廓（世界XY，mm）' + ring + '；底面Z=' + _number(detail['bottom_z_mm']) + '；沿世界+Z拉伸 ' + _number(detail['height_mm']) + '。'


def opening_description(facts: dict, narration: dict | None = None) -> str:
    """Append actual cutting profiles to each floor while retaining old wall detail."""
    text = explicit_description(facts, narration)
    floors = {storey['label']: storey for storey in facts['storeys']}
    if facts.get('unassigned'):
        floors['UNASSIGNED'] = facts['unassigned']
    chunks = re.split(r'(?=^## 楼层 )', text, flags=re.M)
    for index, chunk in enumerate(chunks):
        match = re.match(r'## 楼层 ([^｜\n]+)', chunk)
        if not match:
            continue
        openings = floors.get(match.group(1), {}).get('openings', [])
        if not openings:
            continue
        lines = chunk.splitlines()
        rows = [i for i, line in enumerate(lines) if re.match(r'^\|O\d+\|', line)]
        if not rows:
            raise ValueError('OPENING_TABLE_INSERTION_TARGET_MISSING')
        instruction = ('以下切割实体与上表为同一开口，仍使用上表宿主且仅扣除一次；不得把表格外包尺寸当成矩形截面。'
                       '按世界坐标闭合轮廓及Z重建，不再沿宿主轴旋转轮廓；末尾闭合点不可省略。'
                       '本段轮廓坐标最多保留六位小数，表格其他值沿用原显示精度。')
        lines[rows[-1] + 1:rows[-1] + 1] = ['', instruction, '', '\n\n'.join(_detail_text(item) for item in openings), '']
        chunks[index] = '\n'.join(lines) + '\n\n'
    return ''.join(chunks)
