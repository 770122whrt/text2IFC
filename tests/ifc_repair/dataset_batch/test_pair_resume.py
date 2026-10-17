"""Narrow local resume evidence; fault injection never represents repair capability."""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path

import pytest

from scripts.ifc_repair import dataset_pairs as controller
from scripts.ifc_repair.dataset_batch.validation import sha256


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def hashes(root):
    return {path.relative_to(root).as_posix(): sha256(path)
            for path in root.rglob('*') if path.is_file()}


def recipe_argument(args, kwargs):
    return kwargs['recipe'] if 'recipe' in kwargs else args[-2]


def forbid(monkeypatch, names):
    calls = []
    for name in names:
        def rejected(*args, _name=name, **kwargs):
            calls.append(_name)
            raise AssertionError('CACHED_OR_SPENT_WORK_REEXECUTED:' + _name)
        monkeypatch.setattr(controller, name, rejected)
    return calls


@pytest.fixture
def interrupted_mother(scene_factory, tmp_path, monkeypatch):
    """One real checked damage, then an injected process interruption before damage two."""
    reference = scene_factory(tmp_path / 'mother.ifc')
    spec = {'source_id': 'formal-021', 'input_path': str(reference), 'source_sha256': sha256(reference)}
    production = tmp_path / 'batch/private/production'
    original = controller._check_damage
    recipes = []

    def interrupted(*args, **kwargs):
        recipe = recipe_argument(args, kwargs)
        recipes.append(controller.recipe_key(recipe))
        if len(recipes) == 2:
            raise KeyboardInterrupt('EXPLICIT_LOCAL_PROCESS_INTERRUPTION_FIXTURE')
        result = original(*args, **kwargs)
        assert result[0]['machine_validated'] is True
        return result

    monkeypatch.setattr(controller, '_check_damage', interrupted)
    with pytest.raises(KeyboardInterrupt, match='EXPLICIT_LOCAL_PROCESS_INTERRUPTION_FIXTURE'):
        controller.process_mother(spec, tmp_path, production, pairs_per_ifc=4, max_attempts=6, seed=17)
    root = production / 'sources' / spec['source_id']
    attempts = read(root / 'private/attempts.json')
    assert len(attempts) == len(recipes) == 2 and attempts[0]['status'] == 'passed'
    assert attempts[1]['status'] in {'started', 'failed', 'interrupted'}
    accepted = production / attempts[0]['path']
    assert controller.verify_seal(accepted)
    return {'spec': spec, 'repository': tmp_path, 'production': production, 'root': root,
            'accepted': accepted, 'accepted_hashes': hashes(accepted), 'recipes': recipes,
            'original_check': original, 'attempts': attempts}


def test_resume_preserves_real_sealed_case_skips_interrupted_recipe_and_reuses_admission(
        interrupted_mother, monkeypatch):
    item = interrupted_mother
    admission_calls = forbid(monkeypatch, ('native_validate', 'prepare_inventory'))
    resumed_recipes = []

    def tracked(*args, **kwargs):
        recipe = recipe_argument(args, kwargs)
        resumed_recipes.append(controller.recipe_key(recipe))
        return item['original_check'](*args, **kwargs)

    monkeypatch.setattr(controller, '_check_damage', tracked)
    result = controller.process_mother(item['spec'], item['repository'], item['production'],
                                      pairs_per_ifc=4, max_attempts=6, seed=17, resume=True)
    assert result['status'] == 'complete' and len(result['pairs']) == 4
    assert not admission_calls and resumed_recipes
    assert not set(resumed_recipes) & set(item['recipes'])
    assert hashes(item['accepted']) == item['accepted_hashes']
    assert controller.verify_seal(item['accepted'])
    assert result['attempts'][0] == item['attempts'][0]
    assert result['attempts'][1]['status'] == 'failed'
    assert result['attempts'][1]['machine_validated'] is False
    assert 'interrupt' in json.dumps(result['attempts'][1]).lower()
    assert 3 <= result['attempted_cases'] <= 6
    assert all(row['candidate_number'] > item['attempts'][1]['candidate_number']
               for row in result['attempts'][2:])
    assert len({row['recipe_key'] for row in result['attempts']}) == result['attempted_cases']
    assert sha256(Path(item['spec']['input_path'])) == item['spec']['source_sha256']


@pytest.mark.parametrize('boundary', ['pair_records', 'seal_hash'])
def test_resume_keeps_uncommitted_verified_damage_out_of_acceptance_ledger(
        boundary, scene_factory, tmp_path, monkeypatch):
    """Interrupt real checked output during acceptance preparation, without editing core code."""
    reference = scene_factory(tmp_path / 'mother.ifc')
    spec = {'source_id': 'formal-024', 'input_path': str(reference), 'source_sha256': sha256(reference)}
    production = tmp_path / 'batch/private/production'
    original_check = controller._check_damage
    original_records = controller.make_pair_records
    original_hash = controller.sha256
    checked = {}

    def observed_check(*args, **kwargs):
        result = original_check(*args, **kwargs)
        assert result[0]['machine_validated'] is True
        checked.update(folder=Path(kwargs['folder'] if 'folder' in kwargs else args[-1]),
                       recipe_key=controller.recipe_key(recipe_argument(args, kwargs)))
        return result

    def interrupted_records(*args, **kwargs):
        if boundary == 'pair_records' and checked and not checked.get('interrupted'):
            checked['interrupted'] = True
            raise KeyboardInterrupt('EXPLICIT_ACCEPTANCE_PREPARATION_INTERRUPTION')
        return original_records(*args, **kwargs)

    def interrupted_hash(path):
        if (boundary == 'seal_hash' and checked and not checked.get('interrupted')
                and Path(path) == checked['folder'] / 'private/seal.json'):
            checked['interrupted'] = True
            raise KeyboardInterrupt('EXPLICIT_ACCEPTANCE_PREPARATION_INTERRUPTION')
        return original_hash(path)

    monkeypatch.setattr(controller, '_check_damage', observed_check)
    monkeypatch.setattr(controller, 'make_pair_records', interrupted_records)
    monkeypatch.setattr(controller, 'sha256', interrupted_hash)
    with pytest.raises(KeyboardInterrupt, match='EXPLICIT_ACCEPTANCE_PREPARATION_INTERRUPTION'):
        controller.process_mother(spec, tmp_path, production, pairs_per_ifc=4, max_attempts=6, seed=17)
    assert checked['interrupted'] and controller.verify_seal(checked['folder'])
    uncommitted_hashes = hashes(checked['folder'])
    checkpoint = read(production / 'sources/formal-024/private/checkpoint.json')
    assert len(checkpoint['attempts']) == 1 and not checkpoint['cases'] and not checkpoint['pairs']
    assert {row['case_id'] for row in checkpoint['attempts'] if row['status'] == 'passed'} == {
        row['case_id'] for row in checkpoint['cases']}
    assert checkpoint['attempts'][0]['status'] in {'started', 'failed'}

    monkeypatch.setattr(controller, 'make_pair_records', original_records)
    monkeypatch.setattr(controller, 'sha256', original_hash)
    resumed_keys = []

    def resumed_check(*args, **kwargs):
        resumed_keys.append(controller.recipe_key(recipe_argument(args, kwargs)))
        return original_check(*args, **kwargs)

    monkeypatch.setattr(controller, '_check_damage', resumed_check)
    cached_calls = forbid(monkeypatch, ('native_validate', 'prepare_inventory'))
    result = controller.process_mother(spec, tmp_path, production, pairs_per_ifc=4,
                                      max_attempts=6, seed=17, resume=True)
    assert result['status'] == 'complete' and len(result['pairs']) == 4
    assert not cached_calls and checked['recipe_key'] not in resumed_keys
    assert hashes(checked['folder']) == uncommitted_hashes
    assert result['attempts'][0]['status'] == 'failed'
    assert result['attempts'][0]['machine_validated'] is False
    assert 'interrupt' in json.dumps(result['attempts'][0]).lower()
    assert 3 <= result['attempted_cases'] <= 6
    assert all(row['path'] != checkpoint['attempts'][0]['path'] for row in result['cases'])
    assert all(pair['case_path'] != checkpoint['attempts'][0]['path'] for pair in result['pairs'])
    checkpoint = read(production / 'sources/formal-024/private/checkpoint.json')
    assert checkpoint['attempts'] == result['attempts']
    assert checkpoint['cases'] == result['cases'] and checkpoint['pairs'] == result['pairs']
    assert sha256(reference) == spec['source_sha256']


@pytest.fixture
def exhausted_mother(scene_factory, tmp_path, monkeypatch):
    """Real mother admission plus explicitly simulated damage failures; no accepted IFC evidence."""
    reference = scene_factory(tmp_path / 'mother.ifc')
    spec = {'source_id': 'formal-022', 'input_path': str(reference), 'source_sha256': sha256(reference)}
    production = tmp_path / 'batch/private/production'
    attempted = []

    def failed(*args, **kwargs):
        attempted.append(controller.recipe_key(recipe_argument(args, kwargs)))
        raise ValueError('EXPLICIT_OFFLINE_DAMAGE_FAILURE_FIXTURE')

    monkeypatch.setattr(controller, '_check_damage', failed)
    result = controller.process_mother(spec, tmp_path, production, pairs_per_ifc=4, max_attempts=2, seed=17)
    assert result['attempted_cases'] == len(attempted) == 2
    assert result['status'] == 'incomplete' and result['stop_reason'] == 'attempt_cap_reached'
    root = production / 'sources' / spec['source_id']
    return {'spec': spec, 'repository': tmp_path, 'production': production, 'root': root, 'result': result}


def test_resume_does_not_reset_exhausted_damage_attempt_budget(exhausted_mother, monkeypatch):
    item = exhausted_mother
    evidence = {name: hashes(item['root'] / 'private' / name)
                for name in ('attempt-recipes', 'attempt-errors')}
    calls = forbid(monkeypatch, ('native_validate', 'prepare_inventory', '_check_damage'))
    result = controller.process_mother(item['spec'], item['repository'], item['production'],
                                      pairs_per_ifc=4, max_attempts=2, seed=17, resume=True)
    assert not calls
    assert result['status'] == 'incomplete' and result['stop_reason'] == 'attempt_cap_reached'
    assert result['attempted_cases'] == 2 and not result['pairs']
    assert result['attempts'] == item['result']['attempts']
    assert all(row['status'] == 'failed' for row in result['attempts'])
    assert {name: hashes(item['root'] / 'private' / name) for name in evidence} == evidence


@pytest.mark.parametrize('change', ['seed', 'pairs_per_ifc', 'max_attempts', 'code_binding', 'source'])
def test_resume_rejects_configuration_code_and_source_drift(exhausted_mother, change, monkeypatch):
    item = exhausted_mother
    options = {'pairs_per_ifc': 4, 'max_attempts': 2, 'seed': 17, 'resume': True}
    if change in {'seed', 'pairs_per_ifc', 'max_attempts'}:
        options[change] += 1
    elif change == 'code_binding':
        bindings = controller._program_bindings()
        bindings[next(iter(bindings))] = '0' * 64
        # Simulated code-binding fault; no repository source is edited.
        monkeypatch.setattr(controller, '_program_bindings', lambda: dict(bindings))
    else:
        with Path(item['spec']['input_path']).open('ab') as stream:
            stream.write(b'\nEXPLICIT_SOURCE_DRIFT_FIXTURE\n')
    calls = forbid(monkeypatch, ('native_validate', 'prepare_inventory', '_check_damage'))
    with pytest.raises(ValueError):
        controller.process_mother(item['spec'], item['repository'], item['production'], **options)
    assert not calls
    assert len(read(item['root'] / 'private/attempts.json')) == 2


def test_resume_rejects_accepted_seal_drift_before_new_work(interrupted_mother, monkeypatch):
    item = interrupted_mother
    path = item['accepted'] / 'private/seal.json'
    seal = read(path)
    seal['sha256']['case.json'] = '0' * 64
    path.write_text(json.dumps(seal) + '\n', encoding='utf-8')
    calls = forbid(monkeypatch, ('native_validate', 'prepare_inventory', '_check_damage'))
    with pytest.raises(ValueError):
        controller.process_mother(item['spec'], item['repository'], item['production'],
                                  pairs_per_ifc=4, max_attempts=6, seed=17, resume=True)
    assert not calls
    assert len(read(item['root'] / 'private/attempts.json')) == 2


def test_run_batch_resume_keeps_failure_denominator_and_same_root(scene_factory, tmp_path, monkeypatch):
    """Inline pool and injected damage failures test bookkeeping, never live repair behavior."""
    reference = scene_factory(tmp_path / 'mother.ifc')
    spec = {'source_id': 'formal-023', 'input_path': str(reference), 'source_sha256': sha256(reference)}
    batch = tmp_path / 'batch'

    class InlinePool:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def submit(self, function, *args, **kwargs):
            future = concurrent.futures.Future()
            try:
                future.set_result(function(*args, **kwargs))
            except Exception as exc:
                future.set_exception(exc)
            return future

    def failed(*args, **kwargs):
        raise ValueError('EXPLICIT_OFFLINE_BATCH_DAMAGE_FAILURE_FIXTURE')

    monkeypatch.setattr(controller.concurrent.futures, 'ProcessPoolExecutor', InlinePool)
    monkeypatch.setattr(controller, '_check_damage', failed)
    initial = controller.run_batch([spec], batch, pairs_per_ifc=4, max_attempts=2, workers=1, seed=17)
    assert initial['status'] == 'incomplete'
    assert initial['attempted_cases'] == initial['failed_attempts'] == 2
    snapshots = hashes(batch / 'private/production/private/code-snapshot')
    calls = forbid(monkeypatch, ('native_validate', 'prepare_inventory', '_check_damage'))
    resumed = controller.run_batch([spec], batch, pairs_per_ifc=4, max_attempts=2,
                                   workers=1, seed=17, resume=True)
    assert not calls and resumed['status'] == 'incomplete'
    assert resumed['attempted_cases'] == resumed['failed_attempts'] == 2
    assert resumed['machine_validated_pairs'] == 0 and resumed['missing_pairs'] == 4
    assert not resumed['worker_errors']
    assert hashes(batch / 'private/production/private/code-snapshot') == snapshots
    assert not (batch / 'public').exists()
