"""Structured-output Text-to-BIM-JSON baseline runner."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol

from text2ifc_contract.schema import load_schema_v2
from text2ifc_contract.validation_v2 import validate_v2_document

from .evaluation import _schema_issues, evaluate_prediction_cases
from .splits import ROOT, atomic_write_text, render_json


DEFAULT_PROMPT_PATH = ROOT / "prompts" / "text2json" / "structured-output-v1.md"
DEFAULT_BASELINE_RUNS_DIR = ROOT / "dataset" / "processed" / "text2json" / "baseline-runs"
DEFAULT_PREDICTIONS_DIR = ROOT / "dataset" / "processed" / "text2json" / "predictions"
BASELINE_SCHEMA_VERSION = "text2ifc/text2json-baseline-run-v1"


class BaselineError(ValueError):
    """Raised when the baseline runner cannot safely continue."""


class Provider(Protocol):
    def generate(
        self, record: dict[str, Any], prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Return provider output with `text` and optional `metadata`."""


class FakeProvider:
    """Deterministic provider used by tests and offline smoke runs."""

    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    def generate(
        self, record: dict[str, Any], prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        del prompt, schema
        record_id = record["record_id"]
        if record_id not in self.responses:
            raise BaselineError(f"fake provider has no response for {record_id}")
        response = self.responses[record_id]
        return {
            "text": str(response.get("text", "")),
            "metadata": dict(response.get("metadata", {})),
        }


class FileProvider:
    """Replay provider responses from a JSONL file or directory."""

    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    @classmethod
    def from_path(cls, path: Path | str) -> "FileProvider":
        root = Path(path)
        responses: dict[str, dict[str, Any]] = {}
        if root.is_file():
            for line in root.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                text = record.get("text", record.get("prediction_text"))
                if text is None and "prediction_json" in record:
                    text = _canonical(record["prediction_json"])
                if text is None:
                    raise BaselineError(f"{record.get('record_id')} has no text")
                responses[record["record_id"]] = {
                    "text": text,
                    "metadata": record.get("metadata", {}),
                }
            return cls(responses)
        for item in sorted(root.glob("*.json")):
            responses[item.stem] = {
                "text": item.read_text(encoding="utf-8"),
                "metadata": {"source_path": str(item)},
            }
        for item in sorted(root.glob("*.txt")):
            responses[item.stem] = {
                "text": item.read_text(encoding="utf-8"),
                "metadata": {"source_path": str(item)},
            }
        return cls(responses)

    def generate(
        self, record: dict[str, Any], prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        del prompt, schema
        record_id = record["record_id"]
        if record_id not in self.responses:
            raise BaselineError(f"file provider has no response for {record_id}")
        response = self.responses[record_id]
        return {
            "text": str(response.get("text", "")),
            "metadata": dict(response.get("metadata", {})),
        }


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _resolve(path: Path | str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def _safe_filename(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", value)


def load_prompt_contract(path: Path | str = DEFAULT_PROMPT_PATH) -> str:
    return _resolve(path).read_text(encoding="utf-8")


def build_prompt(record: dict[str, Any], prompt_contract: str) -> str:
    return (
        f"{prompt_contract.rstrip()}\n\n"
        "User request:\n"
        f"{record['input_text']}\n\n"
        "Return exactly one JSON object."
    )


def _issue_payload(issue: Any) -> dict[str, Any]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _classify_prediction(raw_text: str) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        prediction = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return (
            "parse_error",
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
            "schema_error",
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
            "draft_rejected",
            None,
            [
                {
                    "code": "DRAFT_NOT_FORMAL_BASELINE",
                    "path": "/draft_version",
                    "message": "Draft Envelopes are not accepted as formal baseline predictions.",
                }
            ],
        )
    structural = _schema_issues(prediction)
    if structural:
        return ("schema_error", None, [_issue_payload(issue) for issue in structural])
    issues = validate_v2_document(prediction)
    if issues:
        return ("semantic_error", None, [_issue_payload(issue) for issue in issues])
    return ("accepted", prediction, [])


def _load_pair_records(path: Path | str, split: str | None) -> list[dict[str, Any]]:
    root = Path(path)
    paths = sorted(root.glob("*.jsonl")) if root.is_dir() else [root]
    records: list[dict[str, Any]] = []
    for item in paths:
        for line in item.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if split is None or record.get("split") == split:
                records.append(record)
    return sorted(records, key=lambda record: record["record_id"])


def _load_target(record: dict[str, Any]) -> dict[str, Any]:
    path = Path(record["target_json_path"])
    if not path.is_absolute():
        path = ROOT / path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BaselineError(f"{record['record_id']} target is not a JSON object")
    return payload


def build_fake_provider_for_records(records: list[dict[str, Any]]) -> FakeProvider:
    responses = {
        record["record_id"]: {
            "text": _canonical(_load_target(record)),
            "metadata": {"provider": "fake", "mode": "target-echo"},
        }
        for record in records
    }
    return FakeProvider(responses)


def run_baseline_records(
    records: list[dict[str, Any]],
    *,
    provider: Provider,
    output_dir: Path | str,
    prompt_path: Path | str = DEFAULT_PROMPT_PATH,
    evaluate: bool = False,
    prediction_export_path: Path | str | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    prompt_contract = load_prompt_contract(prompt_path)
    schema = load_schema_v2()
    accepted_count = 0
    record_results: dict[str, dict[str, Any]] = {}
    evaluation_cases: list[dict[str, Any]] = []
    prediction_jsonl: list[str] = []
    raw_jsonl: list[str] = []

    for record in records:
        if record.get("target_kind", "formal") != "formal":
            raise BaselineError(
                f"{record['record_id']} target_kind must be formal for baseline"
            )
        prompt = build_prompt(record, prompt_contract)
        response = provider.generate(record, prompt, schema)
        raw_text = str(response.get("text", ""))
        metadata = dict(response.get("metadata", {}))
        safe_id = _safe_filename(record["record_id"])
        raw_path = output / "raw" / f"{safe_id}.txt"
        metadata_path = output / "raw" / f"{safe_id}.metadata.json"
        atomic_write_text(raw_path, raw_text)
        atomic_write_text(
            metadata_path,
            render_json(
                {
                    "record_id": record["record_id"],
                    "provider_metadata": metadata,
                }
            ),
        )
        raw_jsonl.append(
            _canonical(
                {
                    "record_id": record["record_id"],
                    "prediction_text": raw_text,
                    "metadata": metadata,
                }
            )
        )

        status, parsed, diagnostics = _classify_prediction(raw_text)
        result_record = {
            "record_id": record["record_id"],
            "split": record["split"],
            "source_file_id": record["source_file_id"],
            "status": status,
            "raw_response_path": str(raw_path),
            "raw_metadata_path": str(metadata_path),
            "diagnostics": diagnostics,
        }
        if parsed is not None:
            accepted_count += 1
            parsed_path = output / "parsed" / f"{safe_id}.json"
            atomic_write_text(parsed_path, render_json(parsed))
            result_record["parsed_prediction_path"] = str(parsed_path)
            prediction_jsonl.append(
                _canonical(
                    {
                        "record_id": record["record_id"],
                        "prediction_json": parsed,
                    }
                )
            )

        record_results[record["record_id"]] = result_record
        evaluation_cases.append(
            {
                "record_id": record["record_id"],
                "split": record["split"],
                "source_file_id": record["source_file_id"],
                "target_json_path": record["target_json_path"],
                "prediction_text": raw_text,
            }
        )

    summary = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "record_count": len(records),
        "accepted_count": accepted_count,
        "invalid_count": len(records) - accepted_count,
        "records": record_results,
    }
    atomic_write_text(output / "raw-responses.jsonl", "\n".join(raw_jsonl) + "\n")
    atomic_write_text(
        output / "accepted-predictions.jsonl", "\n".join(prediction_jsonl) + "\n"
    )
    if prediction_export_path is not None:
        atomic_write_text(Path(prediction_export_path), "\n".join(prediction_jsonl) + "\n")
    atomic_write_text(output / "diagnostics.json", render_json(summary))

    if evaluate:
        from .evaluation import write_evaluation_outputs

        evaluation = evaluate_prediction_cases(
            evaluation_cases,
            output_dir=output / "evaluation",
        )
        write_evaluation_outputs(evaluation, output / "evaluation")
        summary["evaluation"] = evaluation
    atomic_write_text(output / "run.json", render_json(summary))
    return summary


def run_baseline(
    *,
    pairs_path: Path | str,
    provider: Provider,
    output_dir: Path | str,
    split: str | None = None,
    prompt_path: Path | str = DEFAULT_PROMPT_PATH,
    evaluate: bool = False,
    prediction_export_path: Path | str | None = None,
) -> dict[str, Any]:
    return run_baseline_records(
        _load_pair_records(pairs_path, split),
        provider=provider,
        output_dir=output_dir,
        prompt_path=prompt_path,
        evaluate=evaluate,
        prediction_export_path=prediction_export_path,
    )
