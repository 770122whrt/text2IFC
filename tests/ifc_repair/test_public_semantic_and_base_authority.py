"""Public-authority precedence and nominal/mesh base regression family."""
from copy import deepcopy
import json

import ifcopenshell
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair import door_geometry as geometry
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm
from tests.ifc_repair.test_door_installation_anchor import scene as door_scene, install
from tests.ifc_repair.test_window_installation_anchor import scene as window_scene, PublicWindowProvider


@pytest.mark.parametrize('offset,angle,millimetres',[(75.,0.,False),(100.,90.,True),(-40.,180.,False)])
def test_mapped_geometry_base_is_distinct_from_nominal_base(offset,angle,millimetres):
    model,opening,reference,create,unit=door_scene(angle=angle,millimetres=millimetres)
    style=next(r.RelatingType for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    for item in style.RepresentationMaps[0].MappedRepresentation.Items:
        point=item.Position.Location
        point.Coordinates=(*point.Coordinates[:2],point.Coordinates[2]+offset*unit)
    anchor=geometry.public_door_installation_anchor(reference)
    candidate=create('Candidate reuses the public mapped frame')
    placement=geometry.select_door_placement_in_opening(candidate,opening,installation_anchor=anchor)
    install(model,opening,candidate,placement)
    assert candidate.ObjectPlacement.RelativePlacement.Location.Coordinates[2]==pytest.approx(0.)
    actual=product_geometry_bounds_in_host_mm(candidate,opening)
    assert actual['z'][0]==pytest.approx(offset,abs=.1)
    assert geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']
    point=candidate.ObjectPlacement.RelativePlacement.Location
    point.Coordinates=(*point.Coordinates[:2],point.Coordinates[2]+5.01*unit)
    assert not geometry.measure_door_opening_alignment(candidate,opening,installation_anchor=anchor)['valid']


def test_public_anchor_rejects_shifted_nominal_instance_base():
    model,opening,reference,create,unit=door_scene()
    point=reference.ObjectPlacement.RelativePlacement.Location
    point.Coordinates=(*point.Coordinates[:2],100*unit)
    with pytest.raises(ValueError,match='DOOR_INSTALLATION_REFERENCE_ALIGNMENT_UNSUPPORTED'):
        geometry.public_door_installation_anchor(reference)


def conflicting_windows(*,host_external=True):
    model,wall,opening,reference,create,unit=window_scene()
    relation=next(r for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    style=relation.RelatingType
    style.HasPropertySets=None
    def external(product,kind,value):
        prop=model.createIfcPropertySingleValue('IsExternal',None,model.createIfcBoolean(value),None)
        pset=model.createIfcPropertySet(ifcopenshell.guid.new(),reference.OwnerHistory,f'Pset_{kind}Common',None,[prop])
        model.createIfcRelDefinesByProperties(ifcopenshell.guid.new(),reference.OwnerHistory,None,None,[product],pset)
    external(reference,'Window',True)
    peers=[]
    for index in range(2):
        peer=create(f'Other public same-Type window {index}')
        # IFC2X3 requires one product per IfcLocalPlacement; the axes and
        # parent may be shared without sharing the occurrence placement.
        peer.ObjectPlacement=model.createIfcLocalPlacement(
            reference.ObjectPlacement.PlacementRelTo,
            reference.ObjectPlacement.RelativePlacement)
        external(peer,'Window',False)
        peers.append(peer)
    relation.RelatedObjects=[reference,*peers]
    containment=wall.ContainedInStructure[0]
    containment.RelatedElements=[wall,reference,*peers]
    if host_external is not None:
        external(wall,'Wall',host_external)
    return model,wall,reference


class ExactPublicReferenceProvider(PublicWindowProvider):
    def __init__(self,reference_id,*,explicit=None):
        super().__init__(public_reference_id=reference_id)
        self.reference_id=reference_id
        self.explicit=explicit

    def generate_candidate(self,**kwargs):
        from text2ifc_agent.providers import ProviderOutput
        # Select only the exact retained identity in the actual offered page;
        # neither the page nor the production query result is rewritten.
        result=super().generate_candidate(**kwargs)
        value=json.loads(result.text)
        if value.get('kind')=='intent':
            assert value['bindings'][0]['reference_id']==self.reference_id
            if self.explicit is not None:
                op=value['intent']['operations'][0]
                from text2ifc_ifc_repair.property_intent import ExactPropertyIntent
                from text2ifc_ifc_repair.repair_intent import PublicProvenance
                op['property_intents'].append(ExactPropertyIntent(
                    set_name='Pset_WindowCommon',property_name='IsExternal',value=self.explicit,
                    requested_value_type='IfcBoolean',requested_unit=None,scope='occurrence_direct',
                    intent_kind='exact_property',
                    source=PublicProvenance.from_dict(op['provenance'][0])).to_dict())
            return ProviderOutput(text=json.dumps(value),metadata=result.metadata)
        return result


@pytest.mark.parametrize('host_external,explicit,expected',[(True,None,True),(False,None,False),(None,True,True),(True,False,False)])
def test_stronger_public_authority_precedes_conflicting_type_peers(tmp_path,host_external,explicit,expected):
    model,wall,reference=conflicting_windows(host_external=host_external)
    source=tmp_path/'public.ifc'
    model.write(str(source))
    before=source.read_bytes()
    provider=ExactPublicReferenceProvider(reference.GlobalId,explicit=explicit)
    result=RepairAPI(tmp_path/'native',provider=provider,scene_grounding=True).start(source,
        'Add the requested window using the exact retained frame and installation; preserve other windows. Exterior status is established by the host or explicit request.')
    assert result.status=='succeeded',result.to_dict()
    assert source.read_bytes()==before
    repaired=ifcopenshell.open(str(tmp_path/'native'/result.run_directory/result.artifacts['successful_ifc']))
    new=next(w for w in repaired.by_type('IfcWindow') if w.GlobalId not in {w.GlobalId for w in model.by_type('IfcWindow')})
    from ifcopenshell.util.element import get_psets
    assert get_psets(new)['Pset_WindowCommon']['IsExternal'] is expected
    manifest=json.loads((tmp_path/'native'/result.run_directory/'semantic-manifest.json').read_text(encoding='utf8'))
    assignment=next(a for a in manifest['assignments'] if a['fact_key']=='pset:Pset_WindowCommon.IsExternal')
    assert assignment['source_ref']==('request:/text' if explicit is not None else 'current-host:'+wall.GlobalId)


def test_conflicting_type_peers_without_stronger_authority_still_fail_closed(tmp_path):
    model,wall,reference=conflicting_windows(host_external=None)
    source=tmp_path/'public.ifc'
    model.write(str(source))
    before=source.read_bytes()
    result=RepairAPI(tmp_path/'native',provider=ExactPublicReferenceProvider(reference.GlobalId),scene_grounding=True).start(source,
        'Add a window with the retained public frame. The host does not establish exterior status.')
    assert result.reason_code=='AUTHORIZED_TYPE_COHORT_CONFLICT',result.to_dict()
    assert not result.successful_artifact_publishable and 'successful_ifc' not in result.artifacts
    assert source.read_bytes()==before


def test_mapped_same_thickness_can_preserve_installation_when_request_mentions_wall_face(tmp_path):
    from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider
    model,opening,reference,_,unit=door_scene(angle=90.)
    source=tmp_path/'public.ifc'
    model.write(str(source))
    before=source.read_bytes()
    result=RepairAPI(tmp_path/'native',provider=PublicOnlyProvider(),scene_grounding=True).start(source,
        'Fill the empty opening using the retained door. Keep its installation relative to the target wall face and adapt to wall thickness.')
    assert result.status=='succeeded',result.to_dict()
    assert source.read_bytes()==before
    output=ifcopenshell.open(str(tmp_path/'native'/result.run_directory/result.artifacts['successful_ifc']))
    new=next(d for d in output.by_type('IfcDoor') if d.GlobalId!=reference.GlobalId)
    assert new.ObjectPlacement.RelativePlacement.Location.Coordinates[1]/unit==pytest.approx(75.)
