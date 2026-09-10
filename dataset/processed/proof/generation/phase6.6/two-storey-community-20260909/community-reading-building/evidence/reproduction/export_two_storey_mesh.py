"""Actual IFC mesh payloads for static Proof images only; no review website."""
import hashlib,json,sys
from pathlib import Path
import ifcopenshell,ifcopenshell.geom
source=Path(sys.argv[1]); output=Path(sys.argv[2]); output.mkdir(exist_ok=False)
model=ifcopenshell.open(str(source)); settings=ifcopenshell.geom.settings(); settings.set(settings.USE_WORLD_COORDS,True)
products=[];failures=[]
for p in model.by_type('IfcElement'):
    if p.is_a('IfcOpeningElement') or not p.Representation:continue
    try:
        shape=ifcopenshell.geom.create_shape(settings,p); mesh=shape.geometry
        mats=[]
        for mat in mesh.materials:
            c=mat.diffuse; alpha=1-mat.transparency if mat.transparency==mat.transparency else 1
            mats.append([c.r(),c.g(),c.b(),alpha])
        products.append({'id':p.GlobalId,'name':p.Name,'kind':p.is_a(),'verts':list(mesh.verts),'faces':list(mesh.faces),'materials':mats,'material_ids':list(mesh.material_ids)})
    except Exception as e:failures.append({'guid':p.GlobalId,'error':type(e).__name__})
assert not failures,failures
def write(name,items,note):
    (output/name).write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'products':items,'mesh_failures':failures,'view_note':note},ensure_ascii=False),encoding='utf-8')
write('overall-mesh.json',products,'All represented physical products. No geometry or colors edited.')
def bounds(p,k):return [min(p['verts'][k::3]),max(p['verts'][k::3])]
cut=[]
for p in products:
    z=bounds(p,2);x=bounds(p,0);y=bounds(p,1)
    if z[0]>6.14:continue
    if p['kind'].startswith('IfcWall') and (y[1]<.01 or x[0]>8.99):continue
    cut.append(p)
write('cutaway-mesh.json',cut,'Roof, south and east walls hidden only in this view to reveal floors and stair. IFC unchanged.')
write('fillings-mesh.json',[p for p in products if p['kind'] in ['IfcWindow','IfcDoor']],'Door and window components isolated; actual IFC mesh and styles.')
print(json.dumps({'products':len(products),'mesh_failures':failures}))
