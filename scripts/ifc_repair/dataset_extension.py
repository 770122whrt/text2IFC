"""Append up to five pairs per admitted mother in a separate durable round.

The old controllers, accepted damages and checkpoints stay frozen. Previously
unselected applicable modes are separate additions, not new damaged IFCs. A
new replacement source has its own ID and a fresh native/inventory admission.
Execute this module from a pinned runtime; repository is the data root only.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import copy
import importlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from . import dataset_pairs as q
from . import dataset_supplement as s
from . import dataset_pair_export as exporter
from . import dataset_pair_resume as resume_engine
from .dataset_batch import engine
from .repair_comparison.batch_cases import _pair_safe_path

SCHEMA = 'text2ifc/dataset-extension-round/1.0'
ROUND = 'extension-r2'
BASE_BINDINGS = q._program_bindings
CACHE_FILES = ('private/reference.ifc', 'private/source.json',
               'private/source-validation.json', 'private/inventory.json')


def plan_targets(baseline_pairs, borrowed_capacity, *, replacement=False, cap=30, append=5):
    if (type(cap) is not int or not 1 <= cap <= 30 or type(append) is not int
            or not 1 <= append <= 5 or type(baseline_pairs) is not int
            or not 0 <= baseline_pairs <= cap or type(borrowed_capacity) is not int
            or borrowed_capacity < 0 or (replacement and baseline_pairs)):
        raise ValueError('INVALID_EXTENSION_CAP_OR_BASELINE')
    additional = cap if replacement else min(append, cap - baseline_pairs)
    borrowed = min(borrowed_capacity, additional)
    return {'baseline_pairs': baseline_pairs, 'target_added_pairs': additional,
            'borrowed_pairs': borrowed, 'target_new_damage_pairs': additional - borrowed,
            'total_target_pairs': baseline_pairs + additional}


def verify_pair_uniqueness(records):
    ids, modes = set(), set()
    for pair in records:
        key = pair['case_id'].casefold()
        mode = (pair['damage_id'].casefold(), pair['locator_mode'])
        if key in ids or mode in modes:
            raise ValueError('DUPLICATE_EXTENSION_PAIR_OR_MODE')
        if pair['locator_mode'] not in {'world', 'host_wall'}:
            raise ValueError('INVALID_EXTENSION_LOCATOR')
        ids.add(key)
        modes.add(mode)
    return True


def missing_variants(records, templates):
    """Pure projection; caller must first bind each full sealed case receipt."""
    verify_pair_uniqueness(records)
    anchors = {}
    modes = {}
    for pair in records:
        anchors.setdefault(pair['damage_id'], pair)
        modes.setdefault(pair['damage_id'], set()).add(pair['locator_mode'])
    result = []
    for damage, pair in anchors.items():
        for mode in ('world', 'host_wall'):
            meta = templates[damage].get(mode, {})
            if meta.get('applicable') is True and mode not in modes[damage]:
                result.append({**pair, 'case_id': damage + '-' + mode, 'locator_mode': mode,
                    'request_relative_path': 'public/request-' + mode + '.txt',
                    'request_sha256': exporter._digest(meta.get('sha256'))})
    return result


def exclude_known_geometry(inventory, known):
    """Recorded wall failures exclude deletion targets; existing fields remain usable."""
    result = {**inventory, 'targets': {name: list(rows) for name, rows in inventory['targets'].items()}}
    excluded = []
    for family, rows in result['targets'].items():
        kept = []
        for target in rows:
            reject = any((item.get('host_guid') and (target.get('host') or {}).get('guid') == item['host_guid'])
                or (item.get('opening_guid') and target.get('opening_guid') == item['opening_guid'])
                or (item.get('target_guid') and target['guid'] == item['target_guid']) for item in known)
            if reject:
                excluded.append({'guid': target['guid'], 'class': target.get('ifc_class'),
                                 'reason': 'KNOWN_WALL_INTERIOR_AND_CLOSURE_UNCONFIRMED'})
            else:
                kept.append(target)
        result['targets'][family] = kept
    return result, excluded


def process_mother_up_to_30(spec, repository, production, *, pairs_per_ifc=30,
                           max_attempts=30, seed=20261010, resume=False):
    """The original safe entry, with 30 as quota ceiling; original locked loop unchanged."""
    if not 1 <= pairs_per_ifc <= 30 or not 1 <= max_attempts <= 30:
        raise ValueError('PAIR_QUOTA_1_TO_30_AND_ATTEMPT_CAP_1_TO_30_REQUIRED')
    if not q._valid_source_id(spec.get('source_id')):
        raise ValueError('UNSAFE_SOURCE_ID')
    repository, production = Path(repository).resolve(), _pair_safe_path(Path(production))
    source = _pair_safe_path(repository / spec['input_path'])
    if not 0 < source.stat().st_size < 20_000_000 or q.sha256(source) != spec['source_sha256']:
        raise ValueError('SOURCE_SIZE_OR_SHA_CHANGED')
    root = production / 'sources' / spec['source_id']
    if root.exists() and not resume:
        raise FileExistsError('NEW_MOTHER_REQUIRED_OR_USE_RESUME')
    pause = production.parents[1] / 'PAUSE'
    if pause.exists() and not root.exists():
        return {'source_id': spec['source_id'], 'source': spec, 'status': 'incomplete',
                'source_unchanged': True, 'source_native_passed': False,
                'source_sha256': spec['source_sha256'], 'class_counts': {}, 'eligible_counts': {},
                'pairs': [], 'cases': [], 'attempts': [], 'attempted_cases': 0,
                'candidate_rejection_count': 0, 'stop_reason': 'cooperative_pause',
                'elapsed_seconds': 0, 'target_pairs': pairs_per_ifc}
    root.mkdir(parents=True, exist_ok=True)
    with q._exclusive_lock(root / 'private/MOTHER.lock'):
        return resume_engine._locked(q, spec, source, production, root,
            pairs_per_ifc=pairs_per_ifc, max_attempts=max_attempts, seed=seed, resume=resume, pause=pause)


def program_bindings():
    return {**BASE_BINDINGS(), **{path.relative_to(ROOT).as_posix(): q.sha256(path) for path in (
        ROOT / 'scripts/ifc_repair/dataset_supplement.py',
        ROOT / 'scripts/ifc_repair/dataset_geometry_guard_v2.py', Path(__file__))}}


def baseline_rows(batch):
    return s.merge_results(s.load_results(batch / 'private/production'),
                           s.load_results(batch / 'private' / s.ROUND))


def origin_case(batch, case):
    if case.get('attempt_round') == s.ROUND:
        return batch / 'private' / s.ROUND, case['origin_path']
    return batch / 'private/production', case['path']


def _baseline_binding(batch, source_id):
    records = {}
    for name, root in (('first_pass', batch / 'private/production'),
                       (s.ROUND, batch / 'private' / s.ROUND)):
        folder = root / 'sources' / source_id
        if (folder / 'result.json').is_file():
            records[name] = s._baseline_binding(folder)
    return records


def _borrowed(batch, row):
    templates, locations, bindings = {}, {}, {}
    cases = {case['path']: case for case in row['cases']}
    for pair in row['pairs']:
        damage = pair['damage_id']
        if damage in templates:
            continue
        root, path = origin_case(batch, cases[pair['case_path']])
        folder = _pair_safe_path(root / path)
        meta = q.read(folder / 'case.json')
        templates[damage] = meta['prompt_templates']
        locations[damage] = (root, path)
    additions = missing_variants(row['pairs'], templates)
    for pair in additions:
        root, path = locations[pair['damage_id']]
        checked = exporter._case(root, {**pair, 'case_path': path}, bindings)
        if checked['requests'][pair['locator_mode']][1] != pair['request_sha256']:
            raise ValueError('BORROWED_REQUEST_BINDING_CHANGED')
    return [{'pair': pair, 'origin_root': str(locations[pair['damage_id']][0]),
             'origin_case_path': locations[pair['damage_id']][1]} for pair in additions], bindings


@contextlib.contextmanager
def extension_adapter(binding, skipped_keys, prior_bytes, known):
    from .dataset_geometry_guard_v2 import guard_geometry
    names = ('_program_bindings', '_configuration', 'iter_raw_recipes', 'iter_prepared_recipes',
             'make_pair_records', '_check_damage', '_candidate_inventory')
    before = {name: getattr(q, name) for name in names}
    previous_guard = engine.guard_geometry

    def configuration(*args, **kwargs):
        return {**before['_configuration'](*args, **kwargs), 'extension': binding}

    def raw(inventory, **kwargs):
        return s.raw_with_property_subsets(inventory, original=before['iter_raw_recipes'], **kwargs)

    def prepared(inventory, **kwargs):
        return s.exclude_accepted(before['iter_prepared_recipes'](inventory, **kwargs), skipped_keys)

    def records(**kwargs):
        return [{**row, 'damage_id': row['damage_id'].replace('-d', '-e2-d'),
                 'case_id': row['case_id'].replace('-d', '-e2-d')}
                for row in before['make_pair_records'](**kwargs)]

    def candidates(inventory):
        admitted, rejected = before['_candidate_inventory'](inventory)
        filtered, negatives = exclude_known_geometry(admitted, known)
        return filtered, [*rejected, *negatives]

    def checked(*args, **kwargs):
        result, prompts, walls, meshes = before['_check_damage'](*args, **kwargs)
        folder = Path(kwargs.get('folder', args[-1] if args else None))
        if result['damaged_sha256'] in prior_bytes:
            raise ValueError('DUPLICATE_DAMAGE_OF_PREVIOUS_ROUNDS')
        result = {**result, 'generator_extension': SCHEMA,
            'additional_evidence': [*result['additional_evidence'], 'private/extension-binding.json']}
        q.write_json(folder / 'private/extension-binding.json', {
            'schema_version': SCHEMA, 'baseline': binding, 'code_sha256': program_bindings(),
            'geometry_guard': 'text2ifc/dataset-geometry-guard/2.0', 'request_profile': q.PROFILE,
            'source_admission': 'fresh-this-round' if binding['replacement'] else 'hash-bound-first-pass-reused'})
        q.write_json(folder / 'case.json', result)
        q.seal_case(folder)
        if not q.verify_seal(folder):
            raise ValueError('EXTENSION_CASE_SEAL_INVALID')
        return result, prompts, walls, meshes

    try:
        q._program_bindings = program_bindings
        q._configuration = configuration
        q.iter_raw_recipes = raw
        q.iter_prepared_recipes = prepared
        q.make_pair_records = records
        q._candidate_inventory = candidates
        q._check_damage = checked
        engine.guard_geometry = guard_geometry
        yield
    finally:
        for name, value in before.items():
            setattr(q, name, value)
        engine.guard_geometry = previous_guard


def extension_mother(batch, spec, *, repository, plan):
    batch = Path(batch).resolve()
    production = batch / 'private' / ROUND
    root = production / 'sources' / spec['source_id']
    baseline = next((r for r in baseline_rows(batch) if r['source_id'] == spec['source_id']), None)
    binding = {'round': ROUND, 'source_id': spec['source_id'], 'replacement': plan['replacement'],
        'baseline': _baseline_binding(batch, spec['source_id']),
        'borrowed_bound_hashes': plan['borrowed_bound_hashes'],
        'target_added_pairs': plan['target_added_pairs'], 'per_mother_cap': 30}
    if binding != plan['baseline_binding']:
        raise ValueError('EXTENSION_BASELINE_CHANGED')
    check_environment(batch)
    for path, expected in plan['borrowed_bound_hashes'].items():
        if q.sha256(Path(path)) != expected:
            raise ValueError('BORROWED_CASE_CHANGED')
    keys = s.excluded_first_pass_keys(baseline) if baseline else set()
    prior_bytes = {case['model_sha256'] for case in baseline['cases']} if baseline else set()
    known = spec.get('known_geometry_exclusions', [])
    target = plan['target_new_damage_pairs']
    if target:
        with extension_adapter(binding, keys, prior_bytes, known):
            if not plan['replacement'] and not (root / 'private/checkpoint.json').exists():
                if root.exists():
                    raise ValueError('EXTENSION_CHECKPOINT_MISSING_WITH_EXISTING_FILES')
                first = batch / 'private/production/sources' / spec['source_id']
                cache = binding['baseline']['first_pass']['source_cache_sha256']
                if set(cache) != set(CACHE_FILES):
                    raise ValueError('EXTENSION_SOURCE_CACHE_INCOMPLETE')
                root.mkdir(parents=True)
                for name, digest in cache.items():
                    destination = root / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(first / name, destination)
                    if q.sha256(destination) != digest or q.sha256(first / name) != digest:
                        raise ValueError('EXTENSION_SOURCE_CACHE_COPY_CHANGED')
                config = q._configuration(spec, pairs_per_ifc=target,
                                           max_attempts=plan['max_attempts'], seed=plan['seed'])
                q.write_json(root / 'private/checkpoint.json', {
                    'schema_version': 'text2ifc/dataset-pair-checkpoint/1.0', 'configuration': config,
                    'attempts': [], 'cases': [], 'pairs': [], 'candidate_cursor': 0,
                    'rejected': [], 'cache_sha256': cache})
            result = process_mother_up_to_30(spec, repository, production, pairs_per_ifc=target,
                max_attempts=plan['max_attempts'], seed=plan['seed'],
                resume=(root / 'private/checkpoint.json').exists())
    else:
        root.mkdir(parents=True, exist_ok=True)
        result = {'source_id': spec['source_id'], 'source': spec, 'status': 'complete',
            'source_unchanged': True, 'source_native_passed': True,
            'source_sha256': spec['source_sha256'], 'pairs': [], 'cases': [], 'attempts': [],
            'attempted_cases': 0, 'candidate_rejection_count': 0,
            'stop_reason': 'saved_variants_sufficient', 'target_pairs': 0}
        q.write_json(root / 'result.json', result)
    if _baseline_binding(batch, spec['source_id']) != binding['baseline']:
        raise ValueError('BASELINE_CHANGED_DURING_EXTENSION')
    check_environment(batch)
    new_pairs = [{**pair, 'case_path': pair['case_path'].rsplit('/', 1)[0] +
                  '/' + ROUND + '-' + pair['case_path'].rsplit('/', 1)[1]} for pair in result['pairs']]
    added = [*[item['pair'] for item in plan['borrowed_variants']], *new_pairs]
    verify_pair_uniqueness([*(baseline['pairs'] if baseline else []), *added])
    total = plan['baseline_pairs'] + len(added)
    if total > 30:
        raise ValueError('FINAL_MOTHER_CAP_EXCEEDED')
    summary = {'schema_version': SCHEMA, 'source_id': spec['source_id'], 'replacement': plan['replacement'],
        'status': 'complete' if len(added) == plan['target_added_pairs'] else 'incomplete',
        'baseline_pairs': plan['baseline_pairs'], 'target_added_pairs': plan['target_added_pairs'],
        'target_new_damage_pairs': target, 'borrowed_pairs': len(plan['borrowed_variants']),
        'new_damage_pairs': len(result['pairs']), 'added_pairs': len(added), 'total_pairs': total,
        'missing_added_pairs': plan['target_added_pairs'] - len(added),
        'new_damages': len(result['cases']), 'attempted_cases': result['attempted_cases'],
        'failed_attempts': sum(a['status'] == 'failed' for a in result['attempts']),
        'stop_reason': result['stop_reason'], 'source_unchanged': result['source_unchanged'],
        'borrowed_variants': plan['borrowed_variants'], 'pairs': added,
        'result_sha256': q.sha256(root / 'result.json'), 'baseline_binding': binding,
        'provider_calls': 0, 'human_review': 'pending_human_review'}
    q.write_json(root / 'mother-summary.json', summary)
    return summary


def loaded_programs(root, expected, modules=None):
    loaded = {}
    for name, module in tuple((sys.modules if modules is None else modules).items()):
        if name.startswith(('scripts.ifc_repair', 'text2ifc_')) and getattr(module, '__file__', None):
            path = Path(module.__file__).resolve()
            if not path.is_relative_to(root):
                raise ValueError('MIXED_ACTUAL_LOADED_PROJECT_MODULE:' + name)
            relative = path.relative_to(root).as_posix()
            digest = q.sha256(path)
            if expected.get(relative) != digest:
                raise ValueError('UNBOUND_ACTUAL_LOADED_PROJECT_MODULE:' + name)
            loaded[name] = {'path': str(path), 'sha256': digest}
    return loaded


def check_environment(batch):
    first = q.read(batch / 'private/production/build.json')['code_sha256']
    if BASE_BINDINGS() != first:
        raise ValueError('ACTUAL_EXECUTED_FIRST_PASS_PROGRAMS_NOT_PINNED')
    manifest = q.read(ROOT / 'runtime.json')
    for name, digest in manifest['program_sha256'].items():
        if q.sha256(ROOT / name) != digest:
            raise ValueError('ACTUAL_RUNTIME_PROGRAM_CHANGED:' + name)
    if manifest.get('runtime_root') != str(ROOT) or manifest['program_sha256'].get(
            'scripts/ifc_repair/dataset_extension.py') != q.sha256(Path(__file__)):
        raise ValueError('EXTENSION_MUST_EXECUTE_FROM_BOUND_RUNTIME')
    loaded = loaded_programs(ROOT, manifest['program_sha256'])
    return {'runtime_root': str(ROOT), 'runtime_manifest_sha256': q.sha256(ROOT / 'runtime.json'),
            'loaded_modules': loaded}


def make_build(batch, replacement_spec, repository, *, max_attempts=30, workers=2):
    if not 1 <= max_attempts <= 30 or workers not in (1, 2):
        raise ValueError('INVALID_EXTENSION_ATTEMPTS_OR_WORKERS')
    rows = baseline_rows(batch)
    old_specs = q.read(batch / 'private/production/mother-sources.json')['sources']
    if len(rows) != 40 or len(old_specs) != 40:
        raise ValueError('FORTY_HISTORICAL_SOURCES_REQUIRED')
    excluded = next(r for r in rows if r['source_id'] == 'formal-028')
    if excluded['pairs'] or replacement_spec['source_id'] in {s['source_id'] for s in old_specs}:
        raise ValueError('ONLY_ZERO_SOURCE_REPLACEMENT_WITH_NEW_ID_ALLOWED')
    if replacement_spec['source_sha256'] in {s['source_sha256'] for s in old_specs}:
        raise ValueError('REPLACEMENT_SOURCE_BYTES_ALREADY_USED')
    active = [spec for spec in old_specs if spec['source_id'] != 'formal-028'] + [replacement_spec]
    plans = []
    for spec in active:
        replacement = spec['source_id'] == replacement_spec['source_id']
        row = next((r for r in rows if r['source_id'] == spec['source_id']), None)
        borrowed, hashes = _borrowed(batch, row) if row else ([], {})
        numbers = plan_targets(len(row['pairs']) if row else 0, len(borrowed), replacement=replacement)
        chosen = borrowed[:numbers['borrowed_pairs']]
        seed = q.read(batch / 'private/production/sources' / spec['source_id'] /
                      'private/checkpoint.json')['configuration']['seed'] if row else 20261010
        binding = {'round': ROUND, 'source_id': spec['source_id'], 'replacement': replacement,
            'baseline': _baseline_binding(batch, spec['source_id']), 'borrowed_bound_hashes': hashes,
            'target_added_pairs': numbers['target_added_pairs'], 'per_mother_cap': 30}
        plans.append({'source_id': spec['source_id'], 'replacement': replacement, **numbers,
            'borrowed_variants': chosen, 'borrowed_bound_hashes': hashes,
            'baseline_binding': binding, 'seed': seed, 'max_attempts': max_attempts})
    return {'schema_version': SCHEMA, 'round': ROUND, 'per_mother_cap': 30,
        'append_existing_pairs': 5, 'target_total_pairs': 1200, 'max_attempts': max_attempts,
        'workers': workers, 'sources': active, 'plans': plans,
        'replacements': [{'old_source_id': 'formal-028', 'old_source_sha256': excluded['source_sha256'],
                          'new_source_id': replacement_spec['source_id'],
                          'new_source_sha256': replacement_spec['source_sha256'],
                          'reason': 'ObjectPlacement-only world locator cannot disambiguate the old source'}],
        'code_sha256': program_bindings(), 'execution_environment': check_environment(batch),
        'provider_calls': 0, 'scope': 'Independent append round; old accepted cases/results/checkpoints are unchanged.'}


def round_status(batch, *, running=False, errors=None):
    production = batch / 'private' / ROUND
    build = q.read(production / 'build.json')
    results = [q.read(path) for path in sorted(production.glob('sources/*/mother-summary.json'))]
    summary = {'schema_version': SCHEMA, 'status': 'running' if running else 'finished',
        'mothers_finished': len(results), 'mother_round_target': len(build['sources']),
        'target_added_pairs': sum(plan['target_added_pairs'] for plan in build['plans']),
        'added_pairs': sum(row['added_pairs'] for row in results),
        'borrowed_pairs': sum(row['borrowed_pairs'] for row in results),
        'new_damage_pairs': sum(row['new_damage_pairs'] for row in results),
        'new_damages': sum(row['new_damages'] for row in results),
        'attempted_cases': sum(row['attempted_cases'] for row in results),
        'failed_attempts': sum(row['failed_attempts'] for row in results),
        'missing_added_pairs': sum(row['missing_added_pairs'] for row in results),
        'completed_active_mothers': sum(row['total_pairs'] == 30 for row in results),
        'worker_errors': errors or [], 'provider_calls': 0,
        'per_mother': [{key: row[key] for key in ('source_id', 'total_pairs', 'added_pairs',
            'borrowed_pairs', 'new_damages', 'attempted_cases', 'failed_attempts', 'stop_reason')}
            for row in results]}
    q.write_json(production / 'summary.json', summary)
    return summary


def run_round(batch, replacement_spec, *, repository, workers=2, max_attempts=30):
    batch, repository = _pair_safe_path(Path(batch)), _pair_safe_path(Path(repository))
    with q._exclusive_lock(batch / 'private/RUN.lock'):
        production = batch / 'private' / ROUND
        build = make_build(batch, replacement_spec, repository, max_attempts=max_attempts, workers=workers)
        if (production / 'build.json').exists():
            if q.read(production / 'build.json') != build:
                raise ValueError('EXTENSION_BUILD_OR_BASELINE_CHANGED')
        else:
            if production.exists():
                raise ValueError('EXTENSION_BUILD_MISSING_WITH_EXISTING_OUTPUT')
            production.mkdir(parents=True)
            q.write_json(production / 'build.json', build)
            for name, digest in build['code_sha256'].items():
                target = production / 'code-snapshot' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
                if q.sha256(target) != digest:
                    raise ValueError('EXTENSION_PROGRAM_SNAPSHOT_CHANGED')
        specs = {spec['source_id']: spec for spec in build['sources']}
        errors = []
        pending = iter(build['plans'])
        # runpy's __main__ functions are not a stable Windows spawn target.
        worker = importlib.import_module('scripts.ifc_repair.dataset_extension').extension_mother
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            jobs = {}

            def dispatch():
                if (batch / 'PAUSE').exists():
                    return
                while len(jobs) < workers:
                    plan = next(pending, None)
                    if plan is None:
                        break
                    future = pool.submit(worker, batch, specs[plan['source_id']],
                                         repository=repository, plan=plan)
                    jobs[future] = plan['source_id']

            dispatch()
            while jobs:
                done, _ = concurrent.futures.wait(jobs, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    source_id = jobs.pop(future)
                    try:
                        row = future.result()
                        print(json.dumps({key: row[key] for key in ('source_id', 'added_pairs',
                            'borrowed_pairs', 'new_damages', 'attempted_cases', 'stop_reason')},
                            ensure_ascii=False), flush=True)
                    except Exception as exc:
                        errors.append({'source_id': source_id, 'error': f'{type(exc).__name__}: {exc}'})
                        print(json.dumps(errors[-1], ensure_ascii=False), flush=True)
                    round_status(batch, running=True, errors=errors)
                dispatch()
        return round_status(batch, errors=errors)


def probe_worker(batch):
    return {'schema_version': SCHEMA, 'passed': True, 'provider_calls': 0,
            'scope': 'Read-only pinned program/import bindings in a Windows child process; no IFC or native.',
            'execution_environment': check_environment(Path(batch))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run', 'status', 'probe'))
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--replacement-source', type=Path)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--max-attempts', type=int, default=30)
    args = parser.parse_args(argv)
    if args.command == 'run':
        if args.replacement_source is None:
            parser.error('--replacement-source is required for run')
        spec = q.read(args.replacement_source)
        result = run_round(args.batch, spec, repository=args.repository,
                           workers=args.workers, max_attempts=args.max_attempts)
    elif args.command == 'status':
        result = q.read(args.batch / 'private' / ROUND / 'summary.json')
    else:
        worker = importlib.import_module('scripts.ifc_repair.dataset_extension').probe_worker
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as pool:
            result = pool.submit(worker, args.batch.resolve()).result()
    print(json.dumps({key: value for key, value in result.items() if key != 'per_mother'}, ensure_ascii=False))
    return 0 if not result.get('worker_errors') else 2


if __name__ == '__main__':
    raise SystemExit(main())
