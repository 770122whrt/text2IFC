"""Write or check the Phase 3 BIMNet scene-family split manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_text.splits import (  # noqa: E402
    DEFAULT_FAMILIES_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SEED,
    SplitManifestError,
    check_split_manifest,
    write_split_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--families", type=Path, default=DEFAULT_FAMILIES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    arguments = parser.parse_args()

    try:
        if arguments.write:
            payload = write_split_manifest(
                arguments.output,
                manifest_path=arguments.manifest,
                families_path=arguments.families,
                seed=arguments.seed,
            )
            mode = "write"
        else:
            payload = check_split_manifest(
                arguments.output,
                manifest_path=arguments.manifest,
                families_path=arguments.families,
                seed=arguments.seed,
            )
            mode = "check"
    except (OSError, SplitManifestError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "BIMNET_SPLIT_ERROR",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                },
                sort_keys=True,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "families": payload["counts"]["families"],
                "files": payload["counts"]["files"],
                "mode": mode,
                "output": arguments.output.as_posix(),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
