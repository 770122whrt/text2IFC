"""Deterministic lowering of explicit geometry facts into existing BIM JSON.

Bounds are expressed in the named parent's local frame, in document units.
This module does not infer anchors, convert units, or repair model candidates.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Sequence


def rectangular_prism_attributes(
    *, relative_to: str, lower: Sequence[float], upper: Sequence[float],
) -> dict:
    """Encode a parent-axis-aligned box as a centered XY profile extruded in +Z.

    Parent rotation and elevation are inherited once by ObjectPlacement. The
    caller must resolve the parent and supply explicit bounds before calling.
    """
    if not isinstance(relative_to, str) or not relative_to.strip():
        raise ValueError('An explicit parent identity is required')
    low, high = _point(lower), _point(upper)
    spans = [b-a for a,b in zip(low, high)]
    if any(not math.isfinite(size) or size <= 0 for size in spans):
        raise ValueError('Bounds must define a finite positive volume')
    return {
        'ObjectPlacement': {
            'relative_to': relative_to,
            'origin': [low[0]+spans[0]/2, low[1]+spans[1]/2, low[2]],
            'axis': [0,0,1], 'ref_direction': [1,0,0],
        },
        'Representation': {
            'kind': 'extruded_profile',
            'profile': {'kind':'rectangle', 'x':spans[0], 'y':spans[1]},
            'depth': spans[2], 'direction': [0,0,1],
        },
    }


def _point(value: Sequence[float]) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError('Bounds require explicit three-coordinate points')
    if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) for v in value):
        raise ValueError('Bound coordinates must be finite numbers')
    return [float(v) for v in value]
