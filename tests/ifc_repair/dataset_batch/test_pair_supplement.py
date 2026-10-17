"""Supplement scheduling evidence, separate from IFC repair capability."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_supplement as s


def property_inventory():
    return {'targets': {kind: [] for kind in q.CLASSES}, 'properties': [
        {'guid': 'door-a', 'ifc_class': 'IfcDoor', 'pset_name': 'Pset_DoorCommon',
         'property_name': name, 'value_type': 'IfcLabel', 'before': 'original'}
        for name in ('A', 'B', 'C', 'D')]}


def test_extra_subsets_are_real_distinct_operations_without_changing_wrong_values():
    inv = property_inventory()
    original = list(q.iter_raw_recipes(inv, seed=17))
    extended = list(s.raw_with_property_subsets(inv, original=q.iter_raw_recipes, seed=17))
    assert len(original) == 9 and len(extended) == 15
    assert len({q.recipe_key(recipe) for recipe in extended}) == 15
    original_keys = {q.recipe_key(recipe) for recipe in original}
    extras = [r for r in extended if q.recipe_key(r) not in original_keys]
    assert len(extras) == 6 and all(not r['deletions'] for r in extras)
    expected = {p['property_name']: q._wrong_value(p, 0) for p in inv['properties']}
    assert all(p['after'] == expected[p['property_name']] for r in extras for p in r['property_changes'])
    assert inv == property_inventory()


def test_extra_stream_obeys_cooperative_stop():
    inv = property_inventory()
    stopped = [False]
    stream = s.raw_with_property_subsets(inv, original=lambda *a, **k: iter(()),
                                         stopped=lambda: stopped[0])
    next(stream)
    stopped[0] = True
    assert list(stream) == []


def test_prepared_filter_skips_only_first_pass_accepted_recipes():
    recipes = list(q.iter_raw_recipes(property_inventory(), seed=17))[:3]
    blocked = {q.recipe_key(recipes[0]), q.recipe_key(recipes[2])}
    assert list(s.exclude_accepted(enumerate(recipes, 1), blocked)) == [(2, recipes[1])]


def test_only_repaired_failure_is_retried_in_new_round():
    baseline = {'cases': [{'recipe_key': 'accepted'}], 'attempts': [
        {'status': 'passed', 'recipe_key': 'accepted'},
        {'status': 'failed', 'recipe_key': 'guard',
         'errors': {'exception': 'RuntimeError:Only entities with ids are supported. Provided entity: IfcParameterValue(1)'}},
        {'status': 'failed', 'recipe_key': 'wall', 'errors': {'walls': ['OPENING_CLOSURE_UNCONFIRMED']}},
        {'status': 'failed', 'recipe_key': 'prompt', 'errors': {'prompts': ['basic_shape_surviving_peer_available']}}]}
    assert s.excluded_first_pass_keys(baseline) == {'accepted', 'wall', 'prompt'}


def test_supplement_pair_ids_preserve_modes_and_do_not_collide_with_first_pass():
    recipe = {'deletions': [], 'property_changes': [{'guid': 'door-a'}]}
    first = q.make_pair_records(source_id='formal-021', damage_number=1,
        case_path='sources/formal-021/cases/damage-001', model_sha256='a'*64,
        request_hashes={'world': 'b'*64, 'host_wall': 'c'*64}, recipe=recipe, remaining=2)
    renamed = s.rename_pairs(first)
    assert [p['case_id'] for p in renamed] == ['formal-021-s1-d001-world', 'formal-021-s1-d001-host_wall']
    assert all(p['damage_id'] == 'formal-021-s1-d001' for p in renamed)
    assert first[0]['damage_id'] == 'formal-021-d001'
    assert all(before['model_sha256'] == after['model_sha256'] for before, after in zip(first, renamed))


def test_adapter_restores_existing_functions_after_exception():
    from scripts.ifc_repair.dataset_batch import engine
    names = ('_program_bindings', '_configuration', 'iter_raw_recipes', 'iter_prepared_recipes',
             'make_pair_records', '_check_damage')
    original = {name: getattr(q, name) for name in names}
    original_guard = engine.guard_geometry
    with pytest.raises(RuntimeError, match='local injected failure'):
        with s.supplement_adapter({'first_pass_result_sha256': 'f'*64}, set(), set()):
            assert engine.guard_geometry is not original_guard
            assert q._program_bindings()['scripts/ifc_repair/dataset_supplement.py']
            raise RuntimeError('local injected failure')
    assert all(getattr(q, name) is value for name, value in original.items())
    assert engine.guard_geometry is original_guard


def test_merge_rejects_duplicate_semantic_recipe_even_with_new_pair_ids():
    baseline = {'source_id': 'formal-021', 'pairs': [], 'cases': [{'recipe_key': 'same'}],
                'attempts': [], 'attempted_cases': 0}
    extra = {**copy.deepcopy(baseline), 'source_id': 'formal-021'}
    with pytest.raises(ValueError, match='DUPLICATE_ACCEPTED_RECIPE'):
        s.merge_results([baseline], [extra], quota=25)


def test_real_supplement_preserves_first_pass_and_reuses_bound_source_admission(
        scene_factory, tmp_path, monkeypatch):
    reference = scene_factory(tmp_path / 'mother.ifc')
    spec = {'source_id': 'formal-021', 'input_path': str(reference), 'source_sha256': q.sha256(reference)}
    batch = tmp_path / 'batch'
    original = q.process_mother(spec, tmp_path, batch / 'private/production',
                               pairs_per_ifc=2, max_attempts=6, seed=17)
    source = batch / 'private/production/sources/formal-021'
    frozen = {str(p.relative_to(source)): q.sha256(p) for p in source.rglob('*') if p.is_file()}
    for name in ('native_validate', 'prepare_inventory'):
        monkeypatch.setattr(q, name, lambda *a, **k: pytest.fail('CACHED_ADMISSION_REEXECUTED'))
    result = s.supplement_mother(batch, spec, quota=3, max_attempts=6, seed=17, repository=tmp_path)
    assert len(result['pairs']) == 1 and len(result['cases']) == 1
    assert result['pairs'][0]['case_id'].startswith('formal-021-s1-')
    assert result['source_unchanged'] and result['cases'][0]['machine_validated']
    assert not {c['recipe_key'] for c in result['cases']} & {c['recipe_key'] for c in original['cases']}
    assert {str(p.relative_to(source)): q.sha256(p) for p in source.rglob('*') if p.is_file()} == frozen
    second = s.supplement_mother(batch, spec, quota=3, max_attempts=6, seed=17, repository=tmp_path)
    assert second['pairs'] == result['pairs'] and second['attempts'] == result['attempts']
    with pytest.raises(ValueError, match='CHECKPOINT_CONFIGURATION_OR_PROGRAM_MISMATCH'):
        s.supplement_mother(batch, spec, quota=3, max_attempts=7, seed=17, repository=tmp_path)
    assert {str(p.relative_to(source)): q.sha256(p) for p in source.rglob('*') if p.is_file()} == frozen
    merged = s.merge_results([original], [result], quota=3)
    assert merged[0]['status'] == 'complete' and len(merged[0]['pairs']) == 3
