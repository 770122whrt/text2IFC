"""Frozen synthetic installation family: public surviving references, no Gold.

The frame's normal centre is the installation invariant. Asymmetric hardware
must not translate it. This is offline defect/regression evidence, not a model
capability or an unrevealed formal benchmark.
"""
from __future__ import annotations

import hashlib
from copy import deepcopy
import json
import math

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair import door_geometry as geometry
from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm
from text2ifc_ifc_repair.operations.hosted_opening import local_placement


def scene(*, overhang=60., sign=1., angle=0., millimetres=False):
    """Authored IFC: 900x2100 opening, 150 wall, frame 5 mm proud each face."""
    m = ifcopenshell.file(schema='IFC2X3')
    unit = 1. if millimetres else .001
    point = lambda xyz: m.createIfcCartesianPoint(tuple(float(v)*unit for v in xyz))
    axis = lambda xyz: m.createIfcAxis2Placement3D(point(xyz))
    person = m.createIfcPerson(FamilyName='Offline')
    org = m.createIfcOrganization(Name='Synthetic public fixture')
    app = m.createIfcApplication(org, '1', 'Synthetic fixture', 'test')
    owner = m.createIfcOwnerHistory(m.createIfcPersonAndOrganization(person, org), app, None, 'ADDED', None, None, None, 1)
    context = m.createIfcGeometricRepresentationContext(None, 'Model', 3, 1e-5, axis((0,0,0)), None)
    units = m.createIfcUnitAssignment([m.createIfcSIUnit(None, 'LENGTHUNIT', 'MILLI' if millimetres else None, 'METRE')])
    project = m.createIfcProject(ifcopenshell.guid.new(), owner, 'Public synthetic scene', None, None, None, None, [context], units)
    def root(cls, **kw):
        return m.create_entity(cls, GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, **kw)
    def box(x0,x1,y0,y1,z0,z1):
        p = m.createIfcAxis2Placement2D(m.createIfcCartesianPoint(((x0+x1)/2*unit,(y0+y1)/2*unit)), None)
        profile = m.createIfcRectangleProfileDef('AREA', None, p, (x1-x0)*unit,(y1-y0)*unit)
        return m.createIfcExtrudedAreaSolid(profile, axis((0,0,z0)), m.createIfcDirection((0.,0.,1.)), (z1-z0)*unit)
    def rep(items):
        return m.createIfcShapeRepresentation(context, 'Body', 'SweptSolid', items)
    def shape(product, items):
        product.Representation = m.createIfcProductDefinitionShape(None,None,[rep(items)])
    storey = root('IfcBuildingStorey', Name='Ground', CompositionType='ELEMENT', Elevation=0.)
    storey.ObjectPlacement = local_placement(m, relative_to=None, location=(0.,0.,0.))
    root('IfcRelAggregates', RelatingObject=project, RelatedObjects=[storey])
    wall = root('IfcWall', Name='Public host')
    wall.ObjectPlacement = local_placement(m, relative_to=storey.ObjectPlacement,
        location=(1.*1000*unit,2.*1000*unit,0.), ref_direction=(math.cos(math.radians(angle)),math.sin(math.radians(angle)),0.))
    shape(wall,[box(0,6000,0,150,0,3000)])
    # Axis permits the production index to derive wall-local public positions.
    wall.Representation.Representations = [*wall.Representation.Representations,
        m.createIfcShapeRepresentation(context,'Axis','Curve2D',[m.createIfcPolyline([
            m.createIfcCartesianPoint((0.,0.)),m.createIfcCartesianPoint((6000*unit,0.))])])]
    containment=root('IfcRelContainedInSpatialStructure', RelatingStructure=storey, RelatedElements=[wall])
    openings=[]
    for x in (500.,3500.):
        opening=root('IfcOpeningElement',Name='Public opening')
        opening.ObjectPlacement=local_placement(m,relative_to=wall.ObjectPlacement,location=(x*unit,0.,0.))
        shape(opening,[box(0,900,0,150,0,2100)])
        root('IfcRelVoidsElement',RelatingBuildingElement=wall,RelatedOpeningElement=opening)
        openings.append(opening)
    # Frame is symmetric; only the small hardware component changes its reach.
    frame=[box(-5,25,-80,80,0,2110),box(875,905,-80,80,0,2110),box(25,875,-80,80,2080,2110)]
    panel=box(25,875,30,70,0,2080)
    handle=box(700,800,70,80+overhang,900,1000) if overhang else box(700,800,60,80,900,1000)
    mapped=m.createIfcRepresentationMap(axis((0,0,0)),rep([*frame,panel,handle]))
    style=root('IfcDoorStyle',Name='Public single door',OperationType='SINGLE_SWING_LEFT',ConstructionType='WOOD',ParameterTakesPrecedence=False,Sizeable=False,RepresentationMaps=[mapped])
    def door(name):
        d=root('IfcDoor',Name=name,OverallWidth=900*unit,OverallHeight=2100*unit)
        d.Representation=m.createIfcProductDefinitionShape(None,None,[ifcopenshell.api.geometry.map_representation(m,representation=mapped.MappedRepresentation)])
        return d
    reference=door('Public reference')
    reference.ObjectPlacement=local_placement(m,relative_to=openings[1].ObjectPlacement,
        location=((0 if sign>0 else 900)*unit,75*unit,0.),ref_direction=(sign,0.,0.))
    root('IfcRelFillsElement',RelatingOpeningElement=openings[1],RelatedBuildingElement=reference)
    root('IfcRelDefinesByType',RelatingType=style,RelatedObjects=[reference])
    containment.RelatedElements=[wall,reference]
    return m, openings[0], reference, door, unit


def install(model, opening, door, placement):
    door.ObjectPlacement=local_placement(model,relative_to=opening.ObjectPlacement,
        location=placement['location'],ref_direction=placement['ref_direction'])


@pytest.mark.parametrize('overhang,sign,angle,millimetres',[
    (60.,1.,0.,False),(120.,1.,0.,False),(60.,-1.,0.,False),
    (60.,1.,90.,False),(60.,-1.,180.,True),(0.,1.,90.,True),
])
def test_public_anchor_preserves_frame_not_hardware_centre(overhang,sign,angle,millimetres):
    m,opening,reference,create,unit=scene(overhang=overhang,sign=sign,angle=angle,millimetres=millimetres)
    candidate=create('New door')
    anchor=geometry.public_door_installation_anchor(reference)
    chosen=geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)
    install(m,opening,candidate,chosen)
    # Independent authored frame installation, not an expectation from selector.
    assert chosen['location'][1]/unit == pytest.approx(75.,abs=1e-5)
    assert chosen['ref_direction'][0] == sign
    assert geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']
    assert reference.ObjectPlacement.RelativePlacement.Location.Coordinates[1]/unit == 75.


def test_legacy_centring_reproduces_asymmetric_failure_without_reference():
    m,opening,reference,create,unit=scene(overhang=60.)
    candidate=create('Legacy placement')
    chosen=geometry.select_door_placement_in_opening(candidate,opening)
    assert chosen['location'][1]/unit == pytest.approx(45.)
    install(m,opening,candidate,chosen)
    assert geometry.measure_door_opening_alignment(candidate,opening)['valid']
    # This false-positive legacy control is retained; reference-aware L1 must
    # reject it without changing legacy operations which have no public anchor.
    anchor=geometry.public_door_installation_anchor(reference)
    assert not geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']


@pytest.mark.parametrize('delta',[5.01,30.,-30.])
def test_reference_aware_l1_rejects_displacement(delta):
    m,opening,reference,create,unit=scene()
    candidate=create('Displaced')
    anchor=geometry.public_door_installation_anchor(reference)
    chosen=geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)
    chosen['location']=tuple(v+(delta*unit if i==1 else 0) for i,v in enumerate(chosen['location']))
    install(m,opening,candidate,chosen)
    assert not geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']


@pytest.mark.parametrize('fault',['no_fill','two_fills','no_host','two_hosts','different_depth'])
def test_public_anchor_fails_closed_on_missing_or_ambiguous_relationships(fault):
    m,opening,reference,create,unit=scene()
    ref_open=reference.FillsVoids[0].RelatingOpeningElement
    if fault=='no_fill': m.remove(reference.FillsVoids[0])
    if fault=='two_fills':
        m.createIfcRelFillsElement(ifcopenshell.guid.new(),reference.OwnerHistory,None,None,opening,reference)
    if fault=='no_host': m.remove(ref_open.VoidsElements[0])
    if fault=='two_hosts':
        m.createIfcRelVoidsElement(ifcopenshell.guid.new(),reference.OwnerHistory,None,None,ref_open.VoidsElements[0].RelatingBuildingElement,ref_open)
    if fault=='different_depth':
        opening.Representation.Representations[0].Items[0].SweptArea.YDim=200*unit
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_'):
        anchor=geometry.public_door_installation_anchor(reference)
        geometry.select_door_placement_in_opening(create('New'),opening,installation_anchor=anchor)


class PublicOnlyProvider:
    def __init__(self, *, batch=False, unoffered=False, tamper_anchor=False):
        self.calls=[]
        self.batch,self.unoffered,self.tamper_anchor=batch,unoffered,tamper_anchor
    def generate_candidate(self,**kw):
        from text2ifc_agent.providers import ProviderOutput
        from scripts.ifc_repair.repair_comparison.ours_adapter import _draft,_section,fixture_intent
        self.calls.append(kw)
        prompt=kw['prompt']
        if '## Immutable bindings' in prompt:
            value=_draft(prompt,kw.get('schema') or _section(prompt,'Draft schema'))
            if self.tamper_anchor:
                value['operations'][0]['parameters']['door_installation_anchor']['reference_global_id']='unoffered'
        else:
            pages=_section(prompt,'Read-only query results so far')
            if not pages:
                value={'kind':'query','query':{'ifc_classes':['IfcOpeningElement','IfcDoor']}}
            else:
                rows=pages[0]['records']
                target=next(r for r in rows if r['ifc_class']=='IfcOpeningElement' and not r['filling_ids'])
                reference=next(r for r in rows if r['ifc_class']=='IfcDoor')
                body=fixture_intent('door',{'allowed_ifc_classes':['IfcOpeningElement']},
                    {'fit_existing_opening':True,'door':{'operation_type':'SINGLE_SWING_LEFT','formal_enum_explicit':True}})
                body['operations'][0]['prototype_intent']={'reference_kind':'global_id','reference':reference['type_id'],
                    'source':body['operations'][0]['provenance'][0]}
                targets=[r for r in rows if r['ifc_class']=='IfcOpeningElement' and not r['filling_ids']] if self.batch else [target]
                operation=body['operations'][0]
                body['operations']=[]
                bindings=[]
                for index, target in enumerate(targets):
                    op=deepcopy(operation)
                    op['operation_id']=f'offline-repair-{index}'
                    body['operations'].append(op)
                    bindings.append({'operation_id':op['operation_id'],'target_id':target['id'],
                        'reference_id':'unoffered' if self.unoffered else reference['id']})
                value={'kind':'intent','intent':body,'bindings':bindings}
        return ProviderOutput(text=json.dumps(value),metadata={'provider':'fixture','model':'offline-anchor-family','evidence_class':'offline_fake'})


def test_public_fake_api_reopen_keeps_reference_installation_and_source(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    m,opening,reference,_,unit=scene()
    source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    provider=PublicOnlyProvider()
    result=RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(source,
        'Fill the empty opening with a 900 by 2100 mm door. Use the retained door as the frame and finish reference; align the base.')
    assert result.status=='succeeded',result.to_dict()
    root=tmp_path/'run'/result.run_directory
    output=ifcopenshell.open(str(root/result.artifacts['successful_ifc']))
    created=next(d for d in output.by_type('IfcDoor') if d.GlobalId!=reference.GlobalId)
    # Source frame was at y=75 mm; reference-aware placement must retain it.
    assert created.ObjectPlacement.RelativePlacement.Location.Coordinates[1]/unit==pytest.approx(75.)
    assert source.read_bytes()==before
    assert all('private' not in str(call['state']) for call in provider.calls)
    manifest=json.loads((root/result.artifacts['manifest']).read_text(encoding='utf8'))
    evidence=next(a['path'] for a in manifest['artifacts'] if a['role']=='public_evidence')
    application=json.loads((root/evidence).read_text(encoding='utf8'))['evidence']['application']
    assert application['published'] and application['valid']


def test_anchor_and_offered_identity_persist_across_public_api_restart(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    class CrashAfterIntent(RepairAPI):
        def _resolve_and_finish(self,*args,**kwargs):
            raise RuntimeError('offline crash after committed intent')
    m,opening,reference,_,unit=scene(sign=-1.,angle=90.,millimetres=True)
    source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    provider=PublicOnlyProvider()
    with pytest.raises(RuntimeError,match='offline crash'):
        CrashAfterIntent(tmp_path/'run',provider=provider,scene_grounding=True).start(source,'Use the retained door to fill the empty opening.')
    run=next((tmp_path/'run/runs').iterdir())
    context=json.loads((run/'api-context.json').read_text(encoding='utf8'))
    assert context['schema_version']=='text2ifc/ifc-repair-api-context/0.3'
    assert context['installation_references']['offline-repair-0']['reference_global_id']==reference.GlobalId
    result=RepairAPI(tmp_path/'run',provider=provider).resume(run.name)
    assert result.status=='succeeded',result.to_dict()
    repaired=ifcopenshell.open(str(run/result.artifacts['successful_ifc']))
    door=next(d for d in repaired.by_type('IfcDoor') if d.GlobalId!=reference.GlobalId)
    assert door.ObjectPlacement.RelativePlacement.Location.Coordinates[1]/unit==pytest.approx(75.)
    assert geometry.measure_door_opening_alignment(door,repaired.by_guid(opening.GlobalId),
        installation_anchor=geometry.public_door_installation_anchor(repaired.by_guid(reference.GlobalId)))['valid']
    assert source.read_bytes()==before


@pytest.mark.parametrize('fault',['unoffered','stage2_anchor'])
def test_public_api_cannot_use_unoffered_or_model_rewritten_anchor(tmp_path,fault):
    from text2ifc_ifc_repair.api import RepairAPI
    m,*_=scene();source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    provider=PublicOnlyProvider(unoffered=fault=='unoffered',tamper_anchor=fault=='stage2_anchor')
    result=RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(source,'Fill the empty opening using the retained door.')
    assert result.status=='provider_failed',result.to_dict()
    assert not result.successful_artifact_publishable and 'successful_ifc' not in result.artifacts
    assert source.read_bytes()==before


def test_second_door_l1_failure_rolls_back_whole_public_batch(tmp_path,monkeypatch):
    from text2ifc_ifc_repair.api import RepairAPI
    from text2ifc_ifc_repair.operations import door as door_operation
    from ifcopenshell.util.element import copy_deep
    m,opening,reference,_,unit=scene()
    wall=opening.VoidsElements[0].RelatingBuildingElement
    extra=m.createIfcOpeningElement(ifcopenshell.guid.new(),opening.OwnerHistory,'Second empty')
    extra.ObjectPlacement=local_placement(m,relative_to=wall.ObjectPlacement,location=(2000*unit,0.,0.))
    extra.Representation=copy_deep(m,opening.Representation,exclude=('IfcGeometricRepresentationContext',))
    m.createIfcRelVoidsElement(ifcopenshell.guid.new(),opening.OwnerHistory,None,None,wall,extra)
    source=tmp_path/'public.ifc';m.write(str(source));before=source.read_bytes()
    original=door_operation._create_door
    calls=[]
    def displaced_second(**kw):
        changes=original(**kw);calls.append(changes)
        if len(calls)==2:
            d=kw['model'].by_guid(next(c['global_id'] for c in changes['created'] if c['role']=='door'))
            coords=list(d.ObjectPlacement.RelativePlacement.Location.Coordinates)
            coords[1]+=30*unit
            d.ObjectPlacement.RelativePlacement.Location.Coordinates=coords
        return changes
    monkeypatch.setattr(door_operation,'_create_door',displaced_second)
    result=RepairAPI(tmp_path/'run',provider=PublicOnlyProvider(batch=True),scene_grounding=True).start(source,'Fill both empty openings using the retained reference door.')
    assert len(calls)==2
    assert result.status=='application_failed' and 'successful_ifc' not in result.artifacts
    assert not list((tmp_path/'run').rglob('application-candidate.ifc'))
    assert not list((tmp_path/'run').rglob('repaired.ifc'))
    assert source.read_bytes()==before


def test_anchor_tampering_and_reference_mapping_changes_fail_closed():
    m,opening,reference,create,_=scene()
    anchor=geometry.public_door_installation_anchor(reference)
    tampered=deepcopy(anchor);tampered['normal_center_offset_mm']=0.
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_ANCHOR_MISMATCH'):
        geometry.select_door_placement_in_opening(create('New'),opening,installation_anchor=tampered)
    candidate=create('Different mapping')
    candidate.Representation.Representations[0].Items[0].MappingTarget.Scale=2.
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_MAPPING_MISMATCH'):
        geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)


def test_equal_depth_cutter_shift_cannot_silently_move_reference_frame_in_wall():
    m,opening,reference,create,unit=scene()
    anchor=geometry.public_door_installation_anchor(reference)
    coords=list(opening.ObjectPlacement.RelativePlacement.Location.Coordinates)
    coords[1]+=20*unit
    opening.ObjectPlacement.RelativePlacement.Location.Coordinates=coords
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_OPENING_DEPTH_ORIGIN_UNSUPPORTED'):
        geometry.select_door_placement_in_opening(create('New'),opening,installation_anchor=anchor)
