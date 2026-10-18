"""Generate checked IFC/request pairs in one local batch, without LLM calls.

The frozen dataset_batch engine/profile are reused unchanged. Pair quotas differ
from independent-damage counts; unsupported shapes never spend an IFC attempt.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import hashlib
import itertools
import json
import math
import os
import random
import re
import shutil
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

import ifcopenshell

from .dataset_batch.engine import CLASSES, FAMILIES, _wrong_value, apply_recipe, seal_case, verify_seal, write_json
from .dataset_batch.pilot import _preserved_meshes
from .dataset_batch.prompt_check_v3 import audit_prompt
from .dataset_batch.prompts_v3 import PROFILE, prepare_inventory, prepare_recipe, render_prompts
from .dataset_batch.validation import native_validate, product_state, program_hash, sha256
from .dataset_batch.wall_check import check_wall_closure

DEFAULT_OUTPUT = ROOT / 'dataset/processed/ifc-repair/formal-40-pairs-25-20261010'
SCHEMA = 'text2ifc/dataset-pairs-batch/1.1'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _valid_source_id(value):
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *{f'COM{i}' for i in range(1, 10)}, *{f'LPT{i}' for i in range(1, 10)}}
    return (isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,59}', value) is not None
            and not value.endswith('.') and value.split('.')[0].upper() not in reserved)


def recipe_key(recipe):
    # Same deletion/property operation is one damage, regardless of locator.
    value = {
        'deletions': sorted((t['guid'], bool(t.get('preserve_opening', False))) for t in recipe['deletions']),
        'properties': sorted((p['guid'], p['pset_name'], p['property_name'], p['value_type'],
                              json.dumps(p['after'], ensure_ascii=False, sort_keys=True))
                             for p in recipe.get('property_changes', []))}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def _deletion_stream(rows, *, max_deleted):
    """Traverse every single target, rotating multi-target subsets, then singles' Cartesian combinations."""
    longest = max(len(group) for group in rows)
    sizes = list(dict.fromkeys((1, 2, 3, max(4, math.ceil(longest * .3)))))
    for offset in range(longest):
        for size in sizes:
            selected = [group[(offset + j) % len(group)] for group in rows
                        for j in range(min(size, len(group), max(1, max_deleted // len(rows))))]
            if len(selected) <= max_deleted:
                yield [{**t, 'preserve_opening': False} for t in selected]
    # This is lazy: it is stopped when the checked-pair quota/attempt cap is met.
    for selected in itertools.product(*rows):
        yield [{**t, 'preserve_opening': False} for t in selected]


def _property_stream(properties):
    for offset, prop in enumerate(properties):
        yield [{**prop, 'after': _wrong_value(prop, 0)}]
        for size in (2, 3):
            selected = properties[offset:offset + size]
            if len(selected) == size:
                yield [{**p, 'after': _wrong_value(p, 0)} for p in selected]


def iter_raw_recipes(inventory, *, seed=20261010, max_deleted=30, stopped=None):
    """Round robin across present families, attributes and their mixtures, without a first-six cutoff."""
    if not 1 <= max_deleted <= 30:
        raise ValueError('MAX_DELETED_MUST_BE_1_TO_30')
    rng = random.Random(seed)
    targets = {}
    for family in CLASSES:
        rows = sorted(inventory['targets'].get(family, []), key=lambda row: row['guid'])
        rng.shuffle(rows)
        targets[family] = rows
    properties = sorted((p for p in inventory.get('properties', []) if p['ifc_class'] in CLASSES.values()),
                        key=lambda p: (p['guid'], p.get('pset_name', ''), p.get('property_name', '')))
    rng.shuffle(properties)
    available = [(name, classes) for name, classes in FAMILIES.items() if all(targets[c] for c in classes)]

    def geometry(family, classes, *, mixed=False):
        mandatory = {targets[c][0]['guid'] for c in classes if len(targets[c]) == 1}
        if mixed and all(p['guid'] in mandatory for p in properties):
            return
        for index, deletions in enumerate(_deletion_stream([targets[c] for c in classes], max_deleted=max_deleted)):
            if stopped is not None and stopped():
                return
            changes = []
            if mixed:
                deleted = {t['guid'] for t in deletions}
                prop = next((properties[(index + j) % len(properties)] for j in range(len(properties))
                             if properties[(index + j) % len(properties)]['guid'] not in deleted), None)
                if prop is None:
                    continue
                changes = [{**prop, 'after': _wrong_value(prop, 0)}]
            severity = 'light' if len(deletions) == len(classes) else 'medium' if len(deletions) <= 3 * len(classes) else 'heavy'
            yield {'family': family + ('_attributes' if mixed else ''), 'severity': severity,
                   'deletions': deletions, 'property_changes': changes}

    streams = [iter(geometry(family, classes)) for family, classes in available]
    if properties:
        streams.append(iter({'family': 'attributes', 'severity': 'light' if len(changes) == 1 else 'medium',
                             'deletions': [], 'property_changes': changes} for changes in _property_stream(properties)))
        streams.extend(iter(geometry(family, classes, mixed=True)) for family, classes in available)
        windows = targets['window']
        door_props = [p for p in properties if p['ifc_class'] == 'IfcDoor']
        if windows and len(windows) <= max_deleted and door_props:
            streams.append(iter([{'family': 'all_windows_door_attributes', 'severity': 'heavy',
                'deletions': [{**t, 'preserve_opening': False} for t in windows],
                'property_changes': [{**door_props[0], 'after': _wrong_value(door_props[0], 0)}]}]))
    seen = set()
    while streams:
        remaining = []
        for stream in streams:
            if stopped is not None and stopped():
                return
            try:
                recipe = next(stream)
            except StopIteration:
                continue
            remaining.append(stream)
            key = recipe_key(recipe)
            if key not in seen:
                seen.add(key)
                yield recipe
        streams = remaining


def _location_supported(recipe):
    # v1.3 requires an unambiguous world request for every accepted damage.
    for t in [*recipe['deletions'], *recipe.get('property_changes', [])]:
        if not t.get('storey', {}).get('name_unique') or not t.get('geometry', {}).get('world_unique'):
            return False
        if t.get('host') and not t['host'].get('world_unique'):
            return False
    return True


def iter_prepared_recipes(inventory, *, seed=20261010, rejected=None, after_candidate=0, stopped=None, on_reject=None):
    rejected = rejected if rejected is not None else []
    for number, raw in enumerate(iter_raw_recipes(inventory, seed=seed, stopped=stopped), 1):
        if stopped is not None and stopped():
            return
        if number <= after_candidate:
            continue
        try:
            if not _location_supported(raw):
                raise ValueError('WORLD_OR_STOREY_LOCATION_NOT_UNIQUE')
            recipe = prepare_recipe(raw)
            if not render_prompts(recipe)['world']:
                raise ValueError('WORLD_REQUEST_NOT_APPLICABLE')
        except (ValueError, KeyError) as exc:
            rejected.append({'candidate_number': number, 'family': raw['family'], 'recipe_key': recipe_key(raw),
                             'reason': f'{type(exc).__name__}:{exc}'[:300]})
            if on_reject is not None:
                on_reject(number)
            continue
        yield number, recipe


@contextlib.contextmanager
def _exclusive_lock(path):
    """OS lock released on crash; its harmless file can stay for safe resume."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if handle.seek(0, 2) == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('BATCH_OR_MOTHER_ALREADY_RUNNING') from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _configuration(spec, *, pairs_per_ifc, max_attempts, seed):
    return {'source_sha256': spec['source_sha256'], 'source_id': spec['source_id'],
            'pairs_per_ifc': pairs_per_ifc, 'max_attempts': max_attempts, 'seed': seed,
            'profile': PROFILE, 'code_sha256': _program_bindings()}


def _candidate_inventory(inventory):
    """Conservative single-target eligibility, followed by whole-recipe peer checks."""
    targets, excluded = {}, []
    for family in CLASSES:
        targets[family] = []
        for target in inventory['targets'].get(family, []):
            single = {'deletions': [{**target, 'preserve_opening': False}], 'property_changes': []}
            try:
                if not _location_supported(single):
                    raise ValueError('WORLD_OR_STOREY_LOCATION_NOT_UNIQUE')
                if not render_prompts(prepare_recipe(single))['world']:
                    raise ValueError('WORLD_REQUEST_NOT_APPLICABLE')
                targets[family].append(target)
            except (ValueError, KeyError) as exc:
                excluded.append({'guid': target['guid'], 'class': target['ifc_class'], 'reason': str(exc)[:250]})
    properties = [p for p in inventory.get('properties', [])
                  if _location_supported({'deletions': [], 'property_changes': [p]})]
    return {**inventory, 'targets': targets, 'properties': properties}, excluded


def make_pair_records(*, source_id, damage_number, case_path, model_sha256, request_hashes, recipe, remaining):
    damage_id = f'{source_id}-d{damage_number:03d}'
    count = len(recipe['deletions']) + len({p['guid'] for p in recipe.get('property_changes', [])})
    kind = 'mixed' if recipe['deletions'] and recipe.get('property_changes') else 'geometry' if recipe['deletions'] else 'property'
    return [{'case_id': f'{damage_id}-{mode}', 'source_id': source_id, 'damage_id': damage_id,
             'locator_mode': mode, 'case_path': case_path, 'request_relative_path': f'public/request-{mode}.txt',
             'model_sha256': model_sha256, 'request_sha256': request_hashes[mode],
             'primary_target_count': count, 'task_kind': kind}
            for mode in ('world', 'host_wall') if mode in request_hashes][:max(0, remaining)]


def _check_damage(reference, inventory, baseline, original, recipe, folder):
    result = apply_recipe(reference, recipe, folder, inventory=inventory, baseline_state=baseline, prompt_profile=PROFILE)
    manifest = read(folder / 'private/mutation.json')
    damaged = ifcopenshell.open(str(folder / 'public/model.ifc'))
    prompts = {mode: audit_prompt(original, damaged, manifest, mode,
               (folder / f'public/request-{mode}.txt').read_text(encoding='utf-8'))
               for mode, meta in result['prompt_templates'].items() if meta['applicable']}
    walls = check_wall_closure(reference, folder / 'public/model.ifc', manifest)
    meshes = _preserved_meshes(original, damaged, manifest)
    for name, value in (('prompt', prompts), ('wall', walls), ('mesh', meshes)):
        write_json(folder / f'private/{name}-check.json', value)
    prompt_ok = 'world' in prompts and all(p['passed'] for p in prompts.values())
    passed = result['status'] == 'passed' and prompt_ok and walls['passed'] and meshes['passed']
    if passed:
        shutil.copyfile(folder / 'public/request-world.txt', folder / 'public/request.txt')
    result.update(schema_version='text2ifc/ifc-repair-dataset-case/1.1', status='passed' if passed else 'failed',
                  machine_validated=passed, primary_prompt='world' if passed else None, information_sufficient=prompt_ok,
                  wall_check_passed=walls['passed'], wall_check_applicable=walls['applicable'],
                  independent_mesh_check_passed=meshes['passed'],
                  additional_evidence=['private/prompt-check.json', 'private/wall-check.json', 'private/mesh-check.json']
                                      + (['public/request.txt'] if passed else []))
    write_json(folder / 'case.json', result)
    seal_case(folder)
    if not verify_seal(folder):
        raise ValueError('FINAL_CASE_SEAL_INVALID')
    return result, prompts, walls, meshes


def process_mother(spec, repository, production, *, pairs_per_ifc=25, max_attempts=30, seed=20261010, resume=False):
    from .dataset_pair_resume import process_mother as execute
    return execute(spec, repository, production, pairs_per_ifc=pairs_per_ifc,
                   max_attempts=max_attempts, seed=seed, resume=resume)


def _program_bindings():
    paths = [Path(__file__), ROOT / 'scripts/ifc_repair/dataset_pair_export.py',
             ROOT / 'scripts/ifc_repair/prepare_pair_mothers.py', ROOT / 'scripts/ifc_repair/dataset_pair_resume.py',
             ROOT / 'scripts/ifc_repair/audit_initial_dataset.py',
             *[ROOT / 'scripts/ifc_repair/repair_comparison' / name for name in ('batch_cases.py', 'budget.py', 'contracts.py')],
             *sorted((ROOT / 'src/text2ifc_ifc_repair').glob('*.py')),
             *sorted((ROOT / 'scripts/ifc_repair/dataset_batch').glob('*.py'))]
    return {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths}


def _source_progress(production, specs):
    progress = []
    for spec in specs:
        path = production / 'sources' / spec['source_id'] / 'private/progress.json'
        if path.exists():
            progress.append({'source_id': spec['source_id'], **read(path)})
    return progress


def _write_batch_report(batch, specs, results, errors, *, pairs_per_ifc, finished=False, export=None, final_source_bindings=None):
    all_pairs = [pair for result in results for pair in result['pairs']]
    all_cases = [case for result in results for case in result['cases']]
    attempts = [case for result in results for case in result['attempts']]
    production = batch / 'private/production'
    progress = _source_progress(production, specs)
    complete = (finished and not errors and len(results) == len(specs)
                and all(s['status'] == 'complete' for s in results) and export is not None)
    summary = {'schema_version': SCHEMA, 'status': 'complete' if complete else 'incomplete' if finished else 'running',
               'source_models': len(specs), 'completed_mothers': sum(s['status'] == 'complete' for s in results),
               'target_pairs': len(specs) * pairs_per_ifc, 'pairs_per_ifc': pairs_per_ifc,
               'machine_validated_pairs': len(all_pairs), 'distinct_damages': len(all_cases),
               'attempted_cases': len(attempts), 'failed_attempts': sum(c['status'] != 'passed' for c in attempts),
               'candidate_rejections': sum(s['candidate_rejection_count'] for s in results),
               'worker_errors': errors, 'source_hashes_unchanged': (len(results) == len(specs) and all(s['source_unchanged'] for s in results)
                   and final_source_bindings is not False),
               'locator_modes': dict(Counter(p['locator_mode'] for p in all_pairs)),
               'damage_families': dict(Counter(c['family'] for c in all_cases)),
               'pair_task_kinds': dict(Counter(p['task_kind'] for p in all_pairs)),
               'removed_openings_checked': sum(c['removed_openings'] for c in all_cases),
               'wall_checked_damages': sum(c['wall_check_applicable'] for c in all_cases),
               'provider_calls': 0, 'system_repair_tested': False, 'human_reviewed_pairs': 0,
               'request_profile': PROFILE, 'core_program_sha256': program_hash(),
               'per_mother': [{'source_id': s['source_id'], 'status': s['status'], 'pairs': len(s['pairs']),
                   'distinct_damages': len(s['cases']), 'attempted_cases': s['attempted_cases'],
                   'failed_attempts': sum(c['status'] != 'passed' for c in s['attempts']),
                   'stop_reason': s['stop_reason']} for s in sorted(results, key=lambda r: r['source_id'])],
               'progress': progress, 'public_export': export,
               'missing_pairs': len(specs) * pairs_per_ifc - len(all_pairs),
               'mothers_without_result': [s['source_id'] for s in specs if s['source_id'] not in {r['source_id'] for r in results}],
               'scope': 'Native IFC2X3 schema+EXPRESS, recorded damage/preservation, actual public requests, '
                        'applicable wall closure, at most three surviving meshes per independent damage. '
                        'No system repair, live capability, human acceptance or blind-test claim.'}
    write_json(batch / 'summary.json', summary)
    state = '完成' if complete else '尚未补足或遇到失败' if finished else '生成中'
    lines = ['# text2IFC 40母本批量损伤配对', '',
             f"当前状态：**{state}**。机器校验通过的IFC＋请求对 {len(all_pairs)}/{summary['target_pairs']}；"
             f"独立损伤IFC {len(all_cases)} 份；完成配额的母本 {summary['completed_mothers']}/{len(specs)}。", '',
             '同一损伤的world、host_wall两种合格请求分别计题；普通梁柱及含梁柱的混合题只使用适用的世界坐标请求。'
             '独立损伤按实际配方去重，同一损伤每种定位最多一题。', '',
             '唯一数量权威：[summary.json](summary.json)。公开交接入口：[public/inputs.csv](public/inputs.csv)；'
             '仅挂载public目录给被测系统。其余子目录是私有制作及评价记录。', '',
             '母本清单：[private/production/mother-sources.json](private/production/mother-sources.json)；'
             '配对映射和导出核验：[private/evaluation/export.json](private/evaluation/export.json)。', '',
             f"实际损伤尝试 {len(attempts)} 次，其中失败 {summary['failed_attempts']} 次，工作进程异常 {len(errors)} 条。"
             '候选形状/定位预筛与IFC落盘尝试分开计数；每母本落盘尝试上限30，不以其他母本补缺口。', '',
             '通过损伤均重新打开并使用IfcOpenShell schema＋EXPRESS校验、精确损伤/保全核对、实际公开请求信息检查、'
             '适用墙体补全检查和最多三个保留构件的世界网格抽查。机器校验不代替人工审核或系统修复成功率。', '',
             '新增派生题均标为机器校验、人工待审。formal-021～040是新增母本别名；保留原登记与来源证据，'
             '编号不提升原有审核级别。相同母本、建筑族与损伤的定位变体须在同一评估分组，不能跨开发/测试拆分。', '',
             '源文件和旧批次均不改写；参考母本、删除身份、配方和校验细节仅保存在private。失败配方、日志和'
             '未完成暂存目录保留。若需要暂停，在本根目录创建PAUSE，脚本会在完成当前损伤后停止新尝试。'
             '使用dataset_pairs resume --dataset 本根目录可在同一源码和配置下从检查点继续；暂停标记也会归档保留。', '',
             '|母本|合格对|独立损伤|尝试|终态|', '|---|---:|---:|---:|---|']
    lines.extend(f"|{s['source_id']}|{s['pairs']}|{s['distinct_damages']}|{s['attempted_cases']}|{s['stop_reason']}|"
                 for s in summary['per_mother'])
    if errors:
        lines.extend(['', '异常详细记录：[private/production/worker-errors.json](private/production/worker-errors.json)。'])
    (batch / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return summary


def run_batch(specs, batch, *, repository=ROOT, pairs_per_ifc=25, max_attempts=30, workers=2, seed=20261010, resume=False):
    from .dataset_pair_export import check_pair_export, export_pairs
    from .repair_comparison.batch_cases import _pair_safe_path
    batch, repository = _pair_safe_path(Path(batch)), Path(repository).resolve()
    if batch.exists() and not resume:
        raise FileExistsError('NEW_BATCH_ROOT_REQUIRED:' + str(batch))
    if resume and not batch.is_dir():
        raise ValueError('EXISTING_BATCH_REQUIRED_FOR_RESUME')
    if not 1 <= pairs_per_ifc <= 25 or not 1 <= max_attempts <= 30 or workers not in (1, 2):
        raise ValueError('INVALID_PAIR_QUOTA_ATTEMPT_CAP_OR_WORKERS')
    ids = [spec['source_id'].casefold() for spec in specs]
    hashes = [spec['source_sha256'] for spec in specs]
    if (not specs or len(set(ids)) != len(specs) or len(set(hashes)) != len(specs)
            or not all(_valid_source_id(s.get('source_id')) for s in specs)):
        raise ValueError('DISTINCT_SOURCE_IDS_AND_SOURCE_BYTES_REQUIRED')
    for spec in specs:
        source = _pair_safe_path(repository / spec['input_path'])
        if source.is_relative_to(batch) or not 0 < source.stat().st_size < 20_000_000 or sha256(source) != spec['source_sha256']:
            raise ValueError('SOURCE_BINDING_OR_SIZE_INVALID:' + spec['source_id'])
    bindings = _program_bindings()
    batch.mkdir(parents=True, exist_ok=resume)
    production = batch / 'private/production'
    production.mkdir(parents=True, exist_ok=resume)
    with _exclusive_lock(batch / 'private/RUN.lock'):
        return _run_locked(specs, batch, production, repository, pairs_per_ifc=pairs_per_ifc,
                           max_attempts=max_attempts, workers=workers, seed=seed, bindings=bindings, resume=resume)


def _run_locked(specs, batch, production, repository, *, pairs_per_ifc, max_attempts, workers, seed, bindings, resume):
    from .dataset_pair_export import check_pair_export, export_pairs
    if resume:
        build = read(production / 'build.json')
        expected = {'schema_version': SCHEMA, 'pairs_per_ifc': pairs_per_ifc, 'max_attempts_per_ifc': max_attempts,
                    'workers': workers, 'seed': seed, 'request_profile': PROFILE, 'code_sha256': bindings}
        if any(build.get(key) != value for key, value in expected.items()):
            raise ValueError('BATCH_RESUME_CONFIG_OR_PROGRAM_MISMATCH')
        if read(production / 'mother-sources.json')['sources'] != specs:
            raise ValueError('BATCH_RESUME_MOTHERS_CHANGED')
        if any(sha256(production / 'private/code-snapshot' / name) != value for name, value in bindings.items()):
            raise ValueError('BATCH_RESUME_CODE_SNAPSHOT_CHANGED')
        history = production / 'private/run-history.json'
        runs = read(history)['runs'] if history.exists() else []
        if (batch / 'summary.json').exists():
            previous = read(batch / 'summary.json')
            runs.append({'status': previous['status'], 'attempted_cases': previous['attempted_cases'],
                         'failed_attempts': previous['failed_attempts'], 'worker_errors': previous['worker_errors']})
        write_json(history, {'runs': runs})
        if (batch / 'PAUSE').exists():
            _archive_in_batch(batch, [batch / 'PAUSE'], label='pause')
    else:
        _freeze_batch(specs, production, repository, pairs_per_ifc=pairs_per_ifc, max_attempts=max_attempts,
                      workers=workers, seed=seed, bindings=bindings)
    write_json(production / 'private/run-owner.json', {'pid': os.getpid(), 'started_unix': time.time(), 'resume': resume})
    results, errors = [], []
    _write_batch_report(batch, specs, results, errors, pairs_per_ifc=pairs_per_ifc)
    waiting = iter(enumerate(specs))
    exhausted = False
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        while pending or not exhausted:
            while len(pending) < workers and not exhausted and not (batch / 'PAUSE').exists():
                try:
                    i, spec = next(waiting)
                except StopIteration:
                    exhausted = True
                    break
                pending[pool.submit(process_mother, spec, repository, production, pairs_per_ifc=pairs_per_ifc,
                    max_attempts=max_attempts, seed=seed + i, resume=resume)] = spec
            if not pending:
                break
            done, _ = concurrent.futures.wait(pending, timeout=30, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                spec = pending.pop(future)
                try:
                    results.append(future.result())
                except Exception as exc:
                    errors.append({'source_id': spec['source_id'], 'error': f'{type(exc).__name__}:{exc}'[:500],
                                   'traceback': traceback.format_exc()})
            write_json(production / 'worker-errors.json', errors)
            _write_batch_report(batch, specs, results, errors, pairs_per_ifc=pairs_per_ifc)
    source_unchanged = all(sha256(repository / s['input_path']) == s['source_sha256'] for s in specs)
    if not source_unchanged:
        errors.append({'source_id': 'batch', 'error': 'SOURCE_CHANGED_DURING_BATCH'})
    if _program_bindings() != bindings:
        errors.append({'source_id': 'batch', 'error': 'PROGRAM_CHANGED_DURING_BATCH'})
    export = None
    if not errors and len(results) == len(specs) and all(r['status'] == 'complete' for r in results):
        ordered = sorted(results, key=lambda r: r['source_id'])
        all_pairs = [p for r in ordered for p in r['pairs']]
        write_json(production / 'pairs.json', all_pairs)
        try:
            existing = (batch / 'public', batch / 'private/evaluation')
            if any(path.exists() for path in existing):
                try:
                    export = check_pair_export(*existing)
                    if export['pairs'] != len(all_pairs):
                        raise ValueError('EXISTING_EXPORT_QUOTA_MISMATCH')
                    receipt = read(existing[1] / 'export.json')
                    saved = [{key: item.get(key) for key in pair} for pair, item in
                             zip(all_pairs, receipt['pair_provenance'], strict=True)]
                    if saved != all_pairs:
                        raise ValueError('EXISTING_EXPORT_RECIPE_MAPPING_CHANGED')
                except Exception:
                    export = None
                    _archive_in_batch(batch, list(existing), label='export')
            if export is None:
                export = export_pairs(production, *existing, all_pairs, source_models=len(specs))
        except Exception as exc:
            errors.append({'source_id': 'export', 'error': f'{type(exc).__name__}:{exc}', 'traceback': traceback.format_exc()})
    write_json(production / 'worker-errors.json', errors)
    return _write_batch_report(batch, specs, results, errors, pairs_per_ifc=pairs_per_ifc,
                               finished=True, export=export, final_source_bindings=source_unchanged)


def _archive_in_batch(batch, paths, *, label):
    from .repair_comparison.batch_cases import _pair_safe_path
    archive = batch / 'private/history' / f'{label}-{time.time_ns()}'
    for path in paths:
        path = _pair_safe_path(path)
        if not path.exists():
            continue
        if not path.is_relative_to(batch) or not archive.resolve().is_relative_to(batch):
            raise ValueError('ARCHIVE_MUST_STAY_IN_BATCH')
        if path.is_dir():
            for item in path.rglob('*'):
                _pair_safe_path(item)
        archive.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(archive / path.name))


def _freeze_batch(specs, production, repository, *, pairs_per_ifc, max_attempts, workers, seed, bindings):
    write_json(production / 'mother-sources.json', {'schema_version': SCHEMA, 'sources': specs})
    write_json(production / 'build.json', {'schema_version': SCHEMA, 'pairs_per_ifc': pairs_per_ifc,
        'max_attempts_per_ifc': max_attempts, 'workers': workers, 'seed': seed, 'request_profile': PROFILE,
        'core_program_sha256': program_hash(), 'code_sha256': bindings, 'python_version': sys.version,
        'ifcopenshell_version': ifcopenshell.version, 'provider_calls': 0,
        'resume_policy': 'Same frozen code/config/source only; checkpoint cursor skips failed/interrupted attempts, no budget reset.'})
    for name, expected in bindings.items():
        target = production / 'private/code-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / name, target)
        if sha256(target) != expected:
            raise ValueError('CODE_CHANGED_WHILE_FREEZING')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    generate = commands.add_parser('generate')
    generate.add_argument('--sources', type=Path)
    generate.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    generate.add_argument('--pairs-per-ifc', type=int, default=25)
    generate.add_argument('--max-attempts', type=int, default=30)
    generate.add_argument('--workers', type=int, default=2)
    generate.add_argument('--seed', type=int, default=20261010)
    status = commands.add_parser('status')
    status.add_argument('--dataset', type=Path, default=DEFAULT_OUTPUT)
    check = commands.add_parser('check')
    check.add_argument('--dataset', type=Path, default=DEFAULT_OUTPUT)
    resume = commands.add_parser('resume')
    resume.add_argument('--dataset', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        if args.command == 'generate':
            from .prepare_pair_mothers import build_mother_specs
            specs = read(args.sources)['sources'] if args.sources else build_mother_specs(ROOT)
            summary = run_batch(specs, args.output, pairs_per_ifc=args.pairs_per_ifc, max_attempts=args.max_attempts,
                                workers=args.workers, seed=args.seed)
            batch = args.output
        elif args.command == 'resume':
            batch = args.dataset
            production = batch / 'private/production'
            build = read(production / 'build.json')
            specs = read(production / 'mother-sources.json')['sources']
            summary = run_batch(specs, batch, pairs_per_ifc=build['pairs_per_ifc'], max_attempts=build['max_attempts_per_ifc'],
                                workers=build['workers'], seed=build['seed'], resume=True)
        else:
            batch = args.dataset
            summary = read(batch / 'summary.json')
            if args.command == 'check':
                from .dataset_pair_export import check_pair_export
                if summary['status'] != 'complete':
                    raise ValueError('COMPLETE_BATCH_REQUIRED')
                export = check_pair_export(batch / 'public', batch / 'private/evaluation')
                if export['pairs'] != summary['target_pairs']:
                    raise ValueError('PUBLIC_PAIR_QUOTA_MISMATCH')
        brief = {name: summary[name] for name in ('status', 'source_models', 'completed_mothers', 'target_pairs',
            'machine_validated_pairs', 'distinct_damages', 'attempted_cases', 'failed_attempts', 'locator_modes')}
        print(json.dumps({'event': 'summary', **brief, 'worker_error_count': len(summary['worker_errors']),
                          'report': str(batch.resolve() / 'REPORT.md')}, ensure_ascii=False))
        return 0 if args.command == 'status' or summary['status'] == 'complete' else 2
    except Exception as exc:
        print(json.dumps({'event': 'summary', 'status': 'failed', 'error': f'{type(exc).__name__}:{exc}'}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
