"""Conservative world-coordinate diagnostic comparison; no GUID equality shortcuts."""
from __future__ import annotations

import json
import math
from pathlib import Path

from .compare import _greedy_match, _angle_delta, _orientation_deg
from .observation import all_items, extract_description_facts


def _center(item):
    b = item.get('bounds_mm')
    return [(b[k][0]+b[k][1])/2 for k in ('x','y','z')] if b else None


def _features(category, item):
    result = {}
    if item.get('bounds_mm'):
        result.update({f'bounds_size_{k}': v[1]-v[0] for k,v in item['bounds_mm'].items()})
    fields = ('length_mm','thickness_mm','height_mm') if category=='walls' else ('overall_width_mm','overall_height_mm')
    for key in fields:
        if item.get(key) is not None:
            result[key] = item[key]
    if category == 'openings':
        result.update(item.get('dimensions_mm',{}))
    return result


def compare_roundtrip(source_path, candidate_path, *, position_mm=20.0, dimension_mm=20.0):
    if position_mm <= 0 or dimension_mm <= 0:
        raise ValueError('POSITIVE_TOLERANCES_REQUIRED')
    import ifcopenshell
    try:
        ifcopenshell.open(str(source_path))
        ifcopenshell.open(str(candidate_path))
    except Exception as error:
        return {'schema_version':'text2ifc/ifc2text-roundtrip-compare/0.2',
                'status':{'files_readable':False,'geometry_processable':None,'reconstruction_consistent':None},
                'error_type':type(error).__name__}
    try:
        source = extract_description_facts(source_path)
        candidate = extract_description_facts(candidate_path)
    except Exception as error:
        return {'schema_version':'text2ifc/ifc2text-roundtrip-compare/0.2',
                'status':{'files_readable':True,'geometry_processable':False,'reconstruction_consistent':None},
                'error_type':type(error).__name__}
    floor_pairs, missing_floors, extra_floors = _greedy_match(source['storeys'],candidate['storeys'],
        lambda a,b: abs(a['elevation_mm']-b['elevation_mm']) if a.get('elevation_mm') is not None and b.get('elevation_mm') is not None else math.inf,
        max_cost=2000.0)
    floor_map = {a['label']:b['label'] for a,b,_ in floor_pairs}
    report = {'schema_version':'text2ifc/ifc2text-roundtrip-compare/0.2',
        'alignment':'none; description uses source world coordinates in metres',
        'identity_policy':'one_to_one_geometry_matching_not_GUID_equality',
        'matching_limit_mm':2000, 'tolerances':{'position_mm':position_mm,'dimension_mm':dimension_mm,'angle_deg':2.0},
        'source':source['source'],'candidate':candidate['source'],
        'storeys':{'matched':[{'source':a['label'],'candidate':b['label'],'elevation_delta_mm':d} for a,b,d in floor_pairs],
                   'missing':[a['label'] for a in missing_floors],'extra':[b['label'] for b in extra_floors]},
        'components':{},'relationship_differences':[], 'unassessed':[],
        'limitations':['greedy assignment is diagnostic; crowded/repeated elements may be ambiguous',
                       'world bounding boxes and wall axes do not prove detailed mesh equality',
                       'room connectivity, stair treads and unrepresented classes are not certified'],
    }
    source_items = list(all_items(source))
    candidate_items = list(all_items(candidate))
    identity_map = {}
    matched_items = []
    deviation_count = sum(d > position_mm for _,_,d in floor_pairs)
    for category in ('walls','doors','windows','openings','spaces','stairs','slabs','coverings'):
        left = [i for c,i in source_items if c==category]
        right = [i for c,i in candidate_items if c==category]
        def cost(a,b):
            if a.get('storey') is not None and floor_map.get(a['storey']) != b.get('storey'):
                return math.inf
            ca,cb = _center(a),_center(b)
            return math.dist(ca,cb) if ca is not None and cb is not None else math.inf
        pairs, missing, extra = _greedy_match(left,right,cost,max_cost=2000.0)
        records = []
        for a,b,distance in pairs:
            identity_map[a['label']] = b['label']
            matched_items.append((category,a,b))
            fa,fb = _features(category,a),_features(category,b)
            deltas = {key:abs(fa[key]-fb[key]) for key in fa.keys() & fb.keys()}
            unknown = sorted(fa.keys() ^ fb.keys())
            angle = _angle_delta(_orientation_deg(a),_orientation_deg(b)) if category=='walls' else None
            changed = distance > position_mm or any(d > dimension_mm for d in deltas.values()) or (angle is not None and angle>2)
            if category in ('walls','doors','windows'):
                required = ('length_mm','thickness_mm','height_mm') if category=='walls' else ('overall_width_mm','overall_height_mm')
                unknown += [key for key in required if key not in fa or key not in fb]
            if not a.get('storey') or not b.get('storey'):
                unknown.append('storey')
            if unknown:
                report['unassessed'].append({'category':category,'source':a['label'],'candidate':b['label'],'fields':sorted(set(unknown))})
            def material_values(item):
                return [{k:v for k,v in m.items() if k not in ('origin','type_name','parser')} for m in item.get('materials',[])]
            ma,mb = material_values(a),material_values(b)
            material_delta = ma != mb
            changed |= material_delta
            records.append({'source':a['label'],'candidate':b['label'], 'storey_source':a.get('storey'),
                            'storey_candidate':b.get('storey'), 'center_delta_mm':distance,
                            'dimension_deltas_mm':deltas,'angle_delta_deg':angle,
                            'material_difference':material_delta,'outside_tolerance':bool(changed)})
            deviation_count += int(changed)
        def unmatched(item):
            return {'label':item['label'],'storey':item.get('storey'),
                    'geometry_measured':_center(item) is not None}
        for item in missing+extra:
            if _center(item) is None:
                report['unassessed'].append({'category':category,'entity':item['label'],'fields':['geometry']})
        report['components'][category] = {'matched':records,'missing':[unmatched(i) for i in missing],
                                          'extra':[unmatched(i) for i in extra]}
    for category,a,b in matched_items:
        for relation in ('host_wall','opening','filling'):
            src_ref, dst_ref = a.get(relation),b.get(relation)
            if src_ref is None and dst_ref is None:
                continue
            expected = identity_map.get(src_ref)
            if src_ref is not None and expected is None:
                report['unassessed'].append({'category':category,'source':a['label'],'fields':[relation]})
            elif expected != dst_ref:
                report['relationship_differences'].append({'category':category,'source':a['label'],
                    'candidate':b['label'],'relation':relation,'expected':expected,'actual':dst_ref})
    missing_count = len(missing_floors)+sum(len(v['missing']) for v in report['components'].values())
    extra_count = len(extra_floors)+sum(len(v['extra']) for v in report['components'].values())
    report['summary'] = {'missing_count':missing_count,'extra_count':extra_count,'deviation_count':deviation_count,
                         'relationship_difference_count':len(report['relationship_differences'])}
    any_diff = any(report['summary'].values())
    measured = bool(source_items) and not report['unassessed']
    report['unrepresented_classes'] = {'source':source['unrepresented_classes'],'candidate':candidate['unrepresented_classes']}
    geometry_processable = bool(source_items) and all(_center(i) is not None for _,i in source_items+candidate_items)
    report['status'] = {'files_readable':True,'geometry_processable':geometry_processable,
        'evaluated_scope_consistent':False if any_diff else (True if measured else None),
        # Detailed shapes, space topology and all source classes are not proven by this baseline.
        'reconstruction_consistent':False if any_diff else None}
    return report
