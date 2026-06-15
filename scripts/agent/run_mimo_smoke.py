"""Check or smoke-test the optional Mimo Agent provider."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.providers import (  # noqa: E402
    MimoAgentProvider,
    ProviderOutputError,
    load_mimo_config_from_env,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--prompt-only", action="store_true")
    arguments = parser.parse_args()

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
