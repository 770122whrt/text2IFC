"""Versioned, finite parameterized solids. No arbitrary executable geometry."""
from __future__ import annotations

import copy
import math

from .geometry_v2 import _validate_position
from .validation import ValidationIssue

MAX_PARTS = 512
MAX_SOLIDS = 2048
MAX_COORDINATE = 100_000_000


def expanded_parts(representation):
    """Expand translation in the parent product frame, without modifying input."""
    result = []
    for part in representation['parts']:
        repeat = part.get('repeat')
        for index in range(repeat['count'] if repeat else 1):
            item = copy.deepcopy(part)
            item.pop('repeat', None)
            if repeat:
                item['id'] = f"{part['id']}-{index + 1:03d}"
                item['placement']['origin'] = [x + index*s for x,s in zip(part['placement']['origin'], repeat['step'])]
            result.append(item)
    return result


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _on(a, b, p):
    return abs(_cross(a,b,p)) <= 1e-9 and all(min(x,y)-1e-9 <= v <= max(x,y)+1e-9 for x,y,v in zip(a,b,p))


def _intersect(a,b,c,d):
    if any((_on(a,b,c), _on(a,b,d), _on(c,d,a), _on(c,d,b))):
        return True
    return (_cross(a,b,c)>0) != (_cross(a,b,d)>0) and (_cross(c,d,a)>0) != (_cross(c,d,b)>0)


def _inside(point, ring):
    inside = False
    x,y = point
    for a,b in zip(ring,ring[1:]):
        if _on(a,b,point):
            return False
        if (a[1]>y) != (b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def polygon_problem(profile):
    rings = [profile['points'], *profile.get('holes', [])]
    for ring in rings:
        if ring[0] != ring[-1] or len({tuple(p) for p in ring[:-1]}) != len(ring)-1:
            return 'Rings must be closed with distinct vertices.'
        edges = list(zip(ring,ring[1:]))
        if abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in edges)) <= 1e-9:
            return 'Ring has zero area.'
        for i,(a,b) in enumerate(edges):
            for j,(c,d) in enumerate(edges):
                if j <= i+1 or (i == 0 and j == len(edges)-1):
                    continue
                if _intersect(a,b,c,d):
                    return 'Ring self-intersects.'
    for i,hole in enumerate(rings[1:], 1):
        if not all(_inside(p,rings[0]) for p in hole[:-1]):
            return 'Hole must be strictly inside the outer ring.'
        for other in rings[:i]:
            if any(_intersect(a,b,c,d) for a,b in zip(hole,hole[1:]) for c,d in zip(other,other[1:])):
                return 'Ring boundaries intersect or touch.'
        for other in rings[1:i]:
            if _inside(hole[0],other) or _inside(other[0],hole):
                return 'Holes overlap or nest.'
    return None


def validate_components(rep, ifc_class, path):
    """Called after structural validation; refuses unsupported or ambiguous inputs."""
    issues = []
    def fail(code, suffix, message):
        issues.append(ValidationIssue(code, path+suffix, message))
    if ifc_class not in {'IfcDoor','IfcWindow'}:
        fail('UNSUPPORTED_COMPONENT_PRODUCT', '', 'Component geometry currently supports IfcDoor and IfcWindow only.')
    def finite(value, suffix=''):
        if isinstance(value, dict):
            for k,v in value.items(): finite(v, suffix+'/'+k)
        elif isinstance(value, list):
            for k,v in enumerate(value): finite(v, suffix+'/'+str(k))
        elif isinstance(value, (int,float)) and not isinstance(value,bool):
            if not math.isfinite(value) or abs(value)>MAX_COORDINATE:
                fail('INVALID_COMPONENT_NUMBER', suffix, 'A finite bounded number is required.')
    finite(rep)
    if issues: return issues
    definitions = {d['id']:d for d in rep['definitions']}
    if len(definitions) != len(rep['definitions']):
        fail('DUPLICATE_GEOMETRY_ID', '/definitions', 'Geometry definition IDs must be unique within a product.')
    count = sum(p.get('repeat',{}).get('count',1) for p in rep['parts'])
    solids = sum(p.get('repeat',{}).get('count',1)*len(p['geometry_refs']) for p in rep['parts'])
    if count > MAX_PARTS or solids > MAX_SOLIDS:
        fail('COMPONENT_EXPANSION_LIMIT', '/parts', f'At most {MAX_PARTS} parts and {MAX_SOLIDS} solids after expansion.')
        return issues
    ids = set(); used = set()
    for part in rep['parts']:
        if 'repeat' in part and math.sqrt(sum(x*x for x in part['repeat']['step'])) <= 1e-9:
            fail('ZERO_REPEAT_STEP','/parts','Repeated instances need a nonzero translation; coincident duplicates are refused.')
    for i,p in enumerate(expanded_parts(rep)):
        if p['id'] in ids: fail('DUPLICATE_PART_ID', '/parts', f"Repeated part identity {p['id']}.")
        ids.add(p['id'])
        issues.extend(_validate_position(p['placement'], path+'/parts/'+str(i)+'/placement'))
        if len(p['geometry_refs']) != len(set(p['geometry_refs'])):
            fail('DUPLICATE_GEOMETRY_OWNERSHIP','/parts', 'A solid must not be instantiated twice within one part.')
        for ref in p['geometry_refs']:
            used.add(ref)
            if ref not in definitions: fail('UNRESOLVED_COMPONENT_GEOMETRY','/parts', f'Unknown local geometry definition {ref}.')
    if set(definitions)-used: fail('UNUSED_COMPONENT_GEOMETRY','/definitions', 'Every definition must be used by a part.')
    for i,d in enumerate(rep['definitions']):
        base = '/definitions/'+str(i)
        issues.extend(_validate_position(d['position'],path+base+'/position'))
        magnitude = math.sqrt(sum(x*x for x in d['direction']))
        if magnitude <= 1e-9 or abs(d['direction'][2])/magnitude <= 1e-9:
            fail('INVALID_EXTRUSION_DIRECTION',base+'/direction','Extrusion must leave the profile plane.')
        if d['profile']['kind'] == 'polygon':
            problem = polygon_problem(d['profile'])
            if problem: fail('INVALID_COMPONENT_POLYGON',base+'/profile',problem)
    return issues
