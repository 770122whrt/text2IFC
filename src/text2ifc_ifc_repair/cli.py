"""Thin rendering and argument adapter for :class:`RepairAPI`."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TextIO

from .api import RepairAPI
from .run_models import RunResult, canonical_json


EXIT_CODES = {
    "succeeded": 0,
    "clarification_required": 2,
    "invalid_input": 3,
    "unsupported": 3,
    "provider_failed": 4,
    "audit_failed": 5,
    "application_failed": 5,
    "not_publishable": 6,
    "cancelled": 8,
}


def main(
    argv: Sequence[str] | None = None,
    *,
    api_factory: Callable[[Path], Any] | None = None,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
) -> int:
    parser = _parser()
    out, err, source_in = output_stream or sys.stdout, error_stream or sys.stderr, input_stream or sys.stdin
    try:
        args = parser.parse_args(argv)
        factory = api_factory or _default_api_factory
        api = factory(args.output_root)
        if args.command == "start":
            result = api.start(args.source, args.request, run_id=args.run_id)
        elif args.command == "continue":
            result = api.continue_with_answer(
                args.run_id, _answer(args.answer),
                clarification_id=args.clarification_id,
                expected_state_version=args.expected_state_version,
            )
        else:
            result = api.read_result(args.run_id)
        rounds = 0
        while result.status == "clarification_required" and not args.non_interactive and not args.json and not args.quiet:
            if rounds >= 8:
                raise ValueError("CLARIFICATION_ROUND_LIMIT")
            _render_clarification(result, out)
            answer = _read_answer(result, source_in)
            clarification = result.clarification
            assert clarification is not None
            result = api.continue_with_answer(
                result.run_id, answer,
                clarification_id=clarification.clarification_id,
                expected_state_version=clarification.state_version,
            )
            rounds += 1
        _render(result, json_mode=args.json, quiet=args.quiet, out=out)
        return EXIT_CODES.get(result.status, 7)
    except SystemExit:
        raise
    except Exception as error:
        code = _error_code(error)
        err.write(canonical_json({"schema_version": "text2ifc/ifc-repair-cli-error/0.1", "status": "state_error", "reason_code": code}) + "\n")
        return 7


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bimnet-repair")
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("source", type=Path)
    start.add_argument("--request", required=True)
    start.add_argument("--run-id")
    cont = sub.add_parser("continue")
    cont.add_argument("run_id")
    cont.add_argument("--answer", required=True)
    cont.add_argument("--clarification-id", required=True)
    cont.add_argument("--expected-state-version", required=True, type=int)
    result = sub.add_parser("result")
    result.add_argument("run_id")
    for command in (start, cont, result):
        command.add_argument("--output-root", type=Path, required=True)
        modes = command.add_mutually_exclusive_group()
        modes.add_argument("--json", action="store_true")
        modes.add_argument("--quiet", action="store_true")
        command.add_argument("--non-interactive", action="store_true")
    return parser


def _default_api_factory(output_root: Path) -> RepairAPI:
    return RepairAPI.from_environment(output_root)


def _answer(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("CLARIFICATION_ANSWER_INVALID")
    return parsed


def _read_answer(result: RunResult, stream: TextIO) -> dict[str, Any]:
    clarification = result.clarification
    assert clarification is not None
    raw = stream.readline()
    if raw == "":
        return {"kind": "eof"}
    value = raw.strip()
    if value.casefold() in {"取消", "cancel", "q", "quit"}:
        return {"kind": "cancel"}
    if value.isdigit():
        index = int(value) - 1
        if 0 <= index < len(clarification.candidates):
            token = clarification.candidates[index].token
            if "authorize_prototype" in clarification.answer_modes:
                return {"kind": "authorize_prototype", "candidate_token": token, "authorized": True}
            return {"kind": "select_candidate", "candidate_token": token}
        raise ValueError("CLARIFICATION_ANSWER_INVALID")
    if "add_detail" in clarification.answer_modes and value:
        return {"kind": "add_detail", "detail": value}
    raise ValueError("CLARIFICATION_ANSWER_INVALID")


def _render_clarification(result: RunResult, out: TextIO) -> None:
    clarification = result.clarification
    assert clarification is not None
    out.write(f"需要澄清: {clarification.question}\n")
    for index, item in enumerate(clarification.candidates, start=1):
        evidence = ", ".join(item.evidence)
        out.write(f"{index}. {item.ifc_class} {item.name or '-'} | GUID {item.public_id} | 楼层 {item.storey or '-'} | 位置 {item.position or '-'} | 证据 {evidence}\n")
    out.write("请输入候选编号、补充说明或‘取消’: ")


def _render(result: RunResult, *, json_mode: bool, quiet: bool, out: TextIO) -> None:
    if quiet:
        return
    if json_mode:
        out.write(canonical_json(result.to_dict()) + "\n")
        return
    out.write(f"状态: {result.status}\n")
    out.write(f"运行 ID: {result.run_id}\n")
    if result.reason_code:
        out.write(f"原因: {result.reason_code}\n")
    for name, path in sorted(result.artifacts.items()):
        out.write(f"{name}: {path}\n")
    out.write(f"运行目录: {result.run_directory}\n")


def _error_code(error: Exception) -> str:
    code = getattr(error, "code", None)
    if code:
        return str(code)[:128]
    match = re.search(r"[A-Z][A-Z0-9_]{2,127}", str(error))
    return match.group(0) if match else "REPAIR_CLI_ERROR"


__all__ = ["EXIT_CODES", "main"]
