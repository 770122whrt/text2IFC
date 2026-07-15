"""Query and export Phase 6.2 interactive CLI sessions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.session_store import SessionStore  # noqa: E402


DEFAULT_ROOT = ROOT / "dataset" / "processed" / "agent-demo" / "phase6.2-interactive-cli"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_ROOT / "sessions.sqlite")
    parser.add_argument("--output-root", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    for command in ("show", "turns", "events", "artifacts", "calls", "resume", "export"):
        child = subparsers.add_parser(command)
        child.add_argument("session")
    args = parser.parse_args(argv)
    root = args.output_root or args.db.parent
    store = SessionStore.open(args.db, artifact_root=root)
    try:
        if args.command == "list":
            _print_json([_session_summary(session) for session in store.list_sessions()])
            return 0
        if args.command == "show":
            _print_json(_session_summary(store.get_session(args.session)))
            return 0
        if args.command == "turns":
            _print_json([turn.__dict__ for turn in store.list_turns(args.session)])
            return 0
        if args.command == "events":
            _print_json([event.__dict__ for event in store.list_events(args.session)])
            return 0
        if args.command == "artifacts":
            _print_json(store.list_artifacts(args.session))
            return 0
        if args.command == "calls":
            _print_json(store.session_export_payload(args.session)["agent_calls"])
            return 0
        if args.command == "resume":
            session = store.get_session(args.session)
            _print_json(
                {
                    "session_id": session.session_id,
                    "session_hash": session.session_hash,
                    "resume_argument": session.session_hash,
                    "status": session.status,
                }
            )
            return 0
        if args.command == "export":
            export_path = store.export_session(args.session)
            _print_json({"export_path": str(export_path)})
            return 0
    finally:
        store.close()
    parser.error("unknown command")
    return 2


def _session_summary(session) -> dict[str, str]:
    return {
        "session_id": session.session_id,
        "session_hash": session.session_hash,
        "original_input": session.original_input,
        "status": session.status,
        "run_dir": str(session.run_dir),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
