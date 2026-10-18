"""Two-case development rounds. Scripts inspect outputs; operators see summaries.

This is a compatibility gate, not a benchmark success-rate estimator. Selection
is saved before evaluator controls or model calls; revealed cases stay revealed.
"""
from __future__ import annotations

import argparse
from contextlib import closing, redirect_stdout, redirect_stderr
import csv
import io
import json
from pathlib import Path
import random
import sqlite3

from . import batch_workflow as batch
from .contracts import read_json, write_json, safe_path, sha256


def choose_fresh(rows, sources, *, excluded, seed):
    excluded_sources = {sources[c] for c in excluded if c in sources}
    pool = sorted((r for r in rows if r['level'] == 'S1' and
                   sources[r['case_id']] not in excluded_sources), key=lambda r: r['case_id'])
    random.Random(seed).shuffle(pool)
    chosen = []
    for kind in ('geometry', 'property'):
        row = next((r for r in pool if r['task_kind'] == kind and
                    sources[r['case_id']] not in {sources[c] for c in chosen}), None)
        if row is None:
            raise ValueError('FRESH_TWO_CASES_UNAVAILABLE')
        chosen.append(row['case_id'])
    return chosen


def decision(rows, *, kind):
    passed = sum(r['terminal'] == 'submitted' and r['format'] is True
                 and r['independent'] == 'passed' for r in rows)
    both = len(rows) == 2 and len({r['case_id'] for r in rows}) == 2 and passed == 2
    return {'passed': passed, 'total': len(rows), 'round_passed': both,
            'batch_eligible': kind == 'fresh' and both}


def _record(root):
    value = read_json(safe_path(Path(root)/'round.json'))
    if value['selection_sha256'] != batch._digest(value['selection']):
        raise ValueError('FROZEN_ROUND_SELECTION_CHANGED')
    return value


def prepare(root, dataset, *, kind, arm, case_ids=None, excluded=(), seed=20261012,
            providers=None, existing_controls=None, request_convention=None):
    from .host_evaluator import prepare_evaluator
    root, dataset = safe_path(Path(root)), safe_path(Path(dataset))
    if root.exists():
        raise ValueError('ROUND_EXISTS_USE_RUN_OR_CHECK')
    if arm not in {'B', 'E'} or kind not in {'regression', 'fresh'}:
        raise ValueError('INVALID_DEVELOPMENT_ROUND')
    with (dataset/'public/inputs.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    export = read_json(dataset/'private/evaluation/export.json')
    sources = {p['case_id']: p['source_id'] for p in export['pair_provenance']}
    if kind == 'fresh':
        if case_ids is not None or not excluded:
            raise ValueError('FRESH_REQUIRES_EXCLUSIONS_AND_RANDOM_SELECTION')
        case_ids = choose_fresh(rows, sources, excluded=excluded, seed=seed)
    if not case_ids or len(case_ids) != 2 or len(set(case_ids)) != 2 or not set(case_ids) <= set(sources):
        raise ValueError('TWO_KNOWN_DISTINCT_CASES_REQUIRED')
    selection = {'kind': kind, 'arm': arm, 'case_ids': list(case_ids), 'seed': seed,
                 'excluded': sorted(set(excluded)), 'dataset': str(dataset),
                 'source_groups': [sources[c] for c in case_ids],
                 'public_csv_sha256': sha256(dataset/'public/inputs.csv')}
    if request_convention is not None:
        selection['request_convention'] = request_convention
    root.mkdir(parents=True)
    record = {'selection': selection, 'selection_sha256': batch._digest(selection)}
    write_json(root/'round.json', record)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        checked = prepare_evaluator(dataset, list(case_ids), root/'evaluator',
                                    existing_controls=existing_controls)
    record['evaluator'] = checked
    write_json(root/'round.json', record)
    if checked.get('evaluator_admitted') is not True:
        raise ValueError('ROUND_EVALUATOR_NOT_ADMITTED')
    batch.prepare(root/'batch', dataset/'public', input_format='pairs', scope='full',
                  groups=[arm], case_ids=list(case_ids), concurrency=2, providers=providers,
                  delivery_receipt=dataset/'private/finalization/summary.json',
                  request_convention=request_convention)
    return {'event': 'summary', 'state': 'prepared', 'kind': kind, 'arm': arm,
            'case_ids': case_ids, 'root': str(root), 'evaluator_admitted': True}


def check(root):
    from .host_evaluator import evaluate_result
    root = safe_path(Path(root))
    record = _record(root)
    selection = record['selection']
    folder = root/'batch'
    config = batch.plan(folder)['configuration']
    if (set(config['case_ids']) != set(selection['case_ids']) or
            any(config['case_groups'][c] != [selection['arm']] for c in selection['case_ids'])):
        raise ValueError('ROUND_BATCH_SELECTION_CHANGED')
    status = batch.brief_status(folder)
    complete = status['completed'] == status['total']
    if not (folder/'control.sqlite').is_file():
        return {'event': 'summary', 'state': 'pending', **status, 'batch_eligible': False}
    rows = []
    with closing(sqlite3.connect((folder/'control.sqlite').as_uri()+'?mode=ro', uri=True)) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        exports = ({rid: json.loads(raw) for rid, raw in db.execute('SELECT run_id,summary FROM batch_exports')}
                   if 'batch_exports' in tables else {})
        diagnostics = {rid: (terminal, reason, json.loads(scene) if scene else {}, question)
                       for rid, terminal, reason, scene, question in db.execute(
            "SELECT run_id,json_extract(state,'$.status'),json_extract(state,'$.native.result.reason_code'),"
            "json_extract(state,'$.native.scene_diagnostics'),"
            "json_extract(state,'$.question.binding.native_question.question') FROM runs")}
    for case_id in selection['case_ids']:
        run_id = case_id+'-'+selection['arm']
        exported = exports.get(run_id)
        if exported is None and complete:
            raise ValueError('ROUND_EXPORT_MISSING')
        terminal, reason, scene, question = diagnostics.get(run_id, ('ready', None, {}, None))
        row = {'case_id': case_id, 'group': selection['arm'],
               'terminal': exported['status'] if exported else terminal,
               'format': exported['common_format_validation']['passed'] if exported else None,
               'independent': 'not_evaluated',
               'reason': reason, 'issue_codes': sorted({c for r in scene.get('rounds', [])
                                                       for c in r.get('issue_codes', [])})[:12]}
        if terminal == 'awaiting_user' and question:
            row['clarification'] = str(question)[:400]
        if row['terminal'] == 'submitted' and exported:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                checked = evaluate_result(root/'evaluator', case_id,
                                          folder/'results'/case_id/selection['arm']/'repaired.ifc')
            if checked.get('result_sha256') != exported.get('artifact_sha256'):
                raise ValueError('EXPORTED_ARTIFACT_CHANGED')
            row.update(independent=checked['status'], check_codes=checked['codes'],
                       result_sha256=checked.get('result_sha256'))
        rows.append(row)
    outcome = {'event': 'summary', 'state': 'complete' if complete else status['state'], 'kind': selection['kind'],
               'arm': selection['arm'], **decision(rows, kind=selection['kind']), 'cases': rows,
               'known_tokens': status['known_tokens'], 'unknown_calls': status['unknown_calls']}
    if not complete:
        outcome['batch_eligible'] = False
        record['checkpoint'] = outcome
        write_json(root/'round.json', record)
        return outcome
    if record.get('outcome') is not None and record['outcome'] != outcome:
        raise ValueError('ROUND_OUTCOME_CHANGED')
    record['outcome'] = outcome
    write_json(root/'round.json', record)
    return outcome


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'run', 'check'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--dataset', type=Path)
    parser.add_argument('--kind', choices=['regression', 'fresh'], default='regression')
    parser.add_argument('--arm', choices=['B', 'E'], default='B')
    parser.add_argument('--case-ids', nargs='+')
    parser.add_argument('--exclude-case-ids', nargs='*', default=[])
    parser.add_argument('--exclude-rounds', type=Path, nargs='*', default=[])
    parser.add_argument('--seed', type=int, default=20261012)
    parser.add_argument('--providers', type=Path)
    parser.add_argument('--existing-controls', type=Path)
    parser.add_argument('--request-convention', choices=['existing-ifc-property-units/1.0'])
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            excluded = list(args.exclude_case_ids)
            for prior in args.exclude_rounds:
                excluded.extend(_record(prior)['selection']['case_ids'])
            result = prepare(args.root, args.dataset, kind=args.kind, arm=args.arm,
                case_ids=args.case_ids, excluded=excluded, seed=args.seed,
                providers=read_json(args.providers) if args.providers else None,
                existing_controls=read_json(args.existing_controls) if args.existing_controls else None,
                request_convention=args.request_convention)
        else:
            if args.command == 'run':
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    batch.run(args.root/'batch')
            result = check(args.root)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if args.command == 'prepare' or result.get('round_passed') else 3
    except Exception as error:
        print(json.dumps({'event': 'attention', 'reason': type(error).__name__+': '+str(error)[:200]}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
