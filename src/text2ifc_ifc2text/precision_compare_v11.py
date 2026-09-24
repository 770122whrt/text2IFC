"""Inclusive 1 mm comparison policy, retaining v1.0 raw measurements/evidence."""
from __future__ import annotations
import copy
import math
from . import precision_compare_v10 as previous

VERSION='text2ifc/ifc2text-roundtrip-compare/1.1'
LINEAR_TOLERANCE_MM=1.0
NUMERIC_EPSILON_MM=1e-9

def outside_linear_tolerance(value):
    return not math.isfinite(value) or value > LINEAR_TOLERANCE_MM+NUMERIC_EPSILON_MM

def _material_equal(a,b):
    if isinstance(a,dict):
        if not isinstance(b,dict) or a.keys()!=b.keys(): return False
        return all(((x is None and b[k] is None) or
                    (x is not None and b[k] is not None and not outside_linear_tolerance(abs(x-b[k]))))
                   if k=='thickness_mm' else _material_equal(x,b[k]) for k,x in a.items())
    if isinstance(a,list):
        return isinstance(b,list) and len(a)==len(b) and all(_material_equal(x,y) for x,y in zip(a,b))
    return a==b

def rescore(measured):
    """Apply the approved threshold without re-matching or altering measurements."""
    report=copy.deepcopy(measured)
    report['measurement_schema_version']=measured['schema_version']
    report['schema_version']=VERSION
    if 'categories' not in report: return report
    report['tolerances']={**report['tolerances'],
        **{key:1.0 for key in ('linear_mm','position_mm','dimension_mm','storey_elevation_mm','outline_mm','material_layer_thickness_mm')},
        'boundary':'error <= 1 mm accepted; error > 1 mm fails','numeric_epsilon_mm':NUMERIC_EPSILON_MM}
    for floor in report['storeys']['matched']:
        floor['outside_tolerance']=outside_linear_tolerance(floor['elevation_delta_mm'])
    for category in report['categories'].values():
        for row in category['matched']:
            values=[row['center_delta_mm'],row['bbox_coordinate_max_delta_mm'],*row['bbox_size_deltas_mm'].values(),
                    *row['nominal_dimension_deltas_mm'].values()]
            if row['outline_hausdorff_mm'] is not None: values.append(row['outline_hausdorff_mm'])
            failed=any(outside_linear_tolerance(v) for v in values) or (
                row['angle_delta_deg'] is not None and row['angle_delta_deg']>2.)
            wall=row.get('wall_geometry')
            if wall:
                wall.update(schema_version='text2ifc/wall-compare/1.1',tolerance_mm=1.,boundary=report['tolerances']['boundary'])
                for key in ('before_openings','with_openings'):
                    part=wall[key]
                    if part.get('unassessed'): continue
                    distances=[part['bbox_coordinate_max_delta_mm'],part['bbox_center_delta_mm'],
                        *part['bbox_size_deltas_mm'].values(),part['projected_boundary_distance_mm']]
                    for section in part['sections']:
                        if section.get('distance_mm') is not None:
                            section['pass']=not outside_linear_tolerance(section['distance_mm'])
                    part['pass']=not any(outside_linear_tolerance(v) for v in distances) and all(s.get('pass',False) for s in part['sections'])
                    failed|=not part['pass']
                wall['pass']=all(wall[key].get('pass',False) for key in ('before_openings','with_openings'))
            row['geometry_outside_tolerance']=failed
            row['material_content_difference']=not _material_equal(row['source_material_content'],row['candidate_material_content'])
    file_status={key:report['status'].get(key) for key in ('files_readable','geometry_processable')}
    previous._summarize(report)
    report['status'].update(file_status)
    return report

def compare_observations(source,candidate,*,matching_mm=2000.):
    return rescore(previous.compare_observations(source,candidate,matching_mm=matching_mm))

def compare_roundtrip(source_path,candidate_path,*,original_source_path=None):
    return rescore(previous.compare_roundtrip(source_path,candidate_path,original_source_path=original_source_path))
