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
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import (  # noqa: E402
    build_compatibility_report,
    load_openai_compatible_config,
)


DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "phase6.2-openai-compat"
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
        if key and key not in os.environ:
            os.environ[key] = value


def main(
    argv: list[str] | None = None,
    *,
    compatibility_runner: CompatibilityRunner | None = None,
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-openai-compat", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args(argv)
    load_env_file(arguments.env_file)

    if arguments.check_openai_compat:
        return _check_openai_compat(
            output_dir=arguments.output_dir,
            compatibility_runner=compatibility_runner,
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
            "provider": "mimo-openai-compatible",
            "decision": "blocked",
            "implementation_route": "blocked",
            "blocker": "missing_openai_compatible_config",
            "config": config,
        }
        _write_reports(output_dir=output_dir, report=report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2

    runner = compatibility_runner or _not_implemented_live_runner
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


def _not_implemented_live_runner(config: dict[str, Any]) -> dict[str, Any]:
    del config
    return build_compatibility_report(
        openai_sdk={
            "status": "blocked",
            "evidence_class": "sdk_smoke",
            "blocker": "live_openai_compat_runner_not_implemented",
        },
        agents_sdk={
            "status": "blocked",
            "evidence_class": "sdk_smoke",
            "blocker": "live_agents_sdk_runner_not_implemented",
        },
        responses_api={
            "status": "not_checked",
            "evidence_class": "sdk_smoke",
        },
    )


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
