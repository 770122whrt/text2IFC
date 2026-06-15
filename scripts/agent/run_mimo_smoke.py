"""Check or smoke-test the optional Mimo Agent provider."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.providers import (  # noqa: E402
    MimoAgentProvider,
    ProviderOutputError,
    load_mimo_config_from_env,
)


DEFAULT_ENV_FILE = ROOT / ".env"


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


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--prompt-only", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    arguments = parser.parse_args()
    load_env_file(arguments.env_file)

    if arguments.check_config:
        print(json.dumps(load_mimo_config_from_env(), sort_keys=True))
        return 0
    if arguments.prompt_only:
        config = load_mimo_config_from_env()
        if not config["configured"]:
            print(
                json.dumps(
                    {
                        "provider": "mimo",
                        "status": "skipped",
                        "configured": False,
                        "missing": config["missing"],
                    },
                    sort_keys=True,
                )
            )
            return 2
        try:
            output = MimoAgentProvider().generate_candidate(
                session_id="mimo-smoke",
                prompt='Return exactly this JSON object: {"ok": true}',
                schema={},
                state={},
            )
        except ProviderOutputError as exc:
            print(
                json.dumps(
                    {
                        "provider": "mimo",
                        "status": "failed",
                        "message": str(exc),
                    },
                    sort_keys=True,
                )
            )
            return 2
        status, _, diagnostics = output.parse_json()
        print(
            json.dumps(
                {
                    "provider": "mimo",
                    "status": status,
                    "diagnostics": diagnostics,
                },
                sort_keys=True,
            )
        )
        return 0 if status == "ok" else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
