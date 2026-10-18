"""Offline public-occurrence Brep reuse family, frozen before implementation.

The retained door has no Type maps. Its complete, styled Body contains a
full-size frame plus a narrower leaf and projecting hardware. All dimensions
and expected placements below are authored synthetic facts, never Gold or a
revealed formal-case recipe. Fake Providers select only offered public IDs.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.guid
import ifcopenshell.util.placement
import pytest

from text2ifc_ifc_repair import door_geometry as geometry
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm
from text2ifc_ifc_repair.operations.hosted_opening import local_placement
from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider, install


REQUEST = (
    'Fill the empty opening with a 900 by 2100 mm single-swing door, using '
    'the retained public door as the complete frame, leaf, hardware and finish '
    'reference. Keep all existing geometry unchanged. Keep the retained '
    'installation relative to the target wall face and adapt to wall thickness.'
)
REQUEST_ZH = (
    '用保留的公开参照门补齐空洞口，门宽900毫米、高2100毫米，单扇平开。'
    '完整复用门框、门扇、把手及材质，保持已有构件不变。'
    '门框相对于目标墙面的进出位置按参照门相对于其墙面的方式安装，并适配墙厚。'
)
REQUEST_NO_ADAPTATION = (
    'Fill the empty opening with a 900 by 2100 mm single-swing door, using '
    'the retained public door as the complete frame, leaf, hardware and finish '
    'reference. Keep all existing geometry unchanged.'
)


def brep_scene(*, millimetres=False, angle=0., sign=1.,
               target_thickness_mm=150., fault=None):
    """Return public model, empty opening, retained door, project units/mm.

    Two independent walls prevent a target-thickness change from changing the
    reference. The reference frame is 900 x 2100 x 50 mm; its outer face is
    flush with the 150 mm source wall. The complete Body is 130 mm deep.
    The Body centre is therefore 15 mm beyond the chosen wall face. The frame,
    rather than the hardware endpoint, independently identifies that face.

    ``fault``: missing_frame, ambiguous_frame, invalid_body.
    """
    if sign not in (-1., 1.):
        raise ValueError('synthetic sign must be +1 or -1')
    if fault not in (None, 'missing_frame', 'ambiguous_frame', 'invalid_body'):
        raise ValueError('unknown synthetic fault')
    model = ifcopenshell.file(schema='IFC2X3')
    unit = 1. if millimetres else .001

    def point(xyz):
        return model.createIfcCartesianPoint(tuple(float(v) * unit for v in xyz))

    def axis(xyz):
        return model.createIfcAxis2Placement3D(point(xyz))

    person = model.createIfcPerson(FamilyName='Offline')
    organisation = model.createIfcOrganization(Name='Public synthetic Brep family')
    app = model.createIfcApplication(organisation, '1', 'Synthetic fixture', 'test')
    owner = model.createIfcOwnerHistory(
        model.createIfcPersonAndOrganization(person, organisation), app,
        None, 'ADDED', None, None, None, 1,
    )
    context = model.createIfcGeometricRepresentationContext(
        None, 'Model', 3, 1e-5, axis((0, 0, 0)), None,
    )
    units = model.createIfcUnitAssignment([
        model.createIfcSIUnit(None, 'LENGTHUNIT', 'MILLI' if millimetres else None, 'METRE'),
    ])
    project = model.createIfcProject(
        ifcopenshell.guid.new(), owner, 'Public synthetic scene',
        None, None, None, None, [context], units,
    )

    def root(cls, **kwargs):
        return model.create_entity(cls, GlobalId=ifcopenshell.guid.new(),
                                   OwnerHistory=owner, **kwargs)

    def box(x0, x1, y0, y1, z0, z1):
        position = model.createIfcAxis2Placement2D(
            model.createIfcCartesianPoint(((x0 + x1) / 2 * unit, (y0 + y1) / 2 * unit)), None,
        )
        profile = model.createIfcRectangleProfileDef(
            'AREA', None, position, (x1 - x0) * unit, (y1 - y0) * unit,
        )
        return model.createIfcExtrudedAreaSolid(
            profile, axis((0, 0, z0)), model.createIfcDirection((0., 0., 1.)),
            (z1 - z0) * unit,
        )

    def representation(product, items, kind='SweptSolid'):
        body = model.createIfcShapeRepresentation(context, 'Body', kind, items)
        product.Representation = model.createIfcProductDefinitionShape(None, None, [body])
        return body

    def solid(vertices, faces):
        points = [point(v) for v in vertices]
        shell_faces = [model.createIfcFace([
            model.createIfcFaceOuterBound(
                model.createIfcPolyLoop([points[index] for index in face]), True,
            ),
        ]) for face in faces]
        return model.createIfcFacetedBrep(model.createIfcClosedShell(shell_faces))

    def brep_box(x0, x1, y0, y1, z0, z1):
        vertices = [(x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0),
                    (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)]
        return solid(vertices, [(3,2,1,0), (4,5,6,7), (0,1,5,4),
                                (1,2,6,5), (2,3,7,6), (3,0,4,7)])

    def frame(y0, y1, *, x0=0., x1=900.):
        # A connected rectangular frame with a real central aperture. Every
        # face is an outward oriented quad, not overlapping solid bar boxes.
        outer = [(x0,0.), (x1,0.), (x1,2100.), (x0,2100.)]
        inner = [(x0+40.,40.), (x1-40.,40.), (x1-40.,2060.), (x0+40.,2060.)]
        vertices = [(x,y,z) for y in (y0,y1) for x,z in [*outer,*inner]]
        faces = []
        for i in range(4):
            j = (i + 1) % 4
            faces.extend([
                (i,j,4+j,4+i), (8+i,12+i,12+j,8+j),
                (j,i,8+i,8+j), (4+i,4+j,12+j,12+i),
            ])
        return solid(vertices, faces)

    def finish(item, name, colour):
        rgb = model.createIfcColourRgb(name, *colour)
        shading = model.createIfcSurfaceStyleShading(rgb)
        style = model.createIfcSurfaceStyle(name, 'BOTH', [shading])
        assignment = model.createIfcPresentationStyleAssignment([style])
        model.createIfcStyledItem(item, [assignment], name)

    storey = root('IfcBuildingStorey', Name='Ground', CompositionType='ELEMENT', Elevation=0.)
    storey.ObjectPlacement = local_placement(model, relative_to=None, location=(0.,0.,0.))
    root('IfcRelAggregates', RelatingObject=project, RelatedObjects=[storey])

    def wall_and_opening(name, thickness, origin, degrees):
        wall = root('IfcWall', Name=name)
        wall.ObjectPlacement = local_placement(
            model, relative_to=storey.ObjectPlacement,
            location=tuple(v*unit for v in origin),
            ref_direction=(math.cos(math.radians(degrees)), math.sin(math.radians(degrees)), 0.),
        )
        representation(wall, [box(0,6000,0,thickness,0,3000)])
        wall.Representation.Representations = [*wall.Representation.Representations,
            model.createIfcShapeRepresentation(context, 'Axis', 'Curve2D', [
                model.createIfcPolyline([model.createIfcCartesianPoint((0.,0.)),
                                         model.createIfcCartesianPoint((6000*unit,0.))]),
            ])]
        opening = root('IfcOpeningElement', Name=f'{name} opening')
        opening.ObjectPlacement = local_placement(
            model, relative_to=wall.ObjectPlacement, location=(500*unit,0.,0.),
        )
        representation(opening, [box(0,900,0,thickness,0,2100)])
        root('IfcRelVoidsElement', RelatingBuildingElement=wall, RelatedOpeningElement=opening)
        return wall, opening

    target_wall, target = wall_and_opening(
        'Target public host', float(target_thickness_mm), (1000.,10000.,0.), angle,
    )
    reference_wall, reference_opening = wall_and_opening(
        'Reference public host', 150., (1000.,2000.,0.), 0.,
    )
    pieces = [frame(0.,50., x0=40. if fault=='missing_frame' else 0.,
                    x1=860. if fault=='missing_frame' else 900.),
              brep_box(40.,860.,25.,55.,40.,2060.),
              brep_box(700.,800.,55.,130.,900.,1000.)]
    if fault == 'ambiguous_frame':
        pieces.append(frame(10.,50.))
    if fault == 'invalid_body':
        pieces.append(box(200.,300.,10.,20.,200.,300.))
    for index, item in enumerate(pieces):
        finish(item, f'Public part finish {index}',
               [(0.7,0.2,0.1), (0.1,0.6,0.3), (0.1,0.2,0.8), (0.6,0.4,0.2)][index])
    door_style = root('IfcDoorStyle', Name='Public no-map door style',
                      OperationType='SINGLE_SWING_LEFT', ConstructionType='WOOD',
                      ParameterTakesPrecedence=False, Sizeable=False)
    reference = root('IfcDoor', Name='Public retained complete Brep door',
                     OverallWidth=900*unit, OverallHeight=2100*unit)
    representation(reference, pieces, 'Brep')
    reference.ObjectPlacement = local_placement(
        model, relative_to=reference_opening.ObjectPlacement,
        location=((0. if sign>0 else 900.)*unit, (100. if sign>0 else 50.)*unit, 0.),
        ref_direction=(sign,0.,0.),
    )
    root('IfcRelDefinesByType', RelatingType=door_style, RelatedObjects=[reference])
    root('IfcRelFillsElement', RelatingOpeningElement=reference_opening, RelatedBuildingElement=reference)
    root('IfcRelContainedInSpatialStructure', RelatingStructure=storey,
         RelatedElements=[target_wall,reference_wall,reference])
    return model, target, reference, unit


def _body(product):
    bodies = [r for r in product.Representation.Representations if r.RepresentationIdentifier=='Body']
    assert len(bodies)==1
    return bodies[0]


def _type(reference):
    types = [r.RelatingType for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType')]
    assert len(types)==1
    return types[0]


def _reference_signature(model, reference):
    entities = list(model.traverse(_body(reference)))
    for item in _body(reference).Items:
        for styled in item.StyledByItem:
            entities.extend(model.traverse(styled))
    return {
        'style': _type(reference).to_string(),
        'reference': reference.to_string(),
        'body_and_finishes': {entity.id(): entity.to_string() for entity in entities},
    }


def mapped_candidate(model, reference):
    """Explicit synthetic identity occurrence map, leaving Style maps empty."""
    body = _body(reference)
    mapped_body = model.createIfcShapeRepresentation(
        body.ContextOfItems, body.RepresentationIdentifier, body.RepresentationType, body.Items)
    origin = model.createIfcCartesianPoint((0.,0.,0.))
    source = model.createIfcRepresentationMap(model.createIfcAxis2Placement3D(origin), mapped_body)
    transform = model.createIfcCartesianTransformationOperator3D(None,None,origin,1.,None)
    item = model.createIfcMappedItem(source, transform)
    representation = model.createIfcShapeRepresentation(body.ContextOfItems, 'Body', 'MappedRepresentation', [item])
    candidate = model.createIfcDoor(
        ifcopenshell.guid.new(), reference.OwnerHistory, 'New public synthetic candidate',
        None, None, None, model.createIfcProductDefinitionShape(None,None,[representation]),
        None, reference.OverallHeight, reference.OverallWidth,
    )
    relation = next(r for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    relation.RelatedObjects = [*relation.RelatedObjects, candidate]
    return candidate


def assert_complete_public_reuse(model, candidate, reference, original_signature):
    """Exact public Body/style provenance; an equal AABB alone is inadequate."""
    assert not _type(reference).RepresentationMaps
    assert _type(candidate)==_type(reference)
    assert _reference_signature(model, reference)==original_signature
    representations = candidate.Representation.Representations
    assert len(representations)==1 and representations[0].RepresentationIdentifier=='Body'
    items = representations[0].Items
    assert len(items)==1 and items[0].is_a('IfcMappedItem')
    mapped = items[0].MappingSource.MappedRepresentation
    source = _body(reference)
    assert mapped!=source
    assert mapped.ContextOfItems==source.ContextOfItems
    assert mapped.RepresentationIdentifier==source.RepresentationIdentifier
    assert mapped.RepresentationType==source.RepresentationType
    assert mapped.Items==source.Items
    assert not mapped.OfProductRepresentation and len(mapped.RepresentationMap)==1
    assert len(_body(reference).Items)==3
    assert all(item.is_a('IfcFacetedBrep') for item in _body(reference).Items)
    assert len({item.StyledByItem[0].Name for item in _body(reference).Items})==3
    matrix = ifcopenshell.util.placement.get_mappeditem_transformation(items[0])
    assert list(matrix.flat)==pytest.approx([1.,0.,0.,0., 0.,1.,0.,0., 0.,0.,1.,0., 0.,0.,0.,1.], abs=1e-10)


def assert_authored_installation(candidate, opening, *, sign, thickness):
    bounds = product_geometry_bounds_in_host_mm(candidate, opening)
    assert bounds['x']==pytest.approx([0.,900.], abs=1e-5)
    assert bounds['z']==pytest.approx([0.,2100.], abs=1e-5)
    expected_y = [thickness-50.,thickness+80.] if sign>0 else [-80.,50.]
    assert bounds['y']==pytest.approx(expected_y, abs=1e-5)
    # The complete Body centre is 15 mm outside the independently witnessed
    # frame-flush wall face. Hardware is never used to select the wall face.
    face = thickness if sign>0 else 0.
    assert sum(bounds['y'])/2-face==pytest.approx(sign*15., abs=1e-5)


@pytest.mark.parametrize('millimetres,angle,sign,thickness', [
    (False,0.,1.,150.), (False,90.,-1.,150.), (True,180.,1.,150.),
    (True,0.,-1.,150.), (False,180.,1.,100.), (False,90.,-1.,100.),
    (True,90.,1.,100.), (True,180.,-1.,100.),
])
def test_direct_public_body_anchor_preserves_all_parts_and_authored_face(millimetres,angle,sign,thickness):
    model,opening,reference,_ = brep_scene(
        millimetres=millimetres, angle=angle, sign=sign, target_thickness_mm=thickness,
    )
    signature = _reference_signature(model, reference)
    anchor = geometry.public_door_installation_anchor(reference, allow_wall_face_adaptation=True)
    candidate = mapped_candidate(model, reference)
    selected = geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)
    install(model,opening,candidate,selected)
    assert selected['ref_direction'][0]==sign
    assert_complete_public_reuse(model,candidate,reference,signature)
    assert_authored_installation(candidate,opening,sign=sign,thickness=thickness)
    assert geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']


def test_same_thickness_direct_reuse_does_not_require_adaptation_permission():
    model,opening,reference,_ = brep_scene()
    anchor = geometry.public_door_installation_anchor(reference)
    candidate = mapped_candidate(model,reference)
    install(model,opening,candidate,geometry.select_door_placement_in_opening(
        candidate,opening,installation_anchor=anchor,
    ))
    assert_authored_installation(candidate,opening,sign=1.,thickness=150.)


def test_cross_thickness_without_explicit_permission_is_rejected():
    model,opening,reference,_ = brep_scene(target_thickness_mm=100.)
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_'):
        anchor = geometry.public_door_installation_anchor(reference)
        geometry.select_door_placement_in_opening(mapped_candidate(model,reference),opening,installation_anchor=anchor)


@pytest.mark.parametrize('fault',['missing_frame','ambiguous_frame','invalid_body'])
def test_cross_thickness_requires_one_complete_public_frame_witness(fault):
    model,opening,reference,_ = brep_scene(target_thickness_mm=100.,fault=fault)
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_'):
        anchor = geometry.public_door_installation_anchor(reference,allow_wall_face_adaptation=True)
        geometry.select_door_placement_in_opening(mapped_candidate(model,reference),opening,installation_anchor=anchor)


def test_target_thinner_than_the_complete_frame_is_not_an_adaptation():
    model,opening,reference,_ = brep_scene(target_thickness_mm=25.)
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_'):
        anchor = geometry.public_door_installation_anchor(reference,allow_wall_face_adaptation=True)
        geometry.select_door_placement_in_opening(mapped_candidate(model,reference),opening,installation_anchor=anchor)


@pytest.mark.parametrize('fault',['width','height','body_source','map_scale','map_translation','map_origin','anchor'])
def test_exact_body_dimensions_mapping_and_anchor_cannot_be_rewritten(fault):
    from ifcopenshell.util.element import copy_deep
    model,opening,reference,unit = brep_scene()
    anchor = geometry.public_door_installation_anchor(reference,allow_wall_face_adaptation=True)
    candidate = mapped_candidate(model,reference)
    item = _body(candidate).Items[0]
    if fault=='width': candidate.OverallWidth += 10*unit
    if fault=='height': candidate.OverallHeight += 10*unit
    if fault=='body_source':
        item.MappingSource.MappedRepresentation = copy_deep(
            model,_body(reference),exclude=('IfcGeometricRepresentationContext',),
        )
    if fault=='map_scale': item.MappingTarget.Scale = 1.01
    if fault=='map_translation':
        item.MappingTarget.LocalOrigin = model.createIfcCartesianPoint((0.,10*unit,0.))
    if fault=='map_origin':
        item.MappingSource.MappingOrigin.Location = model.createIfcCartesianPoint((0.,10*unit,0.))
    if fault=='anchor':
        anchor = deepcopy(anchor)
        anchor['normal_center_offset_mm'] += 30.
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_'):
        geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)


@pytest.mark.parametrize('delta',[5.01,-30.])
def test_reference_aware_l1_rejects_body_displacement_after_adaptation(delta):
    model,opening,reference,unit = brep_scene(target_thickness_mm=100.)
    anchor = geometry.public_door_installation_anchor(reference,allow_wall_face_adaptation=True)
    candidate = mapped_candidate(model,reference)
    selected = geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)
    selected['location'] = tuple(v+(delta*unit if i==1 else 0.) for i,v in enumerate(selected['location']))
    install(model,opening,candidate,selected)
    assert not geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']


def _start(tmp_path,model,request_text,*,provider=None):
    source = tmp_path/'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    provider = provider or PublicOnlyProvider()
    result = RepairAPI(tmp_path/'run',provider=provider,scene_grounding=True).start(source,request_text)
    assert source.read_bytes()==before
    return result,tmp_path/'run'/result.run_directory,provider


@pytest.mark.parametrize('millimetres,angle,sign,thickness',[
    (False,0.,1.,150.), (True,90.,-1.,150.),
    (False,180.,-1.,100.), (True,37.,1.,100.),
])
def test_direct_body_public_api_result_has_valid_ifc_representation_ownership(
    tmp_path,millimetres,angle,sign,thickness,
):
    from scripts.ifc_repair.repair_comparison.inspection import native_validation
    model,_,reference,_ = brep_scene(millimetres=millimetres,angle=angle,
                                    sign=sign,target_thickness_mm=thickness)
    assert native_validation(model)['passed']
    original = _reference_signature(model,reference)
    result,run,_ = _start(tmp_path,model,REQUEST)
    assert result.successful_artifact_publishable, result.to_dict()
    output = ifcopenshell.open(str(run/result.artifacts['successful_ifc']))
    validation = native_validation(output)
    assert validation['passed'], validation
    assert _reference_signature(output,output.by_guid(reference.GlobalId))==original


@pytest.mark.parametrize('request_text,millimetres,angle,sign,thickness',[
    (REQUEST_NO_ADAPTATION,False,0.,1.,150.),
    (REQUEST,False,90.,1.,100.),
    (REQUEST_ZH,True,180.,-1.,100.),
])
def test_public_fake_api_reopens_full_styled_body_and_keeps_source(tmp_path,request_text,millimetres,angle,sign,thickness):
    model,opening,reference,_ = brep_scene(
        millimetres=millimetres,angle=angle,sign=sign,target_thickness_mm=thickness,
    )
    signature = _reference_signature(model,reference)
    result,run,provider = _start(tmp_path,model,request_text)
    assert result.status=='succeeded',result.to_dict()
    output = ifcopenshell.open(str(run/result.artifacts['successful_ifc']))
    retained = output.by_guid(reference.GlobalId)
    created = next(d for d in output.by_type('IfcDoor') if d.GlobalId!=reference.GlobalId)
    assert_complete_public_reuse(output,created,retained,signature)
    assert_authored_installation(created,output.by_guid(opening.GlobalId),sign=sign,thickness=thickness)
    anchor = geometry.public_door_installation_anchor(retained,allow_wall_face_adaptation=thickness!=150.)
    assert geometry.measure_door_opening_alignment(created,output.by_guid(opening.GlobalId),installation_anchor=anchor)['valid']
    assert all('private' not in str(call['state']) for call in provider.calls)
    manifest = json.loads((run/result.artifacts['manifest']).read_text(encoding='utf8'))
    evidence_path = next(a['path'] for a in manifest['artifacts'] if a['role']=='public_evidence')
    application = json.loads((run/evidence_path).read_text(encoding='utf8'))['evidence']['application']
    assert application['valid'] and application['published']


def test_public_api_cross_thickness_without_authorization_never_publishes(tmp_path):
    model,*_ = brep_scene(target_thickness_mm=100.)
    result,_,_ = _start(tmp_path,model,REQUEST_NO_ADAPTATION)
    assert result.status!='succeeded'
    assert not result.successful_artifact_publishable and 'successful_ifc' not in result.artifacts


@pytest.mark.parametrize('request_text',[
    REQUEST_NO_ADAPTATION+' Do not adapt the retained wall face installation to wall thickness.',
    '按公开参照门补齐空洞口，门宽900毫米、高2100毫米。不得调整门框相对墙面的位置，不允许适配墙厚。',
])
def test_negated_wall_face_adaptation_does_not_authorize_a_different_thickness(tmp_path,request_text):
    model,*_ = brep_scene(target_thickness_mm=100.)
    result,_,_ = _start(tmp_path,model,request_text)
    assert result.status!='succeeded'
    assert not result.successful_artifact_publishable and 'successful_ifc' not in result.artifacts


@pytest.mark.parametrize('fault',['unoffered','stage2_anchor'])
def test_public_api_cannot_replace_the_offered_reference_or_internal_anchor(tmp_path,fault):
    from text2ifc_agent.providers import ProviderOutput

    class TamperingProvider(PublicOnlyProvider):
        def generate_candidate(self,**kwargs):
            result = super().generate_candidate(**kwargs)
            value = json.loads(result.text)
            if fault=='stage2_anchor' and '## Immutable bindings' in kwargs['prompt']:
                value['operations'][0]['parameters'].setdefault('door_installation_anchor',{})['reference_global_id']='unoffered'
            return ProviderOutput(text=json.dumps(value),metadata=result.metadata)

    model,*_ = brep_scene(target_thickness_mm=100.)
    result,_,_ = _start(tmp_path,model,REQUEST,provider=TamperingProvider(unoffered=fault=='unoffered'))
    assert result.status!='succeeded'
    assert not result.successful_artifact_publishable and 'successful_ifc' not in result.artifacts


def test_direct_body_and_authorized_face_adaptation_survive_restart(tmp_path):
    class CrashAfterIntent(RepairAPI):
        def _resolve_and_finish(self,*args,**kwargs):
            raise RuntimeError('offline crash after committed intent')

    model,opening,reference,_ = brep_scene(millimetres=True,angle=90.,sign=-1.,target_thickness_mm=100.)
    signature = _reference_signature(model,reference)
    source = tmp_path/'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    provider = PublicOnlyProvider()
    with pytest.raises(RuntimeError,match='offline crash'):
        CrashAfterIntent(tmp_path/'run',provider=provider,scene_grounding=True).start(source,REQUEST_ZH)
    run = next((tmp_path/'run/runs').iterdir())
    context = json.loads((run/'api-context.json').read_text(encoding='utf8'))
    assert context['installation_references']['offline-repair-0']['reference_global_id']==reference.GlobalId
    result = RepairAPI(tmp_path/'run',provider=provider).resume(run.name)
    assert result.status=='succeeded',result.to_dict()
    output = ifcopenshell.open(str(run/result.artifacts['successful_ifc']))
    created = next(d for d in output.by_type('IfcDoor') if d.GlobalId!=reference.GlobalId)
    assert_complete_public_reuse(output,created,output.by_guid(reference.GlobalId),signature)
    assert_authored_installation(created,output.by_guid(opening.GlobalId),sign=-1.,thickness=100.)
    assert source.read_bytes()==before


def test_second_direct_body_l1_failure_rolls_back_whole_public_batch(tmp_path,monkeypatch):
    from ifcopenshell.util.element import copy_deep
    from text2ifc_ifc_repair.operations import door as door_operation

    model,opening,reference,unit = brep_scene(target_thickness_mm=100.)
    wall = opening.VoidsElements[0].RelatingBuildingElement
    extra = model.createIfcOpeningElement(ifcopenshell.guid.new(),opening.OwnerHistory,'Second empty opening')
    extra.ObjectPlacement = local_placement(model,relative_to=wall.ObjectPlacement,location=(2000*unit,0.,0.))
    extra.Representation = copy_deep(model,opening.Representation,exclude=('IfcGeometricRepresentationContext',))
    model.createIfcRelVoidsElement(ifcopenshell.guid.new(),opening.OwnerHistory,None,None,wall,extra)
    signature = _reference_signature(model,reference)
    original = door_operation._create_door
    calls = []

    def displace_second(**kwargs):
        changes = original(**kwargs)
        calls.append(changes)
        if len(calls)==2:
            candidate = kwargs['model'].by_guid(next(c['global_id'] for c in changes['created'] if c['role']=='door'))
            point = candidate.ObjectPlacement.RelativePlacement.Location
            coordinates = list(point.Coordinates)
            coordinates[1] += 30*unit
            point.Coordinates = coordinates
        return changes

    monkeypatch.setattr(door_operation,'_create_door',displace_second)
    result,_,_ = _start(tmp_path,model,REQUEST.replace('the empty opening','both empty openings'),provider=PublicOnlyProvider(batch=True))
    assert len(calls)==2
    assert result.status=='application_failed' and 'successful_ifc' not in result.artifacts
    assert not result.successful_artifact_publishable
    assert not list((tmp_path/'run').rglob('application-candidate.ifc'))
    assert not list((tmp_path/'run').rglob('repaired.ifc'))
    assert _reference_signature(model,reference)==signature
