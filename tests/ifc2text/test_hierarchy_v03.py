from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from text2ifc_ifc2text.hierarchy import (
    assemble_hierarchy, batch_plan, coordinate_m, make_hierarchy_plan,
)
from text2ifc_ifc2text.observation import extract_description_facts


def facts_fixture(walls: int = 1) -> dict:
    wall = {
        'label': 'W001', 'source_global_id': 'private-wall', 'storey': 'S01',
        'ifc_class': 'IfcWall', 'axis_start_mm': [1234.567, -5.1, 0],
        'axis_end_mm': [5234.567, -5.1, 0], 'thickness_mm': 200,
        'height_mm': 3000, 'measurement_status': 'measured', 'spaces': ['R001', 'R002'],
        'materials': [{'kind': 'single_material', 'name': '砌体', 'origin': 'occurrence'}],
    }
    storey = {
        'label': 'S01', 'name': '一层', 'elevation_mm': 0,
        'spaces': [{'label': 'R001', 'name': '甲', 'boundary_walls': ['W001'], 'source_kind': 'ifc_space'},
                   {'label': 'R002', 'name': '乙', 'boundary_walls': ['W001'], 'source_kind': 'ifc_space'}],
        'derived_spaces': [], 'walls': [], 'doors': [], 'windows': [], 'openings': [], 'stairs': [],
    }
    for n in range(1, walls + 1):
        w = copy.deepcopy(wall)
        w['label'] = f'W{n:03d}'
        if n > 1:
            w['spaces'] = []
        storey['walls'].append(w)
    return {
        'schema_version': 'text2ifc/ifc2text-facts/0.2',
        'source': {'path': 'private/source.ifc'},
        'building': {'storey_count': 1, 'building_name': None},
        'coordinate_system': {'frame': 'ifc_world'},
        'units': {'length': 'millimetre'}, 'issues': [], 'storeys': [storey],
        'unassigned': {k: [] for k in ('walls','doors','windows','openings','stairs','spaces')},
        'unrepresented_classes': {},
    }


def echoed_batches(plan, limit=5000):
    return [
        {'schema_version': 'text2ifc/ifc2text-layout/0.3',
         'groups': [{'paragraphs': [[item['id']] for item in block['items']], 'block_id': block['id']}
                    for block in batch['blocks']]}
        for batch in batch_plan(plan, max_chars=limit)
    ]


def test_coordinate_is_metres_two_decimals_without_changing_facts():
    assert coordinate_m(1234.567) == '1.23'
    assert coordinate_m(-5.1) == '-0.01'
    assert coordinate_m(-0.1) == '0.00'
    assert coordinate_m(1000) == '1.00'
    with pytest.raises(ValueError):
        coordinate_m(float('nan'))
    facts = facts_fixture()
    before = copy.deepcopy(facts)
    plan = make_hierarchy_plan(facts)
    assert facts == before
    text = assemble_hierarchy(plan, echoed_batches(plan))
    assert '(1.23, -0.01, 0.00)' in text
    assert '形心' not in text
    assert 'private-wall' not in text and 'private/source.ifc' not in text


def test_shared_wall_complete_once_after_rooms_with_materials_last():
    plan = make_hierarchy_plan(facts_fixture())
    text = assemble_hierarchy(plan, echoed_batches(plan))
    assert text.index('房间 R001') < text.index('墙 W001') < text.index('### 材料')
    assert text.count('墙 W001：') == 1
    assert 'R002' in text and '共用' in text
    assert '砌体' in text


def test_large_floor_has_no_cardinality_cutoff_and_batching_drops_nothing():
    plan = make_hierarchy_plan(facts_fixture(170))
    batches = batch_plan(plan, max_chars=4000)
    assert len(batches) > 1
    flat = [i['id'] for b in batches for block in b['blocks'] for i in block['items']]
    original = [i['id'] for block in plan['blocks'] for i in block['items']]
    assert flat == original and len(flat) == len(set(flat))
    text = assemble_hierarchy(plan, echoed_batches(plan, 4000))
    assert 'W170' in text
    assert text.count('墙 W') == 170


@pytest.mark.parametrize('mutate', ['missing','duplicate','unknown','extra_field','empty','reorder_blocks'])
def test_layout_cannot_drop_change_or_invent_facts(mutate):
    plan = make_hierarchy_plan(facts_fixture())
    output = echoed_batches(plan)
    groups = output[0]['groups']
    if mutate == 'missing':
        groups[0]['paragraphs'] = []
    elif mutate == 'duplicate':
        groups[0]['paragraphs'] += groups[0]['paragraphs'][:1]
    elif mutate == 'unknown':
        groups[0]['paragraphs'][0] = ['invented']
    elif mutate == 'extra_field':
        groups[0]['text'] = '建筑完全一致。'
    elif mutate == 'empty':
        output = []
    elif mutate == 'reorder_blocks':
        groups.reverse()
    with pytest.raises(ValueError):
        assemble_hierarchy(plan, output)


def test_unknown_room_membership_and_unassigned_entities_stay_visible():
    facts = facts_fixture()
    facts['storeys'][0]['spaces'] = []
    facts['storeys'][0]['walls'][0]['spaces'] = []
    facts['storeys'][0]['walls'][0]['materials'] = []
    unassigned = copy.deepcopy(facts['storeys'][0]['walls'][0])
    unassigned['label'] = 'W099'
    unassigned['storey'] = None
    facts['unassigned']['walls'].append(unassigned)
    plan = make_hierarchy_plan(facts)
    text = assemble_hierarchy(plan, echoed_batches(plan))
    assert 'W099' in text and '归属未确认' in text
    assert '房间用途' not in text or '未确认' in text
    assert '材料关联未确认' in text


def test_multiple_floors_with_many_rooms_preserve_hierarchy_and_every_room():
    facts = facts_fixture()
    second = copy.deepcopy(facts['storeys'][0])
    second.update(label='S02', name='二层', elevation_mm=3000)
    second['walls'] = []
    second['spaces'] = [
        {'label': f'R{n:03d}', 'name': f'空间{n}', 'boundary_walls': [], 'source_kind': 'ifc_space'}
        for n in range(3, 73)
    ]
    facts['storeys'].append(second)
    plan = make_hierarchy_plan(facts)
    text = assemble_hierarchy(plan, echoed_batches(plan, 2000))
    assert text.index('楼层 S01') < text.index('楼层 S02') < text.index('房间 R072')
    assert plan['component_counts']['spaces'] == 72
    assert text.count('### 材料') == 2


def test_coordinate_rounding_removes_only_consecutive_duplicate_vertices():
    from text2ifc_ifc2text.hierarchy import rounded_ring
    source = [[0, 0], [1000, 0], [1000.01, 0.01], [1000, 1000], [0, 1000], [0, 0]]
    before = copy.deepcopy(source)
    result = rounded_ring(source)
    assert len(result) == 5
    assert result[0] == result[-1]
    assert source == before
    with pytest.raises(ValueError, match='COLLAPSED'):
        rounded_ring([[0,0],[1,0],[1,1],[0,0]])


def test_full_precision_thin_material_is_not_rounded_away():
    facts = facts_fixture()
    facts['storeys'][0]['walls'][0]['materials'] = [{
        'kind': 'material_layer_set_usage', 'origin': 'occurrence',
        'layers': [{'name': '薄膜', 'thickness_mm': 0.25}, {'name': '砌体', 'thickness_mm': 199.75}],
        'direction': 'AXIS2', 'direction_sense': 'POSITIVE', 'offset_mm': -100,
    }]
    plan = make_hierarchy_plan(facts)
    text = assemble_hierarchy(plan, echoed_batches(plan))
    assert '0.25 mm' in text and '199.75 mm' in text


def test_real_ifc_is_read_only_and_space_outline_is_not_bbox(tmp_path: Path):
    from text2ifc_compiler import compile_document
    root = Path(__file__).resolve().parents[2]
    document = json.loads((root/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    room = next(e for e in document['entities'] if e['ifc_class']=='IfcSpace')
    room['attributes']['Representation']['profile']['points'] = [[0,0],[4000,0],[4000,1000],[1000,1000],[1000,3000],[0,3000],[0,0]]
    path = tmp_path/'source.ifc'
    assert compile_document(document, path).success
    before = path.read_bytes()
    facts = extract_description_facts(path)
    space = facts['storeys'][0]['spaces'][0]
    assert space['footprint']['status']=='measured_projection'
    assert len(space['footprint']['polygons'][0]['exterior_xy_mm']) > 5
    assert space['footprint']['area_m2'] == pytest.approx(6.0, abs=.001)
    assert path.read_bytes() == before
    assert facts['schema_version'] == 'text2ifc/ifc2text-facts/0.2'
