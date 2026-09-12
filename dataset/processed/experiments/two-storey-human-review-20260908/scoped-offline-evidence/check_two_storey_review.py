"""Independent reopened IFC checks against the pre-Provider two-storey request."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as element
import ifcopenshell.util.unit

root=Path(__file__).resolve().parents[1]
base=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
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
def check(key, value): checks[key]=bool(value)
check('schema',m.schema=='IFC2X3')
check('units_mm',near(ifcopenshell.util.unit.calculate_unit_scale(m),.001))
counts={k:len(m.by_type(k)) for k in expected['counts']}
physical_roofs=[r for r in m.by_type('IfcRoof') if r.Representation]
normalized_counts={**counts,'IfcSlab':counts['IfcSlab']+len(physical_roofs)}
check('requested_counts',normalized_counts==expected['counts'])
check('storey_elevations',near(sorted(s.Elevation for s in m.by_type('IfcBuildingStorey')),[0,3150]))
walls=m.by_type('IfcWall'); slabs=[*m.by_type('IfcSlab'),*physical_roofs]
check('wall_materials',all(len(materials(w))==1 and materials(w)[0].casefold() in {'砖','brick'} for w in walls))
check('slab_materials',all(len(materials(s))==1 and materials(s)[0].casefold() in {'混凝土','concrete'} for s in slabs))
allowed={'Pset_text2IFCIdentity','Pset_text2IFCBasicFilling','Pset_text2IFCAppearance'}
check('unrequested_properties_absent',all(p.Name in allowed for p in m.by_type('IfcPropertySet')))
check('unrequested_materials_absent',all(not materials(e) for e in m.by_type('IfcElement') if not e.is_a('IfcWall') and e not in slabs))
for z in [0,3.15]:
    wall_boxes=[box(w) for w in walls if near(box(w)[2][0],z)]
    check(f'{z}_five_distinct_walls',len(wall_boxes)==5)
    check(f'{z}_wall_heights',all(near(b[2],[z,z+3]) for b in wall_boxes))
    for side,axis,interval in [('south',1,[-.2,0]),('north',1,[8,8.2]),('west',0,[-.2,0]),('east',0,[9,9.2]),('partition',0,[6.8,7])]:
        matches=[b for b in wall_boxes if near(b[axis],interval)]
        check(f'{z}_{side}_wall',len(matches)==1)
    for name,target in [('hall',[[0,6.8],[0,8],[z,z+3]]),
                        ('stair_space',[[7,9],[0,8] if z==0 else [6.6,8],[z,z+3]])]:
        check(f'{z}_{name}_space',sum(near(box(s),target) for s in m.by_type('IfcSpace'))==1)
for name,z in [('ground',[-.15,0]),('upper',[3,3.15]),('roof',[6.15,6.3])]:
    check(f'{name}_slab_bounds',sum(near(box(s),[[-.2,9.2],[-.2,8.2],z]) for s in slabs)==1)

window_positions=[]; door_positions=[]; template_counts=Counter()
for e in [*m.by_type('IfcDoor'),*m.by_type('IfcWindow')]:
    b=box(e); ps=element.get_psets(e); template=ps.get('Pset_text2IFCBasicFilling',{}).get('TemplateId')
    template_counts[template]+=1
    opening=e.FillsVoids[0].RelatingOpeningElement
    host=opening.VoidsElements[0].RelatingBuildingElement
    hb=box(host); ob=box(opening)
    storey=element.get_container(e) or element.get_container(host)
    z=storey.Elevation*.001 if storey else -999
    c=[sum(v)/2 for v in b]
    side='partition' if near(hb[0],[6.8,7]) else 'west' if near(hb[0],[-.2,0]) else 'east' if near(hb[0],[9,9.2]) else 'south' if near(hb[1],[-.2,0]) else 'north' if near(hb[1],[8,8.2]) else 'unknown'
    axis=0 if side in ['south','north'] else 1; depth=1-axis
    label=f'{e.is_a()}:{z}:{side}:{round(c[axis],3)}'
    check(label+':storey',z in [0,3.15])
    check(label+':host_storey',near(hb[2][0],z))
    check(label+':nominal_mesh_size',near([b[axis][1]-b[axis][0],b[2][1]-b[2][0]],[e.OverallWidth*.001,e.OverallHeight*.001]))
    check(label+':opening_size',near([ob[axis][1]-ob[axis][0],ob[2][1]-ob[2][0]],[e.OverallWidth*.001,e.OverallHeight*.001]))
    check(label+':opening_through_wall',ob[depth][0]<=hb[depth][0]+1e-5 and ob[depth][1]>=hb[depth][1]-1e-5)
    check(label+':filling_inside_wall',b[depth][0]>=hb[depth][0]-1e-5 and b[depth][1]<=hb[depth][1]+1e-5)
    check(label+':theme',ps.get('Pset_text2IFCAppearance',{}).get('Profile')=='warm-residential')
    check(label+':provenance',bool(ps.get('Pset_text2IFCBasicFilling',{}).get('ParameterSourcesJson')))
    st=styles(e); glasses=[s for s in st if s['transparency']>0]
    check(label+':component_colors',len({tuple(s['rgb']) for s in st})>=2)
    if e.is_a('IfcWindow'):
        window_positions.append((z,side,round(c[axis],5),round(e.OverallWidth,3),round(e.OverallHeight,3),round((b[2][0]-z)*1000,3)))
        check(label+':glass_panels',len(glasses)==(1 if side=='east' else 2))
    else:
        door_positions.append((z,side,round(c[axis],5),round(e.OverallWidth,3),round(e.OverallHeight,3),round((b[2][0]-z)*1000,3)))
        t=element.get_type(e)
        check(label+':door_swing',t is not None and t.OperationType==('SINGLE_SWING_LEFT' if side=='south' else 'SINGLE_SWING_RIGHT'))
    details.append({'guid':e.GlobalId,'label':label,'bbox_m':b,'template':template,'styles':st})
want_windows=[(z,w['side'],c*.001,w['width_mm'],w['height_mm'],w['sill_mm']) for z in [0,3.15] for w in expected['windows_per_storey'] for c in w['centers_mm']]
check('all_window_locations_sizes_and_sills',sorted(window_positions)==sorted(want_windows))
check('all_door_locations_sizes_and_sills',sorted(door_positions)==sorted([(0,'south',3.4,1200,2400,0),(0,'partition',.6,900,2100,0),(3.15,'partition',7.3,900,2100,0)]))
check('template_counts',dict(template_counts)=={**expected['door_templates'],**expected['window_templates']})

flights=m.by_type('IfcStairFlight')
check('stair_flight_exists',len(flights)==1)
if flights:
    f=flights[0]; fb=box(f)
    check('stair_bounds',near(fb,[[7.4,8.6],[1.2,6.6],[0,3.15]]))
    verts=list(shape(f).geometry.verts)
    levels=sorted({round(z,6) for z in verts[2::3]})
    check('eighteen_riser_levels',all(any(near(z,n*.175) for z in levels) for n in range(19)))
upper=next((s for s in slabs if near(box(s)[2],[3,3.15])),None)
if upper:
    openings=[r.RelatedOpeningElement for r in upper.HasOpenings]
    check('upper_slab_opening_relation',any(near(box(o),[[7.2,8.8],[1.2,6.6],[3,3.15]]) for o in openings))
    mesh=shape(upper).geometry; vertices=list(mesh.verts); faces=list(mesh.faces)
    def covers(a,b,c,p):
        cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
        sub=lambda u,v:[u[i]-v[i] for i in [0,1]]
        vals=[cross(sub(b,a),sub(p,a)),cross(sub(c,b),sub(p,b)),cross(sub(a,c),sub(p,c))]
        return abs(cross(sub(b,a),sub(c,a)))>1e-10 and (all(v>=-1e-9 for v in vals) or all(v<=1e-9 for v in vals))
    blocked=False
    for i in range(0,len(faces),3):
        vs=[vertices[faces[i+j]*3:faces[i+j]*3+3] for j in range(3)]
        if max(v[2] for v in vs)-min(v[2] for v in vs)<1e-7 and covers(*vs,[8,3.9]): blocked=True
    check('upper_opening_is_mesh_void',not blocked)

report={'status':'passed' if all(checks.values()) else 'failed','ifc_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'request_sha256':expected['request_sha256'],'counts':counts,'physical_roof_count':len(physical_roofs),'checks':checks,
        'failed':[k for k,v in checks.items() if not v],'fillings':details,
        'basis':'Independent IFC graph, typed materials, actual world meshes and StyledItems against pre-Provider frozen request. Agent represented labels unused.',
        'interpretation':'The request does not prescribe IFC roof class or literal English/Chinese material names. Legal represented IfcRoof counts as the requested physical roof slab; only brick/砖 and concrete/混凝土 name equivalence is accepted. The original request and frozen geometry are unchanged. This evaluator policy was refined after Brief inspection and before reading any candidate, and is not a blind fixed-evaluator score.',
        'limits':'Development viability, not construction certification or blind capability evaluation.'}
with output.open('x',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':report['status'],'checks':len(checks),'failed':report['failed']}))
