"""Provider-independent Text-to-BIM-JSON evaluation harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


CompilerHook = Callable[[dict[str, Any], Path], Any]


def evaluate_prediction_cases(
    cases: list[dict[str, Any]],
    *,
    compiler: CompilerHook | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 Wave 4 evaluator is not implemented yet.")
