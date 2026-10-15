"""Host-side compact export of terminal IFC results and returned model reasoning.

Runtime workspaces remain resumable while tasks are active. Export reads only
selected terminal tasks and never chooses an attempt by its score.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Callable, Mapping
import zipfile

from .budget import usage_summary
from .contracts import read_json, safe_path, sha256, write_json
from .ledger import Ledger, TERMINAL, identifier

REPO = Path(__file__).resolve().parents[3]
DIALOGUE = {'question', 'answer', 'delegated_card_answer'}
TASK_REPORT_BYTES = 64 * 1024
TASK_REASONING_BYTES = 8 * 1024


def _decoded(value):
    return json.loads(value) if isinstance(value, str) else value


def returned_messages(call):
    """Retain returned fields verbatim; do not infer an unreturned thought chain."""
    response = _decoded(call.get('response')) or {}
    body = response.get('body', response)
    if not isinstance(body, dict):
        return {'model_returned': None, 'messages': []}
    messages = []
    for choice in body.get('choices', []):
        message = choice.get('message', {})
        if isinstance(message, dict):
            messages.append({k: v for k, v in message.items()
                             if k in {'role', 'content', 'reasoning_content'}})
    messages.extend(block for block in body.get('content', [])
                    if isinstance(block, dict) and block.get('type') in
                    {'thinking', 'redacted_thinking', 'text'})
    return {'model_returned': body.get('model'), 'messages': messages}


def has_returned_thinking(messages):
    return any(message.get('reasoning_content') or (
        message.get('type') == 'thinking' and message.get('thinking')) for message in messages)


def read_run(row):
    """Read existing ZIP authority or a completed live ledger, without raw logs."""
    if row.get('history_record'):
        with zipfile.ZipFile(safe_path(Path(row['history_record']))) as archive:
            state = json.loads(archive.read('ledger/state.original.json'))
            calls = json.loads(archive.read('ledger/calls.sqlite-rows.original.json'))
            event_path = 'ledger/events.sqlite-rows.original.json'
            events = json.loads(archive.read(event_path)) if event_path in archive.namelist() else []
            state['dialogue_capture'] = 'recorded' if event_path in archive.namelist() else 'not_retained_in_source'
        for call in calls:
            for field in ('metadata', 'usage', 'response'):
                call[field] = _decoded(call.get(field))
        for event in events:
            event['payload'] = _decoded(event['payload'])
        return state, calls, events
    root = Path(row['ledger_root']) if row.get('ledger_root') else Path(row['authority']['path']).parent.parent
    path = safe_path(root/'control.sqlite')
    # Do not instantiate Ledger on a missing path: an export must not create evidence.
    if not path.is_file():
        raise ValueError('RESULT_LEDGER_MISSING')
    ledger = Ledger(path)
    return ledger.snapshot(row['run_id']), ledger.calls(row['run_id']), ledger.events(row['run_id'])


def call_summary(call):
    value = {k: call.get(k) for k in ('request_id', 'state', 'failed', 'reservation')}
    value.update({k: _decoded(call.get(k)) for k in ('metadata', 'usage')})
    return value


def _origin(row):
    ref = row.get('history_record') or row.get('ledger_root') or row.get('authority', {}).get('path')
    if ref is None:
        return None
    path = Path(ref).resolve()
    return path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.name


def _task_clip(value, limit):
    """Clip by UTF-8 bytes, without splitting a code point."""
    encoded = value.encode('utf8', errors='replace')
    return encoded[:limit].decode('utf8', errors='ignore'), len(encoded) > limit


def _task_json(value, limit=8192):
    text = json.dumps(value, ensure_ascii=False, indent=2)
    clipped, omitted = _task_clip(text, limit)
    return clipped + ('\n[omitted: detail exceeds report allocation]' if omitted else '')


def _task_reasoning(calls):
    """Capture only actual thinking fields, with one shared byte allocation."""
    pieces, thinking_responses, missing_responses = [], 0, 0
    for call in calls:
        response = call.get('response')
        body = response.get('body', response) if isinstance(response, dict) else {}
        thoughts = []
        if isinstance(body, dict):
            choices = body.get('choices')
            for choice in choices if isinstance(choices, list) else []:
                message = choice.get('message') if isinstance(choice, dict) else None
                text = message.get('reasoning_content') if isinstance(message, dict) else None
                if isinstance(text, str) and text:
                    thoughts.append(text)
            content = body.get('content')
            for block in content if isinstance(content, list) else []:
                text = block.get('thinking') if isinstance(block, dict) and block.get('type') == 'thinking' else None
                if isinstance(text, str) and text:
                    thoughts.append(text)
        if not thoughts:
            missing_responses += 1
            continue
        thinking_responses += 1
        stage = (call.get('metadata') or {}).get('stage', 'unknown')
        header, _ = _task_clip(f"Call {call['request_id']}; stage {stage}", 256)
        pieces.extend((header, text) for text in thoughts)
    marker = '\n    [omitted: returned reasoning exceeds 8 KiB]\n'
    remaining = TASK_REASONING_BYTES - len(marker.encode('utf8'))
    excerpt, truncated = [], False
    for header, text in pieces:
        # Bound before indentation too: many returned newlines must not grow an
        # unbounded rendering string. Indented text stays literal in Markdown.
        text, omitted = _task_clip(text, TASK_REASONING_BYTES)
        piece = '    [' + header + ']\n    ' + text.replace('\n', '\n    ') + '\n\n'
        piece, clipped = _task_clip(piece, remaining)
        excerpt.append(piece)
        remaining -= len(piece.encode('utf8'))
        truncated |= omitted or clipped
        if remaining == 0:
            truncated |= len(excerpt) < len(pieces)
            break
    rendered = ''.join(excerpt).rstrip('\n') + (marker if truncated else '')
    return {'status': 'returned' if thinking_responses else 'not_returned',
            'thinking_responses': thinking_responses, 'missing_responses': missing_responses,
            'bytes': len(rendered.encode('utf8')), 'truncated': truncated, 'excerpt': rendered}


def _task_validation(value, *, source, missing='not_retained'):
    if not isinstance(value, Mapping):
        return {'status': missing, 'passed': None, 'source': source}
    passed = value.get('passed')
    passed = passed if type(passed) is bool else None
    status = value.get('status')
    status = status if isinstance(status, str) else 'passed' if passed is True else 'failed' if passed is False else 'recorded'
    status, _ = _task_clip(status, 128)
    return {'status': status, 'passed': passed, 'source': source}


def export_task(root: Path, destination: Path, run_id: str, *,
                format_check: Mapping[str, Any] | Callable[[Path], Mapping[str, Any]] | None = None) -> dict:
    """Export one terminal task as report.md and its unique frozen formal IFC.

    ``format_check`` is a recorded result mapping or a callable receiving the
    hash-bound formal IFC path. It runs only for submitted tasks. No native
    validation or task score is inferred from submission. This function reads
    the ledger in read-only mode and never scans runtime/staging IFC files.
    """
    identifier(run_id)
    root, destination = safe_path(Path(root)), safe_path(Path(destination))
    path = safe_path(root/'control.sqlite')
    if not path.is_file():
        raise ValueError('RESULT_LEDGER_MISSING')
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')
        state = Ledger._load(db, run_id)
        calls = Ledger._calls(db, run_id)
        event = db.execute("SELECT payload FROM events WHERE run_id=? AND kind='terminal' ORDER BY seq DESC LIMIT 1",
                           (run_id,)).fetchone()
        terminal = json.loads(event['payload']) if event else {}
    for field in ('case_id', 'arm'):
        identifier(state[field])
    case_id, arm, status = state['case_id'], state['arm'], state['status']
    # Windows aliases such as trailing dots, device names and ADS must not
    # collapse two case names onto the same output directory.
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if arm not in set('ABCDEFG') or ':' in case_id or case_id.endswith('.') or case_id.split('.')[0].upper() in reserved:
        raise ValueError('INVALID_RESULT_PATH')
    if status not in TERMINAL:
        raise ValueError('TERMINAL_REQUIRED')
    artifact = state.get('artifact')
    if (status == 'submitted') != bool(artifact):
        raise ValueError('TERMINAL_ARTIFACT_MISMATCH')
    if (state.get('run_id') != run_id or state.get('activities')
            or any(call['state'] == 'inflight' for call in calls)
            or terminal.get('status') != status or terminal.get('artifact') != artifact):
        raise ValueError('TERMINAL_STATE_MISMATCH')
    source, digest = None, None
    if artifact:
        if not isinstance(artifact, dict) or not artifact.get('path'):
            raise ValueError('FORMAL_ARTIFACT_PATH_MISMATCH')
        source = safe_path(Path(artifact['path']))
        formal = safe_path(root/'artifacts'/run_id/'result.ifc')
        if source != formal:
            raise ValueError('FORMAL_ARTIFACT_PATH_MISMATCH')
        if not source.is_file():
            raise ValueError('FORMAL_ARTIFACT_MISSING')
        digest = sha256(source)
        if artifact.get('sha256') != digest:
            raise ValueError('FORMAL_ARTIFACT_HASH_MISMATCH')
    leaf = safe_path(destination/case_id/arm)
    report_path, target = safe_path(leaf/'report.md'), safe_path(leaf/'repaired.ifc')
    origin = hashlib.sha256(str(root).encode('utf8')).hexdigest()
    binding = '<!-- repair-comparison-task:'+run_id+':'+origin+' -->\n'
    if status != 'submitted' and target.exists():
        raise ValueError('NO_OUTPUT_ARTIFACT_EXISTS')
    if leaf.exists():
        if not leaf.is_dir() or any(item.name not in {'report.md', 'repaired.ifc'} for item in leaf.iterdir()):
            raise ValueError('RESULT_DIRECTORY_NOT_COMPACT')
        if report_path.exists():
            with report_path.open('rb') as handle:
                if handle.readline() != binding.encode('utf8'):
                    raise ValueError('RESULT_TASK_EXISTS')
    if target.exists() and (not target.is_file() or sha256(target) != digest):
        raise ValueError('RESULT_ARTIFACT_EXISTS')
    native = state.get('native') or {}
    from text2ifc_ifc_repair.scene_diagnostics import checked_scene_diagnostics
    diagnostics = checked_scene_diagnostics(native.get('scene_diagnostics')) if isinstance(native, dict) else None
    native = native.get('result', {}) if isinstance(native, dict) else {}
    native = native.get('result', native) if isinstance(native, dict) else {}
    native = native if isinstance(native, dict) else {}
    runtime = {key: native[key] for key in ('status', 'stage', 'error', 'error_code', 'reason_code',
               'finish_reason', 'complete_repair_success', 'successful_artifact_publishable') if key in native}
    for key in ('status', 'stage', 'reason_code'):
        runtime.setdefault(key, 'not_retained')
    native_check = next((native[key] for key in ('native_validation', 'validation')
                         if isinstance(native.get(key), Mapping)), None)
    native_validation = _task_validation(native_check, source='recorded native result')
    if source is None:
        common_check = {'status': 'not_applicable', 'passed': None, 'reason': 'No formally submitted IFC.'}
    else:
        try:
            common_check = format_check(source) if callable(format_check) else format_check
            if common_check is None:
                common_check = state.get('common_format_validation')
            if common_check is None:
                common_check = {'status': 'pending', 'passed': None, 'reason': 'Common format validation not performed or retained.'}
            if not isinstance(common_check, Mapping):
                raise TypeError('Format check must return a result mapping.')
        except Exception as error:
            common_check = {'status': 'error', 'passed': None, 'error': f'{type(error).__name__}: {error}'}
        if sha256(source) != digest:
            raise ValueError('FORMAL_ARTIFACT_HASH_MISMATCH')
    common_validation = _task_validation(common_check, source='common format check', missing='pending')
    usage = usage_summary(calls, Ledger.limits(state)['tokens'])
    started, ended = state.get('started'), state.get('ended')
    timing = {key: state.get(key) for key in ('started', 'ended', 'active_elapsed_s', 'human_wait_s')}
    timing['wall_elapsed_s'] = ended-started if started is not None and ended is not None else None
    reasoning = _task_reasoning(calls)
    missing = ('Missing provider reasoning: no thought chain was returned; no thoughts inferred.'
               if reasoning['status'] == 'not_returned' else
               f"Missing provider reasoning in {reasoning['missing_responses']} recorded calls; no thoughts inferred.")
    lines = [binding.rstrip('\n'), '# Repair comparison task', '', f'Run ID: {run_id}',
             f'Case ID: {case_id}', f'Arm: {arm}', f'Evidence mode: {state.get("mode", "not_retained")}', f'Ledger authority: {path}',
             f'Terminal status: {status}',
             'Formal submission: '+('submitted' if artifact else 'none'),
             'Repair score: pending; submission does not imply repair success.',
             'Artifact: '+('repaired.ifc' if artifact else 'none'),
             'Artifact SHA-256: '+(digest or 'not applicable'), '',
             'Bounded scene diagnostics (missing means not retained):', '```json',
             json.dumps(diagnostics, ensure_ascii=False, separators=(',', ':'), allow_nan=False), '```', '',
             'Native runtime and stage:', '```json', _task_json(runtime), '```', '', 'Terminal failure/reason:', '```json',
             _task_json(terminal.get('detail', state.get('detail', 'not_retained'))), '```', '',
             'Unanswered clarification (retained without a fabricated answer):', '```json',
             _task_json(state.get('question')), '```', '',
             'Existing native validation (recorded, not rerun by export):', '```json',
             _task_json({'summary': native_validation, 'detail': native_check}), '```', '',
             'Common format validation (separate from submission and task score):', '```json',
             _task_json({'summary': common_validation, 'detail': dict(common_check)}), '```', '',
             'Actual returned usage; null totals remain unknown:', '```json', _task_json(usage, 4096),
             '```', '', 'Budget and time (seconds):', '```json',
             _task_json({'budget': state['budget'], 'time': timing}, 4096), '```', '',
             f"Reasoning status: {reasoning['status']}", missing,
             f"Returned thinking responses: {reasoning['thinking_responses']}",
             f"Reasoning omitted by byte limit: {str(reasoning['truncated']).lower()}",
             '', '<!-- returned-reasoning:start -->', reasoning['excerpt'], '<!-- returned-reasoning:end -->', '']
    encoded = '\n'.join(lines).encode('utf8', errors='replace')
    if len(encoded) > TASK_REPORT_BYTES:
        raise ValueError('RESULT_REPORT_BUDGET_EXCEEDED')
    leaf.mkdir(parents=True, exist_ok=True)
    if source is not None and not target.exists():
        try:
            with source.open('rb') as incoming, target.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
        except FileExistsError:
            if sha256(target) != digest:
                raise ValueError('RESULT_ARTIFACT_EXISTS')
        if sha256(target) != digest:
            raise ValueError('FORMAL_ARTIFACT_HASH_MISMATCH')
    # Recheck ownership at write time; a concurrent different task cannot
    # overwrite the report occupying this unique case/arm directory.
    try:
        with report_path.open('xb') as handle:
            handle.write(encoded)
    except FileExistsError:
        with report_path.open('rb') as handle:
            if handle.readline() != binding.encode('utf8'):
                raise ValueError('RESULT_TASK_EXISTS')
        if report_path.read_bytes() != encoded:
            report_path.write_bytes(encoded)
    return {'run_id': run_id, 'case_id': case_id, 'arm': arm, 'status': status,
            'report': report_path.relative_to(destination).as_posix(), 'report_bytes': len(encoded),
            'artifact': target.relative_to(destination).as_posix() if artifact else None,
            'artifact_sha256': digest, 'usage': usage, 'time': timing,
            'reasoning_status': reasoning['status'], 'reasoning_bytes': reasoning['bytes'],
            'reasoning_truncated': reasoning['truncated'], 'thinking_responses': reasoning['thinking_responses'],
            'scene_diagnostics': diagnostics,
            'native_validation': native_validation, 'common_format_validation': common_validation}


def export_runs(rows, destination):
    """Write one records file, one reasoning stream, and each unique formal IFC."""
    destination = safe_path(Path(destination))
    seen = set()
    material = []
    # Validate the full selection before exporting any selected artifact.
    for row in rows:
        for field in ('run_id', 'case_id', 'arm'):
            identifier(row[field])
        if row['arm'] not in {'A', 'B', 'C', 'D'} or row['case_id'] in {'.', '..'} or any(
                char in row['case_id'] for char in ':'):
            raise ValueError('INVALID_RESULT_PATH')
        key = row['case_id'], row['arm']
        if key in seen:
            raise ValueError('DUPLICATE_SELECTION')
        seen.add(key)
        if row['status'] not in TERMINAL:
            raise ValueError('TERMINAL_REQUIRED')
        if (row['status'] == 'submitted') != bool(row.get('artifact')):
            raise ValueError('TERMINAL_ARTIFACT_MISMATCH')
        state, calls, events = read_run(row)
        if state['status'] != row['status'] or state.get('activities'):
            raise ValueError('TERMINAL_STATE_MISMATCH')
        evaluation = row.get('evaluation')
        if isinstance(evaluation, dict) and 'path' in evaluation:
            evaluation = read_json(safe_path(Path(evaluation['path'])))
        material.append((row, state, calls, events, evaluation))
    destination.mkdir(parents=True, exist_ok=True)
    exported, reasoning = [], []
    for row, state, calls, events, evaluation in material:
        # Existing machine facts retain their values; removed paths are not authorities.
        result = {k: row[k] for k in ('run_id', 'case_id', 'arm', 'status', 'strict_success',
                  'metric_status', 'score_version', 'model_requested', 'runtime_metadata',
                  'known_tokens', 'unknown_calls', 'active_seconds', 'budget', 'selection',
                  'public_inputs', 'display', 'clarification_questions') if k in row}
        result.update({'source_origin': _origin(row), 'evaluation': evaluation,
                       'artifact': None, 'artifact_sha256': None,
                       'dialogue_capture': state.get('dialogue_capture', 'recorded'),
                       'calls': [call_summary(c) for c in calls],
                       'dialogue': [{k: e[k] for k in ('kind', 'payload', 'at') if k in e}
                                    for e in events if e['kind'] in DIALOGUE]})
        result['usage'] = state.get('usage')
        terminal = next((e['payload'] for e in reversed(events) if e['kind'] == 'terminal'), {})
        result['terminal_detail'] = terminal.get('detail', state.get('detail'))
        native = state.get('native', {}).get('result', {})
        if isinstance(native, dict):
            nested = native.get('result', native)
            if isinstance(nested, dict):
                result['runtime_outcome'] = {k: nested[k] for k in
                    ('status', 'error', 'error_code', 'reason_code', 'finish_reason') if k in nested}
        if result.get('active_seconds') is None:
            result['active_seconds'] = state.get('active_elapsed_s')
        if row.get('artifact'):
            source = safe_path(Path(row['artifact']))
            target = destination/'outputs'/row['case_id']/(row['arm']+'.ifc')
            if not source.is_file():
                raise ValueError('FORMAL_ARTIFACT_MISSING')
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = sha256(source)
            if target.exists():
                if digest != sha256(target):
                    raise ValueError('RESULT_ARTIFACT_EXISTS')
            else:
                shutil.copyfile(source, target)
            result['artifact'] = target.relative_to(destination).as_posix()
            result['artifact_sha256'] = digest
        result['reasoning_records'] = 0
        result['thinking_responses'] = 0
        if row['arm'] in {'A', 'B', 'D'}:
            for call in calls:
                returned = returned_messages(call)
                if returned['messages']:
                    reasoning.append({'run_id': row['run_id'], 'case_id': row['case_id'],
                        'arm': row['arm'], 'request_id': call['request_id'],
                        'stage': _decoded(call.get('metadata') or {}).get('stage'), **returned})
                    result['reasoning_records'] += 1
                    result['thinking_responses'] += bool(has_returned_thinking(returned['messages']))
        result['reasoning_status'] = 'returned' if result['thinking_responses'] else 'not_returned'
        exported.append(result)
    write_reasoning(destination/'reasoning.jsonl.gz', reasoning)
    value = {'schema_version': 'repair-comparison-compact-results/0.1', 'rows': exported,
             'reasoning_file': 'reasoning.jsonl.gz',
             'role': 'Selected real outcomes; submission and scored success are separate.'}
    write_json(destination/'latest-records.json', value)
    return value


def write_reasoning(path, records):
    with gzip.open(path, 'wt', encoding='utf8', newline='\n') as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False)+'\n')


def export_experiment(root, output):
    root = safe_path(Path(root))
    plan = read_json(root/'experiment.json')
    if plan.get('role') == 'Completed financial checkpoint; not runnable.':
        raise ValueError('FINANCIAL_CHECKPOINT_IS_NOT_RESULT_AUTHORITY')
    ledger_path = safe_path(root/'control.sqlite')
    if not ledger_path.is_file():
        raise ValueError('RESULT_LEDGER_MISSING')
    ledger = Ledger(ledger_path)
    rows = []
    for run_id in plan['order']:
        state = ledger.snapshot(run_id)
        rows.append({**state, 'artifact': (state.get('artifact') or {}).get('path'),
                     'ledger_root': str(root), 'metric_status': 'deferred', 'strict_success': None})
    return export_runs(rows, output)


def retire_accounting(root):
    """After export, retain stopped-task charges and stream flags, not response bodies.

    Does not remove workspaces or logs. The caller owns that explicit cleanup.
    The resulting checkpoint is financial authority only and cannot be resumed.
    """
    root = safe_path(Path(root))
    plan = read_json(root/'experiment.json')
    ledger = Ledger(root/'control.sqlite')
    before = [ledger.snapshot(run)['usage'] for run in plan['order']]
    states = [ledger.snapshot(run) for run in plan['order']]
    if any(s['status'] not in TERMINAL or s.get('activities') for s in states):
        raise ValueError('ACTIVE_ACCOUNTING_CANNOT_RETIRE')
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        with db:
            for run_id, encoded in db.execute('SELECT run_id,state FROM runs').fetchall():
                state = json.loads(encoded)
                state['native'], state['metadata'] = {}, {}
                if state.get('artifact'):
                    state['artifact'] = {'role': 'Retired financial reference',
                                         'sha256': state['artifact'].get('sha256')}
                db.execute('UPDATE runs SET state=? WHERE run_id=?', (json.dumps(state), run_id))
            for run_id, request_id, encoded in db.execute(
                    'SELECT run_id,request_id,response FROM calls').fetchall():
                response = _decoded(encoded) or {}
                flags = {k: response[k] for k in ('usage_complete', 'stream_complete') if k in response}
                db.execute('UPDATE calls SET response=? WHERE run_id=? AND request_id=?',
                           (json.dumps(flags), run_id, request_id))
            db.execute('DELETE FROM events')
        db.execute('VACUUM')
    if [ledger.snapshot(run)['usage'] for run in plan['order']] != before:
        raise ValueError('RETIRED_ACCOUNTING_CHANGED')
    plan['role'] = 'Completed financial checkpoint; not runnable.'
    write_json(root/'experiment.json', plan)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--selection', type=Path, help='Existing selected terminal rows; no score selection.')
    source.add_argument('--root', type=Path, help='Completed experiment ledger and experiment.json.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.selection:
        rows = read_json(args.selection)['rows']
        value = export_runs(rows, args.output)
    else:
        value = export_experiment(args.root, args.output)
    print(json.dumps({'event': 'results_exported', 'tasks': len(value['rows']),
                      'artifacts': sum(bool(r['artifact']) for r in value['rows'])}))


if __name__ == '__main__':
    main()
