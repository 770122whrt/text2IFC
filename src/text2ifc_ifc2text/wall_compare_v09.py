"""Wall-only v0.9 policy: 0.1 mm, native world coordinates, no best-fit alignment.

The historical 20 mm comparator and committed reports remain unchanged. This
module evaluates wall bodies before/after openings and sampled horizontal cuts;
it does not certify arbitrary curved surfaces, load-bearing safety or materials.
"""
from __future__ import annotations
import math
from typing import Any
import numpy as np
import ifcopenshell.geom
from shapely import hausdorff_distance
from shapely.geometry import Polygon, LineString, GeometryCollection
from shapely.ops import unary_union

WALL_TOLERANCE_MM=.1
VERSION='text2ifc/wall-compare/0.9'


def wall_mesh(entity: Any, *, subtract_openings: bool=True):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS,not subtract_openings)
    shape=ifcopenshell.geom.create_shape(settings,entity)
    vertices=np.asarray(shape.geometry.verts,dtype=float).reshape((-1,3))*1000.
    faces=np.asarray(shape.geometry.faces,dtype=int).reshape((-1,3))
    if not len(vertices) or not len(faces) or not np.isfinite(vertices).all():
        raise ValueError('WALL_MESH_UNAVAILABLE_OR_NONFINITE')
    return vertices,faces


def footprint(vertices,faces):
    polygons=[]
    for face in faces:
        p=Polygon(vertices[face,:2])
        if p.is_valid and p.area>1e-8:polygons.append(p)
    if not polygons:raise ValueError('WALL_FOOTPRINT_UNAVAILABLE')
    return unary_union(polygons)


def section_boundary(vertices,faces,z):
    """Intersect triangle surfaces with a world XY plane, including void boundaries."""
    segments=[]
    eps=1e-8
    for face in faces:
        triangle=vertices[face]; dz=triangle[:,2]-z
        if np.all(dz>eps) or np.all(dz<-eps) or np.all(np.abs(dz)<=eps):continue
        hits=[]
        for i,j in ((0,1),(1,2),(2,0)):
            a,b=triangle[i],triangle[j]; da,db=dz[i],dz[j]
            if abs(da)<=eps:hits.append(a[:2])
            if da*db<0:hits.append((a+(b-a)*(-da/(db-da)))[:2])
        unique=[]
        for p in hits:
            if not any(np.linalg.norm(p-q)<=eps for q in unique):unique.append(p)
        if len(unique)==2 and np.linalg.norm(unique[0]-unique[1])>eps:
            segments.append(LineString(unique))
    return unary_union(segments) if segments else GeometryCollection()


def volume_mm3(vertices,faces):
    # Re-centering is only numerical conditioning of the volume integral, not alignment.
    vv=vertices-vertices.mean(axis=0)
    t=vv[faces]
    return float(abs(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum())/6.)


def _compare_meshes(a,b,*,tolerance_mm):
    va,fa=a;vb,fb=b
    ba=np.array([va.min(axis=0),va.max(axis=0)])
    bb=np.array([vb.min(axis=0),vb.max(axis=0)])
    dims=np.abs(np.diff(ba,axis=0)[0]-np.diff(bb,axis=0)[0])
    center=float(np.linalg.norm(ba.mean(axis=0)-bb.mean(axis=0)))
    coord=float(np.max(np.abs(ba-bb)))
    pa,pb=footprint(va,fa),footprint(vb,fb)
    planar=float(hausdorff_distance(pa.boundary,pb.boundary,densify=.1))
    sections=[]
    for f in (.01,.25,.5,.75,.99):
        z=float(ba[0,2]+f*(ba[1,2]-ba[0,2]))
        sa=section_boundary(va,fa,z);sb=section_boundary(vb,fb,z)
        if sa.is_empty and sb.is_empty:
            sections.append({'z_mm':z,'distance_mm':None,'assessed':False,'reason':'both_empty'})
        elif sa.is_empty or sb.is_empty:
            sections.append({'z_mm':z,'distance_mm':None,'assessed':True,'pass':False,'reason':'one_empty'})
        else:
            d=float(hausdorff_distance(sa,sb,densify=.1))
            sections.append({'z_mm':z,'distance_mm':d,'assessed':True,'pass':bool(d<=tolerance_mm)})
    vol_a,vol_b=volume_mm3(va,fa),volume_mm3(vb,fb)
    passed=bool(center<=tolerance_mm and coord<=tolerance_mm and max(dims)<=tolerance_mm
                and planar<=tolerance_mm and all(s.get('pass',False) for s in sections))
    return {'pass':passed,'bbox_coordinate_max_delta_mm':coord,'bbox_center_delta_mm':center,
            'bbox_size_deltas_mm':dict(zip('xyz',map(float,dims))),
            'source_bounds_mm':{k:[float(ba[0,i]),float(ba[1,i])] for i,k in enumerate('xyz')},
            'candidate_bounds_mm':{k:[float(bb[0,i]),float(bb[1,i])] for i,k in enumerate('xyz')},
            'projected_boundary_distance_mm':planar,'projected_symmetric_difference_mm2':float(pa.symmetric_difference(pb).area),
            'sections':sections,'source_volume_mm3':vol_a,'candidate_volume_mm3':vol_b,
            'volume_difference_mm3':abs(vol_a-vol_b),'volume_is_report_only':True}


def compare_wall_entities(source,candidate,*,tolerance_mm=WALL_TOLERANCE_MM):
    if not math.isfinite(tolerance_mm) or tolerance_mm<=0:raise ValueError('FINITE_POSITIVE_TOLERANCE_REQUIRED')
    report={'schema_version':VERSION,'tolerance_mm':tolerance_mm,'alignment':'none',
            'metric':'world bbox, projected boundary and five horizontal surface sections; densified discrete Hausdorff',
            'material_or_relationship_equality_certified':False,'full_surface_equivalence_certified':False}
    for key,subtract in (('before_openings',False),('with_openings',True)):
        try:
            report[key]=_compare_meshes(wall_mesh(source,subtract_openings=subtract),wall_mesh(candidate,subtract_openings=subtract),tolerance_mm=tolerance_mm)
        except (RuntimeError,ValueError,TypeError) as e:
            report[key]={'pass':False,'unassessed':True,'error_type':type(e).__name__}
    report['pass']=all(report[k]['pass'] for k in ('before_openings','with_openings'))
    return report


def compare_with_wall_policy(source_facts,candidate_facts):
    """Keep historic matching and non-wall thresholds, apply 0.1 mm to wall scalars.

    Detailed wall-body comparisons must also be attached by the file-level runner.
    Unknown intrinsic dimensions remain unknown; no new equivalence claim is made.
    """
    from .diagnostic_review import compare_observations
    report=compare_observations(source_facts,candidate_facts)
    report['schema_version']='text2ifc/diagnostic-review/0.2'
    report['tolerances']={'walls':{'position_mm':.1,'dimension_mm':.1,'outline_mm':.1},
        'other_categories_legacy':{'position_mm':20.,'dimension_mm':20.},
        'angle_deg_legacy':2.,'note':'0.1 mm applies to walls; other categories retain historical settings, not a new approval'}
    for row in report['categories']['walls']['matched']:
        row['scalar_tolerance_mm']=.1
        values=[row['center_delta_mm'],*row['bbox_size_deltas_mm'].values(),*row['nominal_dimension_deltas_mm'].values()]
        if row['outline_hausdorff_mm'] is not None:values.append(row['outline_hausdorff_mm'])
        row['geometry_outside_tolerance']=any(v>.1 for v in values) or (row['angle_delta_deg'] is not None and row['angle_delta_deg']>2.)
    report['summary']['geometric_deviations']=sum(r['geometry_outside_tolerance'] for c in report['categories'].values() for r in c['matched'])
    return report
