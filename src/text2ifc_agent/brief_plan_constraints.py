"""Analytic checks for explicitly requested orthogonal inside-wall envelopes.

This module consumes typed public Brief facts, never natural-language aliases,
candidate geometry, a scene name, or independent evaluation answers.
"""
from __future__ import annotations

import math
from text2ifc_contract.validation import ValidationIssue

VERSION = 'text2ifc/design-brief/2.4'
VERSIONS = {VERSION, 'text2ifc/design-brief/2.5', 'text2ifc/design-brief/2.6'}
EPS = 1e-6  # Numerical equality in millimetres; not a mesh acceptance tolerance.


def resolve(document, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/known_facts/'):
        raise ValueError('Reference must point inside known_facts.')
    current = document
    for token in pointer[1:].split('/'):
        key = token.replace('~1', '/').replace('~0', '~')
        if isinstance(current,list):
            if not key.isdigit() or str(int(key))!=key:raise ValueError('Array references require canonical nonnegative indices.')
            current=current[int(key)]
        else:current=current[key]
    return current


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _polygon(value):
    if not isinstance(value, list) or not 5 <= len(value) <= 65:
        raise ValueError('Require a simple closed orthogonal ring of 4..64 edges.')
    if any(not isinstance(p, list) or len(p) != 2 or not all(_number(v) for v in p) for p in value):
        raise ValueError('Ring coordinates must be finite XY numbers in millimetres.')
    points = [tuple(p) for p in value]
    if points[0] != points[-1] or len(set(points[:-1])) != len(points)-1:
        raise ValueError('Ring must close once, without repeated vertices.')
    edges = list(zip(points, points[1:]))
    for a,b in edges:
        if (a[0] == b[0]) == (a[1] == b[1]):
            raise ValueError('Zero-length or non-orthogonal edge.')
    if abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in edges)) <= EPS:
        raise ValueError('Ring has zero area.')
    for i,(a,b) in enumerate(edges):
        for j,(c,d) in enumerate(edges[:i]):
            if i-j == 1 or (i == len(edges)-1 and j == 0):
                continue
            if all(max(min(a[k],b[k]), min(c[k],d[k])) <= min(max(a[k],b[k]),max(c[k],d[k])) for k in [0,1]):
                raise ValueError('Nonadjacent boundary edges intersect or touch.')
    return points,edges


def _bounds(wall):
    value=wall.get('bounds')
    if not isinstance(value,dict) or set(value) != {'x','y'}:
        raise ValueError('Constrained walls require canonical XY solid bounds.')
    for axis in ['x','y']:
        a=value[axis]
        if not isinstance(a,list) or len(a)!=2 or not all(_number(v) for v in a) or a[1]-a[0] <= EPS:
            raise ValueError('Wall bounds must be finite positive extents.')
    return value['x'][0],value['x'][1],value['y'][0],value['y'][1]


def constraint_context(brief, constraint):
    points,edges=_polygon(resolve(brief,constraint['outline_ref']))
    storey=resolve(brief,constraint['storey_ref'])
    walls=storey['walls']
    if not isinstance(walls,dict) or set(walls) - {'exterior','interior'}:
        raise ValueError('Constrained storey walls use exterior/interior lists, with no omitted wall groups.')
    records=[]
    for role in ['exterior','interior']:
        values=walls.get(role,[])
        if not isinstance(values,list):raise ValueError('Wall groups must be arrays.')
        for i,wall in enumerate(values):
            if not isinstance(wall,dict) or not isinstance(wall.get('id'),str) or not wall['id']:raise ValueError('Wall ID required.')
            if role=='exterior' and wall.get('thickness_mm',constraint['thickness_mm']) != constraint['thickness_mm']:
                raise ValueError('Wall thickness and envelope thickness disagree; do not overwrite explicit values.')
            records.append({'id':wall['id'],'role':role,'bounds':_bounds(wall),
                'path':constraint['storey_ref']+f'/walls/{role}/{i}/bounds'})
            if wall['id'] in constraint['derived_wall_ids'] and any(k in wall for k in ['start_mm','end_mm']):
                raise ValueError('Derived solid bounds cannot have competing centerline coordinates.')
    ids=[w['id'] for w in records]
    if not 1 <= len(records) <= 64 or len(set(ids)) != len(ids):raise ValueError('Require 1..64 uniquely identified walls.')
    if not any(w['role']=='exterior' for w in records):raise ValueError('Exterior walls required.')
    if not set(constraint['derived_wall_ids']).issubset(ids):raise ValueError('Unknown derived wall ID.')
    return points,edges,records


def _inside(x,y,edges):
    return sum(1 for a,b in edges if a[0]==b[0] and min(a[1],b[1]) < y < max(a[1],b[1]) and a[0]>x)%2 == 1


def _distance(x,y,edge):
    a,b=edge
    return max(max(min(a[0],b[0])-x,0,x-max(a[0],b[0])),
               max(min(a[1],b[1])-y,0,y-max(a[1],b[1])))


def _failures(points,edges,records,thickness):
    # Partition at every relevant boundary. Testing one interior point per cell
    # is exact for these axis-aligned unions, including concave corners.
    xs={p[0]+d for p in points for d in [-thickness,0,thickness]}
    ys={p[1]+d for p in points for d in [-thickness,0,thickness]}
    for w in records:
        x1,x2,y1,y2=w['bounds'];xs.update([x1,x2]);ys.update([y1,y2])
    xs=sorted(xs);ys=sorted(ys);found={}
    for x1,x2 in zip(xs,xs[1:]):
        for y1,y2 in zip(ys,ys[1:]):
            if min(x2-x1,y2-y1)<=EPS:continue
            x=(x1+x2)/2;y=(y1+y2)/2
            owners=[w for w in records if w['bounds'][0]<x<w['bounds'][1] and w['bounds'][2]<y<w['bounds'][3]]
            inside=_inside(x,y,edges)
            band=inside and min(_distance(x,y,e) for e in edges)<thickness-EPS
            kind=('outside' if owners and not inside else 'overlap' if len(owners)>1 else
                  'gap' if band and not owners else 'boundary_depth' if owners and not band and
                  any(w['role']=='exterior' for w in owners) else None)
            if kind and kind not in found:found[kind]={'cell_mm':[x1,x2,y1,y2],'wall_ids':[w['id'] for w in owners]}
    return found


def validate_plan_constraints(brief, conversation=None):
    if brief.get('schema_version') not in VERSIONS:return []
    constraints=brief.get('known_facts',{}).get('plan_constraints',[])
    issues=[];seen=set();storeys=set()
    user_turns=None if conversation is None else {t.get('turn_id') for t in conversation if t.get('role')=='user'}
    for i,c in enumerate(constraints):
        path=f'/known_facts/plan_constraints/{i}'
        try:
            if c['id'] in seen or c['storey_ref'] in storeys:raise ValueError('Duplicate constraint ID or constrained storey.')
            seen.add(c['id']);storeys.add(c['storey_ref'])
            if user_turns is not None and not set(c['source_turns']).issubset(user_turns):raise ValueError('Constraint must cite actual user turns.')
            points,edges,records=constraint_context(brief,c)
            if brief.get('status')!='ready':continue
            for kind,evidence in _failures(points,edges,records,c['thickness_mm']).items():
                issues.append(ValidationIssue('BRIEF_PLAN_GEOMETRY',path,
                    f'{kind}: {evidence}; correct only declared derived wall bounds; preserve all explicit facts.'))
        except (KeyError,TypeError,ValueError,IndexError) as error:
            issues.append(ValidationIssue('BRIEF_PLAN_CONTRACT',path,str(error)))
    return issues


def derived_bound_paths(brief, constraint_indices=None):
    paths=[]
    for i,c in enumerate(brief['known_facts']['plan_constraints']):
        if constraint_indices is not None and i not in constraint_indices:continue
        _,_,records=constraint_context(brief,c)
        paths.extend(w['path'] for w in records if w['id'] in c['derived_wall_ids'])
    return sorted(set(paths))


def fixed_plan_conflict(brief):
    """A fixed wall outside/deep inside, or two fixed walls overlapping, cannot
    be corrected by changing another derived wall. Do not spend a repair call.
    """
    for c in brief['known_facts']['plan_constraints']:
        points,edges,records=constraint_context(brief,c)
        fixed=[w for w in records if w['id'] not in c['derived_wall_ids']]
        failures=_failures(points,edges,fixed,c['thickness_mm'])
        if {'outside','overlap','boundary_depth'} & failures.keys():return True
    return False
