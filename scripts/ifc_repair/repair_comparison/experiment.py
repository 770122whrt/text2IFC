"""Offline experiment CLI; deliberately has no real-Provider entry point."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
for path in (REPO, REPO / 'src'):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner, ReplayProvider
from scripts.ifc_repair.repair_comparison.ledger import Ledger


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    commands = p.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create')
    create.add_argument('--public', type=Path, required=True)
    create.add_argument('--case-id', required=True)
    create.add_argument('--arm', choices=['A', 'B', 'C'], required=True)
    create.add_argument('--budget', type=Path, required=True)
    for command in ('status', 'run', 'answer', 'score'):
        sub = commands.add_parser(command)
        sub.add_argument('run_id')
        if command == 'run':
            sub.add_argument('--replay', type=Path, required=True)
            sub.add_argument('--reservation', type=int, required=True)
        if command == 'answer':
            sub.add_argument('--question-id', required=True)
            sub.add_argument('--text', required=True)
            sub.add_argument('--event-id', required=True)
            sub.add_argument('--native-answer', type=Path)
            sub.add_argument('--requested-fact', action='append', default=[])
            sub.add_argument('--answered-fact', action='append', default=[])
        if command == 'score':
            sub.add_argument('--case', type=Path, required=True)
    return p


def execute(args):
    if args.command == 'create':
        runner = DirectRunner.create(args.public, args.root, case_id=args.case_id, arm=args.arm, budget=read_json(args.budget))
        return runner.ledger.snapshot(runner.run_id)
    ledger_path = args.root / 'control.sqlite'
    if not ledger_path.is_file():
        raise ValueError('EXPERIMENT_NOT_FOUND')
    ledger = Ledger(ledger_path)
    state = ledger.snapshot(args.run_id)
    if args.command == 'status':
        return state
    if args.command == 'score':
        from scripts.ifc_repair.repair_comparison.scoring import score
        spec = read_json(args.case / 'private/task.json')
        if spec['case_id'] != state['case_id'] or spec['damaged_sha256'] != state['metadata']['input_sha256']:
            raise ValueError('SCORING_CASE_INPUT_MISMATCH')
        path = Path(state['artifact']['path']) if state['artifact'] else None
        if path and sha256(path) != state['artifact']['sha256']:
            raise ValueError('SUBMITTED_ARTIFACT_CHANGED')
        report = score(args.case, path, terminal=state['status'], events=ledger.events(args.run_id))
        report['usage'] = state['usage']
        target = args.root / 'evaluation' / args.run_id
        target.mkdir(parents=True, exist_ok=True)
        write_json(target / 'score.json', report)
        return report
    if state['arm'] == 'B':
        from scripts.ifc_repair.repair_comparison.ours_adapter import OursAdapter, NativeReplayProvider
        runner = OursAdapter(args.root, args.run_id)
        if args.command == 'run':
            return runner.run(NativeReplayProvider(read_json(args.replay)), reservation=args.reservation)
    else:
        runner = DirectRunner(args.root, args.run_id)
        if args.command == 'run':
            return runner.run(ReplayProvider(read_json(args.replay)), reservation=args.reservation)
    if state['status'] != 'awaiting_user' or state['question']['question_id'] != args.question_id:
        raise ValueError('QUESTION_BINDING_STALE')
    common = {'text': args.text, 'event_id': args.event_id,
              'requested_fact_ids': args.requested_fact, 'answered_fact_ids': args.answered_fact}
    if state['arm'] == 'B':
        if args.native_answer is None:
            raise ValueError('NATIVE_ANSWER_REQUIRED')
        runner.answer(native_answer=read_json(args.native_answer), **common)
    else:
        if args.native_answer is not None:
            raise ValueError('NATIVE_ANSWER_ONLY_FOR_B')
        ledger.answer(args.run_id, question_id=args.question_id, **common)
    return ledger.snapshot(args.run_id)


def main():
    try:
        result = execute(parser().parse_args())
    except (ValueError, KeyError, OSError) as error:
        print(json.dumps({'error': type(error).__name__, 'detail': str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
