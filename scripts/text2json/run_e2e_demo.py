"""Run the Phase 3 Natural Language -> BIM JSON -> IFC2X3 demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_compiler import compile_document  # noqa: E402
from text2ifc_contract.schema import load_schema_v2  # noqa: E402
from text2ifc_contract.validation_v2 import validate_v2_document  # noqa: E402
from text2ifc_text.baseline import (  # noqa: E402
    DEFAULT_PROMPT_PATH,
    FakeProvider,
    build_fake_provider_for_records,
    build_prompt,
    load_prompt_contract,
)
from text2ifc_text.evaluation import evaluate_prediction_cases  # noqa: E402
from text2ifc_text.splits import atomic_write_text, render_json  # noqa: E402


DEFAULT_PAIRS_DIR = ROOT / "dataset" / "processed" / "text2json" / "pairs"
DEFAULT_OUTPUT_DIR = ROOT / "dataset" / "processed" / "text2json" / "e2e-demo"


class DemoError(ValueError):
    """Raised when the E2E demo cannot be configured."""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def select_spatial_sample(pairs_path: Path | str = DEFAULT_PAIRS_DIR) -> dict[str, Any]:
    root = Path(pairs_path)
    for split in ("validation", "test"):
        path = root / f"{split}.jsonl" if root.is_dir() else root
        records = _load_jsonl(path)
        for record in sorted(records, key=lambda item: item["record_id"]):
            if (
                record.get("split") == split
                and record.get("target_kind") == "formal"
                and record.get("text_style") == "spatial"
            ):
                return record
    raise DemoError("no formal spatial validation/test sample found")


def _target(record: dict[str, Any]) -> dict[str, Any]:
    path = Path(record["target_json_path"])
    if not path.is_absolute():
        path = ROOT / path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DemoError(f"{record['record_id']} target is not a JSON object")
    return payload


def _issue_payload(issue: Any) -> dict[str, Any]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _validate_prediction(raw_text: str) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        prediction = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return (
            "parse",
            None,
            [
                {
                    "code": "JSON_DECODE_ERROR",
                    "path": "",
                    "message": f"{exc.msg} at line {exc.lineno} column {exc.colno}",
                }
            ],
        )
    if not isinstance(prediction, dict):
        return (
            "schema",
            None,
            [
                {
                    "code": "INVALID_JSON_ROOT",
                    "path": "",
                    "message": "Prediction root must be a JSON object.",
                }
            ],
        )
    if prediction.get("draft_version") is not None:
        return (
            "draft",
            None,
            [
                {
                    "code": "DRAFT_NOT_COMPILABLE",
                    "path": "/draft_version",
                    "message": "Draft predictions are not compiled by the Phase 3 demo.",
                }
            ],
        )
    issues = validate_v2_document(prediction)
    if issues:
        return ("validation", None, [_issue_payload(issue) for issue in issues])
    return ("ok", prediction, [])


def _compiler_issues(result: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for issue in getattr(result, "input_issues", ()):
        issues.append(_issue_payload(issue))
    for issue in getattr(result, "ifc_issues", ()):
        issues.append(
            {
                "code": issue.code,
                "path": f"{issue.entity}/{issue.attribute}",
                "message": issue.message,
            }
        )
    return issues


def _write_report(
    *,
    output_dir: Path,
    sample: dict[str, Any],
    success: bool,
    diagnostics: dict[str, Any],
) -> None:
    lines = [
        "# Phase 3 E2E Demo Report",
        "",
        f"- Success: {success}",
        f"- Record ID: {sample['record_id']}",
        f"- Split: {sample['split']}",
        f"- Source file ID: {sample['source_file_id']}",
        f"- Text style: {sample['text_style']}",
        f"- Output directory: {output_dir}",
        "",
        "## Reproduce",
        "",
        "```powershell",
        "python scripts/text2json/run_e2e_demo.py --check",
        "python scripts/text2json/run_baseline.py --provider fake --split validation --evaluate",
        "python scripts/text2json/evaluate.py --check-fixtures",
        "```",
        "",
        "## Validation",
        "",
        f"- Stage: {diagnostics['validation']['stage']}",
        f"- Issue count: {len(diagnostics['validation']['issues'])}",
        "",
        "## Compilation",
        "",
        f"- Attempted: {diagnostics['compiled_ifc']['attempted']}",
        f"- Success: {diagnostics['compiled_ifc']['success']}",
    ]
    atomic_write_text(output_dir / "report.md", "\n".join(lines) + "\n")


def run_demo(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    check: bool = False,
    provider: Any | None = None,
    sample: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del check
    output = Path(output_dir)
    selected = sample or select_spatial_sample(DEFAULT_PAIRS_DIR)
    prompt = build_prompt(selected, load_prompt_contract(DEFAULT_PROMPT_PATH))
    active_provider = provider or build_fake_provider_for_records([selected])
    response = active_provider.generate(selected, prompt, load_schema_v2())
    raw_text = str(response.get("text", ""))
    atomic_write_text(output / "input.txt", selected["input_text"] + "\n")
    atomic_write_text(output / "raw-response.txt", raw_text)

    stage, prediction, issues = _validate_prediction(raw_text)
    diagnostics: dict[str, Any] = {
        "sample": selected,
        "provider_metadata": response.get("metadata", {}),
        "validation": {"stage": stage, "issues": issues},
        "compiled_ifc": {"attempted": False, "success": False, "issues": []},
    }
    if prediction is None:
        atomic_write_text(output / "diagnostics.json", render_json(diagnostics))
        _write_report(
            output_dir=output,
            sample=selected,
            success=False,
            diagnostics=diagnostics,
        )
        return {"success": False, "sample": selected, "diagnostics": diagnostics}

    atomic_write_text(output / "prediction.json", render_json(prediction))
    evaluation = evaluate_prediction_cases(
        [
            {
                "record_id": selected["record_id"],
                "split": selected["split"],
                "source_file_id": selected["source_file_id"],
                "target_json_path": selected["target_json_path"],
                "prediction_text": raw_text,
            }
        ],
        output_dir=output / "evaluation",
    )
    atomic_write_text(output / "metrics.json", render_json(evaluation["metrics"]))

    output_ifc = output / "output.ifc"
    compile_target = output_ifc if not output_ifc.exists() else output / ".output.check.ifc"
    compilation = compile_document(prediction, compile_target)
    if compilation.success and compile_target != output_ifc:
        compile_target.unlink(missing_ok=True)
    diagnostics["compiled_ifc"] = {
        "attempted": True,
        "success": compilation.success,
        "output_path": str(output_ifc if compilation.success else compilation.output_path),
        "issues": _compiler_issues(compilation),
    }
    atomic_write_text(output / "diagnostics.json", render_json(diagnostics))
    _write_report(
        output_dir=output,
        sample=selected,
        success=compilation.success,
        diagnostics=diagnostics,
    )
    return {
        "success": compilation.success,
        "sample": selected,
        "diagnostics": diagnostics,
        "evaluation": evaluation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()

    try:
        result = run_demo(output_dir=arguments.output_dir, check=arguments.check)
    except (DemoError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "TEXT2JSON_E2E_ERROR",
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
                "record_id": result["sample"]["record_id"],
                "split": result["sample"]["split"],
                "status": "ok" if result["success"] else "failed",
                "success": result["success"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
