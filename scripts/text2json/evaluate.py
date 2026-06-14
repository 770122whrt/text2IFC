"""Evaluate Text-to-BIM-JSON predictions against formal BIM JSON targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_text.evaluation import (  # noqa: E402
    DEFAULT_EVALUATION_FIXTURE_DIR,
    DEFAULT_PAIRS_DIR,
    EvaluationError,
    evaluate_pair_predictions,
    run_fixture_evaluation,
    write_evaluation_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS_DIR)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EVALUATION_FIXTURE_DIR)
    parser.add_argument("--split", choices=("train", "validation", "test"))
    parser.add_argument("--compile", action="store_true", dest="run_compiler")
    parser.add_argument("--check-fixtures", action="store_true")
    arguments = parser.parse_args()

    try:
        if arguments.check_fixtures:
            result = run_fixture_evaluation(arguments.output_dir)
            mode = "check-fixtures"
        else:
            if arguments.predictions is None:
                raise EvaluationError("--predictions is required unless --check-fixtures is used")
            result = evaluate_pair_predictions(
                pairs_path=arguments.pairs,
                predictions_path=arguments.predictions,
                output_dir=arguments.output_dir,
                split=arguments.split,
                run_compiler=arguments.run_compiler,
            )
            write_evaluation_outputs(result, arguments.output_dir)
            mode = "evaluate"
    except (EvaluationError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "TEXT2JSON_EVALUATION_ERROR",
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
                "mode": mode,
                "output_dir": str(arguments.output_dir),
                "record_count": result["metrics"]["record_count"],
                "parse_success_rate": result["metrics"]["validity"][
                    "parse_success_rate"
                ],
                "schema_valid_rate": result["metrics"]["validity"][
                    "schema_valid_rate"
                ],
                "semantic_valid_rate": result["metrics"]["validity"][
                    "semantic_valid_rate"
                ],
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
