"""Hand-authored fixture for deterministic admission; NEVER a live result."""
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(OUT)]

def build():
    expected=json.loads((OUT/'frozen-expectations.json').read_text(encoding='utf-8'))
    previous=ROOT/'dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910/evidence/frozen/A-revise/runtime/runs/6b4c8ce023e02a07'
    old=json.loads((previous/'generator/candidate.json').read_text(encoding='utf-8'))
    oldbrief=json.loads((previous/'design-brief/design-brief.json').read_text(encoding='utf-8'))
    entities=[];rels=[];semantics=[]
    def placement(parent,origin,ref=None):return dict(relative_to=parent,origin=origin,axis=[0,0,1],ref_direction=ref or [1,0,0])
    def add(identity,kind,attributes,material=None,template=None):
        item=dict(id=identity,ifc_class=kind,attributes=attributes,property_sets={},provenance={'source':'test'})
        if material:item['materials']=[dict(kind='single_material',name=material)];semantics.append(dict(entity_id=identity,material=item['materials'][0],scope='direct',source='user'))
        if template:semantics.append(dict(entity_id=identity,template=dict(template_id=template,template_version='text2ifc/basic-filling/1.0'),scope='direct',source='user'))
        entities.append(item);return item
    def relation(identity,kind,attrs):rels.append(dict(id=identity,ifc_class=kind,attributes=attrs,provenance={'source':'test'}))
    def rect(width,depth,height):return dict(kind='extruded_profile',profile=dict(kind='rectangle',x=width,y=depth),depth=height,direction=[0,0,1])
    def box(identity,kind,xy,parent,z,height,material=None):
        x,y=xy
        return add(identity,kind,dict(Name=identity,ObjectPlacement=placement(parent,[(x[0]+x[1])/2,(y[0]+y[1])/2,z]),Representation=rect(x[1]-x[0],y[1]-y[0],height)),material)
    for kind in ('IfcProject','IfcSite','IfcBuilding'):
        e=copy.deepcopy(next(e for e in old['entities'] if e['ifc_class']==kind));e['provenance']={'source':'test'};entities.append(e)
    project,site,building=[e['id'] for e in entities]
    relation('project-site','IfcRelAggregates',dict(RelatingObject=project,RelatedObjects=[site]))
    relation('site-building','IfcRelAggregates',dict(RelatingObject=site,RelatedObjects=[building]))
    walls={
        'south':[[0,13200],[0,200]],'north':[[0,13200],[16600,16800]],'west':[[0,200],[200,16600]],
        'east_south':[[13000,13200],[200,4800]],'east_north':[[13000,13200],[12000,16600]],
        'courtyard_south':[[4800,13000],[4600,4800]],'courtyard_north':[[4800,13000],[12000,12200]],
        'spine':[[4600,4800],[4800,12000]],'partition_south':[[4600,4800],[200,4800]],'partition_north':[[4600,4800],[12000,16600]]}
    facts=dict(appearance={'profile':'warm-residential'},building=dict(id=building,storey_count=3,outline={'x_min':0,'x_max':13200,'y_min':0,'y_max':16800}),storeys=[],floor_slabs=[],stairs=[])
    points=expected['footprint_mm'];polygon=dict(kind='polygon',points=[*points,points[0]])
    for i,elevation in enumerate([0,3150,6300],1):
        s=f'storey-{i}';contained=[]
        add(s,'IfcBuildingStorey',dict(Name=s,Elevation=elevation,ObjectPlacement=placement(building,[0,0,elevation])))
        storey=dict(id=s,elevation_mm=elevation,net_height_mm=3000,spaces=[],walls={'exterior':[],'interior':[]},windows=[],doors=[])
        for j,xy in enumerate(expected['space_xy_mm']):
            sid=f'space-{i}-{j}';box(sid,'IfcSpace',xy,s,0,3000)['attributes']['InteriorOrExteriorSpace']='INTERNAL'
            storey['spaces'].append(dict(id=sid,bounds=dict(zip(['x','y'],xy))));
        relation('spaces-'+s,'IfcRelAggregates',dict(RelatingObject=s,RelatedObjects=[r['id'] for r in storey['spaces']]))
        for side,xy in walls.items():
            identity=f'wall-{i}-{side}';wall=box(identity,'IfcWall',xy,s,0,3000,'砖');contained.append(identity)
            if xy[0][1]-xy[0][0]==200:
                wall['attributes']['ObjectPlacement']['ref_direction']=[0,1,0]
                wall['attributes']['Representation']['profile'].update(x=xy[1][1]-xy[1][0],y=200)
            category='interior' if side.startswith('partition') else 'exterior'
            storey['walls'][category].append(dict(id=identity,bounds=dict(zip(['x','y'],xy)),height_mm=3000,thickness_mm=200))
        slab=f'slab-{i}';add(slab,'IfcSlab',dict(Name=slab,PredefinedType='FLOOR',ObjectPlacement=placement(s,[0,0,-150]),Representation=dict(kind='extruded_profile',profile=polygon,depth=150,direction=[0,0,1])),'混凝土');contained.append(slab)
        sf=dict(id=slab,storey=s,bounds={'x':[0,13200],'y':[0,16800]},thickness_mm=150,top_elevation_mm=elevation)
        if i>1:
            opening=f'floor-opening-{i}';b=expected['floor_openings'][i-2]['bbox_mm']
            box(opening,'IfcOpeningElement',b[:2],slab,0,150)
            relation('void-'+opening,'IfcRelVoidsElement',dict(RelatingBuildingElement=slab,RelatedOpeningElement=opening))
            sf['opening']=dict(id=opening,bounds={'x':b[0],'y':b[1]},real_through_opening=True)
        facts['floor_slabs'].append(sf)
        def filling(row,kind,j):
            side,centre,width,height,sill=row[:5];host=f'wall-{i}-{side}';xy=walls[side]
            vertical=side in ['west','partition_south','partition_north']
            x=(xy[0][0]+xy[0][1])/2 if vertical else centre
            y=centre if vertical else (xy[1][0]+xy[1][1])/2
            identity=f'{kind.lower()}-{i}-{j}';opening='opening-'+identity
            local_x=(y-(xy[1][0]+xy[1][1])/2) if vertical else (x-(xy[0][0]+xy[0][1])/2)
            add(opening,'IfcOpeningElement',dict(Name=opening,ObjectPlacement=placement(host,[local_x,0,sill]),Representation=rect(width,200,height)))
            template=('window-single' if side=='west' else 'window-double-vertical') if kind=='IfcWindow' else ('door-left' if row[-1]=='SINGLE_SWING_LEFT' else 'door-right')
            add(identity,kind,dict(Name=identity,OverallWidth=width,OverallHeight=height,ObjectPlacement=placement(opening,[0,0,0]),Representation=dict(kind='basic_filling',template_id=template,template_version='text2ifc/basic-filling/1.0',width=width,height=height,depth=200)),template=template)
            relation('void-'+identity,'IfcRelVoidsElement',dict(RelatingBuildingElement=host,RelatedOpeningElement=opening))
            relation('fill-'+identity,'IfcRelFillsElement',dict(RelatingOpeningElement=opening,RelatedBuildingElement=identity));contained.append(identity)
            storey['windows' if kind=='IfcWindow' else 'doors'].append(dict(id=identity,host_wall=host,center_global_mm=[x,y],width_mm=width,height_mm=height,sill_height_mm=sill,template_id=template))
        for j,row in enumerate(expected['window_rows_per_storey']):filling(row,'IfcWindow',j)
        for j,row in enumerate(expected['door_rows_per_storey']):filling(row,'IfcDoor',j)
        if i==1:filling(expected['entrance'][1:],'IfcDoor','entry')
        if i<3:
            stair=copy.deepcopy(next(e for e in old['entities'] if e['id']==f'stair-{i}'))
            stair['attributes']['ObjectPlacement']['origin']=[400,5400,0] if i==1 else [2800,10800,0]
            stair['provenance']={'source':'test'};entities.append(stair);contained.append(stair['id'])
            flight=copy.deepcopy(next(e for e in old['entities'] if e['id']==f'stair-flight-{i}'));flight['provenance']={'source':'test'};entities.append(flight)
            relation(f'aggregate-stair-{i}','IfcRelAggregates',dict(RelatingObject=stair['id'],RelatedObjects=[flight['id']]))
            b=expected['stairs'][i-1]['bbox_mm'];facts['stairs'].append(dict(id=stair['id'],bounds={'x':b[0],'y':b[1]},from_storey=s,to_storey=f'storey-{i+1}',start_elevation_mm=elevation,end_elevation_mm=elevation+3150,width_mm=1200,number_of_risers=18,number_of_treads=18,riser_height_mm=175,tread_depth_mm=300))
        if i==3:
            add('roof-slab','IfcRoof',dict(Name='roof-slab',ShapeType='FLAT_ROOF',ObjectPlacement=placement(s,[0,0,3000]),Representation=dict(kind='extruded_profile',profile=polygon,depth=150,direction=[0,0,1])),'混凝土');contained.append('roof-slab')
        # Compiler derives supported containment from placement ownership.
        facts['storeys'].append(storey)
    relation('building-storeys','IfcRelAggregates',dict(RelatingObject=building,RelatedObjects=['storey-1','storey-2','storey-3']))
    facts['roof_slab']=dict(id='roof-slab',bounds={'x':[0,13200],'y':[0,16800]},bottom_elevation_mm=9300,thickness_mm=150)
    facts['semantic_requirements']=semantics
    facts['semantic_review']={k:dict(status='specified' if k in ('material','template') else 'not_specified',source_turns=['turn-user-001']) for k in ('material','template','property','type','appearance')}
    candidate=dict(schema_version='bim-json/2.1',ifc_schema='IFC2X3',units={'length':'MILLIMETRE'},appearance={'profile':'warm-residential'},entities=entities,relationships=rels,provenance={'source':'test'})
    brief={**oldbrief,'original_request':(OUT/'request.txt').read_text(encoding='utf-8'),'known_facts':facts,'fact_sources':[],'missing_facts':[],'ambiguities':[],'unsupported_requests':[],'user_corrections':[],'clarification_questions':[],'status':'ready'}
    brief['provenance']=copy.deepcopy(oldbrief['provenance']);brief['provenance']['source_turns']=['turn-user-001']
    return brief,candidate

if __name__=='__main__':
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from check_ifc import check_ifc
    brief,candidate=build()
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,'deterministic_gate_status':'passed','findings':[],'evidence_paths':['gate-summary.json']}
    provider=SequenceProvider([brief,candidate,audit])
    runtime=OUT/(sys.argv[1] if len(sys.argv)>1 else 'offline-public');assert not runtime.exists();runtime.mkdir()
    with SessionStore.open(runtime/'sessions.sqlite',artifact_root=runtime) as store:
        session=store.create_session(original_input=brief['original_request'])
        # Match the fixture's explicit turn identity to the public conversation.
        turns=json.loads((session.run_dir/'conversation.json').read_text(encoding='utf-8')) if (session.run_dir/'conversation.json').exists() else [{'turn_id':'turn-user-001','role':'user','content':brief['original_request']}]
        result=run_design_brief_stage(provider=provider,output_dir=session.run_dir/'calls/01-design-brief',design_brief_schema_version='text2ifc/design-brief/2.3',case={'case_id':session.session_hash,'user_request':brief['original_request'],'conversation':turns,'call_index':1})
        assert result['valid'],result
        store.record_agent_call(session.session_id,{'role':'design_brief','call_index':1,**result});store.mark_session_status(session.session_id,'ready')
        result=run_ready_session_to_ifc(store=store,session=session.session_hash,provider_factory=lambda:provider,generation_strategy='legacy_full')
        assert result.status=='compiled',result
        check=check_ifc(Path(result.ifc_path));assert check['status']=='passed',check['failed']
        (runtime/'independent-checks.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
        (runtime/'result.json').write_text(json.dumps(dict(status='passed',evidence_class='hand_authored_fake_offline',provider_transport=False,provider_calls=len(provider.calls),run_dir=str(session.run_dir),check_count=check['check_count']),indent=2),encoding='utf-8')
        print('Offline public fake: compiled,',check['check_count'],'native checks passed.')
