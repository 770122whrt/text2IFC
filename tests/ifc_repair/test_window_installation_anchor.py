"""Frozen offline family for public-reference window installation and sizes.

All geometry is independently authored synthetic public IFC. No benchmark
Gold, deleted identity, case-specific offset or real Provider is used.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import math

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair import window_geometry as geometry
from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm, opening_dimensions_mm
from text2ifc_ifc_repair.operations.hosted_opening import local_placement


def scene(*, extension=25., normal=-45., sign=1., angle=0., millimetres=False,
          opening_height=1200., nominal_height=1200., body_height=None,
          base_gap=0., cut_depth=150., cut_center=0.):
    """Author a public frame, glazing and optional projecting window board."""
    m=ifcopenshell.file(schema='IFC2X3'); unit=1. if millimetres else .001
    body_height=opening_height if body_height is None else body_height
    point=lambda xyz:m.createIfcCartesianPoint(tuple(float(v)*unit for v in xyz))
    axis=lambda xyz:m.createIfcAxis2Placement3D(point(xyz))
    person=m.createIfcPerson(FamilyName='Offline')
    org=m.createIfcOrganization(Name='Synthetic public window fixture')
    app=m.createIfcApplication(org,'1','Synthetic fixture','test')
    owner=m.createIfcOwnerHistory(m.createIfcPersonAndOrganization(person,org),app,None,'ADDED',None,None,None,1)
    context=m.createIfcGeometricRepresentationContext(None,'Model',3,1e-5,axis((0,0,0)),None)
    units=m.createIfcUnitAssignment([m.createIfcSIUnit(None,'LENGTHUNIT','MILLI' if millimetres else None,'METRE')])
    def root(cls,**kw):
        return m.create_entity(cls,GlobalId=ifcopenshell.guid.new(),OwnerHistory=owner,**kw)
    project=root('IfcProject',Name='Public synthetic scene',RepresentationContexts=[context],UnitsInContext=units)
    def box(x0,x1,y0,y1,z0,z1):
        p=m.createIfcAxis2Placement2D(m.createIfcCartesianPoint(((x0+x1)/2*unit,(y0+y1)/2*unit)),None)
        profile=m.createIfcRectangleProfileDef('AREA',None,p,(x1-x0)*unit,(y1-y0)*unit)
        return m.createIfcExtrudedAreaSolid(profile,axis((0,0,z0)),m.createIfcDirection((0.,0.,1.)),(z1-z0)*unit)
    def rep(items): return m.createIfcShapeRepresentation(context,'Body','SweptSolid',items)
    def shape(product,items):product.Representation=m.createIfcProductDefinitionShape(None,None,[rep(items)])
    storey=root('IfcBuildingStorey',Name='Ground',CompositionType='ELEMENT',Elevation=0.)
    storey.ObjectPlacement=local_placement(m,relative_to=None,location=(0.,0.,0.))
    root('IfcRelAggregates',RelatingObject=project,RelatedObjects=[storey])
    wall=root('IfcWall',Name='Public straight host')
    wall.ObjectPlacement=local_placement(m,relative_to=storey.ObjectPlacement,
        location=(1000*unit,2000*unit,0.),ref_direction=(math.cos(math.radians(angle)),math.sin(math.radians(angle)),0.))
    shape(wall,[box(0,7000,-75,75,0,3000)])
    wall.Representation.Representations=[*wall.Representation.Representations,
        m.createIfcShapeRepresentation(context,'Axis','Curve2D',[m.createIfcPolyline([
            m.createIfcCartesianPoint((0.,0.)),m.createIfcCartesianPoint((7000*unit,0.))])])]
    opening=root('IfcOpeningElement',Name='Retained public opening')
    opening.ObjectPlacement=local_placement(m,relative_to=wall.ObjectPlacement,location=(5000*unit,0.,700*unit))
    shape(opening,[box(0,900,cut_center-cut_depth/2,cut_center+cut_depth/2,0,opening_height)])
    root('IfcRelVoidsElement',RelatingBuildingElement=wall,RelatedOpeningElement=opening)
    frame=[box(0,30,-20,20,0,body_height),box(870,900,-20,20,0,body_height),
           box(30,870,-20,20,0,30),box(30,870,-20,20,body_height-30,body_height)]
    glass=box(30,870,-2,2,30,body_height-30)
    board=[box(-extension,900+extension,-30,45,-10,0)] if extension else []
    mapped=m.createIfcRepresentationMap(axis((0,0,0)),rep([*frame,glass,*board]))
    style=root('IfcWindowStyle',Name='Public mapped window',OperationType='SINGLE_PANEL',
        ConstructionType='ALUMINIUM',ParameterTakesPrecedence=False,Sizeable=False,RepresentationMaps=[mapped])
    common=root('IfcPropertySet',Name='Pset_WindowCommon',HasProperties=[
        m.createIfcPropertySingleValue('IsExternal',None,m.createIfcBoolean(True),None)])
    style.HasPropertySets=[common]
    def window(name):
        w=root('IfcWindow',Name=name,OverallWidth=900*unit,OverallHeight=nominal_height*unit)
        w.Representation=m.createIfcProductDefinitionShape(None,None,[
            ifcopenshell.api.geometry.map_representation(m,representation=mapped.MappedRepresentation)])
        return w
    reference=window('Public reference window')
    reference.ObjectPlacement=local_placement(m,relative_to=opening.ObjectPlacement,
        location=((0 if sign>0 else 900)*unit,normal*unit,base_gap*unit),ref_direction=(sign,0.,0.))
    root('IfcRelFillsElement',RelatingOpeningElement=opening,RelatedBuildingElement=reference)
    root('IfcRelDefinesByType',RelatingType=style,RelatedObjects=[reference])
    root('IfcRelContainedInSpatialStructure',RelatingStructure=storey,RelatedElements=[wall,reference])
    return m,wall,opening,reference,window,unit


class PublicWindowProvider:
    def __init__(self,*,batch=False,unoffered=False,tamper=False,opening_height=1200.,nominal_height=1200.,public_reference_id=None):
        self.calls=[];self.batch=batch;self.unoffered=unoffered;self.tamper=tamper
        self.opening_height=opening_height;self.nominal_height=nominal_height
        self.public_reference_id=public_reference_id
    def generate_candidate(self,**kw):
        from text2ifc_agent.providers import ProviderOutput
        from scripts.ifc_repair.repair_comparison.ours_adapter import _draft,_section,fixture_intent
        self.calls.append(kw);prompt=kw['prompt']
        if '## Immutable bindings' in prompt:
            value=_draft(prompt,kw.get('schema') or _section(prompt,'Draft schema'))
            if self.tamper:
                value['operations'][0]['evidence_refs'].append('public-window-installation/0.1:unoffered')
        else:
            pages=_section(prompt,'Read-only query results so far')
            if not pages:
                value={'kind':'query','query':{'ifc_classes':['IfcWall','IfcWindow']}}
            else:
                rows=pages[0]['records'];wall=next(r for r in rows if r['ifc_class']=='IfcWall')
                reference=next(r for r in rows if r['ifc_class']=='IfcWindow'
                    and (self.public_reference_id is None or r['id']==self.public_reference_id))
                body=fixture_intent('window',{'allowed_ifc_classes':['IfcWall']},{
                    'opening':{'width_mm':900.,'height_mm':self.opening_height,'sill_height_mm':700.},
                    'window':{'fit_opening':True}})
                op=body['operations'][0]
                op['prototype_intent']={'reference_kind':'global_id','reference':reference['type_id'],'source':op['provenance'][0]}
                op['attribute_intents']=[{'intent_kind':'attribute','name':name,'value':v,'source':op['provenance'][0]}
                    for name,v in [('OverallWidth',900.),('OverallHeight',self.nominal_height)]]
                body['operations']=[];bindings=[]
                for i,offset in enumerate([1500.,3200.] if self.batch else [1500.]):
                    current=deepcopy(op);current['operation_id']=f'offline-window-{i}'
                    body['operations'].append(current)
                    axis=wall['wall_axis'];p=[axis['start_world_mm'][j]+offset*axis['direction_world'][j] for j in range(3)]
                    bindings.append({'operation_id':current['operation_id'],'target_id':wall['id'],
                        'reference_id':'unoffered' if self.unoffered else reference['id'],
                        'position':{'kind':'world_point','point_world_mm':p}})
                value={'kind':'intent','intent':body,'bindings':bindings}
        return ProviderOutput(text=json.dumps(value),metadata={'provider':'fixture','model':'offline-window-family','evidence_class':'offline_fake'})


def api_case(tmp_path,**configuration):
    from text2ifc_ifc_repair.api import RepairAPI
    m,wall,opening,reference,_,unit=scene(**configuration)
    source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    provider=PublicWindowProvider(opening_height=configuration.get('opening_height',1200.),
        nominal_height=configuration.get('nominal_height',1200.))
    result=RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(source,
        'Add a window at the requested wall position and sill. Preserve the retained window frame, glazing and installation. Use the separately specified nominal and opening sizes.')
    assert source.read_bytes()==before
    return result,source,reference.GlobalId,unit,provider


@pytest.mark.parametrize('configuration',[
    {'extension':25.,'normal':-45.},
    {'extension':60.,'normal':35.,'sign':-1.,'angle':90.},
    {'extension':25.,'normal':-45.,'angle':180.,'millimetres':True},
    {'extension':0.,'normal':-90.,'cut_depth':450.},
    {'extension':25.,'normal':35.,'sign':-1.,'angle':37.,'millimetres':True},
])
def test_public_api_preserves_exact_reference_installation(tmp_path,configuration):
    result,source,reference_id,unit,provider=api_case(tmp_path,**configuration)
    assert result.status=='succeeded',result.to_dict()
    repaired=ifcopenshell.open(str(tmp_path/'run'/result.run_directory/result.artifacts['successful_ifc']))
    reference=repaired.by_guid(reference_id);wall=reference.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
    new=next(w for w in repaired.by_type('IfcWindow') if w.GlobalId!=reference_id)
    actual=product_geometry_bounds_in_host_mm(new,wall);expected=product_geometry_bounds_in_host_mm(reference,wall)
    assert actual['y']==pytest.approx(expected['y'],abs=.1)
    assert actual['z']==pytest.approx(expected['z'],abs=.1)
    assert (sum(actual['x'])/2)-(sum(expected['x'])/2)==pytest.approx(-3950.,abs=.1)
    context=json.loads((tmp_path/'run'/result.run_directory/'api-context.json').read_text(encoding='utf8'))
    assert context['installation_references']['offline-window-0']['reference_global_id']==reference_id
    assert all('Gold' not in str(call['state']) for call in provider.calls)


@pytest.mark.parametrize('millimetres,angle',[(False,0.),(True,90.)])
def test_nominal_height_and_void_height_are_separate_authorities(tmp_path,millimetres,angle):
    result,source,reference_id,unit,_=api_case(tmp_path,millimetres=millimetres,angle=angle,
        extension=0.,opening_height=1190.,nominal_height=1200.,body_height=1170.,base_gap=20.)
    assert result.status=='succeeded',result.to_dict()
    m=ifcopenshell.open(str(tmp_path/'run'/result.run_directory/result.artifacts['successful_ifc']))
    w=next(w for w in m.by_type('IfcWindow') if w.GlobalId!=reference_id)
    assert w.OverallHeight/unit==pytest.approx(1200.)
    assert opening_dimensions_mm(w.FillsVoids[0].RelatingOpeningElement)['height']==pytest.approx(1190.)


@pytest.mark.parametrize('name',['OverallWidth','attribute:OverallHeight'])
@pytest.mark.parametrize('value',[1200,1200.5])
def test_explicit_dimension_authority_uses_declared_ifc_attribute_type(name,value):
    from text2ifc_ifc_repair.production_evidence import _request_fact
    from text2ifc_ifc_repair.repair_intent import AttributeIntent,PublicProvenance
    source=PublicProvenance('user_request','request:/text','The nominal size is explicitly specified.')
    fact=_request_fact('window-or-door',AttributeIntent('attribute',name,value,source))
    assert fact.value_type=='IfcPositiveLengthMeasure'
    assert fact.value==value and fact.unit is None and fact.source_ref=='request:/text'


@pytest.mark.parametrize('value',[0,-1,True,'1200',None,float('nan'),float('inf')])
def test_explicit_dimension_authority_rejects_invalid_lengths(value):
    from text2ifc_ifc_repair.production_evidence import ProductionEvidenceError,_request_fact
    from text2ifc_ifc_repair.repair_intent import AttributeIntent,PublicProvenance
    source=PublicProvenance('user_request','request:/text','An invalid dimension is not an authorized length.')
    with pytest.raises(ProductionEvidenceError,match='REQUEST_DIMENSION_INVALID'):
        _request_fact('window-or-door',AttributeIntent('attribute','OverallWidth',value,source))


@pytest.mark.parametrize('kind,name,value,expected',[
    ('attribute','Name','1200','IfcLabel'),('pset','Pset_Custom.Count',1200,'IfcInteger'),
])
def test_dimension_typing_does_not_coerce_labels_or_property_slots(kind,name,value,expected):
    from text2ifc_ifc_repair.production_evidence import _request_fact
    from text2ifc_ifc_repair.repair_intent import AttributeIntent,PublicProvenance
    source=PublicProvenance('user_request','request:/text','An ordinary slot retains its existing type.')
    assert _request_fact('window-or-door',AttributeIntent(kind,name,value,source)).value_type==expected


@pytest.mark.parametrize('fault',['unoffered','stage2_anchor'])
def test_public_api_rejects_unoffered_or_rewritten_reference(tmp_path,fault):
    from text2ifc_ifc_repair.api import RepairAPI
    m,*_=scene();source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    provider=PublicWindowProvider(unoffered=fault=='unoffered',tamper=fault=='stage2_anchor')
    result=RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(source,'Add a window using the retained public reference.')
    assert result.status=='provider_failed',result.to_dict()
    assert 'successful_ifc' not in result.artifacts and not result.successful_artifact_publishable
    assert source.read_bytes()==before


def test_verified_window_reference_survives_restart(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    class CrashAfterIntent(RepairAPI):
        def _resolve_and_finish(self,*args,**kwargs):raise RuntimeError('offline window crash')
    m,_,_,reference,_,unit=scene(sign=-1.,angle=90.,millimetres=True)
    source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    provider=PublicWindowProvider()
    with pytest.raises(RuntimeError,match='offline window crash'):
        CrashAfterIntent(tmp_path/'run',provider=provider,scene_grounding=True).start(source,'Use the retained window to repair the requested position.')
    run=next((tmp_path/'run/runs').iterdir())
    context=json.loads((run/'api-context.json').read_text(encoding='utf8'))
    assert context['installation_references']['offline-window-0']['reference_global_id']==reference.GlobalId
    result=RepairAPI(tmp_path/'run',provider=provider).resume(run.name)
    assert result.status=='succeeded',result.to_dict()
    assert source.read_bytes()==before


@pytest.mark.parametrize('fault',['no_fill','two_fills','no_host','two_hosts','no_type','nonpositive_nominal','tilted'])
def test_missing_ambiguous_or_incompatible_reference_fails_closed(fault):
    m,wall,opening,reference,_,unit=scene()
    if fault=='no_fill':m.remove(reference.FillsVoids[0])
    if fault=='two_fills':m.createIfcRelFillsElement(ifcopenshell.guid.new(),reference.OwnerHistory,None,None,opening,reference)
    if fault=='no_host':m.remove(opening.VoidsElements[0])
    if fault=='two_hosts':m.createIfcRelVoidsElement(ifcopenshell.guid.new(),reference.OwnerHistory,None,None,wall,opening)
    if fault=='no_type':m.remove(next(r for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType')))
    if fault=='nonpositive_nominal':reference.OverallWidth=0.
    if fault=='tilted':reference.ObjectPlacement.RelativePlacement.Axis.DirectionRatios=(0.,1.,1.)
    with pytest.raises(ValueError,match='WINDOW_INSTALLATION_'):
        geometry.public_window_installation_anchor(reference)


@pytest.mark.parametrize('fault',['shift','mapping','anchor','wrong_size','different_thickness'])
def test_independent_window_witness_rejects_tampering(fault):
    m,wall,reference_opening,reference,create,unit=scene()
    anchor=geometry.public_window_installation_anchor(reference)
    opening=m.create_entity('IfcOpeningElement',GlobalId=ifcopenshell.guid.new(),OwnerHistory=reference.OwnerHistory)
    opening.Representation=reference_opening.Representation
    opening.ObjectPlacement=local_placement(m,relative_to=wall.ObjectPlacement,location=(1000*unit,0.,700*unit))
    m.createIfcRelVoidsElement(ifcopenshell.guid.new(),reference.OwnerHistory,None,None,wall,opening)
    new=create('New public window')
    style=next(r.RelatingType for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    placement=geometry.select_window_placement_in_opening(new,opening,style,host_wall=wall,installation_anchor=anchor)
    new.ObjectPlacement=local_placement(m,relative_to=opening.ObjectPlacement,location=placement['location'],ref_direction=placement['ref_direction'])
    assert geometry.measure_window_installation(new,opening,anchor)['valid']
    if fault=='shift':new.ObjectPlacement.RelativePlacement.Location.Coordinates=tuple(v+(.101*unit if i==1 else 0) for i,v in enumerate(placement['location']))
    if fault=='mapping':new.Representation.Representations[0].Items[0].MappingTarget.Scale=1.01
    if fault=='anchor':anchor['normal_center_offset_from_wall_mm']+=1.
    if fault=='wrong_size':new.OverallHeight+=unit
    if fault=='different_thickness':wall.Representation.Representations[0].Items[0].SweptArea.YDim=180*unit
    assert not geometry.measure_window_installation(new,opening,anchor)['valid']


@pytest.mark.parametrize('write_failure',[False,True])
def test_batch_distinct_sizes_and_atomic_publication(tmp_path,monkeypatch,write_failure):
    from text2ifc_ifc_repair.api import RepairAPI
    m,_,_,reference,_,unit=scene(opening_height=1190.,nominal_height=1200.,body_height=1170.,base_gap=20.)
    source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    injected=[]
    if write_failure:
        original=ifcopenshell.file.write
        def fail(model,path,*args,**kwargs):
            value=original(model,path,*args,**kwargs)
            if 'application-candidate.ifc-' in str(path):
                injected.append(str(path));raise OSError('offline injected window batch write failure')
            return value
        monkeypatch.setattr(ifcopenshell.file,'write',fail)
    provider=PublicWindowProvider(batch=True,opening_height=1190.,nominal_height=1200.)
    result=RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(source,'Add two windows with the requested nominal and opening sizes using the retained public window.')
    assert source.read_bytes()==before
    if write_failure:
        assert injected and not result.successful_artifact_publishable
        assert 'successful_ifc' not in result.artifacts and all(not Path(p).exists() for p in injected)
    else:
        assert result.status=='succeeded',result.to_dict()
        repaired=ifcopenshell.open(str(tmp_path/'run'/result.run_directory/result.artifacts['successful_ifc']))
        new=[w for w in repaired.by_type('IfcWindow') if w.GlobalId!=reference.GlobalId]
        assert len(new)==2
        for w in new:
            assert w.OverallHeight/unit==pytest.approx(1200.)
            assert opening_dimensions_mm(w.FillsVoids[0].RelatingOpeningElement)['height']==pytest.approx(1190.)
