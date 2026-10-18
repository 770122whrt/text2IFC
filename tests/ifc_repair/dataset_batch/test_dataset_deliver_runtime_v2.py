"""Startup isolation tests; the historical batch is read only, not finalized."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_deliver_runtime_v2 as runtime_api


@pytest.fixture
def frozen_runtime_batch(tmp_path):
    # Copy already frozen program evidence, not IFC/source/native test claims.
    historical = q.DEFAULT_OUTPUT
    batch = tmp_path / 'batch'
    base = batch / 'private/delivery-runtime'
    shutil.copytree(historical / 'private/delivery-runtime', base)
    record = q.read(base / 'runtime.json')
    record['runtime_root'] = str(base)
    record['batch'] = str(batch)
    q.write_json(base / 'runtime.json', record)
    for folder in ('production', 'supplement-r1'):
        path = batch / 'private' / folder / 'build.json'
        path.parent.mkdir(parents=True)
        shutil.copyfile(historical / 'private' / folder / 'build.json', path)
    return batch, base


def test_bootstrap_imports_use_no_main_source_or_package_fallback(frozen_runtime_batch):
    batch, base = frozen_runtime_batch
    record = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base)
    runtime = Path(record['runtime_root'])
    completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(runtime / 'bootstrap.py'), '--check-imports'],
        cwd=q.ROOT, capture_output=True, text=True, encoding='utf-8', timeout=90)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result['status'] == 'ready'
    assert result['main_project_fallbacks'] == []
    assert result['loaded_project_modules']
    for entry in result['loaded_project_modules'].values():
        path = Path(entry['path'])
        assert path.is_relative_to(runtime)
        assert record['program_sha256'][path.relative_to(runtime).as_posix()] == entry['sha256']
    assert 'text2ifc_knowledge.property_search' in result['loaded_project_modules']
    assert 'scripts.ifc_repair.repair_comparison.batch_cases' in result['loaded_project_modules']
    assert runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base) == record
    assert record['registered_program_sha256'] == q.read(batch / 'private/supplement-r1/build.json')['code_sha256']
    assert record['ancillary_sha256']
    assert not (batch / 'public').exists() and not (batch / 'private/finalization').exists()


@pytest.mark.parametrize('change', ['ancillary', 'unexpected', 'baseline'])
def test_runtime_hash_or_whitelist_drift_is_rejected(frozen_runtime_batch, change):
    batch, base = frozen_runtime_batch
    record = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base)
    runtime = Path(record['runtime_root'])
    if change == 'unexpected':
        (runtime / 'extra.py').write_text('# unexpected\n', encoding='utf-8')
    else:
        name = next(iter(record['ancillary_sha256'] if change == 'ancillary' else record['registered_program_sha256']))
        (runtime / name).write_bytes(b'# changed\n')
    with pytest.raises(ValueError):
        runtime_api.check_runtime(runtime)


def test_declared_extra_entry_module_is_bound_and_cannot_be_replaced(frozen_runtime_batch):
    batch, base = frozen_runtime_batch
    entry = 'scripts.ifc_repair.dataset_deliver_runtime_v2'
    record = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base, extra_modules=[entry])
    assert entry in record['entry_modules']
    assert 'scripts/ifc_repair/dataset_deliver_runtime_v2.py' in record['program_sha256']
    runtime = Path(record['runtime_root'])
    completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(runtime / 'bootstrap.py'),
        '--module', entry, 'check', '--runtime', str(runtime)], cwd=q.ROOT,
        capture_output=True, text=True, encoding='utf-8', timeout=90)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)['runtime_root'] == str(runtime)
    with pytest.raises(ValueError, match='EXISTING_RUNTIME_BINDINGS_DIFFERENT'):
        runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base, extra_modules=[])


def test_main_loaded_code_cannot_be_reported_as_runtime_execution(frozen_runtime_batch):
    batch, base = frozen_runtime_batch
    record = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base)
    with pytest.raises(ValueError, match='PROJECT_MODULE_OUTSIDE_RUNTIME'):
        runtime_api.check_loaded_runtime(Path(record['runtime_root']))


def test_generic_entry_spawn_keeps_child_code_pinned_without_recursive_dispatch(frozen_runtime_batch):
    batch, base = frozen_runtime_batch
    # A read-only actual ProcessPool child checks the original 87-file build;
    # it generates no IFC/case/export and makes no native or Provider call.
    entry = 'scripts.ifc_repair.dataset_extension'
    record = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base, extra_modules=[entry])
    runtime = Path(record['runtime_root'])
    completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(runtime / 'bootstrap.py'),
        '--module', entry, 'probe', '--batch', str(batch), '--repository', str(q.ROOT)],
        cwd=q.ROOT, capture_output=True, text=True, encoding='utf-8', timeout=90)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result['passed'] is True and result['provider_calls'] == 0
    assert result['execution_environment']['runtime_root'] == str(runtime)
    assert result['execution_environment']['loaded_modules']
    assert all(Path(row['path']).is_relative_to(runtime)
        for row in result['execution_environment']['loaded_modules'].values())
    assert not (batch / 'private/extension-r2').exists()


def test_runtime_derivation_preserves_every_already_pinned_program_and_ancestor(frozen_runtime_batch):
    batch, base = frozen_runtime_batch
    first = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=base)
    parent = Path(first['runtime_root'])
    before = q.sha256(parent / 'runtime.json')
    derived = runtime_api.prepare_runtime(batch, repository=q.ROOT, base_runtime=parent,
        runtime=batch / 'private/final-runtime', extra_modules=['scripts.ifc_repair.dataset_deliver_runtime_v2'])
    assert q.sha256(parent / 'runtime.json') == before
    assert derived['base_runtime_manifest_sha256'] == before
    assert derived['ancillary_sha256'] == first['ancillary_sha256']
    assert all(derived['program_sha256'][name] == digest for name, digest in first['program_sha256'].items())
    assert runtime_api.check_runtime(parent) == first
