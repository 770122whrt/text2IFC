from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.ifc_repair.dataset_batch.engine import build_recipes, verify_seal
from scripts.ifc_repair.dataset_batch.pilot import process_source, recipe_from_plan, select_recipes, write_report
from scripts.ifc_repair.dataset_batch.prompts_v2 import prepare_inventory


def test_preassigned_coverage_uses_fresh_admitted_geometry(scene_factory, tmp_path):
    inv = prepare_inventory(scene_factory(tmp_path / 'source.ifc'))
    target = inv['targets']['window'][0]
    plan = {'family': 'window', 'deletions': [{'class_family': 'window', 'private_target_guid': target['guid'], 'preserve_opening': False}], 'property_change': None}
    recipe = recipe_from_plan(inv, plan)
    assert recipe['deletions'][0]['opening']['geometry']['body_spec']['method'] == 'complete_extrusions'
    assert not recipe['deletions'][0]['preserve_opening']
    bad = copy.deepcopy(plan)
    bad['deletions'][0]['private_target_guid'] = 'not-in-admitted-IFC'
    with pytest.raises(ValueError, match='NOT_ADMITTED'):
        recipe_from_plan(inv, bad)
    groups = select_recipes(build_recipes(inv, count=30), 4, ['window', 'column', 'beam_column', 'attribute'])
    assert [g[0]['family'] for g in groups] == ['window', 'column', 'beam_column', 'attribute']


def test_single_ifc_produces_four_pairs_with_bound_checks(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc', millimetres=True)
    out = tmp_path / 'pilot'
    out.mkdir()
    spec = {'source_id': 'fixture', 'input_path': str(source), 'pilot_families': ['window', 'door_window', 'beam_column', 'attribute']}
    result = process_source(spec, str(tmp_path), str(out), 4, 20261010)
    assert result['status'] == 'complete', [(x['family'], x.get('errors')) for x in result['attempts']]
    assert len(result['cases']) == 4
    for row in result['cases']:
        case = out / row['path']
        assert (case / 'public/request.txt').is_file()
        assert verify_seal(case)
        details = json.loads((case / 'case.json').read_text(encoding='utf-8'))
        assert details['information_sufficient'] and details['wall_check_passed']
    summary = write_report(out, [result], [], 4)
    assert summary['status'] == 'complete'
    assert summary['provider_calls'] == 0 and summary['human_reviewed_cases'] == 0
    assert summary['wall_check_cases'] == 2
    case = out / result['cases'][0]['path']
    (case / 'public/request.txt').write_text('changed', encoding='utf-8')
    assert not verify_seal(case)
