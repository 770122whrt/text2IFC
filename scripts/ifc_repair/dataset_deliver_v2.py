"""Immutable offline handoff of first pass, r1 and the cap30 extension round."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair import dataset_deliver as old
from scripts.ifc_repair import dataset_deliver_runtime_v2 as pinned
from scripts.ifc_repair import dataset_extension as x
from scripts.ifc_repair import dataset_pair_export as e
from scripts.ifc_repair import dataset_pair_export_v2 as handoff
from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_supplement as s

SCHEMA = 'text2ifc/dataset-offline-delivery/1.1'
ACTIVE_SOURCES = 40
PER_MOTHER_CAP = 30
APPEND_PAIRS = 5
EXCLUDED_SOURCE = 'formal-028'
REPLACEMENT_SOURCE = 'formal-041'


def _environment(repository, code_root=None):
    root, record = old._code_environment(repository, code_root)
    e._require(x.ROOT.resolve() == root and Path(x.__file__).resolve() == root / 'scripts/ifc_repair/dataset_extension.py'
        and Path(__file__).resolve() == root / 'scripts/ifc_repair/dataset_deliver_v2.py', 'CODE_ROOT_NOT_ACTUALLY_LOADED')
    loaded = pinned.check_loaded_runtime(root)
    e._require(loaded['source_repository'] == str(repository), 'SOURCE_REPOSITORY_CHANGED')
    return root, {**record, 'pinned_runtime': loaded}


def _environment_identity(record):
    """Lazy imports may change the observed inventory, never the pinned identity."""
    e._require(isinstance(record, dict), 'DELIVERY_LOADED_ENVIRONMENT_CHANGED')
    identity = {key: value for key, value in record.items() if key != 'loaded_modules'}
    if 'pinned_runtime' in identity:
        runtime = identity['pinned_runtime']
        e._require(isinstance(runtime, dict), 'DELIVERY_LOADED_ENVIRONMENT_CHANGED')
        identity['pinned_runtime'] = {key: value for key, value in runtime.items()
            if key != 'loaded_project_modules'}
    return identity


def _round_environment(batch, repository, environment, bindings):
    root = e._pair_safe_path(Path(environment['runtime_root']))
    manifest = root / 'runtime.json'
    e._bind(manifest, bindings, environment['runtime_manifest_sha256'])
    record = pinned.check_runtime(root)
    e._require(record['batch'] == str(batch) and record['repository'] == str(repository), 'ROUND_RUNTIME_CONTEXT_CHANGED')
    for name, digest in record['program_sha256'].items():
        e._bind(e._file(root, name), bindings, digest)
    loaded = environment.get('loaded_modules')
    e._require(isinstance(loaded, dict) and bool(loaded), 'ROUND_ACTUAL_LOADED_MODULES_MISSING')
    for name, item in loaded.items():
        path = e._pair_safe_path(Path(item['path']))
        e._require(path.is_relative_to(root) and record['program_sha256'].get(path.relative_to(root).as_posix()) == item['sha256'],
                   'ROUND_LOADED_MODULE_BINDING_CHANGED:' + name)
        e._bind(path, bindings, item['sha256'])


def _pairs(records):
    return [{**p, 'case_id': p['case_id'].replace('-d', '-e2-d'),
        'damage_id': p['damage_id'].replace('-d', '-e2-d')} for p in records]


def _mother(round_root, spec, plan, build, bindings):
    folder = round_root / 'sources' / spec['source_id']
    row = old._read(e._file(folder, 'result.json'), bindings)
    target = plan['target_new_damage_pairs']
    e._require(row.get('source_id') == spec['source_id'] and row.get('source') == spec
        and row.get('source_sha256') == spec['source_sha256'] and row.get('source_unchanged') is True
        and row.get('source_native_passed') is True, 'EXTENSION_RESULT_SOURCE_CHANGED')
    if not target:
        e._require(row.get('status') == 'complete' and row.get('stop_reason') == 'saved_variants_sufficient'
            and row.get('target_pairs') == 0 and row.get('attempted_cases') == 0
            and row.get('candidate_rejection_count') == 0
            and all(row.get(name) == [] for name in ('pairs', 'cases', 'attempts')),
            'ZERO_DAMAGE_EXTENSION_RESULT_INVALID')
        return row
    old._terminal(row, target, plan['max_attempts'])
    checkpoint = old._source(folder, spec, bindings)
    for digest in checkpoint['cache_sha256'].values():
        e._digest(digest)
    config = {'source_sha256': spec['source_sha256'], 'source_id': spec['source_id'],
        'pairs_per_ifc': target, 'max_attempts': plan['max_attempts'], 'seed': plan['seed'],
        'profile': q.PROFILE, 'code_sha256': build['code_sha256'], 'extension': plan['baseline_binding']}
    e._require(checkpoint.get('configuration') == config and all(checkpoint.get(name) == row.get(name)
        for name in ('pairs', 'cases', 'attempts')), 'EXTENSION_CHECKPOINT_LEDGER_CHANGED')
    e._require(row.get('cases') == [a for a in row['attempts'] if a['status'] == 'passed']
        and type(checkpoint.get('candidate_cursor')) is int and checkpoint['candidate_cursor'] >= 0
        and isinstance(checkpoint.get('rejected'), list)
        and row.get('candidate_rejection_count') == len(checkpoint['rejected']), 'EXTENSION_CANDIDATE_LEDGER_CHANGED')
    records, numbers = [], []
    for number, attempt in enumerate(row['attempts'], 1):
        name = f'damage-{number:03d}'
        path = f'sources/{spec["source_id"]}/cases/{name}'
        e._require(attempt.get('source_id') == spec['source_id'] and attempt.get('case_id') == name
            and attempt.get('path') == path, 'EXTENSION_ATTEMPT_PATH_INVALID')
        numbers.append(attempt.get('candidate_number'))
        recipe_path = e._file(folder, f'private/attempt-recipes/{name}.json')
        e._bind(recipe_path, bindings, e._digest(attempt.get('attempt_recipe_sha256')))
        recipe = q.read(recipe_path)
        e._require(q.recipe_key(recipe) == attempt.get('recipe_key'), 'EXTENSION_ATTEMPT_RECIPE_CHANGED')
        if attempt['status'] == 'failed':
            e._require(attempt.get('machine_validated') is False, 'FAILED_EXTENSION_MARKED_VALID')
            continue
        e._require(attempt.get('machine_validated') is True and attempt.get('family') == recipe.get('family'),
                   'EXTENSION_CASE_STATE_INVALID')
        case = folder / 'cases' / name
        e._bind(e._file(case, 'private/seal.json'), bindings, e._digest(attempt.get('accepted_seal_sha256')))
        e._digest(attempt.get('model_sha256'))
        e._require(q.verify_seal(case) and q.read(e._file(case, 'private/recipe.json')) == recipe
            and q.recipe_key(q.read(e._file(case, 'private/mutation.json'))) == attempt['recipe_key'],
            'EXTENSION_SEALED_RECIPE_CHANGED')
        modes = attempt.get('prompt_modes')
        e._require(isinstance(modes, list) and len(modes) == len(set(modes)) and 'world' in modes
            and set(modes) <= {'world', 'host_wall'}, 'EXTENSION_MODES_INVALID')
        pair_records = _pairs(q.make_pair_records(source_id=spec['source_id'], damage_number=number,
            case_path=path, model_sha256=attempt['model_sha256'],
            request_hashes={mode: q.sha256(e._file(case, f'public/request-{mode}.txt')) for mode in modes},
            recipe=recipe, remaining=target - len(records)))
        e._require(bool(pair_records), 'EXTENSION_CASE_WITHOUT_PAIRS')
        checked = e._case(round_root, pair_records[0], bindings)
        e._require(checked['model_sha256'] == attempt['model_sha256'] and set(checked['requests']) == set(modes),
                   'EXTENSION_CASE_BINDING_CHANGED')
        receipt = old._read(e._file(case, 'private/extension-binding.json'), bindings)
        e._require(receipt.get('schema_version') == x.SCHEMA and receipt.get('baseline') == plan['baseline_binding']
            and receipt.get('code_sha256') == build['code_sha256']
            and receipt.get('geometry_guard') == 'text2ifc/dataset-geometry-guard/2.0'
            and receipt.get('request_profile') == q.PROFILE
            and receipt.get('source_admission') == ('fresh-this-round' if plan['replacement'] else 'hash-bound-first-pass-reused'),
            'EXTENSION_CASE_RECEIPT_CHANGED')
        records.extend(pair_records)
    e._require(all(type(n) is int and n > 0 for n in numbers) and numbers == sorted(set(numbers))
        and (not numbers or checkpoint['candidate_cursor'] >= numbers[-1]), 'EXTENSION_CANDIDATE_CURSOR_CHANGED')
    e._require(records == row['pairs'], 'EXTENSION_RESULT_PAIR_MAPPING_CHANGED')
    return row


def _collect_inputs(batch, repository, code_root):
    baseline, _, bindings, base_stats, rounds = old._collect_inputs(batch, repository, code_root)
    e._bind(Path(__file__), bindings)
    production = batch / 'private/production'
    root = batch / 'private' / x.ROUND
    for row in baseline:
        e._digest(row['source_sha256'])
    for authoring_root in (production, batch / 'private' / s.ROUND):
        for path in (authoring_root / 'sources').glob('*/private/checkpoint.json'):
            for digest in q.read(e._pair_safe_path(path))['cache_sha256'].values():
                e._digest(digest)
    build = old._read(e._file(root, 'build.json'), bindings)
    e._require(build.get('schema_version') == x.SCHEMA and build.get('round') == x.ROUND
        and build.get('per_mother_cap') == PER_MOTHER_CAP and build.get('append_existing_pairs') == APPEND_PAIRS
        and build.get('target_total_pairs') == ACTIVE_SOURCES * PER_MOTHER_CAP
        and type(build.get('max_attempts')) is int and 1 <= build['max_attempts'] <= 30
        and build.get('workers') in (1, 2) and build.get('provider_calls') == 0
        and base_stats['pairs_per_ifc'] == PER_MOTHER_CAP - APPEND_PAIRS, 'EXTENSION_BUILD_INVALID')
    old._program(build, root / 'code-snapshot', x.program_bindings(), bindings, code_root)
    _round_environment(batch, repository, build['execution_environment'], bindings)
    prior = {row['source_id']: row for row in baseline}
    excluded = prior.get(EXCLUDED_SOURCE)
    e._require(excluded is not None and excluded['pairs'] == [] and len(prior) == ACTIVE_SOURCES,
               'ONLY_ZERO_PAIR_HISTORICAL_SOURCE_MAY_BE_REPLACED')
    specs, plans = build.get('sources'), build.get('plans')
    e._require(isinstance(specs, list) and isinstance(plans, list) and len(specs) == len(plans) == ACTIVE_SOURCES
        and all(isinstance(spec, dict) and q._valid_source_id(spec.get('source_id')) for spec in specs),
        'EXTENSION_ACTIVE_CATALOGUE_INVALID')
    ids = [spec['source_id'] for spec in specs]
    e._require(len({sid.casefold() for sid in ids}) == len(ids)
        and set(ids) == (set(prior) - {EXCLUDED_SOURCE}) | {REPLACEMENT_SOURCE}
        and ids == [plan.get('source_id') for plan in plans], 'EXTENSION_ACTIVE_SOURCE_SET_CHANGED')
    replacement = next(spec for spec in specs if spec['source_id'] == REPLACEMENT_SOURCE)
    e._require(replacement['source_sha256'] not in {row['source_sha256'] for row in baseline}
        and REPLACEMENT_SOURCE not in prior, 'REPLACEMENT_SOURCE_ALREADY_USED')
    links = build.get('replacements')
    e._require(isinstance(links, list) and len(links) == 1 and links[0].get('old_source_id') == EXCLUDED_SOURCE
        and links[0].get('old_source_sha256') == excluded['source_sha256']
        and links[0].get('new_source_id') == REPLACEMENT_SOURCE
        and links[0].get('new_source_sha256') == replacement['source_sha256']
        and isinstance(links[0].get('reason'), str) and bool(links[0]['reason']), 'REPLACEMENT_LINK_CHANGED')
    round_summary = old._read(e._file(root, 'summary.json'), bindings)
    e._require(round_summary.get('schema_version') == x.SCHEMA and round_summary.get('status') == 'finished'
        and round_summary.get('worker_errors') == [] and round_summary.get('mothers_finished') == ACTIVE_SOURCES
        and round_summary.get('mother_round_target') == ACTIVE_SOURCES and round_summary.get('provider_calls') == 0,
        'EXTENSION_ROUND_NOT_TERMINAL_OR_WORKER_ERRORS')
    e._require({p.name for p in (root / 'sources').iterdir()} == set(ids), 'EXTENSION_SOURCE_DIRECTORY_SET_CHANGED')
    raw, summaries, merged, catalogue = [], [], [], []
    for spec, plan in zip(specs, plans, strict=True):
        new = spec['source_id'] == REPLACEMENT_SOURCE
        previous = prior.get(spec['source_id'])
        e._require(new or spec == previous['source'], 'EXTENSION_EXISTING_SOURCE_METADATA_CHANGED')
        value = spec.get('input_path')
        e._require(isinstance(value, str) and bool(value), 'SOURCE_INPUT_PATH_INVALID')
        source_path = e._pair_safe_path(Path(value)) if Path(value).is_absolute() else e._file(repository, value)
        e._bind(source_path, bindings, e._digest(spec['source_sha256']))
        borrowed, hashes = x._borrowed(batch, previous) if previous else ([], {})
        numbers = x.plan_targets(len(previous['pairs']) if previous else 0, len(borrowed),
            replacement=new, cap=PER_MOTHER_CAP, append=APPEND_PAIRS)
        chosen = borrowed[:numbers['borrowed_pairs']]
        old_binding = x._baseline_binding(batch, spec['source_id'])
        binding = {'round': x.ROUND, 'source_id': spec['source_id'], 'replacement': new,
            'baseline': old_binding, 'borrowed_bound_hashes': hashes,
            'target_added_pairs': numbers['target_added_pairs'], 'per_mother_cap': PER_MOTHER_CAP}
        e._require(plan.get('replacement') is new and all(plan.get(k) == v for k, v in numbers.items())
            and plan.get('borrowed_variants') == chosen and plan.get('borrowed_bound_hashes') == hashes
            and plan.get('baseline_binding') == binding and plan.get('max_attempts') == build['max_attempts'],
            'EXTENSION_PLAN_OR_BORROWED_VARIANT_CHANGED')
        seed = q.read(production / 'sources' / spec['source_id'] / 'private/checkpoint.json')['configuration']['seed'] if previous else 20261010
        e._require(plan.get('seed') == seed, 'EXTENSION_SEED_CHANGED')
        for path, digest in hashes.items():
            e._bind(e._pair_safe_path(Path(path)), bindings, digest)
        row = _mother(root, spec, plan, build, bindings)
        raw.append(row)
        mapped = [{**pair, 'case_path': pair['case_path'].rsplit('/', 1)[0] + '/' + x.ROUND + '-' +
            pair['case_path'].rsplit('/', 1)[1]} for pair in row['pairs']]
        added = [*[item['pair'] for item in chosen], *mapped]
        all_pairs = [*(previous['pairs'] if previous else []), *added]
        x.verify_pair_uniqueness(all_pairs)
        e._require(len(all_pairs) <= PER_MOTHER_CAP, 'FINAL_MOTHER_CAP_EXCEEDED')
        summary = old._read(e._file(root / 'sources' / spec['source_id'], 'mother-summary.json'), bindings)
        expected = {'schema_version': x.SCHEMA, 'source_id': spec['source_id'], 'replacement': new,
            'status': 'complete' if len(added) == numbers['target_added_pairs'] else 'incomplete',
            'baseline_pairs': numbers['baseline_pairs'], 'target_added_pairs': numbers['target_added_pairs'],
            'target_new_damage_pairs': numbers['target_new_damage_pairs'], 'borrowed_pairs': len(chosen),
            'new_damage_pairs': len(row['pairs']), 'added_pairs': len(added), 'total_pairs': len(all_pairs),
            'missing_added_pairs': numbers['target_added_pairs'] - len(added), 'new_damages': len(row['cases']),
            'attempted_cases': row['attempted_cases'],
            'failed_attempts': sum(a['status'] == 'failed' for a in row['attempts']),
            'stop_reason': row['stop_reason'], 'source_unchanged': True, 'borrowed_variants': chosen,
            'pairs': added, 'result_sha256': q.sha256(root / 'sources' / spec['source_id'] / 'result.json'),
            'baseline_binding': binding, 'provider_calls': 0, 'human_review': 'pending_human_review'}
        e._require(summary == expected, 'EXTENSION_MOTHER_SUMMARY_CHANGED')
        summaries.append(summary)
        cases = [*(previous['cases'] if previous else []), *[{**case, 'origin_path': case['path'],
            'path': case['path'].rsplit('/', 1)[0] + '/' + x.ROUND + '-' + case['path'].rsplit('/', 1)[1],
            'attempt_round': x.ROUND} for case in row['cases']]]
        attempts = [*(previous['attempts'] if previous else []), *row['attempts']]
        merged.append({'source_id': spec['source_id'], 'source': spec, 'source_sha256': spec['source_sha256'],
            'pairs': all_pairs, 'cases': cases, 'attempts': attempts,
            'attempted_cases': len(attempts), 'stop_reason': summary['stop_reason']})
        catalogue.append({'source': spec, 'active': True, 'replacement': new})
    aggregate = {'target_added_pairs': sum(r['target_added_pairs'] for r in summaries),
        'added_pairs': sum(r['added_pairs'] for r in summaries), 'borrowed_pairs': sum(r['borrowed_pairs'] for r in summaries),
        'new_damage_pairs': sum(r['new_damage_pairs'] for r in summaries),
        'new_damages': sum(r['new_damages'] for r in summaries), 'attempted_cases': sum(r['attempted_cases'] for r in summaries),
        'failed_attempts': sum(r['failed_attempts'] for r in summaries),
        'missing_added_pairs': sum(r['missing_added_pairs'] for r in summaries),
        'completed_active_mothers': sum(r['total_pairs'] == PER_MOTHER_CAP for r in summaries)}
    e._require(all(round_summary.get(k) == v for k, v in aggregate.items()), 'EXTENSION_ROUND_SUMMARY_CHANGED')
    per_round = [{'source_id': r['source_id'], **{key:r[key] for key in ('total_pairs', 'added_pairs',
        'borrowed_pairs', 'new_damages', 'attempted_cases', 'failed_attempts', 'stop_reason')}} for r in summaries]
    e._require(round_summary.get('per_mother') == per_round, 'EXTENSION_ROUND_MOTHER_MAPPING_CHANGED')
    cases = [c for row in merged for c in row['cases']]
    pairs = [p for row in merged for p in row['pairs']]
    recipe_keys = [(row['source_sha256'], c['recipe_key']) for row in merged for c in row['cases']]
    e._require(len(set(recipe_keys)) == len(recipe_keys), 'DUPLICATE_ACCEPTED_RECIPE')
    e._require(len({c['model_sha256'] for c in cases}) == len(cases), 'DUPLICATE_ACCEPTED_DAMAGE_BYTES')
    x.verify_pair_uniqueness(pairs)
    extension_record = {'name': x.ROUND, 'root': str(root), 'build_sha256': bindings[str(root / 'build.json')],
        'code_sha256': build['code_sha256'], 'mothers': len(raw), 'pairs': aggregate['added_pairs'],
        'distinct_damages': aggregate['new_damages'], 'borrowed_pairs': aggregate['borrowed_pairs'],
        'new_damage_pairs': aggregate['new_damage_pairs'], 'attempted_cases': aggregate['attempted_cases'],
        'failed_attempts': aggregate['failed_attempts'], 'candidate_rejections': sum(r['candidate_rejection_count'] for r in raw),
        'stop_reasons': dict(Counter(r['stop_reason'] for r in raw)), 'worker_errors': []}
    rounds = [*rounds, extension_record]
    historical = {row['source_id']: row for row in baseline}
    active = {row['source_id']: row for row in merged}
    historical.update(active)
    catalogue.append({'source': excluded['source'], 'active': False, 'replacement': False,
        'replaced_by': REPLACEMENT_SOURCE, 'reason': links[0]['reason']})
    catalogue.sort(key=lambda r:r['source']['source_id'])
    per_mother = [{'source_id': sid, 'source_sha256': row['source_sha256'], 'active': sid in active,
        'replacement': sid == REPLACEMENT_SOURCE, 'status': ('complete' if len(row['pairs']) == PER_MOTHER_CAP else 'incomplete')
            if sid in active else 'excluded', 'pairs': len(row['pairs']), 'total_pairs': len(row['pairs']),
        'distinct_damages': len(row['cases']), 'cap': PER_MOTHER_CAP,
        'missing_pairs': PER_MOTHER_CAP - len(row['pairs']) if sid in active else 0,
        'attempted_cases': row['attempted_cases'], 'failed_attempts': sum(a['status'] == 'failed' for a in row['attempts']),
        'stop_reason': row['stop_reason'], 'replaced_by': REPLACEMENT_SOURCE if sid == EXCLUDED_SOURCE else None}
        for sid, row in sorted(historical.items())]
    stats = {**base_stats, 'pairs': len(pairs), 'distinct_damages': len(cases),
        'source_models': len({p['source_id'] for p in pairs}), 'catalogue_source_models': len(historical),
        'historical_source_models': len(historical), 'active_source_models': ACTIVE_SOURCES,
        'pairs_per_ifc': PER_MOTHER_CAP, 'target_pairs': ACTIVE_SOURCES * PER_MOTHER_CAP,
        'quota_complete': all(len(row['pairs']) == PER_MOTHER_CAP for row in merged),
        'missing_pairs': ACTIVE_SOURCES * PER_MOTHER_CAP - len(pairs),
        'completed_mothers': sum(len(row['pairs']) == PER_MOTHER_CAP for row in merged),
        'mothers_without_pairs': [r['source_id'] for r in merged if not r['pairs']],
        'replacements': links, 'borrowed_pairs': aggregate['borrowed_pairs'],
        'extension_pairs': aggregate['added_pairs'], 'extension_new_damage_pairs': aggregate['new_damage_pairs'],
        'extension_new_damages': aggregate['new_damages'], 'rounds': rounds, 'supplement_rounds': rounds[1:],
        'attempted_cases': sum(r['attempted_cases'] for r in rounds), 'failed_attempts': sum(r['failed_attempts'] for r in rounds),
        'candidate_rejections': sum(r['candidate_rejections'] for r in rounds),
        'failed_counts_by_round': {r['name']:r['failed_attempts'] for r in rounds},
        'damage_families': dict(Counter(c['family'] for c in cases)), 'locator_modes': dict(Counter(p['locator_mode'] for p in pairs)),
        'pair_task_kinds': dict(Counter(p['task_kind'] for p in pairs)),
        'budget_levels': dict(Counter(e.budget_level_for_primary_targets(p['primary_target_count']) for p in pairs)),
        'removed_openings_checked': sum(c.get('removed_openings',0) for c in cases),
        'wall_checked_damages': sum(c.get('wall_check_applicable') is True for c in cases),
        'per_mother': per_mother, 'request_transforms_checked': len(pairs),
        'native_evidence': {**base_stats['native_evidence'], 'source_receipts_reused': len(historical),
            'case_receipts_reused': len(cases), 'fresh_source_sha_checks': len(historical),
            'fresh_seal_and_receipt_binding_checks': len(cases), 'extension_source_receipts_reused': ACTIVE_SOURCES - 1,
            'new_source_admissions_in_extension_round': 1,
            'scope': 'All historical and active source SHA/cache plus same-version zero-finding schema/EXPRESS receipts checked; '
                'replacement source freshly admitted in r2. Finalization reuses native receipts, with zero fresh native runs.'}}
    return merged, pairs, bindings, stats, rounds, catalogue


def _copies(batch, merged, catalogue, bindings):
    receipts = old._collect_copies(batch, merged, bindings)
    production = batch / 'private/production'
    for item in catalogue:
        if not item['replacement']:
            continue
        sid = item['source']['source_id']
        source, target = batch / 'private' / x.ROUND / 'sources' / sid, production / 'sources' / sid
        expected = {name:q.sha256(e._file(source,name)) for name in sorted(old.CACHE_FILES)}
        if target.exists():
            e._require(target.is_dir() and {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()} == set(expected)
                and all(q.sha256(e._file(target,name)) == digest for name,digest in expected.items()),
                'NEW_SOURCE_CACHE_EXISTS_DIFFERENT')
        else:
            target.mkdir()
            for name in expected:
                destination=target/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                with destination.open('xb') as stream:
                    stream.write(e._file(source,name).read_bytes())
        for name,digest in expected.items():
            e._bind(e._file(source,name),bindings,digest)
            e._bind(e._file(target,name),bindings,digest)
        receipts.append({'kind':'source-cache','origin':source.relative_to(batch).as_posix(),
            'target':target.relative_to(batch).as_posix(),'files':expected})
    for row in merged:
        for case in row['cases']:
            if case.get('attempt_round') != x.ROUND:
                continue
            origin = e._pair_safe_path(batch / 'private' / x.ROUND / e._relative(case['origin_path']))
            target = e._pair_safe_path(production / e._relative(case['path']))
            tree = old._tree(origin)
            if target.exists():
                e._require(q.verify_seal(target) and old._tree(target)==tree, 'COLLECTION_COPY_EXISTS_DIFFERENT')
            else:
                shutil.copytree(origin,target,copy_function=shutil.copyfile)
            e._require(q.verify_seal(origin) and q.verify_seal(target) and old._tree(origin)==old._tree(target)==tree,
                       'COLLECTION_COPY_CHANGED')
            for name,digest in tree['files'].items():
                e._bind(e._file(origin,name),bindings,digest)
                e._bind(e._file(target,name),bindings,digest)
            receipts.append({'origin':origin.relative_to(batch).as_posix(),'target':target.relative_to(batch).as_posix(),**tree})
    return receipts


def _check_locked(batch, repository, code_root=None):
    final = batch / 'private/finalization'
    e._require((final/'summary.json').is_file() and not (final/'failed.json').exists()
        and not (batch/'private/evaluation/export-failed.json').exists(), 'INCOMPLETE_OR_FAILED_DELIVERY')
    summary=q.read(e._file(final,'summary.json'))
    e._require(summary.get('schema_version')==SCHEMA and summary.get('status')=='complete', 'DELIVERY_SUMMARY_INVALID')
    authorities={str(final/name) for name in ('collection.json','pairs.json','checks.json','catalogue.json')}
    authorities.add(str(batch/'private/evaluation/export.json'))
    e._require(set(summary.get('authority_sha256',{}))==authorities,'DELIVERY_AUTHORITY_SET_CHANGED')
    old._recheck(summary['authority_sha256'])
    checks=q.read(final/'checks.json')
    e._require(checks.get('schema_version')==SCHEMA and checks.get('passed') is True
        and checks.get('stats')=={k:summary.get(k) for k in checks.get('stats',{})},'DELIVERY_STATS_CHANGED')
    collection=q.read(final/'collection.json')
    e._require(collection.get('schema_version')==SCHEMA and collection.get('status')=='collected'
        and collection.get('batch')==str(batch) and collection.get('repository')==str(repository),'COLLECTION_RECEIPT_INVALID')
    _,environment=_environment(repository,code_root)
    e._require(_environment_identity(collection.get('execution_environment'))==_environment_identity(environment),
               'DELIVERY_LOADED_ENVIRONMENT_CHANGED')
    e._require(not (batch/'PAUSE').exists(),'PAUSED_BATCH_CANNOT_BE_DELIVERED')
    old._recheck(collection['bound_hashes'])
    for item in collection['copied_cases']:
        origin=e._pair_safe_path(batch/e._relative(item['origin']))
        target=e._pair_safe_path(batch/e._relative(item['target']))
        if item.get('kind')=='source-cache':
            for name,digest in item['files'].items():
                e._require(q.sha256(e._file(origin,name))==q.sha256(e._file(target,name))==digest,'SOURCE_CACHE_COPY_CHANGED')
        else:
            expected={key:item[key] for key in ('files','directories')}
            e._require(q.verify_seal(origin) and q.verify_seal(target) and old._tree(origin)==old._tree(target)==expected,
                       'COLLECTION_COPY_CHANGED')
    pairs=q.read(final/'pairs.json')
    receipt=q.read(batch/'private/evaluation/export.json')
    e._require([{key:p[key] for key in e.PAIR_FIELDS} for p in pairs]
        ==[{key:p[key] for key in e.PAIR_FIELDS} for p in receipt['pair_provenance']], 'DELIVERY_EXPORT_MAPPING_CHANGED')
    checked=handoff.check_pair_export_v2(batch/'public',batch/'private/evaluation')
    e._require(summary.get('public_export')==checked and all(summary[key]==checked[key]
        for key in ('pairs','distinct_damages','source_models')),'DELIVERY_EXPORT_SUMMARY_CHANGED')
    return summary


def check_delivery(batch, *, repository=ROOT, code_root=None):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    with q._exclusive_lock(batch/'private/RUN.lock'):
        return _check_locked(batch,repository,code_root)


def deliver_batch(batch, *, repository=ROOT, code_root=None):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    production,public,evaluation=e._roots(batch/'public',batch/'private/evaluation')
    final=batch/'private/finalization'
    with q._exclusive_lock(batch/'private/RUN.lock'):
        if final.exists():
            return _check_locked(batch,repository,code_root)
        e._require(not public.exists() and not evaluation.exists(),'NEW_OUTPUT_REQUIRED')
        code_root,environment=_environment(repository,code_root)
        merged,pairs,bindings,stats,rounds,catalogue=_collect_inputs(batch,repository,code_root)
        final.mkdir()
        stage='collect_sealed_cases_and_source_cache'
        try:
            copies=_copies(batch,merged,catalogue,bindings)
            old._recheck(bindings)
            old._write_new(final/'pairs.json',pairs)
            old._write_new(final/'catalogue.json',{'schema_version':SCHEMA,'historical_sources':catalogue,
                'replacements':stats['replacements'],'active_source_models':ACTIVE_SOURCES})
            old._write_new(final/'collection.json',{'schema_version':SCHEMA,'status':'collected','batch':str(batch),
                'repository':str(repository),'execution_environment':environment,'rounds':rounds,
                'bound_hashes':bindings,'copied_cases':copies,'pairs_sha256':q.sha256(final/'pairs.json'),
                'provider_calls':0,'scope':'Exact new sealed cases and replacement cache only; all historic evidence retained.'})
            old._write_new(final/'checks.json',{'schema_version':SCHEMA,'passed':True,'stats':stats,
                'scope':'All three rounds, historical source admissions, seals, recipes, unique damage/modes, cap30 and replacement checked.'})
            stage='export_public_pairs'
            exported=handoff.export_pairs(production,public,evaluation,pairs,source_models=stats['source_models'])
            old._recheck(bindings)
            authority={str(path):q.sha256(path) for path in (
                final/'pairs.json',final/'catalogue.json',final/'collection.json',final/'checks.json',evaluation/'export.json')}
            summary={'schema_version':SCHEMA,'status':'complete',**stats,'public_export':exported,
                'authority_sha256':authority,'validation_scope':'Offline source/program/cache/seal/hash and reused native/EXPRESS gates; '
                'exact model bytes, all public 1.4 transforms and six-column CSV/whitelist checked. No fresh native, Provider or repair capability test.'}
            old._write_new(final/'summary.json',summary)
            stage='verify_completed_delivery'
            return _check_locked(batch,repository,code_root)
        except Exception as exc:
            old._write_new(final/'failed.json',{'schema_version':SCHEMA,'status':'failed','stage':stage,
                'error':f'{type(exc).__name__}: {exc}','provider_calls':0,
                'scope':'All partial files/error receipts retained; no automatic deletion, replacement or retry.'})
            raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('deliver','check'))
    parser.add_argument('--batch',type=Path,default=q.DEFAULT_OUTPUT)
    parser.add_argument('--repository',type=Path,default=ROOT)
    parser.add_argument('--code-root',type=Path)
    args=parser.parse_args(argv)
    try:
        action=deliver_batch if args.command=='deliver' else check_delivery
        result=action(args.batch,repository=args.repository,code_root=args.code_root)
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({'schema_version':SCHEMA,'status':'failed','error':f'{type(exc).__name__}: {exc}'},ensure_ascii=False),flush=True)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
