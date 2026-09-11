"""Building outline extraction does not prove solid or concave topology."""
import pytest
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


@pytest.mark.parametrize('wrapper', ['polygon', 'points', 'list'])
@pytest.mark.parametrize('points', [
    [[0,0],[6000,0],[6000,2000],[2000,2000],[2000,5000],[0,5000]],
    [[-3000,1000],[3000,1000],[3000,2000],[-1000,2000],[-1000,4000],[3000,4000],[3000,6000],[-3000,6000]],
])
def test_outline_wrappers_keep_slab_roof_and_opening_expectations(wrapper, points):
    outline = points if wrapper == 'list' else {wrapper: points}
    result = derive(outline)
    assert result['slabs']['slab']['bbox']['x'] == [min(p[0] for p in points)/1000, max(p[0] for p in points)/1000]
    assert result['roof']['roof']['bbox']['y'] == [min(p[1] for p in points)/1000, max(p[1] for p in points)/1000]
    assert result['floor_openings']['void']['host_slab_id'] == 'slab'
    assert result['floor_openings']['void']['bbox']['z'] == [2.85,3.0]


def derive(outline):
    return build_design_geometry_expectation(case_id='independent-shape',
        design_brief={'known_facts':{'building':{'outline':outline}}},
        expected_facts={'slabs':[{'id':'slab','top_elevation_mm':3000,'thickness_mm':150,
            'openings':[{'id':'void','bounds':{'x_min':0,'x_max':1000,'y_min':1000,'y_max':2000}}]}],
            'roof':{'id':'roof','bottom_elevation_mm':6000,'thickness_mm':150}})


@pytest.mark.parametrize('outline', [
    {'polygon':[[0,0],[1000,0]]}, {'polygon':[[0,0],[0,1000],[0,2000]]},
    {'polygon':[[0,0],['bad',1000],[1000,2000]]},
    {'points':[[0,0],[1000,0],[1000,1000]],'polygon':[[0,0],[2000,0],[2000,2000]]},
])
def test_invalid_or_conflicting_outline_never_produces_geometry_pass(outline):
    result=derive(outline)
    assert not result['slabs'] and not result['roof']
    assert result['unresolved']
