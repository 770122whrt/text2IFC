"""First incremental lowering slice: explicit parent-frame boxes, no LLM."""
import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import pytest


@pytest.mark.parametrize('lower,upper', [
    ([0, 0, 6150], [8000, 6000, 6300]),
    ([-900, -400, -150], [1500, 1800, 0]),
    ([25, 35, 40], [25.5, 36.5, 42.5]),
])
def test_explicit_bounds_lower_to_center_without_mutating_inputs(lower, upper):
    from text2ifc_agent.geometry_authoring import rectangular_prism_attributes
    before = copy.deepcopy((lower, upper))
    result = rectangular_prism_attributes(relative_to='parent', lower=lower, upper=upper)
    placement, rep = result['ObjectPlacement'], result['Representation']
    assert placement['origin'] == [(lower[0]+upper[0])/2, (lower[1]+upper[1])/2, lower[2]]
    assert placement['relative_to'] == 'parent'
    assert placement['ref_direction'] == [1, 0, 0]
    assert rep['profile']['x'] == upper[0]-lower[0]
    assert rep['profile']['y'] == upper[1]-lower[1]
    assert rep['depth'] == upper[2]-lower[2]
    assert set(result) == {'ObjectPlacement', 'Representation'}
    assert (lower, upper) == before


@pytest.mark.parametrize('lower,upper', [
    ([0,0,0], [0,1,1]), ([0,0,0], [1,-1,1]), ([0,0,0], [1,1,0]),
    ([0,0], [1,1,1]), ([0,0,0], [1,1,float('inf')]),
    ([0,float('nan'),0], [1,1,1]), ([False,0,0], [1,1,1]),
    (['0',0,0], [1,1,1]), (None, [1,1,1]),
    ([-1e308,0,0], [1e308,1,1]),
])
def test_invalid_or_degenerate_bounds_are_rejected(lower, upper):
    from text2ifc_agent.geometry_authoring import rectangular_prism_attributes
    with pytest.raises(ValueError):
        rectangular_prism_attributes(relative_to='parent', lower=lower, upper=upper)


@pytest.mark.parametrize('parent', ['', None, 42])
def test_parent_must_be_explicit(parent):
    from text2ifc_agent.geometry_authoring import rectangular_prism_attributes
    with pytest.raises(ValueError):
        rectangular_prism_attributes(relative_to=parent, lower=[0,0,0], upper=[1,1,1])


@pytest.mark.parametrize('fixture', ['two-storey', 'three-storey'])
@pytest.mark.parametrize('rotated', [False, True])
def test_scaffold_roof_covers_requested_footprint_after_ifc_reopen(tmp_path, fixture, rotated):
    from text2ifc_agent.complex_scaffold import build_scaffold_candidate
    from text2ifc_agent.expected_facts import build_expected_facts
    from text2ifc_compiler import compile_document
    root = Path(__file__).resolve().parents[2]
    brief = json.loads((root/f'dataset/processed/agent-demo/phase6.5-cases/{fixture}-case.json').read_text(encoding='utf-8'))['design_brief']
    before = copy.deepcopy(brief)
    expected = build_expected_facts(case_id='roof-bounds', design_brief=brief)
    value = build_scaffold_candidate(case_id='roof-bounds', design_brief=brief, expected_facts=expected)
    assert brief == before
    parent = next(e for e in value['entities'] if e['id']=='building-1')['attributes']['ObjectPlacement']
    parent['origin'] = [1300, -700, 500]
    if rotated:
        parent['ref_direction'] = [0,1,0]
    out = tmp_path/'roof.ifc'
    result = compile_document(value, out)
    assert result.success, result
    model = ifcopenshell.open(str(out))
    settings = ifcopenshell.geom.settings(); settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, model.by_type('IfcRoof')[0])
    vertices = shape.geometry.verts
    building = brief['known_facts']['building']; roof = expected['roof']
    w, d = building['width_x_mm']/1000, building['depth_y_mm']/1000
    xy = ([1.3-d,1.3], [-.7,-.7+w]) if rotated else ([1.3,1.3+w], [-.7,-.7+d])
    bounds = [*xy, [.5+roof['elevation_mm']/1000, .5+(roof['elevation_mm']+roof['thickness_mm'])/1000]]
    for axis, interval in enumerate(bounds):
        assert [min(vertices[axis::3]), max(vertices[axis::3])] == pytest.approx(interval)
