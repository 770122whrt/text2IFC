"""Explicit development fork at a quiescent B question; never a blind retry.

The copied request IDs identify common, already billed work. Each branch carries
that usage in its task budget, while aggregate billing counts those IDs once.
No inference, key loading, prompt rewriting or answer submission occurs here.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import uuid

from .container_tools import docker, IMAGE
from .contracts import PUBLIC_FILES, read_json, safe_path, write_json
from .controller_owner import task_owner
from .isolated_b import verify_runtime_bundle
from .ledger import Ledger, encode, identifier


def _copy_tree(source, destination):
    source, destination = safe_path(Path(source)), safe_path(Path(destination))
    for path in source.rglob('*'):
        safe_path(path)
    shutil.copytree(source, destination)


def _clone_volume(source, destination):
    for name in (source, destination):
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,159}', name):
            raise ValueError('INVALID_STATE_VOLUME')
    if source == destination:
        raise ValueError('DISTINCT_STATE_VOLUMES_REQUIRED')
    docker('volume', 'inspect', source)
    if docker('ps', '--filter', 'volume=' + source, '--format', '{{.Names}}'):
        raise ValueError('NATIVE_STATE_NOT_QUIESCENT')
    if destination in docker('volume', 'ls', '--format', '{{.Name}}').splitlines():
        raise ValueError('TRIAL_VOLUME_ALREADY_EXISTS')
    docker('volume', 'create', destination)
    docker('run', '--rm', '--pull=never', '--network=none', '--read-only',
           '--user=0:0', '--cap-drop=ALL', '--cap-add=CHOWN',
           '--security-opt=no-new-privileges', '--memory=512m', '--cpus=1', '--pids-limit=32',
           '--mount', f'type=volume,source={destination},target=/copy,volume-nocopy',
           IMAGE, 'python', '-c', 'import os; os.chown("/copy",65532,65532)', timeout=30)
    # Native state files belong to the worker and may be mode 0600. Reading
    # them as that UID avoids extra root read privileges or changing originals.
    program = ('from pathlib import Path; import shutil; '
               'assert not list(Path("/copy").iterdir()); '
               'shutil.copytree("/original","/copy",dirs_exist_ok=True)')
    docker('run', '--rm', '--pull=never', '--network=none', '--read-only',
           '--user=65532:65532', '--cap-drop=ALL', '--security-opt=no-new-privileges',
           '--memory=512m', '--cpus=1', '--pids-limit=32',
           '--mount', f'type=volume,source={source},target=/original,readonly,volume-nocopy',
           '--mount', f'type=volume,source={destination},target=/copy,volume-nocopy',
           IMAGE, 'python', '-c', program, timeout=120)


def fork_pending_b(source, destination, run_id, *, trial):
    """Copy one unanswered B task into a separate, labelled development trial."""
    source, destination = safe_path(Path(source)), safe_path(Path(destination))
    identifier(run_id)
    identifier(trial)
    if destination.exists():
        raise ValueError('TRIAL_DESTINATION_ALREADY_EXISTS')
    if source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('DISTINCT_EXPERIMENT_ROOTS_REQUIRED')
    config = read_json(source / 'experiment.json')
    ledger = Ledger(source / 'control.sqlite')
    with task_owner(source, run_id), ledger.transaction() as db:
        state = ledger._load(db, run_id)
        if state['arm'] != 'B':
            raise ValueError('B_ARM_REQUIRED')
        if state['status'] != 'awaiting_user' or not state.get('question') or state.get('artifact'):
            raise ValueError('UNANSWERED_PENDING_QUESTION_REQUIRED')
        calls = ledger._calls(db, run_id)
        if state['activities'] or any(c['state'] == 'inflight' for c in calls):
            raise ValueError('QUIESCENT_TASK_REQUIRED')
        native = state.get('native', {}).get('result', {})
        question = native.get('clarification', {})
        if (question.get('clarification_id') != state['question']['question_id']
                or native.get('state_version') != state['question']['binding'].get('state_version')):
            raise ValueError('NATIVE_PENDING_BINDING_REQUIRED')
        workspace = safe_path(source / 'workspaces' / run_id)
        inputs = safe_path(source / 'inputs' / state['case_id'])
        if (safe_path(Path(state['metadata']['workspace'])) != workspace
                or safe_path(Path(state['metadata']['input_dir'])) != inputs):
            raise ValueError('TASK_WORKSPACE_BINDING_MISMATCH')
        if {p.name for p in inputs.iterdir()} != PUBLIC_FILES:
            raise ValueError('PUBLIC_INPUT_ALLOWLIST_REQUIRED')
        if {p.name for p in workspace.iterdir()} - {'model.ifc', 'task.txt', 'work', 'output'}:
            raise ValueError('WORKSPACE_ALLOWLIST_REQUIRED')
        verify_runtime_bundle(source / 'runtime/b')
        ledger._tick(state)  # Keep elapsed active work; checkpoint only human wait.
        suffix = uuid.uuid4().hex[:10]
        route = {'token': uuid.uuid4().hex, 'container': 'repair-trial-' + suffix + '-' + run_id.lower(),
                 'volume': 'repair-trial-state-' + suffix + '-' + run_id.lower()}
        destination.mkdir(parents=True)
        _copy_tree(inputs, destination / 'inputs' / state['case_id'])
        _copy_tree(workspace, destination / 'workspaces' / run_id)
        _copy_tree(source / 'runtime/b', destination / 'runtime/b')
        if (source / 'wire' / run_id).exists():
            _copy_tree(source / 'wire' / run_id, destination / 'wire' / run_id)
        _clone_volume(config['routes'][run_id]['volume'], route['volume'])
        child_state = copy.deepcopy(state)
        child_state['metadata']['workspace'] = str(destination / 'workspaces' / run_id)
        child_state['metadata']['input_dir'] = str(destination / 'inputs' / state['case_id'])
        child_state['native']['state_volume'] = route['volume']
        report = {'kind': 'controlled_clarification_development_trial', 'trial': trial,
                  'parent_root': str(source), 'parent_run_id': run_id,
                  'question_id': state['question']['question_id'], 'native_state_version': native['state_version'],
                  'shared_request_ids': [c['request_id'] for c in calls],
                  'shared_known_tokens': ledger.snapshot(run_id)['usage']['known_total_tokens'],
                  'new_calls_at_fork': 0, 'budget_reset': False,
                  'accounting': 'Task totals include common seed calls; aggregate billing deduplicates request IDs.',
                  'use': 'Development answer comparison only; excluded from original eight-task denominator.'}
        child_state['metadata']['clarification_trial'] = report
        child = Ledger(destination / 'control.sqlite')
        with child.transaction() as out:
            out.execute('INSERT INTO runs VALUES(?,?)', (run_id, encode(child_state)))
            for table in ('events', 'calls'):
                rows = db.execute(f'SELECT * FROM {table} WHERE run_id=? ORDER BY rowid', (run_id,)).fetchall()
                for row in rows:
                    values = dict(row)
                    if table == 'events':
                        del values['seq']
                    columns = ','.join(values)
                    placeholders = ','.join('?' for _ in values)
                    out.execute(f'INSERT INTO {table}({columns}) VALUES({placeholders})', tuple(values.values()))
            child._event(out, run_id, 'clarification_trial_fork', report)
        child_config = copy.deepcopy(config)
        child_config.update(order=[run_id], routes={run_id: route},
                            network='repair-trial-' + suffix, relay='repair-trial-relay-' + suffix,
                            clarification_trial=report)
        write_json(destination / 'experiment.json', child_config)
        write_json(destination / 'clarification-trial.json', report)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--trial', required=True)
    args = parser.parse_args()
    print(json.dumps(fork_pending_b(args.source, args.destination, args.run_id, trial=args.trial), ensure_ascii=False))


if __name__ == '__main__':
    main()
