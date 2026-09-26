"""Read explicit public world-XY wall outlines; never infer from a candidate."""
from collections.abc import Mapping
from math import isfinite, hypot

from shapely.geometry import Polygon


def public_wall_outline(wall):
    shapes = []
    for name in ('polygon', 'solid_outline'):
        if name not in wall:
            continue
        points = wall[name]
        if isinstance(points, Mapping):
            if 'points' in points and 'polygon' in points and points['points'] != points['polygon']:
                raise ValueError('Conflicting wall outline wrappers')
            points = points.get('polygon', points.get('points'))
        if (not isinstance(points, list) or len(points) < 3
                or not all(isinstance(p, list) and len(p) == 2
                    and all(isinstance(v, (int,float)) and not isinstance(v,bool) and isfinite(v) for v in p)
                    for p in points)):
            raise ValueError('Wall outline requires finite world-XY points')
        shape = Polygon(points)
        if not shape.is_valid or shape.is_empty or shape.area <= 0:
            raise ValueError('Invalid wall outline')
        shapes.append(shape)
    if not shapes:
        if all(key in wall for key in ('start_mm', 'end_mm', 'thickness_mm')):
            start, end, thickness = wall['start_mm'], wall['end_mm'], wall['thickness_mm']
            finite = lambda v: isinstance(v,(int,float)) and not isinstance(v,bool) and isfinite(v)
            if (not all(isinstance(p,list) and len(p) in (2,3) and all(finite(v) for v in p) for p in (start,end))
                    or not finite(thickness) or thickness <= 0):
                raise ValueError('Invalid wall centreline or thickness')
            dx, dy = end[0]-start[0], end[1]-start[1]
            length = hypot(dx,dy)
            if length <= 0:
                raise ValueError('Wall centreline has zero plan length')
            nx, ny = -dy/length*thickness/2, dx/length*thickness/2
            return Polygon([[start[0]+nx,start[1]+ny],[end[0]+nx,end[1]+ny],
                            [end[0]-nx,end[1]-ny],[start[0]-nx,start[1]-ny]])
        return None
    if any(not shapes[0].equals(s) for s in shapes[1:]):
        raise ValueError('Conflicting explicit wall outlines')
    return shapes[0]
