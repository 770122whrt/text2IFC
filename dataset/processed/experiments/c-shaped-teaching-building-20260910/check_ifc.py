"""Frozen request evaluator. Reads native IFC, never candidate coverage claims."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as element
import numpy as np

def check_ifc(path):
    expected=json.loads((Path(__file__).parent/'frozen-expectations.json').read_text(encoding='utf-8'))
    model=ifcopenshell.open(str(path))
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    cache={};checks={}
    def check(name,value): checks[name]=bool(value)
    def near(a,b): return bool(np.allclose(a,b,atol=1e-6,rtol=0))
    def mesh(e):
        if e.id() not in cache:
            shape=ifcopenshell.geom.create_shape(settings,e)
            cache[e.id()]=(np.array(shape.geometry.verts).reshape(-1,3),np.array(shape.geometry.faces).reshape(-1,3))
        return cache[e.id()]
    def box(e):
        v,_=mesh(e);return np.array([v.min(axis=0),v.max(axis=0)]).T
    def volume(e):
        v,f=mesh(e);t=v[f]
        return abs(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
    def covers(e,x,y):
        v,f=mesh(e);t=v[f]
        t=t[np.ptp(t[:,:,2],axis=1)<1e-7]
        for tri in t:
            a,b,c=tri[:,:2];mat=np.array([b-a,c-a]).T
            if abs(np.linalg.det(mat))<1e-10:continue
            u,w=np.linalg.solve(mat,np.array([x,y])-a)
            if min(u,w)>=-1e-7 and u+w<=1+1e-7:return True
        return False
    def materials(e):
        return [m.Name.lower() for m in element.get_materials(e)]
    def styles(e):
        rows=[]
        for rep in e.Representation.Representations:
            for item in rep.Items:
                for styled in item.StyledByItem:
                    for assignment in styled.Styles:
                        for style in assignment.Styles if assignment.is_a('IfcPresentationStyleAssignment') else [assignment]:
                            if style.is_a('IfcSurfaceStyle'):
                                for shading in style.Styles:
                                    if shading.is_a('IfcSurfaceStyleShading'):
                                        rgb=shading.SurfaceColour
                                        rows.append(([rgb.Red,rgb.Green,rgb.Blue],getattr(shading,'Transparency',0) or 0))
        return rows
    check('schema',model.schema=='IFC2X3')
    units=model.by_type('IfcSIUnit')
    check('units_mm',any(u.UnitType=='LENGTHUNIT' and u.Name=='METRE' and u.Prefix=='MILLI' for u in units))
    for kind,count in expected['counts'].items():check('count:'+kind,len(model.by_type(kind))==count)
    levels=[0,3.15,6.3]
    check('storey_elevations',near(sorted(s.Elevation for s in model.by_type('IfcBuildingStorey')),[0,3150,6300]))
    walls=model.by_type('IfcWall')
    plates=[*model.by_type('IfcSlab'),*[r for r in model.by_type('IfcRoof') if r.Representation]]
    check('four_physical_floor_roof_plates',len(plates)==4)
    check('wall_material',all(materials(w) and all(m in ('brick','砖') for m in materials(w)) for w in walls))
    check('wall_count',len(walls)==30)
    wall_centres=[(.1,8.4),(6.6,.1),(6.6,16.7),(13.1,2.4),(13.1,14.4),
        (9,4.7),(9,12.1),(4.7,8.4),(4.7,2.4),(4.7,14.4)]
    for z in levels:
        current=[w for w in walls if near(box(w)[2],[z,z+3])]
        check(f'walls_{z}:level_count',len(current)==10)
        check(f'walls_{z}:thickness',all(abs(min(np.ptp(box(w),axis=1)[:2])-.2)<1e-6 for w in current))
        expected_volume=46.56-(.576 if z==0 else 0)
        check(f'walls_{z}:volume',abs(sum(volume(w) for w in current)-expected_volume)<1e-5)
        for i,(x,y) in enumerate(wall_centres):
            check(f'walls_{z}:segment_{i}',sum(covers(w,x,y) for w in current)==1)
    check('slab_roof_material',all(materials(s) and all(m in ('concrete','混凝土') for m in materials(s)) for s in plates))
    allowed_psets={'Pset_text2IFCIdentity','Pset_text2IFCAppearance','Pset_text2IFCBasicFilling'}
    check('no_unsolicited_properties',all(p.Name in allowed_psets for p in model.by_type('IfcPropertySet')))
    allowed_elements={'IfcWall','IfcWallStandardCase','IfcSlab','IfcRoof','IfcDoor','IfcWindow','IfcStair','IfcStairFlight','IfcOpeningElement'}
    check('no_extra_element_families',all(e.is_a() in allowed_elements for e in model.by_type('IfcElement')))
    check('no_extra_materials',all(not materials(e) for e in model.by_type('IfcElement') if not e.is_a('IfcWall') and e not in plates))
    for index,zrange in enumerate([[-.15,0],[3,3.15],[6.15,6.3],[9.3,9.45]]):
        matches=[p for p in plates if near(box(p)[2],zrange)]
        check(f'plate_{index}:unique_elevation',len(matches)==1)
        if len(matches)!=1:continue
        plate=matches[0]
        check(f'plate_{index}:bbox',near(box(plate),[[0,13.2],[0,16.8],zrange]))
        hole=expected['floor_openings'][index-1]['bbox_mm'] if index in (1,2) else None
        check(f'plate_{index}:native_volume',abs(volume(plate)-(161.28-(6.48 if hole else 0))*.15)<1e-5)
        for x in [1.,3.,6.,9.,12.]:
            for y in [1.,3.,6.,9.,13.,15.]:
                should=x<4.8 or y<4.8 or y>12
                if hole and hole[0][0]<x*1000<hole[0][1] and hole[1][0]<y*1000<hole[1][1]:should=False
                check(f'plate_{index}:coverage:{x}:{y}',covers(plate,x,y)==should)
        openings=[r.RelatedOpeningElement for r in plate.HasOpenings]
        check(f'plate_{index}:opening_count',len(openings)==int(hole is not None))
        if hole and len(openings)==1:check(f'plate_{index}:opening_bbox',near(box(openings[0]),np.array(hole)/1000))
    # Space geometry independently matched by position, not generated identities.
    for z in levels:
        for i,b in enumerate(expected['space_xy_mm']):
            target=[*[np.array(axis)/1000 for axis in b],[z,z+3]]
            check(f'space:{z}:{i}',sum(near(box(s),target) for s in model.by_type('IfcSpace'))==1)
    def host_side(host):
        b=box(host)
        for side,axis,interval in [('south',1,[0,.2]),('north',1,[16.6,16.8]),('west',0,[0,.2]),
                ('courtyard_south',1,[4.6,4.8]),('courtyard_north',1,[12,12.2])]:
            if near(b[axis],interval):return side
        if near(b[0],[4.6,4.8]):return 'partition_south' if b[1].mean()<8.4 else 'partition_north'
        return 'unrequested_host'
    windows=[];doors=[]
    for e in [*model.by_type('IfcWindow'),*model.by_type('IfcDoor')]:
        key=e.GlobalId;fills=e.FillsVoids
        check(key+':one_filling_relation',len(fills)==1)
        if len(fills)!=1:continue
        opening=fills[0].RelatingOpeningElement;voids=opening.VoidsElements
        check(key+':one_host_relation',len(voids)==1)
        if len(voids)!=1:continue
        host=voids[0].RelatingBuildingElement;b=box(e);ob=box(opening);hb=box(host)
        side=host_side(host);axis=1 if side in ['west','partition_south','partition_north'] else 0;depth=1-axis
        storey=element.get_container(host);z=storey.Elevation*.001 if storey else -999
        check(key+':width_height',near([b[axis,1]-b[axis,0],b[2,1]-b[2,0]],[e.OverallWidth*.001,e.OverallHeight*.001]))
        check(key+':opening_size',near([ob[axis,1]-ob[axis,0],ob[2,1]-ob[2,0]],[e.OverallWidth*.001,e.OverallHeight*.001]))
        check(key+':inside_host',b[depth,0]>=hb[depth,0]-1e-6 and b[depth,1]<=hb[depth,1]+1e-6)
        check(key+':void_through_host',ob[depth,0]<=hb[depth,0]+1e-6 and ob[depth,1]>=hb[depth,1]-1e-6)
        row=[z,side,round(b[axis].mean()*1000,5),e.OverallWidth,e.OverallHeight,round((b[2,0]-z)*1000,5)]
        ps=element.get_psets(e);st=styles(e)
        check(key+':theme',ps.get('Pset_text2IFCAppearance',{}).get('Profile')=='warm-residential')
        check(key+':parameter_provenance',bool(ps.get('Pset_text2IFCBasicFilling',{}).get('ParameterSourcesJson')))
        check(key+':component_colors',len({tuple(rgb) for rgb,_ in st})>=2)
        if e.is_a('IfcWindow'):
            windows.append(row)
            check(key+':glass_count',sum(t>0 for _,t in st)==(1 if side=='west' else 2))
        else:
            style=element.get_type(e);doors.append(row+[style.OperationType if style else None])
    check('all_windows_match',sorted(windows)==sorted([[z,*r] for z in levels for r in expected['window_rows_per_storey']]))
    check('all_doors_match',sorted(doors)==sorted([[z,*r] for z in levels for r in expected['door_rows_per_storey']]+[expected['entrance']]))
    types=model.by_type('IfcTypeObject');rels=model.by_type('IfcRelDefinesByType')
    check('minimum_door_styles_only',len(types)==7 and all(t.is_a('IfcDoorStyle') for t in types))
    check('type_family_and_uniqueness',len(rels)==7 and all(r.RelatingType.is_a('IfcDoorStyle') and len(r.RelatedObjects)==1 and r.RelatedObjects[0].is_a('IfcDoor') for r in rels) and len({r.RelatedObjects[0].id() for r in rels})==7)
    check('type_no_material_or_property',all(not t.HasAssociations and not t.HasPropertySets for t in types))
    for i,want in enumerate(expected['stairs']):
        flights=[f for f in model.by_type('IfcStairFlight') if near(box(f),np.array(want['bbox_mm'])/1000)]
        check(f'stair_{i}:bbox',len(flights)==1)
        if len(flights)!=1:continue
        flight=flights[0];v,_=mesh(flight)
        south=v[np.isclose(v[:,1],v[:,1].min()),2].max();north=v[np.isclose(v[:,1],v[:,1].max()),2].max()
        check(f'stair_{i}:rise_direction',(north>south)==(want['direction']=='north'))
        check(f'stair_{i}:step_attributes',flight.NumberOfRiser==18 and flight.NumberOfTreads==18 and flight.RiserHeight==175 and flight.TreadLength==300)
    return dict(status='passed' if all(checks.values()) else 'failed',checks=checks,
        failed=[k for k,v in checks.items() if not v],check_count=len(checks),
        ifc_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),request_sha256=expected['request_sha256'],
        scope='Frozen request fidelity, C-footprint native mesh, counts, relationships, templates, material and type. No full engineering/code certification.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('ifc',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    result=check_ifc(args.ifc)
    with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:result[k] for k in ['status','check_count','failed']},ensure_ascii=False))
    raise SystemExit(0 if result['status']=='passed' else 2)
