"""Write or check Phase 3 formal gold targets and Draft sidecars."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_text.gold import (  # noqa: E402
    DEFAULT_AUDIT_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SPLIT_PATH,
    GoldSetError,
    check_all_artifacts,
    write_all_artifacts,
)
from text2ifc_text.splits import DEFAULT_MANIFEST_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLIT_PATH)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()

    try:
        if arguments.write:
            manifest = write_all_artifacts(
                manifest_path=arguments.manifest,
                split_manifest_path=arguments.splits,
                audit_path=arguments.audit,
                output_dir=arguments.output_dir,
            )
            mode = "write"
        else:
            manifest = check_all_artifacts(
                manifest_path=arguments.manifest,
                split_manifest_path=arguments.splits,
                audit_path=arguments.audit,
                output_dir=arguments.output_dir,
            )
            mode = "check"
    except (GoldSetError, OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "TEXT2JSON_GOLD_SET_ERROR",
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
                "counts": manifest["counts"],
                "file_count": manifest["file_count"],
                "mode": mode,
                "output_dir": arguments.output_dir.as_posix(),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
