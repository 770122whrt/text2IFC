"""Generated reference support for BIM JSON Patch 1.0."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATCH_REFERENCE_PATH = (
    ROOT / "docs" / "reference" / "bim-json-patch-1.0.md"
)
REGENERATION_COMMAND = (
    "python scripts/jsonfix/generate_patch_reference.py"
)


def _inline(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def render_patch_reference(schema: dict[str, Any]) -> str:
    required = schema["required"]
    layer = schema["$defs"]["layer"]
    target = schema["$defs"]["target"]
    operations = schema["x-supported-operations"]

    lines = [
        "<!-- Generated from schemas/bim-json-patch/1.0/schema.json. Do not edit. -->",
        "<!-- Regenerate with: python scripts/jsonfix/generate_patch_reference.py -->",
        "",
        "# BIM JSON Patch 1.0 Reference",
        "",
        schema["description"],
        "",
        "## Envelope",
        "",
        f"Required fields: {_inline(required)}.",
        "",
        "- `patch_version` is fixed to `bim-json-patch/1.0`.",
        "- `target_schema_version` is fixed to `bim-json/2.0`.",
        "- `target_ifc_schema` is fixed to `IFC2X3`.",
        "- `target_document_id` identifies the immutable base document.",
        "",
        "## Layers",
        "",
        f"Every ordered layer requires {_inline(layer['required'])}.",
        "Layer provenance distinguishes user, Agent, validator, and reviewer facts.",
        "",
        "## Operations",
        "",
        f"Supported operations: {_inline(operations)}.",
        "",
        "Targets require "
        f"{_inline(target['required'])}; optional addressing fields are "
        f"{_inline(sorted(set(target['properties']) - set(target['required'])))}.",
        "",
        "`request_tombstone` records deletion-like intent but requires review.",
        "",
        "## Safety Boundary",
        "",
        "Patch output forbids raw IFC/STEP, STEP line identifiers, low-level IFC "
        "helper objects, OpenUSD mesh facts, and generic transform operations.",
        "Unknown facts stay explicit through `mark_missing` or "
        "`mark_unsupported_loss`; they are not filled with defaults.",
        "",
        "## Compilation Boundary",
        "",
        "A patch is not a Formal BIM JSON document and cannot be compiled directly.",
        "The composer applies validated operations to an immutable BIM JSON 2.0 "
        "base document.",
        "The resulting candidate must pass `validate_v2_document` before the "
        "IFC2X3 compiler is invoked.",
        "",
    ]
    return "\n".join(lines)


def check_patch_reference(
    schema: dict[str, Any],
    path: Path = DEFAULT_PATCH_REFERENCE_PATH,
) -> tuple[bool, str]:
    expected = render_patch_reference(schema)
    try:
        actual = path.read_text(encoding="utf-8")
    except OSError:
        actual = None
    if actual == expected:
        return True, f"Reference is current: {path}"
    return (
        False,
        f"Reference is stale. Regenerate with `{REGENERATION_COMMAND}`.",
    )


def write_patch_reference(
    schema: dict[str, Any],
    path: Path = DEFAULT_PATCH_REFERENCE_PATH,
) -> None:
    content = render_patch_reference(schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
