"""Compose BIM JSON patches into a validation-gated candidate document."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_jsonfix.composer import compose_patches  # noqa: E402


MAX_INPUT_BYTES = 10 * 1024 * 1024


def _load_json(path: Path) -> Any:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"Input exceeds {MAX_INPUT_BYTES} bytes: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(
                value,
                temporary,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compose semantic patches onto Formal BIM JSON 2.0."
    )
    parser.add_argument("base", type=Path)
    parser.add_argument("patches", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        base = _load_json(args.base)
        patches = [_load_json(path) for path in args.patches]
        result = compose_patches(base, patches)
        diagnostics = result.to_dict()
        if args.diagnostics:
            _write_json_atomic(args.diagnostics, diagnostics)
        if result.valid:
            _write_json_atomic(args.output, result.document)
        print(
            json.dumps(
                {
                    "valid": result.valid,
                    "formal_valid": result.formal_valid,
                    "diagnostic_count": len(result.diagnostics),
                    "output_written": result.valid,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if result.valid else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                    "output_written": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
