"""Durable per-mother state for pair generation and same-version resume.

Checkpoint is the mutable scheduling authority; accepted case bytes and seals
are immutable. Started/uncommitted attempts are not promoted from file presence.
"""
from __future__ import annotations

import contextlib
import json
from pathlib import Path
import re
import shutil
import time
import traceback

import ifcopenshell


def process_mother(spec, repository, production, *, pairs_per_ifc=25, max_attempts=30, seed=20261010, resume=False):
    from . import dataset_pairs as q
    from .repair_comparison.batch_cases import _pair_safe_path
    if not 1 <= pairs_per_ifc <= 25 or not 1 <= max_attempts <= 30:
        raise ValueError('PAIR_QUOTA_1_TO_25_AND_ATTEMPT_CAP_1_TO_30_REQUIRED')
    if not q._valid_source_id(spec.get('source_id')):
        raise ValueError('UNSAFE_SOURCE_ID')
    repository, production = Path(repository).resolve(), _pair_safe_path(Path(production))
    source = _pair_safe_path(repository / spec['input_path'])
    source_hash = spec['source_sha256']
    if not 0 < source.stat().st_size < 20_000_000 or q.sha256(source) != source_hash:
        raise ValueError('SOURCE_SIZE_OR_SHA_CHANGED')
    root = production / 'sources' / spec['source_id']
    if root.exists() and not resume:
        raise FileExistsError('NEW_MOTHER_REQUIRED_OR_USE_RESUME')
    pause = production.parents[1] / 'PAUSE'
    if pause.exists() and not root.exists():
        return {'source_id': spec['source_id'], 'source': spec, 'status': 'incomplete', 'source_unchanged': True,
                'source_native_passed': False, 'source_sha256': source_hash, 'class_counts': {}, 'eligible_counts': {},
                'pairs': [], 'cases': [], 'attempts': [], 'attempted_cases': 0, 'candidate_rejection_count': 0,
                'stop_reason': 'cooperative_pause', 'elapsed_seconds': 0, 'target_pairs': pairs_per_ifc}
    root.mkdir(parents=True, exist_ok=True)
    with q._exclusive_lock(root / 'private/MOTHER.lock'):
        return _locked(q, spec, source, production, root, pairs_per_ifc=pairs_per_ifc,
                       max_attempts=max_attempts, seed=seed, resume=resume, pause=pause)


def _locked(q, spec, source, production, root, *, pairs_per_ifc, max_attempts, seed, resume, pause):
    started = time.monotonic()
    config = q._configuration(spec, pairs_per_ifc=pairs_per_ifc, max_attempts=max_attempts, seed=seed)
    checkpoint = root / 'private/checkpoint.json'
    reference = root / 'private/reference.ifc'
    source_hash = spec['source_sha256']
    if checkpoint.exists():
        state = q.read(checkpoint)
        if not resume or state.get('configuration') != config:
            raise ValueError('CHECKPOINT_CONFIGURATION_OR_PROGRAM_MISMATCH')
        if state.get('schema_version') != 'text2ifc/dataset-pair-checkpoint/1.0':
            raise ValueError('CHECKPOINT_SCHEMA_MISMATCH')
        if q.read(root / 'private/source.json') != spec or q.sha256(reference) != source_hash:
            raise ValueError('CHECKPOINT_SOURCE_BINDING_CHANGED')
    else:
        if any((root / name).exists() for name in ('cases', 'result.json', 'private/attempts.json')):
            raise ValueError('CHECKPOINT_MISSING_WITH_EXISTING_ATTEMPTS')
        if (root / 'private/source.json').exists() and q.read(root / 'private/source.json') != spec:
            raise ValueError('CHECKPOINT_SOURCE_METADATA_CHANGED')
        q.write_json(root / 'private/source.json', spec)
        if not reference.exists():
            shutil.copyfile(source, reference)
        if q.sha256(reference) != source_hash:
            raise ValueError('PRIVATE_REFERENCE_COPY_MISMATCH')
        state = {'schema_version': 'text2ifc/dataset-pair-checkpoint/1.0', 'configuration': config,
                 'attempts': [], 'cases': [], 'pairs': [], 'candidate_cursor': 0, 'rejected': [], 'cache_sha256': {}}
        q.write_json(checkpoint, state)
    cache_paths = ('private/reference.ifc', 'private/source.json', 'private/source-validation.json', 'private/inventory.json')
    if state['cache_sha256']:
        if set(state['cache_sha256']) != set(cache_paths) or any(
            q.sha256(root / name) != expected for name, expected in state['cache_sha256'].items()):
            raise ValueError('CHECKPOINT_ADMISSION_CACHE_CHANGED')
        admission, inv = q.read(root / 'private/source-validation.json'), q.read(root / 'private/inventory.json')
        if not (admission.get('passed') is True and admission.get('input_sha256') == source_hash
                and admission.get('finding_count') == 0 and admission.get('express_rules') is True
                and admission.get('schema') == 'IFC2X3' and admission.get('ifcopenshell_version') == ifcopenshell.version):
            raise ValueError('CHECKPOINT_SOURCE_NATIVE_RECEIPT_INVALID')
    else:
        history = root / 'private/admission-history'
        history.mkdir(exist_ok=True)
        number = len(list(history.glob('validation-*.json'))) + 1
        with (history / f'admission-{number:03d}.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            admission = {**q.native_validate(reference), 'input_sha256': source_hash}
            q.write_json(history / f'validation-{number:03d}.json', admission)
            q.write_json(root / 'private/source-validation.json', admission)
            if not admission['passed']:
                raise ValueError('SOURCE_NATIVE_VALIDATION_FAILED')
            inv = q.prepare_inventory(reference)
            q.write_json(root / 'private/inventory.json', inv)
        state['cache_sha256'] = {name: q.sha256(root / name) for name in cache_paths}
        q.write_json(checkpoint, state)
    attempts = state['attempts']
    if not isinstance(attempts, list) or len(attempts) > max_attempts:
        raise ValueError('CHECKPOINT_ATTEMPT_LEDGER_INVALID')
    cursor = state.get('candidate_cursor')
    if type(cursor) is not int or cursor < 0:
        raise ValueError('CHECKPOINT_CANDIDATE_CURSOR_INVALID')
    numbers = [row.get('candidate_number') for row in attempts]
    if any(type(n) is not int or n <= 0 for n in numbers) or numbers != sorted(set(numbers)) or (numbers and cursor < numbers[-1]):
        raise ValueError('CHECKPOINT_CANDIDATE_CURSOR_INVALID')
    cases, pairs, seen_bytes = [], [], set()
    for index, row in enumerate(attempts, 1):
        name = f'damage-{index:03d}'
        expected_path = (root / 'cases' / name).relative_to(production).as_posix()
        if row.get('case_id') != name or row.get('path') != expected_path or row.get('source_id') != spec['source_id']:
            raise ValueError('CHECKPOINT_ATTEMPT_PATH_INVALID')
        recipe_path = root / f'private/attempt-recipes/{name}.json'
        if q.sha256(recipe_path) != row.get('attempt_recipe_sha256'):
            raise ValueError('CHECKPOINT_ATTEMPT_RECIPE_CHANGED')
        recipe = q.read(recipe_path)
        if q.recipe_key(recipe) != row['recipe_key']:
            raise ValueError('CHECKPOINT_RECIPE_KEY_CHANGED')
        if row['status'] == 'started':
            row.update(status='failed', machine_validated=False,
                       errors={'interrupted': 'INTERRUPTED_BEFORE_TERMINAL_COMMIT; attempt remains spent'})
            q.write_json(root / f'private/attempt-errors/{name}-interrupted.json', row['errors'])
        if row['status'] == 'passed':
            folder = root / 'cases' / name
            if not q.verify_seal(folder) or q.sha256(folder / 'private/seal.json') != row.get('accepted_seal_sha256'):
                raise ValueError('ACCEPTED_CASE_SEAL_CHANGED')
            meta = q.read(folder / 'case.json')
            if not (meta['machine_validated'] is True and meta['status'] == 'passed'
                    and meta['source_sha256'] == source_hash and meta['damaged_sha256'] == row['model_sha256']):
                raise ValueError('ACCEPTED_CASE_STATE_CHANGED')
            if q.recipe_key(q.read(folder / 'private/recipe.json')) != row['recipe_key']:
                raise ValueError('ACCEPTED_CASE_RECIPE_CHANGED')
            records = q.make_pair_records(source_id=spec['source_id'], damage_number=index, case_path=row['path'],
                model_sha256=row['model_sha256'], request_hashes={mode: q.sha256(folder / f'public/request-{mode}.txt')
                    for mode in row['prompt_modes']}, recipe=recipe, remaining=pairs_per_ifc - len(pairs))
            if not records or row['model_sha256'] in seen_bytes:
                raise ValueError('CHECKPOINT_DUPLICATE_OR_EXCESS_ACCEPTED_DAMAGE')
            cases.append(row.copy())
            pairs.extend(records)
            seen_bytes.add(row['model_sha256'])
        elif row['status'] != 'failed':
            raise ValueError('CHECKPOINT_ATTEMPT_STATUS_INVALID')
    if cases != state['cases'] or pairs != state['pairs']:
        raise ValueError('CHECKPOINT_ACCEPTANCE_LEDGER_MISMATCH')
    state['cases'], state['pairs'] = cases, pairs

    def save():
        q.write_json(checkpoint, state)
        q.write_json(root / 'private/attempts.json', attempts)
        q.write_json(root / 'private/pairs.json', pairs)
        q.write_json(root / 'private/candidate-rejections.json', state['rejected'])
        q.write_json(root / 'private/progress.json', {'target_pairs': pairs_per_ifc, 'accepted_pairs': len(pairs),
            'distinct_damages': len(cases), 'attempted_cases': len(attempts), 'candidate_rejections': len(state['rejected']),
            'candidate_cursor': state['candidate_cursor'], 'attempt_cap': max_attempts, 'provider_calls': 0})

    def stopped():
        return len(pairs) >= pairs_per_ifc or len(attempts) >= max_attempts or pause.exists()

    def rejected(number):
        state['candidate_cursor'] = number
        save()

    save()
    if not stopped():
        original = ifcopenshell.open(str(reference))
        baseline = q.product_state(original)
        candidates, excluded = q._candidate_inventory(inv)
        q.write_json(root / 'private/target-exclusions.json', excluded)
        iterator = q.iter_prepared_recipes(candidates, seed=seed, rejected=state['rejected'],
            after_candidate=state['candidate_cursor'], stopped=stopped, on_reject=rejected)
        for candidate_number, recipe in iterator:
            if stopped():
                break
            number = len(attempts) + 1
            folder = root / 'cases' / f'damage-{number:03d}'
            recipe_path = root / f'private/attempt-recipes/{folder.name}.json'
            q.write_json(recipe_path, recipe)
            row = {'source_id': spec['source_id'], 'case_id': folder.name, 'path': folder.relative_to(production).as_posix(),
                   'candidate_number': candidate_number, 'recipe_key': q.recipe_key(recipe), 'family': recipe['family'],
                   'severity': recipe['severity'], 'status': 'started', 'machine_validated': False,
                   'attempt_recipe_sha256': q.sha256(recipe_path)}
            attempts.append(row)
            state['candidate_cursor'] = candidate_number
            save()  # Reservation must be durable before entering the IFC writer.
            pending_row = row.copy()
            records = []
            passed = False
            try:
                with (root / f'private/{folder.name}.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                    result, prompt_checks, walls, meshes = q._check_damage(reference, inv, baseline, original, recipe, folder)
                passed = result['machine_validated'] and result['damaged_sha256'] not in seen_bytes
                pending_row.update(status='passed' if passed else 'failed', machine_validated=passed,
                    model_sha256=result['damaged_sha256'], deleted_counts=result['deleted_counts'],
                    property_changes=result['property_changes'], prompt_modes=list(prompt_checks),
                    wall_check_applicable=walls['applicable'],
                    removed_openings=sum(bool(t.get('opening_guid')) and not t['preserve_opening'] for t in recipe['deletions']),
                    errors=[] if passed else {'native': q.read(folder / 'private/validation.json')['finding_count'],
                        'preservation': q.read(folder / 'private/preservation.json').get('errors', []),
                        'prompts': {mode: p.get('errors', []) for mode, p in prompt_checks.items() if not p['passed']},
                        'walls': walls.get('errors', []), 'meshes': meshes['errors'],
                        'duplicate_damaged_bytes': result['damaged_sha256'] in seen_bytes})
                if passed:
                    records = q.make_pair_records(source_id=spec['source_id'], damage_number=number, case_path=row['path'],
                        model_sha256=result['damaged_sha256'], request_hashes={mode: q.sha256(folder / f'public/request-{mode}.txt')
                            for mode in prompt_checks}, recipe=recipe, remaining=pairs_per_ifc - len(pairs))
                    pending_row['accepted_seal_sha256'] = q.sha256(folder / 'private/seal.json')
            except Exception as exc:
                passed = False
                pending_row.update(status='failed', machine_validated=False, errors={'exception': f'{type(exc).__name__}:{exc}'[:400]})
                q.write_json(root / f'private/attempt-errors/{folder.name}.json', {'error': pending_row['errors'], 'traceback': traceback.format_exc()})
            next_state = {**state, 'attempts': attempts[:-1] + [pending_row],
                          'cases': cases + [pending_row.copy()] if passed else cases,
                          'pairs': pairs + records if passed else pairs}
            # Single durable terminal commit. No finally may overwrite this
            # with partial local state if a BaseException arrives mid-acceptance.
            q.write_json(checkpoint, next_state)
            state = next_state
            attempts, cases, pairs = state['attempts'], state['cases'], state['pairs']
            if passed:
                seen_bytes.add(pending_row['model_sha256'])
            save()
    unchanged = source_hash == q.sha256(source) == q.sha256(reference)
    reason = ('pair_quota_met' if len(pairs) >= pairs_per_ifc else 'attempt_cap_reached' if len(attempts) >= max_attempts
              else 'cooperative_pause' if pause.exists() else 'candidate_catalogue_exhausted')
    result = {'source_id': spec['source_id'], 'source': spec, 'status': 'complete' if len(pairs) == pairs_per_ifc and unchanged else 'incomplete',
        'target_pairs': pairs_per_ifc, 'source_unchanged': unchanged, 'source_native_passed': admission['passed'],
        'source_sha256': source_hash, 'class_counts': inv['class_counts'], 'eligible_counts': {k: len(v) for k, v in inv['targets'].items()},
        'pairs': pairs, 'cases': cases, 'attempts': attempts, 'attempted_cases': len(attempts),
        'candidate_rejection_count': len(state['rejected']), 'stop_reason': reason, 'elapsed_seconds': round(time.monotonic() - started, 3),
        'conservative_exclusions': ['source-coordinate uniqueness retained', 'frozen inventory still requires named equal-geometry peers']}
    q.write_json(root / 'result.json', result)
    return result
