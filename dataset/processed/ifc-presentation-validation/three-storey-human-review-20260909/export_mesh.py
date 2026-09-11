"""Read-only IFC views; view hiding does not modify the source model."""
import hashlib,json,sys
from pathlib import Path
import ifcopenshell,ifcopenshell.geom,ifcopenshell.util.element

source=Path(sys.argv[1]);output=Path(sys.argv[2]);output.mkdir(exist_ok=False)
expected=json.loads((Path(__file__).parent/'frozen-expectations.json').read_text(encoding='utf-8'))
model=ifcopenshell.open(str(source));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
products=[];failures=[]
for product in model.by_type('IfcElement'):
    if product.is_a('IfcOpeningElement') or not product.Representation:continue
    try:
        shape=ifcopenshell.geom.create_shape(settings,product);mesh=shape.geometry
        materials=[]
        for mat in mesh.materials:
            c=mat.diffuse;opacity=1-mat.transparency if mat.transparency==mat.transparency else 1
            materials.append([c.r(),c.g(),c.b(),opacity])
        products.append({'id':product.GlobalId,'name':product.Name,'kind':product.is_a(),
            'verts':list(mesh.verts),'faces':list(mesh.faces),'materials':materials,'material_ids':list(mesh.material_ids),
            'template':ifcopenshell.util.element.get_psets(product).get('Pset_text2IFCBasicFilling',{}).get('TemplateId')})
    except Exception as e:failures.append({'guid':product.GlobalId,'error':type(e).__name__})
assert not failures,failures
def bounds(p,axis):return [min(p['verts'][axis::3]),max(p['verts'][axis::3])]
def write(name,items,note):
    (output/name).write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'products':items,'mesh_failures':failures,'view_note':note},ensure_ascii=False),encoding='utf-8')
write('overall-mesh.json',products,'All represented physical IFC products; exact IFC meshes and colors.')
cut=[]
east=expected['wall_intervals_mm']['east'][1][0]*.001
for p in products:
    if bounds(p,2)[0]>=expected['roof_bottom_mm']*.001-1e-5:continue
    if p['kind'].startswith('IfcWall') and (bounds(p,1)[1]<.01 or bounds(p,0)[0]>=east-.001):continue
    cut.append(p)
write('cutaway-mesh.json',cut,'Roof, south and east walls hidden for inspection; IFC unchanged.')
for name,template in [('window-double','window-double-vertical'),('door','door-left')]:
    selected=[p for p in products if p['template']==template]
    assert selected,template
    write(name+'-mesh.json',selected[:1],'One actual IFC filling isolated; exact mesh and component colors.')
print(json.dumps({'products':len(products),'mesh_failures':failures}))
