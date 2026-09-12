"""Offline authoring feasibility only; not a live Generation result."""
from pathlib import Path
import json
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

def main():
    import numpy as np
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element as util
    from text2ifc_compiler import compile_document
    from tests.compiler.test_v2_railing import _document
    d = _document()
    d['schema_version'] = 'bim-json/2.1'
    d['entities'] = d['entities'][:5]
    d['entities'][4]['attributes']['ObjectPlacement']['origin'][2] = 3600
    d['entities'][4]['attributes']['Elevation'] = 3600
    d['appearance'] = {'profile': 'warm-residential', 'seed': 'courtyard'}
    def box(identity, cls, bounds, **extra):
        x, y, z = bounds
        e = {'id': identity, 'ifc_class': cls,
             'attributes': {'Name': identity, 'ObjectPlacement': {
                 'relative_to': 'building-1', 'origin': [(x[0]+x[1])/2, (y[0]+y[1])/2, z[0]],
                 'axis': [0,0,1], 'ref_direction': [1,0,0]},
                 'Representation': {'kind': 'extruded_profile', 'profile': {'kind':'rectangle', 'x':x[1]-x[0], 'y':y[1]-y[0]}, 'depth':z[1]-z[0], 'direction':[0,0,1]}},
             'property_sets': {}, 'provenance': {'source':'offline-authoring-probe'}, **extra}
        d['entities'].append(e)
        return e
    for slab, z in [('upper', [3400,3600]), ('roof', [7000,7200])]:
        box(slab, 'IfcSlab', [[0,24000],[0,18000],z], materials=[{'kind':'material_layer_set_usage',
            'layer_set_name':'concrete-mortar', 'direction':'AXIS3', 'direction_sense':'POSITIVE', 'offset_from_reference_line':0,
            'layers':[{'name':'混凝土','thickness':180},{'name':'砂浆','thickness':20}]}])
        opening = slab+'-courtyard'
        box(opening, 'IfcOpeningElement', [[8000,16000],[6000,12000],z])
        d['relationships'].append({'id':'void-'+slab, 'ifc_class':'IfcRelVoidsElement', 'attributes':{
            'RelatingBuildingElement':slab, 'RelatedOpeningElement':opening}, 'provenance':{'source':'offline-authoring-probe'}})
    rails = {
        'south':[[7980,16020],[5980,6000],[3600,4700]],
        'north':[[7980,16020],[12000,12020],[3600,4700]],
        'west':[[7980,8000],[6000,12000],[3600,4700]],
        'east':[[16000,16020],[6000,12000],[3600,4700]],
    }
    for name,bounds in rails.items():
        box(name, 'IfcRailing', bounds, materials=[{'kind':'single_material','name':'玻璃'}],
            appearance={'color':[0.85,0.90,0.90], 'transparency':0.75})
    target=OUT/'offline-combination';target.mkdir(exist_ok=True)
    (target/'candidate.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    result=compile_document(d,target/'probe.ifc')
    assert result.success,result
    model=ifcopenshell.open(str(target/'probe.ifc'))
    settings=ifcopenshell.geom.settings(); settings.set(settings.USE_WORLD_COORDS,True)
    checks=[]
    for entity in model.by_type('IfcSlab'):
        shape=ifcopenshell.geom.create_shape(settings,entity)
        v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3)
        # Triangle areas on the horizontal top face prove the courtyard was cut
        # in the reopened physical mesh; a bbox alone cannot establish a void.
        top=v[:,2].max();t=v[f];mask=np.all(np.abs(t[:,:,2]-top)<1e-7,axis=1)
        area=float(np.linalg.norm(np.cross(t[mask,1]-t[mask,0],t[mask,2]-t[mask,0]),axis=1).sum()/2)
        assert abs(area-(24*18-8*6))<1e-6,area
        assert len(entity.HasOpenings)==1
        layers=util.get_material(entity).ForLayerSet.MaterialLayers
        assert [float(x.LayerThickness) for x in layers]==[180,20]
        checks.append({'class':'IfcSlab','top_area_m2':area,'opening':True,'layers_mm':[180,20]})
    for entity in model.by_type('IfcRailing'):
        shape=ifcopenshell.geom.create_shape(settings,entity)
        v=np.array(shape.geometry.verts).reshape(-1,3)
        assert np.allclose([v[:,2].min(),v[:,2].max()],[3.6,4.7])
        assert util.get_material(entity).Name=='玻璃'
        styles=[s for r in entity.Representation.Representations for i in r.Items for a in i.StyledByItem for assignment in a.Styles for s in assignment.Styles for s in s.Styles if s.is_a('IfcSurfaceStyleRendering')]
        assert styles and all(abs(s.Transparency-0.75)<1e-7 for s in styles)
    result={'status':'passed','evidence_class':'offline_hand_authored_compiler_probe','checks':checks,
        'railings':4,'railing_elevation_m':[3.6,4.7],'glass_transparency':0.75,
        'clear_gallery_width_m':2.0,'not_a_public_generation_or_provider_result':True}
    (target/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
