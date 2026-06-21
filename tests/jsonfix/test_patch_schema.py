from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "jsonfix"


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.validation")
    except ModuleNotFoundError as exc:
        pytest.fail(f"jsonfix patch validation is not implemented: {exc}")
    return module.load_patch_schema, module.validate_patch_document


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _issue_pairs(name: str) -> set[tuple[str, str]]:
    _, validate_patch_document = _api()
    return {
        (issue.code, issue.path)
        for issue in validate_patch_document(_fixture(name))
    }


@pytest.mark.parametrize(
    "fixture_name",
    [
        "valid_add_wall_patch.json",
        "valid_set_fire_rating_patch.json",
        "valid_mark_missing_patch.json",
    ],
)
def test_positive_patch_fixtures_validate(fixture_name: str) -> None:
    _, validate_patch_document = _api()

    assert validate_patch_document(_fixture(fixture_name)) == []


def test_patch_schema_is_separate_local_draft_2020_12_contract() -> None:
    load_patch_schema, _ = _api()

    schema = load_patch_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/bim-json-patch/1.0/schema.json")
    assert schema["properties"]["patch_version"]["const"] == (
        "bim-json-patch/1.0"
    )
    assert schema["properties"]["target_schema_version"]["const"] == (
        "bim-json/2.0"
    )
    assert schema["properties"]["target_ifc_schema"]["const"] == "IFC2X3"
    assert "entities" not in schema["properties"]
    assert "relationships" not in schema["properties"]


@pytest.mark.parametrize(
    ("fixture_name", "expected"),
    [
        (
            "invalid_missing_provenance_patch.json",
            ("REQUIRED_FIELD", "/layers/0/provenance"),
        ),
        (
            "invalid_unsupported_operation_patch.json",
            (
                "UNSUPPORTED_PATCH_OPERATION",
                "/layers/0/operations/0/op",
            ),
        ),
        (
            "invalid_raw_step_patch.json",
            ("RAW_IFC_STEP_FORBIDDEN", "/layers/0/operations/0/value"),
        ),
        (
            "invalid_low_level_helper_patch.json",
            (
                "LOW_LEVEL_IFC_OBJECT_FORBIDDEN",
                "/layers/0/operations/0/value/ifc_class",
            ),
        ),
        (
            "invalid_step_id_patch.json",
            ("STEP_ID_FORBIDDEN", "/layers/0/operations/0/target/id"),
        ),
        (
            "invalid_delete_patch.json",
            (
                "DESTRUCTIVE_OPERATION_REQUIRES_REVIEW",
                "/layers/0/operations/0/op",
            ),
        ),
        (
            "invalid_missing_target_schema_patch.json",
            ("REQUIRED_FIELD", "/target_schema_version"),
        ),
        (
            "invalid_ifc4_target_patch.json",
            ("INVALID_ENUM", "/target_ifc_schema"),
        ),
    ],
)
def test_negative_patch_fixtures_have_stable_diagnostics(
    fixture_name: str,
    expected: tuple[str, str],
) -> None:
    assert expected in _issue_pairs(fixture_name)


def test_patch_validation_does_not_mutate_input() -> None:
    _, validate_patch_document = _api()
    document = _fixture("valid_add_wall_patch.json")
    before = json.dumps(document, sort_keys=True)

    validate_patch_document(document)

    assert json.dumps(document, sort_keys=True) == before
