"""Provider skeleton for Phase 5 RED tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProviderOutputError(ValueError):
    """Raised when provider output violates the Agent boundary."""


@dataclass(frozen=True)
class ProviderOutput:
    text: str
    metadata: dict[str, Any]

    def parse_json(self) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
        return ("parse_error", None, [])


class FakeAgentProvider:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    def generate_candidate(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> ProviderOutput:
        del prompt, schema, state
        response = self.responses[session_id]
        return ProviderOutput(text=str(response.get("text", "")), metadata={})


class FileAgentProvider:
    @classmethod
    def from_path(cls, path: Path | str) -> "FileAgentProvider":
        del path
        return cls()

    def generate_candidate(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> ProviderOutput:
        del session_id, prompt, schema, state
        return ProviderOutput(text="", metadata={})


def load_mimo_config_from_env() -> dict[str, Any]:
    return {"configured": False, "missing": []}


def redact_provider_payload(payload: Any) -> Any:
    return payload


def validate_provider_output(output: ProviderOutput) -> ProviderOutput:
    return output

