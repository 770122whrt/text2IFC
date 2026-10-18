"""Deliver a finished offline first pass and supplement without requiring full quota.

Only new collection copies and private/finalization records are created. The two
rounds' checkpoints/results remain immutable. Native, prompt, wall and mesh
receipts are hash-bound and reused; this controller does not execute a Provider,
rerun IFC validation, or update the batch's human report/root summary.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair import dataset_pair_export as exporter
from scripts.ifc_repair import dataset_pair_export_v2 as handoff
from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_request_v4 as request_profile
from scripts.ifc_repair import dataset_supplement as s
from scripts.ifc_repair.dataset_batch import engine
from scripts.ifc_repair.repair_comparison.batch_cases import _pair_safe_path

SCHEMA = 'text2ifc/dataset-offline-delivery/1.0'
EXPECTED_SOURCES = 40
CACHE_FILES = {'private/reference.ifc', 'private/source.json',
               'private/source-validation.json', 'private/inventory.json'}
TERMINAL_REASONS = {'pair_quota_met', 'attempt_cap_reached', 'candidate_catalogue_exhausted'}


def _require(condition, reason):
    exporter._require(condition, reason)


def _read(path, bindings):
    exporter._bind(path, bindings)
    return q.read(path)


def _write_new(path, value):
    path = _pair_safe_path(path)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def _file(root, relative):
    return exporter._file(root, relative)


def _program(build, snapshot, expected, bindings, code_root):
    _require(isinstance(build.get('code_sha256'), dict) and build['code_sha256'] == expected,
             'FROZEN_PROGRAM_BINDINGS_CHANGED')
    for name, digest in expected.items():
        exporter._bind(_file(code_root, name), bindings, digest)
        exporter._bind(_file(snapshot, name), bindings, digest)


def _index(rows, expected, root):
    _require(isinstance(rows, list) and len(rows) == len(expected), 'ROUND_RESULTS_NOT_FINISHED')
    ids = [row.get('source_id') for row in rows if isinstance(row, dict)]
    _require(len(ids) == len(rows) and len(set(ids)) == len(ids) and set(ids) == set(expected),
             'ROUND_SOURCE_SET_MISMATCH')
    folders = {_pair_safe_path(path).name for path in (root / 'sources').iterdir()}
    _require(folders == set(expected), 'ROUND_SOURCE_DIRECTORY_SET_MISMATCH')
    return {row['source_id']: row for row in rows}


def _terminal(row, quota, cap):
    _require(row.get('status') in {'complete', 'incomplete'} and row.get('stop_reason') in TERMINAL_REASONS,
             'ROUND_NOT_TERMINAL')
    _require(row.get('target_pairs') == quota and isinstance(row.get('pairs'), list)
             and len(row['pairs']) <= quota and isinstance(row.get('attempts'), list)
             and row.get('attempted_cases') == len(row['attempts']) <= cap,
             'ROUND_QUOTA_OR_ATTEMPT_COUNT_INVALID')
    complete = len(row['pairs']) == quota
    _require((row['status'] == 'complete') == complete
             and (row['stop_reason'] == 'pair_quota_met') == complete, 'ROUND_TERMINAL_QUOTA_MISMATCH')
    if row['stop_reason'] == 'attempt_cap_reached':
        _require(len(row['attempts']) == cap, 'ROUND_ATTEMPT_CAP_NOT_REACHED')
    if row['stop_reason'] == 'candidate_catalogue_exhausted':
        _require(len(row['attempts']) < cap, 'ROUND_EXHAUSTED_AFTER_ATTEMPT_CAP')
    _require(all(a.get('status') in {'passed', 'failed'} for a in row['attempts']),
             'ROUND_HAS_UNCOMMITTED_ATTEMPT')


def _source(root, spec, bindings):
    checkpoint = _read(_file(root, 'private/checkpoint.json'), bindings)
    _require(checkpoint.get('schema_version') == 'text2ifc/dataset-pair-checkpoint/1.0',
             'CHECKPOINT_SCHEMA_INVALID')
    cache = checkpoint.get('cache_sha256')
    _require(isinstance(cache, dict) and set(cache) == CACHE_FILES, 'SOURCE_CACHE_SET_INVALID')
    for name, digest in cache.items():
        exporter._bind(_file(root, name), bindings, digest)
    _require(q.read(root / 'private/source.json') == spec, 'SOURCE_METADATA_BINDING_CHANGED')
    exporter._bind(_file(root, 'private/reference.ifc'), bindings, spec['source_sha256'])
    admission = q.read(root / 'private/source-validation.json')
    exporter._native(admission)
    _require(admission.get('input_sha256') == spec['source_sha256'], 'SOURCE_NATIVE_HASH_MISMATCH')
    _require(0 < (root / 'private/reference.ifc').stat().st_size < exporter.MAX_IFC_BYTES,
             'SOURCE_SIZE_INVALID')
    return checkpoint


def _mother(round_root, spec, row, config, bindings, *, supplement=False):
    source = round_root / 'sources' / spec['source_id']
    _read(_file(source, 'result.json'), bindings)
    _terminal(row, config['pairs_per_ifc'], config['max_attempts'])
    _require(row.get('source') == spec and row.get('source_sha256') == spec['source_sha256']
             and row.get('source_unchanged') is True and row.get('source_native_passed') is True,
             'RESULT_SOURCE_BINDING_INVALID')
    checkpoint = _source(source, spec, bindings)
    _require(checkpoint.get('configuration') == config, 'CHECKPOINT_CONFIGURATION_CHANGED')
    _require(all(checkpoint.get(key) == row.get(key) for key in ('cases', 'pairs', 'attempts')),
             'CHECKPOINT_RESULT_LEDGER_MISMATCH')
    accepted = [a for a in row['attempts'] if a['status'] == 'passed']
    _require(isinstance(row.get('cases'), list) and accepted == row['cases'], 'ACCEPTED_CASE_LEDGER_INVALID')
    _require(type(checkpoint.get('candidate_cursor')) is int and checkpoint['candidate_cursor'] >= 0
             and isinstance(checkpoint.get('rejected'), list)
             and row.get('candidate_rejection_count') == len(checkpoint['rejected']), 'CANDIDATE_LEDGER_INVALID')
    recipe_keys, damaged_bytes, pairs, candidate_numbers = set(), set(), [], []
    for number, attempt in enumerate(row['attempts'], 1):
        name = f'damage-{number:03d}'
        expected_path = f'sources/{spec["source_id"]}/cases/{name}'
        _require(attempt.get('source_id') == spec['source_id'] and attempt.get('case_id') == name
                 and attempt.get('path') == expected_path, 'ATTEMPT_PATH_INVALID')
        candidate_numbers.append(attempt.get('candidate_number'))
        recipe_path = _file(source, f'private/attempt-recipes/{name}.json')
        exporter._bind(recipe_path, bindings, attempt.get('attempt_recipe_sha256'))
        recipe = q.read(recipe_path)
        _require(q.recipe_key(recipe) == attempt.get('recipe_key'), 'ATTEMPT_RECIPE_KEY_CHANGED')
        if attempt['status'] != 'passed':
            _require(attempt.get('machine_validated') is False, 'FAILED_ATTEMPT_MARKED_VALID')
            continue
        _require(attempt.get('machine_validated') is True, 'ACCEPTED_ATTEMPT_NOT_VALID')
        case = source / 'cases' / name
        exporter._bind(_file(case, 'private/seal.json'), bindings, attempt.get('accepted_seal_sha256'))
        _require(q.verify_seal(case), 'ACCEPTED_CASE_SEAL_CHANGED')
        sealed_recipe = q.read(_file(case, 'private/recipe.json'))
        _require(q.recipe_key(sealed_recipe) == attempt['recipe_key'] and sealed_recipe == recipe,
                 'ACCEPTED_CASE_RECIPE_CHANGED')
        mutation = q.read(_file(case, 'private/mutation.json'))
        _require(q.recipe_key(mutation) == attempt['recipe_key'] and attempt.get('family') == recipe.get('family'),
                 'ACCEPTED_MUTATION_RECIPE_CHANGED')
        _require(attempt['recipe_key'] not in recipe_keys, 'DUPLICATE_ACCEPTED_RECIPE')
        _require(attempt.get('model_sha256') not in damaged_bytes, 'DUPLICATE_ACCEPTED_DAMAGE_BYTES')
        recipe_keys.add(attempt['recipe_key'])
        damaged_bytes.add(attempt.get('model_sha256'))
        modes = attempt.get('prompt_modes')
        _require(isinstance(modes, list) and len(set(modes)) == len(modes)
                 and 'world' in modes and set(modes) <= {'world', 'host_wall'}, 'ACCEPTED_MODES_INVALID')
        records = q.make_pair_records(source_id=spec['source_id'], damage_number=number,
            case_path=expected_path, model_sha256=attempt['model_sha256'],
            request_hashes={mode: q.sha256(_file(case, f'public/request-{mode}.txt')) for mode in modes},
            recipe=recipe, remaining=config['pairs_per_ifc'] - len(pairs))
        if supplement:
            records = s.rename_pairs(records)
        _require(bool(records), 'ACCEPTED_CASE_WITHOUT_PAIR')
        checked = exporter._case(round_root, records[0], bindings)  # All original native/EXPRESS/export gates.
        _require(checked['model_sha256'] == attempt['model_sha256']
                 and set(checked['requests']) == set(modes), 'ACCEPTED_CASE_BINDING_CHANGED')
        if supplement:
            binding_path = _file(case, 'private/supplement-binding.json')
            receipt = _read(binding_path, bindings)
            _require(receipt.get('schema_version') == s.SCHEMA
                     and receipt.get('baseline') == config['supplement']
                     and receipt.get('code_sha256') == config['code_sha256']
                     and receipt.get('geometry_guard') == 'text2ifc/dataset-geometry-guard/2.0'
                     and receipt.get('request_profile') == q.PROFILE,
                     'SUPPLEMENT_CASE_BINDING_CHANGED')
        pairs.extend(records)
    _require(all(type(n) is int and n > 0 for n in candidate_numbers)
             and candidate_numbers == sorted(set(candidate_numbers))
             and (not candidate_numbers or checkpoint['candidate_cursor'] >= candidate_numbers[-1]),
             'CANDIDATE_CURSOR_INVALID')
    _require(pairs == row['pairs'], 'RESULT_PAIR_MAPPING_CHANGED')
    return checkpoint


def _round_stats(name, rows):
    return {'name': name, 'mothers': len(rows), 'pairs': sum(len(r['pairs']) for r in rows),
            'distinct_damages': sum(len(r['cases']) for r in rows),
            'attempted_cases': sum(r['attempted_cases'] for r in rows),
            'failed_attempts': sum(a['status'] == 'failed' for r in rows for a in r['attempts']),
            'candidate_rejections': sum(r['candidate_rejection_count'] for r in rows),
            'stop_reasons': dict(Counter(r['stop_reason'] for r in rows)), 'worker_errors': []}


def _code_environment(repository, code_root=None):
    code_root = _pair_safe_path(Path(code_root or q.ROOT))
    anchors = {'scripts/ifc_repair/dataset_pairs.py': Path(q.__file__),
        'scripts/ifc_repair/dataset_supplement.py': Path(s.__file__),
        'scripts/ifc_repair/dataset_batch/engine.py': Path(engine.__file__),
        'scripts/ifc_repair/dataset_pair_export.py': Path(exporter.__file__),
        'scripts/ifc_repair/dataset_pair_export_v2.py': Path(handoff.__file__),
        'scripts/ifc_repair/dataset_request_v4.py': Path(request_profile.__file__),
        'scripts/ifc_repair/dataset_deliver.py': Path(__file__)}
    _require(q.ROOT.resolve() == code_root and s.ROOT.resolve() == code_root
        and all(path.resolve() == code_root / name for name, path in anchors.items()),
        'CODE_ROOT_NOT_ACTUALLY_LOADED')
    loaded = {name: str(path.resolve()) for name, path in anchors.items()}
    for relative in s.program_bindings():
        name = relative.removeprefix('src/').removesuffix('.py').replace('/', '.').removesuffix('.__init__')
        module = sys.modules.get(name)
        if module is not None and getattr(module, '__file__', None):
            actual = Path(module.__file__).resolve()
            _require(actual == code_root / relative, 'MIXED_LOADED_PROGRAM_ROOT:' + name)
            loaded[relative] = str(actual)
    return code_root, {'code_root': str(code_root), 'source_repository': str(repository),
        'loaded_modules': dict(sorted(loaded.items())), 'scope': 'Actual loaded registered modules checked; '
        'all frozen program bytes checked independently against both round snapshots.'}


def _collect_inputs(batch, repository, code_root):
    _require(not (batch / 'PAUSE').exists(), 'PAUSED_BATCH_CANNOT_BE_DELIVERED')
    production = batch / 'private/production'
    extra_root = batch / 'private' / s.ROUND
    bindings = {}
    exporter._bind(Path(__file__), bindings)
    for value, digest in handoff.transform_program_bindings().items():
        exporter._bind(Path(value), bindings, digest)
    manifest = code_root / 'runtime.json'
    if manifest.exists():
        runtime = _read(manifest, bindings)
        _require(runtime.get('status') == 'prepared' and runtime.get('runtime_root') == str(code_root)
                 and runtime.get('repository') == str(repository) and runtime.get('batch') == str(batch)
                 and runtime.get('round_build_sha256') == {
                     'first_pass': q.sha256(_file(production, 'build.json')),
                     s.ROUND: q.sha256(_file(extra_root, 'build.json'))}, 'PINNED_RUNTIME_MANIFEST_INVALID')
        for name, digest in runtime['program_sha256'].items():
            exporter._bind(_file(code_root, name), bindings, digest)
    build = _read(_file(production, 'build.json'), bindings)
    _require(build.get('schema_version') == q.SCHEMA and type(build.get('pairs_per_ifc')) is int
             and 1 <= build['pairs_per_ifc'] <= 25 and type(build.get('max_attempts_per_ifc')) is int
             and 1 <= build['max_attempts_per_ifc'] <= 30 and build.get('request_profile') == q.PROFILE
             and build.get('ifcopenshell_version') == q.ifcopenshell.version
             and build.get('provider_calls') == 0, 'FIRST_PASS_BUILD_INVALID')
    _require(build.get('core_program_sha256') == q.program_hash(), 'FROZEN_CORE_PROGRAM_CHANGED')
    _program(build, production / 'private/code-snapshot', s.BASE_BINDINGS(), bindings, code_root)
    catalogue = _read(_file(production, 'mother-sources.json'), bindings)
    specs = catalogue.get('sources')
    _require(catalogue.get('schema_version') == q.SCHEMA and isinstance(specs, list)
             and len(specs) == EXPECTED_SOURCES and all(isinstance(spec, dict)
             and q._valid_source_id(spec.get('source_id')) for spec in specs), 'SOURCE_CATALOGUE_INVALID')
    ids = [spec['source_id'] for spec in specs]
    _require(len({sid.casefold() for sid in ids}) == len(ids), 'DUPLICATE_SOURCE_ID')
    _require(_read(_file(production, 'worker-errors.json'), bindings) == [], 'FIRST_PASS_WORKER_ERRORS')
    baseline = s.load_results(production)
    first = _index(baseline, ids, production)
    for spec in specs:
        value = spec.get('input_path')
        _require(isinstance(value, str) and bool(value), 'SOURCE_INPUT_PATH_INVALID')
        source_path = Path(value)
        source_path = _pair_safe_path(source_path) if source_path.is_absolute() else _file(repository, value)
        exporter._bind(source_path, bindings, spec.get('source_sha256'))
        config = {'source_sha256': spec['source_sha256'], 'source_id': spec['source_id'],
                  'pairs_per_ifc': build['pairs_per_ifc'], 'max_attempts': build['max_attempts_per_ifc'],
                  'seed': build['seed'], 'profile': q.PROFILE, 'code_sha256': build['code_sha256']}
        _mother(production, spec, first[spec['source_id']], config, bindings)
    extra_build = _read(_file(extra_root, 'build.json'), bindings)
    _require(extra_build.get('schema_version') == s.SCHEMA
             and extra_build.get('pairs_per_ifc') == build['pairs_per_ifc']
             and type(extra_build.get('max_additional_attempts_per_mother')) is int
             and 1 <= extra_build['max_additional_attempts_per_mother'] <= 30, 'SUPPLEMENT_BUILD_INVALID')
    _program(extra_build, extra_root / 'code-snapshot', s.program_bindings(), bindings, code_root)
    eligible = [spec for spec in specs if len(first[spec['source_id']]['pairs']) < build['pairs_per_ifc']]
    _require(extra_build.get('sources') == eligible and extra_build.get('first_pass_results') == {
        sid: bindings[str(production / 'sources' / sid / 'result.json')] for sid in ids},
        'SUPPLEMENT_FIRST_PASS_BINDING_CHANGED')
    supplements = s.load_results(extra_root)
    extra = _index(supplements, [spec['source_id'] for spec in eligible], extra_root)
    summary = _read(_file(extra_root, 'summary.json'), bindings)
    _require(summary.get('schema_version') == s.SCHEMA and summary.get('status') == 'finished'
             and summary.get('worker_errors') == [] and summary.get('mothers_finished') == len(eligible)
             and summary.get('mother_round_target') == len(eligible) and summary.get('provider_calls') == 0,
             'SUPPLEMENT_NOT_FINISHED_OR_WORKER_ERRORS')
    for spec in eligible:
        source = production / 'sources' / spec['source_id']
        config = {'source_sha256': spec['source_sha256'], 'source_id': spec['source_id'],
                  'pairs_per_ifc': build['pairs_per_ifc'] - len(first[spec['source_id']]['pairs']),
                  'max_attempts': extra_build['max_additional_attempts_per_mother'],
                  'seed': build['seed'], 'profile': q.PROFILE, 'code_sha256': extra_build['code_sha256'],
                  'supplement': s._baseline_binding(source)}
        _mother(extra_root, spec, extra[spec['source_id']], config, bindings, supplement=True)
    merged = s.merge_results(baseline, supplements, quota=build['pairs_per_ifc'])
    pairs = [p for row in merged for p in row['pairs']]
    cases = [c for row in merged for c in row['cases']]
    keys = [(first[row['source_id']]['source_sha256'], case['recipe_key']) for row in merged for case in row['cases']]
    _require(len(set(keys)) == len(keys), 'DUPLICATE_ACCEPTED_RECIPE')
    _require(len({c['model_sha256'] for c in cases}) == len(cases), 'DUPLICATE_ACCEPTED_DAMAGE_BYTES')
    _require(bool(pairs), 'NO_PUBLIC_PAIRS')
    levels = Counter(exporter.budget_level_for_primary_targets(p['primary_target_count']) for p in pairs)
    rounds = [_round_stats('first_pass', baseline), _round_stats(s.ROUND, supplements)]
    _require(summary.get('first_pass_pairs') == rounds[0]['pairs']
             and summary.get('supplement_pairs') == rounds[1]['pairs']
             and summary.get('pairs_total') == len(pairs)
             and summary.get('supplement_damages') == rounds[1]['distinct_damages']
             and summary.get('supplement_attempts') == rounds[1]['attempted_cases']
             and summary.get('supplement_failures') == rounds[1]['failed_attempts'], 'SUPPLEMENT_SUMMARY_COUNTS_CHANGED')
    stats = {'pairs': len(pairs), 'distinct_damages': len(cases),
        'source_models': len({p['source_id'] for p in pairs}), 'catalogue_source_models': len(specs),
        'pairs_per_ifc': build['pairs_per_ifc'], 'target_pairs': len(specs) * build['pairs_per_ifc'],
        'quota_complete': all(len(row['pairs']) == build['pairs_per_ifc'] for row in merged),
        'missing_pairs': len(specs) * build['pairs_per_ifc'] - len(pairs),
        'completed_mothers': sum(len(row['pairs']) == build['pairs_per_ifc'] for row in merged),
        'mothers_without_pairs': [r['source_id'] for r in merged if not r['pairs']],
        'first_pass_pairs': rounds[0]['pairs'], 'supplement_pairs': rounds[1]['pairs'],
        'attempted_cases': sum(r['attempted_cases'] for r in rounds),
        'failed_attempts': sum(r['failed_attempts'] for r in rounds),
        'candidate_rejections': sum(r['candidate_rejections'] for r in rounds),
        'failed_counts_by_round': {r['name']: r['failed_attempts'] for r in rounds},
        'supplement_rounds': [rounds[1]], 'damage_families': dict(Counter(c['family'] for c in cases)),
        'locator_modes': dict(Counter(p['locator_mode'] for p in pairs)),
        'pair_task_kinds': dict(Counter(p['task_kind'] for p in pairs)), 'budget_levels': dict(levels),
        'removed_openings_checked': sum(c.get('removed_openings', 0) for c in cases),
        'wall_checked_damages': sum(c.get('wall_check_applicable') is True for c in cases),
        'per_mother': [{'source_id': r['source_id'], 'pairs': len(r['pairs']), 'distinct_damages': len(r['cases']),
            'missing_pairs': build['pairs_per_ifc'] - len(r['pairs']), 'attempted_cases': r['attempted_cases'],
            'failed_attempts': sum(a['status'] == 'failed' for a in r['attempts']),
            'first_pass_stop_reason': first[r['source_id']]['stop_reason'],
            'supplement_stop_reason': extra[r['source_id']]['stop_reason'] if r['source_id'] in extra else None,
            'stop_reason': r['stop_reason']} for r in merged],
        'native_evidence': {'schema': 'IFC2X3', 'express_rules': True,
            'ifcopenshell_version': q.ifcopenshell.version, 'source_receipts_reused': len(specs),
            'supplement_source_receipts_reused': len(eligible), 'case_receipts_reused': len(cases),
            'fresh_native_validations': 0, 'fresh_source_sha_checks': len(specs),
            'fresh_full_source_ifc_reopens': 0, 'fresh_seal_and_receipt_binding_checks': len(cases),
            'scope': 'All catalogued source SHA/cache and same-version zero-finding schema+EXPRESS receipts checked; '
                     'native/prompt/wall/mesh evidence reused, no native rerun.'},
        'provider_calls': 0, 'system_repair_tested': False, 'human_reviewed_pairs': 0,
        'authoring_request_profile': q.PROFILE, 'request_profile': request_profile.PROFILE,
        'request_transforms_checked': len(pairs), 'worker_errors': []}
    round_bindings = [{'name': name, 'root': str(root), 'build_sha256': bindings[str(root / 'build.json')],
                       'code_sha256': plan['code_sha256'], **record}
                      for name, root, plan, record in (
                          ('first_pass', production, build, rounds[0]), (s.ROUND, extra_root, extra_build, rounds[1]))]
    return merged, pairs, bindings, stats, round_bindings


def _tree(folder):
    folder = _pair_safe_path(folder)
    _require(folder.is_dir(), 'COLLECTION_COPY_DIRECTORY_MISSING')
    files = {}
    directories = []
    for entry in sorted(folder.rglob('*')):
        path = _pair_safe_path(entry)
        relative = path.relative_to(folder).as_posix()
        exporter._relative(relative)
        if path.is_file():
            files[relative] = q.sha256(path)
        else:
            _require(path.is_dir(), 'COLLECTION_COPY_UNSUPPORTED_ENTRY')
            directories.append(relative)
    return {'files': files, 'directories': directories}


def _collect_copies(batch, merged, bindings):
    copies = []
    for mother in merged:
        for case in mother['cases']:
            if case.get('attempt_round') != s.ROUND:
                continue
            origin = _pair_safe_path(batch / 'private' / s.ROUND / exporter._relative(case['origin_path']))
            target = _pair_safe_path(batch / 'private/production' / exporter._relative(case['path']))
            expected = _tree(origin)
            if target.exists():
                _require(q.verify_seal(target) and _tree(target) == expected, 'COLLECTION_COPY_EXISTS_DIFFERENT')
            else:
                shutil.copytree(origin, target, copy_function=shutil.copyfile)
            _require(q.verify_seal(target) and _tree(origin) == _tree(target) == expected,
                     'COLLECTION_COPY_CHANGED')
            for relative, digest in expected['files'].items():
                exporter._bind(_file(origin, relative), bindings, digest)
                exporter._bind(_file(target, relative), bindings, digest)
            copies.append({'origin': origin.relative_to(batch).as_posix(),
                           'target': target.relative_to(batch).as_posix(), **expected})
    return copies


def _recheck(bindings):
    for value, digest in bindings.items():
        path = _pair_safe_path(Path(value))
        _require(path.is_file() and q.sha256(path) == exporter._digest(digest),
                 'DELIVERY_BINDING_CHANGED:' + value)


def _check_locked(batch, repository, code_root=None):
    final = batch / 'private/finalization'
    _require((final / 'summary.json').is_file() and not (final / 'failed.json').exists()
             and not (batch / 'private/evaluation/export-failed.json').exists(), 'INCOMPLETE_OR_FAILED_DELIVERY')
    summary = q.read(_file(final, 'summary.json'))
    _require(summary.get('schema_version') == SCHEMA and summary.get('status') == 'complete',
             'DELIVERY_SUMMARY_INVALID')
    expected_authority = {str(path) for path in (
        final / 'collection.json', final / 'pairs.json', final / 'checks.json', batch / 'private/evaluation/export.json')}
    _require(isinstance(summary.get('authority_sha256'), dict)
             and set(summary['authority_sha256']) == expected_authority, 'DELIVERY_AUTHORITY_SET_CHANGED')
    _recheck(summary['authority_sha256'])
    checks = q.read(_file(final, 'checks.json'))
    control_fields = {'schema_version', 'passed', 'core_and_round_programs_unchanged', 'all_sources_checked',
        'terminal_rounds_only', 'case_seals_checked', 'semantic_recipes_and_damage_bytes_unique', 'source_cache_bindings_checked'}
    _require(checks.get('schema_version') == SCHEMA and all(checks.get(key) is True for key in control_fields - {'schema_version'})
             and all(summary.get(key) == value for key, value in checks.items() if key not in control_fields),
             'DELIVERY_STATS_CHANGED')
    collection = q.read(_file(final, 'collection.json'))
    _require(collection.get('schema_version') == SCHEMA and collection.get('batch') == str(batch)
             and collection.get('status') == 'collected', 'COLLECTION_RECEIPT_INVALID')
    _, environment = _code_environment(repository, code_root)
    _require(collection.get('execution_environment') == environment, 'DELIVERY_LOADED_ENVIRONMENT_CHANGED')
    _require(not (batch / 'PAUSE').exists(), 'PAUSED_BATCH_CANNOT_BE_DELIVERED')
    _recheck(collection['bound_hashes'])
    for receipt in collection['copied_cases']:
        origin = _pair_safe_path(batch / exporter._relative(receipt['origin']))
        target = _pair_safe_path(batch / exporter._relative(receipt['target']))
        expected = {key: receipt[key] for key in ('files', 'directories')}
        _require(q.verify_seal(origin) and q.verify_seal(target)
                 and _tree(origin) == _tree(target) == expected, 'COLLECTION_COPY_CHANGED')
    pairs = q.read(_file(final, 'pairs.json'))
    receipt = q.read(_file(batch / 'private/evaluation', 'export.json'))
    _require([{key: pair[key] for key in exporter.PAIR_FIELDS} for pair in pairs]
             == [{key: pair[key] for key in exporter.PAIR_FIELDS} for pair in receipt['pair_provenance']],
             'DELIVERY_EXPORT_MAPPING_CHANGED')
    _recheck(receipt['bound_hashes'])
    checked = handoff.check_pair_export_v2(batch / 'public', batch / 'private/evaluation')
    _require(all(checked[key] == summary[key] for key in ('pairs', 'distinct_damages', 'source_models')),
             'DELIVERY_EXPORT_COUNTS_CHANGED')
    _require(summary.get('public_export') == checked, 'DELIVERY_EXPORT_SUMMARY_CHANGED')
    return summary


def check_delivery(batch, *, repository=ROOT, code_root=None):
    """Read back a completed immutable handoff; never repair or retry partial output."""
    batch, repository = _pair_safe_path(Path(batch)), _pair_safe_path(Path(repository))
    with q._exclusive_lock(batch / 'private/RUN.lock'):
        return _check_locked(batch, repository, code_root)


def deliver_batch(batch, *, repository=ROOT, code_root=None):
    """Explicit offline finalization; missing quota is reported and may be delivered."""
    batch, repository = _pair_safe_path(Path(batch)), _pair_safe_path(Path(repository))
    production, public, evaluation = exporter._roots(batch / 'public', batch / 'private/evaluation')
    final = batch / 'private/finalization'
    with q._exclusive_lock(batch / 'private/RUN.lock'):
        if final.exists():
            return _check_locked(batch, repository, code_root)
        _require(not public.exists() and not evaluation.exists(), 'NEW_OUTPUT_REQUIRED')
        code_root, environment = _code_environment(repository, code_root)
        merged, pairs, bindings, stats, rounds = _collect_inputs(batch, repository, code_root)
        final.mkdir()
        stage = 'collect_sealed_cases'
        try:
            copies = _collect_copies(batch, merged, bindings)
            _recheck(bindings)
            _write_new(final / 'pairs.json', pairs)
            _write_new(final / 'collection.json', {'schema_version': SCHEMA, 'status': 'collected',
                'batch': str(batch), 'repository': str(repository), 'rounds': rounds,
                'execution_environment': environment,
                'bound_hashes': bindings, 'copied_cases': copies,
                'pairs_sha256': q.sha256(final / 'pairs.json'), 'provider_calls': 0,
                'scope': 'Exact sealed case copies only; original round results/checkpoints and failed attempts preserved.'})
            _write_new(final / 'checks.json', {'schema_version': SCHEMA, 'passed': True, **stats,
                'core_and_round_programs_unchanged': True, 'all_sources_checked': True,
                'terminal_rounds_only': True, 'case_seals_checked': True,
                'semantic_recipes_and_damage_bytes_unique': True, 'source_cache_bindings_checked': True})
            stage = 'export_public_pairs'
            exported = handoff.export_pairs(production, public, evaluation, pairs, source_models=stats['source_models'])
            _recheck(bindings)
            authority = {str(path): q.sha256(path) for path in (
                final / 'collection.json', final / 'pairs.json', final / 'checks.json', evaluation / 'export.json')}
            summary = {'schema_version': SCHEMA, 'status': 'complete', **stats,
                       'public_export': exported, 'authority_sha256': authority,
                       'validation_scope': 'Fresh source/cache/program/case byte bindings and saved native/EXPRESS '
                           'receipt gates; authoring 1.3 bodies upgraded by fixed public axis glossary to 1.4; '
                           'all final request transforms/body/prefix/bytes and public whitelist/hash/CSV checked. No fresh native run, '
                           'system repair, human acceptance, live admission or capability claim.'}
            _write_new(final / 'summary.json', summary)
            stage = 'verify_completed_delivery'
            return _check_locked(batch, repository, code_root)
        except Exception as exc:
            _write_new(final / 'failed.json', {'schema_version': SCHEMA, 'status': 'failed', 'stage': stage,
                'error': f'{type(exc).__name__}: {exc}', 'provider_calls': 0,
                'scope': 'Existing outputs and receipts retained; no automatic deletion, overwrite or retry.'})
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('deliver', 'check'))
    parser.add_argument('--batch', type=Path, default=q.DEFAULT_OUTPUT)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--code-root', type=Path)
    args = parser.parse_args(argv)
    try:
        action = deliver_batch if args.command == 'deliver' else check_delivery
        result = action(args.batch, repository=args.repository, code_root=args.code_root)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({'schema_version': SCHEMA, 'status': 'failed',
                          'error': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
