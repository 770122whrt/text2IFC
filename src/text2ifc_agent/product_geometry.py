"""Explicit world-axis product bounds; no inferred size, origin or storey offset."""
from collections.abc import Mapping
from math import isfinite


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
