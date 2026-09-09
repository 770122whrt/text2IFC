"""Independent native IFC checks, frozen before Provider output."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as element
import ifcopenshell.util.unit

base=Path(__file__).resolve().parent
source=Path(sys.argv[1]); output=Path(sys.argv[2])
expected=json.loads((base/'frozen-expectations.json').read_text(encoding='utf-8'))
assert hashlib.sha256((base/'request.txt').read_bytes()).hexdigest()==expected['request_sha256']
m=ifcopenshell.open(str(source))
settings=ifcopenshell.geom.settings(); settings.set(settings.USE_WORLD_COORDS,True)
def near(a,b,tol=1e-5):
    if isinstance(b,(tuple,list)):
        return len(a)==len(b) and all(near(x,y,tol) for x,y in zip(a,b))
    return abs(a-b)<tol
cache={}
def shape(e):
    if e.id() not in cache: cache[e.id()]=ifcopenshell.geom.create_shape(settings,e)
    return cache[e.id()]
def box(e):
    v=list(shape(e).geometry.verts)
    return [[min(v[k::3]),max(v[k::3])] for k in range(3)]
def materials(e): return [x.Name for x in element.get_materials(e)]
def styles(e):
    result=[]
    for rep in e.Representation.Representations:
        if rep.RepresentationIdentifier!='Body': continue
        for item in rep.Items:
            for si in item.StyledByItem:
                for assignment in si.Styles:
                    for style in assignment.Styles if assignment.is_a('IfcPresentationStyleAssignment') else [assignment]:
                        if style.is_a('IfcSurfaceStyle'):
                            for shading in style.Styles:
                                if shading.is_a('IfcSurfaceStyleShading'):
                                    result.append({'name':style.Name,'rgb':[shading.SurfaceColour.Red,shading.SurfaceColour.Green,shading.SurfaceColour.Blue],
                                                   'transparency':getattr(shading,'Transparency',0) or 0})
    return result
checks={}; details=[]
def check(key,value): checks[key]=bool(value)
metres=lambda box:[[v*.001 for v in pair] for pair in box]
levels=[v*.001 for v in expected['storey_elevations_mm']]
intervals={side:(axis,[v*.001 for v in pair]) for side,(axis,pair) in expected['wall_intervals_mm'].items()}
check('schema',m.schema=='IFC2X3')
check('units_mm',near(ifcopenshell.util.unit.calculate_unit_scale(m),.001))
counts={kind:len(m.by_type(kind)) for kind in expected['counts']}
physical_roofs=[r for r in m.by_type('IfcRoof') if r.Representation]
check('requested_counts',{**counts,'IfcSlab':counts['IfcSlab']+len(physical_roofs)}==expected['counts'])
check('storey_elevations',near(sorted(s.Elevation for s in m.by_type('IfcBuildingStorey')),expected['storey_elevations_mm']))
walls=m.by_type('IfcWall'); slabs=[*m.by_type('IfcSlab'),*physical_roofs]
check('wall_materials',all(len(materials(w))==1 and materials(w)[0].casefold() in {'砖','brick'} for w in walls))
check('slab_materials',all(len(materials(s))==1 and materials(s)[0].casefold() in {'混凝土','concrete'} for s in slabs))
allowed={'Pset_text2IFCIdentity','Pset_text2IFCBasicFilling','Pset_text2IFCAppearance'}
check('unrequested_properties_absent',all(p.Name in allowed for p in m.by_type('IfcPropertySet')))
check('unrequested_materials_absent',all(not materials(e) for e in m.by_type('IfcElement') if not e.is_a('IfcWall') and e not in slabs))
for z in levels:
    wall_boxes=[box(w) for w in walls if near(box(w)[2][0],z)]
    check(f'{z}:five_distinct_walls',len(wall_boxes)==5)
    check(f'{z}:wall_heights',all(near(b[2],[z,z+3]) for b in wall_boxes))
    for side,(axis,interval) in intervals.items():
        matches=[b for b in wall_boxes if near(b[axis],interval)]
        check(f'{z}:{side}:wall',len(matches)==1)
        if side=='partition': check(f'{z}:partition_full_length',len(matches)==1 and near(matches[0][1],[0,8.4]))
for i,bounds in enumerate(expected['spaces_mm']):
    check(f'space_{i}_bounds',sum(near(box(s),metres(bounds)) for s in m.by_type('IfcSpace'))==1)
floor_ranges=[[z-150,z] for z in expected['floor_tops_mm']]+[[expected['roof_bottom_mm'],expected['roof_bottom_mm']+150]]
for i,z in enumerate(floor_ranges):
    target=metres([expected['outer_bounds_mm']['x'],expected['outer_bounds_mm']['y'],z])
    check(f'slab_{i}_bounds',sum(near(box(s),target) for s in slabs)==1)
def same_rows(actual,expected):
    from math import isclose
    if len(actual)!=len(expected):return False
    return all(len(a)==len(e) and all(
        x==y if isinstance(y,str) else isclose(x,y,rel_tol=0,abs_tol=1e-9)
        for x,y in zip(a,e)) for a,e in zip(sorted(actual),sorted(expected)))
window_positions=[];door_positions=[];template_counts=Counter()
for e in [*m.by_type('IfcDoor'),*m.by_type('IfcWindow')]:
    b=box(e);ps=element.get_psets(e);template=ps.get('Pset_text2IFCBasicFilling',{}).get('TemplateId')
    template_counts[template]+=1
    label=e.GlobalId
    fills=e.FillsVoids
    check(label+':one_filling_relation',len(fills)==1)
    if len(fills)!=1: continue
    opening=fills[0].RelatingOpeningElement; voids=opening.VoidsElements
    check(label+':one_host_relation',len(voids)==1)
    if len(voids)!=1:continue
    host=voids[0].RelatingBuildingElement;hb=box(host);ob=box(opening)
    storey=element.get_container(e) or element.get_container(host)
    z=storey.Elevation*.001 if storey else -999
    c=[sum(v)/2 for v in b]
    sides=[side for side,(axis,interval) in intervals.items() if near(hb[axis],interval)]
    side=sides[0] if len(sides)==1 else 'unknown'
    axis=0 if side in ['south','north'] else 1;depth=1-axis
    check(label+':storey',z in levels)
    check(label+':host_storey',near(hb[2][0],z))
    nominal=[e.OverallWidth*.001,e.OverallHeight*.001]
    check(label+':nominal_mesh_size',near([b[axis][1]-b[axis][0],b[2][1]-b[2][0]],nominal))
    check(label+':opening_size',near([ob[axis][1]-ob[axis][0],ob[2][1]-ob[2][0]],nominal))
    check(label+':opening_through_wall',ob[depth][0]<=hb[depth][0]+1e-5 and ob[depth][1]>=hb[depth][1]-1e-5)
    check(label+':filling_inside_wall',b[depth][0]>=hb[depth][0]-1e-5 and b[depth][1]<=hb[depth][1]+1e-5)
    check(label+':theme',ps.get('Pset_text2IFCAppearance',{}).get('Profile')==expected['theme'])
    check(label+':provenance',bool(ps.get('Pset_text2IFCBasicFilling',{}).get('ParameterSourcesJson')))
    st=styles(e);glasses=[s for s in st if s['transparency']>0]
    check(label+':component_colors',len({tuple(s['rgb']) for s in st})>=2)
    position=(z,side,round(c[axis],5),round(e.OverallWidth,3),round(e.OverallHeight,3),round((b[2][0]-z)*1000,3))
    if e.is_a('IfcWindow'):
        window_positions.append(position)
        check(label+':glass_panels',len(glasses)==(1 if side=='east' else 2))
    else:
        door_positions.append(position);t=element.get_type(e)
        check(label+':door_swing',t is not None and t.OperationType==('SINGLE_SWING_LEFT' if side=='south' else 'SINGLE_SWING_RIGHT'))
    details.append({'guid':e.GlobalId,'storey_m':z,'side':side,'bbox_m':b,'template':template,'styles':st})
want_windows=[(z,w['side'],c*.001,w['width_mm'],w['height_mm'],w['sill_mm']) for z in levels for w in expected['windows_per_storey'] for c in w['centers_mm']]
check('all_window_locations_sizes_sills',same_rows(window_positions,want_windows))
check('all_door_locations_sizes_sills',same_rows(door_positions,[(z*.001,side,c*.001,w,h,sill) for z,side,c,w,h,sill in expected['doors']]))
check('template_counts',dict(template_counts)=={**expected['door_templates'],**expected['window_templates']})
flights=m.by_type('IfcStairFlight');check('stair_count',len(flights)==len(expected['stairs']))
for i,want in enumerate(expected['stairs']):
    target=metres(want['bbox_mm']);matches=[f for f in flights if near(box(f),target)]
    check(f'stair_{i}_bounds',len(matches)==1)
    if len(matches)!=1: continue
    f=matches[0];v=list(shape(f).geometry.verts);points=[v[j:j+3] for j in range(0,len(v),3)]
    zs={round(p[2],6) for p in points}
    check(f'stair_{i}_riser_levels',all(any(near(z,target[2][0]+n*.175) for z in zs) for n in range(19)))
    top_south=max(p[2] for p in points if near(p[1],target[1][0]))
    top_north=max(p[2] for p in points if near(p[1],target[1][1]))
    check(f'stair_{i}_direction',top_north>top_south if want['direction']=='+Y' else top_south>top_north)
    check(f'stair_{i}_riser_attribute',f.NumberOfRiser==want['risers'])
    check(f'stair_{i}_tread_attribute',f.NumberOfTreads==want['treads'])
def covers(a,b,c,p):
    cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
    sub=lambda u,v:[u[i]-v[i] for i in [0,1]]
    vals=[cross(sub(b,a),sub(p,a)),cross(sub(c,b),sub(p,b)),cross(sub(a,c),sub(p,c))]
    return abs(cross(sub(b,a),sub(c,a)))>1e-10 and (all(v>=-1e-9 for v in vals) or all(v<=1e-9 for v in vals))
for i,bounds in enumerate(expected['openings_mm']):
    target=metres(bounds); hosts=[s for s in slabs if near(box(s)[2],target[2])]
    check(f'opening_{i}_unique_host',len(hosts)==1)
    if len(hosts)!=1:continue
    host=hosts[0];opens=[r.RelatedOpeningElement for r in host.HasOpenings]
    check(f'opening_{i}_relation_and_bounds',len(opens)==1 and near(box(opens[0]),target))
    mesh=shape(host).geometry;v=list(mesh.verts);faces=list(mesh.faces)
    probes=[[x,y] for x in [target[0][0]+.1,sum(target[0])/2,target[0][1]-.1] for y in [target[1][0]+.1,sum(target[1])/2,target[1][1]-.1]]
    blocked=False
    for j in range(0,len(faces),3):
        vs=[v[faces[j+k]*3:faces[j+k]*3+3] for k in range(3)]
        if max(p[2] for p in vs)-min(p[2] for p in vs)<1e-7 and any(covers(*vs,p) for p in probes):blocked=True
    check(f'opening_{i}_actual_mesh_void',not blocked)
report={'status':'passed' if all(checks.values()) else 'failed','ifc_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'request_sha256':expected['request_sha256'],'counts':counts,'checks':checks,'failed':[k for k,v in checks.items() if not v],
 'fillings':details,'evaluator_version':2,'table_numeric_abs_tolerance':1e-9,'basis':expected['evaluator_policy'],'limits':expected['limits']}
with output.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':report['status'],'checks':len(checks),'failed':report['failed']}))
