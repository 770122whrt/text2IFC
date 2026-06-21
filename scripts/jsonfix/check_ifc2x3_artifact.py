"""CLI for the strict IFC2X3 artifact gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_jsonfix.ifc_artifact import check_ifc2x3_artifact  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    values = sys.argv[1:] if argv is None else argv
    if len(values) != 1:
        print("usage: check_ifc2x3_artifact.py PATH", file=sys.stderr)
        return 2
    result = check_ifc2x3_artifact(Path(values[0]))
    print(
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
