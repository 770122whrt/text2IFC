from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from text2ifc_jsonfix.validation import load_patch_schema


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference" / "bim-json-patch-1.0.md"
CLI = ROOT / "scripts" / "jsonfix" / "generate_patch_reference.py"


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.reference")
    except ModuleNotFoundError as exc:
        pytest.fail(f"patch reference generator is not implemented: {exc}")
    return module.render_patch_reference, module.check_patch_reference


def test_checked_in_patch_reference_matches_canonical_schema() -> None:
    render_patch_reference, _ = _api()

    assert REFERENCE.exists()
    assert REFERENCE.read_text(encoding="utf-8") == render_patch_reference(
        load_patch_schema()
    )


def test_patch_reference_is_stable_and_explains_the_boundary() -> None:
    render_patch_reference, _ = _api()

    first = render_patch_reference(load_patch_schema())
    second = render_patch_reference(load_patch_schema())

    assert first == second
    assert "\r" not in first
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    for heading in (
        "## Envelope",
        "## Layers",
        "## Operations",
        "## Safety Boundary",
        "## Compilation Boundary",
    ):
        assert heading in first
    for operation in (
        "add_entity",
        "set_attribute",
        "set_property",
        "add_relationship",
        "set_material",
        "mark_missing",
        "mark_unsupported_loss",
        "request_tombstone",
    ):
        assert f"`{operation}`" in first
    assert "not a Formal BIM JSON document" in first
    assert "validate_v2_document" in first


def test_patch_reference_cli_check_is_read_only() -> None:
    before = REFERENCE.read_bytes() if REFERENCE.exists() else None

    result = subprocess.run(
        [sys.executable, str(CLI), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert REFERENCE.read_bytes() == before
