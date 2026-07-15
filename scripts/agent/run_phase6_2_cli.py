"""Phase 6.2 interactive CLI entrypoint.

Wave 0 currently implements only the OpenAI-compatible compatibility check.
Later waves add the interactive session shell and live multi-agent workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, TextIO

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
    run_phase6_2_compatibility_check,
)
from text2ifc_agent.clarification import DesignBriefInvoker  # noqa: E402
from text2ifc_agent.interactive_cli_flow import (  # noqa: E402
    make_openai_design_brief_invoker,
    run_design_brief_clarification_loop,
    run_ready_session_to_ifc,
)
from text2ifc_agent.interactive_session import run_interactive_session  # noqa: E402
from text2ifc_agent.session_store import SessionStore  # noqa: E402


DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "phase6.2-openai-compat"
)
DEFAULT_INTERACTIVE_ROOT = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "phase6.2-interactive-cli"
)


CompatibilityRunner = Callable[[dict[str, Any]], dict[str, Any]]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _unquote(value.strip())
        if key:
            os.environ[key] = value


def main(
    argv: list[str] | None = None,
    *,
    compatibility_runner: CompatibilityRunner | None = None,
    design_brief_invoker: DesignBriefInvoker | None = None,
    openai_client_factory: Callable[..., Any] | None = None,
    live_provider_factory: Callable[[], Any] | None = None,
    stdin: TextIO | Iterable[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-openai-compat", action="store_true")
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_INTERACTIVE_ROOT)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--scripted-stdin", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--stop-after", choices=("design-brief", "ifc"))
    parser.add_argument("--resume")
    arguments = parser.parse_args(argv)
    load_env_file(arguments.env_file)

    if arguments.check_config:
        print(json.dumps(load_openai_compatible_config(dict(os.environ)), ensure_ascii=False, sort_keys=True))
        return 0
    if arguments.check_openai_compat:
        return _check_openai_compat(
            output_dir=arguments.output_dir,
            compatibility_runner=compatibility_runner,
        )
    if (
        arguments.dry_run
        or arguments.live
        or arguments.prompt
        or arguments.scripted_stdin
        or arguments.resume
    ):
        return _run_interactive_cli(
            arguments,
            design_brief_invoker=design_brief_invoker,
            openai_client_factory=openai_client_factory,
            live_provider_factory=live_provider_factory,
            stdin=stdin or sys.stdin,
        )
    parser.print_help()
    return 2


def _check_openai_compat(
    *,
    output_dir: Path,
    compatibility_runner: CompatibilityRunner | None,
) -> int:
    config = load_openai_compatible_config(dict(os.environ))
    output_dir.mkdir(parents=True, exist_ok=True)
    if not config["configured"]:
        report = {
            "phase": "6.2",
            "provider": config["provider"],
            "decision": "blocked",
            "implementation_route": "blocked",
            "blocker": "missing_openai_compatible_config",
            "config": config,
        }
        _write_reports(output_dir=output_dir, report=report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2

    runner = compatibility_runner or _live_compatibility_runner
    report = runner(config)
    _write_reports(output_dir=output_dir, report=report)
    summary = {
        "phase": report.get("phase"),
        "provider": report.get("provider"),
        "decision": report.get("decision"),
        "implementation_route": report.get("implementation_route"),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("decision") != "blocked" else 2


def _live_compatibility_runner(config: dict[str, Any]) -> dict[str, Any]:
    del config
    return run_phase6_2_compatibility_check(dict(os.environ))


def _run_interactive_cli(
    arguments: argparse.Namespace,
    *,
    design_brief_invoker: DesignBriefInvoker | None,
    openai_client_factory: Callable[..., Any] | None,
    live_provider_factory: Callable[[], Any] | None,
    stdin: TextIO | Iterable[str],
) -> int:
    output_root = arguments.output_root
    db_path = arguments.db or (output_root / "sessions.sqlite")
    input_lines = (
        []
        if arguments.resume and arguments.scripted_stdin is None and arguments.prompt is None
        else _load_input_lines(arguments.scripted_stdin, stdin=stdin)
    )
    store = SessionStore.open(db_path, artifact_root=output_root)
    try:
        if arguments.live and arguments.stop_after in {"design-brief", "ifc"}:
            if arguments.resume:
                session = store.get_session(arguments.resume)
            else:
                initial_prompt = arguments.prompt or _initial_user_prompt(input_lines)
                session = store.create_session(original_input=initial_prompt)
            if (
                arguments.stop_after == "ifc"
                and arguments.resume
                and session.status == "ready"
            ):
                result = run_ready_session_to_ifc(
                    store=store,
                    session=session.session_hash,
                    provider_factory=live_provider_factory
                    or _default_openai_live_provider_factory(
                        openai_client_factory=openai_client_factory
                    ),
                )
            else:
                if design_brief_invoker is None:
                    design_brief_invoker = make_openai_design_brief_invoker(
                        config=load_openai_compatible_runtime_config(dict(os.environ)),
                        run_dir=session.run_dir,
                        client_factory=openai_client_factory,
                    )
                result = run_design_brief_clarification_loop(
                    store=store,
                    session=session.session_hash,
                    invoke_design_brief=design_brief_invoker,
                    user_answers=_remaining_user_answers(input_lines, arguments.prompt),
                )
            if arguments.stop_after == "ifc" and result.status == "ready":
                result = run_ready_session_to_ifc(
                    store=store,
                    session=session.session_hash,
                    provider_factory=live_provider_factory
                    or _default_openai_live_provider_factory(
                        openai_client_factory=openai_client_factory
                    ),
                )
        else:
            result = run_interactive_session(
                store=store,
                input_lines=input_lines,
                dry_run=arguments.dry_run,
                prompt=arguments.prompt,
                resume=arguments.resume,
            )
    finally:
        store.close()
    print(json.dumps(result.__dict__, ensure_ascii=False, sort_keys=True))
    return 0 if getattr(result, "status", None) in {"ready", "compiled", "open", "incomplete"} else 2


def _default_openai_live_provider_factory(
    *,
    openai_client_factory: Callable[..., Any] | None,
) -> Callable[[], Any]:
    def create_provider() -> OpenAICompatibleLiveProvider:
        return OpenAICompatibleLiveProvider(
            config=load_openai_compatible_runtime_config(dict(os.environ)),
            client_factory=openai_client_factory,
        )

    return create_provider


def _load_input_lines(path: Path | None, *, stdin: TextIO | Iterable[str]) -> Iterable[str]:
    if path is not None:
        return iter(path.read_text(encoding="utf-8").splitlines())
    return (line.rstrip("\r\n") for line in stdin)


def _remaining_user_answers(input_lines: Iterable[str], prompt: str | None) -> Iterable[str]:
    if prompt is not None:
        return [line for line in input_lines if line.strip()]
    return (line for line in input_lines if line.strip())


def _initial_user_prompt(input_lines: list[str]) -> str:
    for line in input_lines:
        if line.strip():
            return line.strip()
    raise ValueError("Phase 6.2 live Design Brief requires an initial user prompt")


def _write_reports(*, output_dir: Path, report: dict[str, Any]) -> None:
    _write_json(output_dir / "compatibility-report.json", report)
    _write_markdown(output_dir / "report.md", report)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.2 OpenAI Compatibility Report",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Implementation route: `{report.get('implementation_route')}`",
        f"- Provider: `{report.get('provider')}`",
    ]
    if report.get("blocker"):
        lines.append(f"- Blocker: `{report.get('blocker')}`")
    for section in ("openai_sdk", "agents_sdk", "responses_api"):
        if section in report:
            lines.extend(
                [
                    "",
                    f"## {section}",
                    "",
                    "```json",
                    json.dumps(report[section], ensure_ascii=False, indent=2, sort_keys=True),
                    "```",
                ]
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
