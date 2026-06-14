"""Run the Phase 3 Natural Language -> BIM JSON -> IFC2X3 demo."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))


def select_spatial_sample(pairs_path: Path | str) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 Wave 6 E2E sample selection is not implemented yet.")


def run_demo(
    *,
    output_dir: Path | str,
    check: bool = False,
    provider: Any | None = None,
    sample: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 Wave 6 E2E demo is not implemented yet.")


def main() -> int:
    raise NotImplementedError("Phase 3 Wave 6 E2E CLI is not implemented yet.")


if __name__ == "__main__":
    raise SystemExit(main())
