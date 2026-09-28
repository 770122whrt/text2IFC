"""Native component parsing: no Source IFC at the generation endpoint."""
import copy

import ifcopenshell
import ifcopenshell.geom
import numpy as np
import pytest

from tests.compiler.test_component_geometry_v26 import document, rep
from text2ifc_compiler.compiler import compile_document


def test_native_parts_readback_retains_holes_circle_and_repeated_positions(tmp_path):
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    doc = document(); result = compile_document(doc,tmp_path/'source.ifc')
    assert result.success, result
    source = ifcopenshell.open(str(result.output_path)).by_type('IfcWindow')[0]
    value = read_component_geometry(source)
    assert value['status'] == 'supported', value
    assert len(value['representation']['parts']) == 15
    assert {p['id'] for p in value['representation']['parts']} == {'frame',*(f'blade-{i:03d}' for i in range(1,15))}
    assert value['representation']['definitions'][0]['profile']['holes'] == rep(doc)['definitions'][0]['profile']['holes']
    target = copy.deepcopy(doc)
    target['entities'][-1]['attributes']['Representation'] = value['representation']
    rebuilt = compile_document(target,tmp_path/'rebuilt.ifc')
    assert rebuilt.success, rebuilt
    def mesh(product):
        shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),product)
        return np.asarray(shape.geometry.verts).reshape(-1,3)
    a = mesh(source); b = mesh(ifcopenshell.open(str(rebuilt.output_path)).by_type('IfcWindow')[0])
    assert np.max(np.min(np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2),axis=0)) < 1e-6


def test_unsupported_geometry_is_explicit_without_partial_representation(tmp_path):
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    doc = document(); result = compile_document(doc,tmp_path/'source.ifc')
    model = ifcopenshell.open(str(result.output_path)); source = model.by_type('IfcWindow')[0]
    body = source.Representation.Representations[0]
    body.Items = (*body.Items,model.createIfcBlock(model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((0.,0.,0.)),None,None),10.,10.,10.))
    value = read_component_geometry(source)
    assert value['status'] == 'unsupported'
    assert 'representation' not in value
    assert value['unsupported'][0]['ifc_class'] == 'IfcBlock'
    assert value['unsupported'][0]['source_item_id'] == body.Items[-1].id()


@pytest.mark.parametrize('source_path', ['dataset/external/bimnet/hxp.ifc', 'dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc'])
def test_real_sources_yield_supported_doors_and_windows_with_explicit_refusals(source_path):
    from pathlib import Path
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    if not Path(source_path).exists(): pytest.skip('External source corpus not installed')
    model = ifcopenshell.open(source_path)
    for cls in ('IfcWindow','IfcDoor'):
        results = [read_component_geometry(e) for e in model.by_type(cls)]
        assert any(r['status'] == 'supported' for r in results), results
        for r in results:
            assert (r['status'] == 'supported') == ('representation' in r)


def test_invalid_native_dimensions_are_refused_before_public_description(tmp_path):
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    result = compile_document(document(),tmp_path/'valid.ifc')
    model = ifcopenshell.open(str(result.output_path)); product = model.by_type('IfcWindow')[0]
    product.Representation.Representations[0].Items[1].Depth = -5.
    value = read_component_geometry(product)
    assert value['status'] == 'unsupported'
    assert 'representation' not in value


@pytest.mark.parametrize('scale', [1., -1., 2.])
def test_mapping_transform_preserved_or_explicitly_refused(tmp_path, scale):
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    doc = document(); result = compile_document(doc,tmp_path/'source.ifc')
    model = ifcopenshell.open(str(result.output_path)); product = model.by_type('IfcWindow')[0]
    old = product.Representation.Representations[0]
    origin = model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((120.,30.,5.)),None,None)
    source_map = model.createIfcRepresentationMap(origin,old)
    transform = model.createIfcCartesianTransformationOperator3D(
        model.createIfcDirection((0.,1.,0.)),model.createIfcDirection((-1.,0.,0.)),
        model.createIfcCartesianPoint((300.,400.,500.)),scale,model.createIfcDirection((0.,0.,1.)))
    mapped = model.createIfcMappedItem(source_map,transform)
    product.Representation = model.createIfcProductDefinitionShape(None,None,[model.createIfcShapeRepresentation(old.ContextOfItems,'Body','MappedRepresentation',[mapped])])
    detail = read_component_geometry(product)
    if scale != 1.:
        assert detail['status'] == 'unsupported'; return
    assert detail['status'] == 'supported', detail
    doc['entities'][-1]['attributes']['Representation'] = detail['representation']
    rebuilt = compile_document(doc,tmp_path/'rebuilt.ifc')
    assert rebuilt.success, rebuilt
    def mesh(p):
        shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),p)
        return np.asarray(shape.geometry.verts).reshape(-1,3)
    a,b = mesh(product),mesh(ifcopenshell.open(str(rebuilt.output_path)).by_type('IfcWindow')[0])
    assert np.max(np.min(np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2),axis=0)) < 1e-6


def test_metre_source_parameters_normalize_to_millimetres():
    from tests.compiler.test_basic_filling import model_for, representation
    from tests.compiler.test_component_geometry_v26 import position
    from text2ifc_compiler.component_geometry import add_component_geometry
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    model,product,context = model_for(representation(),millimetres=False)
    geometry = {'kind':'component_geometry','geometry_version':'text2ifc/components/1.0',
        'definitions':[{'id':'solid','profile':{'kind':'rectangle','x':.9,'y':2.1},'position':position(), 'direction':[0,0,1],'depth':.04}],
        'parts':[{'id':'panel','role':'panel','placement':position(),'geometry_refs':['solid']}]}
    add_component_geometry(model,product,geometry,context)
    detail = read_component_geometry(product)
    assert detail['status'] == 'supported',detail
    solid = detail['representation']['definitions'][0]
    assert solid['profile'] == {'kind':'rectangle','x':900.,'y':2100.}
    assert solid['depth'] == 40.


def test_ifc4_source_is_not_silently_admitted():
    from text2ifc_ifc2text.component_details_v10 import read_component_geometry
    model = ifcopenshell.file(schema='IFC4')
    product = model.createIfcWindow()
    result = read_component_geometry(product)
    assert result['status'] == 'unsupported'
    assert any('IFC2X3' in r['reason'] for r in result['unsupported'])
