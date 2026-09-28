"""Public wall outlines must catch a mirrored bevel even with the same bbox."""
import math

import pytest

from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation
from text2ifc_compiler.compiler import compile_document
from text2ifc_quality.generated_ifc import check_generated_ifc
from tests.ifc2text.test_component_hosted_public_chain import hosted_document


def scene(angle=0, mirror=False, offset=0):
    points = [[0,-120],[1000,-120],[760,120],[0,120],[0,-120]]
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    world = [[300+c*x-s*y, -700+s*x+c*y] for x,y in points]
    brief = {'known_facts': {'storeys': [{'id':'floor','elevation_mm':-200}],
        'walls':[{'id':'wall','storey':'floor','polygon':world,'z_min_mm':100,'height_mm':2400}]}}
    facts = build_expected_facts(case_id='bevel', design_brief=brief)
    expectation = build_design_geometry_expectation(case_id='bevel', design_brief=brief,
        expected_facts=facts, schema_version='text2ifc/design-geometry-expectation/1.3')
    candidate, _, storey_id = hosted_document('IfcWindow')
    product = next(e for e in candidate['entities'] if e['id']=='W001')
    candidate['entities'] = [e for e in candidate['entities'] if e['ifc_class'] in
        {'IfcProject','IfcSite','IfcBuilding','IfcBuildingStorey'}] + [product]
    candidate['relationships'] = []
    product.update(id='wall')
    product['attributes']['ObjectPlacement'] = {'relative_to':storey_id,'origin':[300+offset,-700,100], 'axis':[0,0,1], 'ref_direction':[c,s,0]}
    product['attributes']['Representation'] = {'kind':'extruded_profile', 'depth':2400,'direction':[0,0,1],
        'profile':{'kind':'polygon','points':[[x,-y if mirror else y] for x,y in points]}}
    return candidate, expectation


@pytest.mark.parametrize('angle', [0,37,90,157])
@pytest.mark.parametrize('mirror', [False,True])
def test_compiled_wall_outline_uses_composed_world_geometry(tmp_path, angle, mirror):
    candidate, expectation = scene(angle, mirror)
    assert expectation['complete'], expectation['unresolved']
    assert 'axis' not in expectation['walls']['wall']  # Full footprint replaces the unstable dominant-bbox-axis proxy.
    path = tmp_path/'wall.ifc'
    result = compile_document(candidate, path)
    assert result.success, result
    checked = check_generated_ifc(path, expectation)
    assert checked.success is not mirror, checked.issues
    if mirror:
        assert any(i['code']=='WALL_OUTLINE_MISMATCH' for i in checked.issues)


@pytest.mark.parametrize('offset,passes', [(1,True),(1.01,False)])
def test_wall_outline_uses_one_mm_inclusive_tolerance(tmp_path, offset, passes):
    candidate, expectation = scene(offset=offset)
    path = tmp_path/'wall.ifc'
    assert compile_document(candidate,path).success
    checked = check_generated_ifc(path,expectation)
    assert checked.success is passes, checked.issues


def test_conflicting_explicit_wall_outlines_fail_closed():
    candidate, expectation = scene()
    from text2ifc_agent.wall_outline import public_wall_outline
    with pytest.raises(ValueError):
        public_wall_outline({'polygon':[[0,0],[100,0],[100,50],[0,0]],
                             'solid_outline':[[0,0],[200,0],[100,50],[0,0]]})


@pytest.mark.parametrize('start,end', [([0,0],[1000,1000]),([1000,1000],[0,0]),([0,0],[0,1000])])
def test_oblique_or_reversed_centrelines_have_a_checked_footprint(start,end):
    from text2ifc_agent.wall_outline import public_wall_outline
    result = public_wall_outline({'start_mm':start,'end_mm':end,'thickness_mm':200})
    assert result.area == pytest.approx(math.dist(start,end)*200)
    assert result.is_valid
