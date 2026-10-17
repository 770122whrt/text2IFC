"""Delivery boundaries use opaque metadata; the final fixture executes native gates."""
from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_request_v4 as request_profile
from scripts.ifc_repair import dataset_supplement as s
from .test_pair_export import opaque_sealed_pair_source


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_deliver')


def hashes(root):
    return {p.relative_to(root).as_posix(): q.sha256(p) for p in root.rglob('*') if p.is_file()}


def checkpoint(root, spec, result, config):
    q.write_json(root / 'private/inventory.json', {'fixture_kind': 'simulated cached inventory'})
    cache = {name: q.sha256(root / name) for name in (
        'private/reference.ifc', 'private/source.json', 'private/source-validation.json', 'private/inventory.json')}
    q.write_json(root / 'private/checkpoint.json', {
        'schema_version': 'text2ifc/dataset-pair-checkpoint/1.0', 'configuration': config,
        'cache_sha256': cache, 'attempts': result['attempts'], 'cases': result['cases'],
        'pairs': result['pairs'], 'candidate_cursor': len(result['attempts']), 'rejected': []})
    q.write_json(root / 'result.json', result)


def accepted(root, folder, recipe):
    q.write_json(folder / 'private/recipe.json', recipe)
    q.seal_case(folder)
    target = root / 'private/attempt-recipes' / (folder.name + '.json')
    q.write_json(target, recipe)
    return {'source_id': root.name, 'case_id': folder.name,
            'path': f'sources/{root.name}/cases/{folder.name}', 'candidate_number': 1,
            'recipe_key': q.recipe_key(recipe), 'family': recipe['family'], 'severity': 'light',
            'status': 'passed', 'machine_validated': True, 'errors': [],
            'model_sha256': q.sha256(folder / 'public/model.ifc'),
            'attempt_recipe_sha256': q.sha256(target),
            'accepted_seal_sha256': q.sha256(folder / 'private/seal.json'),
            'prompt_modes': ['world', 'host_wall'], 'removed_openings': 0,
            'wall_check_applicable': True}


def result(spec, cases, pairs, *, target, reason):
    return {'source_id': spec['source_id'], 'source': spec, 'status': 'complete' if len(pairs) == target else 'incomplete',
            'source_sha256': spec['source_sha256'], 'source_unchanged': True, 'source_native_passed': True,
            'target_pairs': target, 'attempts': cases, 'cases': cases, 'pairs': pairs,
            'attempted_cases': len(cases), 'candidate_rejection_count': 0, 'stop_reason': reason}


def freeze_round(batch, specs, *, repository=q.ROOT):
    production = batch / 'private/production'
    q._freeze_batch(specs, production, repository, pairs_per_ifc=3, max_attempts=30,
                    workers=1, seed=17, bindings=s.BASE_BINDINGS())
    q.write_json(production / 'worker-errors.json', [])
    baseline = s.load_results(production)
    round_root = batch / 'private' / s.ROUND
    bindings = s.program_bindings()
    q.write_json(round_root / 'build.json', {
        'schema_version': s.SCHEMA, 'pairs_per_ifc': 3, 'max_additional_attempts_per_mother': 30,
        'workers': 1, 'sources': specs, 'code_sha256': bindings,
        'first_pass_results': {r['source_id']: q.sha256(production / 'sources' / r['source_id'] / 'result.json')
                               for r in baseline}})
    for name in bindings:
        target = round_root / 'code-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / name, target)


@pytest.fixture
def simulated_batch(opaque_sealed_pair_source, monkeypatch):
    """Small source/program catalogues and IFC/native receipts are explicitly simulated."""
    module = api()
    monkeypatch.setattr(module, 'EXPECTED_SOURCES', 1)
    code = {'scripts/ifc_repair/dataset_pairs.py': q.sha256(Path(q.__file__))}
    monkeypatch.setattr(q, '_program_bindings', lambda: code)
    monkeypatch.setattr(s, 'BASE_BINDINGS', lambda: code)
    production, _, _, folder, pairs = opaque_sealed_pair_source
    batch = production.parents[1]
    source = production / 'sources/formal-021'
    spec = q.read(source / 'private/source.json')
    spec['input_path'] = str(source / 'private/reference.ifc')
    q.write_json(source / 'private/source.json', spec)
    meta = q.read(folder / 'case.json')
    for pair in pairs:
        path = folder / pair['request_relative_path']
        body = path.read_bytes().decode('utf-8-sig')
        path.write_bytes((request_profile.HEADER + '\n' + body).encode('utf-8'))
        pair['request_sha256'] = q.sha256(path)
        meta['prompt_templates'][pair['locator_mode']]['sha256'] = pair['request_sha256']
    q.write_json(folder / 'case.json', meta)
    recipe = {'family': 'window', 'severity': 'light',
              'deletions': [{'guid': 'private-hidden-window', 'ifc_class': 'IfcWindow', 'preserve_opening': False}],
              'property_changes': []}
    row = accepted(source, folder, recipe)
    first = result(spec, [row], pairs, target=3, reason='candidate_catalogue_exhausted')
    checkpoint(source, spec, first, q._configuration(spec, pairs_per_ifc=3, max_attempts=30, seed=17))
    freeze_round(batch, [spec])
    extra_source = batch / 'private' / s.ROUND / 'sources' / spec['source_id']
    for name in q.read(source / 'private/checkpoint.json')['cache_sha256']:
        target = extra_source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    binding = s._baseline_binding(source)
    extra = result(spec, [], [], target=1, reason='candidate_catalogue_exhausted')
    config = {**q._configuration(spec, pairs_per_ifc=1, max_attempts=30, seed=17),
              'code_sha256': s.program_bindings(), 'supplement': binding}
    checkpoint(extra_source, spec, extra, config)
    s.round_status(batch)
    return module, batch, source, extra_source, spec


def add_supplement_case(fixture):
    _, batch, source, extra_source, spec = fixture
    origin = source / 'cases/damage-001'
    folder = extra_source / 'cases/damage-001'
    shutil.copytree(origin, folder)
    (folder / 'public/model.ifc').write_bytes(b'OPAQUE SECOND DAMAGE; NO NATIVE EXECUTION')
    model_hash = q.sha256(folder / 'public/model.ifc')
    meta = q.read(folder / 'case.json')
    meta.update(damaged_sha256=model_hash, generator_extension=s.SCHEMA,
                additional_evidence=[*meta['additional_evidence'], 'private/supplement-binding.json'])
    q.write_json(folder / 'case.json', meta)
    mutation = q.read(folder / 'private/mutation.json')
    mutation.update(damaged_sha256=model_hash,
                    deletions=[{'guid': 'private-another-window', 'ifc_class': 'IfcWindow'}])
    q.write_json(folder / 'private/mutation.json', mutation)
    recipe = {'family': 'window', 'severity': 'light',
              'deletions': [{'guid': 'private-another-window', 'ifc_class': 'IfcWindow', 'preserve_opening': False}],
              'property_changes': []}
    q.write_json(folder / 'private/supplement-binding.json', {
        'schema_version': s.SCHEMA, 'baseline': s._baseline_binding(source), 'code_sha256': s.program_bindings(),
        'geometry_guard': 'text2ifc/dataset-geometry-guard/2.0', 'request_profile': q.PROFILE,
        'source_admission': 'hash-bound first-pass receipt reused'})
    row = accepted(extra_source, folder, recipe)
    pairs = s.rename_pairs(q.make_pair_records(source_id=spec['source_id'], damage_number=1,
        case_path=row['path'], model_sha256=model_hash,
        request_hashes={mode: q.sha256(folder / f'public/request-{mode}.txt') for mode in row['prompt_modes']},
        recipe=recipe, remaining=1))
    extra = result(spec, [row], pairs, target=1, reason='pair_quota_met')
    config = q.read(extra_source / 'private/checkpoint.json')['configuration']
    checkpoint(extra_source, spec, extra, config)
    s.round_status(batch)
    return folder


def test_delivery_under_quota_preserves_rounds_and_is_readback_idempotent(simulated_batch):
    module, batch, source, extra_source, _ = simulated_batch
    before = hashes(source), hashes(extra_source)
    summary = module.deliver_batch(batch)
    assert summary['status'] == 'complete' and summary['quota_complete'] is False
    assert summary['pairs'] == 2 and summary['distinct_damages'] == 1 and summary['missing_pairs'] == 1
    assert summary['catalogue_source_models'] == summary['source_models'] == 1
    assert summary['per_mother'][0]['missing_pairs'] == 1
    assert summary['native_evidence']['fresh_native_validations'] == 0
    assert summary['native_evidence']['source_receipts_reused'] == 1
    assert summary['authoring_request_profile'] == request_profile.SOURCE_PROFILE
    assert summary['request_profile'] == request_profile.PROFILE
    assert summary['request_transforms_checked'] == 2
    assert (hashes(source), hashes(extra_source)) == before
    frozen = hashes(batch)
    assert module.deliver_batch(batch) == module.check_delivery(batch) == summary
    assert hashes(batch) == frozen
    with (batch / 'public/inputs.csv').open(encoding='utf-8', newline='') as stream:
        assert csv.DictReader(stream).fieldnames == ['case_id', 'ifc_path', 'request_path', 'level',
                                                     'primary_target_count', 'task_kind']


def test_new_cases_are_exact_copies_and_do_not_overwrite_old_records(simulated_batch):
    module, batch, source, extra_source, _ = simulated_batch
    origin = add_supplement_case(simulated_batch)
    before = hashes(source), hashes(extra_source)
    summary = module.deliver_batch(batch)
    target = source / 'cases/supplement-r1-damage-001'
    assert q.verify_seal(target) and hashes(target) == hashes(origin)
    assert summary['pairs'] == 3 and summary['supplement_pairs'] == 1
    assert summary['distinct_damages'] == 2 and summary['quota_complete'] is True
    assert all(q.sha256(source / name) == digest for name, digest in before[0].items())
    assert hashes(extra_source) == before[1]
    assert module.check_delivery(batch) == summary


def add_empty_mother(fixture, monkeypatch):
    module, batch, _, _, spec = fixture
    monkeypatch.setattr(module, 'EXPECTED_SOURCES', 2)
    production = batch / 'private/production'
    source = production / 'sources/formal-022'
    source.mkdir()
    (source / 'private').mkdir()
    reference = source / 'private/reference.ifc'
    reference.write_bytes(b'OPAQUE ZERO-PAIR SOURCE; SIMULATED RECEIPTS')
    zero = {**spec, 'source_id': 'formal-022', 'source_sha256': q.sha256(reference), 'input_path': str(reference)}
    q.write_json(source / 'private/source.json', zero)
    receipt = q.read(production / 'sources/formal-021/private/source-validation.json')
    receipt['input_sha256'] = zero['source_sha256']
    q.write_json(source / 'private/source-validation.json', receipt)
    first = result(zero, [], [], target=3, reason='candidate_catalogue_exhausted')
    checkpoint(source, zero, first, q._configuration(zero, pairs_per_ifc=3, max_attempts=30, seed=17))
    freeze_round(batch, [spec, zero])
    extra_source = batch / 'private' / s.ROUND / 'sources' / zero['source_id']
    for name in q.read(source / 'private/checkpoint.json')['cache_sha256']:
        target = extra_source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    config = {**q._configuration(zero, pairs_per_ifc=3, max_attempts=30, seed=17),
              'code_sha256': s.program_bindings(), 'supplement': s._baseline_binding(source)}
    checkpoint(extra_source, zero, result(zero, [], [], target=3, reason='candidate_catalogue_exhausted'), config)
    s.round_status(batch)
    return source


def test_zero_pair_mother_is_catalogued_but_not_counted_as_public_coverage(simulated_batch, monkeypatch):
    module, batch, _, _, _ = simulated_batch
    add_empty_mother(simulated_batch, monkeypatch)
    summary = module.deliver_batch(batch)
    assert summary['catalogue_source_models'] == 2 and summary['source_models'] == 1
    assert summary['mothers_without_pairs'] == ['formal-022'] and summary['missing_pairs'] == 4
    assert summary['native_evidence']['source_receipts_reused'] == 2
    assert summary['public_export']['source_models'] == 1


def test_zero_pair_mother_native_admission_still_blocks_export(simulated_batch, monkeypatch):
    module, batch, _, _, _ = simulated_batch
    source = add_empty_mother(simulated_batch, monkeypatch)
    native = source / 'private/source-validation.json'
    receipt = q.read(native)
    receipt['express_rules'] = False
    q.write_json(native, receipt)
    path = source / 'private/checkpoint.json'
    data = q.read(path)
    data['cache_sha256']['private/source-validation.json'] = q.sha256(native)
    q.write_json(path, data)
    with pytest.raises(ValueError, match='NATIVE_RECEIPT_INVALID'):
        module.deliver_batch(batch)
    assert not (batch / 'public').exists()


@pytest.mark.parametrize('duplicate', ['recipe', 'bytes'])
def test_supplement_cannot_repackage_an_accepted_semantic_recipe_or_damage(simulated_batch, duplicate):
    module, batch, source, extra_source, spec = simulated_batch
    folder = add_supplement_case(simulated_batch)
    original = source / 'cases/damage-001'
    recipe = q.read(folder / 'private/recipe.json')
    mutation = q.read(folder / 'private/mutation.json')
    if duplicate == 'recipe':
        recipe = q.read(original / 'private/recipe.json')
        mutation['deletions'] = q.read(original / 'private/mutation.json')['deletions']
    else:
        shutil.copyfile(original / 'public/model.ifc', folder / 'public/model.ifc')
        meta = q.read(folder / 'case.json')
        meta['damaged_sha256'] = q.sha256(folder / 'public/model.ifc')
        mutation['damaged_sha256'] = meta['damaged_sha256']
        q.write_json(folder / 'case.json', meta)
    q.write_json(folder / 'private/mutation.json', mutation)
    row = accepted(extra_source, folder, recipe)
    pairs = s.rename_pairs(q.make_pair_records(source_id=spec['source_id'], damage_number=1,
        case_path=row['path'], model_sha256=row['model_sha256'],
        request_hashes={mode: q.sha256(folder / f'public/request-{mode}.txt') for mode in row['prompt_modes']},
        recipe=recipe, remaining=1))
    config = q.read(extra_source / 'private/checkpoint.json')['configuration']
    checkpoint(extra_source, spec, result(spec, [row], pairs, target=1, reason='pair_quota_met'), config)
    with pytest.raises(ValueError, match='DUPLICATE_ACCEPTED_'):
        module.deliver_batch(batch)
    assert not (batch / 'public').exists()


@pytest.mark.parametrize('change', ['pause', 'running', 'worker_error', 'missing_result', 'started',
    'source_hash', 'native_findings', 'native_version', 'cache_hash', 'core_snapshot',
    'supplement_snapshot', 'checkpoint_pairs', 'baseline_binding', 'path_escape'])
def test_incomplete_or_changed_inputs_fail_before_public_output(simulated_batch, change):
    module, batch, source, extra_source, _ = simulated_batch
    if change == 'pause':
        (batch / 'PAUSE').write_text('stop', encoding='utf-8')
    elif change in {'running', 'worker_error'}:
        path = batch / 'private' / s.ROUND / 'summary.json'
        data = q.read(path)
        data['status' if change == 'running' else 'worker_errors'] = 'running' if change == 'running' else [{'error': 'kept'}]
        q.write_json(path, data)
    elif change == 'missing_result':
        (extra_source / 'result.json').rename(extra_source / 'missing-result.json')
    elif change == 'source_hash':
        (source / 'private/reference.ifc').write_bytes(b'changed')
    elif change in {'native_findings', 'native_version'}:
        path = source / 'private/source-validation.json'
        data = q.read(path)
        data['finding_count' if change == 'native_findings' else 'ifcopenshell_version'] = 1 if change == 'native_findings' else 'old'
        q.write_json(path, data)
        path = source / 'private/checkpoint.json'
        data = q.read(path)
        data['cache_sha256']['private/source-validation.json'] = q.sha256(source / 'private/source-validation.json')
        q.write_json(path, data)
    elif change in {'core_snapshot', 'supplement_snapshot'}:
        snapshot = source.parents[1] / 'private/code-snapshot' if change == 'core_snapshot' else extra_source.parents[1] / 'code-snapshot'
        (snapshot / 'scripts/ifc_repair/dataset_pairs.py').write_bytes(b'changed')
    else:
        path = source / 'private/checkpoint.json' if change in {'started', 'cache_hash', 'checkpoint_pairs', 'path_escape'} else extra_source / 'private/checkpoint.json'
        data = q.read(path)
        if change == 'started':
            data['attempts'][0]['status'] = 'started'
        elif change == 'cache_hash':
            data['cache_sha256']['private/inventory.json'] = '0' * 64
        elif change == 'checkpoint_pairs':
            data['pairs'] = []
        elif change == 'baseline_binding':
            data['configuration']['supplement']['first_pass_result_sha256'] = '0' * 64
        elif change == 'path_escape':
            data['cases'][0]['path'] = 'sources/formal-021/cases/../../escape'
        q.write_json(path, data)
    with pytest.raises((ValueError, FileNotFoundError)):
        module.deliver_batch(batch)
    assert not (batch / 'public').exists() and not (batch / 'private/evaluation').exists()


@pytest.mark.parametrize('change', ['different_bytes', 'extra_file', 'invalid_seal'])
def test_existing_collection_copy_must_be_exact_and_valid(simulated_batch, change):
    module, batch, source, _, _ = simulated_batch
    origin = add_supplement_case(simulated_batch)
    target = source / 'cases/supplement-r1-damage-001'
    shutil.copytree(origin, target)
    (target / {'different_bytes': 'public/model.ifc', 'extra_file': 'unsealed.txt',
               'invalid_seal': 'private/seal.json'}[change]).write_bytes(b'preserve these bytes')
    before = hashes(target)
    with pytest.raises(ValueError, match='COLLECTION_COPY'):
        module.deliver_batch(batch)
    assert hashes(target) == before and not (batch / 'public').exists()


def test_existing_exact_copy_is_allowed(simulated_batch):
    module, batch, source, _, _ = simulated_batch
    origin = add_supplement_case(simulated_batch)
    target = source / 'cases/supplement-r1-damage-001'
    shutil.copytree(origin, target)
    assert module.deliver_batch(batch)['pairs'] == 3
    assert hashes(origin) == hashes(target)


def test_export_failure_is_retained_and_never_automatically_retried(simulated_batch, monkeypatch):
    module, batch, _, _, _ = simulated_batch
    calls = []
    original = module.exporter.shutil.copyfile
    def fail(*args, **kwargs):
        calls.append(args)
        raise OSError('fixture copy failure')
    monkeypatch.setattr(module.exporter.shutil, 'copyfile', fail)
    with pytest.raises(OSError, match='fixture copy failure'):
        module.deliver_batch(batch)
    assert q.read(batch / 'private/evaluation/export-failed.json')['error']
    assert q.read(batch / 'private/finalization/failed.json')['error']
    frozen = hashes(batch)
    monkeypatch.setattr(module.exporter.shutil, 'copyfile', original)
    with pytest.raises(ValueError, match='INCOMPLETE_OR_FAILED_DELIVERY'):
        module.deliver_batch(batch)
    assert len(calls) == 1 and hashes(batch) == frozen


def test_finished_readback_rejects_later_round_drift(simulated_batch):
    module, batch, _, extra_source, _ = simulated_batch
    module.deliver_batch(batch)
    path = extra_source / 'result.json'
    data = q.read(path)
    data['stop_reason'] = 'cooperative_pause'
    q.write_json(path, data)
    with pytest.raises(ValueError, match='BINDING_CHANGED'):
        module.check_delivery(batch)


def test_code_root_must_be_the_actually_loaded_runtime(simulated_batch, tmp_path):
    module, batch, _, _, _ = simulated_batch
    unrelated = tmp_path / 'pretty-but-unloaded-snapshot'
    unrelated.mkdir()
    with pytest.raises(ValueError, match='CODE_ROOT_NOT_ACTUALLY_LOADED'):
        module.deliver_batch(batch, repository=q.ROOT, code_root=unrelated)
    assert not (batch / 'public').exists()


def test_completed_summary_must_match_immutable_checked_stats(simulated_batch):
    module, batch, _, _, _ = simulated_batch
    module.deliver_batch(batch)
    path = batch / 'private/finalization/summary.json'
    data = q.read(path)
    data['damage_families'] = {'invented': 999}
    q.write_json(path, data)
    with pytest.raises(ValueError, match='DELIVERY_STATS_CHANGED'):
        module.check_delivery(batch)


def test_native_scene_delivery_keeps_actual_schema_express_and_export_gates(scene_factory, tmp_path):
    from scripts.ifc_repair.dataset_deliver_runtime import prepare_runtime, check_runtime
    # Isolate frozen bytes from unrelated concurrent edits in the shared workspace.
    # Production deliver still checks its real 87-entry registry without overrides.
    code_root = tmp_path / 'native-fixture-code'
    frozen = {}
    for name in s.BASE_BINDINGS():
        path = code_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((q.ROOT / name).read_bytes())
        frozen[name] = q.sha256(path)
    for name in ('scripts/ifc_repair/dataset_supplement.py', 'scripts/ifc_repair/dataset_geometry_guard_v2.py'):
        path = code_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((q.ROOT / name).read_bytes())
    reference = scene_factory(tmp_path / 'mother.ifc')
    spec = {'source_id': 'formal-021', 'input_path': str(reference), 'source_sha256': q.sha256(reference)}
    batch = tmp_path / 'native-batch'
    production = batch / 'private/production'
    q._freeze_batch([spec], production, code_root, pairs_per_ifc=3, max_attempts=1,
                    workers=1, seed=17, bindings=frozen)
    bindings = {**frozen, **{name: q.sha256(code_root / name) for name in (
        'scripts/ifc_repair/dataset_supplement.py', 'scripts/ifc_repair/dataset_geometry_guard_v2.py')}}
    extra_root = batch / 'private' / s.ROUND
    q.write_json(extra_root / 'build.json', {'schema_version': s.SCHEMA, 'code_sha256': bindings})
    for name in bindings:
        target = extra_root / 'code-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(code_root / name, target)
    record = prepare_runtime(batch, repository=q.ROOT)
    runtime = Path(record['runtime_root'])
    assert check_runtime(runtime) == prepare_runtime(batch, repository=q.ROOT) == record
    child = '''
import json, shutil, sys
from pathlib import Path
runtime, repository, batch = map(Path, sys.argv[1:4])
sys.path[:0] = [str(runtime), str(runtime/'src'), str(repository/'.deps/python312')]
from scripts.ifc_repair import dataset_pairs as q, dataset_supplement as s, dataset_deliver as d, dataset_request_v4 as profile
d.EXPECTED_SOURCES = 1  # Bounded real scene, no claim of 40-mother coverage.
spec = q.read(batch/'private/production/mother-sources.json')['sources'][0]
production = batch/'private/production'
first = q.process_mother(spec, repository, production, pairs_per_ifc=3, max_attempts=1, seed=17)
q._freeze_batch([spec], production, runtime, pairs_per_ifc=3, max_attempts=1, workers=1, seed=17, bindings=s.BASE_BINDINGS())
q.write_json(production/'worker-errors.json', [])
extra = s.supplement_mother(batch, spec, quota=3, max_attempts=1, seed=17, repository=repository)
round_root = batch/'private'/s.ROUND
q.write_json(round_root/'build.json', {'schema_version':s.SCHEMA,'pairs_per_ifc':3,'max_additional_attempts_per_mother':1,
 'sources':[spec], 'code_sha256':s.program_bindings(), 'first_pass_results':{spec['source_id']:q.sha256(production/'sources'/spec['source_id']/'result.json')}})
s.round_status(batch)
assert first['source_native_passed'] and extra['source_native_passed']
summary = d.deliver_batch(batch, repository=repository, code_root=runtime)
assert summary['pairs']==3 and summary['distinct_damages']==2 and summary['native_evidence']['express_rules']
receipt = q.read(batch/'private/evaluation/export.json')
assert {p['locator_mode'] for p in receipt['pair_provenance']}=={'world','host_wall'}
for p in receipt['pair_provenance']:
 body=(production/p['case_path']/p['request_relative_path']).read_bytes().decode('utf-8-sig')
 assert body.startswith(profile.HEADER if p['locator_mode']=='world' else profile.HOST_HEADER)
 final=(batch/'public'/p['public_row']['request_path']).read_bytes().decode('utf-8')
 assert profile.validate_request(final,body)
assert d.check_delivery(batch, repository=repository, code_root=runtime)==summary
print(json.dumps({'pairs':summary['pairs'],'distinct_damages':summary['distinct_damages'],'actual_q_file':q.__file__}))
'''
    generation = child.split('summary = d.deliver_batch', 1)[0]
    completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', generation, str(runtime), str(q.ROOT), str(batch)],
        cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    # The final runtime binds the completed round plans, not the generation scaffold.
    record = prepare_runtime(batch, repository=q.ROOT, runtime=batch / 'private/delivery-runtime-final')
    runtime = Path(record['runtime_root'])
    delivery = child.split('spec = q.read', 1)[0] + "production = batch/'private/production'\nsummary = d.deliver_batch" + child.split('summary = d.deliver_batch', 1)[1]
    completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', delivery, str(runtime), str(q.ROOT), str(batch)],
        cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    outcome = json.loads(completed.stdout.splitlines()[-1])
    assert outcome['pairs'] == 3 and Path(outcome['actual_q_file']).is_relative_to(runtime)
