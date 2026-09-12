"""Freeze the delegated design before any candidate; no Provider or IFC input."""
from pathlib import Path
import hashlib,json
from shapely.geometry import Polygon,box
OUT=Path(__file__).resolve().parent
records=[]
COLORS={'concrete':'#D8D4CA','frame':'#333D40','structure':'#E2DFD7','wood':'#A87950'}

def add(label,cls,bounds,**extra):
    records.append({'label':label,'ifc_class':cls,'bbox_m':{k:list(v) for k,v in zip('xyz',bounds)},**extra})

walls={'西外墙':(0,.2,0,18),'东外墙':(23.8,24,0,18),'北外墙':(.2,23.8,17.8,18),
       '西前墙':(.2,4.8,0,.2),'东前墙':(19.2,23.8,0,.2),
       '西临庭墙':(4.8,5,0,12.9),'东临庭墙':(19,19.2,0,12.9),'北室南墙':(.2,23.8,12.9,13.1)}
wall_polys=[box(a,c,b,d) for a,b,c,d in walls.values()]
assert all(a.intersection(b).area<1e-9 for i,a in enumerate(wall_polys) for b in wall_polys[i+1:])
columns=[(x0,x1,y0,y1) for x0,x1 in [(7.1,7.4),(16.6,16.9)]
         for y0,y1 in [(0,.3),(3.4,3.7),(6.8,7.1),(10.3,10.6)]]+[(x0,x1,10.6,10.9) for x0,x1 in [(10.35,10.65),(13.35,13.65)]]
beams=[(7.1,7.4,0,10.9),(16.6,16.9,0,10.9),(7.4,16.6,10.6,10.9)]
u=[[0,0],[7.4,0],[7.4,10.6],[16.6,10.6],[16.6,0],[24,0],[24,18],[0,18],[0,0]]
upper=Polygon(u);landing=box(14.8,8.2,16.6,10.6)
assert upper.is_valid and upper.intersection(landing).area<1e-9
assert upper.boundary.intersection(landing.boundary).length>0
rooms={'西阅读室':(.2,4.8,.2,12.9),'东阅读室':(19.2,23.8,.2,12.9),'北阅览室':(.2,23.8,13.1,17.8),
       '西回廊':(5,7.4,0,10.6),'东回廊':(16.6,19,0,10.6),'北回廊':(5,19,10.6,12.9)}
windows=[]
for host in ('西外墙','东外墙'):
    windows += [(host,'y',v,2) for v in (3,7,11,16)]
windows += [('北外墙','x',v,2) for v in (4,9,15,20)]
for host in ('西临庭墙','东临庭墙'):
    windows += [(host,'y',v,2) for v in (2,5,11)]
windows += [('北室南墙','x',v,2) for v in (7,17)]
windows += [('西前墙','x',2.5,2.6),('东前墙','x',21.5,2.6)]
doors=[('西临庭墙','y',8,1.2,'door-left'),('东临庭墙','y',8,1.2,'door-right'),('北室南墙','x',12,1.4,'door-left')]
openings={}
for host,axis,center,width,*rest in [*windows,*doors]:
    x0,x1,y0,y1=walls[host];lo,hi=(x0,x1) if axis=='x' else (y0,y1)
    assert lo+.05<=center-width/2 and center+width/2<=hi-.05,(host,center,width)
    for a,b in openings.get(host,[]):assert min(b,center+width/2)-max(a,center-width/2)<=0
    openings.setdefault(host,[]).append((center-width/2,center+width/2))
for level,z in [('首层',0),('二层',3.6)]:
    for name,(x0,x1,y0,y1) in walls.items():add(level+name,'IfcWall',[(x0,x1),(y0,y1),(z,z+3.4)],material='混凝土',color=COLORS['concrete'])
    for i,(x0,x1,y0,y1) in enumerate(columns):
        assert upper.covers(box(x0,y0,x1,y1))
        add(f'{level}柱{i+1}','IfcColumn',[(x0,x1),(y0,y1),(z,z+3.1)],material='混凝土',color=COLORS['structure'])
    for i,(x0,x1,y0,y1) in enumerate(beams):add(f'{level}梁{i+1}','IfcBeam',[(x0,x1),(y0,y1),(z+3.1,z+3.4)],material='混凝土',color=COLORS['structure'])
    for name,(x0,x1,y0,y1) in rooms.items():add(level+name,'IfcSpace',[(x0,x1),(y0,y1),(z,z+3.4)],space_role='EXTERNAL' if '回廊' in name else 'INTERNAL')
    for cls,rows in [('IfcWindow',windows),('IfcDoor',doors)]:
        for i,(host,axis,center,width,*rest) in enumerate(rows):
            x0,x1,y0,y1=walls[host];cx,cy=((x0+x1)/2,center) if axis=='y' else (center,(y0+y1)/2)
            records.append({'label':f'{level}{host}{cls}{i+1}','ifc_class':cls,'host_label':level+host,
                'center_xy_m':[cx,cy],'length_axis':axis,'width_m':width,'height_m':2.4,
                'bottom_m':z+(.6 if cls=='IfcWindow' else 0),
                'template_id':rest[0] if rest else 'window-double-vertical',
                'material':'木材' if cls=='IfcDoor' else None,'frame_color':COLORS['frame'],
                'panel_color':COLORS['wood'] if cls=='IfcDoor' else None,'glazing_transparency':.65 if cls=='IfcWindow' else None})
add('首层地板','IfcSlab',[(0,24),(0,18),(-.2,0)],polygon_m=[[0,0],[24,0],[24,18],[0,18],[0,0]])
add('二层U形地板','IfcSlab',[(0,24),(0,18),(3.4,3.6)],polygon_m=u)
add('U形屋盖','IfcSlab',[(0,24),(0,18),(7,7.2)],polygon_m=u)
add('二层楼梯平台','IfcSlab',[(14.8,16.6),(8.2,10.6),(3.4,3.6)],polygon_m=[[14.8,8.2],[16.6,8.2],[16.6,10.6],[14.8,10.6],[14.8,8.2]])
add('外露梯段','IfcStairFlight',[(14.8,16.6),(2.2,8.2),(0,3.6)],risers=20,treads=20)
rails=[]
for x,spans in [(7.38,[(.3,3.4),(3.7,6.8),(7.1,10.3)]),(16.62,[(.3,3.4),(3.7,6.8),(7.1,8.2)])]:
    rails += [([x,a,3.6],[x,b,3.6]) for a,b in spans]
rails += [([a,10.62,3.6],[b,10.62,3.6]) for a,b in [(7.4,10.35),(10.65,13.35),(13.65,14.8)]]
rails += [([a,.02,3.6],[b,.02,3.6]) for a,b in [(5,7.1),(16.9,19)]]
rails += [([14.82,8.2,3.6],[14.82,10.6,3.6])]
rails += [([x,2.2,0],[x,8.2,3.6]) for x in [14.82,16.58]]
for i,(a,b) in enumerate(rails):
    records.append({'label':f'护栏{i+1}','ifc_class':'IfcRailing','start_m':a,'end_m':b,'height_m':1.1,
                    'depth_m':.04,'template_id':'metal-picket','material':'钢材','color':COLORS['frame']})
counts={cls:sum(r['ifc_class']==cls for r in records) for cls in sorted({r['ifc_class'] for r in records})}
assert counts['IfcWall']==16 and counts['IfcWindow']==44 and counts['IfcDoor']==6 and counts['IfcColumn']==20 and counts['IfcRailing']==14
request=(OUT/'request-draft.txt').read_bytes()
result={'schema_version':'text2ifc/delegated-courtyard-expectations/1.0','role':'local_independent_request_expectation_not_provider_input',
        'request_sha256':hashlib.sha256(request).hexdigest(),'source':'delegated design, frozen before Provider; no candidate-derived values',
        'counts':{**counts,'IfcStair':1,'IfcBuildingStorey':2,'IfcOpeningElement':50},'records':records,
        'geometry_tolerance_m':.005,'area_tolerance_m2':.001,
        'checks':{'wall_overlap':False,'all_fillings_inside_hosts':True,'door_window_overlap':False,
                  'upper_landing_overlap':False,'upper_landing_connected':True,'columns_supported_by_footprint':True},
        'limitations':['No structural, accessibility or fire-code certification.','Graspable profile and anchorage details need engineering review.']}
for name,payload in [('expected-independent.json',result)]:
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2);f.write('\n')
with (OUT/'request.txt').open('xb') as f:f.write(request)
print(json.dumps({'counts':result['counts'],'request_sha256':result['request_sha256'],'precheck':'passed'},ensure_ascii=False))
