"""Lossless notation conversion before canonical Brief validation."""
import copy
from .brief_plan_constraints import _number, resolve


def normalize_layout_outlines(brief):
    """Only exact XY rectangles; never approximate a polygon by its bounds."""
    fixed = copy.deepcopy(brief)
    changes = []
    if not isinstance(fixed, dict) or fixed.get('schema_version') != 'text2ifc/design-brief/2.7':
        return fixed, changes
    known = fixed.get('known_facts')
    constraints = known.get('plan_constraints') if isinstance(known, dict) else None
    if not isinstance(constraints, list): return fixed, changes
    for constraint in constraints:
        if not isinstance(constraint, dict) or constraint.get('kind') != 'wall_layout': continue
        pointer = constraint.get('outline_ref')
        try:
            value = resolve(fixed, pointer)
            if not isinstance(value, dict) or set(value) != {'x_min','x_max','y_min','y_max'}: continue
            if not all(_number(v) for v in value.values()): continue
            x1,x2,y1,y2 = (value[k] for k in ['x_min','x_max','y_min','y_max'])
            if x1 >= x2 or y1 >= y2: continue
            ring = [[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]
            parent_pointer, key = pointer.rsplit('/',1)
            parent = known if parent_pointer == '/known_facts' else resolve(fixed,parent_pointer)
            key = key.replace('~1','/').replace('~0','~')
            parent[int(key) if isinstance(parent,list) else key] = ring
            changes.append({'path':pointer,'before':value,'after':ring,
                'rule':'exact-xy-rectangle-to-closed-ring/1.0'})
        except (KeyError,TypeError,ValueError,IndexError):
            # Leave malformed references for the canonical validator to reject.
            continue
    return fixed, changes
