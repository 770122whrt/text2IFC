"""Explicit world-axis product bounds; no inferred size, origin or storey offset."""
from collections.abc import Mapping
from math import isfinite, hypot


def world_box_bbox(value):
    """Return metre bounds only for a complete, finite millimetre box contract."""
    if not isinstance(value, Mapping) or value.get("kind") != "world_axis_aligned_box":
        return None
    bounds = value.get("bounds_mm")
    if not isinstance(bounds, Mapping) or set(bounds) != {"x", "y", "z"}:
        return None
    result = {}
    for axis in ("x", "y", "z"):
        pair = bounds[axis]
        if not isinstance(pair, list) or len(pair) != 2 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or
            not isfinite(v) or abs(v) > 100_000_000 for v in pair
        ) or pair[0] >= pair[1]:
            return None
        result[axis] = [v / 1000 for v in pair]
    return result


def basic_railing_bbox(value):
    """New sloping baseline contract; old linear_segment remains horizontal."""
    if not isinstance(value, Mapping) or value.get('kind') != 'basic_railing_segment':
        return None
    start, end = value.get('start_mm'), value.get('end_mm')
    if any(not isinstance(p, list) or len(p) != 3 or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or abs(v)>100_000_000
        for v in p) for p in (start, end)):
        return None
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = hypot(dx, dy)
    template = value.get('template')
    if not isinstance(template, Mapping):
        return None
    from text2ifc_contract.basic_railing import validate_basic_railing
    rep = {**template, 'kind':'basic_railing', 'length':length, 'rise':end[2]-start[2],
           'height':value.get('height_mm'), 'depth':value.get('thickness_mm')}
    if validate_basic_railing(rep, 'IfcRailing'):
        return None
    half = rep['depth']/2
    ox, oy = abs(dy/length)*half, abs(dx/length)*half
    return {'x':[(min(start[0],end[0])-ox)/1000,(max(start[0],end[0])+ox)/1000],
            'y':[(min(start[1],end[1])-oy)/1000,(max(start[1],end[1])+oy)/1000],
            'z':[min(start[2],end[2])/1000,(max(start[2],end[2])+rep['height'])/1000]}
