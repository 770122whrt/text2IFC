"""Run the frozen offline case or a configured DeepSeek UAT."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from collections.abc import Sequence

from text2ifc_agent.openai_compat import (
    OpenAICompatibleLiveProvider,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.workflow import (
    LARGE_BUILDING_SHA256,
    run_live_window_repair_case,
    run_offline_window_repair_case,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    ROOT
    / "dataset"
    / "external"
    / "bim-whale-ifc-samples"
    / "LargeBuilding"
    / "IFC"
    / "LargeBuilding.ifc"
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--mode", choices=("fake", "live"), default="fake")
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--case-id", default="large-building-window-repair-001")
    parser.add_argument("--wall-id", default="1F6umJ5H50aeL3A1As_wTm")
    parser.add_argument("--opening-id", default="2cXV28XOjE6f6irhW0CO4t")
    parser.add_argument("--window-id", default="2cXV28XOjE6f6irgi0CO4t")
    parser.add_argument("--expected-source-sha256", default=LARGE_BUILDING_SHA256)
    arguments = parser.parse_args(argv)
    environment = _environment_from_file(arguments.env_file)
    if arguments.check_config:
        print(
            json.dumps(
                load_openai_compatible_config(environment),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.output is None:
        parser.error("output is required unless --check-config is used")
    common = {
        "source_path": arguments.source,
        "output_dir": arguments.output,
        "case_id": arguments.case_id,
        "wall_global_id": arguments.wall_id,
        "opening_global_id": arguments.opening_id,
        "window_global_id": arguments.window_id,
        "expected_source_sha256": arguments.expected_source_sha256,
    }
    if arguments.mode == "live":
        config = load_openai_compatible_runtime_config(environment)
        result = run_live_window_repair_case(
            provider=OpenAICompatibleLiveProvider(config=config), **common
        )
    else:
        result = run_offline_window_repair_case(**common)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["complete_repair_success"] else 1


def _environment_from_file(path: Path) -> dict[str, str]:
    """Merge one dotenv file without overriding process environment values."""

    environment = dict(os.environ)
    if not path.is_file():
        return environment
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            environment.setdefault(key, value)
    return environment


if __name__ == "__main__":
    raise SystemExit(main())
