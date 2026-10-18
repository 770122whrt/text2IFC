from __future__ import annotations

import copy
import json

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, build_recipes
from scripts.ifc_repair.dataset_batch.prompts_v2 import PROFILE, prepare_inventory, render_prompts


def window_recipe(inv):
    return next(r for r in build_recipes(inv, count=25, seed=42) if r['family'] == 'window')


def test_two_modes_do_not_share_names_and_world_locators(scene_factory, tmp_path):
    inv = prepare_inventory(scene_factory(tmp_path / 'source.ifc', millimetres=True))
    recipe = window_recipe(inv)
    prompts = render_prompts(recipe)
    assert set(prompts) == {'host_wall', 'world'}
    assert 'Host wall' in prompts['host_wall']
    assert '世界' not in prompts['host_wall']
    assert '世界坐标' in prompts['world']
    assert 'Host wall' not in prompts['world']
    assert all(t['name'] not in prompts['world'] for t in recipe['deletions'])
    assert '宿主墙世界原点' in prompts['world']
    assert '洞口规格开始' in prompts['world']


def test_beams_and_columns_use_world_without_fabricated_wall(scene_factory, tmp_path):
    inv = prepare_inventory(scene_factory(tmp_path / 'source.ifc'))
    recipe = next(r for r in build_recipes(inv, count=25) if r['family'] == 'beam_column')
    prompts = render_prompts(recipe)
    assert prompts['host_wall'] is None
    assert '补建一根梁' in prompts['world'] and '补建一根柱' in prompts['world']
    assert '宿主墙' not in prompts['world']
    assert '几何实体1采用' in prompts['world']


def test_duplicate_wall_names_cannot_be_disambiguated_with_world_in_host_mode(scene_factory, tmp_path):
    inv = prepare_inventory(scene_factory(tmp_path / 'source.ifc'))
    recipe = window_recipe(inv)
    target = copy.deepcopy(recipe['deletions'][0])
    target['host']['name_storey_unique'] = False
    prompts = render_prompts({**recipe, 'deletions': [target]})
    assert prompts['host_wall'] is None
    assert prompts['world'] is not None


def test_new_profile_is_opt_in_and_writes_automatic_requests(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc')
    inv = prepare_inventory(source)
    recipe = window_recipe(inv)
    case = tmp_path / 'case'
    result = apply_recipe(source, recipe, case, inventory=inv, prompt_profile=PROFILE)
    assert result['status'] == 'passed'
    assert set(result['prompt_templates']) == {'host_wall', 'world'}
    manifest = json.loads((case / 'private/mutation.json').read_text(encoding='utf-8'))
    assert manifest['prompt_profile'] == PROFILE
    assert not (case / 'public/request-storey_local.txt').exists()
    assert (case / 'public/request-world.txt').read_text(encoding='utf-8') == render_prompts(manifest)['world']
