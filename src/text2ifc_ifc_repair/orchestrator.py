"""Initial fail-closed repair stage runner through ChangeSet persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .resolution_flow import authorize_prototype, resolve_repair_intent


@dataclass(frozen=True)
class OrchestrationResult:
    status: str
    reason_code: str | None = None
    changeset: Any = None


class RepairOrchestrator:
    """Run deterministic resolution once and expose only an exact Stage 2 seam."""

    def __init__(
        self,
        *,
        run_directory: Path | str,
        resolver: Callable[..., Any] = resolve_repair_intent,
        prototype_authorizer: Callable[..., Any] = authorize_prototype,
        changeset_stage: Callable[..., Any],
        audit_stage: Callable[..., Any] | None = None,
        apply_stage: Callable[..., Any] | None = None,
    ) -> None:
        self.run_directory = Path(run_directory)
        self.run_directory.mkdir(parents=True, exist_ok=True)
        self._resolver = resolver
        self._prototype_authorizer = prototype_authorizer
        self._changeset_stage = changeset_stage
        # These are intentionally retained as disconnected Phase 09-03 seams.
        self._audit_stage = audit_stage
        self._apply_stage = apply_stage
        self._resolution: Any = None

    def start(
        self,
        *,
        intent: Any,
        repository: Any,
        expected_source_sha256: str,
    ) -> OrchestrationResult:
        self._write("intent.json", intent)
        resolution = self._resolver(
            intent,
            repository,
            expected_source_sha256=expected_source_sha256,
        )
        self._resolution = resolution
        self._write("resolution.json", resolution)
        return self._advance_if_exact(resolution)

    def continue_with_answer(self, answer: Mapping[str, Any]) -> OrchestrationResult:
        if self._resolution is None:
            raise ValueError("REPAIR_RESOLUTION_NOT_STARTED")
        resolution = self._prototype_authorizer(self._resolution, **dict(answer))
        self._resolution = resolution
        self._write("resolution.json", resolution)
        self._write("clarification-answer.json", dict(answer))
        return self._advance_if_exact(resolution)

    def _advance_if_exact(self, resolution: Any) -> OrchestrationResult:
        if resolution.status != "resolved":
            return OrchestrationResult(
                status="clarification_required",
                reason_code=resolution.reason_code,
            )
        changeset = self._changeset_stage(resolution)
        self._write("changeset.json", changeset)
        return OrchestrationResult(status="changeset_ready", changeset=changeset)

    def _write(self, name: str, value: Any) -> None:
        payload = _public_json(value)
        rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        (self.run_directory / name).write_text(rendered + "\n", encoding="utf-8")


def _public_json(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _public_json(value.to_dict())
    if is_dataclass(value):
        return _public_json(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _public_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_public_json(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {"type": type(value).__name__}


__all__ = ["OrchestrationResult", "RepairOrchestrator"]
