"""Prepare, inspect, decide, and export a component review without an LLM call."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'.deps/python312')]
from text2ifc_agent.session_store import SessionStore
from text2ifc_ifc2text.compact_pipeline import prepare_compact
from text2ifc_ifc2text.component_review import start_review, review_state, decide_review, approved_description


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('prepare'); prepare.add_argument('--source', required=True); prepare.add_argument('--output', required=True)
    prepare.add_argument('--description-version', choices=['1.1', '1.2'], default='1.1')
    for command in ('show', 'decide', 'export'):
        p = sub.add_parser(command); p.add_argument('--database', required=True); p.add_argument('--session', required=True)
        if command == 'decide':
            p.add_argument('--review-sha256', required=True)
            p.add_argument('--action', choices=['pause', 'exclude_and_continue'], required=True)
            p.add_argument('--exclude', nargs='*', default=[])
        if command == 'export':p.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        root = Path(args.output); root.mkdir(parents=True, exist_ok=False)
        prepare_compact(args.source, root/'description', description_version=args.description_version)
        facts = json.loads((root/'description/source-facts.json').read_text(encoding='utf-8'))
        with SessionStore.open(root/'review.sqlite', artifact_root=root) as store:
            result = start_review(store=store, facts=facts)
        _write(root/'review.json', result)
    else:
        database = Path(args.database)
        if not database.is_file():raise ValueError('COMPONENT_REVIEW_REQUIRED')
        with SessionStore.open(database) as store:
            if args.command == 'show':
                result = review_state(store=store, session_id=args.session)
            elif args.command == 'decide':
                result = decide_review(store=store, session_id=args.session,
                    review_sha256=args.review_sha256, action=args.action, excluded_labels=args.exclude)
            else:
                packet = approved_description(store=store, session_id=args.session)
                root = Path(args.output); root.mkdir(parents=True, exist_ok=False)
                (root/'design-description.md').write_text(packet['description'], encoding='utf-8')
                _write(root/'source-facts.private.json', packet['facts'])
                _write(root/'refusals.json', packet['refusals'])
                result = {k:v for k,v in packet.items() if k not in {'facts','description','refusals'}}
                result['component_review'] = {'database':str(database.resolve()), 'session_id':args.session,
                    'review_sha256':packet['review_sha256']}
                _write(root/'export.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':raise SystemExit(main())
