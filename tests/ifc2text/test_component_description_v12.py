"""Wall coordinate precision survives public text without relaxing validation."""
import copy
import json
import re

import numpy as np
import pytest

from tests.ifc2text.test_component_review import sample
from text2ifc_contract.polygon_wall import wall_section
from text2ifc_ifc2text.compact_pipeline import prepare_compact, render_prepared_description


@pytest.mark.parametrize('angle,origin,bevel', [
    (45, [3237.353, 2047.058], 0),
    (137, [-830.234, 2390.777], 55),
    (26.75, [830000.234, -72390.777], 130),
    (180, [0, 0], 0),
])
def test_precise_public_wall_coordinates_retain_layer_section(sample, angle, origin, bevel):
    facts, _ = sample
    wall = facts['storeys'][0]['walls'][0]
    theta = np.deg2rad(angle)
    x = np.array([np.cos(theta), np.sin(theta)])
    y = np.array([-x[1], x[0]])
    length, thickness = 651.887, 240.
    points = [[0, -120], [length, -120], [length-bevel, 120], [0, 120], [0, -120]]
    world = [(np.array(origin) + p[0]*x + p[1]*y).tolist() for p in points]
    wall.update(axis_start_mm=[*origin, 0], axis_end_mm=[*(np.array(origin)+length*x), 0],
                thickness_mm=thickness, height_mm=2160)
    wall['solid_detail'].update(requires_explicit_outline=True, bottom_outline_xy_mm=world,
                                bottom_z_mm=0, height_mm=2160)
    old = render_prepared_description(facts)
    facts['description_policy']['version'] = '1.2'
    frozen = copy.deepcopy(facts)
    text = render_prepared_description(facts)
    row = next(line for line in text.splitlines() if line.startswith('|'+wall['label']+'|'))
    axis = [list(map(float, value.split(','))) for value in re.findall(r'\(([^)]+)\)', row)]
    actual_x = np.array(axis[1][:2])-axis[0][:2]; actual_x /= np.linalg.norm(actual_x)
    actual_y = np.array([-actual_x[1], actual_x[0]])
    line = next(line for line in text.splitlines() if line.startswith('**墙 '+wall['label']+' 的实体轮廓**'))
    ring = line.split('（世界XY，mm）', 1)[1].split('；', 1)[0]
    recovered = [list(map(float, v.split(','))) for v in re.findall(r'\(([^)]+)\)', ring)]
    local = [[float(np.dot(np.array(p)-axis[0][:2], a)) for a in (actual_x, actual_y)] for p in recovered]
    _, low, high, _, _ = wall_section(dict(kind='extruded_profile', direction=[0,0,1], depth=2160,
                                         profile=dict(kind='polygon', points=local)))
    assert abs(high-low-thickness) < .00001
    assert np.max(np.abs(np.array(recovered)-world)) < .000001
    assert facts == frozen
    facts['description_policy']['version']='1.1'
    assert render_prepared_description(facts)==old


def test_v12_prepare_and_review_keep_source_and_unsupported_choice(sample, tmp_path):
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_ifc2text.component_review import start_review, decide_review, approved_description
    facts, source = sample
    original = source.read_bytes()
    report = prepare_compact(source, tmp_path/'v12', description_version='1.2', containment_policy='preserve_recorded')
    assert report['wall_coordinate_decimals'] == 9
    facts['description_policy']['version']='1.2'
    with SessionStore.open(tmp_path/'v12.sqlite', artifact_root=tmp_path/'review12') as store:
        review = start_review(store=store, facts=facts)
        assert review['status']=='awaiting_human'
        decide_review(store=store,session_id=review['session_id'],review_sha256=review['review_sha256'],
                      action='exclude_and_continue',excluded_labels=['D099'])
        text=approved_description(store=store,session_id=review['session_id'])['description']
        assert '#### N001 部件几何' in text and '#### D099 部件几何' not in text
    assert source.read_bytes()==original


def test_nonfinite_wall_coordinate_is_refused(sample):
    facts, _ = sample
    facts['description_policy']['version']='1.2'
    facts['storeys'][0]['walls'][0]['axis_start_mm'][0]=float('nan')
    with pytest.raises(ValueError,match='NONFINITE'):
        render_prepared_description(facts)
