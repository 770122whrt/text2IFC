"""Local independent reread of a new IFC against pre-Provider design facts."""
import argparse,json,math,hashlib
from pathlib import Path
import ifcopenshell,ifcopenshell.geom,ifcopenshell.util.element,ifcopenshell.util.unit
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from text2ifc_presentation import item_appearance_signatures
from text2ifc_presentation.part_readback import part_request_matches
from text2ifc_quality.generated_ifc import check_generated_ifc

OUT=Path(__file__).resolve().parent

def run(ifc_path):
    expected=json.loads((OUT/'expected-independent.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((OUT/'request.txt').read_bytes()).hexdigest()==expected['request_sha256']
    model=ifcopenshell.open(str(ifc_path));scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    checks=[];cache={};tol=expected['geometry_tolerance_m'];matched={}
    def check(code,okay,want=None,actual=None):checks.append({'check':code,'passed':bool(okay),'expected':want,'actual':actual})
    def mesh(product):
        if product.id() not in cache:
            shape=ifcopenshell.geom.create_shape(settings,product)
            vertices=np.asarray(shape.geometry.verts).reshape(-1,3)
            triangles=np.asarray(shape.geometry.faces).reshape(-1,3)
            cache[product.id()]=(vertices,triangles)
        return cache[product.id()]
    def bbox(product):
        v,_=mesh(product);return {k:[float(v[:,i].min()),float(v[:,i].max())] for i,k in enumerate('xyz')}
    def near(a,b):return np.allclose(a,b,rtol=0,atol=tol)
    def match_record(row,product):
        try:
            actual=bbox(product)
            if 'bbox_m' in row:return all(near(actual[k],row['bbox_m'][k]) for k in 'xyz')
            if row['ifc_class']=='IfcRailing':
                a,b=row['start_m'],row['end_m'];d=row['depth_m']/2;length=math.hypot(b[0]-a[0],b[1]-a[1])
                ox,oy=abs(b[1]-a[1])/length*d,abs(b[0]-a[0])/length*d
                want={'x':[min(a[0],b[0])-ox,max(a[0],b[0])+ox],
                      'y':[min(a[1],b[1])-oy,max(a[1],b[1])+oy],
                      'z':[min(a[2],b[2]),max(a[2],b[2])+row['height_m']]}
                return all(near(actual[k],want[k]) for k in 'xyz')
            center=[sum(actual[k])/2 for k in 'xy'];axis=row['length_axis']
            return near(center,row['center_xy_m']) and near(actual[axis][1]-actual[axis][0],row['width_m']) and near(actual['z'],[row['bottom_m'],row['bottom_m']+row['height_m']])
        except (RuntimeError,ValueError,AttributeError):return False
    check('IFC2X3',model.schema=='IFC2X3','IFC2X3',model.schema)
    for cls,count in expected['counts'].items():check('count:'+cls,len(model.by_type(cls))==count,count,len(model.by_type(cls)))
    allowed=set(expected['counts'])
    unexpected=[p.is_a() for p in model.by_type('IfcBuildingElement') if not any(p.is_a(cls) for cls in allowed)]
    check('no_extra_building_families',not unexpected,[],unexpected)
    aliases={'混凝土':{'混凝土','Concrete','concrete'},'木材':{'木材','Wood','wood'},'钢材':{'钢材','Steel','steel'}}
    rail_expect={}
    for row in expected['records']:
        label=row['label'];matches=[p for p in model.by_type(row['ifc_class']) if match_record(row,p)]
        check(label+':unique_geometry',len(matches)==1,1,len(matches))
        if len(matches)!=1:continue
        product=matches[0];matched[label]=product.GlobalId
        if row['ifc_class'] not in {'IfcStairFlight','IfcSpace'}:
            expected_storey=3.6 if (row.get('bbox_m',{}).get('z',[row.get('bottom_m',0)])[0]>=3.1 or row['ifc_class']=='IfcRailing' and row['start_m'][2]==3.6) else 0
            if row['ifc_class']=='IfcBeam':expected_storey=3.6 if row['bbox_m']['z'][0]>6 else 0
            container=ifcopenshell.util.element.get_container(product)
            actual=container.Elevation*scale if container and container.is_a('IfcBuildingStorey') else None
            check(label+':storey',actual is not None and near(actual,expected_storey),expected_storey,actual)
        if 'space_role' in row:check(label+':space_role',product.InteriorOrExteriorSpace==row['space_role'],row['space_role'],product.InteriorOrExteriorSpace)
        wanted_material=row.get('material')
        if row['ifc_class'] in {'IfcSlab','IfcStairFlight'}:wanted_material='混凝土'
        if wanted_material:
            material=ifcopenshell.util.element.get_material(product)
            actual=material.Name if material is not None and material.is_a('IfcMaterial') else None
            # Existing IFC2X3 WallStandardCase adapter may use one legal layer.
            if product.is_a('IfcWallStandardCase') and material is not None and material.is_a('IfcMaterialLayerSetUsage') and len(material.ForLayerSet.MaterialLayers)==1:
                actual=material.ForLayerSet.MaterialLayers[0].Material.Name
            check(label+':material',actual in aliases[wanted_material],sorted(aliases[wanted_material]),actual)
        color=row.get('color')
        if row['ifc_class'] in {'IfcSlab','IfcStairFlight'}:color='#E6E0D3'
        if color:
            rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
            items=[i for r in product.Representation.Representations if r.RepresentationIdentifier=='Body' for i in r.Items]
            styles=[item_appearance_signatures(i) for i in items]
            okay=bool(items) and all(len(s)==1 and all(abs(s[0][k]-v)<1e-5 for k,v in zip(('red','green','blue'),rgb)) for s in styles)
            check(label+':color',okay,color)
        if row['ifc_class'] in {'IfcDoor','IfcWindow'}:
            frame=row['frame_color'];request={'frame':{'color':[int(frame[i:i+2],16)/255 for i in (1,3,5)]}}
            if row['ifc_class']=='IfcDoor':
                panel=row['panel_color'];request['panel']={'color':[int(panel[i:i+2],16)/255 for i in (1,3,5)]}
            else:request['glazing']={'transparency':row['glazing_transparency']}
            check(label+':part_colors',part_request_matches(product,request),request)
            meta=ifcopenshell.util.element.get_psets(product,should_inherit=False).get('Pset_text2IFCBasicFilling',{})
            check(label+':template',meta.get('TemplateId')==row['template_id'],row['template_id'],meta.get('TemplateId'))
            openings=[r.RelatingOpeningElement for r in product.FillsVoids]
            hosts=[r.RelatingBuildingElement for opening in openings for r in opening.VoidsElements]
            check(label+':host',len(openings)==1 and len(hosts)==1 and hosts[0].GlobalId==matched.get(row['host_label']),row['host_label'],[p.GlobalId for p in hosts])
        if 'polygon_m' in row:
            vertices,faces=mesh(product);triangles=vertices[faces]
            flat=[Polygon(t[:,:2]) for t in triangles if np.ptp(t[:,2])<1e-7 and Polygon(t[:,:2]).area>1e-10]
            actual=unary_union(flat);want=Polygon(row['polygon_m'])
            difference=actual.symmetric_difference(want).area
            check(label+':actual_footprint',difference<=expected['area_tolerance_m2'],0,difference)
        if row['ifc_class']=='IfcStairFlight':
            check(label+':riser_count',product.NumberOfRiser==row['risers'],row['risers'],product.NumberOfRiser)
            check(label+':tread_count',product.NumberOfTreads==row['treads'],row['treads'],product.NumberOfTreads)
            vertices,_=mesh(product)
            levels={round(float(z),6) for z in vertices[:,2]}
            check(label+':real_step_levels',len(levels)>=21,21,len(levels))
        if row['ifc_class']=='IfcRailing':
            identity=ifcopenshell.util.element.get_psets(product).get('Pset_text2IFCIdentity',{}).get('BimJsonId')
            geometry={'kind':'basic_railing_segment','start_mm':[v*1000 for v in row['start_m']],
                'end_mm':[v*1000 for v in row['end_m']],'height_mm':row['height_m']*1000,'thickness_mm':row['depth_m']*1000,
                'template':{'template_id':'metal-picket','template_version':'text2ifc/basic-railing/1.0'}}
            rail_expect[identity]={'ifc_class':'IfcRailing','geometry_kind':'basic_railing_segment','railing_geometry':geometry}
    if rail_expect:
        checked=check_generated_ifc(ifc_path,{'case_id':'independent-courtyard','products':rail_expect,'tolerance':tol})
        check('railing_actual_baselines_and_solids',checked.success,[],checked.issues)
    return {'role':'independent reopened IFC vs pre-Provider frozen design','ifc_sha256':hashlib.sha256(Path(ifc_path).read_bytes()).hexdigest(),
            'expected_sha256':hashlib.sha256((OUT/'expected-independent.json').read_bytes()).hexdigest(),
            'passed':all(c['passed'] for c in checks),'checks':checks,'matches':matched,
            'limitations':['Not a building-code or structural certification.','Visual quality still needs actual IFC views and human review.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('ifc');p.add_argument('output');args=p.parse_args()
    result=run(args.ifc)
    with Path(args.output).open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'failures':[c for c in result['checks'] if not c['passed']]},ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
