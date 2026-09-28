"""The current comparator has one strict 0.1 mm policy across categories."""
import copy
import json
from pathlib import Path

import pytest

from tests.ifc2text.test_diagnostic_review import facts, item


def compare(a, b):
    from text2ifc_ifc2text.precision_compare_v10 import compare_observations
    return compare_observations(a, b)


@pytest.mark.parametrize('category', ['walls', 'openings', 'doors', 'windows', 'spaces', 'stairs', 'slabs', 'coverings'])
@pytest.mark.parametrize('shift, changed', [(0., False), (.099, False), (.1, True), (.101, True)])
def test_every_category_uses_strict_linear_tolerance(category, shift, changed):
    a = facts(**{category: [item('A')]})
    b = facts(**{category: [item('B', shift)]})
    report = compare(a, b)
    assert report['categories'][category]['matched'][0]['geometry_outside_tolerance'] is changed
    assert report['tolerances']['linear_mm'] == .1


@pytest.mark.parametrize('shift, changed', [(.099, False), (.1, True), (.101, True)])
def test_floor_elevation_is_scored(shift, changed):
    a = facts(windows=[item('A')]); b = copy.deepcopy(a)
    b['storeys'][0]['elevation_mm'] += shift
    report = compare(a, b)
    assert report['summary']['storey_elevation_deviations'] == int(changed)


@pytest.mark.parametrize('delta, changed', [(.099, False), (.1, True), (.101, True)])
def test_nominal_width_is_scored_even_when_geometry_bounds_do_not_change(delta, changed):
    a = item('A'); b = item('B')
    b['overall_width_mm'] += delta
    report = compare(facts(windows=[a]), facts(windows=[b]))
    assert report['categories']['windows']['matched'][0]['geometry_outside_tolerance'] is changed


def test_missing_extra_and_unknown_geometry_are_not_hidden():
    a = facts(doors=[item('A'), item('MISSING', 5000)])
    b = facts(doors=[item('B'), item('EXTRA', 10000)])
    report = compare(a, b)
    assert report['summary']['missing'] == report['summary']['extra'] == 1
    assert report['status']['reconstruction_consistent'] is False
    del a['storeys'][0]['doors'][0]['bounds_mm']
    report = compare(a, b)
    assert any('geometry' in r['fields'] for r in report['unassessed'])


def test_area_is_reported_without_a_millimetre_threshold():
    a = item('A'); b = item('B')
    def footprint(y):
        return {'status': 'measured_projection', 'polygons': [
            {'exterior_xy_mm': [[0, y], [10000, y], [10000, 10000], [0, 10000], [0, y]]}]}
    a['footprint'] = footprint(0); b['footprint'] = footprint(.09)
    report = compare(facts(spaces=[a]), facts(spaces=[b]))
    row = report['categories']['spaces']['matched'][0]
    assert row['outline_area_delta_m2'] > 0
    assert row['geometry_outside_tolerance'] is False


@pytest.mark.parametrize('shift, changed', [(.099, False), (.1, True), (.101, True)])
def test_material_thickness_is_compared_without_rounding(shift, changed):
    a = item('A'); b = item('B')
    a['materials'] = [{'kind': 'material_layer_set', 'layers': [{'name': 'Brick', 'thickness_mm': 200.049}]}]
    b['materials'] = [{'kind': 'material_layer_set', 'layers': [{'name': 'Brick', 'thickness_mm': 200.049 + shift}]}]
    report = compare(facts(walls=[a]), facts(walls=[b]))
    assert report['summary']['material_content_differences'] == int(changed)


def test_host_policy_corrects_source_expectation_but_never_candidate():
    a = facts(walls=[item('WA')], windows=[item('A', floor='S02', host='WA')])
    b = facts(walls=[item('WB')], windows=[item('B', host='WB')])
    original = copy.deepcopy((a, b))
    report = compare(a, b)
    assert not report['relation_differences']
    assert report['original_source_relation_differences']
    assert report['containment_policy']['source_adjustments'][0]['to'] == 'S01'
    assert (a, b) == original
    b['storeys'][0]['windows'][0]['storey'] = 'S02'
    report = compare(a, b)
    assert any(r['relation'] == 'storey' for r in report['relation_differences'])
    assert report['summary']['missing'] == report['summary']['extra'] == 0


@pytest.mark.parametrize('shift, changed', [(.0996, False), (.1, True)])
def test_historical_file_comparator_and_preserves_source(tmp_path, shift, changed):
    from text2ifc_compiler import compile_document
    from text2ifc_ifc2text.precision_compare_v10 import compare_roundtrip
    doc = json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    a = tmp_path / 'a.ifc'; b = tmp_path / 'b.ifc'
    assert compile_document(doc, a).success
    candidate = copy.deepcopy(doc)
    wall = next(e for e in candidate['entities'] if e['id'] == 'wall-1')
    wall['attributes']['ObjectPlacement']['origin'][0] += shift
    assert compile_document(candidate, b).success
    before = a.read_bytes()
    report = compare_roundtrip(a, b)
    assert report['schema_version'] == 'text2ifc/ifc2text-roundtrip-compare/1.0'
    assert (report['summary']['geometric_deviations'] > 0) is changed
    assert report['categories']['walls']['matched'][0]['wall_geometry']['pass'] is not changed
    assert a.read_bytes() == before


def test_boundary_comparison_tolerates_only_floating_point_noise():
    from text2ifc_ifc2text.precision_compare_v10 import outside_linear_tolerance
    assert outside_linear_tolerance(.1 - 1e-12)
    assert not outside_linear_tolerance(.1 - 1e-6)
    assert outside_linear_tolerance(float('nan'))
