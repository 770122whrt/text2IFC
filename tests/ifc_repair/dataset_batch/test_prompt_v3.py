from __future__ import annotations

import copy
import json
import re

import pytest
import ifcopenshell
import ifcopenshell.guid

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, build_recipes
from scripts.ifc_repair.dataset_batch.prompts_v3 import (
    PROFILE, prepare_inventory, prepare_recipe, render_prompts,
)


def test_reference_first_and_single_locator(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc', millimetres=True)
    inv = prepare_inventory(source)
    recipe = prepare_recipe(next(r for r in build_recipes(inv, count=30) if r['family'] == 'window'))
    texts = render_prompts(recipe)
    named, world = texts['host_wall'], texts['world']
    assert 'Host wall' in named and '大致朝' in named
    assert '世界' not in named
    assert 'Host wall' not in world and '完整形状复制参照：现存IfcWindow世界基点' in world
    assert '自身坐标的外包范围' not in world and '几何实体' not in world
    assert '洞口复制参照构件所填洞口' in world
    assert '朝向与参照相同' in world
    assert recipe['deletions'][0]['geometry']['body_spec']['method'] == 'complete_extrusions'
    for text in texts.values():
        assert not re.search(r'\d+\.\d{4,}', re.sub(r'「.*?」', '', text))


def test_no_reference_complex_shape_is_rejected(scene_factory, tmp_path):
    inv = prepare_inventory(scene_factory(tmp_path / 'source.ifc'))
    recipe = next(r for r in build_recipes(inv, count=30) if r['family'] == 'window')
    recipe = copy.deepcopy(recipe)
    geometry = recipe['deletions'][0]['geometry']
    geometry['peers'] = []
    geometry['basic_shape'] = None
    with pytest.raises(ValueError, match='NO_SUPPORTED_SHAPE_REFERENCE_OR_BASIC_BOX'):
        prepare_recipe(recipe)


def test_wall_properties_are_not_damage_candidates(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc')
    model = ifcopenshell.open(str(source))
    wall = model.by_type('IfcWall')[0]
    prop = model.createIfcPropertySingleValue('Reference', None, model.createIfcIdentifier('wall property'), None)
    pset = model.createIfcPropertySet(ifcopenshell.guid.new(), wall.OwnerHistory, 'Pset_WallCommon', None, [prop])
    model.createIfcRelDefinesByProperties(ifcopenshell.guid.new(), wall.OwnerHistory, None, None, [wall], pset)
    model.write(str(source))
    inv = prepare_inventory(source)
    assert all(p['guid'] != wall.GlobalId for p in inv['properties'])


def test_deleted_reference_is_not_used_and_simple_fallback_is_explicit(scene_factory, tmp_path):
    inv = prepare_inventory(scene_factory(tmp_path / 'source.ifc'))
    targets = [{**t, 'preserve_opening': False} for t in inv['targets']['beam']]
    recipe = prepare_recipe({'family': 'beam', 'severity': 'light', 'deletions': targets, 'property_changes': []})
    text = render_prompts(recipe)['world']
    assert text.count('形状为单一长方体') == 2
    assert '完整形状复制参照' not in text
    assert render_prompts(recipe)['host_wall'] is None


def test_new_profile_writes_requests_without_rewriting_private_body(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc')
    inv = prepare_inventory(source)
    recipe = prepare_recipe(next(r for r in build_recipes(inv, count=30) if r['family'] == 'window'))
    result = apply_recipe(source, recipe, tmp_path / 'case', inventory=inv, prompt_profile=PROFILE)
    assert result['status'] == 'passed'
    manifest = json.loads((tmp_path / 'case/private/mutation.json').read_text(encoding='utf-8'))
    assert manifest['prompt_profile'] == PROFILE
    assert manifest['deletions'][0]['geometry']['body_spec']['components']
    assert manifest['deletions'][0]['geometry']['request_shape']['method'] == 'surviving_instance'


def test_new_profile_batch_uses_independent_public_checker(scene_factory, tmp_path):
    from scripts.ifc_repair.dataset_batch.pilot import process_source, write_report
    source = scene_factory(tmp_path / 'source.ifc', millimetres=True)
    output = tmp_path / 'pilot'
    output.mkdir()
    spec = {'source_id': 'fixture', 'input_path': str(source), 'request_profile': PROFILE,
            'pilot_families': ['window', 'door_window', 'beam_column', 'attribute']}
    result = process_source(spec, str(tmp_path), str(output), 4, 20261010)
    assert result['status'] == 'complete', [(c['family'], c.get('errors')) for c in result['attempts']]
    assert write_report(output, [result], [], 4)['request_profile'] == PROFILE
    for row in result['cases']:
        folder = output / row['path']
        manifest = json.loads((folder / 'private/mutation.json').read_text(encoding='utf-8'))
        checks = json.loads((folder / 'private/prompt-check.json').read_text(encoding='utf-8'))
        assert manifest['prompt_profile'] == PROFILE
        assert checks['world']['checker_version'] == 'text2ifc/dataset-prompt-check/1.2'
