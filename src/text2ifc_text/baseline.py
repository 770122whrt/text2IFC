"""Structured-output Text-to-BIM-JSON baseline runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FakeProvider:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    def generate(self, record: dict[str, Any], prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Phase 3 Wave 5 baseline is not implemented yet.")


def load_prompt_contract(path: Path | str) -> str:
    raise NotImplementedError("Phase 3 Wave 5 prompt contract is not implemented yet.")


def run_baseline_records(
    records: list[dict[str, Any]],
    *,
    provider: FakeProvider,
    output_dir: Path | str,
    prompt_path: Path | str,
    evaluate: bool = False,
) -> dict[str, Any]:
    raise NotImplementedError("Phase 3 Wave 5 baseline runner is not implemented yet.")
