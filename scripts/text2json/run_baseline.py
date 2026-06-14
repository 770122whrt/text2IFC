"""Run the structured-output Text-to-BIM-JSON baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_text.baseline import (  # noqa: E402
    DEFAULT_BASELINE_RUNS_DIR,
    DEFAULT_PROMPT_PATH,
    DEFAULT_PREDICTIONS_DIR,
    BaselineError,
    FileProvider,
    build_fake_provider_for_records,
    run_baseline,
    _load_pair_records,
)


DEFAULT_PAIRS = ROOT / "dataset" / "processed" / "text2json" / "pairs"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("fake", "file"), required=True)
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--split", choices=("train", "validation", "test"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BASELINE_RUNS_DIR)
    parser.add_argument("--responses", type=Path)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--evaluate", action="store_true")
    arguments = parser.parse_args()

    try:
        records = _load_pair_records(arguments.pairs, arguments.split)
        if arguments.provider == "fake":
            provider = build_fake_provider_for_records(records)
        else:
            if arguments.responses is None:
                raise BaselineError("--responses is required for --provider file")
            provider = FileProvider.from_path(arguments.responses)
        result = run_baseline(
            pairs_path=arguments.pairs,
            provider=provider,
            output_dir=arguments.output_dir,
            split=arguments.split,
            prompt_path=arguments.prompt,
            evaluate=arguments.evaluate,
            prediction_export_path=(
                DEFAULT_PREDICTIONS_DIR
                / f"{arguments.provider}-{arguments.split or 'all'}.jsonl"
            ),
        )
    except (BaselineError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "TEXT2JSON_BASELINE_ERROR",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                },
                sort_keys=True,
            )
        )
        return 2

    payload = {
        "accepted_count": result["accepted_count"],
        "invalid_count": result["invalid_count"],
        "mode": arguments.provider,
        "output_dir": str(arguments.output_dir),
        "record_count": result["record_count"],
        "status": "ok",
    }
    if arguments.evaluate:
        payload["semantic_valid_rate"] = result["evaluation"]["metrics"]["validity"][
            "semantic_valid_rate"
        ]
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
