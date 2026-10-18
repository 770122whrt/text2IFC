"""Pair-count regression tests; fixtures never represent live repair evidence."""
from __future__ import annotations

import itertools
import json
import concurrent.futures
from pathlib import Path

import pytest

from scripts.ifc_repair import dataset_pairs as pairs
from scripts.ifc_repair.dataset_batch.validation import sha256


def _inventory(count=30):
    return {'targets': {'window': [
        {'guid': f'w{i:02d}', 'ifc_class': 'IfcWindow', 'opening_guid': f'o{i:02d}'}
        for i in range(count)]}, 'properties': []}


def test_full_single_target_traversal_is_not_limited_to_first_six():
    raw = list(pairs.iter_raw_recipes(_inventory(), seed=3, max_deleted=12))
    singles = {r['deletions'][0]['guid'] for r in raw if len(r['deletions']) == 1}
    assert singles == {f'w{i:02d}' for i in range(30)}
    assert len({pairs.recipe_key(r) for r in raw}) == len(raw)


def test_unsupported_shapes_do_not_consume_validation_attempts(monkeypatch):
    rejected = []

    def prepare(recipe):
        if any(t['guid'] in {f'w{i:02d}' for i in range(6)} for t in recipe['deletions']):
            raise ValueError('NO_SUPPORTED_SHAPE_REFERENCE_OR_BASIC_BOX')
        return recipe

    monkeypatch.setattr(pairs, 'prepare_recipe', prepare)
    monkeypatch.setattr(pairs, 'render_prompts', lambda _: {'world': '公开请求', 'host_wall': None})
    monkeypatch.setattr(pairs, '_location_supported', lambda _: True)
    selected = list(itertools.islice(pairs.iter_prepared_recipes(_inventory(), seed=3, rejected=rejected), 8))
    assert len(selected) == 8
    assert len({pairs.recipe_key(r) for _, r in selected}) == 8
    assert rejected
    assert not any(t['guid'] in {f'w{i:02d}' for i in range(6)} for _, r in selected for t in r['deletions'])


def test_pair_modes_count_separately_and_stop_at_odd_quota():
    records = []
    for number in range(13):
        records.extend(pairs.make_pair_records(
            source_id='formal-001', damage_number=number + 1, case_path='a/b',
            model_sha256='a' * 64, request_hashes={'world': 'b' * 64, 'host_wall': 'c' * 64},
            recipe={'deletions': [{'guid': 'x'}], 'property_changes': []}, remaining=25 - len(records)))
    assert len(records) == 25
    assert len({r['damage_id'] for r in records}) == 13
    assert records[-1]['locator_mode'] == 'world'
    assert len({(r['damage_id'], r['locator_mode']) for r in records}) == 25


def test_structural_world_only_and_unique_attribute_targets():
    recipe = {'deletions': [{'guid': 'beam'}], 'property_changes': [{'guid': 'col'}, {'guid': 'col'}]}
    records = pairs.make_pair_records(source_id='formal-022', damage_number=1, case_path='x',
        model_sha256='a' * 64, request_hashes={'world': 'b' * 64}, recipe=recipe, remaining=25)
    assert len(records) == 1 and records[0]['locator_mode'] == 'world'
    assert records[0]['primary_target_count'] == 2 and records[0]['task_kind'] == 'mixed'


def test_absent_classes_are_not_fabricated_and_scope_is_restricted():
    inv = _inventory(2)
    raw = list(pairs.iter_raw_recipes(inv, seed=7, max_deleted=30))
    assert {r['family'] for r in raw} == {'window'}
    assert not any(t['preserve_opening'] for r in raw for t in r['deletions'])
    inv['properties'] = [{'guid': 'wall', 'ifc_class': 'IfcWall', 'before': True, 'value_type': 'IfcBoolean'}]
    assert not any(r['property_changes'] for r in pairs.iter_raw_recipes(inv, seed=7))


def test_failure_and_attempt_cap_remain_in_denominator(monkeypatch, scene_factory, tmp_path):
    reference = scene_factory(tmp_path / 'source.ifc')
    spec = {'source_id': 'formal-002', 'input_path': str(reference), 'source_sha256': sha256(reference)}

    def failed(*args, **kwargs):
        raise ValueError('EXPLICIT_OFFLINE_FAILURE_FIXTURE')

    monkeypatch.setattr(pairs, '_check_damage', failed)
    result = pairs.process_mother(spec, tmp_path, tmp_path / 'production', pairs_per_ifc=25, max_attempts=3)
    assert result['status'] == 'incomplete' and result['stop_reason'] == 'attempt_cap_reached'
    assert result['attempted_cases'] == 3 and not result['pairs']
    assert all(a['status'] == 'failed' for a in result['attempts'])
    assert len(list((tmp_path / 'production/sources/formal-002/private/attempt-errors').glob('*.json'))) == 3


def test_worker_error_cannot_publish_complete_batch(monkeypatch, tmp_path):
    # Mocked orchestration fault fixture; no IFC/native/capability evidence.
    reference = tmp_path / 'opaque.ifc'
    reference.write_text('explicit offline opaque input', encoding='utf-8')
    spec = {'source_id': 'formal-003', 'input_path': str(reference), 'source_sha256': sha256(reference)}

    class FailedPool:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def submit(self, *args, **kwargs):
            future = concurrent.futures.Future()
            future.set_exception(ValueError('EXPLICIT_WORKER_FAILURE_FIXTURE'))
            return future

    monkeypatch.setattr(pairs.concurrent.futures, 'ProcessPoolExecutor', FailedPool)
    result = pairs.run_batch([spec], tmp_path / 'batch', workers=1)
    assert result['status'] == 'incomplete' and result['missing_pairs'] == 25
    assert result['worker_errors'] and result['completed_mothers'] == 0
    assert not (tmp_path / 'batch/public').exists()


@pytest.mark.parametrize('source_id', ['../outside', 'CON', 'trailing.', 'a/b', ''])
def test_unsafe_source_ids_rejected_before_writes(source_id, tmp_path):
    with pytest.raises(ValueError, match='UNSAFE_SOURCE_ID'):
        pairs.process_mother({'source_id': source_id}, tmp_path, tmp_path / 'production')
    assert not (tmp_path / 'production').exists()


def test_actual_scene_generates_25_checked_pairs_and_preserves_source(scene_factory, tmp_path, monkeypatch):
    reference = scene_factory(tmp_path / 'source.ifc', millimetres=True)
    original_hash = sha256(reference)
    spec = {'source_id': 'formal-001', 'input_path': str(reference), 'source_sha256': original_hash}
    result = pairs.process_mother(spec, tmp_path, tmp_path / 'production', pairs_per_ifc=25, max_attempts=30, seed=17)
    assert result['status'] == 'complete' and len(result['pairs']) == 25
    assert result['source_unchanged'] and sha256(reference) == original_hash
    assert 13 <= len(result['cases']) <= 25
    assert result['attempted_cases'] <= 30
    assert all(case['machine_validated'] for case in result['cases'])
    assert {'beam', 'column', 'door_window_beam_column'} <= {c['family'] for c in result['cases']}
    for case in result['cases']:
        folder = tmp_path / 'production' / case['path']
        assert pairs.verify_seal(folder)
        checks = json.loads((folder / 'private/prompt-check.json').read_text(encoding='utf-8'))
        assert all(check['passed'] for check in checks.values())
    with pytest.raises(FileExistsError):
        pairs.process_mother(spec, tmp_path, tmp_path / 'production', pairs_per_ifc=25, max_attempts=30, seed=17)
    def forbidden(*args, **kwargs):
        raise AssertionError('COMPLETE_MOTHER_REEXECUTED')
    for function in ('_check_damage', 'native_validate', 'prepare_inventory'):
        monkeypatch.setattr(pairs, function, forbidden)
    resumed = pairs.process_mother(spec, tmp_path, tmp_path / 'production', pairs_per_ifc=25,
                                  max_attempts=30, seed=17, resume=True)
    assert resumed['status'] == 'complete' and resumed['pairs'] == result['pairs']
    assert resumed['attempted_cases'] == result['attempted_cases']


def test_operating_system_lock_excludes_a_second_writer(tmp_path):
    path = tmp_path / 'lockfile'
    with pairs._exclusive_lock(path):
        with pytest.raises(ValueError, match='ALREADY_RUNNING'):
            with pairs._exclusive_lock(path):
                pytest.fail('concurrent writer entered')
    with pairs._exclusive_lock(path):
        pass


def test_mixed_candidate_inner_loop_honors_stop(monkeypatch):
    consumed = []
    def stream(rows, *, max_deleted):
        for index in range(40):
            consumed.append(index)
            yield [{**row[0], 'preserve_opening': False} for row in rows]
    monkeypatch.setattr(pairs, '_deletion_stream', stream)
    inv = {'targets': {'door': [{'guid': 'd', 'ifc_class': 'IfcDoor'}],
                       'window': [{'guid': 'w', 'ifc_class': 'IfcWindow'}]},
           'properties': [{'guid': 'd', 'ifc_class': 'IfcDoor', 'pset_name': 'Pset_DoorCommon',
                           'property_name': 'Reference', 'before': 'original', 'value_type': 'IfcLabel'}]}
    list(pairs.iter_raw_recipes(inv, seed=1, stopped=lambda: len(consumed) >= 5))
    assert len(consumed) <= 5


def test_direct_execution_dependencies_are_frozen():
    required = {'scripts/ifc_repair/audit_initial_dataset.py',
                'scripts/ifc_repair/repair_comparison/batch_cases.py',
                'scripts/ifc_repair/repair_comparison/budget.py',
                'scripts/ifc_repair/repair_comparison/contracts.py'}
    assert required <= set(pairs._program_bindings())


def test_actual_batch_handoff_with_shared_parent_roots(scene_factory, tmp_path):
    reference = scene_factory(tmp_path / 'source.ifc')
    spec = {'source_id': 'formal-001', 'input_path': str(reference), 'source_sha256': sha256(reference)}
    batch = tmp_path / 'batch'
    result = pairs.run_batch([spec], batch, pairs_per_ifc=3, max_attempts=4, workers=1)
    assert result['status'] == 'complete'
    assert result['machine_validated_pairs'] == 3 and result['public_export']['pairs'] == 3
    assert len(list((batch / 'public').rglob('*.*'))) == 7
    assert (batch / 'private/production/mother-sources.json').is_file()
    assert (batch / 'private/evaluation/export.json').is_file()
    assert sha256(reference) == spec['source_sha256']
