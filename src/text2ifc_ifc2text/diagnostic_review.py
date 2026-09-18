"""Additive diagnostic comparator. Does not change Generation or historic reports.

Match geometry globally before evaluating containment; use mapped hosts to
separate coincident voids. Identity strings are used only to report correspondences.
Material substance/layers and association reference metadata are separate outputs.
"""
from __future__ import annotations

import math
from typing import Any, Callable
from .observation import all_items
from .compare import _angle_delta, _orientation_deg

CATEGORIES = ('walls', 'openings', 'doors', 'windows', 'spaces', 'stairs', 'slabs', 'coverings')
INVALID = 1e12
UNMATCHED = 1e9


def _assignment(left: list, right: list, cost: Callable) -> tuple[list, list, list, list]:
    """Rectangular Hungarian assignment, with one private unmatched column per row."""
    if not left or not right:
        return [], list(left), list(right), []
    matrix = [[cost(a,b) for b in right] for a in left]
    n, m = len(left), len(right) + len(left)
    a = [row + [UNMATCHED] * n for row in matrix]
    u, v, p, way = [0.]*(n+1), [0.]*(m+1), [0]*(m+1), [0]*(m+1)
    for i in range(1,n+1):
        p[0], j0 = i, 0
        minimum, used = [math.inf]*(m+1), [False]*(m+1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], math.inf, 0
            for j in range(1,m+1):
                if not used[j]:
                    current = a[i0-1][j-1]-u[i0]-v[j]
                    if current < minimum[j]:
                        minimum[j], way[j] = current, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(m+1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    pairs, seen_left, seen_right, ambiguous = [], set(), set(), []
    for j in range(1,len(right)+1):
        if p[j] and a[p[j]-1][j-1] < UNMATCHED:
            i = p[j]-1
            pairs.append((left[i],right[j-1]))
            seen_left.add(i); seen_right.add(j-1)
            ties = [k for k,c in enumerate(matrix[i]) if abs(c-matrix[i][j-1]) <= 1e-6]
            if len(ties)>1:
                ambiguous.append({'source':left[i]['label'],
                                  'equal_cost_candidates':[right[k]['label'] for k in ties]})
    return pairs, [x for i,x in enumerate(left) if i not in seen_left], [x for j,x in enumerate(right) if j not in seen_right], ambiguous


def _center(item):
    box=item.get('bounds_mm')
    if not box:
        return None
    values=[(box[k][0]+box[k][1])/2 for k in ('x','y','z')]
    return values if all(math.isfinite(x) for x in values) else None


def _size(item):
    box=item.get('bounds_mm')
    return [box[k][1]-box[k][0] for k in ('x','y','z')] if box else None


def _material_name(value):
    """Normalize presentation-only whitespace without merging distinct materials."""
    if value is None:
        return None
    return str(value).strip()


def _material_content(item):
    result=[]
    for material in item.get('materials',[]):
        kind=material['kind']
        if kind in ('material_layer_set','material_layer_set_usage'):
            result.append({'kind':'layers','layers':[
                {'name':_material_name(l.get('name')), 'thickness_mm':None if l.get('thickness_mm') is None else round(l['thickness_mm'],1)}
                for l in material['layers']]})
        elif kind=='material_list':
            names=[_material_name(v) for v in material['names']]
            result.append({'kind':'list','names':sorted(names,key=lambda x:str(x))})
        elif kind=='single_material':
            result.append({'kind':'single','name':_material_name(material.get('name'))})
        else:
            result.append({'kind':'unsupported','ifc_class':material.get('ifc_class')})
    return result


def _outline(item):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    value=item.get('footprint',{})
    if value.get('status')!='measured_projection':
        return None
    polygons=[Polygon(p['exterior_xy_mm'],p.get('holes_xy_mm',[])) for p in value['polygons']]
    if not polygons or any(not p.is_valid for p in polygons):
        return None
    return unary_union(polygons)


def compare_observations(source: dict[str,Any], candidate: dict[str,Any], *,
                         position_mm: float=20., dimension_mm: float=20., matching_mm: float=2000.) -> dict:
    if not all(math.isfinite(v) and v>0 for v in (position_mm,dimension_mm,matching_mm)):
        raise ValueError('FINITE_POSITIVE_TOLERANCE_REQUIRED')
    report={'schema_version':'text2ifc/diagnostic-review/0.1',
        'alignment':'none; native world coordinates normalized to mm',
        'matching':'global one-to-one assignment by position, bbox size and mapped host; no GUID or label equality',
        'matching_limit_mm':matching_mm,
        'tolerances':{'position_mm':position_mm,'dimension_mm':dimension_mm,'angle_deg':2.},
        'categories':{},'relation_differences':[],'unassessed':[],'matching_ambiguities':[],
        'whole_building_equivalence_certified':False,
        'limitations':['Equal local assignment costs are flagged, not a proof of globally unique identity.',
            'Material-content equality excludes reference metadata; it does not prove equal physical layer orientation.',
            'Projection and bounds do not establish exact 3D shape or traversability.',
            'A corrected comparison is an evaluator change, not a change or improvement of the reconstructed IFC.']}
    floor_pairs,missing_floors,extra_floors,_ = _assignment(source['storeys'],candidate['storeys'],
        lambda a,b: abs(a['elevation_mm']-b['elevation_mm']) if a.get('elevation_mm') is not None and b.get('elevation_mm') is not None and abs(a['elevation_mm']-b['elevation_mm'])<=matching_mm else INVALID)
    floor_map={a['label']:b['label'] for a,b in floor_pairs}
    report['storeys']={'matched':[{'source':a['label'],'candidate':b['label'],
        'elevation_delta_mm':abs(a['elevation_mm']-b['elevation_mm'])} for a,b in floor_pairs],
        'missing':[x['label'] for x in missing_floors],'extra':[x['label'] for x in extra_floors]}
    source_items, candidate_items=list(all_items(source)),list(all_items(candidate))
    for items in (source_items,candidate_items):
        labels=[i['label'] for _,i in items]
        if len(labels)!=len(set(labels)):
            raise ValueError('NONUNIQUE_LOCAL_LABELS')
    mapping={}; all_pairs=[]
    for category in CATEGORIES:
        left=[i for c,i in source_items if c==category]; right=[i for c,i in candidate_items if c==category]
        def cost(a,b):
            ca,cb=_center(a),_center(b)
            if ca is None or cb is None or math.dist(ca,cb)>matching_mm:
                return INVALID
            value=math.dist(ca,cb)+0.25*math.dist(_size(a),_size(b))
            # Host context affects matching but does not impose a hard correctness filter.
            for relation in ('host_wall','opening'):
                expected=mapping.get(a.get(relation))
                if expected is not None and expected!=b.get(relation):
                    value+=matching_mm
            return value
        pairs,missing,extra,ambiguous=_assignment(left,right,cost)
        rows=[]
        report['matching_ambiguities'].extend({'category':category,**v} for v in ambiguous)
        for a,b in pairs:
            mapping[a['label']]=b['label']; all_pairs.append((category,a,b))
            delta=math.dist(_center(a),_center(b))
            size_deltas={k:abs(x-y) for k,x,y in zip(('x','y','z'),_size(a),_size(b))}
            unknown=[]; nominal={}
            fields=('overall_width_mm','overall_height_mm') if category in ('doors','windows') else ()
            if category=='walls':
                if a.get('measurement_method')==b.get('measurement_method'):
                    fields=('length_mm','thickness_mm','height_mm')
                else:
                    unknown.append('wall_intrinsic_dimensions_measurement_method_changed')
            if category=='openings':
                for k in ('width','height','depth'):
                    x,y=a.get('dimensions_mm',{}).get(k),b.get('dimensions_mm',{}).get(k)
                    if x is None or y is None: unknown.append('opening_'+k)
                    else: nominal[k]=abs(x-y)
            for k in fields:
                if a.get(k) is None or b.get(k) is None: unknown.append(k)
                else: nominal[k]=abs(a[k]-b[k])
            angle=_angle_delta(_orientation_deg(a),_orientation_deg(b)) if category=='walls' and a.get('measurement_method')==b.get('measurement_method') else None
            hausdorff,area_delta=None,None
            if category in ('spaces','slabs','coverings'):
                pa,pb=_outline(a),_outline(b)
                if pa is None or pb is None: unknown.append('projected_outline')
                else:
                    hausdorff=float(pa.hausdorff_distance(pb)); area_delta=float(abs(pa.area-pb.area)/1e6)
            if not a.get('storey') or not b.get('storey'): unknown.append('storey')
            if unknown:
                report['unassessed'].append({'category':category,'source':a['label'],'candidate':b['label'],'fields':unknown})
            ma,mb=_material_content(a),_material_content(b)
            rows.append({'source':a['label'],'candidate':b['label'],'source_storey':a.get('storey'),
                'candidate_storey':b.get('storey'),'center_delta_mm':delta,'bbox_size_deltas_mm':size_deltas,
                'nominal_dimension_deltas_mm':nominal,'angle_delta_deg':angle,
                'outline_hausdorff_mm':hausdorff,'outline_area_delta_m2':area_delta,
                'geometry_outside_tolerance':delta>position_mm or any(v>dimension_mm for v in [*size_deltas.values(),*nominal.values()]) or (angle is not None and angle>2.) or (hausdorff is not None and hausdorff>position_mm),
                'material_content_difference':ma!=mb,
                'source_material_content':ma,'candidate_material_content':mb,
                'material_association_metadata_difference':a.get('materials',[])!=b.get('materials',[])})
        report['categories'][category]={'source_count':len(left),'candidate_count':len(right),'matched':rows,
            'missing':[{'source':x['label'],'storey':x.get('storey')} for x in missing],
            'extra':[{'candidate':x['label'],'storey':x.get('storey')} for x in extra]}
        for side,items in (('source',missing),('candidate',extra)):
            report['unassessed'].extend({'category':category,side:x['label'],'fields':['geometry']} for x in items if _center(x) is None)
    for category,a,b in all_pairs:
        for relation in ('storey','host_wall','opening','filling'):
            av,bv=a.get(relation),b.get(relation)
            if av is None and bv is None: continue
            expected=(floor_map if relation=='storey' else mapping).get(av)
            if av is not None and expected is None:
                report['unassessed'].append({'category':category,'source':a['label'],'fields':[relation]})
            elif expected!=bv:
                report['relation_differences'].append({'category':category,'source':a['label'],'candidate':b['label'],
                    'relation':relation,'source_reference':av,'expected_candidate_reference':expected,'actual_candidate_reference':bv})
    rows=[r for c in report['categories'].values() for r in c['matched']]
    report['summary']={'matched':len(rows),'missing':sum(len(c['missing']) for c in report['categories'].values()),
        'extra':sum(len(c['extra']) for c in report['categories'].values()),
        'geometric_deviations':sum(r['geometry_outside_tolerance'] for r in rows),
        'material_content_differences':sum(r['material_content_difference'] for r in rows),
        'material_metadata_differences':sum(r['material_association_metadata_difference'] for r in rows),
        'relation_differences':len(report['relation_differences'])}
    report['unrepresented_classes']={'source':source.get('unrepresented_classes',{}),'candidate':candidate.get('unrepresented_classes',{})}
    return report
