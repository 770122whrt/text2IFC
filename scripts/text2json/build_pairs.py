"""Write or check deterministic Phase 3 Text-to-BIM-JSON pairs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_text.pairs import (  # noqa: E402
    DEFAULT_GOLD_MANIFEST_PATH,
    DEFAULT_OUTPUT_DIR,
    PairGenerationError,
    check_pair_artifacts,
    write_pair_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--gold-manifest", type=Path, default=DEFAULT_GOLD_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()

    try:
        if arguments.write:
            manifest = write_pair_artifacts(
                gold_manifest_path=arguments.gold_manifest,
                output_dir=arguments.output_dir,
            )
            mode = "write"
        else:
            manifest = check_pair_artifacts(
                gold_manifest_path=arguments.gold_manifest,
                output_dir=arguments.output_dir,
            )
            mode = "check"
    except (OSError, PairGenerationError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "TEXT2JSON_PAIR_ERROR",
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
                "counts_by_split": manifest["counts_by_split"],
                "counts_by_style": manifest["counts_by_style"],
                "mode": mode,
                "record_count": manifest["record_count"],
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
