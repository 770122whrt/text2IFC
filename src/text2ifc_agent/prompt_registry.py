"""Versioned prompt loading, rendering, and trace identity validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "prompts" / "agent" / "registry.json"
REQUIRED_TEMPLATE_FIELDS = (
    "template_id",
    "role",
    "mode",
    "path",
    "sha256",
    "required_inputs",
    "forbidden_outputs",
)
REQUIRED_TRACE_FIELDS = (
    "template_id",
    "template_hash",
    "renderer_input_path",
    "rendered_prompt_path",
    "raw_response_path",
    "parsed_response_path",
    "validation_feedback_path",
    "metrics_path",
    "artifact_paths",
)


class PromptRegistryError(ValueError):
    """Raised when prompt identity, content, or trace data is incomplete."""


def load_prompt_registry(
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
) -> dict[str, dict[str, Any]]:
    """Load templates keyed by ID and verify their content hashes."""
    path = Path(registry_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    templates = payload.get("templates")
    if not isinstance(templates, list):
        raise PromptRegistryError("prompt registry templates must be a list")

    registry: dict[str, dict[str, Any]] = {}
    for raw_template in templates:
        if not isinstance(raw_template, dict):
            raise PromptRegistryError("prompt registry template must be an object")
        missing = [field for field in REQUIRED_TEMPLATE_FIELDS if field not in raw_template]
        if missing:
            raise PromptRegistryError(
                "prompt template missing required fields: " + ", ".join(missing)
            )
        template = dict(raw_template)
        template_id = str(template["template_id"])
        if template_id in registry:
            raise PromptRegistryError(f"duplicate prompt template_id: {template_id}")
        template_path = _project_path(str(template["path"]))
        actual_hash = _template_sha256(template_path)
        if template["sha256"] != actual_hash:
            raise PromptRegistryError(
                f"prompt template hash mismatch for {template_id}: {actual_hash}"
            )
        registry[template_id] = template
    return registry


def render_prompt(
    *,
    template_id: str,
    inputs: Mapping[str, Any],
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """Render a registered prompt from explicit structured inputs."""
    registry = load_prompt_registry(registry_path)
    if template_id not in registry:
        raise PromptRegistryError(f"unknown prompt template_id: {template_id}")
    template = registry[template_id]
    missing_inputs = [
        name for name in template["required_inputs"] if name not in inputs
    ]
    if missing_inputs:
        raise PromptRegistryError(
            "prompt renderer missing required inputs: " + ", ".join(missing_inputs)
        )

    text = _project_path(str(template["path"])).read_text(encoding="utf-8")
    normalized_inputs: dict[str, Any] = {}
    for name in template["required_inputs"]:
        value = inputs[name]
        normalized_inputs[name] = value
        text = text.replace("{{" + name + "}}", _render_value(value))

    unresolved = [
        name
        for name in template["required_inputs"]
        if "{{" + name + "}}" in text
    ]
    if unresolved:
        raise PromptRegistryError(
            "prompt renderer left unresolved inputs: " + ", ".join(unresolved)
        )
    return {
        "text": text,
        "inputs": normalized_inputs,
        "metadata": {
            "template_id": template_id,
            "template_hash": template["sha256"],
            "role": template["role"],
            "mode": template["mode"],
            "template_path": template["path"],
        },
    }


def validate_prompt_trace(trace: Mapping[str, Any]) -> None:
    """Reject a provider trace that cannot reproduce its prompt call."""
    missing = [field for field in REQUIRED_TRACE_FIELDS if not trace.get(field)]
    if missing:
        raise PromptRegistryError(
            "prompt trace missing required fields: " + ", ".join(missing)
        )
    expected = load_prompt_registry().get(str(trace["template_id"]))
    if expected is None:
        raise PromptRegistryError(
            f"prompt trace has unknown template_id: {trace['template_id']}"
        )
    if trace["template_hash"] != expected["sha256"]:
        raise PromptRegistryError("prompt trace template_hash does not match registry")


def _render_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _template_sha256(path: Path) -> str:
    canonical_bytes = path.read_bytes().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()


def _project_path(relative_path: str) -> Path:
    path = (PROJECT_ROOT / relative_path).resolve()
    try:
        path.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise PromptRegistryError("prompt template path escapes project root") from exc
    if not path.is_file():
        raise PromptRegistryError(f"prompt template file does not exist: {relative_path}")
    return path
