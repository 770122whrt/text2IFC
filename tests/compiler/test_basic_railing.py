"""Bounded single-material picket railing; actual serialized IFC geometry."""
from copy import deepcopy

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import pytest

from text2ifc_compiler import compile_document


def document(*, rise=0, yaw=0, elevation=0):
    entities=[]
    for identity,cls,parent,z in [("project","IfcProject",None,0),
            ("site","IfcSite","project",0),("building","IfcBuilding","site",0),
            ("level","IfcBuildingStorey","building",elevation)]:
        attr={"Name":identity}
        if parent:attr["ObjectPlacement"]={"relative_to":parent,"origin":[0,0,z],"axis":[0,0,1],"ref_direction":[1,0,0]}
        if cls=="IfcBuildingStorey":attr["Elevation"]=z
        entities.append({"id":identity,"ifc_class":cls,"attributes":attr,"property_sets":{},"provenance":{"source":"test"}})
    entities.append({"id":"guard","ifc_class":"IfcRailing","attributes":{
        "Name":"guard", "ObjectPlacement":{"relative_to":"level","origin":[1000,2000,0],
            "axis":[0,0,1],"ref_direction":[1,0,0] if yaw==0 else [0,1,0]},
        "Representation":{"kind":"basic_railing","template_id":"metal-picket",
            "template_version":"text2ifc/basic-railing/1.0","length":4000,"height":1100,"depth":40,"rise":rise}},
        "materials":[{"kind":"single_material","name":"Steel"}],
        "appearance":{"color":[.2,.24,.25],"transparency":0},"property_sets":{},"provenance":{"source":"test"}})
    return {"schema_version":"bim-json/2.3","ifc_schema":"IFC2X3","units":{"length":"MILLIMETRE"},
        "entities":entities,"relationships":[],"provenance":{"source":"test"}}


@pytest.mark.parametrize("rise,yaw,elevation", [(0,0,0),(0,90,4200),(1800,0,0),(1800,90,4200),(-1800,0,4200)])
def test_serialized_railing_has_real_pickets_and_handrails_inside_frozen_envelope(tmp_path,rise,yaw,elevation):
    source=document(rise=rise,yaw=yaw,elevation=elevation);before=deepcopy(source)
    result=compile_document(source,tmp_path/'railing.ifc')
    assert result.success,(result.input_issues,result.ifc_issues)
    model=ifcopenshell.open(str(result.output_path));guard=model.by_type('IfcRailing')[0]
    shape=guard.Representation.Representations[0]
    roles={a.Name: list(a.ShapeRepresentations[0].Items) for a in guard.Representation.HasShapeAspects}
    assert set(roles)=={'Posts','Pickets','TopRail','BottomRail'}
    assert len(roles['Posts'])==5 and len(roles['TopRail'])==1 and len(roles['BottomRail'])==4
    assert len(roles['Pickets'])==32
    assert len(shape.Items)==42
    settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
    mesh_shape=ifcopenshell.geom.create_shape(settings,guard)
    mesh=mesh_shape.geometry
    bbox=[[min(mesh.verts[i::3]),max(mesh.verts[i::3])] for i in range(3)]
    expected=([1,5],[1.98,2.02]) if yaw==0 else ([.98,1.02],[2,6])
    assert bbox[0]==pytest.approx(expected[0],abs=1e-6)
    assert bbox[1]==pytest.approx(expected[1],abs=1e-6)
    assert bbox[2]==pytest.approx([(elevation+min(0,rise))/1000,(elevation+1100+max(0,rise))/1000],abs=1e-6)
    # The empty spaces between rods must exist in actual solids, not merely names.
    assert all(item.SweptArea.is_a('IfcArbitraryClosedProfileDef') for item in shape.Items)
    assert ifcopenshell.util.element.get_material(guard).Name=='Steel'
    assert source==before


@pytest.mark.parametrize("patch", [
    {'height':0},{'length':100},{'depth':1},{'rise':5000},{'length':float('nan')},
    {'parameters':{'max_clear_gap':0}}, {'parameters':{'picket_width':True}},
    {'parameters':{'invented':5}},{'template_version':'unregistered'},
])
def test_invalid_railing_parameters_do_not_replace_an_existing_output(tmp_path,patch):
    source=document();source['entities'][-1]['attributes']['Representation'].update(patch)
    output=tmp_path/'preserved.ifc';output.write_bytes(b'original output')
    result=compile_document(source,output)
    assert not result.success
    assert output.read_bytes()==b'original output'


def test_legacy_representation_contract_does_not_acquire_new_railing_meaning(tmp_path):
    source=document();source['schema_version']='bim-json/2.2'
    result=compile_document(source,tmp_path/'legacy.ifc')
    assert not result.success and not (tmp_path/'legacy.ifc').exists()


def test_railing_template_cannot_be_attached_to_a_column(tmp_path):
    source=document();source['entities'][-1]['ifc_class']='IfcColumn'
    assert not compile_document(source,tmp_path/'wrong-family.ifc').success


@pytest.mark.parametrize('mutation',['remove_picket','solid_panel','wrong_provenance','move'])
def test_reopened_verifier_rejects_geometry_and_provenance_tampering(tmp_path,mutation):
    from text2ifc_compiler.basic_railing import verify_basic_railing
    source=document();result=compile_document(source,tmp_path/'original.ifc')
    assert result.success
    model=ifcopenshell.open(str(result.output_path));guard=model.by_type('IfcRailing')[0]
    shape=guard.Representation.Representations[0]
    aspect=next(a for a in guard.Representation.HasShapeAspects if a.Name=='Pickets')
    item=aspect.ShapeRepresentations[0].Items[0]
    if mutation=='remove_picket':shape.Items=[i for i in shape.Items if i.id()!=item.id()]
    elif mutation=='solid_panel':
        # Same named part, deliberately fill its horizontal gap with extra mass.
        points=item.SweptArea.OuterCurve.Points
        points[1].Coordinates=(float(points[1].Coordinates[0])+80.,float(points[1].Coordinates[1]))
    elif mutation=='wrong_provenance':
        from ifcopenshell.api.pset import edit_pset
        pset_id=ifcopenshell.util.element.get_psets(guard)['Pset_text2IFCBasicRailing']['id']
        edit_pset(model,pset=model.by_id(pset_id),properties={'FireRating':'invented'})
    else:guard.ObjectPlacement.RelativePlacement.Location.Coordinates=(1200.,2000.,0.)
    modified=tmp_path/'modified.ifc';model.write(str(modified))
    assert verify_basic_railing(ifcopenshell.open(str(modified)),source)


@pytest.mark.parametrize('attack',['none','wrong_parameters','missing_picket'])
def test_frozen_template_request_is_verified_from_actual_ifc(tmp_path,attack):
    from text2ifc_compiler.semantic_verification import verify_semantic_expectations
    source=document(rise=1800)
    result=compile_document(source,tmp_path/'request.ifc')
    assert result.success
    model=ifcopenshell.open(str(result.output_path))
    template={'template_id':'metal-picket','template_version':'text2ifc/basic-railing/1.0'}
    if attack=='wrong_parameters':template['parameters']={'max_clear_gap':80}
    if attack=='missing_picket':
        guard=model.by_type('IfcRailing')[0];shape=guard.Representation.Representations[0]
        shape.Items=shape.Items[:-1]
    issues=verify_semantic_expectations(model,[{'entity_id':'guard','kind':'template','value':template}])
    assert bool(issues)==(attack!='none'),issues
