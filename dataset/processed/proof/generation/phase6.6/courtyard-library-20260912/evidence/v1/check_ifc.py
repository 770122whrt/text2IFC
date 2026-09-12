"""Independent frozen design checks. Never used as Provider context."""
import argparse
import hashlib
import json
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as util
import numpy as np

OUT=Path(__file__).resolve().parent

def check_ifc(path):
    model=ifcopenshell.open(str(path)); checks={}; cache={}
    settings=ifcopenshell.geom.settings(); settings.set(settings.USE_WORLD_COORDS,True)
    def check(key,value): checks[key]=bool(value)
    def near(a,b): return bool(np.allclose(a,b,atol=1e-5,rtol=0))
    def mesh(e):
        if e.id() not in cache:
            s=ifcopenshell.geom.create_shape(settings,e)
            cache[e.id()]=(np.array(s.geometry.verts).reshape(-1,3),np.array(s.geometry.faces).reshape(-1,3))
        return cache[e.id()]
    def box(e):
        v,_=mesh(e);return np.array([v.min(axis=0),v.max(axis=0)]).T
    def volume(e):
        v,f=mesh(e);t=v[f]
        return abs(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
    def covers(e,x,y):
        v,f=mesh(e);t=v[f];t=t[np.ptp(t[:,:,2],axis=1)<1e-7]
        for tri in t:
            a,b,c=tri[:,:2];m=np.array([b-a,c-a]).T
            if abs(np.linalg.det(m))<1e-10:continue
            u,w=np.linalg.solve(m,np.array([x,y])-a)
            if min(u,w)>=-1e-7 and u+w<=1+1e-7:return True
        return False
    counts={'IfcBuildingStorey':2,'IfcSpace':16,'IfcWall':20,'IfcSlab':3,
            'IfcWindow':40,'IfcDoor':15,'IfcRailing':4,'IfcStair':1,'IfcStairFlight':1,'IfcOpeningElement':58}
    check('IFC2X3',model.schema=='IFC2X3')
    check('millimetres',any(u.UnitType=='LENGTHUNIT' and u.Name=='METRE' and u.Prefix=='MILLI' for u in model.by_type('IfcSIUnit')))
    for cls,n in counts.items():check('count:'+cls,len(model.by_type(cls))==n)
    check('storey_elevations',near(sorted(s.Elevation for s in model.by_type('IfcBuildingStorey')),[0,3600]))
    for i,(base,holes,vol) in enumerate([(-.2,0,86.4),(3.4,2,75.0),(7,1,76.8)]):
        items=[e for e in model.by_type('IfcSlab') if abs(box(e)[2,0]-base)<1e-5]
        check(f'plate:{i}:unique',len(items)==1)
        if len(items)!=1:continue
        e=items[0]
        check(f'plate:{i}:bounds',near(box(e),[[0,24],[0,18],[base,base+.2]]))
        check(f'plate:{i}:opening_count',len(e.HasOpenings)==holes)
        check(f'plate:{i}:volume',abs(volume(e)-vol)<1e-4)
        for x,y in [(8.1,6.1),(12,9),(15.9,11.9)]:check(f'plate:{i}:courtyard:{x}:{y}',covers(e,x,y)==(i==0))
        check(f'plate:{i}:gallery_remains',all(covers(e,x,y) for x,y in [(7,9),(17,9),(12,5),(12,13)]))
        check(f'plate:{i}:stair_void',covers(e,1.75,8)==(i!=1))
        material=util.get_material(e)
        layers=material.ForLayerSet.MaterialLayers if material and material.is_a('IfcMaterialLayerSetUsage') else []
        check(f'plate:{i}:layers',len(layers)==2 and near([x.LayerThickness for x in layers],[180,20]) and [x.Material.Name for x in layers]==['混凝土','砂浆'])
        if i==2:check('roof_is_roof_slab',e.PredefinedType=='ROOF')
    rail_boxes=[[[7.98,16.02],[5.98,6],[3.6,4.7]],[[7.98,16.02],[12,12.02],[3.6,4.7]],
                [[7.98,8],[6,12],[3.6,4.7]],[[16,16.02],[6,12],[3.6,4.7]]]
    for i,bounds in enumerate(rail_boxes):
        items=[e for e in model.by_type('IfcRailing') if near(box(e),bounds)]
        check(f'railing:{i}:position',len(items)==1)
        if not items:continue
        e=items[0];material=util.get_material(e)
        check(f'railing:{i}:glass',material is not None and material.is_a('IfcMaterial') and material.Name=='玻璃')
        styles=[s for r in e.Representation.Representations for item in r.Items for a in item.StyledByItem for ass in a.Styles for st in ass.Styles for s in st.Styles if s.is_a('IfcSurfaceStyleRendering')]
        check(f'railing:{i}:transparency',bool(styles) and all(abs((s.Transparency or 0)-.75)<1e-6 for s in styles))
        check(f'railing:{i}:second_floor',util.get_container(e).Elevation==3600)
    flight=model.by_type('IfcStairFlight')
    if len(flight)==1:
        e=flight[0];check('stair:bounds',near(box(e),[[1,2.5],[5,11],[0,3.6]]))
        check('stair:risers',e.NumberOfRiser==20)
        check('stair:rise',e.RiserHeight==180)
        check('stair:tread',e.TreadLength==300)
    # Match physical opening centres and nominal sizes, independent of Brief IDs.
    slots=[]
    for z in [0,3.6]:
        for y in [.12,17.88]:
            for x in [3,8,16,21]:slots.append(('IfcWindow',x,y,z+.6,2000,2400))
        for y in [6.5,11.5]:slots.append(('IfcWindow',23.88,y,z+.6,2000,2400))
        for y in [2,16]:slots.append(('IfcWindow',.12,y,z+1.2,1000,1800))
        for y in [3.86,14.14]:
            for x in [10,14]:slots.append(('IfcWindow',x,y,z+.9,1600,2100))
        for x in [5.86,18.14]:
            for y in [6.5,11.5]:slots.append(('IfcWindow',x,y,z+.9,1600,2100))
        for y in [3.86,14.14]:
            for x in [7,17]:slots.append(('IfcDoor',x,y,z,1000,2400))
        for x in [5.86,18.14]:slots.append(('IfcDoor',x,9,z,1000,2400))
    slots += [('IfcDoor',12,.12,0,1400,2600),('IfcDoor',2.62,4.5,0,900,2100),('IfcDoor',2.62,11.8,3.6,900,2100)]
    for i,(cls,x,y,z,w,h) in enumerate(slots):
        found=[]
        for e in model.by_type(cls):
            if len(e.FillsVoids)!=1:continue
            opening=e.FillsVoids[0].RelatingOpeningElement;b=box(opening)
            if near([b[0].mean(),b[1].mean(),b[2,0]],[x,y,z]):found.append((e,opening))
        check(f'filling:{i}:unique_position',len(found)==1)
        if len(found)!=1:continue
        e,opening=found[0]
        check(f'filling:{i}:dimensions',e.OverallWidth==w and e.OverallHeight==h)
        check(f'filling:{i}:wall_host',len(opening.VoidsElements)==1 and opening.VoidsElements[0].RelatingBuildingElement.is_a('IfcWall'))
        check(f'filling:{i}:effective_type',util.get_type(e) is not None)
        check(f'filling:{i}:storey',abs(util.get_container(e).Elevation/1000-(0 if z<3.6 else 3.6))<1e-6)
    for e in model.by_type('IfcWall'):
        material=util.get_material(e);layers=material.ForLayerSet.MaterialLayers if material and material.is_a('IfcMaterialLayerSetUsage') else []
        check(f'wall:{e.id()}:layers',len(layers)==3 and near([x.LayerThickness for x in layers],[20,200,20]) and [x.Material.Name for x in layers]==['砂浆','混凝土','砂浆'])
    for p in model.by_type('IfcPropertySingleValue'):
        check(f'property:{p.id()}:no_invented_performance',p.Name not in {'FireRating','ThermalTransmittance','CompressiveStrength'})
    return {'status':'passed' if all(checks.values()) else 'failed','ifc_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'request_sha256':hashlib.sha256((OUT/'request.txt').read_bytes()).hexdigest(),'checks':checks,
        'passed':sum(checks.values()),'total':len(checks),'failed':[k for k,v in checks.items() if not v],
        'limitations':['Not a structural/fire/code certification','Does not yet prove door swing clearance or complete opening-to-room accessibility','No provider self-report is used']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('ifc');args=parser.parse_args()
    r=check_ifc(Path(args.ifc));(OUT/'independent-ifc-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in r.items() if k!='checks'},ensure_ascii=False))
    raise SystemExit(0 if r['status']=='passed' else 1)
