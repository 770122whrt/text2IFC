"""Phase 6.2-fix human-facing text2IFC REPL."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.agent.run_phase6_2_cli import load_env_file  # noqa: E402
from text2ifc_agent.clarification import DesignBriefInvoker  # noqa: E402
from text2ifc_agent.interactive_cli_flow import (  # noqa: E402
    make_openai_design_brief_invoker,
)
from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_agent.repl_chat import (  # noqa: E402
    InputFunc,
    configure_utf8_stdio,
    run_repl_chat,
)
from text2ifc_agent.session_store import SessionStore  # noqa: E402
from text2ifc_agent.trace_levels import DEFAULT_TRACE_LEVEL  # noqa: E402


DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.2-fix-repl"
)


def main(
    argv: list[str] | None = None,
    *,
    design_brief_invoker: DesignBriefInvoker | None = None,
    live_provider_factory: Callable[[], Any] | None = None,
    openai_client_factory: Callable[..., Any] | None = None,
    input_func: InputFunc | None = None,
    stdout: TextIO | None = None,
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--stop-after", choices=("design-brief", "ifc"), default="ifc")
    parser.add_argument(
        "--trace-level",
        choices=("compact", "debug", "full"),
        default=DEFAULT_TRACE_LEVEL,
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    active_stdout = stdout or sys.stdout
    terminal_metadata = configure_utf8_stdio(active_stdout)
    load_env_file(args.env_file)
    if not args.live:
        parser.print_help(file=active_stdout)
        return 2

    output_root = args.output_root
    db_path = args.db or (output_root / "sessions.sqlite")
    store = SessionStore.open(db_path, artifact_root=output_root)
    try:
        design_brief_invoker_factory = None
        if design_brief_invoker is None:
            config = load_openai_compatible_runtime_config(dict(os.environ))

            def design_brief_invoker_factory(run_dir: Path) -> DesignBriefInvoker:
                return make_openai_design_brief_invoker(
                    config=config,
                    run_dir=run_dir,
                    client_factory=openai_client_factory,
                )

        if live_provider_factory is None:
            live_provider_factory = _default_provider_factory(
                openai_client_factory=openai_client_factory
            )
        result = run_repl_chat(
            store=store,
            invoke_design_brief=design_brief_invoker,
            design_brief_invoker_factory=design_brief_invoker_factory,
            input_func=input_func,
            stdout=active_stdout,
            stop_after=args.stop_after,
            provider_factory=live_provider_factory,
            terminal_metadata=terminal_metadata,
            trace_level=args.trace_level,
        )
    finally:
        store.close()

    if args.debug:
        active_stdout.write(json.dumps(result.__dict__, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if result.status in {"ready", "compiled", "incomplete", "draft_required"} else 2


def _default_provider_factory(
    *,
    openai_client_factory: Callable[..., Any] | None,
) -> Callable[[], OpenAICompatibleLiveProvider]:
    def create_provider() -> OpenAICompatibleLiveProvider:
        return OpenAICompatibleLiveProvider(
            config=load_openai_compatible_runtime_config(dict(os.environ)),
            client_factory=openai_client_factory,
        )

    return create_provider


if __name__ == "__main__":
    raise SystemExit(main())
