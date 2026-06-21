from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_jsonfix.composer import compose_patches
from text2ifc_jsonfix.validation import validate_patch_document


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "jsonfix" / "build_repair_case.py"


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.repair_cases")
    except ModuleNotFoundError as exc:
        pytest.fail(f"repair case builder is not implemented: {exc}")
    return module.build_repair_case


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_missing_piece_case_writes_complete_deterministic_artifacts(
    tmp_path: Path,
) -> None:
    build_repair_case = _api()

    first = build_repair_case("missing-piece-repair", tmp_path)
    first_bytes = {
        path.name: path.read_bytes()
        for path in sorted(tmp_path.iterdir())
        if path.is_file()
    }
    second = build_repair_case("missing-piece-repair", tmp_path)
    second_bytes = {
        path.name: path.read_bytes()
        for path in sorted(tmp_path.iterdir())
        if path.is_file()
    }

    assert first == second
    assert first_bytes == second_bytes
    assert set(first_bytes) == {
        "base.json",
        "expected.json",
        "input.txt",
        "metadata.json",
        "patch.json",
    }


def test_missing_piece_base_and_patch_compose_to_expected_formal_document(
    tmp_path: Path,
) -> None:
    build_repair_case = _api()
    build_repair_case("missing-piece-repair", tmp_path)
    base = _load(tmp_path / "base.json")
    patch = _load(tmp_path / "patch.json")
    expected = _load(tmp_path / "expected.json")

    assert validate_v2_document(base) == []
    assert validate_patch_document(patch) == []
    assert "wall-west" not in {item["id"] for item in base["entities"]}

    result = compose_patches(base, [patch])

    assert result.valid
    assert result.document == expected
    assert validate_v2_document(expected) == []
    west = next(
        item for item in expected["entities"] if item["id"] == "wall-west"
    )
    assert west["ifc_class"] == "IfcWallStandardCase"
    assert west["attributes"]["ObjectPlacement"]["origin"] == [0, 2000, 0]
    assert west["attributes"]["ObjectPlacement"]["ref_direction"] == [0, 1, 0]


def test_case_metadata_declares_expected_fact_and_quality_gates(
    tmp_path: Path,
) -> None:
    build_repair_case = _api()
    build_repair_case("missing-piece-repair", tmp_path)
    metadata = _load(tmp_path / "metadata.json")

    assert metadata["schema_version"] == "text2ifc/jsonfix-repair-case-v1"
    assert metadata["case_id"] == "missing-piece-repair"
    assert metadata["expected_facts"]["added_entity_ids"] == ["wall-west"]
    assert metadata["expected_facts"]["unchanged_entity_ids"]
    assert metadata["quality"]["case_id"] == "missing-piece-repair"
    assert set(metadata["quality"]["walls"]) == {
        "wall-south",
        "wall-north",
        "wall-west",
        "wall-east",
    }
    assert metadata["quality"]["walls"]["wall-west"]["axis"] == "y"
    assert metadata["target_ifc_schema"] == "IFC2X3"


def test_case_input_is_chinese_and_explicit_enough_for_one_patch(
    tmp_path: Path,
) -> None:
    build_repair_case = _api()
    build_repair_case("missing-piece-repair", tmp_path)
    text = (tmp_path / "input.txt").read_text(encoding="utf-8")

    assert "西墙" in text
    assert "200" in text
    assert "Y" in text
    assert "(0, 2000, 0)" in text
    assert "不要修改其他构件" in text


def test_repair_case_cli_builds_the_named_case(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--case",
            "missing-piece-repair",
            "--output-dir",
            str(tmp_path),
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["success"]
    assert payload["formal_valid"]
    assert payload["patch_valid"]
    assert Path(payload["output_dir"]) == tmp_path
