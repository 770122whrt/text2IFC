"""Recover only omitted repeated endpoints in explicit 2.6 polygon profiles."""
from __future__ import annotations

import copy
import math

from shapely.geometry import Polygon

from text2ifc_contract.validation_v2 import validate_v2_document


def recover_polygon_closures(document):
    """Append existing first vertices without moving, guessing or removing points.

    All other contract checks must pass afterwards. This is a derived syntax
    recovery, never a relaxation of the schema or a replacement of raw output.
    Component profiles, arbitrary loops and old schema versions are untouched.
    """
    blocked={'eligible':False}
    if not isinstance(document,dict) or document.get('schema_version')!='bim-json/2.6':
        return blocked
    issues=validate_v2_document(document)
    # An unresolved host ring also prevents checking its filling and layers.
    # These remain mandatory checks on the normalized document below.
    if not issues or any(i.code not in {'OPEN_POLYGON_PROFILE','UNSUPPORTED_LAYER_GEOMETRY',
                                       'BASIC_FILLING_CONSTRAINT_CONFLICT'} for i in issues):
        return blocked
    candidate=copy.deepcopy(document)
    paths=[]
    for index,entity in enumerate(candidate['entities']):
        rep=entity.get('attributes',{}).get('Representation',{})
        profile=rep.get('profile',{})
        if rep.get('kind')!='extruded_profile' or profile.get('kind')!='polygon':
            continue
        points=profile.get('points')
        if not isinstance(points,list) or len(points)<3:
            continue
        if points[0]==points[-1]:
            continue
        if any(not isinstance(p,list) or len(p)!=2 or any(
            type(v) not in {int,float} or not math.isfinite(v) for v in p) for p in points):
            return blocked
        if len({tuple(p) for p in points})!=len(points):
            return blocked
        polygon=Polygon(points)
        if not polygon.is_valid or polygon.is_empty or polygon.area<=0:
            return blocked
        paths.append(f'/entities/{index}/attributes/Representation/profile/points')
        points.append(copy.deepcopy(points[0]))
    if not paths or validate_v2_document(candidate):
        return blocked
    return {'eligible':True,'candidate':candidate,'appended_paths':paths,
            'schema_version':'text2ifc/polygon-closure-recovery/1.0',
            'operation':'append exact first point; preserve all supplied vertices and other fields'}


def recover_repair_polygons(before, after, *, allowed_change_paths, evidence_by_path):
    """Check the model's original changes before authorizing derived closures."""
    from .fact_delta import evaluate_repair_fact_delta
    raw_delta=evaluate_repair_fact_delta(before=before,after=after,
        allowed_change_paths=allowed_change_paths,evidence_by_path=evidence_by_path)
    if not raw_delta['valid']:
        return {'eligible':False,'raw_fact_delta':raw_delta}
    result=recover_polygon_closures(after)
    if not result['eligible']:
        return result
    paths=sorted(set(allowed_change_paths)|set(result['appended_paths']))
    evidence={**evidence_by_path,**{p:['schema:bim-json/2.6:closed-polygon-ring',
                                   'polygon-closure-recovery/1.0: exact first-point append after raw fact preservation passed']
                                  for p in result['appended_paths']}}
    final_delta=evaluate_repair_fact_delta(before=before,after=result['candidate'],
        allowed_change_paths=paths,evidence_by_path=evidence)
    return {**result,'eligible':final_delta['valid'],'raw_fact_delta':raw_delta,
            'fact_delta':final_delta,'allowed_change_paths':paths,'evidence_by_path':evidence}
