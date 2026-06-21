"""Write or verify the deterministic Phase 6 data manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_dataset.phase6_manifest import (  # noqa: E402
    DEFAULT_OUTPUT,
    Phase6ManifestError,
    check_phase6_manifest,
    write_phase6_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        if args.write:
            manifest = write_phase6_manifest(args.output)
            mode = "write"
        else:
            manifest = check_phase6_manifest(args.output)
            mode = "check"
    except (OSError, Phase6ManifestError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "PHASE6_MANIFEST_ERROR",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "counts": manifest["counts"],
                "mode": mode,
                "output": str(args.output),
                "status": "ok",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
