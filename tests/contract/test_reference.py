import copy
import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from text2ifc_contract.schema import load_schema


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference" / "bim-json-1.0.md"
DOCS_INDEX = ROOT / "docs" / "README.md"
CLI = ROOT / "scripts" / "bim_json" / "generate_reference.py"
SUPPORTED_KINDS = (
    "wall",
    "column",
    "beam",
    "slab",
    "door",
    "window",
    "stair",
    "stair_flight",
    "roof",
)


def _reference_api():
    try:
        module = importlib.import_module("text2ifc_contract.reference")
    except ModuleNotFoundError as exc:
        pytest.fail(f"reference generator is not implemented: {exc}")
    return module.render_reference, module.check_reference


def _run_cli(*arguments):
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_checked_in_reference_exactly_matches_schema_rendering():
    render_reference, _ = _reference_api()

    assert REFERENCE.exists(), "generated reference is not checked in"
    assert REFERENCE.read_text(encoding="utf-8") == render_reference(load_schema())


def test_rendering_is_byte_stable_lf_only_and_has_one_final_newline():
    render_reference, _ = _reference_api()

    first = render_reference(load_schema())
    second = render_reference(load_schema())

    assert first == second
    assert "\r" not in first
    assert first.endswith("\n")
    assert not first.endswith("\n\n")


def test_reference_describes_contract_sections_and_constraints():
    render_reference, _ = _reference_api()
    reference = render_reference(load_schema())

    for heading in (
        "## Metadata",
        "## Hierarchy",
        "## Storeys",
        "## Common Element Fields",
        "## Element Kinds",
    ):
        assert heading in reference

    for value in ("bim-json/1.0", "IFC2X3", "MILLIMETRE"):
        assert f"`{value}`" in reference

    for field in ("is_external", "load_bearing", "predefined_type"):
        assert f"`{field}`" in reference

    assert "greater than `0`" in reference


def test_reference_lists_every_element_kind_and_required_dimensions():
    render_reference, _ = _reference_api()
    reference = render_reference(load_schema())
    expected_dimensions = {
        "wall": ("length", "height", "thickness"),
        "column": ("width", "depth", "height"),
        "beam": ("length", "width", "height"),
        "slab": ("length", "width", "thickness"),
        "door": ("width", "height"),
        "window": ("width", "height"),
        "stair": ("length", "width", "height"),
        "stair_flight": ("width", "rise", "run"),
        "roof": ("length", "width", "thickness"),
    }

    for kind in SUPPORTED_KINDS:
        section = reference.split(f"### `{kind}`", 1)[1].split("\n### ", 1)[0]
        for dimension in expected_dimensions[kind]:
            assert f"`{dimension}`" in section


def test_changed_schema_fails_drift_check_with_regeneration_instruction():
    _, check_reference = _reference_api()
    schema = copy.deepcopy(load_schema())
    schema["properties"]["target_schema"]["const"] = "IFC4"

    matches, message = check_reference(schema, REFERENCE)

    assert matches is False
    assert "python scripts/bim_json/generate_reference.py" in message


def test_docs_index_links_contract_reference():
    index = DOCS_INDEX.read_text(encoding="utf-8")

    assert "reference/bim-json-1.0.md" in index


def test_cli_check_passes_without_rewriting_reference():
    before = REFERENCE.read_bytes() if REFERENCE.exists() else None

    result = _run_cli("--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert REFERENCE.read_bytes() == before


def test_cli_can_generate_reference_to_requested_path(tmp_path):
    render_reference, _ = _reference_api()
    output = tmp_path / "nested" / "reference.md"

    result = _run_cli("--output", output)

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_text(encoding="utf-8") == render_reference(load_schema())
