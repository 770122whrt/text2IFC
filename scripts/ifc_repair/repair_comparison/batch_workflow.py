"""Persistent bounded batch execution over the existing isolated repair carrier.

Only this controller reads run results. Its public output is one completion or
blocking summary, one results table, and at most two files per task.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
import xml.etree.ElementTree as ET

from . import demo_workflow as carrier
from .batch_cases import (PROPERTY_UNITS_REQUEST_CONVENTION, load_candidates,
                          load_pair_candidates, materialize_public, select_rounds)
from .budget import FIXED_BUDGET_POLICY_VERSION, fixed_budget_profile
from .container_tools import docker
from .contracts import read_json, safe_path, sha256, write_json
from .controller_owner import task_owner
from .group_config import GROUPS, SCALABLE_STAGE, default_providers
from .isolated_b import PROPERTY_RUNTIME_IMAGE
from .isolated_dsh import CLARIFICATION_FAILURE
from .ledger import Ledger, TERMINAL, encode
from .results import export_task

TASK_BUDGET_ONLY = 'per-task-only/no-batch-total'
PLAN_SCHEMA = 'repair-comparison-small-rounds/0.1'
PARALLEL_PLAN_SCHEMA = 'repair-comparison-small-rounds/0.2'
QWEN_PRIORITY_PLAN_SCHEMA = 'repair-comparison-small-rounds/0.3'
PARALLEL_PLAN_SCHEMAS = {PARALLEL_PLAN_SCHEMA, QWEN_PRIORITY_PLAN_SCHEMA}
CLI = [sys.executable, '-m', 'scripts.ifc_repair.repair_comparison.demo_workflow']
CHECK_SCRIPT = '''
import json, sys
import ifcopenshell
import ifcopenshell.validate
try:
    model = ifcopenshell.open(sys.argv[1])
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    errors = logger.statements
    result = {'status': 'failed' if errors else 'passed', 'passed': not errors,
        'schema': model.schema, 'validator': 'ifcopenshell.validate',
        'version': ifcopenshell.version, 'express_rules': True,
        'diagnostic_count': len(errors), 'diagnostics': [
            {'attribute': str(e.get('attribute', ''))[:160],
             'message': str(e.get('message', ''))[:640]} for e in errors[:5]]}
except Exception as error:
    result = {'status': 'error', 'passed': False,
              'error': type(error).__name__ + ': ' + str(error)[:1024]}
print(json.dumps(result, ensure_ascii=False))
'''


class ControllerLedger(Ledger):
    """Allow bounded SQLite writer waits; never retry a transaction body/task."""
    LOCK_WAIT_SECONDS = 30

    def _connect(self):
        db = super()._connect()
        db.execute('PRAGMA busy_timeout='+str(int(self.LOCK_WAIT_SECONDS*1000)))
        return db


def _need(value, reason):
    if not value:
        raise ValueError(reason)


def _digest(value):
    return hashlib.sha256(encode(value).encode('utf8')).hexdigest()


def plan(root):
    root = safe_path(Path(root))
    value = read_json(root/'batch.json')
    body = {k: v for k, v in value.items() if k != 'sha256'}
    _need(value.get('schema_version') in {PLAN_SCHEMA, *PARALLEL_PLAN_SCHEMAS}
          and value.get('sha256') == _digest(body),
          'FROZEN_BATCH_CHANGED')
    _need(value.get('budget_policy') == TASK_BUDGET_ONLY, 'TASK_BUDGET_POLICY_REQUIRED')
    _need(type(value.get('retain_debug', False)) is bool, 'INVALID_RETENTION_POLICY')
    _need(value.get('request_convention') in {None, PROPERTY_UNITS_REQUEST_CONVENTION}, 'INVALID_REQUEST_CONVENTION')
    if value['schema_version'] in PARALLEL_PLAN_SCHEMAS:
        scheduler = value.get('scheduler', {})
        capacity = scheduler.get('max_running')
        keys = {'max_running'}
        if value['schema_version'] == QWEN_PRIORITY_PLAN_SCHEMA:
            keys.update({'priority', 'qwen_max_running'})
            _need(scheduler.get('priority') == 'qwen-first'
                  and type(scheduler.get('qwen_max_running')) is int
                  and scheduler['qwen_max_running'] == 2, 'INVALID_QWEN_PRIORITY_POLICY')
        _need(set(scheduler) == keys and type(capacity) is int and 1 <= capacity <= 7,
              'INVALID_CONCURRENCY_CAPACITY')
        _need(value.get('selection') in {'full', 'two-rounds'}, 'INVALID_BATCH_SELECTION')
        if value.get('input_format') == 'pairs':
            checks = value.get('input_format_checks', {})
            _need(set(checks) == set(value['configuration']['case_ids'])
                  and all(v.get('passed') is True for v in checks.values()), 'INPUT_IFC_FORMAT_FAILED')
    return value


def _set_scheduler(value, concurrency, qwen_first):
    _need(type(concurrency) is int and 1 <= concurrency <= 7, 'INVALID_CONCURRENCY_CAPACITY')
    _need(type(qwen_first) is bool, 'INVALID_QWEN_PRIORITY_POLICY')
    value['schema_version'] = QWEN_PRIORITY_PLAN_SCHEMA if qwen_first else PARALLEL_PLAN_SCHEMA
    value['scheduler'] = {'max_running': concurrency}
    if qwen_first:
        value['scheduler'].update(priority='qwen-first', qwen_max_running=2)


def prepare(root, dataset, *, seed=42, second_count=2, providers=None,
            property_model=None, mode='live', scope='two-rounds', input_format='auto',
            concurrency=1, default_level=None, index_path=None, groups=None, case_ids=None, retain_debug=False,
            delivery_receipt=None, request_convention=None, qwen_first=False):
    root, dataset = safe_path(Path(root)), safe_path(Path(dataset))
    _need(mode in {'live', 'offline'}, 'INVALID_EXPERIMENT_MODE')
    _need(type(retain_debug) is bool, 'INVALID_RETENTION_POLICY')
    _need(request_convention in {None, PROPERTY_UNITS_REQUEST_CONVENTION}, 'INVALID_REQUEST_CONVENTION')
    _need(not root.exists(), 'BATCH_EXISTS_USE_RESUME')
    _need(scope in {'full', 'two-rounds'}, 'INVALID_BATCH_SELECTION')
    _need(input_format in {'auto', 'dataset', 'pairs'}, 'INVALID_INPUT_FORMAT')
    _need(type(concurrency) is int and 1 <= concurrency <= 7, 'INVALID_CONCURRENCY_CAPACITY')
    _need(type(qwen_first) is bool, 'INVALID_QWEN_PRIORITY_POLICY')
    if input_format == 'auto':
        input_format = 'dataset' if (dataset/'summary.json').exists() else 'pairs'
    candidates = load_candidates(dataset) if input_format == 'dataset' else load_pair_candidates(
        dataset, default_level=default_level, index_path=index_path,
        case_ids=case_ids, delivery_receipt=delivery_receipt)
    if case_ids is not None:
        _need(scope == 'full', 'TWO_ROUNDS_HAVE_AUTOMATIC_CASE_SELECTION')
        _need(case_ids, 'CASE_SELECTION_REQUIRED')
        _need(len(set(case_ids)) == len(case_ids), 'DUPLICATE_CASE_SELECTION')
        known = {c['case_id'] for c in candidates}
        _need(set(case_ids) <= known, 'UNKNOWN_CASE_SELECTION')
        candidates = [c for c in candidates if c['case_id'] in set(case_ids)]
    if scope == 'full':
        cases = candidates if input_format == 'pairs' else sorted(candidates, key=lambda c: c['case_id'])
        selected = {'round1': [], 'round2': cases, 'coverage': {'selected_count': len(cases)}, 'missing_coverage': []}
        arms = list(groups or 'ABCDEFG')
        _need(arms and len(set(arms)) == len(arms) and set(arms) <= set(GROUPS), 'INVALID_EXPERIMENT_ARMS')
        case_groups = {c['case_id']: arms[:] for c in cases}
    else:
        _need(groups is None, 'TWO_ROUNDS_HAVE_FIXED_GROUPS')
        selected = select_rounds(candidates, seed=seed, second_count=second_count)
        _need(all(selected['coverage'][r]['shortfall'] == 0 for r in ('round1', 'round2')),
              'INSUFFICIENT_ELIGIBLE_CASES')
        cases = selected['round1'] + selected['round2']
        case_groups = {c['case_id']: list('BEF') for c in selected['round1']}
        case_groups.update({c['case_id']: list('ABCDEFG') for c in selected['round2']})
    public = materialize_public(cases, root/'cases', **(
        {'request_convention': request_convention} if request_convention is not None else {}))
    ids = [c['case_id'] for c in cases]
    b = None
    if any(set(case_groups[c['case_id']]) & set('BEF')
           and c['category'] in {'property', 'mixed', 'unknown'} for c in cases):
        directory = Path(property_model or carrier.REPO/'.cache/models/BAAI-bge-m3')
        b = {'image': PROPERTY_RUNTIME_IMAGE, 'property_model_directory': str(directory)}
    providers = default_providers() if providers is None else providers
    from .dsh_search import search_configuration
    configuration = carrier.batch_configuration(cases_root=root/'cases', case_ids=ids,
        budgets={c['case_id']: fixed_budget_profile(c['level']) for c in cases},
        stage=SCALABLE_STAGE, providers=providers, case_groups=case_groups,
        scene_grounding=True, b=b, b_validation_corrections=2,
        d_web_search=search_configuration({}, model=providers['deepseek']['model']), d_web_access='proxy')
    checks = {}
    if input_format == 'pairs':
        for case in cases:
            checked = case.get('upstream_admission', {}).get('native_validation')
            checks[case['case_id']] = checked or check_ifc(root/'cases'/case['case_id']/'public/model.ifc')
    value = {'schema_version': PARALLEL_PLAN_SCHEMA, 'mode': mode,
        'budget_policy': TASK_BUDGET_ONLY, 'fixed_budget_version': FIXED_BUDGET_POLICY_VERSION,
        'selection': scope, 'input_format': input_format, 'scheduler': {'max_running': concurrency},
        'input_format_checks': checks, 'retain_debug': retain_debug,
        'dataset': str(dataset), 'selection_seed': seed, 'coverage': selected['coverage'],
        'missing_coverage': selected['missing_coverage'], 'configuration': configuration,
        'rounds': {r: [c['case_id'] for c in selected[r]] for r in ('round1', 'round2')},
        'input_bindings': public['bindings'], 'metrics_status': 'pending'}
    if request_convention is not None:
        value['request_convention'] = request_convention
    _set_scheduler(value, concurrency, qwen_first)
    value['sha256'] = _digest(value)
    write_json(root/'batch.json', value)
    results = root/'results'
    results.mkdir()
    (results/'README.md').write_text('# Repair 批次结果\n\n题目、组别和每项预算已冻结；等待离线准入后开始。\n', encoding='utf8')
    _need(not checks or all(v.get('passed') is True for v in checks.values()),
          'INPUT_IFC_FORMAT_FAILED:' + ','.join(c for c, v in checks.items() if not v.get('passed'))[:200])
    return {'event': 'summary', 'state': 'prepared', 'tasks': len(configuration['order']),
            'concurrency': concurrency, 'selection': scope, 'budget_policy': TASK_BUDGET_ONLY,
            'first': configuration['order'][0], 'root': str(root)}


def _database(root):
    path = safe_path(Path(root)/'control.sqlite')
    _need(path.is_file(), 'BATCH_NOT_INITIALIZED')
    return sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=10)


def _replace_bytes(path, data):
    temporary = path.with_name(path.name+'.refresh-tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def _budget_runtime_digest(runtime):
    unchanged = deepcopy(runtime)
    unchanged.pop('budgets', None)
    unchanged.pop('admission', None)
    unchanged['configuration'].pop('budgets', None)
    return _digest(unchanged)


def _budget_evidence_seal(db, changed_cases):
    """Hash existing evidence without exporting raw calls or reading outputs."""
    digest = hashlib.sha256()
    for table in ('runs', 'calls', 'events', 'batch_exports'):
        if not db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (table,)).fetchone():
            continue
        for row in db.execute('SELECT * FROM '+table+' ORDER BY 1,2'):
            if table == 'runs' and json.loads(row[1])['case_id'] in changed_cases:
                state = json.loads(row[1])
                state.pop('budget')
                row = (row[0], encode(state))
            digest.update(encode([table, *tuple(row)]).encode('utf8'))
    return digest.hexdigest()


def _budget_target(original, revision):
    target = deepcopy(original)
    configuration = target['configuration']
    versions = target.setdefault('case_budget_versions', {
        case: original['fixed_budget_version'] for case in configuration['case_ids']})
    for case, change in revision['changes'].items():
        old = configuration['budgets'][case]
        _need(old == change['before'] and change['after']['tokens'] < old['tokens'], 'BUDGET_REVISION_INVALID')
        level = next((level for level in ('S1', 'S2', 'S3')
                      if old == fixed_budget_profile(level, policy_version=versions[case])), None)
        _need(level is not None and change['after'] == fixed_budget_profile(level), 'BUDGET_REVISION_POLICY_REQUIRED')
        configuration['budgets'][case] = deepcopy(change['after'])
        versions[case] = FIXED_BUDGET_POLICY_VERSION
    target['fixed_budget_version'] = FIXED_BUDGET_POLICY_VERSION
    target['budget_revision'] = {'path': revision['receipt_path'], 'policy_version': FIXED_BUDGET_POLICY_VERSION}
    target.pop('sha256', None)
    target['sha256'] = _digest(target)
    return target


def apply_unstarted_budgets(root):
    """Apply an authorized versioned reduction to whole unstarted case cohorts.

    A journal covers DB/file commit interruption. The batch stays paused until
    a new source/configuration-bound admission is earned; no tasks are restarted.
    """
    root = safe_path(Path(root))
    with task_owner(root, 'batch-owner'):
        ledger = ControllerLedger(root/'control.sqlite')
        pending = root/'admission/budget-update.pending.json'
        current = plan(root)
        runtime = read_json(root/'experiment.json')
        with ledger.transaction() as db:
            states = {row[0]: json.loads(row[1]) for row in db.execute('SELECT run_id,state FROM runs')}
            _need(not any(s['status'] in {'running', 'awaiting_user'} for s in states.values())
                  and not db.execute("SELECT 1 FROM calls WHERE state='inflight' LIMIT 1").fetchone(),
                  'BUDGET_REVISION_REQUIRES_QUIESCENT_BATCH')
            _need(set(states) == set(current['configuration']['order']), 'BUDGET_REVISION_RUNS_CHANGED')
            called = {row[0] for row in db.execute('SELECT DISTINCT run_id FROM calls')}
            if pending.exists():
                revision = read_json(pending)
                previous = Path(revision['previous_plan']['path'])
                _need(sha256(previous) == revision['previous_plan']['sha256'], 'BUDGET_REVISION_HISTORY_CHANGED')
                original = read_json(previous)
            elif current.get('budget_revision'):
                return {'event': 'summary', 'state': 'unchanged', 'policy': current['fixed_budget_version']}
            else:
                original = deepcopy(current)
                _need(runtime['configuration'] == current['configuration']
                      and runtime['budgets'] == current['configuration']['budgets'], 'BUDGET_REVISION_CONFIG_CHANGED')
                changes = {}
                for case in current['configuration']['case_ids']:
                    cohort = [states[run] for run in current['configuration']['order'] if states[run]['case_id'] == case]
                    if not all(s['status'] == 'ready' and s['started'] is None and s['checkpoint'] is None
                               and not s['activities'] and not s['native'] and not s['artifact']
                               and s['active_elapsed_s'] == 0 and s['run_id'] not in called for s in cohort):
                        continue
                    old = current['configuration']['budgets'][case]
                    version = current.get('case_budget_versions', {}).get(case, current['fixed_budget_version'])
                    level = next((l for l in ('S1', 'S2', 'S3')
                                  if old == fixed_budget_profile(l, policy_version=version)), None)
                    _need(level is not None, 'BUDGET_REVISION_POLICY_REQUIRED')
                    new = fixed_budget_profile(level)
                    if new != old:
                        changes[case] = {'before': old, 'after': new}
                if not changes:
                    return {'event': 'summary', 'state': 'unchanged', 'updated_cases': 0}
                folder = root/'admission'
                folder.mkdir(exist_ok=True)
                previous = folder/('prepared-'+current['sha256']+'.json')
                if not previous.exists():
                    _replace_bytes(previous, (root/'batch.json').read_bytes())
                _need(read_json(previous) == original, 'BUDGET_REVISION_HISTORY_CHANGED')
                revision = {'schema_version': 'repair-budget-revision/1.0',
                    'policy_version': FIXED_BUDGET_POLICY_VERSION, 'changes': changes,
                    'previous_plan': {'path': str(previous), 'sha256': sha256(previous)},
                    'receipt_path': str(folder/'budget-policy-0_2.json'),
                    'runtime_invariants': _budget_runtime_digest(runtime),
                    'evidence_seal': _budget_evidence_seal(db, set(changes)), 'time': time.time()}
            target = _budget_target(original, revision)
            _need(current['sha256'] in {original['sha256'], target['sha256']}, 'BUDGET_REVISION_PLAN_CHANGED')
            _need(_budget_runtime_digest(runtime) == revision['runtime_invariants'], 'BUDGET_REVISION_RUNTIME_CHANGED')
            _need(_budget_evidence_seal(db, set(revision['changes'])) == revision['evidence_seal'],
                  'BUDGET_REVISION_EVIDENCE_CHANGED')
            _source_guard(root, current)
            # Persistence markers remain even if an interrupted file commit
            # needs recovery. Current admission rejects any half-applied plan.
            (root/'pause-between-tasks').touch()
            (root/'stop-service').touch()
            _replace_bytes(pending, (encode(revision)+'\n').encode('utf8'))
            for state in states.values():
                change = revision['changes'].get(state['case_id'])
                if change is None:
                    continue
                _need(state['status'] == 'ready' and state['started'] is None
                      and state['run_id'] not in called and not state['activities']
                      and state['budget'] in (change['before'], change['after']), 'BUDGET_REVISION_TASK_CHANGED')
                state['budget'] = deepcopy(change['after'])
                ledger._save(db, state)
            db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)', ('budget-revision', encode({
                'path': revision['receipt_path'],
                'sha256': hashlib.sha256((encode(revision)+'\n').encode('utf8')).hexdigest()})))
        runtime['configuration'] = target['configuration']
        runtime['budgets'] = deepcopy(target['configuration']['budgets'])
        _replace_bytes(root/'batch.json', (encode(target)+'\n').encode('utf8'))
        _replace_bytes(root/'experiment.json', (encode(runtime)+'\n').encode('utf8'))
        receipt_path = Path(revision['receipt_path'])
        document = (encode(revision)+'\n').encode('utf8')
        if receipt_path.exists():
            _need(receipt_path.read_bytes() == document, 'BUDGET_REVISION_RECEIPT_CHANGED')
        else:
            _replace_bytes(receipt_path, document)
        pending.unlink()
        return {'event': 'summary', 'state': 'budget_applied_requires_admission',
            'policy': FIXED_BUDGET_POLICY_VERSION, 'updated_cases': len(revision['changes']),
            'updated_tasks': sum(s['case_id'] in revision['changes'] for s in states.values()),
            'previous_plan': str(previous), 'receipt': revision['receipt_path']}


def _verify_budget_revision(root, previous, value, old, current):
    """Permit exactly the explicitly applied lower budgets and their policy code."""
    ref = value.get('budget_revision', {})
    path = safe_path(Path(ref.get('path', '')))
    _need(path == root/'admission/budget-policy-0_2.json', 'BUDGET_REVISION_RECEIPT_REQUIRED')
    revision = read_json(path)
    original_path = Path(revision['previous_plan']['path'])
    _need(sha256(original_path) == revision['previous_plan']['sha256'], 'BUDGET_REVISION_HISTORY_CHANGED')
    original = read_json(original_path)
    _need(previous['configuration'] == original['configuration']
          and value == _budget_target(original, revision), 'BUDGET_REVISION_CONFIGURATION_CHANGED')
    _need({k: v for k, v in old.items() if k not in {'files', 'budgets'}} ==
          {k: v for k, v in current.items() if k not in {'files', 'budgets'}}, 'BUDGET_REVISION_BINDINGS_CHANGED')
    _need(old['budgets'] == original['configuration']['budgets']
          and current['budgets'] == value['configuration']['budgets'], 'BUDGET_REVISION_BINDINGS_CHANGED')
    with closing(_database(root)) as db:
        recorded = db.execute("SELECT value FROM batch_control WHERE key='budget-revision'").fetchone()
        _need(recorded and json.loads(recorded[0]) == {'path': str(path), 'sha256': sha256(path)}
              and _budget_evidence_seal(db, set(revision['changes'])) == revision['evidence_seal'],
              'BUDGET_REVISION_EVIDENCE_CHANGED')
        for run, raw in db.execute('SELECT run_id,state FROM runs'):
            state = json.loads(raw)
            _need(state['budget'] == value['configuration']['budgets'][state['case_id']], 'BUDGET_REVISION_LEDGER_CHANGED')
    return {'path': str(path), 'sha256': sha256(path)}


def _convention_refresh(root, value, convention, *, recovering=False):
    """Validate the entire snapshot before changing any public request copy."""
    from .batch_cases import request_convention_parts
    metadata, appendix = request_convention_parts(convention)
    current = value.get('request_convention')
    _need(current in {None, convention}, 'REQUEST_CONVENTION_FROZEN')
    target = json.loads(json.dumps(value))
    guard = json.loads(json.dumps(value))
    replacements = []
    if current is None:
        for case, binding in target['input_bindings'].items():
            path = root/'cases'/case/'public/request.txt'
            raw = path.read_bytes()
            original_digest = binding['input_digests']['request.txt']
            if sha256(path) == original_digest:
                effective = raw+appendix
            else:
                # Recovery accepts exactly the authorized suffix, never an
                # arbitrary replacement matching a user-supplied new digest.
                _need(recovering and raw.endswith(appendix)
                      and hashlib.sha256(raw[:-len(appendix)]).hexdigest() == original_digest,
                      'PUBLIC_INPUT_CHANGED')
                effective = raw
            guard['input_bindings'][case]['input_digests']['request.txt'] = hashlib.sha256(raw).hexdigest()
            binding['source_input_digests'] = dict(binding['input_digests'])
            binding['input_digests']['request.txt'] = hashlib.sha256(effective).hexdigest()
            binding['request_convention'] = dict(metadata)
            if raw != effective:
                replacements.append((path, effective))
        target['request_convention'] = convention
    _source_guard(root, guard)
    return target, replacements


def refresh_unstarted(root, *, request_convention=None, concurrency=None, qwen_first=None):
    """Explicitly re-freeze an unstarted method, public convention or scheduler.

    Original inputs, task order, providers and budgets stay unchanged. A single
    journal resumes interrupted public-copy updates; current admission is required.
    """
    root = safe_path(Path(root))
    with task_owner(root, 'batch-owner'):
        _need(not any((root/name).exists() for name in ('experiment.json', 'control.sqlite')),
              'STARTED_BATCH_IMMUTABLE')
        value = plan(root)
        journal = root/'admission/request-refresh-pending.json'
        recovering = journal.is_file()
        pending = read_json(journal) if recovering else None
        if recovering:
            _need(concurrency is None and qwen_first is None, 'REQUEST_REFRESH_RECOVERY_REQUIRED')
            _need(request_convention in {None, pending['request_convention']}, 'REQUEST_CONVENTION_FROZEN')
            request_convention = pending['request_convention']
            _need(value['sha256'] in {pending['previous_sha256'], pending['target_sha256']}, 'REQUEST_REFRESH_PLAN_CHANGED')
            if value['sha256'] == pending['target_sha256']:
                _source_guard(root, value)
                journal.unlink()
                return {'event': 'summary', 'state': 'refrozen_requires_admission',
                        'previous_plan': str(root/'admission'/('prepared-'+pending['previous_sha256']+'.json'))}
        original_value = deepcopy(value)
        replacements = []
        if request_convention is not None:
            value, replacements = _convention_refresh(root, value, request_convention, recovering=recovering)
        if concurrency is not None or qwen_first is not None:
            _set_scheduler(value,
                concurrency if concurrency is not None else value.get('scheduler', {}).get('max_running', 1),
                qwen_first if qwen_first is not None else value['schema_version'] == QWEN_PRIORITY_PLAN_SCHEMA)
        version = carrier.SCENE_GROUNDING_VERSION
        if (value['configuration'].get('scene_grounding_version') == version
                and value.get('request_convention') == original_value.get('request_convention')
                and value.get('scheduler') == original_value.get('scheduler')
                and value['schema_version'] == original_value['schema_version']):
            return {'event': 'summary', 'state': 'unchanged', 'method': version}
        _need(value['configuration'].get('scene_grounding_version'), 'SCENE_METHOD_NOT_ENABLED')
        if request_convention is None:
            _source_guard(root, value)
        previous = root/'admission'/('prepared-'+original_value['sha256']+'.json')
        previous.parent.mkdir(exist_ok=True)
        original = (root/'batch.json').read_bytes()
        if previous.exists():
            _need(previous.read_bytes() == original, 'PREVIOUS_PLAN_CHANGED')
        else:
            with previous.open('xb') as stream:
                stream.write(original)
        value['configuration']['scene_grounding_version'] = version
        value.pop('sha256')
        value['sha256'] = _digest(value)
        if request_convention is not None:
            if recovering:
                _need(value['sha256'] == pending['target_sha256'], 'REQUEST_REFRESH_PLAN_CHANGED')
            else:
                write_json(journal, {'request_convention': request_convention,
                    'previous_sha256': original_value['sha256'], 'target_sha256': value['sha256']})
            for path, data in replacements:
                _replace_bytes(path, data)
            _source_guard(root, value)
        _replace_bytes(root/'batch.json', (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf8'))
        journal.unlink(missing_ok=True)
    return {'event': 'summary', 'state': 'refrozen_requires_admission', 'method': version,
            'previous_plan': str(previous)}


def _case_progress(rows):
    """Rows are in frozen insertion order; a partially completed case stays pending."""
    cases = {}
    for run_id, status, case, arm in rows:
        cases.setdefault(case, []).append(status)
    pending = next(((i, case) for i, (case, statuses) in enumerate(cases.items(), 1)
                    if any(status not in TERMINAL for status in statuses)), (None, None))
    return {'cases_total': len(cases),
            'cases_completed': sum(all(s in TERMINAL for s in statuses) for statuses in cases.values()),
            'next_case_index': pending[0], 'next_case_id': pending[1]}


def brief_status(root):
    """Read projected control fields only, never reports, IFC or response bodies."""
    root = Path(root)
    if not (root/'control.sqlite').is_file():
        value = plan(root)
        total = len(value['configuration']['order'])
        rows = [(run, 'ready', *run.rsplit('-', 1)) for run in value['configuration']['order']]
        return {'state': 'prepared', 'completed': 0, 'total': total, **_case_progress(rows),
                'active': None, 'active_count': 0, 'known_tokens': 0, 'reserved_tokens': 0, 'unknown_calls': 0,
                'status_counts': {'ready': total}}
    with closing(_database(root)) as db:
        rows = db.execute("SELECT run_id, json_extract(state,'$.status'), "
                          "json_extract(state,'$.case_id'), json_extract(state,'$.arm') FROM runs ORDER BY rowid").fetchall()
        active = next((r for r in rows if r[1] in {'running', 'awaiting_user'}), None)
        known = reserved = unknown = 0
        for usage, reservation, state, protocol, complete in db.execute(
                "SELECT usage,reservation,state,json_extract(metadata,'$.wire_protocol'), "
                "coalesce(json_extract(response,'$.usage_complete'),json_extract(response,'$.stream_complete')) FROM calls"):
            from .budget import normalize_usage
            normalized = normalize_usage(json.loads(usage) if usage else None,
                protocol=protocol or 'chat', complete=protocol != 'messages' or complete == 1) if state != 'inflight' else None
            if normalized is None:
                unknown += 1
                reserved += reservation
            else:
                known += normalized['total_tokens']
        status = {'state': 'running' if active else 'idle', 'completed': sum(r[1] in TERMINAL for r in rows),
                  **_case_progress(rows),
                  'total': len(rows), 'active': active[0] if active else None,
                  'active_count': sum(r[1] in {'running', 'awaiting_user'} for r in rows),
                  'known_tokens': known, 'reserved_tokens': reserved, 'unknown_calls': unknown}
        status['status_counts'] = {state: sum(r[1] == state for r in rows)
                                  for state in sorted({r[1] for r in rows})}
        if active:
            status.update(case_id=active[2], group=active[3], task_status=active[1])
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        timed = db.execute("SELECT json_extract(state,'$.arm'), count(*), "
            "avg(json_extract(state,'$.ended')-json_extract(state,'$.started')) FROM runs "
            "WHERE json_extract(state,'$.status') IN ("+','.join('?' for _ in TERMINAL)+") "
            "AND json_extract(state,'$.started') IS NOT NULL "
            "AND json_extract(state,'$.ended') >= json_extract(state,'$.started') "
            "GROUP BY json_extract(state,'$.arm')", tuple(TERMINAL)).fetchall()
        status['timing_by_group'] = {arm: {'timed': count, 'mean_wall_s': round(mean, 3)}
                                     for arm, count, mean in timed if arm in GROUPS}
        capacity = db.execute('SELECT capacity FROM concurrency_policy WHERE singleton=1').fetchone() \
            if 'concurrency_policy' in tables else None
        samples = sum(count for arm, count, mean in timed)
        status['eta_days_at_capacity'] = round(
            (status['total']-status['completed'])*sum(count*mean for arm, count, mean in timed)
            /samples/capacity[0]/86400, 4) if samples and capacity else None
        if 'batch_exports' in tables:
            status['format_passed'] = db.execute("SELECT count(*) FROM batch_exports "
                "WHERE json_extract(summary,'$.common_format_validation.passed')=1").fetchone()[0]
        if 'batch_control' in tables:
            row = db.execute("SELECT value FROM batch_control WHERE key='controller'").fetchone()
            if row:
                control = json.loads(row[0])
                status.update(state=control.get('state', status['state']), reason=control.get('reason'))
            held = _held_groups(db)
            if held:
                status.update(held_groups=held,
                              held_pending=sum(r[3] in held and r[1] not in TERMINAL for r in rows))
    return status


def _held_groups(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='batch_control'").fetchone():
        return []
    row = db.execute("SELECT value FROM batch_control WHERE key='held-groups'").fetchone()
    held = json.loads(row[0])['groups'] if row else []
    _need(isinstance(held, list) and len(set(held)) == len(held) and set(held) <= set(GROUPS),
          'INVALID_GROUP_HOLD_RECORD')
    return held


def set_group_hold(root, groups, *, hold, reason):
    """Defer arms without changing frozen tasks, budgets, outputs or method configuration."""
    root = safe_path(Path(root))
    _need((root/'control.sqlite').is_file(), 'BATCH_NOT_INITIALIZED')
    _need(isinstance(groups, list) and groups and len(set(groups)) == len(groups)
          and set(groups) <= set(GROUPS), 'INVALID_EXPERIMENT_ARMS')
    _need(isinstance(reason, str) and 0 < len(reason.strip()) <= 240, 'GROUP_HOLD_REASON_REQUIRED')
    with task_owner(root, 'batch-owner'):
        configured = {r.rsplit('-', 1)[-1] for r in plan(root)['configuration']['order']}
        _need(set(groups) <= configured, 'INVALID_EXPERIMENT_ARMS')
        ledger = ControllerLedger(root/'control.sqlite')
        with ledger.transaction() as db:
            previous = _held_groups(db)
            held = sorted(set(previous) | set(groups) if hold else set(previous) - set(groups))
            if held:
                placeholders = ','.join('?' for _ in held)
                busy = db.execute("SELECT 1 FROM runs r WHERE json_extract(r.state,'$.arm') IN ("
                    +placeholders+") AND (json_extract(r.state,'$.status') IN ('running','awaiting_user') "
                    "OR EXISTS(SELECT 1 FROM json_each(r.state,'$.activities')) "
                    "OR EXISTS(SELECT 1 FROM calls c WHERE c.run_id=r.run_id AND c.state='inflight')) LIMIT 1",
                    held).fetchone()
                _need(not busy, 'GROUP_HOLD_REQUIRES_QUIESCENT_TASKS')
            record = {'groups': held, 'previous': previous, 'reason': reason.strip(), 'time': time.time()}
            db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)', ('held-groups', encode(record)))
            db.execute('INSERT INTO batch_control VALUES(?,?)', ('group-hold-event:'+str(time.time_ns()), encode(record)))
    return {'event': 'summary', 'state': 'group_hold_updated', 'held_groups': held}


def _dispatch_order(value, config, states):
    """Priority affects dispatch only; CSV/checkpoint and task identities stay fixed."""
    order = config['order']
    if value.get('scheduler', {}).get('priority') != 'qwen-first':
        return order
    # Restore an existing session before starting any new task, regardless of arm.
    return sorted(order, key=lambda run: (
        0 if states[run]['status'] == 'running' else
        1 if run.rsplit('-', 1)[1] in {'F', 'G'} else 2))


def _states(root):
    with closing(_database(root)) as db:
        result = []
        for run_id, raw in db.execute('SELECT run_id,state FROM runs ORDER BY rowid'):
            state = json.loads(raw)
            detail = db.execute("SELECT json_extract(payload,'$.detail') FROM events "
                "WHERE run_id=? AND kind='terminal' ORDER BY seq DESC LIMIT 1", (run_id,)).fetchone()
            if detail:
                state['detail'] = detail[0]
            result.append(state)
        return result


def _task_control(root, run_id):
    with closing(_database(root)) as db:
        row = db.execute("SELECT json_extract(state,'$.status'),json_extract(state,'$.question') "
                         "FROM runs WHERE run_id=?", (run_id,)).fetchone()
    _need(row is not None, 'RUN_NOT_FOUND')
    return {'status': row[0], 'question': json.loads(row[1]) if row[1] else None}


def _control(root, state, **fields):
    ledger = ControllerLedger(Path(root)/'control.sqlite')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                   ('controller', encode({'state': state, 'pid': os.getpid(), **fields})))


def _emit(event, **fields):
    """Expose control summaries only; never per-task results or runtime bodies."""
    if event not in {'complete', 'paused', 'attention'}:
        return
    allowed = {'completed', 'total', 'active', 'known_tokens', 'reserved_tokens',
               'unknown_calls', 'reason', 'run_id', 'question_id', 'warm_owner',
               'exit_code', 'results', 'status_counts', 'worker_reason', 'failure_site',
               'drain_cleanup_reason', 'service_stop_reason'}
    allowed.update({'active_count', 'pending_count', 'service_retained', 'cases_total',
                    'cases_completed', 'next_case_index', 'next_case_id', 'format_passed',
                    'timing_by_group', 'eta_days_at_capacity', 'held_groups', 'held_pending'})
    summary = {'event': 'summary', 'state': event}
    for key in sorted(allowed & fields.keys()):
        value = fields[key]
        if key == 'status_counts':
            value = {status: count for status, count in value.items()
                     if status in TERMINAL | {'ready', 'running', 'awaiting_user'}
                     and isinstance(count, int)}
        elif key == 'held_groups':
            value = [arm for arm in value if arm in GROUPS]
        elif key == 'timing_by_group':
            value = {arm: {'timed': row['timed'], 'mean_wall_s': row['mean_wall_s']}
                     for arm, row in value.items() if arm in GROUPS
                     and type(row.get('timed')) is int and row['timed'] >= 0
                     and type(row.get('mean_wall_s')) in {int, float} and row['mean_wall_s'] >= 0}
        elif isinstance(value, str):
            value = value.replace('\n', ' ').replace('\r', ' ')[:512 if key == 'results' else 240]
        elif value is not None and not isinstance(value, (bool, int, float)):
            continue
        summary[key] = value
    print(json.dumps(summary, ensure_ascii=False, separators=(',', ':')), flush=True)


def pause(root):
    root = safe_path(Path(root))
    _need((root/'batch.json').is_file() or (root/'control.sqlite').is_file(), 'BATCH_NOT_FOUND')
    (root/'pause-between-tasks').write_text('Cooperative pause after the active task.\n', encoding='utf8')


def clear_pause(root):
    safe_path(Path(root)/'pause-between-tasks').unlink(missing_ok=True)


def may_start(state):
    limits = state.get('limits') or Ledger.limits(state)
    usage = state.get('usage', {})
    return (state['status'] in {'ready', 'running'} and not state.get('activities')
            and usage.get('known_total_tokens', 0) + usage.get('reserved_tokens', 0) < limits['tokens']
            and usage.get('calls', 0) < limits['calls']
            and state.get('active_elapsed_s', 0) < limits['active_seconds'])


def common_failure(states):
    signatures = defaultdict(set)
    for state in states:
        if state['arm'] not in 'BEF' or state['status'] != 'runtime_error':
            continue
        native = state.get('native', {}).get('result', {})
        # Model repair failures are ordinary outcomes. Only a repeated system
        # invariant or transport/runtime defect is an automatic pause reason.
        code = native.get('error_code') or state.get('detail') or ''
        if not isinstance(code, str) or not any(word in code.upper() for word in
                ('NATIVE_', 'WORKER_', 'DOCKER_', 'PROVIDER_', 'GATEWAY_', 'ISOLATION_', 'BUNDLE_', 'RECOVERY_')):
            continue
        signatures[code[:256]].add(state['case_id'])
    return next(({'reason': 'COMMON_HARNESS_SYSTEM_FAILURE', 'signature': code, 'cases': sorted(cases)}
                 for code, cases in signatures.items() if len(cases) >= 2), None)


def check_ifc(path):
    """Bounded independent schema/EXPRESS check; source is opened read-only."""
    path = safe_path(Path(path))
    before = sha256(path)
    try:
        completed = subprocess.run([sys.executable, '-c', CHECK_SCRIPT, str(path)],
            cwd=carrier.REPO, capture_output=True, text=True, encoding='utf8', errors='replace', timeout=120)
        result = json.loads(completed.stdout.strip().splitlines()[-1]) if completed.returncode == 0 else {
            'status': 'error', 'passed': False, 'error': 'VALIDATOR_PROCESS_EXITED', 'exit_code': completed.returncode}
    except (subprocess.TimeoutExpired, ValueError, IndexError) as error:
        result = {'status': 'error', 'passed': False, 'error': type(error).__name__}
    _need(sha256(path) == before, 'VALIDATOR_MUTATED_ARTIFACT')
    return result


def _gate_report(path):
    path = safe_path(Path(path))
    value = read_json(path)
    _need(value.get('exit_code') == 0 and value.get('source_before') == value.get('source_after'),
          'SCOPED_GATE_FAILED_OR_CHANGED')
    for key in ('log', 'junit'):
        reference = value[key]
        _need(sha256(Path(reference['path'])) == reference['sha256'], 'GATE_EVIDENCE_CHANGED')
    suites = ET.parse(value['junit']['path']).getroot()
    _need(all(int(suite.get(field, '0')) == 0 for suite in suites.iter('testsuite')
              for field in ('failures','errors','skipped')), 'SCOPED_GATE_INCOMPLETE')
    nodes = list(suites.iter('testcase'))
    _need(sum(int(s.get('tests', '0')) for s in suites.iter('testsuite')) == len(nodes),
          'SCOPED_GATE_INCOMPLETE')
    _need(nodes and not any(n.find(tag) is not None for n in nodes for tag in ('failure', 'error', 'skipped')),
          'SCOPED_GATE_INCOMPLETE')
    _need(value['source_after'] == carrier.bindings(value['configuration']), 'SCOPED_GATE_STALE')
    _need(all(sha256(carrier.REPO/p) == h for p, h in value['tests'].items()), 'GATE_TEST_CHANGED')
    return value


def _runtime_bindings(value):
    value = deepcopy(value)
    controller_files = {'batch_workflow.py','batch_operator.py','batch_cases.py',
                        'results.py','formal_admission.py','formal_workflow.py',
                        'property_confirmation.py'}
    value['files'] = {k: v for k, v in value['files'].items()
                      if not (k.startswith('scripts/ifc_repair/repair_comparison/')
                              and k.split('/')[-1] in controller_files) and not k.startswith('public/')}
    value.pop('budgets', None)
    value.pop('budget', None)
    return value


def _verify_native(receipt_path, configuration, *, groups):
    path = safe_path(Path(receipt_path))
    check = read_json(path)
    _need(check.get('all_passed') is True and check.get('real_models_called') is False
          and check.get('real_credentials_used') is False, 'KEYLESS_NATIVE_GATE_REQUIRED')
    _need({r['arm'] for r in check.get('runs', [])} >= set(groups), 'NATIVE_GROUPS_REQUIRED')
    _need(all(r.get('status') == 'submitted' and r.get('source_unchanged') is True
              and r.get('mode') == 'real_runtime_fake_model' and r.get('reopen', {}).get('express_errors') == 0
              for r in check['runs']), 'NATIVE_PUBLICATION_GATE_FAILED')
    for key in ('test_file','service_log'):
        _need(sha256(Path(check[key]['path'])) == check[key]['sha256'], 'NATIVE_GATE_EVIDENCE_CHANGED')
    before, after = check.get('runtime_bindings_before'), check.get('runtime_bindings_after')
    _need(before and before == after, 'NATIVE_RUNTIME_BINDING_REQUIRED')
    current = _runtime_bindings(carrier.bindings(configuration))
    checked = _runtime_bindings(after)
    expected = _runtime_bindings(carrier.bindings(check.get('configuration') or configuration))
    _need(checked.get('files') and checked['files'] == expected['files'], 'NATIVE_RUNTIME_SOURCE_BINDINGS_REQUIRED')
    required_images = {carrier.IMAGE, carrier.DSH_IMAGE}
    if check.get('configuration', {}).get('b'):
        required_images.add(PROPERTY_RUNTIME_IMAGE)
    _need(set(checked.get('images', {})) >= required_images
          and check.get('images') == after.get('images'), 'NATIVE_IMAGE_BINDINGS_REQUIRED')
    # The default-image matrix has no property dependencies. Its tested files
    # must all be current; the separate property gate covers the added closure.
    _need(all(current['files'].get(k) == h for k, h in checked['files'].items()), 'NATIVE_RUNTIME_CHANGED')
    _need(all(current['images'].get(k) == h for k, h in checked['images'].items()), 'NATIVE_IMAGE_CHANGED')
    _need(checked['models'] == current['models'], 'NATIVE_MODELS_CHANGED')
    for row in check['runs']:
        for key in ('public_source','artifact'):
            _need(sha256(Path(row[key]['path'])) == row[key]['sha256'], 'NATIVE_GATE_OUTPUT_CHANGED')
    return check


def _check_admission(root, configuration):
    root = Path(root)
    runtime = read_json(root/'experiment.json') if (root/'experiment.json').is_file() else {}
    admission_path = safe_path(Path(runtime.get('admission') or root/'admission/live.json'))
    _need(admission_path.resolve().parent == (root/'admission').resolve(), 'ADMISSION_PATH_OUTSIDE_BATCH')
    value = carrier.verify_admission(admission_path, configuration)
    reference = value.get('scoped_receipt_reference')
    path = safe_path(Path(reference['path'])) if reference else Path(root)/'admission/scoped.json'
    if reference:
        _need(sha256(path) == reference['sha256'], 'LIVE_SCOPED_RECEIPT_CHANGED')
    receipt = _gate_report(path)
    _need(value.get('scoped_receipt') == receipt, 'LIVE_SCOPED_RECEIPT_CHANGED')
    refs = value.get('native_receipts')
    _need(isinstance(refs, list) and len(refs) == (2 if configuration.get('b') else 1),
          'LIVE_NATIVE_RECEIPTS_REQUIRED')
    for i, reference in enumerate(refs):
        path = safe_path(Path(reference['path']))
        _need(sha256(path) == reference['sha256'], 'LIVE_NATIVE_RECEIPT_CHANGED')
        _verify_native(path, configuration, groups=_native_groups(configuration, property_only=i > 0))
    return value


def _native_groups(configuration, *, property_only=False):
    groups = {run.rsplit('-', 1)[-1] for run in configuration['order']}
    _need(groups and groups <= set(GROUPS), 'INVALID_EXPERIMENT_ARMS')
    return sorted(groups & set('BEF') if property_only else groups)


def gate(root, tests, *, revision=None):
    """Earn a source-bound focused pytest receipt, with actual stdout and JUnit."""
    value = plan(root)
    _need(revision is None or isinstance(revision, str) and
          re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', revision), 'INVALID_GATE_REVISION')
    stem = 'scoped' if revision is None else 'scoped-'+revision
    folder = Path(root)/'admission'
    folder.mkdir(exist_ok=True)
    receipt_path = folder/(stem+'.json')
    _need(not receipt_path.exists(), 'SCOPED_GATE_ALREADY_RECORDED')
    _need(tests and all(t.startswith('tests/') and t.split('::')[0].endswith('.py') for t in tests), 'TEST_FILE_LIST_REQUIRED')
    log, junit = folder/(stem+'.log'), folder/(stem+'.xml')
    before = carrier.bindings(value['configuration'])
    helper_files = ['tests/ifc_repair/repair_comparison/demo_http_fixture.py',
                    'tests/ifc_repair/repair_comparison/public_repair_fixture.py',
                    'tests/ifc_repair/test_scene_repair_api.py',
                    # Host-only public parsers are outside the runtime package,
                    # but changes still invalidate the policy's scoped gate.
                    'scripts/ifc_repair/dataset_batch/prompt_check.py',
                    'scripts/ifc_repair/dataset_batch/prompt_check_v3.py',
                    'scripts/ifc_repair/dataset_request_v4.py',
                    'scripts/ifc_repair/audit_initial_dataset.py']
    test_bindings = {p: sha256(carrier.REPO/p) for p in {*[t.split('::')[0] for t in tests], *helper_files}}
    command = [sys.executable, '-m', 'pytest', '-q', *tests,
               '--basetemp='+str(folder/('pytest-'+stem)), '--junitxml='+str(junit)]
    with log.open('wb') as output:
        finished = subprocess.run(command, cwd=carrier.REPO, stdout=output, stderr=subprocess.STDOUT)
    def reference(path):
        return {'path': str(path.resolve()), 'sha256': sha256(path)}
    receipt = {'configuration': value['configuration'], 'command': command, 'exit_code': finished.returncode,
               'source_before': before, 'source_after': carrier.bindings(value['configuration']),
               'tests': test_bindings, 'log': reference(log), 'junit': reference(junit)}
    write_json(receipt_path, receipt)
    _gate_report(receipt_path)
    return {'event': 'scoped_gate_passed', 'receipt': str(receipt_path)}


def admit(root, native_receipt, *, property_receipt=None, scoped_receipt=None, revision=None):
    """Bind genuinely completed native fake tests and focused tests to this batch."""
    value = plan(root)
    root = safe_path(Path(root))
    _need(revision is None or isinstance(revision, str) and
          re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', revision), 'INVALID_ADMISSION_REVISION')
    destination = root/'admission'/('live.json' if revision is None else 'live-'+revision+'.json')
    _need(not destination.exists(), 'LIVE_ADMISSION_ALREADY_RECORDED')
    scoped_path = safe_path(Path(scoped_receipt or Path(root)/'admission/scoped.json'))
    receipt = _gate_report(scoped_path)
    _need(receipt['configuration'] == value['configuration'], 'GATE_CONFIGURATION_MISMATCH')
    native_receipt = safe_path(Path(native_receipt))
    groups = _native_groups(value['configuration'])
    native = _verify_native(native_receipt, value['configuration'], groups=groups)
    _need(native.get('timeout_stop', native.get('native_timeout_stop', {})).get('quiescent') is True, 'NATIVE_STOP_GATE_REQUIRED')
    current = carrier.bindings(value['configuration'])
    evidence = [{'path': str(native_receipt), 'sha256': sha256(native_receipt)}]
    if value['configuration'].get('b'):
        _need(property_receipt is not None, 'PROPERTY_NATIVE_GATE_REQUIRED')
        path = safe_path(Path(property_receipt))
        property_groups = _native_groups(value['configuration'], property_only=True)
        check = _verify_native(path, value['configuration'], groups=property_groups)
        _need(check['configuration']['b'] == value['configuration']['b'], 'PROPERTY_NATIVE_BINDING_CHANGED')
        _need({r['arm'] for r in check['runs']} >= set(property_groups)
              and all(r['status'] == 'submitted' for r in check['runs']), 'PROPERTY_NATIVE_GROUPS_REQUIRED')
        evidence.append({'path': str(path), 'sha256': sha256(path)})
    admission = {'stage': SCALABLE_STAGE, 'passed': True, 'configuration': value['configuration'],
                 'bindings': current, 'authorized_arms': groups, 'scoped_receipt': receipt,
                 'scoped_receipt_reference': {'path': str(scoped_path), 'sha256': sha256(scoped_path)},
                 'native_receipts': evidence, 'scope': 'Offline routing/transport/isolated-runtime gate; no model capability claim.'}
    if revision is None:
        write_json(destination, admission)
    else:
        # Keep original frozen records in place. Only the mutable runtime
        # reference advances to an append-only controller admission receipt.
        with task_owner(root, 'batch-owner'):
            _need((root/'experiment.json').is_file(), 'ADMISSION_REVISION_REQUIRES_INITIALIZED_BATCH')
            runtime = read_json(root/'experiment.json')
            _need(runtime.get('configuration') == value['configuration'], 'RESUME_CONFIGURATION_CHANGED')
            previous_path = safe_path(Path(runtime['admission']))
            previous = read_json(previous_path)
            old = previous['bindings']
            changed = {key for key in set(old['files']) | set(current['files'])
                       if old['files'].get(key) != current['files'].get(key)}
            allowed = {'scripts/ifc_repair/repair_comparison/batch_workflow.py',
                       'scripts/ifc_repair/repair_comparison/batch_operator.py'}
            if previous['configuration'] != value['configuration'] and value.get('qwen_context_revision'):
                from scripts.ifc_repair.qwen_batch import verify_context_revision
                admission['qwen_context_revision'] = verify_context_revision(root, previous, value, old, current)
                allowed.update({'scripts/ifc_repair/qwen_batch.py', 'qwen-policy.json',
                                'scripts/ifc_repair/repair_comparison/group_config.py'})
                _need(changed <= allowed, 'QWEN_CONTEXT_REVISION_SOURCE_SCOPE_CHANGED')
            elif previous['configuration'] != value['configuration']:
                admission['budget_revision'] = _verify_budget_revision(root, previous, value, old, current)
                allowed.add('scripts/ifc_repair/repair_comparison/budget.py')
                _need(changed <= allowed, 'BUDGET_REVISION_SOURCE_SCOPE_CHANGED')
            else:
                _need(changed <= allowed and {k: v for k, v in old.items() if k != 'files'} ==
                      {k: v for k, v in current.items() if k != 'files'}, 'CONTROLLER_ONLY_ADMISSION_REQUIRED')
            with closing(_database(root)) as db:
                busy = db.execute("SELECT 1 FROM runs WHERE json_extract(state,'$.status') "
                                  "IN ('running','awaiting_user') LIMIT 1").fetchone()
                inflight = db.execute("SELECT 1 FROM calls WHERE state='inflight' LIMIT 1").fetchone()
                _need(not busy and not inflight, 'ADMISSION_REVISION_REQUIRES_QUIESCENT_BATCH')
            admission['previous_admission'] = {'path': str(previous_path), 'sha256': sha256(previous_path)}
            write_json(destination, admission)
            runtime['admission'] = str(destination)
            pending = root/'experiment-admission.pending'
            write_json(pending, runtime)
            pending.replace(root/'experiment.json')
        return {'event': 'admitted', 'tasks': len(value['configuration']['order']), 'admission': str(destination)}
    return {'event': 'admitted', 'tasks': len(value['configuration']['order'])}


def _initialize(root, value):
    configuration = value['configuration']
    if (Path(root)/'experiment.json').exists():
        existing = read_json(Path(root)/'experiment.json')
        _need(existing.get('configuration') == configuration and existing.get('mode') == value['mode'],
              'RESUME_CONFIGURATION_CHANGED')
        return existing
    return carrier.initialize(root, mode=value['mode'], admission=Path(root)/'admission/live.json'
        if value['mode'] == 'live' else None, scene_grounding=True,
        cases_root=configuration['cases_root'], case_ids=configuration['case_ids'], budgets=configuration['budgets'],
        stage=SCALABLE_STAGE, providers=configuration['providers'], case_groups=configuration['case_groups'],
        b=configuration.get('b'), b_validation_corrections=configuration['b_validation_corrections'],
        d_web_search=configuration.get('d_web_search'), d_web_access=configuration.get('d_web_access'))


def _source_guard(root, value, case_id=None):
    checked_metadata = set()
    for case, binding in value['input_bindings'].items():
        if case_id is not None and case != case_id:
            continue
        for name, digest in binding['input_digests'].items():
            _need(sha256(Path(root)/'cases'/case/'public'/name) == digest, 'PUBLIC_INPUT_CHANGED')
        for path, digest in binding['metadata_bindings'].items():
            if (path, digest) in checked_metadata:
                continue
            _need(sha256(safe_path(Path(path))) == digest, 'DATASET_ADMISSION_CHANGED')
            checked_metadata.add((path, digest))


def _publish(root, value):
    states = _states(root)
    states_by_run = {s['run_id']: s for s in states}
    ledger = ControllerLedger(Path(root)/'control.sqlite')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS batch_exports(run_id TEXT PRIMARY KEY,summary TEXT NOT NULL)')
        exported = {r[0]: json.loads(r[1]) for r in db.execute('SELECT run_id,summary FROM batch_exports')}
    for state in states:
        if state['status'] not in TERMINAL or state['run_id'] in exported:
            continue
        result = export_task(Path(root), Path(root)/'results', state['run_id'], format_check=check_ifc)
        result['reason'] = str(state.get('detail') or state['status'])[:240]
        with ledger.transaction() as db:
            db.execute('INSERT INTO batch_exports VALUES(?,?)', (state['run_id'], encode(result)))
        exported[state['run_id']] = result
        _emit('task_complete', run_id=state['run_id'], status=state['status'],
              reason=result['reason'], format=result['common_format_validation']['status'],
              completed=len(exported), total=len(states))
    lines = ['# Repair 批次结果', '', '提交、IFC 格式检查和修复评价分别记录；修复指标待定。', '',
             '| 范围 | 案例 | 组 | 终态 | IFC格式 | 原因 | 已知token | 报告 |',
             '|---|---|---|---|---|---|---:|---|']
    with closing(_database(root)) as db:
        held = _held_groups(db)
    if held:
        lines[2] += ' 当前暂停派发：'+ '/'.join(held)+'；其待运行任务和历史失败保留。'
    for run_id in value['configuration']['order']:
        case, arm = run_id.rsplit('-', 1)
        row = exported.get(run_id)
        round_id = ('全量' if value.get('selection') == 'full' else
                    '第1轮' if case in value['rounds']['round1'] else '第2轮')
        if row is None:
            state = states_by_run[run_id]
            lines.append(f'| {round_id} | {case} | {arm} | {state["status"]} | 待定 | | | |')
        else:
            reason = row['reason'].replace('|', '/').replace('\n', ' ')
            lines.append(f'| {round_id} | {case} | {arm} | {row["status"]} | '
                f'{row["common_format_validation"]["status"]} | {reason} | '
                f'{row["usage"]["known_total_tokens"]} | [report]({row["report"]}) |')
    folder = Path(root)/'results'
    folder.mkdir(exist_ok=True)
    (folder/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
    return exported


class _Process:
    """Both CLI streams are bounded in memory, never exported as task logs."""
    def __init__(self, command):
        self.tail = b''
        environment = dict(os.environ, PYTHONUTF8='1')
        self.process = subprocess.Popen(command, cwd=carrier.REPO, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, env=environment)
        def drain():
            while block := self.process.stdout.read(4096):
                self.tail = (self.tail + block)[-16384:]
        self.reader = threading.Thread(target=drain, daemon=True)
        self.reader.start()

    def poll(self):
        return self.process.poll()

    def wait(self, timeout=None):
        code = self.process.wait(timeout=timeout)
        self.reader.join(timeout=5)
        self.process.stdout.close()
        return code


def _worker_reason(tail):
    """Expose only a CLI attention reason, never the captured runtime body."""
    for line in reversed(tail.decode('utf8', errors='replace').splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if (isinstance(value, dict) and (value.get('event') == 'attention'
                or value.get('event') == 'summary' and value.get('state') == 'attention')
                and isinstance(value.get('reason'), str)):
            return value['reason'].replace('\n', ' ').replace('\r', ' ')[:240]
    return None


def _controller_failure(error):
    fields = {'reason': type(error).__name__+': '+str(error)[:240]}
    trace = error.__traceback__
    if trace is not None:
        while trace.tb_next is not None:
            trace = trace.tb_next
        code = trace.tb_frame.f_code
        fields['failure_site'] = f'{Path(code.co_filename).name}:{trace.tb_lineno}:{code.co_name}'
    return fields


def _attention(root, reason, **fields):
    _control(root, 'attention', reason=reason, **fields)
    _emit('attention', reason=reason, **{k: v for k, v in fields.items() if k != 'stderr'})
    return 2


def _interface_fault(root, run_id):
    with closing(_database(root)) as db:
        row = db.execute("SELECT json_extract(response,'$.http_status'),json_extract(response,'$.error_type') FROM calls "
                         "WHERE run_id=? AND failed=1 ORDER BY rowid DESC LIMIT 1", (run_id,)).fetchone()
    return bool(row and (row[1] or row[0] is not None and (int(row[0]) >= 400 or int(row[0]) == 0)))


def _environment_fault(state):
    native = state.get('native', {}).get('result', {})
    if isinstance(native.get('result'), dict):
        native = native['result']
    detail = ' '.join(str(value) for value in
        (state.get('detail'), native.get('error_code'), native.get('reason_code'), native.get('error')) if value)
    return state['status'] == 'runtime_error' and any(code in detail.upper() for code in
        ('DOCKER_', 'ISOLATION_', 'SOURCE_', 'NATIVE_PROCESS_STOP_', 'NATIVE_RESULT_MISSING',
         'CONTAINER_STOP_', 'BUNDLE_', 'RECOVERY_', 'ARTIFACT_HASH_', 'GATEWAY_SERVICE_'))


def _queued_answer(root, *, run_ids=None):
    ledger = ControllerLedger(Path(root)/'control.sqlite')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        rows = db.execute("SELECT key,value FROM batch_control WHERE key='answer' OR key LIKE 'answer:%' ORDER BY key").fetchall()
    for key, raw in rows:
        value = json.loads(raw)
        if run_ids is not None and value['run_id'] not in run_ids:
            continue
        state = ledger.snapshot(value['run_id'])
        _need(state['status'] == 'awaiting_user' and state['question']['question_id'] == value['answer']['question_id'],
              'QUEUED_ANSWER_QUESTION_CHANGED')
        carrier.answer(root, value['run_id'], value['answer'])
        with ledger.transaction() as db:
            db.execute('DELETE FROM batch_control WHERE key=?', (key,))


def _rebind_budget_policy(root, db, value, key, policy):
    """Carry a prior user policy across the registered budget-only revision."""
    root = safe_path(Path(root))
    path = root/'admission/budget-policy-0_2.json'
    _need(value.get('budget_revision', {}).get('path') == str(path), 'POLICY_BUDGET_REVISION_REQUIRED')
    revision = read_json(path)
    previous_path = Path(revision['previous_plan']['path'])
    _need(sha256(previous_path) == revision['previous_plan']['sha256'], 'POLICY_BUDGET_REVISION_HISTORY_CHANGED')
    original = read_json(previous_path)
    registered = db.execute("SELECT value FROM batch_control WHERE key='budget-revision'").fetchone()
    _need(registered and json.loads(registered[0]) == {'path': str(path), 'sha256': sha256(path)}
          and value == _budget_target(original, revision)
          and policy['batch_sha256'] == original['sha256'], 'POLICY_BUDGET_REVISION_SCOPE_CHANGED')
    _need(not db.execute("SELECT 1 FROM runs WHERE json_extract(state,'$.status') IN ('running','awaiting_user') LIMIT 1").fetchone()
          and not db.execute("SELECT 1 FROM calls WHERE state='inflight' LIMIT 1").fetchone(),
          'POLICY_BUDGET_REVISION_REQUIRES_QUIESCENT_BATCH')
    db.execute('INSERT OR IGNORE INTO batch_control VALUES(?,?)',
               (key+'@'+original['sha256'], encode(policy)))
    rebound = {**policy, 'batch_sha256': value['sha256']}
    db.execute('UPDATE batch_control SET value=? WHERE key=?', (encode(rebound), key))
    return rebound


def _property_authorization(root, value, *, grant=False):
    """Persist explicit user delegation separately from model/configuration state."""
    ledger = ControllerLedger(Path(root)/'control.sqlite')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        row = db.execute("SELECT value FROM batch_control WHERE key='property_authorization'").fetchone()
        policy = json.loads(row[0]) if row else None
        if policy is not None:
            _need(policy.get('version') == 'public-existing-property-confirmation/0.1'
                  and policy.get('source') == 'user_delegated_policy', 'PROPERTY_AUTHORIZATION_INVALID')
            if policy.get('batch_sha256') != value['sha256']:
                _need(value.get('budget_revision'), 'PROPERTY_AUTHORIZATION_BATCH_CHANGED')
                policy = _rebind_budget_policy(root, db, value, 'property_authorization', policy)
        elif grant:
            policy = {'version': 'public-existing-property-confirmation/0.1',
                      'source': 'user_delegated_policy', 'batch_sha256': value['sha256'],
                      'scope': 'Explicit existing occurrence properties only; verify public target set, path, value and type. Missing or ambiguous facts still require clarification.'}
            db.execute('INSERT INTO batch_control VALUES(?,?)', ('property_authorization', encode(policy)))
    return policy


def _verified_property_answer(state, public_ifc, public_request):
    from .property_confirmation import verified_answer
    return verified_answer(state, public_ifc, public_request)


def _clarification_policy(root, value, requested=None):
    """Freeze an explicit batch policy; omitted flags reuse it or default to wait."""
    _need(requested in {None, 'wait', 'fail'}, 'INVALID_CLARIFICATION_POLICY')
    ledger = ControllerLedger(Path(root)/'control.sqlite')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        row = db.execute("SELECT value FROM batch_control WHERE key='clarification_policy'").fetchone()
        policy = json.loads(row[0]) if row else None
        if policy is not None:
            _need(policy.get('version') == 'batch-clarification-policy/0.1'
                  and policy.get('source') == 'user_selected_policy'
                  and policy.get('policy') in {'wait', 'fail'}, 'CLARIFICATION_POLICY_INVALID')
            if policy.get('batch_sha256') != value['sha256']:
                _need(value.get('budget_revision'), 'CLARIFICATION_POLICY_BATCH_CHANGED')
                policy = _rebind_budget_policy(root, db, value, 'clarification_policy', policy)
            _need(requested is None or requested == policy['policy'], 'CLARIFICATION_POLICY_FROZEN')
        elif requested is not None:
            policy = {'version': 'batch-clarification-policy/0.1', 'source': 'user_selected_policy',
                      'batch_sha256': value['sha256'], 'policy': requested}
            db.execute('INSERT INTO batch_control VALUES(?,?)', ('clarification_policy', encode(policy)))
    return policy['policy'] if policy else 'wait'


def _delegated_property_answers(root, value, ledger, jobs):
    """Answer stopped native previews only; never inspect private evaluation data."""
    if (Path(root)/'pause-between-tasks').exists() or not _property_authorization(root, value):
        return
    for state in _states(root):
        if (state['status'] != 'awaiting_user' or state['arm'] not in {'B', 'E', 'F'}
                or state['run_id'] in jobs):
            continue
        key = 'property-policy:'+state['run_id']+':'+state['question']['question_id']
        with ledger.transaction() as db:
            if db.execute('SELECT 1 FROM batch_control WHERE key=?', (key,)).fetchone():
                continue
        _need(not state.get('activities') and not any(c['state'] == 'inflight' for c in ledger.calls(state['run_id'])),
              'PROPERTY_CONFIRMATION_REQUIRES_QUIESCENCE')
        _source_guard(root, value, case_id=state['case_id'])
        public = Path(root)/'cases'/state['case_id']/'public'
        answer = _verified_property_answer(state, public/'model.ifc', public/'request.txt')
        if answer is not None:
            _need(answer.get('source') == 'user_confirmed'
                  and answer.get('question_id') == state['question']['question_id'],
                  'PROPERTY_POLICY_ANSWER_BINDING_INVALID')
            carrier.answer(root, state['run_id'], answer)
        with ledger.transaction() as db:
            db.execute('INSERT INTO batch_control VALUES(?,?)', (key, encode({
                'source': 'user_delegated_policy', 'decision': 'confirmed' if answer else 'clarification_retained',
                'question_id': state['question']['question_id'],
                'verification': answer.get('provenance') if answer else None})))


def _fail_pending_clarifications(root, value, config, ledger, jobs):
    """Retain unanswered questions; only a stopped task can become no-output."""
    if (Path(root)/'pause-between-tasks').exists():
        return
    for state in _states(root):
        if state['status'] != 'awaiting_user':
            continue
        run_id = state['run_id']
        if run_id in jobs:
            if state['arm'] == 'D':
                carrier.request_clarification_stop(root, run_id, state['question']['question_id'])
            continue
        _need(not state.get('activities') and not any(c['state'] == 'inflight' for c in ledger.calls(run_id)),
              'CLARIFICATION_FAILURE_REQUIRES_QUIESCENCE')
        _need(not docker('ps', '--filter', f'name=^/{config["routes"][run_id]["container"]}$', '--format', '{{.Names}}'),
              'NATIVE_PROCESS_STOP_NOT_CONFIRMED')
        _source_guard(root, value, case_id=state['case_id'])
        ledger.finish(run_id, 'no_output', detail=CLARIFICATION_FAILURE)
        _publish(root, value)
        _retire_task(root, ledger.snapshot(run_id), config, value.get('retain_debug', False))


def _retire_task(root, state, config, retain_debug=False):
    """Discard terminal scratch, unless debug retention was frozen at prepare.

    Both modes require compact export and confirmed stop.

    Financial flags, questions, failure classification and formal authority stay
    in the shared ledger. A pending task never reaches this function.
    """
    root = safe_path(Path(root))
    run_id = state['run_id']
    _need(state['status'] in TERMINAL and not state.get('activities'), 'ACTIVE_TASK_CANNOT_RETIRE')
    ledger = ControllerLedger(root/'control.sqlite')
    _need(not any(c['state'] == 'inflight' for c in ledger.calls(run_id)), 'INFLIGHT_TASK_CANNOT_RETIRE')
    route = config['routes'][run_id]
    _need(not docker('ps', '--filter', f'name=^/{route["container"]}$', '--format', '{{.Names}}'),
          'NATIVE_PROCESS_STOP_NOT_CONFIRMED')
    with ledger.transaction() as db:
        _need(db.execute('SELECT 1 FROM batch_exports WHERE run_id=?', (run_id,)).fetchone(), 'EXPORT_REQUIRED_BEFORE_RETIRE')
    if retain_debug:
        return
    volumes = docker('volume', 'ls', '--filter', f'name=^{route["volume"]}$', '--format', '{{.Name}}')
    if volumes:
        _need(volumes == route['volume'] and not docker('ps', '-aq', '--filter',
              'volume='+route['volume']), 'NATIVE_VOLUME_STILL_ATTACHED')
        docker('volume', 'rm', route['volume'])
    with ledger.transaction() as db:
        _need(db.execute('SELECT 1 FROM batch_exports WHERE run_id=?', (run_id,)).fetchone(), 'EXPORT_REQUIRED_BEFORE_RETIRE')
        for request_id, raw in db.execute('SELECT request_id,response FROM calls WHERE run_id=?', (run_id,)).fetchall():
            response = json.loads(raw) if raw else {}
            flags = {k: response[k] for k in ('http_status','content_type','usage_complete','stream_complete','error_type') if k in response}
            flags['retained_as'] = 'usage flags; actual returned reasoning excerpt in report.md'
            flags['response_sha256'] = _digest(response)
            db.execute('UPDATE calls SET response=? WHERE run_id=? AND request_id=?', (encode(flags), run_id, request_id))
    # Explicit task-owned paths, confined to this fresh experiment root. Do not
    # touch source cases, formal artifacts, admission receipts or active peers.
    for relative in (Path('wire')/run_id, Path('workspaces')/run_id, Path('runtime')/run_id):
        path = safe_path(root/relative)
        _need(path.is_relative_to(root) and path != root, 'RETIRE_PATH_OUTSIDE_BATCH')
        if path.exists():
            for entry in path.rglob('*'):
                safe_path(entry)
            shutil.rmtree(path)
    safe_path(root/'runtime'/(run_id+'-commands.json')).unlink(missing_ok=True)


def _debug_files(destination):
    state = safe_path(destination/'state')
    _need((state/'task.json').is_file() and (state/'native').is_dir(), 'DEBUG_EXPORT_INCOMPLETE')
    files = {}
    for path in sorted(state.rglob('*')):
        safe_path(path)
        if path.is_file():
            files[path.relative_to(destination).as_posix()] = sha256(path)
    return files


def debug_export(root, *, run_id=None):
    """Copy retained, stopped Harness evidence; never start a model or overwrite it."""
    from .group_config import harness_profile
    from .isolated_b import IsolatedB, IsolatedBConfig
    root = safe_path(Path(root))
    with task_owner(root, 'batch-owner'):
        value = plan(root)
        _need(value.get('retain_debug') is True, 'DEBUG_RETENTION_REQUIRED')
        _need((root/'experiment.json').is_file(), 'BATCH_NOT_INITIALIZED')
        config = _initialize(root, value)
        runs = [run_id] if run_id else value['configuration']['order']
        _need(runs and set(runs) <= set(value['configuration']['order']), 'UNKNOWN_DEBUG_RUN')
        ledger = ControllerLedger(root/'control.sqlite')
        tasks = []
        for identifier in runs:
            state = ledger.snapshot(identifier)
            _need(state['arm'] in {'B', 'E', 'F'}, 'DEBUG_EXPORT_UNSUPPORTED_ARM')
            _retire_task(root, state, config, True)
            _source_guard(root, value, state['case_id'])
            tasks.append(state)
        exported = reused = 0
        for state in tasks:
            identifier, arm = state['run_id'], state['arm']
            route = config['routes'][identifier]
            profile = harness_profile(value['configuration'], arm)
            image = (value['configuration'].get('b') or {}).get('image', 'text2ifc/repair-tools:py312-ifc085-v2')
            digests = value['input_bindings'][state['case_id']]['input_digests']
            public_request = safe_path(root/'cases'/state['case_id']/'public/request.txt')
            native_request = safe_path(root/'workspaces'/identifier/'task.txt')
            _need(native_request.is_file(), 'DEBUG_EXPORT_REQUEST_MISSING')
            # DirectRunner materializes stripped public text plus one newline.
            # Native task.json binds that mounted file's bytes; host newline
            # translation can legitimately differ from the frozen public file.
            _need(native_request.read_text(encoding='utf8') == public_request.read_text(encoding='utf8').strip()+'\n',
                  'DEBUG_EXPORT_REQUEST_BINDING_MISMATCH')
            binding = {'run_id': identifier, 'source_sha256': digests['model.ifc'],
                       'request_sha256': sha256(native_request), 'model': profile['model'], 'model_profile': profile}
            identity = {'batch_sha256': value['sha256'], 'binding': binding,
                        'image': image, 'volume': route['volume']}
            destination = safe_path(root/'debug'/identifier)
            _need(destination.is_relative_to(root/'debug'), 'DEBUG_EXPORT_PATH_ESCAPE')
            receipt_path = safe_path(destination/'receipt.json')
            if destination.exists():
                _need(receipt_path.is_file(), 'DEBUG_EXPORT_INCOMPLETE')
                receipt = read_json(receipt_path)
                body = {k: v for k, v in receipt.items() if k != 'sha256'}
                _need(receipt.get('sha256') == _digest(body) and receipt.get('identity') == identity
                      and receipt.get('files') == _debug_files(destination), 'DEBUG_EXPORT_CHANGED')
                reused += 1
            else:
                cfg = IsolatedBConfig(root/'runtime/b', root/'workspaces'/identifier,
                    route['volume'], config['network'], 'http://repair-gateway:8000/'+route['token']+'/v1',
                    image=image, container_name=route['container'], model=profile['model'], model_profile=profile,
                    evidence_class='live' if value['mode'] == 'live' else 'deterministic_fake_http')
                IsolatedB(cfg).export_state(destination)
                files = _debug_files(destination)
                task = read_json(destination/'state/task.json')
                _need(all(task.get(k) == v for k, v in binding.items()), 'DEBUG_EXPORT_BINDING_MISMATCH')
                receipt = {'schema_version': 'repair-debug-export/0.1', 'identity': identity, 'files': files}
                receipt['sha256'] = _digest(receipt)
                write_json(receipt_path, receipt)
                exported += 1
        return {'event': 'summary', 'debug_snapshots': len(tasks), 'exported': exported,
                'reused': reused, 'path': str(root/'debug')}


def _run_slots(root, value, config, ledger, capacity, *, clarification_policy='wait'):
    """Retain owned jobs through controller errors; never replay a failed task."""
    jobs = {}
    try:
        return _dispatch_slots(root, value, config, ledger, capacity, jobs=jobs,
                               clarification_policy=clarification_policy)
    except Exception as error:
        fields = _controller_failure(error)
        try:
            _control(root, 'draining', **fields, active_count=len(jobs))
        except (OSError, ValueError, sqlite3.Error):
            pass  # A failed status write must not abandon native ownership.
        finished = []
        while jobs:
            warm_runs = {run for run in jobs if run.endswith('-D')}
            if warm_runs:
                try:
                    _queued_answer(root, run_ids=warm_runs)
                except (OSError, ValueError, sqlite3.Error):
                    pass  # Keep the question/answer and warm owner for correction.
            for run_id, job in list(jobs.items()):
                if run_id.endswith('-D'):
                    try:
                        current = _task_control(root, run_id)
                        if current['status'] == 'awaiting_user':
                            question = current['question']
                            if clarification_policy == 'fail':
                                carrier.request_clarification_stop(root, run_id, question['question_id'])
                            else:
                                _control(root, 'attention', reason='CLARIFICATION_REQUIRED',
                                         run_id=run_id, question_id=question['question_id'], warm_owner=True)
                    except (OSError, ValueError, sqlite3.Error):
                        pass
                if job.poll() is None:
                    continue
                job.wait()
                del jobs[run_id]
                finished.append(run_id)
            if jobs:
                time.sleep(.5)
        try:
            if clarification_policy == 'fail':
                _fail_pending_clarifications(root, value, config, ledger, jobs)
            _source_guard(root, value)
            _publish(root, value)
            for run_id in finished:
                state = next(s for s in _states(root) if s['run_id'] == run_id)
                if state['status'] in TERMINAL:
                    _retire_task(root, state, config, value.get('retain_debug', False))
        except Exception as cleanup:
            fields['drain_cleanup_reason'] = type(cleanup).__name__+': '+str(cleanup)[:240]
        return 2, 'attention', fields


def _dispatch_slots(root, value, config, ledger, capacity, *, jobs, clarification_policy='wait'):
    """One persistent owner dispatches bounded, independent native processes.

    Blocking faults stop new dispatch. Already running tasks drain to their
    own terminal/wait states; native D keeps its owner while waiting for facts.
    """
    seen_questions = {}
    blocked = None
    while True:
        if blocked is None:
            try:
                _queued_answer(root)
            except Exception as error:
                blocked = {'reason': type(error).__name__+': '+str(error)[:240]}
        for run_id, job in list(jobs.items()):
            current = _task_control(root, run_id)
            question = current.get('question')
            if run_id.endswith('-D') and current['status'] == 'awaiting_user' and clarification_policy == 'wait':
                if seen_questions.get(run_id) != question['question_id']:
                    seen_questions[run_id] = question['question_id']
                    _control(root, 'attention', reason='CLARIFICATION_REQUIRED', run_id=run_id)
                    _emit('attention', reason='CLARIFICATION_REQUIRED', run_id=run_id,
                          question_id=question['question_id'], warm_owner=True)
            elif run_id in seen_questions:
                del seen_questions[run_id]
            code = job.poll()
            if code is None:
                continue
            job.wait()
            del jobs[run_id]
            try:
                _source_guard(root, value, case_id=run_id.rsplit('-', 1)[0])
                _publish(root, value)
                state = next(s for s in _states(root) if s['run_id'] == run_id)
                if code:
                    blocked = blocked or {'reason': 'TASK_PROCESS_EXITED', 'run_id': run_id,
                                          'exit_code': code, 'stderr': job.tail.decode('utf8', errors='replace'),
                                          'worker_reason': _worker_reason(job.tail)}
                elif state['status'] not in TERMINAL | {'awaiting_user'}:
                    blocked = blocked or {'reason': 'RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH', 'run_id': run_id}
                elif state['status'] in TERMINAL:
                    if _interface_fault(root, run_id):
                        blocked = blocked or {'reason': 'PROVIDER_INTERFACE_FAILURE', 'run_id': run_id}
                    elif _environment_fault(state):
                        blocked = blocked or {'reason': 'ENVIRONMENT_OR_ISOLATION_FAILURE', 'run_id': run_id}
                    blocked = blocked or common_failure(_states(root))
                    _retire_task(root, state, config, value.get('retain_debug', False))
            except Exception as error:
                blocked = blocked or {'reason': type(error).__name__+': '+str(error)[:240], 'run_id': run_id}
        if not blocked:
            try:
                _delegated_property_answers(root, value, ledger, jobs)
                if clarification_policy == 'fail':
                    _fail_pending_clarifications(root, value, config, ledger, jobs)
            except Exception as error:
                blocked = {'reason': type(error).__name__+': '+str(error)[:240]}
        states = {s['run_id']: s for s in _states(root)}
        # Holds can be released while unrelated jobs are still running.
        with closing(_database(root)) as db:
            held = set(_held_groups(db))
        waiting = [s for s in states.values() if s['status'] == 'awaiting_user']
        requested_pause = (Path(root)/'pause-between-tasks').exists()
        # Only the short registration step is serialized. Once the worker has
        # registered running, all frozen task slots may execute concurrently.
        pending_start = any(_task_control(root, run)['status'] == 'ready' for run in jobs)
        if not blocked and not requested_pause and not pending_start:
            for run_id in _dispatch_order(value, config, states):
                if len(jobs) >= capacity:
                    break
                state = states[run_id]
                if state['arm'] in held:
                    continue
                if run_id in jobs or state['status'] in TERMINAL | {'awaiting_user'}:
                    continue
                qwen_limit = value.get('scheduler', {}).get('qwen_max_running')
                if (qwen_limit is not None and state['arm'] in {'F', 'G'}
                        and sum(run.rsplit('-', 1)[1] in {'F', 'G'} for run in jobs) >= qwen_limit):
                    continue
                # A confirmed cold answer must finish its existing session even
                # while another task waits. New tasks remain blocked by questions.
                if waiting and state['status'] == 'ready':
                    continue
                if state.get('activities') or any(c['state'] == 'inflight' for c in ledger.calls(run_id)):
                    blocked = {'reason': 'RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH', 'run_id': run_id}
                    break
                if state['status'] == 'running' and state['arm'] == 'D':
                    blocked = {'reason': 'D_WARM_OWNER_MISSING_NO_COLD_RESTART', 'run_id': run_id}
                    break
                if not may_start(state):
                    ledger.finish(run_id, 'budget_exhausted', detail='FROZEN_TASK_BUDGET_EXHAUSTED')
                    continue
                try:
                    jobs[run_id] = _Process(CLI+['run', '--root', str(root), '--run-id', run_id])
                    if _task_control(root, run_id)['status'] == 'ready':
                        break
                except Exception as error:
                    blocked = {'reason': type(error).__name__+': '+str(error)[:240], 'run_id': run_id}
                    break
        if not jobs:
            _publish(root, value)
            _source_guard(root, value)
            if blocked:
                return 2, 'attention', blocked
            if waiting:
                return 2, 'attention', {'reason': 'CLARIFICATION_REQUIRED',
                                        'run_id': waiting[0]['run_id'], 'pending_count': len(waiting)}
            if requested_pause:
                return 0, 'paused', {'reason': 'requested_between_tasks'}
            pending = [s for s in _states(root) if s['status'] not in TERMINAL]
            if pending and all(s['arm'] in held for s in pending):
                return 0, 'paused', {'reason': 'HELD_GROUPS_REMAINING'}
            if all(s['status'] in TERMINAL for s in _states(root)):
                return 0, 'complete', {}
        # A newly launched native worker can ask before this iteration ends.
        # Publish waiting state before sleeping, without dispatching more jobs.
        waiting = [s for s in _states(root) if s['status'] == 'awaiting_user']
        if waiting:
            _control(root, 'attention', reason='CLARIFICATION_REQUIRED', run_id=waiting[0]['run_id'])
        elif blocked or requested_pause:
            _control(root, 'draining', **(blocked or {'reason': 'requested_between_tasks'}))
        else:
            _control(root, 'running', active_count=len(jobs))
        time.sleep(.5)


def _execute(root, *, confirm_existing_properties=False, clarification_policy=None):
    value = plan(root)
    _source_guard(root, value)
    config = _initialize(root, value)
    ledger = ControllerLedger(Path(root)/'control.sqlite')
    capacity = value.get('scheduler', {}).get('max_running', 1)
    if value['schema_version'] in PARALLEL_PLAN_SCHEMAS:
        ledger.configure_concurrency(capacity, stage=SCALABLE_STAGE)
    if value['mode'] == 'live':
        _check_admission(root, config['configuration'])
    _property_authorization(root, value, grant=confirm_existing_properties)
    policy = _clarification_policy(root, value, clarification_policy)
    start_id = uuid.uuid4().hex
    service = _Process(CLI+['serve', '--root', str(root), '--service-start-id', start_id])
    retained = False
    stop_error = None
    outcome = (2, 'attention', {'reason': 'SERVICE_START_TIMEOUT'})
    try:
        # A large frozen batch is checked again by the child before serving.
        # Keep this bounded startup wait separate from each task's active budget.
        deadline = time.monotonic()+600
        while True:
            if service.poll() is not None:
                service.wait()
                outcome = (2, 'attention', {'reason': 'SERVICE_START_FAILED', 'exit_code': service.process.returncode})
                break
            path = Path(root)/'service.json'
            if path.exists():
                ready = read_json(path)
                if ready.get('state') == 'running' and ready.get('start_id') == start_id:
                    _control(root, 'running')
                    outcome = _run_slots(root, value, config, ledger, capacity, clarification_policy=policy)
                    break
            if time.monotonic() >= deadline:
                break
            time.sleep(.2)
    finally:
        try:
            carrier.request_service_stop(root)
        except (ValueError, OSError, sqlite3.Error) as error:
            retained = True
            stop_error = type(error).__name__+': '+str(error)[:240]
        else:
            try:
                service.wait(timeout=45)
            except (OSError, subprocess.TimeoutExpired) as error:
                retained = True
                stop_error = type(error).__name__+': '+str(error)[:240]
    code, event, fields = outcome
    if retained:
        code, event = 2, 'attention'
        fields = {'reason': 'ACTIVE_SERVICE_RETAINED', **fields, 'service_retained': True}
        if stop_error:
            fields['service_stop_reason'] = stop_error
    _control(root, event, **fields)
    _emit(event, **brief_status(root), **{k: v for k, v in fields.items() if k != 'reason'},
          results=str(Path(root)/'results/README.md'))
    return code


def run(root, *, confirm_existing_properties=False, clarification_policy=None):
    root = safe_path(Path(root))
    with task_owner(root, 'batch-owner'):
        previous = {}
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda *_: pause(root))
        try:
            return _execute(root, confirm_existing_properties=confirm_existing_properties,
                            clarification_policy=clarification_policy)
        except Exception as error:
            if (root/'control.sqlite').is_file():
                return _attention(root, type(error).__name__+': '+str(error)[:240])
            raise
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def _verify_resume_position(root, position):
    """Optional operator checkpoint assertion; never skip or rewrite task state."""
    value = plan(root)
    cases = list(dict.fromkeys(run.rsplit('-', 1)[0] for run in value['configuration']['order']))
    _need(type(position) is int and 1 <= position <= len(cases), 'INVALID_RESUME_CASE_INDEX')
    preceding = set(cases[:position-1])
    if (Path(root)/'control.sqlite').is_file():
        with closing(_database(root)) as db:
            statuses = dict(db.execute("SELECT run_id,json_extract(state,'$.status') FROM runs"))
        expected = [run for run in value['configuration']['order'] if run.rsplit('-', 1)[0] in preceding]
        _need(all(statuses.get(run) in TERMINAL for run in expected), 'EARLIER_CASE_INCOMPLETE')
    else:
        _need(not preceding, 'EARLIER_CASE_INCOMPLETE')


def resume(root, *, answer_file=None, run_id=None, from_case=None, confirm_existing_properties=False,
           clarification_policy=None):
    root = safe_path(Path(root))
    if from_case is not None:
        _verify_resume_position(root, from_case)
    clear_pause(root)
    if answer_file is not None:
        answer = read_json(safe_path(Path(answer_file)))
        _need(run_id and answer.get('source') == 'user_confirmed', 'USER_CONFIRMED_ANSWER_REQUIRED')
        try:
            with task_owner(root, 'batch-owner'):
                ledger = ControllerLedger(root/'control.sqlite')
                state = ledger.snapshot(run_id)
                _need(state['status'] == 'awaiting_user', 'PENDING_QUESTION_REQUIRED')
                answer.setdefault('event_id', 'user:'+run_id+':'+state['question']['question_id'])
                answer.setdefault('question_id', state['question']['question_id'])
                with ledger.transaction() as db:
                    db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
                    db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                               ('answer:'+run_id, encode({'run_id': run_id, 'answer': answer})))
        except ValueError as error:
            if str(error) != 'RUN_CONTROLLER_ALREADY_ACTIVE':
                raise
            _need(clarification_policy is None, 'CLARIFICATION_POLICY_REQUIRES_IDLE_CONTROLLER')
            carrier.answer(root, run_id, answer)
            return 0
    return run(root, confirm_existing_properties=confirm_existing_properties, clarification_policy=clarification_policy)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'refresh-unstarted', 'apply-budget', 'gate', 'admit', 'run', 'pause', 'resume', 'status', 'debug-export', 'hold-groups', 'release-groups'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--dataset', type=Path)
    parser.add_argument('--input-format', choices=['auto', 'dataset', 'pairs'], default='auto')
    parser.add_argument('--scope', choices=['full', 'two-rounds'], default='full')
    parser.add_argument('--concurrency', type=int, help='Prepare/refresh-unstarted: fixed running-task slots, 1..7; default 2')
    parser.add_argument('--qwen-first', action=argparse.BooleanOptionalAction, default=None,
                        help='Prepare/refresh-unstarted: prioritize F/G, at most two Qwen tasks at once')
    parser.add_argument('--retain-debug', action=argparse.BooleanOptionalAction, default=None,
                        help='Prepare only: preserve raw responses, state volume and runtime artifacts')
    parser.add_argument('--default-level', choices=['S1', 'S2', 'S3'])
    parser.add_argument('--index', type=Path, help='Optional inputs.csv with paths and per-case levels')
    parser.add_argument('--delivery-receipt', type=Path, help='Prepare pairs: reuse hash-bound dataset validation evidence')
    parser.add_argument('--request-convention', choices=[PROPERTY_UNITS_REQUEST_CONVENTION],
                        help='Prepare/refresh-unstarted: annotate public requests with the existing IFC property-unit convention')
    parser.add_argument('--groups', nargs='+', choices=list('ABCDEFG'), help='Prepare groups, or arms to hold/release without changing frozen tasks')
    parser.add_argument('--reason', help='Required operator reason for hold-groups/release-groups')
    parser.add_argument('--case-ids', nargs='+', help='Prepare full mode: freeze only these admitted case IDs')
    parser.add_argument('--providers', type=Path)
    parser.add_argument('--property-model', type=Path)
    parser.add_argument('--mode', choices=['live', 'offline'], default='live')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--second-count', type=int, choices=[1, 2], default=2)
    parser.add_argument('--brief', action='store_true')
    parser.add_argument('--tests', nargs='+')
    parser.add_argument('--revision', help='Gate/admit: append a named receipt without replacing earlier evidence')
    parser.add_argument('--scoped-receipt', type=Path, help='Admit only: named source-bound scoped gate receipt')
    parser.add_argument('--native-receipt', type=Path)
    parser.add_argument('--property-receipt', type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--answer-file', type=Path)
    parser.add_argument('--from-case', type=int, help='Resume: 1-based frozen CSV row; preceding cases must be terminal')
    parser.add_argument('--confirm-existing-properties', action='store_true',
                        help='Run/resume only: delegate verified existing-property preview confirmations; unanswered questions follow the clarification policy')
    parser.add_argument('--clarification-policy', choices=['wait', 'fail'],
                        help='Run/resume only: freeze wait (default) or count unanswered clarification as no-output for complete-input batches; resume reuses the saved policy')
    args = parser.parse_args(argv)
    try:
        return _command(args)
    except Exception as error:
        _emit('attention', reason=type(error).__name__+': '+str(error)[:240])
        return 2


def _command(args):
    _need(args.reason is None or args.command in {'hold-groups', 'release-groups'}, 'GROUP_HOLD_REASON_ONLY')
    _need(args.groups is None or args.command in {'prepare', 'hold-groups', 'release-groups'}, 'GROUP_SELECTION_COMMAND_ONLY')
    _need(not args.confirm_existing_properties or args.command in {'run', 'resume'}, 'PROPERTY_AUTHORIZATION_EXECUTION_ONLY')
    _need(args.clarification_policy is None or args.command in {'run', 'resume'}, 'CLARIFICATION_POLICY_EXECUTION_ONLY')
    _need(args.request_convention is None or args.command in {'prepare', 'refresh-unstarted'}, 'REQUEST_CONVENTION_UNSTARTED_ONLY')
    _need(args.revision is None or args.command in {'gate', 'admit'}, 'GATE_REVISION_ONLY')
    _need(args.scoped_receipt is None or args.command == 'admit', 'SCOPED_RECEIPT_ADMIT_ONLY')
    if args.from_case is not None:
        _need(args.command == 'resume', 'RESUME_POSITION_ONLY')
    if args.command != 'prepare' and args.retain_debug is not None:
        _need(args.retain_debug == plan(args.root).get('retain_debug', False), 'RETENTION_POLICY_FROZEN')
    if args.command not in {'prepare', 'refresh-unstarted'} and args.concurrency is not None:
        frozen = plan(args.root).get('scheduler', {}).get('max_running', 1)
        _need(args.concurrency == frozen, 'CONCURRENCY_POLICY_FROZEN')
    if args.command not in {'prepare', 'refresh-unstarted'} and args.qwen_first is not None:
        _need(args.qwen_first == (plan(args.root)['schema_version'] == QWEN_PRIORITY_PLAN_SCHEMA),
              'SCHEDULER_POLICY_FROZEN')
    if args.command == 'prepare':
        _need(args.dataset is not None, 'DATASET_REQUIRED')
        result = prepare(args.root, args.dataset, seed=args.seed, second_count=args.second_count,
            providers=read_json(args.providers) if args.providers else None,
            property_model=args.property_model, mode=args.mode, scope=args.scope,
            input_format=args.input_format, concurrency=2 if args.concurrency is None else args.concurrency,
            default_level=args.default_level, index_path=args.index, groups=args.groups, case_ids=args.case_ids,
            retain_debug=bool(args.retain_debug), delivery_receipt=args.delivery_receipt,
            request_convention=args.request_convention, qwen_first=bool(args.qwen_first))
    elif args.command == 'refresh-unstarted':
        result = refresh_unstarted(args.root, request_convention=args.request_convention,
                                   concurrency=args.concurrency, qwen_first=args.qwen_first)
    elif args.command == 'apply-budget':
        result = apply_unstarted_budgets(args.root)
    elif args.command in {'hold-groups', 'release-groups'}:
        result = set_group_hold(args.root, args.groups, hold=args.command == 'hold-groups', reason=args.reason)
    elif args.command == 'debug-export':
        result = debug_export(args.root, run_id=args.run_id)
    elif args.command == 'gate':
        result = gate(args.root, args.tests, revision=args.revision)
    elif args.command == 'admit':
        result = admit(args.root, args.native_receipt, property_receipt=args.property_receipt,
                       scoped_receipt=args.scoped_receipt, **({'revision': args.revision} if args.revision else {}))
    elif args.command == 'run':
        return run(args.root, confirm_existing_properties=args.confirm_existing_properties,
                   clarification_policy=args.clarification_policy)
    elif args.command == 'pause':
        pause(args.root)
        result = {'event': 'pause_requested', 'contract': 'between tasks; active work persists'}
    elif args.command == 'resume':
        return resume(args.root, answer_file=args.answer_file, run_id=args.run_id, from_case=args.from_case,
                      confirm_existing_properties=args.confirm_existing_properties,
                      clarification_policy=args.clarification_policy)
    else:
        result = brief_status(args.root)
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
