"""Phase 6.2 interactive CLI session shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .session_store import SessionStore


@dataclass(frozen=True)
class InteractiveSessionResult:
    session_id: str
    session_hash: str
    status: str


def run_interactive_session(
    *,
    store: SessionStore,
    input_lines: Iterable[str],
    dry_run: bool,
    prompt: str | None = None,
    resume: str | None = None,
) -> InteractiveSessionResult:
    lines = iter(input_lines)
    if resume:
        session = store.get_session(resume)
    else:
        original_input = prompt if prompt is not None else _next_nonempty(lines)
        session = store.create_session(original_input=original_input)
        store.append_event(
            session.session_id,
            event_type="cli.session_started",
            payload={"dry_run": dry_run},
        )

    for raw_line in lines:
        command = raw_line.strip()
        if not command:
            continue
        if command == "help":
            store.append_event(session.session_id, event_type="cli.help", payload={})
        elif command == "status":
            current = store.get_session(session.session_id)
            store.append_event(
                session.session_id,
                event_type="cli.status",
                payload={"status": current.status},
            )
        elif command == "quit":
            store.append_event(session.session_id, event_type="cli.quit", payload={})
            session = store.mark_session_status(session.session_id, "incomplete")
            break
        else:
            store.append_turn(session.session_id, role="user", text=command)
            store.append_event(
                session.session_id,
                event_type="cli.user_input",
                payload={"text_length": len(command)},
            )

    if dry_run and store.get_session(session.session_id).status == "open":
        session = store.mark_session_status(session.session_id, "incomplete")
    return InteractiveSessionResult(
        session_id=session.session_id,
        session_hash=session.session_hash,
        status=session.status,
    )


def _next_nonempty(lines: Iterable[str]) -> str:
    for raw_line in lines:
        line = raw_line.strip()
        if line:
            return line
    raise ValueError("interactive session requires an initial prompt")
