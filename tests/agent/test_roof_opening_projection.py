import copy
import pytest
from text2ifc_agent.cross_storey_identity import cross_storey_entity_records
from text2ifc_agent.generation_packages import build_generation_package_manifest
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation

@pytest.mark.parametrize('offset', [0,1350])
@pytest.mark.parametrize('kind',['IfcSlab','IfcRoof'])
def test_roof_openings_keep_identity_ownership_and_exact_datum(offset,kind):
    roof={'id':'opaque-top','ifc_class':kind,'storey':'level-upper','bottom_elevation_mm':5700,
        'thickness_mm':180,'bounds':{'x':[offset,offset+7000],'y':[0,9000]},
        'openings':[{'id':'opaque-void','bounds':{'x':[offset+1500,offset+3500],'y':[2000,5500]}}]}
    expected={'storeys':[{'id':'level-upper','elevation_mm':3000}],'slabs':[],'stairs':[],'roof':roof}
    before=copy.deepcopy(expected)
    ids=cross_storey_entity_records(slabs=[],stairs=[],roof=roof)
    assert ids['floor_openings']==[{'brief_id':'opaque-void','entity_id':'opaque-void','host_id':'opaque-top','storey':'level-upper','identity_source':'explicit'}]
    manifest=build_generation_package_manifest(expected)
    package=next(p for p in manifest['packages'] if p['kind']=='cross_storey')
    assert 'opaque-void' in package['owned_component_ids']
    assert 'rel-voids-opaque-top' in package['owned_relationship_ids']
    geometry=build_design_geometry_expectation(case_id='offline',design_brief={'known_facts':{'roof_slab':roof}},expected_facts=expected)
    hole=geometry['floor_openings']['opaque-void']
    assert hole['bbox']=={'x':[(offset+1500)/1000,(offset+3500)/1000],'y':[2,5.5],'z':[5.7,5.88]}
    assert hole['host_slab_id']=='opaque-top'
    assert expected==before

def test_roof_missing_opening_bounds_is_not_silently_dropped():
    roof={'id':'top','storey':'upper','bottom_elevation_mm':6000,'thickness_mm':200,'bounds':{'x':[0,8000],'y':[0,7000]},'opening':{'id':'void'}}
    e={'roof':roof,'storeys':[{'id':'upper','elevation_mm':3000}]}
    m=build_generation_package_manifest(e)
    assert m['status']=='draft_required'
    g=build_design_geometry_expectation(case_id='negative',design_brief={'known_facts':{'roof_slab':roof}},expected_facts=e)
    assert any(i['reason']=='floor_opening_bounds_missing' for i in g['unresolved'])


@pytest.mark.parametrize('kind',['IfcSlab','IfcRoof'])
@pytest.mark.parametrize('bad_host',[False,True])
def test_projected_roof_void_is_checked_from_compiled_reopened_ifc(tmp_path,kind,bad_host):
    from tests.ifc_quality.test_floor_opening_identity import _solid
    from text2ifc_compiler import compile_document
    from text2ifc_quality.generated_ifc import check_generated_ifc
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    roof={'id':'opaque-top','ifc_class':kind,'storey':'upper','bottom_elevation_mm':3000,
        'thickness_mm':200,'bounds':{'x':[0,4000],'y':[0,4000]},
        'opening':{'id':'opaque-void','bounds':{'x':[600,1400],'y':[1000,2000]}}}
    geometry=build_design_geometry_expectation(case_id='offline',design_brief={'known_facts':{'roof_slab':roof}},
        expected_facts={'roof':roof})
    entities=[{'id':'project','ifc_class':'IfcProject','attributes':{'Name':'Roof probe'},
        'property_sets':{},'provenance':{'source':'test'}},
        _solid('opaque-top',kind,2000,2000,3000,4000,4000,200),
        _solid('wrong-host','IfcSlab',2000,2000,7000,4000,4000,200),
        _solid('opaque-void','IfcOpeningElement',1000,1500,3000,800,1000,200)]
    doc={'schema_version':'bim-json/2.0','ifc_schema':'IFC2X3','units':{'length':'MILLIMETRE'},
        'entities':entities,'relationships':[{'id':'void-relation','ifc_class':'IfcRelVoidsElement',
        'attributes':{'RelatingBuildingElement':'wrong-host' if bad_host else 'opaque-top','RelatedOpeningElement':'opaque-void'},
        'provenance':{'source':'test'}}],'provenance':{'source':'test'}}
    path=tmp_path/'roof.ifc';result=compile_document(doc,path);assert result.success,result
    result=check_generated_ifc(path,geometry)
    assert result.success is (not bad_host),result.issues
    if not bad_host:
        model=ifcopenshell.open(str(path));host=model.by_type('IfcRelVoidsElement')[0].RelatingBuildingElement
        shape=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),host)
        assert ifcopenshell.util.shape.get_volume(shape.geometry)==pytest.approx(3.04)
