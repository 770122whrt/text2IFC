"""S0/S1 frozen deterministic family; not live-Provider capability evidence."""
import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import numpy as np
import pytest

from text2ifc_compiler.compiler import compile_document
from text2ifc_contract.validation_v2 import validate_v2_document


def position(origin=(0, 0, 0), axis=(0, 0, 1), ref=(1, 0, 0)):
    return dict(origin=list(origin), axis=list(axis), ref_direction=list(ref))


def components():
    return {
        "kind": "component_geometry", "geometry_version": "text2ifc/components/1.0",
        "definitions": [
            {"id": "frame-solid", "profile": {"kind": "polygon", "points": [[0,0],[850,0],[850,1100],[0,1100],[0,0]],
                "holes": [[[40,40],[40,1060],[810,1060],[810,40],[40,40]]]},
             "position": position(axis=(0,-1,0)), "direction": [0,0,1], "depth": 100},
            {"id": "blade-solid", "profile": {"kind":"rectangle", "x":60, "y":20},
             "position": position(), "direction":[0,0,1], "depth":770},
        ],
        "parts": [
            {"id":"frame", "role":"frame", "geometry_refs":["frame-solid"], "placement":position(),
             "appearance":{"color":[0.2,0.3,0.4],"transparency":0}},
            {"id":"blade", "role":"slat", "geometry_refs":["blade-solid"],
             "placement":position((40,-50,90), (1,0,0), (0,-2**-.5,2**-.5)),
             "repeat":{"count":14,"step":[0,0,920/13]}},
        ],
    }


def document(ifc_class="IfcWindow"):
    fixture = Path(__file__).parents[1]/"contract_v2/fixtures/complete.json"
    doc = json.loads(fixture.read_text(encoding="utf-8"))
    doc["schema_version"] = "bim-json/2.6"
    # Isolated products first: avoid exercising template-specific host assumptions.
    keep = {"IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey"}
    product = copy.deepcopy(next(e for e in doc["entities"] if e["ifc_class"] == "IfcDoor"))
    doc["entities"] = [e for e in doc["entities"] if e["ifc_class"] in keep]
    doc["relationships"] = []
    product.update(id="filling-1", ifc_class=ifc_class, property_sets={})
    storey = next(e["id"] for e in doc["entities"] if e["ifc_class"] == "IfcBuildingStorey")
    product["attributes"] = {"Name":"Parameterized filling", "OverallWidth":850., "OverallHeight":1100.,
        "ObjectPlacement":{"relative_to":storey, **position()}, "Representation":components()}
    doc["entities"].append(product)
    return doc


def rep(doc):
    return doc["entities"][-1]["attributes"]["Representation"]


@pytest.mark.parametrize("cls", ["IfcDoor", "IfcWindow"])
def test_versioned_component_contract_and_real_reopen(tmp_path, cls):
    doc = document(cls)
    before = copy.deepcopy(doc)
    assert validate_v2_document(doc) == []
    result = compile_document(doc, tmp_path/"filling.ifc")
    assert result.success, result
    assert doc == before
    model = ifcopenshell.open(str(result.output_path))
    product = model.by_type(cls)[0]
    assert len(model.by_type("IfcDoor")) + len(model.by_type("IfcWindow")) == 1
    assert not model.by_type("IfcBuildingElementPart")
    assert len(product.Representation.Representations[0].Items) == 15
    aspects = {a.Name:a for a in product.Representation.HasShapeAspects}
    assert set(aspects) == {"frame", *(f"blade-{i:03d}" for i in range(1,15))}
    frame = aspects["frame"].ShapeRepresentations[0].Items[0]
    assert frame.SweptArea.is_a("IfcArbitraryProfileDefWithVoids")
    assert len(frame.SweptArea.InnerCurves) == 1
    from text2ifc_presentation import item_appearance_signatures
    color = item_appearance_signatures(frame)
    assert len(color) == 1
    assert [color[0][k] for k in ('red','green','blue','transparency')] == [.2,.3,.4,0.]
    # Independent mesh check: frame opening survives, not a bounding-box replacement.
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), frame)
    verts = np.asarray(shape.verts).reshape(-1,3)
    assert np.isclose(np.ptp(verts[:,0]), .85)
    assert np.isclose(np.ptp(verts[:,2]), 1.1)


@pytest.mark.parametrize("fault", ["missing-ref", "duplicate-part", "unused-definition", "open-ring", "outside-hole", "crossed-ring", "bad-axis", "zero-depth", "unknown-kind", "mixed-template", "repeat-limit", "nan"])
def test_invalid_components_refused_atomically(tmp_path, fault):
    doc = document(); r = rep(doc)
    if fault == "missing-ref": r["parts"][0]["geometry_refs"] = ["missing"]
    elif fault == "duplicate-part": r["parts"].append(copy.deepcopy(r["parts"][0]))
    elif fault == "unused-definition": r["parts"] = r["parts"][:1]
    elif fault == "open-ring": r["definitions"][0]["profile"]["points"].pop()
    elif fault == "outside-hole": r["definitions"][0]["profile"]["holes"][0][1] = [900,1060]
    elif fault == "crossed-ring": r["definitions"][0]["profile"]["points"] = [[0,0],[850,1100],[850,0],[0,1100],[0,0]]
    elif fault == "bad-axis": r["parts"][0]["placement"]["axis"] = [1,0,0]
    elif fault == "zero-depth": r["definitions"][0]["depth"] = 0
    elif fault == "unknown-kind": r["definitions"][0]["profile"]["kind"] = "brep"
    elif fault == "mixed-template": r["template_id"] = "window-single"
    elif fault == "repeat-limit": r["parts"][1]["repeat"]["count"] = 1000000
    elif fault == "nan": r["definitions"][1]["profile"]["x"] = float("nan")
    target = tmp_path/"existing.ifc"; target.write_bytes(b"prior artifact")
    assert validate_v2_document(doc)
    result = compile_document(doc, target)
    assert not result.success and result.input_issues
    assert target.read_bytes() == b"prior artifact"


def test_old_version_rejects_component_geometry():
    doc = document(); doc["schema_version"] = "bim-json/2.5"
    assert any(i.code == "UNSUPPORTED_GEOMETRY_KIND" for i in validate_v2_document(doc))


def test_round_handle_outside_nominal_door_envelope(tmp_path):
    doc = document("IfcDoor"); r = rep(doc)
    r["definitions"][1]["profile"] = {"kind":"circle", "radius":12}
    r["definitions"][1]["depth"] = 120
    r["parts"][1].pop("repeat")
    r["parts"][1].update(id="handle", role="handle", placement=position((750,-180,600)))
    result = compile_document(doc, tmp_path/"door.ifc")
    assert result.success, result
    product = ifcopenshell.open(str(result.output_path)).by_type("IfcDoor")[0]
    handle = next(a for a in product.Representation.HasShapeAspects if a.Name == "handle").ShapeRepresentations[0].Items[0]
    assert handle.SweptArea.is_a("IfcCircleProfileDef")
    assert handle.SweptArea.Radius == 12
    assert product.OverallWidth == 850 and product.OverallHeight == 1100


@pytest.mark.parametrize('damage', ['depth','hole','move','missing','role','color','nominal'])
def test_reopen_verifier_detects_actual_component_corruption(tmp_path, damage):
    from text2ifc_compiler.component_geometry import verify_components
    doc = document()
    result = compile_document(doc,tmp_path/'original.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    product = model.by_type('IfcWindow')[0]
    body = product.Representation.Representations[0]
    item = body.Items[0]
    if damage == 'depth': item.Depth += 10
    elif damage == 'hole': item.SweptArea.InnerCurves[0].Points[0].Coordinates = (50.,40.)
    elif damage == 'move': item.Position.Location.Coordinates = (10.,0.,0.)
    elif damage == 'missing': body.Items = body.Items[1:]
    elif damage == 'role': product.Representation.HasShapeAspects[0].Description = '{}'
    elif damage == 'color': item.StyledByItem[0].Styles[0].Styles[0].Styles[0].SurfaceColour.Red = .8
    elif damage == 'nominal': product.OverallWidth += 20
    assert verify_components(model,doc)


@pytest.mark.parametrize('version', ['bim-json/2.2','bim-json/2.4','bim-json/2.5','bim-json/2.6'])
def test_legacy_part_display_survives_additive_versions(tmp_path, version):
    from tests.compiler.test_basic_filling import public_document
    from text2ifc_presentation import item_appearance_signatures
    doc = public_document('door-left'); doc['schema_version'] = version
    door = next(e for e in doc['entities'] if e['id'] == 'door-1')
    door['part_appearance'] = {'panel':{'color':[.1,.2,.3], 'transparency':.25}}
    result = compile_document(doc,tmp_path/'legacy.ifc')
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    product = model.by_type('IfcDoor')[0]
    panel = next(a for a in product.Representation.HasShapeAspects if a.Name == 'Panel').ShapeRepresentations[0].Items[0]
    signature = item_appearance_signatures(panel)[0]
    assert [signature[k] for k in ('red','green','blue','transparency')] == [.1,.2,.3,.25]


def test_composed_frames_have_independent_measured_extent(tmp_path):
    doc = document(); r = rep(doc)
    r['definitions'] = [r['definitions'][1]]
    r['definitions'][0].update(position=position((0,30,0),(0,1,0)), depth=150)
    r['parts'] = [{'id':'solid', 'role':'test', 'geometry_refs':['blade-solid'],
                  'placement':position((100,200,300),(0,0,1),(0,1,0))}]
    result = compile_document(doc,tmp_path/'rotated.ifc')
    assert result.success, result
    product = ifcopenshell.open(str(result.output_path)).by_type('IfcWindow')[0]
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),product)
    vertices = np.asarray(shape.geometry.verts).reshape(-1,3)*1000
    # Definition Z extrudes along part +Y, then part +Y rotates to product -X.
    assert np.allclose(vertices.min(axis=0),[-80,170,290],atol=1e-6)
    assert np.allclose(vertices.max(axis=0),[70,230,310],atol=1e-6)


@pytest.mark.parametrize('fault', ['touching-hole','nested-holes','duplicate-definition','expanded-collision','parallel-extrusion','near-parallel-extrusion','zero-step','backtracking-edge','wrong-product','unknown-transform','profile-offset'])
def test_additional_component_contract_boundaries(fault):
    doc = document(); r = rep(doc)
    profile = r['definitions'][0]['profile']
    if fault == 'touching-hole': profile['holes'][0][0] = profile['holes'][0][-1] = [0,40]
    elif fault == 'nested-holes': profile['holes'].append([[50,50],[60,50],[60,60],[50,60],[50,50]])
    elif fault == 'duplicate-definition': r['definitions'].append(copy.deepcopy(r['definitions'][0]))
    elif fault == 'expanded-collision': r['parts'][0]['id'] = 'blade-001'
    elif fault == 'parallel-extrusion': r['definitions'][0]['direction'] = [1,0,0]
    elif fault == 'near-parallel-extrusion': r['definitions'][0]['direction'] = [100000000,0,0.00000001]
    elif fault == 'zero-step': r['parts'][1]['repeat']['step'] = [0,0,0]
    elif fault == 'backtracking-edge':
        profile['points'] = [[0,0],[850,0],[800,0],[850,1100],[0,1100],[0,0]]
        profile['holes'] = []
    elif fault == 'wrong-product': doc['entities'][-1]['ifc_class'] = 'IfcBuildingElementProxy'
    elif fault == 'unknown-transform': r['parts'][0]['placement']['scale'] = 2
    elif fault == 'profile-offset': r['definitions'][1]['profile']['origin'] = [0,10]
    assert validate_v2_document(doc)


def test_new_version_keeps_material_list_and_template_wall_support(tmp_path):
    from tests.compiler.test_material_list_v25 import material_document
    doc = material_document(['Steel','Paint'])
    doc['schema_version'] = 'bim-json/2.6'
    result = compile_document(doc,tmp_path/'materials.ifc')
    assert result.success, result


@pytest.mark.parametrize('error', [ValueError('invalid solid'), RuntimeError('geometry kernel refused solid')])
def test_builder_failure_returns_issue_and_preserves_previous_output(tmp_path, monkeypatch, error):
    import text2ifc_compiler.compiler as compiler
    def broken(document): raise error
    monkeypatch.setattr(compiler,'build_ifc_v2',broken)
    output = tmp_path/'existing.ifc'; output.write_bytes(b'prior IFC bytes')
    result = compile_document(document(),output)
    assert not result.success
    assert result.ifc_issues[0].code == 'IFC_BUILD_ERROR'
    assert output.read_bytes() == b'prior IFC bytes'
    assert not list(tmp_path.glob('*.tmp'))


def test_component_display_inherits_type_with_explicit_part_priority(tmp_path):
    from text2ifc_presentation import item_appearance_signatures
    doc = document()
    style = {'id':'style','ifc_class':'IfcWindowStyle','attributes':{'Name':'Requested style','ConstructionType':'NOTDEFINED',
        'OperationType':'NOTDEFINED','ParameterTakesPrecedence':False,'Sizeable':False},'property_sets':{},
        'appearance':{'color':[.7,.8,.9],'transparency':.2},'provenance':{'source':'test'}}
    doc['entities'].append(style)
    doc['relationships'].append({'id':'type-link','ifc_class':'IfcRelDefinesByType','attributes':{
        'RelatedObjects':['filling-1'],'RelatingType':'style'},'provenance':{'source':'test'}})
    result = compile_document(doc,tmp_path/'typed.ifc')
    assert result.success, result
    product = ifcopenshell.open(str(result.output_path)).by_type('IfcWindow')[0]
    for aspect in product.Representation.HasShapeAspects:
        item = aspect.ShapeRepresentations[0].Items[0]
        actual = item_appearance_signatures(item)[0]
        expected = [.2,.3,.4,0.] if aspect.Name == 'frame' else [.7,.8,.9,.2]
        assert [actual[k] for k in ('red','green','blue','transparency')] == expected
