"""A separately budgeted supplement; the first-pass controller stays frozen.

Reuse its tested, durable per-mother scheduler and all IFC/request checks. Each
worker temporarily selects the explicitly versioned guard and extra attribute
subsets in its own process, restores those bindings afterwards, and never edits
the first-pass checkpoint. No provider calls or changes to request profile 1.3.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import copy
import itertools
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from . import dataset_pairs as q
from .dataset_batch import engine

SCHEMA = 'text2ifc/dataset-supplement-round/1.0'
ROUND = 'supplement-r1'
BASE_BINDINGS = q._program_bindings


def raw_with_property_subsets(inventory, *, original, stopped=None, **kwargs):
    """Add omitted existing-field subsets; never invent new wrong values."""
    seen = set()
    for recipe in original(inventory, stopped=stopped, **kwargs):
        key = q.recipe_key(recipe)
        if key not in seen:
            seen.add(key)
            yield recipe
    groups = {}
    for prop in inventory.get('properties', []):
        groups.setdefault(prop['guid'], []).append(prop)
    for guid in sorted(groups):
        rows = sorted(groups[guid], key=lambda p: (p['pset_name'], p['property_name']))
        for size in range(2, min(4, len(rows)) + 1):
            for selected in itertools.combinations(rows, size):
                if stopped is not None and stopped():
                    return
                recipe = {'family': 'attributes', 'severity': 'medium', 'deletions': [],
                          'property_changes': [{**p, 'after': q._wrong_value(p, 0)} for p in selected]}
                key = q.recipe_key(recipe)
                if key not in seen:
                    seen.add(key)
                    yield recipe


def exclude_accepted(iterator, keys):
    for number, recipe in iterator:
        if q.recipe_key(recipe) not in keys:
            yield number, recipe


def excluded_first_pass_keys(baseline):
    """Retry the repaired guard failure, skip unchanged known rejections."""
    result = {row['recipe_key'] for row in baseline['cases']}
    for row in baseline['attempts']:
        if row['status'] == 'passed':
            continue
        error = row.get('errors', {}).get('exception', '')
        if 'Only entities with ids' in error and 'IfcParameterValue' in error:
            continue
        result.add(row['recipe_key'])
    return result


def rename_pairs(records):
    return [{**row, 'damage_id': row['damage_id'].replace('-d', '-s1-d'),
             'case_id': row['case_id'].replace('-d', '-s1-d')} for row in records]


def program_bindings():
    return {**BASE_BINDINGS(), **{path.relative_to(ROOT).as_posix(): q.sha256(path)
            for path in (Path(__file__), ROOT / 'scripts/ifc_repair/dataset_geometry_guard_v2.py')}}


@contextlib.contextmanager
def supplement_adapter(binding, accepted_keys, accepted_bytes):
    """Explicit process-local selection; never modifies the library or baseline files."""
    from .dataset_geometry_guard_v2 import guard_geometry
    names = ('_program_bindings', '_configuration', 'iter_raw_recipes', 'iter_prepared_recipes',
             'make_pair_records', '_check_damage')
    before = {name: getattr(q, name) for name in names}
    before_guard = engine.guard_geometry

    def configuration(*args, **kwargs):
        return {**before['_configuration'](*args, **kwargs), 'supplement': binding}

    def raw(inventory, **kwargs):
        return raw_with_property_subsets(inventory, original=before['iter_raw_recipes'], **kwargs)

    def prepared(inventory, **kwargs):
        return exclude_accepted(before['iter_prepared_recipes'](inventory, **kwargs), accepted_keys)

    def records(**kwargs):
        return rename_pairs(before['make_pair_records'](**kwargs))

    def checked(*args, **kwargs):
        result, prompts, walls, meshes = before['_check_damage'](*args, **kwargs)
        folder = Path(kwargs.get('folder', args[-1] if args else None))
        if result['damaged_sha256'] in accepted_bytes:
            raise ValueError('DUPLICATE_DAMAGE_OF_FIRST_PASS')
        result = {**result, 'generator_extension': SCHEMA,
                  'additional_evidence': [*result['additional_evidence'], 'private/supplement-binding.json']}
        q.write_json(folder / 'private/supplement-binding.json', {
            'schema_version': SCHEMA, 'baseline': binding, 'code_sha256': program_bindings(),
            'geometry_guard': 'text2ifc/dataset-geometry-guard/2.0',
            'request_profile': q.PROFILE, 'source_admission': 'hash-bound first-pass receipt reused'})
        q.write_json(folder / 'case.json', result)
        q.seal_case(folder)
        if not q.verify_seal(folder):
            raise ValueError('SUPPLEMENT_CASE_SEAL_INVALID')
        return result, prompts, walls, meshes

    try:
        q._program_bindings = program_bindings
        q._configuration = configuration
        q.iter_raw_recipes = raw
        q.iter_prepared_recipes = prepared
        q.make_pair_records = records
        q._check_damage = checked
        engine.guard_geometry = guard_geometry
        yield
    finally:
        for name, value in before.items():
            setattr(q, name, value)
        engine.guard_geometry = before_guard


def _baseline_binding(source):
    checkpoint = q.read(source / 'private/checkpoint.json')
    cache = checkpoint['cache_sha256']
    expected = {'private/reference.ifc', 'private/source.json',
                'private/source-validation.json', 'private/inventory.json'}
    if set(cache) != expected or any(q.sha256(source / name) != digest for name, digest in cache.items()):
        raise ValueError('FIRST_PASS_ADMISSION_CHANGED')
    return {'first_pass_result_sha256': q.sha256(source / 'result.json'),
            'first_pass_checkpoint_sha256': q.sha256(source / 'private/checkpoint.json'),
            'source_cache_sha256': cache}


def supplement_mother(batch, spec, *, quota=25, max_attempts=30, seed=None, repository=ROOT):
    """Resume a new round; old attempts and admission remain byte-for-byte intact."""
    batch = Path(batch).resolve()
    if not 1 <= quota <= 25 or not 1 <= max_attempts <= 30 or not q._valid_source_id(spec.get('source_id')):
        raise ValueError('INVALID_SUPPLEMENT_LIMIT_OR_SOURCE')
    first = batch / 'private/production/sources' / spec['source_id']
    baseline = q.read(first / 'result.json')
    remaining = quota - len(baseline['pairs'])
    if remaining <= 0:
        raise ValueError('NO_MOTHER_SHORTFALL')
    checkpoint = q.read(first / 'private/checkpoint.json')
    seed = checkpoint['configuration']['seed'] if seed is None else seed
    binding = _baseline_binding(first)
    admission = q.read(first / 'private/source-validation.json')
    if not (admission.get('passed') is True and admission.get('finding_count') == 0
            and admission.get('express_rules') is True and admission.get('schema') == 'IFC2X3'
            and admission.get('input_sha256') == spec['source_sha256']
            and admission.get('ifcopenshell_version') == q.ifcopenshell.version
            and q.read(first / 'private/source.json') == spec):
        raise ValueError('FIRST_PASS_ADMISSION_INVALID')
    keys = excluded_first_pass_keys(baseline)
    byte_hashes = {row['model_sha256'] for row in baseline['cases']}
    production = batch / 'private' / ROUND
    root = production / 'sources' / spec['source_id']
    with supplement_adapter(binding, keys, byte_hashes):
        config = q._configuration(spec, pairs_per_ifc=remaining, max_attempts=max_attempts, seed=seed)
        if not (root / 'private/checkpoint.json').exists():
            if root.exists():
                raise ValueError('SUPPLEMENT_CHECKPOINT_MISSING_WITH_EXISTING_FILES')
            root.mkdir(parents=True)
            for name, digest in binding['source_cache_sha256'].items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(first / name, target)
                if q.sha256(target) != digest or q.sha256(first / name) != digest:
                    raise ValueError('SUPPLEMENT_CACHE_COPY_CHANGED')
            q.write_json(root / 'private/checkpoint.json', {
                'schema_version': 'text2ifc/dataset-pair-checkpoint/1.0', 'configuration': config,
                'attempts': [], 'cases': [], 'pairs': [], 'candidate_cursor': 0, 'rejected': [],
                'cache_sha256': binding['source_cache_sha256']})
        result = q.process_mother(spec, repository, production, pairs_per_ifc=remaining,
                                 max_attempts=max_attempts, seed=seed, resume=True)
    if _baseline_binding(first) != binding:
        raise ValueError('FIRST_PASS_CHANGED_DURING_SUPPLEMENT')
    return result


def merge_results(baseline, supplements, *, quota=25):
    """Consolidate without editing either round's durable records."""
    extras = {row['source_id']: row for row in supplements}
    merged = []
    for original in baseline:
        row = copy.deepcopy(original)
        extra = extras.pop(row['source_id'], None)
        if extra:
            keys = {case['recipe_key'] for case in row['cases']}
            hashes = {case.get('model_sha256') for case in row['cases']}
            for case in extra['cases']:
                if case['recipe_key'] in keys:
                    raise ValueError('DUPLICATE_ACCEPTED_RECIPE')
                if case.get('model_sha256') in hashes:
                    raise ValueError('DUPLICATE_ACCEPTED_DAMAGE_BYTES')
                keys.add(case['recipe_key'])
                hashes.add(case.get('model_sha256'))
            row['pairs'].extend({**pair, 'case_path': pair['case_path'].rsplit('/', 1)[0] +
                                '/' + ROUND + '-' + pair['case_path'].rsplit('/', 1)[1]}
                               for pair in extra['pairs'])
            row['cases'].extend({**case, 'origin_path': case['path'], 'attempt_round': ROUND,
                                'path': case['path'].rsplit('/', 1)[0] + '/' + ROUND + '-' + case['case_id']}
                               for case in extra['cases'])
            row['attempts'] = [{**attempt, 'attempt_round': 'first_pass'} for attempt in row['attempts']]
            row['attempts'].extend({**attempt, 'attempt_round': ROUND} for attempt in extra['attempts'])
            row['attempted_cases'] += extra['attempted_cases']
            row['candidate_rejection_count'] = row.get('candidate_rejection_count', 0) + extra['candidate_rejection_count']
            row['source_unchanged'] = row['source_unchanged'] and extra['source_unchanged']
            row['stop_reason'] = extra['stop_reason']
        if len(row['pairs']) > quota:
            raise ValueError('MOTHER_PAIR_QUOTA_EXCEEDED')
        row['status'] = 'complete' if len(row['pairs']) == quota else 'incomplete'
        row['target_pairs'] = quota
        merged.append(row)
    if extras:
        raise ValueError('SUPPLEMENT_SOURCE_NOT_IN_FIRST_PASS')
    return merged


def load_results(production):
    return [q.read(path) for path in sorted(Path(production).glob('sources/*/result.json'))]


def round_status(batch, *, running=False, errors=None):
    batch = Path(batch)
    baseline = load_results(batch / 'private/production')
    extra = load_results(batch / 'private' / ROUND)
    build = q.read(batch / 'private' / ROUND / 'build.json')
    merged = merge_results(baseline, extra, quota=build['pairs_per_ifc'])
    summary = {'schema_version': SCHEMA, 'status': 'running' if running else 'finished',
        'first_pass_pairs': sum(len(r['pairs']) for r in baseline),
        'supplement_pairs': sum(len(r['pairs']) for r in extra),
        'pairs_total': sum(len(r['pairs']) for r in merged),
        'supplement_damages': sum(len(r['cases']) for r in extra),
        'supplement_attempts': sum(r['attempted_cases'] for r in extra),
        'supplement_failures': sum(a['status'] != 'passed' for r in extra for a in r['attempts']),
        'mothers_finished': len(extra), 'mother_round_target': len(build['sources']), 'worker_errors': errors or [],
        'provider_calls': 0,
        'active_progress': [{'source_id': path.parent.parent.name, **q.read(path)}
                            for path in sorted((batch / 'private' / ROUND).glob('sources/*/private/progress.json'))],
        'per_mother': [{'source_id': r['source_id'], 'pairs': len(r['pairs']),
                       'missing': r['target_pairs'] - len(r['pairs']), 'stop_reason': r['stop_reason']}
                      for r in merged if r['status'] != 'complete']}
    q.write_json(batch / 'private' / ROUND / 'summary.json', summary)
    return summary


def run_round(batch, *, max_attempts=30, workers=2):
    batch = Path(batch).resolve()
    if not 1 <= max_attempts <= 30 or not 1 <= workers <= 2:
        raise ValueError('SUPPLEMENT_LIMITS_INVALID')
    production = batch / 'private/production'
    previous = q.read(production / 'build.json')
    bindings = program_bindings()
    if previous['code_sha256'] != BASE_BINDINGS():
        raise ValueError('FROZEN_FIRST_PASS_CODE_CHANGED')
    specs = q.read(production / 'mother-sources.json')['sources']
    baseline = load_results(production)
    if len(baseline) != len(specs) or any(not r['source_unchanged'] for r in baseline):
        raise ValueError('FIRST_PASS_NOT_FINISHED_OR_SOURCE_CHANGED')
    eligible = [spec for spec in specs if len(next(r for r in baseline if r['source_id'] == spec['source_id'])['pairs'])
                < previous['pairs_per_ifc']]
    round_root = batch / 'private' / ROUND
    config = {'schema_version': SCHEMA, 'pairs_per_ifc': previous['pairs_per_ifc'],
        'max_additional_attempts_per_mother': max_attempts, 'workers': workers,
        'sources': eligible, 'code_sha256': bindings,
        'first_pass_results': {r['source_id']: q.sha256(production / 'sources' / r['source_id'] / 'result.json')
                               for r in baseline},
        'policy': 'first-pass attempts remain spent; bounded separate round; accepted recipes/bytes and unchanged known failures excluded; only repaired inline-value failures retried; profile1.3 unchanged'}
    with q._exclusive_lock(batch / 'private/RUN.lock'):
        if (round_root / 'build.json').exists():
            if q.read(round_root / 'build.json') != config:
                raise ValueError('SUPPLEMENT_ROUND_CONFIGURATION_CHANGED')
        else:
            if round_root.exists():
                raise ValueError('NEW_SUPPLEMENT_ROOT_REQUIRED')
            round_root.mkdir()
            q.write_json(round_root / 'build.json', config)
            history = batch / 'private/history/first-pass-20261011'
            history.mkdir(parents=True)
            for name in ('REPORT.md', 'summary.json'):
                shutil.copyfile(batch / name, history / name)
            for name, digest in bindings.items():
                target = round_root / 'code-snapshot' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
                if q.sha256(target) != digest:
                    raise ValueError('SUPPLEMENT_CODE_SNAPSHOT_CHANGED')
        errors = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            pending = {pool.submit(supplement_mother, batch, spec,
                         quota=previous['pairs_per_ifc'], max_attempts=max_attempts): spec for spec in eligible}
            while pending:
                done, _ = concurrent.futures.wait(pending, timeout=30,
                                                  return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    spec = pending.pop(future)
                    try:
                        result = future.result()
                        print(json.dumps({'source_id': spec['source_id'], 'additional_pairs': len(result['pairs']),
                            'attempts': result['attempted_cases'], 'stop_reason': result['stop_reason']},
                            ensure_ascii=False), flush=True)
                    except Exception as exc:
                        errors.append({'source_id': spec['source_id'], 'error': f'{type(exc).__name__}:{exc}'})
                round_status(batch, running=bool(pending), errors=errors)
        for path, digest in bindings.items():
            if q.sha256(ROOT / path) != digest:
                raise ValueError('SUPPLEMENT_CODE_CHANGED_DURING_RUN')
        result = round_status(batch, errors=errors)
        print(json.dumps({k: v for k, v in result.items() if k != 'active_progress'}, ensure_ascii=False), flush=True)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run', 'status'))
    parser.add_argument('--batch', type=Path, default=ROOT / 'dataset/processed/ifc-repair/formal-40-pairs-25-20261010')
    parser.add_argument('--max-attempts', type=int, default=30)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    result = run_round(args.batch, max_attempts=args.max_attempts, workers=args.workers) if args.command == 'run' else q.read(args.batch / 'private' / ROUND / 'summary.json')
    if args.command == 'status':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get('worker_errors') else 0


if __name__ == '__main__':
    raise SystemExit(main())
